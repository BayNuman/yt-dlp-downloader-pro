package com.baynuman.ytdownloader.data.storage

import android.content.Context
import android.media.MediaScannerConnection
import android.net.Uri
import android.util.Log

object MediaStoreScanner {
    /**
     * Natively scans local downloaded files into Android MediaStore.
     * This ensures the files immediately appear inside native apps like Gallery, Photos, or Music players.
     */
    fun scanFile(context: Context, filePath: String, onScanComplete: (Uri?) -> Unit = {}) {
        try {
            MediaScannerConnection.scanFile(
                context.applicationContext,
                arrayOf(filePath),
                null
            ) { _, uri ->
                onScanComplete(uri)
            }
        } catch (e: Exception) {
            Log.e("MediaStoreScanner", "Failed to scan file via MediaScanner", e)
            onScanComplete(null)
        }
    }
}
