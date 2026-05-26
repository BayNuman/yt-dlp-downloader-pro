package com.baynuman.ytdownloader.data

import android.content.Context
import android.util.Log
import com.baynuman.ytdownloader.data.algorithms.ClipOptimizer
import com.baynuman.ytdownloader.data.algorithms.MacroClip
import com.baynuman.ytdownloader.data.algorithms.MicroClip
import com.baynuman.ytdownloader.data.storage.MediaStoreScanner
import com.yausername.ffmpeg.FFmpeg
import com.yausername.youtubedl_android.YoutubeDL
import com.yausername.youtubedl_android.YoutubeDLException
import com.yausername.youtubedl_android.YoutubeDLRequest
import java.io.File
import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject

sealed class PipelineException(message: String, cause: Throwable? = null) : Exception(message, cause) {
    class InsufficientStorageException(message: String) : PipelineException(message)
    class FFmpegSlicingException(message: String, cause: Throwable? = null) : PipelineException(message, cause)
    class YtDlpExecutionException(message: String) : PipelineException(message)
}

class YtDlpRunner(
    private val appContext: Context,
    private val commandBuilder: YtDlpCommandBuilder = YtDlpCommandBuilder(),
) {
    @Volatile
    private var cancelRequested = false

    @Volatile
    private var activeProcessId: String? = null

    @Volatile
    private var activeSubprocess: Process? = null

    suspend fun run(request: DownloadRequest, onEvent: (DownloadEvent) -> Unit): Unit = withContext(Dispatchers.IO) {
        if (cancelRequested) {
            onEvent(DownloadEvent.Status("Iptal edildi"))
            onEvent(DownloadEvent.Finished(success = false, exitCode = -1))
            return@withContext
        }
        cancelRequested = false
        activeSubprocess = null

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

        // Run the robust multi-stage pipeline
        var tempFile: File? = null
        try {
            // Stage 1: Pre-download Storage Space Check (Requires at least 100MB)
            checkStorageCapacity(normalizedRequest.outputDir, minMbRequired = 100)

            val isClipsOperation = normalizedRequest.clips.isNotEmpty()
            val macroClips = if (isClipsOperation) {
                ClipOptimizer.optimizeClipIntervals(normalizedRequest.clips)
            } else {
                emptyList()
            }

            onEvent(DownloadEvent.Status("Indirme baslatiliyor..."))
            logRunnerEvent("pipeline_start_download")

            // Stage 2: Execute core yt-dlp Download
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

            if (result.exitCode != 0) {
                if (result.sawHttp403 && commandBuilder.containsYoutubeUrls(normalizedRequest.urls)) {
                    onEvent(
                        DownloadEvent.LogLine(
                            "[oneri] 403 devam ediyor: browser cookies sec veya cookies.txt kullan.\n",
                        ),
                    )
                }
                throw PipelineException.YtDlpExecutionException("yt-dlp indirme hatasi (kod: ${result.exitCode})")
            }

            // Since yt-dlp finished successfully, let's locate the downloaded file
            val downloadedFile = findDownloadedFile(outputDir, result.lastDownloadedFilePath)
            if (downloadedFile == null || !downloadedFile.exists()) {
                throw PipelineException.YtDlpExecutionException("Indirilen dosya bulunamadi.")
            }
            tempFile = downloadedFile

            var finalSize = 0L

            // Stage 3: FFmpeg Slicing & Profiling (LeetCode 56 Consolidated Clips)
            if (isClipsOperation) {
                onEvent(DownloadEvent.Status("Videolar kesiliyor..."))
                
                // Check storage capacity for slicing (Estimated requirement: 2 * size of downloaded file)
                val expectedSizeMb = (downloadedFile.length() / (1024 * 1024)) * 2
                checkStorageCapacity(normalizedRequest.outputDir, minMbRequired = maxOf(50, expectedSizeMb))

                val microFiles = runFFmpegSlicing(downloadedFile, macroClips, onEvent)
                
                // Lossless Merge of Sliced Clips
                val mergedFile = runFFmpegConcat(microFiles, outputDir, onEvent)
                finalSize = mergedFile.length()
                
                // Cleanup sliced parts if merge was successful
                microFiles.forEach { f -> if (f.exists()) f.delete() }
                
                // Notify scan for the final merged file
                scanToMediaStore(mergedFile, onEvent)
            } else {
                finalSize = downloadedFile.length()
                // Single standard file download completion
                scanToMediaStore(downloadedFile, onEvent)
            }

            onEvent(DownloadEvent.Progress(1f))
            onEvent(DownloadEvent.Status("Indirme tamamlandi"))
            onEvent(DownloadEvent.Finished(success = true, exitCode = 0, sizeBytes = finalSize))
            logRunnerEvent("download_pipeline_success")

        } catch (e: PipelineException.InsufficientStorageException) {
            onEvent(DownloadEvent.LogLine("[hata] Disk doldu! ${e.message}\n"))
            onEvent(DownloadEvent.Status("Depolama Hatasi"))
            onEvent(DownloadEvent.Finished(success = false, exitCode = -2))
            logRunnerEvent("pipeline_storage_error", level = Log.ERROR)
        } catch (e: PipelineException.FFmpegSlicingException) {
            onEvent(DownloadEvent.LogLine("[hata] Video kesme hatasi: ${e.message}\n"))
            onEvent(DownloadEvent.Status("FFmpeg Hatasi"))
            onEvent(DownloadEvent.Finished(success = false, exitCode = -3))
            logRunnerEvent("pipeline_ffmpeg_error", level = Log.ERROR)
        } catch (e: PipelineException.YtDlpExecutionException) {
            onEvent(DownloadEvent.LogLine("[hata] Basarisiz: ${e.message}\n"))
            onEvent(DownloadEvent.Status("Indirme Hatasi"))
            onEvent(DownloadEvent.Finished(success = false, exitCode = -4))
            logRunnerEvent("pipeline_ytdlp_error", level = Log.ERROR)
        } catch (e: Exception) {
            onEvent(DownloadEvent.LogLine("[hata] Beklenmeyen hata: ${e.localizedMessage}\n"))
            onEvent(DownloadEvent.Status("Hata Olustu"))
            onEvent(DownloadEvent.Finished(success = false, exitCode = -1))
            logRunnerEvent("pipeline_unexpected_error", level = Log.ERROR)
        } finally {
            // Clean temporary master video file if we did slicing
            if (tempFile != null && tempFile.exists() && normalizedRequest.clips.isNotEmpty()) {
                tempFile.delete()
            }
        }
    }

    fun cancel() {
        cancelRequested = true
        activeProcessId?.let { processId ->
            YoutubeDL.getInstance().destroyProcessById(processId)
        }
        activeSubprocess?.destroy()
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

    private fun checkStorageCapacity(outputDir: String, minMbRequired: Long) {
        val file = File(outputDir)
        if (!file.exists()) {
            file.mkdirs()
        }
        val freeSpace = file.freeSpace // in bytes
        val freeMb = freeSpace / (1024 * 1024)
        if (freeMb < minMbRequired) {
            throw PipelineException.InsufficientStorageException(
                "Yetersiz depolama alani: $freeMb MB bos (Gereken: $minMbRequired MB)"
            )
        }
    }

    private fun findDownloadedFile(outputDir: File, parsedPath: String?): File? {
        if (parsedPath != null) {
            val file = File(parsedPath)
            val absoluteFile = if (file.isAbsolute) file else File(outputDir, parsedPath)
            if (absoluteFile.exists() && absoluteFile.isFile) {
                return absoluteFile
            }
        }
        // Resolve latest downloaded file by checking files sorted by modified date
        return outputDir.listFiles()
            ?.filter { it.isFile && !it.name.endsWith(".tmp") && !it.name.endsWith(".part") }
            ?.maxByOrNull { it.lastModified() }
    }

    private fun getFFmpegFile(): File {
        try {
            val youtubeDLClass = com.yausername.youtubedl_android.YoutubeDL::class.java
            val ffmpegPathField = youtubeDLClass.getDeclaredField("ffmpegPath")
            ffmpegPathField.isAccessible = true
            val file = ffmpegPathField.get(null) as? File
            if (file != null && file.exists()) {
                return file
            }
        } catch (e: Exception) {
            Log.w(RUNNER_TAG, "Reflection failed to resolve FFmpeg path", e)
        }

        // Multi-path fallback manual resolution
        val possiblePaths = listOf(
            File(appContext.noBackupFilesDir, "ffmpeg/ffmpeg"),
            File(appContext.noBackupFilesDir, "ffmpeg"),
            File(appContext.filesDir, "no_backup/ffmpeg/ffmpeg"),
            File(appContext.filesDir, "no_backup/ffmpeg"),
            File(appContext.filesDir, "ffmpeg/ffmpeg"),
            File(appContext.filesDir, "ffmpeg")
        )
        for (path in possiblePaths) {
            if (path.exists() && path.isFile) {
                return path
            }
        }

        return File(appContext.noBackupFilesDir, "ffmpeg/ffmpeg")
    }

    private suspend fun runFFmpegCommand(cmd: List<String>, onEvent: (DownloadEvent) -> Unit): Int = withContext(Dispatchers.IO) {
        try {
            onEvent(DownloadEvent.LogLine("$ ffmpeg ${cmd.drop(1).joinToString(" ")}\n"))
            val process = ProcessBuilder(cmd)
                .redirectErrorStream(true)
                .start()
            
            activeSubprocess = process
            
            process.inputStream.bufferedReader().use { reader ->
                var line: String?
                while (reader.readLine().also { line = it } != null) {
                    if (cancelRequested) {
                        process.destroy()
                        break
                    }
                    onEvent(DownloadEvent.LogLine("[ffmpeg] $line\n"))
                }
            }
            
            val exitCode = process.waitFor()
            activeSubprocess = null
            exitCode
        } catch (e: Exception) {
            onEvent(DownloadEvent.LogLine("[hata] ffmpeg hatasi: ${e.message}\n"))
            -1
        }
    }

    private suspend fun runFFmpegSlicing(
        downloadedFile: File,
        macroClips: List<MacroClip>,
        onEvent: (DownloadEvent) -> Unit
    ): List<File> {
        val ffmpegBin = getFFmpegFile()
        if (!ffmpegBin.exists()) {
            throw PipelineException.FFmpegSlicingException("FFmpeg binary dosyasi bulunamadi: ${ffmpegBin.absolutePath}")
        }

        val slicedFiles = mutableListOf<File>()
        var clipIndex = 1

        for (macro in macroClips) {
            for (micro in macro.subClips) {
                if (cancelRequested) break
                
                val ext = downloadedFile.extension
                val nameWithoutExt = downloadedFile.nameWithoutExtension
                val slicedFile = File(downloadedFile.parentFile, "${nameWithoutExt}_slice_${clipIndex}.$ext")
                
                val duration = micro.end - micro.start
                onEvent(DownloadEvent.LogLine("[slicing] Klip $clipIndex kesiliyor: ${micro.start}s - ${micro.end}s (Sure: ${duration}s)\n"))
                
                // Execute seeking & lossless slicing
                val cmd = listOf(
                    ffmpegBin.absolutePath,
                    "-y",
                    "-ss", micro.start.toString(),
                    "-t", duration.toString(),
                    "-i", downloadedFile.absolutePath,
                    "-c", "copy",
                    slicedFile.absolutePath
                )
                
                val exitCode = runFFmpegCommand(cmd, onEvent)
                if (exitCode != 0 || !slicedFile.exists()) {
                    throw PipelineException.FFmpegSlicingException("Klip $clipIndex kesme islemi basarisiz oldu.")
                }
                
                slicedFiles.add(slicedFile)
                clipIndex++
            }
        }
        
        return slicedFiles
    }

    private suspend fun runFFmpegConcat(
        slicedFiles: List<File>,
        outputDir: File,
        onEvent: (DownloadEvent) -> Unit
    ): File {
        if (slicedFiles.isEmpty()) {
            throw PipelineException.FFmpegSlicingException("Birlestirilecek dilim bulunamadi.")
        }
        if (slicedFiles.size == 1) {
            // No merge needed, just rename
            val finalFile = File(outputDir, slicedFiles[0].name.replace(Regex("_slice_\\d+"), "_merged"))
            slicedFiles[0].renameTo(finalFile)
            return finalFile
        }

        val ffmpegBin = getFFmpegFile()
        val ext = slicedFiles[0].extension
        val firstSlicedName = slicedFiles[0].nameWithoutExtension
        val finalFile = File(outputDir, firstSlicedName.replace(Regex("_slice_\\d+"), "_merged") + ".$ext")
        
        // Write the demux list file
        val listFile = File(outputDir, "concat_list_${UUID.randomUUID()}.txt")
        listFile.bufferedWriter().use { writer ->
            for (file in slicedFiles) {
                // Escape simple quotes for FFmpeg demuxer spec
                val escapedPath = file.absolutePath.replace("'", "\\'")
                writer.write("file '$escapedPath'\n")
            }
        }

        try {
            onEvent(DownloadEvent.LogLine("[concat] Dilimler kayipsiz birlestiriliyor...\n"))
            val cmd = listOf(
                ffmpegBin.absolutePath,
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", listFile.absolutePath,
                "-c", "copy",
                finalFile.absolutePath
            )
            
            val exitCode = runFFmpegCommand(cmd, onEvent)
            if (exitCode != 0 || !finalFile.exists()) {
                throw PipelineException.FFmpegSlicingException("Klipler lossless birlestirilemedi.")
            }
        } finally {
            if (listFile.exists()) listFile.delete()
        }

        return finalFile
    }

    private fun scanToMediaStore(file: File, onEvent: (DownloadEvent) -> Unit) {
        onEvent(DownloadEvent.LogLine("[storage] MediaStore taramasi tetikleniyor: ${file.absolutePath}\n"))
        MediaStoreScanner.scanFile(appContext, file.absolutePath) { uri ->
            if (uri != null) {
                onEvent(DownloadEvent.LogLine("[storage] Medya veritabani tarandi. Uri: $uri\n"))
            } else {
                onEvent(DownloadEvent.LogLine("[storage] MediaStore taramasi basarisiz.\n"))
            }
        }
    }

    private fun parsePathFromLine(line: String): String? {
        return when {
            line.contains("[download] Destination: ") -> {
                line.substringAfter("[download] Destination: ").trim()
            }
            line.contains(" has already been downloaded") && line.contains("[download] ") -> {
                line.substringAfter("[download] ").substringBefore(" has already been downloaded").trim()
            }
            line.contains("[Merger] Merging formats into \"") -> {
                line.substringAfter("[Merger] Merging formats into \"").substringBefore("\"").trim()
            }
            line.contains("[VideoConvertor] Converting video from") && line.contains(" to \"") -> {
                line.substringAfter(" to \"").substringBefore("\"").trim()
            }
            line.contains("[ExtractAudio] Destination: ") -> {
                line.substringAfter("[ExtractAudio] Destination: ").trim()
            }
            else -> null
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
        var lastDownloadedFilePath: String? = null

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
                    val parsedPath = parsePathFromLine(safeLine)
                    if (parsedPath != null) {
                        lastDownloadedFilePath = parsedPath
                    }
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
                val parsedPath = parsePathFromLine(line)
                if (parsedPath != null) {
                    lastDownloadedFilePath = parsedPath
                }
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
                lastDownloadedFilePath = lastDownloadedFilePath,
            )
        } catch (_: YoutubeDL.CanceledException) {
            canceled = true
            return ProcessResult(
                exitCode = -1,
                sawHttp403 = sawHttp403,
                sawOutdatedWarning = sawOutdatedWarning,
                canceled = true,
                lastDownloadedFilePath = lastDownloadedFilePath,
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
                lastDownloadedFilePath = lastDownloadedFilePath,
            )
        } catch (exc: InterruptedException) {
            Thread.currentThread().interrupt()
            canceled = true
            return ProcessResult(
                exitCode = -1,
                sawHttp403 = sawHttp403,
                sawOutdatedWarning = sawOutdatedWarning,
                canceled = true,
                lastDownloadedFilePath = lastDownloadedFilePath,
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
        val lastDownloadedFilePath: String? = null,
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
        private const val YOUTUBE_FALLBACK_EXTRACTOR_ARGS = "youtube:player-client=tv"
    }
}
