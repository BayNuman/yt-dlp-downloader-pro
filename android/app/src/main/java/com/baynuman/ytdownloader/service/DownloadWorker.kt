package com.baynuman.ytdownloader.service

import android.content.Context
import android.content.Intent
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import android.util.Log

class DownloadWorker(
    appContext: Context,
    params: WorkerParameters
) : CoroutineWorker(appContext, params) {

    override suspend fun doWork(): Result {
        Log.d("DownloadWorker", "WorkManager background schedule trigger fired!")
        val requestJson = inputData.getString("request_json")
        val title = inputData.getString("title") ?: "Downloading..."

        if (requestJson.isNullOrBlank()) {
            Log.e("DownloadWorker", "Empty request JSON inside WorkManager input data!")
            return Result.failure()
        }

        try {
            val intent = Intent(applicationContext, DownloadService::class.java).apply {
                action = DownloadService.ACTION_START
                putExtra(DownloadService.EXTRA_REQUEST_JSON, requestJson)
                putExtra(DownloadService.EXTRA_TITLE, title)
            }
            if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
                applicationContext.startForegroundService(intent)
            } else {
                applicationContext.startService(intent)
            }
            Log.d("DownloadWorker", "Successfully triggered DownloadService from WorkManager")
            return Result.success()
        } catch (e: Exception) {
            Log.e("DownloadWorker", "Failed to delegate execution to DownloadService from worker", e)
            return Result.failure()
        }
    }
}
