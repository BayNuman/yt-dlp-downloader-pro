package com.baynuman.ytdownloader.data

import android.content.Context
import android.util.Log
import com.yausername.ffmpeg.FFmpeg
import com.yausername.youtubedl_android.YoutubeDL
import com.yausername.youtubedl_android.YoutubeDLException
import com.yausername.youtubedl_android.YoutubeDLRequest
import java.io.File
import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject

class YtDlpRunner(
    private val appContext: Context,
    private val commandBuilder: YtDlpCommandBuilder = YtDlpCommandBuilder(),
) {
    @Volatile
    private var cancelRequested = false

    @Volatile
    private var activeProcessId: String? = null

    suspend fun run(request: DownloadRequest, onEvent: (DownloadEvent) -> Unit) = withContext(Dispatchers.IO) {
        cancelRequested = false

        val outputDir = File(request.outputDir)
        if (!outputDir.exists()) {
            outputDir.mkdirs()
        }

        val normalizedRequest = request.copy(
            urls = request.urls.map { it.trim() }.filter { it.isNotEmpty() },
            outputDir = outputDir.absolutePath,
        )
        if (normalizedRequest.urls.isEmpty()) {
            onEvent(DownloadEvent.Status("En az bir URL gir."))
            onEvent(DownloadEvent.Finished(success = false, exitCode = -1))
            return@withContext
        }

        val initError = ensureRuntimeInitialized()
        if (initError != null) {
            onEvent(DownloadEvent.LogLine("[hata] $initError\n"))
            onEvent(DownloadEvent.Status("yt-dlp baslatilamadi"))
            onEvent(DownloadEvent.Finished(success = false, exitCode = -1))
            logRunnerEvent("runtime_init_failed", level = Log.ERROR)
            return@withContext
        }

        val primaryCommand = commandBuilder.buildPrimaryCommand(normalizedRequest)
        onEvent(DownloadEvent.LogLine("$ yt-dlp ${commandBuilder.formatForLog(primaryCommand)}\n"))

        var result = runCommand(primaryCommand, normalizedRequest.urls, onEvent)
        val shouldFallback = (
            result.exitCode != 0 &&
                result.sawHttp403 &&
                !cancelRequested &&
                normalizedRequest.youtube403Fallback &&
                commandBuilder.containsYoutubeUrls(normalizedRequest.urls)
            )
        if (shouldFallback) {
            onEvent(
                DownloadEvent.LogLine(
                    "[uyari] YouTube 403 algilandi, fallback deneniyor ($YOUTUBE_FALLBACK_EXTRACTOR_ARGS).\n",
                ),
            )
            logRunnerEvent("event_403_fallback_triggered", level = Log.WARN)
            val fallbackCommand = commandBuilder.buildFallbackCommand(normalizedRequest)
            onEvent(DownloadEvent.LogLine("$ yt-dlp ${commandBuilder.formatForLog(fallbackCommand)}\n"))
            result = runCommand(fallbackCommand, normalizedRequest.urls, onEvent)
        }

        if (result.sawOutdatedWarning) {
            onEvent(DownloadEvent.LogLine("[bilgi] yt-dlp runtime guncellenebilir.\n"))
        }

        if (cancelRequested || result.canceled) {
            onEvent(DownloadEvent.Status("Iptal edildi"))
            onEvent(DownloadEvent.Finished(success = false, exitCode = result.exitCode))
            logRunnerEvent("download_canceled")
            return@withContext
        }

        if (result.exitCode == 0) {
            onEvent(DownloadEvent.Progress(1f))
            onEvent(DownloadEvent.Status("Indirme tamamlandi"))
            onEvent(DownloadEvent.Finished(success = true, exitCode = 0))
            logRunnerEvent("download_process_success")
        } else {
            if (result.sawHttp403 && commandBuilder.containsYoutubeUrls(normalizedRequest.urls)) {
                onEvent(
                    DownloadEvent.LogLine(
                        "[oneri] 403 devam ediyor: browser cookies sec veya cookies.txt kullan.\n",
                    ),
                )
                logRunnerEvent("event_403_still_failing", level = Log.WARN)
            }
            onEvent(DownloadEvent.Status("Hata olustu (kod: ${result.exitCode})"))
            onEvent(DownloadEvent.Finished(success = false, exitCode = result.exitCode))
            logRunnerEvent("download_process_failed", level = Log.ERROR)
        }
    }

    fun cancel() {
        cancelRequested = true
        activeProcessId?.let { processId ->
            YoutubeDL.getInstance().destroyProcessById(processId)
        }
    }

    private fun ensureRuntimeInitialized(): String? {
        return try {
            YoutubeDL.getInstance().init(appContext)
            FFmpeg.getInstance().init(appContext)
            null
        } catch (exc: Exception) {
            exc.message ?: "yt-dlp runtime baslatilamadi"
        }
    }

    private fun runCommand(
        commandWithUrls: List<String>,
        urls: List<String>,
        onEvent: (DownloadEvent) -> Unit,
    ): ProcessResult {
        val processId = UUID.randomUUID().toString()
        activeProcessId = processId

        var sawHttp403 = false
        var sawOutdatedWarning = false
        var canceled = false

        val options = if (urls.isEmpty()) {
            commandWithUrls
        } else {
            commandWithUrls.dropLast(urls.size)
        }
        val request = YoutubeDLRequest(urls).addCommands(options)

        try {
            val response = YoutubeDL.getInstance().execute(
                request = request,
                processId = processId,
                redirectErrorStream = true,
            ) { progress, _, line ->
                val safeLine = line ?: ""
                if (safeLine.isNotBlank()) {
                    onEvent(DownloadEvent.LogLine("$safeLine\n"))
                    if (safeLine.contains("HTTP Error 403: Forbidden")) {
                        sawHttp403 = true
                    }
                    if (safeLine.contains("older than 90 days", ignoreCase = true)) {
                        sawOutdatedWarning = true
                    }
                }
                if (progress >= 0f) {
                    onEvent(DownloadEvent.Progress((progress / 100f).coerceIn(0f, 1f)))
                }
                if (cancelRequested) {
                    YoutubeDL.getInstance().destroyProcessById(processId)
                }
            }

            val mergedLogs = buildString {
                append(response.out)
                if (response.err.isNotEmpty()) {
                    append('\n')
                    append(response.err)
                }
            }
            mergedLogs.lineSequence().forEach { line ->
                if (line.contains("HTTP Error 403: Forbidden")) {
                    sawHttp403 = true
                }
                if (line.contains("older than 90 days", ignoreCase = true)) {
                    sawOutdatedWarning = true
                }
            }

            return ProcessResult(
                exitCode = response.exitCode,
                sawHttp403 = sawHttp403,
                sawOutdatedWarning = sawOutdatedWarning,
                canceled = false,
            )
        } catch (_: YoutubeDL.CanceledException) {
            canceled = true
            return ProcessResult(
                exitCode = -1,
                sawHttp403 = sawHttp403,
                sawOutdatedWarning = sawOutdatedWarning,
                canceled = true,
            )
        } catch (exc: YoutubeDLException) {
            val text = exc.message ?: "yt-dlp calistirilamadi"
            onEvent(DownloadEvent.LogLine("[hata] $text\n"))
            if (text.contains("HTTP Error 403: Forbidden")) {
                sawHttp403 = true
            }
            if (text.contains("older than 90 days", ignoreCase = true)) {
                sawOutdatedWarning = true
            }
            return ProcessResult(
                exitCode = -1,
                sawHttp403 = sawHttp403,
                sawOutdatedWarning = sawOutdatedWarning,
                canceled = canceled,
            )
        } catch (exc: InterruptedException) {
            Thread.currentThread().interrupt()
            canceled = true
            return ProcessResult(
                exitCode = -1,
                sawHttp403 = sawHttp403,
                sawOutdatedWarning = sawOutdatedWarning,
                canceled = true,
            )
        } finally {
            activeProcessId = null
        }
    }

    private data class ProcessResult(
        val exitCode: Int,
        val sawHttp403: Boolean,
        val sawOutdatedWarning: Boolean,
        val canceled: Boolean,
    )

    private fun logRunnerEvent(event: String, level: Int = Log.INFO) {
        val payload = JSONObject()
            .put("event", event)
            .put("source", "runner")
            .put("ts", System.currentTimeMillis())
            .toString()

        when (level) {
            Log.ERROR -> Log.e(RUNNER_TAG, payload)
            Log.WARN -> Log.w(RUNNER_TAG, payload)
            else -> Log.i(RUNNER_TAG, payload)
        }
    }

    companion object {
        private const val RUNNER_TAG = "YTDownloaderRunner"
    }
}
