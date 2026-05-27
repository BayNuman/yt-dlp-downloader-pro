package com.baynuman.ytdownloader.data

import com.baynuman.ytdownloader.data.algorithms.MicroClip

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
    "OPUS (Open)",
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
    val archiveFile: String = "",
    val clips: List<MicroClip> = emptyList(),
    val wifiOnly: Boolean = false,
    val schedulerEnabled: Boolean = false,
    val schedulerTime: String = "03:00",
    val folderOrg: String = "None",
    val clipPrecise: Boolean = false,
    val taskId: String = java.util.UUID.randomUUID().toString(),
    val thumbnailPath: String? = null,
) {
    fun toJsonString(): String {
        val obj = org.json.JSONObject()
            .put("urls", org.json.JSONArray(urls))
            .put("outputDir", outputDir)
            .put("outputTemplate", outputTemplate)
            .put("executablePath", executablePath)
            .put("ffmpegLocation", ffmpegLocation)
            .put("clipPrecise", clipPrecise)
            .put("mode", mode.name)
            .put("videoPreset", videoPreset)
            .put("customVideoHeight", customVideoHeight)
            .put("videoContainer", videoContainer)
            .put("videoAudioCodec", videoAudioCodec)
            .put("audioFormat", audioFormat)
            .put("audioQualityPreset", audioQualityPreset)
            .put("playlistEnabled", playlistEnabled)
            .put("metadata", metadata)
            .put("thumbnail", thumbnail)
            .put("subtitles", subtitles)
            .put("autoSubtitles", autoSubtitles)
            .put("restrictNames", restrictNames)
            .put("playlistItems", playlistItems)
            .put("maxDownloads", maxDownloads ?: -1)
            .put("rateLimit", rateLimit)
            .put("downloadArchive", downloadArchive)
            .put("cookiesFile", cookiesFile)
            .put("browserCookies", browserCookies)
            .put("retries", retries ?: -1)
            .put("concurrentFragments", concurrentFragments ?: -1)
            .put("extraArgs", extraArgs)
            .put("youtube403Fallback", youtube403Fallback)
            .put("archiveFile", archiveFile)
            .put("wifiOnly", wifiOnly)
            .put("schedulerEnabled", schedulerEnabled)
            .put("schedulerTime", schedulerTime)
            .put("folderOrg", folderOrg)
            .put("taskId", taskId)
            .put("thumbnailPath", thumbnailPath ?: "")
        
        val clipsArray = org.json.JSONArray()
        clips.forEach { clip ->
            clipsArray.put(org.json.JSONObject()
                .put("start", clip.start.toDouble())
                .put("end", clip.end.toDouble())
                .put("title", clip.title)
            )
        }
        obj.put("clips", clipsArray)
        return obj.toString()
    }

    companion object {
        fun fromJsonString(jsonStr: String): DownloadRequest {
            val obj = org.json.JSONObject(jsonStr)
            val urlsArr = obj.getJSONArray("urls")
            val urls = mutableListOf<String>()
            for (i in 0 until urlsArr.length()) {
                urls.add(urlsArr.getString(i))
            }
            val mode = DownloadMode.valueOf(obj.getString("mode"))
            val maxD = obj.getInt("maxDownloads")
            val ret = obj.getInt("retries")
            val conc = obj.getInt("concurrentFragments")
            
            val clipsArr = obj.optJSONArray("clips")
            val clips = mutableListOf<MicroClip>()
            if (clipsArr != null) {
                for (i in 0 until clipsArr.length()) {
                    val cObj = clipsArr.getJSONObject(i)
                    clips.add(MicroClip(
                        start = cObj.getDouble("start").toFloat(),
                        end = cObj.getDouble("end").toFloat(),
                        title = cObj.getString("title")
                    ))
                }
            }

            return DownloadRequest(
                urls = urls,
                outputDir = obj.getString("outputDir"),
                outputTemplate = obj.optString("outputTemplate", DEFAULT_OUTPUT_TEMPLATE),
                executablePath = obj.optString("executablePath", "yt-dlp"),
                ffmpegLocation = obj.optString("ffmpegLocation", ""),
                mode = mode,
                videoPreset = obj.getString("videoPreset"),
                customVideoHeight = obj.getString("customVideoHeight"),
                videoContainer = obj.getString("videoContainer"),
                videoAudioCodec = obj.getString("videoAudioCodec"),
                audioFormat = obj.getString("audioFormat"),
                audioQualityPreset = obj.getString("audioQualityPreset"),
                playlistEnabled = obj.getBoolean("playlistEnabled"),
                metadata = obj.getBoolean("metadata"),
                thumbnail = obj.getBoolean("thumbnail"),
                subtitles = obj.getBoolean("subtitles"),
                autoSubtitles = obj.getBoolean("autoSubtitles"),
                restrictNames = obj.getBoolean("restrictNames"),
                playlistItems = obj.getString("playlistItems"),
                maxDownloads = if (maxD == -1) null else maxD,
                rateLimit = obj.getString("rateLimit"),
                downloadArchive = obj.getBoolean("downloadArchive"),
                cookiesFile = obj.getString("cookiesFile"),
                browserCookies = obj.getString("browserCookies"),
                retries = if (ret == -1) null else ret,
                concurrentFragments = if (conc == -1) null else conc,
                extraArgs = obj.getString("extraArgs"),
                youtube403Fallback = obj.getBoolean("youtube403Fallback"),
                archiveFile = obj.optString("archiveFile", ""),
                clips = clips,
                wifiOnly = obj.optBoolean("wifiOnly", false),
                schedulerEnabled = obj.optBoolean("schedulerEnabled", false),
                schedulerTime = obj.optString("schedulerTime", "03:00"),
                folderOrg = obj.optString("folderOrg", "None"),
                clipPrecise = obj.optBoolean("clipPrecise", false),
                taskId = obj.optString("taskId", java.util.UUID.randomUUID().toString()),
                thumbnailPath = obj.optString("thumbnailPath", "").takeIf { it.isNotEmpty() }
            )
        }
    }
}

sealed interface DownloadEvent {
    data class LogLine(val text: String) : DownloadEvent
    data class Progress(val value: Float) : DownloadEvent
    data class Status(val text: String) : DownloadEvent
    data class Finished(val success: Boolean, val exitCode: Int, val sizeBytes: Long = 0L, val filePath: String = "") : DownloadEvent
}

data class SponsorSegment(val start: Float, val end: Float, val category: String)

data class DownloadRecord(
    val id: String,
    val title: String,
    val url: String,
    val format: String,
    val downloadedAt: Long,
    val fileSizeBytes: Long,
    val thumbnailPath: String? = null
)

