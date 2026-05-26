package com.baynuman.ytdownloader.data

class YtDlpCommandBuilder {
    fun buildPrimaryCommand(request: DownloadRequest): List<String> {
        val cmd = mutableListOf(
            "--newline",
            "-P",
            request.outputDir,
            "-o",
            request.outputTemplate.ifBlank { DEFAULT_OUTPUT_TEMPLATE },
        )

        if (request.mode == DownloadMode.VIDEO) {
            val quality = effectiveVideoHeight(request)
            val audioCodec = request.videoAudioCodec.trim().uppercase()
            val preferredAudioSelector: String
            val secondaryAudioSelector: String
            if (audioCodec.startsWith("AAC")) {
                preferredAudioSelector = "ba[acodec^=mp4a]"
                secondaryAudioSelector = "ba[ext=m4a]"
            } else {
                preferredAudioSelector = "ba[acodec*=opus]"
                secondaryAudioSelector = "ba[ext=webm]"
            }

            val videoSelector: String
            val fallbackSelector: String
            if (quality == "Best") {
                videoSelector = "bv*"
                fallbackSelector = "b"
            } else {
                videoSelector = "bv*[height<=?$quality]"
                fallbackSelector = "b[height<=?$quality]"
            }

            val selector = buildString {
                append(videoSelector)
                append("+")
                append(preferredAudioSelector)
                append("/")
                append(videoSelector)
                append("+")
                append(secondaryAudioSelector)
                append("/")
                append(videoSelector)
                append("+ba/")
                append(fallbackSelector)
            }
            cmd += listOf("-f", selector, "--merge-output-format", request.videoContainer)
        } else {
            val audioQuality = AUDIO_PRESET_QUALITY[request.audioQualityPreset] ?: "0"
            cmd += listOf(
                "-x",
                "--audio-format",
                request.audioFormat,
                "--audio-quality",
                audioQuality,
            )
        }

        request.ffmpegLocation.trim().takeIf { it.isNotEmpty() }?.let { location ->
            cmd += listOf("--ffmpeg-location", location)
        }

        if (!request.playlistEnabled) {
            cmd += "--no-playlist"
        }
        if (request.metadata) {
            cmd += "--add-metadata"
        }
        if (request.thumbnail) {
            cmd += listOf("--write-thumbnail", "--convert-thumbnails", "jpg")
            if (request.mode == DownloadMode.AUDIO) {
                cmd += "--embed-thumbnail"
            }
        }
        if (request.subtitles) {
            cmd += listOf("--write-subs", "--sub-langs", "all,-live_chat")
        }
        if (request.autoSubtitles) {
            cmd += "--write-auto-subs"
        }
        if (request.restrictNames) {
            cmd += "--restrict-filenames"
        }

        request.playlistItems.trim().takeIf { it.isNotEmpty() }?.let {
            cmd += listOf("--playlist-items", it.replace(" ", ""))
        }
        request.maxDownloads?.let { cmd += listOf("--max-downloads", it.toString()) }
        request.rateLimit.trim().takeIf { it.isNotEmpty() }?.let {
            cmd += listOf("--limit-rate", it)
        }

        if (request.downloadArchive) {
            val archivePath = request.archiveFile.takeIf { it.isNotBlank() }
                ?: "${request.outputDir}/.downloaded_archive.txt"
            cmd += listOf("--download-archive", archivePath)
        }

        // Network I/O optimization: download only requested clip sections
        if (request.clips.isNotEmpty()) {
            val optimized = com.baynuman.ytdownloader.data.algorithms.ClipOptimizer.optimizeClipIntervals(request.clips)
            for (macro in optimized) {
                cmd += listOf("--download-sections", "*${macro.start}-${macro.end}")
            }
            cmd += "--force-keyframes-at-cuts"
        }

        request.retries?.let { cmd += listOf("--retries", it.toString()) }
        request.concurrentFragments?.let { cmd += listOf("--concurrent-fragments", it.toString()) }

        val cookiesFile = request.cookiesFile.trim()
        if (cookiesFile.isNotEmpty()) {
            cmd += listOf("--cookies", cookiesFile)
        } else {
            val browserCookies = request.browserCookies.trim().lowercase()
            if (browserCookies.isNotEmpty() && browserCookies != "kapali") {
                cmd += listOf("--cookies-from-browser", browserCookies)
            }
        }

        val extraArgs = parseExtraArgs(request.extraArgs)
        if (extraArgs.isNotEmpty()) {
            cmd += extraArgs
        }

        cmd += request.urls
        return cmd
    }

    fun buildFallbackCommand(request: DownloadRequest): List<String> {
        val primary = buildPrimaryCommand(request)
        return appendOptionsBeforeUrls(
            command = primary,
            urls = request.urls,
            options = listOf("--extractor-args", YOUTUBE_FALLBACK_EXTRACTOR_ARGS),
        )
    }

    fun containsYoutubeUrls(urls: List<String>): Boolean {
        return urls.any { url ->
            val lower = url.lowercase()
            lower.contains("youtube.com/") || lower.contains("youtu.be/")
        }
    }

    fun formatForLog(cmd: List<String>): String {
        return cmd.joinToString(" ") {
            if (it.contains(' ') || it.contains('\t')) {
                "\"$it\""
            } else {
                it
            }
        }
    }

    private fun effectiveVideoHeight(request: DownloadRequest): String {
        val selected = VIDEO_PRESET_HEIGHT[request.videoPreset] ?: "1080"
        return if (selected == "CUSTOM") request.customVideoHeight else selected
    }

    private fun appendOptionsBeforeUrls(
        command: List<String>,
        urls: List<String>,
        options: List<String>,
    ): List<String> {
        if (urls.isEmpty()) {
            return command + options
        }
        val optionArea = command.dropLast(urls.size)
        val urlArea = command.takeLast(urls.size)
        return optionArea + options + urlArea
    }

    private fun parseExtraArgs(rawArgs: String): List<String> {
        val args = rawArgs.trim()
        if (args.isEmpty()) {
            return emptyList()
        }

        val tokens = mutableListOf<String>()
        val current = StringBuilder()
        var quote: Char? = null

        fun flush() {
            if (current.isNotEmpty()) {
                tokens += current.toString()
                current.clear()
            }
        }

        args.forEach { ch ->
            when {
                quote == null && (ch == '"' || ch == '\'') -> quote = ch
                quote != null && ch == quote -> quote = null
                quote == null && ch.isWhitespace() -> flush()
                else -> current.append(ch)
            }
        }
        flush()
        return tokens
    }
}
