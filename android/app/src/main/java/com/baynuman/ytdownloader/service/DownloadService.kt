package com.baynuman.ytdownloader.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.core.app.ServiceCompat
import com.baynuman.ytdownloader.MainActivity
import com.baynuman.ytdownloader.data.DownloadEvent
import com.baynuman.ytdownloader.data.DownloadRequest
import com.baynuman.ytdownloader.data.YtDlpRunner
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.launch

class DownloadService : Service() {

    private val serviceScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private val waveformExecutor = java.util.concurrent.Executors.newSingleThreadExecutor()

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    private var networkCallback: android.net.ConnectivityManager.NetworkCallback? = null

    override fun onDestroy() {
        unregisterWifiOnlyKillSwitch()
        serviceScope.cancel()
        waveformExecutor.shutdown()
        super.onDestroy()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent == null) {
            stopForegroundService()
            return START_NOT_STICKY
        }

        val action = intent.action ?: ACTION_STOP
        when (action) {
            ACTION_START -> {
                val requestJson = intent.getStringExtra(EXTRA_REQUEST_JSON)
                if (requestJson != null) {
                    val title = intent.getStringExtra(EXTRA_TITLE) ?: "Downloading..."
                    val notification = buildProgressNotification(title, 0, "--", "--")
                    startForeground(NOTIFICATION_ID, notification)

                    try {
                        val request = DownloadRequest.fromJsonString(requestJson)
                        startDownloadJob(request, title)
                    } catch (e: Exception) {
                        Log.e("DownloadService", "Failed to parse request JSON", e)
                        serviceScope.launch {
                            downloadEvents.emit(DownloadEvent.Finished(success = false, exitCode = -1))
                        }
                        stopForegroundService()
                    }
                } else {
                    stopForegroundService()
                }
            }
            ACTION_UPDATE -> {
                val title = intent.getStringExtra(EXTRA_TITLE) ?: "Downloading..."
                val progress = intent.getIntExtra(EXTRA_PROGRESS, 0)
                val speed = intent.getStringExtra(EXTRA_SPEED) ?: "--"
                val eta = intent.getStringExtra(EXTRA_ETA) ?: "--"
                updateNotification(title, progress, speed, eta)
            }
            ACTION_STOP -> {
                cancelActiveDownload()
                stopForegroundService()
            }
        }

        return START_NOT_STICKY
    }

    private fun registerWifiOnlyKillSwitch() {
        val cm = getSystemService(Context.CONNECTIVITY_SERVICE) as android.net.ConnectivityManager
        val request = android.net.NetworkRequest.Builder()
            .addCapability(android.net.NetworkCapabilities.NET_CAPABILITY_INTERNET)
            .build()
        
        val callback = object : android.net.ConnectivityManager.NetworkCallback() {
            override fun onCapabilitiesChanged(
                network: android.net.Network,
                networkCapabilities: android.net.NetworkCapabilities
            ) {
                super.onCapabilitiesChanged(network, networkCapabilities)
                val isMetered = !networkCapabilities.hasCapability(android.net.NetworkCapabilities.NET_CAPABILITY_NOT_METERED)
                val isCellular = networkCapabilities.hasTransport(android.net.NetworkCapabilities.TRANSPORT_CELLULAR)
                if (isMetered || isCellular) {
                    Log.w("DownloadService", "Wifi-Only: Switched to cellular network. Aborting download to prevent network bleeding.")
                    serviceScope.launch {
                        downloadEvents.emit(DownloadEvent.LogLine("[hata] WiFi bağlantısı kesildi! Hücresel veri kullanımını önlemek için indirme iptal edildi.\n"))
                    }
                    cancelActiveDownload()
                    stopForegroundService()
                }
            }

            override fun onLost(network: android.net.Network) {
                super.onLost(network)
                Log.w("DownloadService", "Wifi-Only: Network connection lost completely.")
                serviceScope.launch {
                    downloadEvents.emit(DownloadEvent.LogLine("[hata] Ağ bağlantısı tamamen kesildi! İndirme durduruldu.\n"))
                }
                cancelActiveDownload()
                stopForegroundService()
            }
        }
        
        try {
            cm.registerNetworkCallback(request, callback)
            networkCallback = callback
            Log.d("DownloadService", "Registered Wifi-Only Connectivity NetworkCallback Kill-Switch")
        } catch (e: Exception) {
            Log.e("DownloadService", "Failed to register network callback", e)
        }
    }

    private fun unregisterWifiOnlyKillSwitch() {
        networkCallback?.let { callback ->
            try {
                val cm = getSystemService(Context.CONNECTIVITY_SERVICE) as android.net.ConnectivityManager
                cm.unregisterNetworkCallback(callback)
                Log.d("DownloadService", "Unregistered Wifi-Only Connectivity NetworkCallback")
            } catch (e: Exception) {
                Log.e("DownloadService", "Failed to unregister network callback", e)
            }
            networkCallback = null
        }
    }

    private fun startDownloadJob(request: DownloadRequest, title: String) {
        isRunning.value = true
        activeRequest = request
        
        if (request.wifiOnly) {
            registerWifiOnlyKillSwitch()
        }

        serviceScope.launch {
            try {
                val runner = YtDlpRunner(applicationContext)
                activeRunner = runner
                
                // Speed & ETA regex for parsing inside the service to update notification
                val speedRegex = Regex("""\bat\s+([0-9.]+\s*[KMGT]?i?B/s)""", RegexOption.IGNORE_CASE)
                val etaRegex = Regex("""\bETA\s+([0-9:.]+)""", RegexOption.IGNORE_CASE)
                val batchProgressRegex = Regex("""\[download\]\s+Downloading\s+video\s+(\d+)\s+of\s+(\d+)""", RegexOption.IGNORE_CASE)
                val destRegex = Regex("""\[download\]\s+Destination:\s+(.+)""", RegexOption.IGNORE_CASE)
                val alreadyRegex = Regex("""\[download\]\s+(.+)\s+has already been downloaded""", RegexOption.IGNORE_CASE)
                val mergerRegex = Regex("""\[Merger\]\s+Merging\s+formats\s+into\s+"(.+)"""", RegexOption.IGNORE_CASE)
                
                var currentSpeed = "--"
                var currentEta = "--"
                var currentProgressPercent = 0

                val urls = request.urls
                var batchTotalCount = urls.size
                var batchCurrentIndex = 0
                var batchCompletedCount = 0
                var batchActiveTitle = if (urls.isNotEmpty()) "İndiriliyor..." else ""

                runner.run(request) { event ->
                    // Emit event to shared flow
                    serviceScope.launch {
                        downloadEvents.emit(event)
                    }

                    // Update local service notification
                    when (event) {
                        is DownloadEvent.Progress -> {
                            val percent = (event.value * 100).toInt().coerceIn(0, 100)
                            currentProgressPercent = percent
                            updateNotification(
                                title = title,
                                progress = currentProgressPercent,
                                speed = currentSpeed,
                                eta = currentEta,
                                force = false,
                                batchCurrentIndex = batchCurrentIndex,
                                batchTotalCount = batchTotalCount,
                                batchCompletedCount = batchCompletedCount,
                                batchActiveTitle = batchActiveTitle
                            )
                        }
                        is DownloadEvent.LogLine -> {
                            val line = event.text
                            
                            batchProgressRegex.find(line)?.let { match ->
                                val curr = match.groupValues[1].toIntOrNull()
                                val total = match.groupValues[2].toIntOrNull()
                                if (curr != null && total != null) {
                                    batchCurrentIndex = curr - 1
                                    batchTotalCount = total
                                    batchCompletedCount = batchCurrentIndex
                                }
                            }

                            val destMatch = destRegex.find(line)?.groupValues?.getOrNull(1)
                                ?: alreadyRegex.find(line)?.groupValues?.getOrNull(1)
                                ?: mergerRegex.find(line)?.groupValues?.getOrNull(1)
                            if (destMatch != null) {
                                val file = java.io.File(destMatch)
                                batchActiveTitle = file.name
                            }

                            val speedMatch = speedRegex.find(line)?.groupValues?.getOrNull(1)
                            val etaMatch = etaRegex.find(line)?.groupValues?.getOrNull(1)
                            if (speedMatch != null || etaMatch != null || line.contains("Destination:") || line.contains("has already been downloaded")) {
                                currentSpeed = speedMatch ?: currentSpeed
                                currentEta = etaMatch ?: currentEta
                                updateNotification(
                                    title = title,
                                    progress = currentProgressPercent,
                                    speed = currentSpeed,
                                    eta = currentEta,
                                    force = false,
                                    batchCurrentIndex = batchCurrentIndex,
                                    batchTotalCount = batchTotalCount,
                                    batchCompletedCount = batchCompletedCount,
                                    batchActiveTitle = batchActiveTitle
                                )
                            }
                        }
                        is DownloadEvent.Status -> {
                            // Update status if needed
                        }
                        is DownloadEvent.Finished -> {
                            if (event.success && request.mode == com.baynuman.ytdownloader.data.DownloadMode.AUDIO && event.filePath.isNotBlank()) {
                                enqueueWaveformGeneration(request, event.filePath)
                            }
                            stopForegroundService()
                        }
                    }
                }
            } catch (e: Exception) {
                serviceScope.launch {
                    downloadEvents.emit(DownloadEvent.Finished(success = false, exitCode = -1))
                }
                stopForegroundService()
            } finally {
                activeRunner = null
                activeRequest = null
                isRunning.value = false
                if (request.wifiOnly) {
                    unregisterWifiOnlyKillSwitch()
                }
            }
        }
    }

    private fun cancelActiveDownload() {
        activeRunner?.cancel()
        activeRunner = null
        activeRequest = null
        isRunning.value = false
    }

    private fun stopForegroundService() {
        ServiceCompat.stopForeground(this, ServiceCompat.STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    private var lastNotificationTime = 0L

    private fun updateNotification(
        title: String,
        progress: Int,
        speed: String,
        eta: String,
        force: Boolean = false,
        batchCurrentIndex: Int = 0,
        batchTotalCount: Int = 1,
        batchCompletedCount: Int = 0,
        batchActiveTitle: String = ""
    ) {
        val now = System.currentTimeMillis()
        if (!force && now - lastNotificationTime < 1000L) {
            return
        }
        lastNotificationTime = now
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val notification = buildProgressNotification(
            title = title,
            progress = progress,
            speed = speed,
            valEta = eta,
            batchCurrentIndex = batchCurrentIndex,
            batchTotalCount = batchTotalCount,
            batchCompletedCount = batchCompletedCount,
            batchActiveTitle = batchActiveTitle
        )
        manager.notify(NOTIFICATION_ID, notification)
    }

    private fun buildProgressNotification(
        title: String,
        progress: Int,
        speed: String,
        valEta: String,
        batchCurrentIndex: Int = 0,
        batchTotalCount: Int = 1,
        batchCompletedCount: Int = 0,
        batchActiveTitle: String = ""
    ): Notification {
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val builder = NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.stat_sys_download)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setSilent(true)
            .setOnlyAlertOnce(true)

        if (batchTotalCount > 1) {
            val currentIdxHuman = (batchCurrentIndex + 1).coerceAtMost(batchTotalCount)
            val headline = "İndiriliyor ($currentIdxHuman/$batchTotalCount)"
            val activeText = "▶ $batchActiveTitle: $progress% ($speed)"
            val remaining = batchTotalCount - currentIdxHuman
            val summaryText = "✓ $batchCompletedCount tamamlandı, $remaining bekliyor"

            builder.setContentTitle(headline)
            builder.setContentText(activeText)
            builder.setProgress(100, progress, false)

            val inboxStyle = NotificationCompat.InboxStyle()
                .setBigContentTitle(headline)
                .addLine(activeText)
                .addLine(summaryText)
            if (valEta != "--" && valEta.isNotBlank()) {
                inboxStyle.setSummaryText("Kalan süre: $valEta")
            }
            builder.setStyle(inboxStyle)
        } else {
            val speedEta = if (speed != "--" || valEta != "--") {
                "Speed: $speed  •  ETA: $valEta"
            } else {
                "Downloading..."
            }
            builder.setContentTitle(title)
            builder.setContentText(speedEta)
            builder.setProgress(100, progress, false)
        }

        return builder.build()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Download Progress",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Shows progress of active media downloads"
                setShowBadge(false)
            }
            val manager = getSystemService(NotificationManager::class.java)
            manager?.createNotificationChannel(channel)
        }
    }

    private fun enqueueWaveformGeneration(request: DownloadRequest, filePath: String) {
        val context = applicationContext
        waveformExecutor.submit {
            try {
                val audioFile = java.io.File(filePath)
                if (!audioFile.exists() || !audioFile.isFile) return@submit

                val waveformsDir = java.io.File(context.filesDir, "waveforms")
                if (!waveformsDir.exists()) {
                    waveformsDir.mkdirs()
                }
                val uuid = java.util.UUID.randomUUID().toString()
                val outputPng = java.io.File(waveformsDir, "waveform_$uuid.png")

                // Resolve FFmpeg path
                val runner = YtDlpRunner(context)
                val ffmpegBin = runner.getFFmpegFile()
                if (!ffmpegBin.exists()) {
                    Log.w("DownloadService", "FFmpeg binary not found for waveform generation.")
                    return@submit
                }

                // Command: ffmpeg -i input.mp3 -filter_complex "aresample=1000,showwavespic=s=320x60:colors=#6366f1" -frames:v 1 output.png
                val cmd = listOf(
                    ffmpegBin.absolutePath,
                    "-y",
                    "-i", audioFile.absolutePath,
                    "-filter_complex", "aresample=1000,showwavespic=s=320x60:colors=#6366f1",
                    "-frames:v", "1",
                    outputPng.absolutePath
                )

                Log.d("DownloadService", "Enqueuing waveform: $cmd")
                val process = ProcessBuilder(cmd)
                    .redirectErrorStream(true)
                    .start()

                // Read output to avoid process block
                process.inputStream.bufferedReader().use { reader ->
                    while (reader.readLine() != null) { /* no-op */ }
                }

                val exitCode = process.waitFor()
                if (exitCode == 0 && outputPng.exists()) {
                    Log.i("DownloadService", "Waveform successfully generated at: ${outputPng.absolutePath}")
                    // Update SQLite database record using taskId directly with a retry block (B1 / B4)
                    val db = com.baynuman.ytdownloader.data.db.DownloadDatabase.getDatabase(context)
                    val dao = db.downloadRecordDao()
                    
                    var rowsUpdated = 0
                    for (i in 1..20) {
                        rowsUpdated = dao.updateThumbnailPath(request.taskId, outputPng.absolutePath)
                        if (rowsUpdated > 0) {
                            Log.i("DownloadService", "Waveform path updated in DB for taskId: ${request.taskId}")
                            break
                        }
                        Thread.sleep(500) // Wait for database insertion from ViewModel
                    }
                    if (rowsUpdated == 0) {
                        Log.w("DownloadService", "Failed to update waveform path in DB: record not found for taskId: ${request.taskId}")
                    }
                } else {
                    Log.w("DownloadService", "FFmpeg waveform process failed (exit code: $exitCode)")
                }
            } catch (e: Exception) {
                Log.e("DownloadService", "Error during sequential waveform generation", e)
            }
        }
    }

    companion object {
        private const val NOTIFICATION_ID = 4040
        private const val CHANNEL_ID = "download_progress_channel"

        const val ACTION_START = "com.baynuman.ytdownloader.action.START"
        const val ACTION_UPDATE = "com.baynuman.ytdownloader.action.UPDATE"
        const val ACTION_STOP = "com.baynuman.ytdownloader.action.STOP"

        const val EXTRA_TITLE = "extra_title"
        const val EXTRA_PROGRESS = "extra_progress"
        const val EXTRA_SPEED = "extra_speed"
        const val EXTRA_ETA = "extra_eta"
        const val EXTRA_REQUEST_JSON = "extra_request_json"

        // Delegate to thread-safe Application-scoped Repository Singleton (A1)
        val downloadEvents get() = com.baynuman.ytdownloader.data.DownloadRepository.downloadEvents
        val isRunning get() = com.baynuman.ytdownloader.data.DownloadRepository.isRunning
        
        var activeRunner: YtDlpRunner?
            get() = com.baynuman.ytdownloader.data.DownloadRepository.activeRunner
            set(value) { com.baynuman.ytdownloader.data.DownloadRepository.activeRunner = value }
            
        var activeRequest: DownloadRequest?
            get() = com.baynuman.ytdownloader.data.DownloadRepository.activeRequest
            set(value) { com.baynuman.ytdownloader.data.DownloadRepository.activeRequest = value }
    }
}
