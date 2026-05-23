package com.salih.ytdownloader.data

const val DEFAULT_OUTPUT_TEMPLATE = "%(title)s [%(id)s].%(ext)s"
const val YOUTUBE_FALLBACK_EXTRACTOR_ARGS = "youtube:player-client=tv"

val VIDEO_PRESET_HEIGHT = linkedMapOf(
    "Maksimum (Best)" to "Best",
    "Ultra HD (2160p)" to "2160",
    "QHD (1440p)" to "1440",
    "Full HD (1080p)" to "1080",
    "Dengeli (720p)" to "720",
    "Hizli (480p)" to "480",
    "Ekonomi (360p)" to "360",
    "Ozel" to "CUSTOM",
)

val AUDIO_PRESET_QUALITY = linkedMapOf(
    "Best" to "0",
    "Yuksek (320K)" to "320K",
    "Dengeli (192K)" to "192K",
    "Kucuk Boyut (128K)" to "128K",
)

val VIDEO_AUDIO_CODEC_OPTIONS = listOf(
    "AAC",
    "OPUS (OPEC)",
)

val BROWSER_COOKIE_SOURCES = listOf(
    "Kapali",
    "chrome",
    "edge",
    "firefox",
    "brave",
    "opera",
    "vivaldi",
)

val VIDEO_CONTAINER_OPTIONS = listOf("mp4", "mkv", "webm")
val AUDIO_FORMAT_OPTIONS = listOf("aac", "opus", "mp3", "m4a", "wav", "flac")
val VIDEO_LIMIT_OPTIONS = listOf("2160", "1440", "1080", "720", "480", "360")

enum class DownloadMode {
    VIDEO,
    AUDIO,
}

data class DownloadRequest(
    val urls: List<String>,
    val outputDir: String,
    val outputTemplate: String = DEFAULT_OUTPUT_TEMPLATE,
    val executablePath: String = "yt-dlp",
    val ffmpegLocation: String = "",
    val mode: DownloadMode = DownloadMode.VIDEO,
    val videoPreset: String = "Full HD (1080p)",
    val customVideoHeight: String = "1080",
    val videoContainer: String = "mp4",
    val videoAudioCodec: String = "AAC",
    val audioFormat: String = "aac",
    val audioQualityPreset: String = "Dengeli (192K)",
    val playlistEnabled: Boolean = true,
    val metadata: Boolean = true,
    val thumbnail: Boolean = false,
    val subtitles: Boolean = false,
    val autoSubtitles: Boolean = false,
    val restrictNames: Boolean = false,
    val playlistItems: String = "",
    val maxDownloads: Int? = null,
    val rateLimit: String = "",
    val downloadArchive: Boolean = true,
    val cookiesFile: String = "",
    val browserCookies: String = "Kapali",
    val retries: Int? = null,
    val concurrentFragments: Int? = null,
    val extraArgs: String = "",
    val youtube403Fallback: Boolean = true,
)

sealed interface DownloadEvent {
    data class LogLine(val text: String) : DownloadEvent
    data class Progress(val value: Float) : DownloadEvent
    data class Status(val text: String) : DownloadEvent
    data class Finished(val success: Boolean, val exitCode: Int) : DownloadEvent
}

data class DownloadRecord(
    val id: String,
    val title: String,
    val url: String,
    val format: String,
    val downloadedAt: Long,
    val fileSizeBytes: Long
) {
    fun toJsonObject(): org.json.JSONObject {
        return org.json.JSONObject()
            .put("id", id)
            .put("title", title)
            .put("url", url)
            .put("format", format)
            .put("downloadedAt", downloadedAt)
            .put("fileSizeBytes", fileSizeBytes)
    }

    companion object {
        fun fromJsonObject(obj: org.json.JSONObject): DownloadRecord {
            return DownloadRecord(
                id = obj.getString("id"),
                title = obj.getString("title"),
                url = obj.getString("url"),
                format = obj.getString("format"),
                downloadedAt = obj.getLong("downloadedAt"),
                fileSizeBytes = obj.getLong("fileSizeBytes")
            )
        }
    }
}

