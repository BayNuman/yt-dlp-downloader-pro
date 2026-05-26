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

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    override fun onDestroy() {
        serviceScope.cancel()
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

    private fun startDownloadJob(request: DownloadRequest, title: String) {
        isRunning.value = true
        activeRequest = request
        serviceScope.launch {
            try {
                val runner = YtDlpRunner(applicationContext)
                activeRunner = runner
                
                // Speed & ETA regex for parsing inside the service to update notification
                val speedRegex = Regex("""\bat\s+([0-9.]+\s*[KMGT]?i?B/s)""", RegexOption.IGNORE_CASE)
                val etaRegex = Regex("""\bETA\s+([0-9:.]+)""", RegexOption.IGNORE_CASE)
                
                var currentSpeed = "--"
                var currentEta = "--"
                var currentProgressPercent = 0

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
                            updateNotification(title, currentProgressPercent, currentSpeed, currentEta)
                        }
                        is DownloadEvent.LogLine -> {
                            val line = event.text
                            val speedMatch = speedRegex.find(line)?.groupValues?.getOrNull(1)
                            val etaMatch = etaRegex.find(line)?.groupValues?.getOrNull(1)
                            if (speedMatch != null || etaMatch != null) {
                                currentSpeed = speedMatch ?: currentSpeed
                                currentEta = etaMatch ?: currentEta
                                updateNotification(title, currentProgressPercent, currentSpeed, currentEta)
                            }
                        }
                        is DownloadEvent.Status -> {
                            // Update status if needed
                        }
                        is DownloadEvent.Finished -> {
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

    private fun updateNotification(title: String, progress: Int, speed: String, eta: String) {
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val notification = buildProgressNotification(title, progress, speed, eta)
        manager.notify(NOTIFICATION_ID, notification)
    }

    private fun buildProgressNotification(
        title: String,
        progress: Int,
        speed: String,
        valEta: String
    ): Notification {
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val speedEta = if (speed != "--" || valEta != "--") {
            "Speed: $speed  •  ETA: $valEta"
        } else {
            "Downloading..."
        }

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(title)
            .setContentText(speedEta)
            .setSmallIcon(android.R.drawable.stat_sys_download)
            .setProgress(100, progress, false)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setSilent(true)
            .setOnlyAlertOnce(true)
            .build()
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

        val downloadEvents = MutableSharedFlow<DownloadEvent>(extraBufferCapacity = 128)
        val isRunning = MutableStateFlow(false)
        
        @Volatile
        private var activeRunner: YtDlpRunner? = null
        
        @Volatile
        var activeRequest: DownloadRequest? = null
    }
}
