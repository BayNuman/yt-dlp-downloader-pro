package com.baynuman.ytdownloader.data

import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow

object DownloadRepository {
    val downloadEvents = MutableSharedFlow<DownloadEvent>(extraBufferCapacity = 128)
    val isRunning = MutableStateFlow(false)
    
    @Volatile
    private var _activeRunner: YtDlpRunner? = null
    
    @Volatile
    private var _activeRequest: DownloadRequest? = null
    
    var activeRunner: YtDlpRunner?
        @Synchronized get() = _activeRunner
        @Synchronized set(value) {
            _activeRunner = value
        }
        
    var activeRequest: DownloadRequest?
        @Synchronized get() = _activeRequest
        @Synchronized set(value) {
            _activeRequest = value
        }
}
