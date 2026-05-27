package com.baynuman.ytdownloader.data

import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow

object DownloadRepository {
    val downloadEvents = MutableSharedFlow<DownloadEvent>(extraBufferCapacity = 128)
    val isRunning = MutableStateFlow(false)
    
    @Volatile
    var activeRunner: YtDlpRunner? = null
    
    @Volatile
    var activeRequest: DownloadRequest? = null
}
