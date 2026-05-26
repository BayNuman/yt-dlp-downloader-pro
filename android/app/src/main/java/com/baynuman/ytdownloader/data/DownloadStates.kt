package com.baynuman.ytdownloader.data

import com.baynuman.ytdownloader.ui.UrlValidationState

data class DownloadPreferencesState(
    val mode: DownloadMode = DownloadMode.VIDEO,
    val videoPreset: String = "Full HD (1080p)",
    val customVideoHeight: String = "1080",
    val videoContainer: String = "mp4",
    val videoAudioCodec: String = "AAC",
    val audioFormat: String = "aac",
    val audioQualityPreset: String = "Dengeli (192K)",
    val isBatchMode: Boolean = false,
    val playlistEnabled: Boolean = true,
    val showAdvanced: Boolean = false,
    val rateLimit: String = "",
    val downloadArchive: Boolean = true,
    val cookiesFile: String = "",
    val browserCookies: String = "Kapali",
    val restrictNames: Boolean = false,
    val playlistItems: String = "",
    val maxDownloads: String = "",
    val retries: String = "",
    val concurrentFragments: String = "",
    val extraArgs: String = "",
    val youtube403Fallback: Boolean = true,
    val outputDir: String = "",
    val metadata: Boolean = true,
    val thumbnail: Boolean = false,
    val subtitles: Boolean = false,
    val autoSubtitles: Boolean = false,
    val outputTemplate: String = ""
)

data class ActiveTaskState(
    val isRunning: Boolean = false,
    val status: String = "Hazir",
    val progress: Float = 0f,
    val speedText: String = "--",
    val etaText: String = "--",
    val logs: String = "Uygulama hazir.\n",
    val playlistProgressText: String = ""
)

data class FormValidationState(
    val urlsText: String = "",
    val urlValidationState: UrlValidationState = UrlValidationState.IDLE,
    val urlStatusText: String = "YouTube baglantisini yapistirin.",
    val previewTitle: String = "",
    val previewChannel: String = "",
    val previewItemCount: Int? = null,
    val sharedUrlBuffer: String = "",
    val clipTextDetected: String = "",
    val errorText: String? = null
)
