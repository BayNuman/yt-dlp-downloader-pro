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
import androidx.core.app.NotificationCompat
import com.baynuman.ytdownloader.MainActivity

class DownloadService : Service() {

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent == null) {
            stopSelf()
            return START_NOT_STICKY
        }

        val action = intent.action ?: ACTION_STOP
        when (action) {
            ACTION_START -> {
                val title = intent.getStringExtra(EXTRA_TITLE) ?: "Downloading..."
                val notification = buildProgressNotification(title, 0, "--", "--")
                startForeground(NOTIFICATION_ID, notification)
            }
            ACTION_UPDATE -> {
                val title = intent.getStringExtra(EXTRA_TITLE) ?: "Downloading..."
                val progress = intent.getIntExtra(EXTRA_PROGRESS, 0)
                val speed = intent.getStringExtra(EXTRA_SPEED) ?: "--"
                val eta = intent.getStringExtra(EXTRA_ETA) ?: "--"
                updateNotification(title, progress, speed, eta)
            }
            ACTION_STOP -> {
                stopForeground(true)
                stopSelf()
            }
        }

        return START_NOT_STICKY
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
    }
}
