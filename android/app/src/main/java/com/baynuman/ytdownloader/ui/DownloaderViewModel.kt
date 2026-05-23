package com.baynuman.ytdownloader.ui

import android.app.Application
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Environment
import android.provider.DocumentsContract
import android.util.Log
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.baynuman.ytdownloader.data.BROWSER_COOKIE_SOURCES
import com.baynuman.ytdownloader.data.BinaryInstaller
import com.baynuman.ytdownloader.data.DEFAULT_OUTPUT_TEMPLATE
import com.baynuman.ytdownloader.data.DownloadEvent
import com.baynuman.ytdownloader.data.DownloadMode
import com.baynuman.ytdownloader.data.DownloadRequest
import com.baynuman.ytdownloader.data.UrlPreview
import com.baynuman.ytdownloader.data.UrlPreviewResolver
import com.baynuman.ytdownloader.data.YtDlpRunner
import java.io.File
import java.io.IOException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import android.os.Build
import com.baynuman.ytdownloader.data.DownloadRecord

enum class UrlValidationState {
    IDLE,
    LOADING,
    VALID,
    PLAYLIST,
    INVALID,
    ERROR,
}

data class DownloaderUiState(
    val urlsText: String = "",
    val outputDir: String = "",
    val outputTemplate: String = DEFAULT_OUTPUT_TEMPLATE,
    val executablePath: String = "internal://youtubedl-android",
    val ffmpegLocation: String = "",
    val binaryStatus: String = "yt-dlp otomatik hazirlaniyor...",
    val detectedAbi: String = "",
    val mediaPermissionsGranted: Boolean = false,
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
    val maxDownloads: String = "",
    val rateLimit: String = "",
    val downloadArchive: Boolean = true,
    val showAdvanced: Boolean = false,
    val showDiagnostics: Boolean = false,
    val showFullOutputPath: Boolean = false,
    val cookiesFile: String = "",
    val browserCookies: String = BROWSER_COOKIE_SOURCES.first(),
    val retries: String = "",
    val concurrentFragments: String = "",
    val extraArgs: String = "",
    val youtube403Fallback: Boolean = true,
    val urlValidationState: UrlValidationState = UrlValidationState.IDLE,
    val urlStatusText: String = "YouTube baglantisini yapistirin.",
    val previewTitle: String = "",
    val previewChannel: String = "",
    val previewItemCount: Int? = null,
    val sharedUrlBuffer: String = "",
    val status: String = "Hazir",
    val progress: Float = 0f,
    val speedText: String = "--",
    val etaText: String = "--",
    val playlistProgressText: String = "",
    val logs: String = "Uygulama hazir.\n",
    val isRunning: Boolean = false,
    val errorText: String? = null,
    
    // Modernized UI properties
    val currentLanguage: String = "en",
    val isDarkTheme: Boolean = true,
    val isBatchMode: Boolean = false,
    val clipTextDetected: String = "",
    val activeTab: Int = 0,
    val historyRecords: List<DownloadRecord> = emptyList(),
)

class DownloaderViewModel(application: Application) : AndroidViewModel(application) {
    private val appContext = application.applicationContext
    private val prefs = appContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    private val runner = YtDlpRunner(appContext)
    private val binaryInstaller = BinaryInstaller(appContext)
    private val previewResolver = UrlPreviewResolver(appContext)
    private val _uiState = MutableStateFlow(buildInitialState(application))
    private var previewJob: Job? = null

    val uiState: StateFlow<DownloaderUiState> = _uiState.asStateFlow()

    init {
        bootstrapEmbeddedBinaries()
        loadHistory()
    }

    private fun buildInitialState(application: Application): DownloaderUiState {
        val fallbackOutputDir = application
            .getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS)
            ?.resolve("yt-downloads")
            ?.absolutePath
            ?: application.filesDir.resolve("yt-downloads").absolutePath
        val savedOutputDir = prefs.getString(KEY_OUTPUT_DIR, null)?.trim().orEmpty()
        val outputDir = if (savedOutputDir.isNotBlank()) {
            savedOutputDir
        } else {
            fallbackOutputDir
        }
        
        val savedLang = prefs.getString("current_language", "en") ?: "en"
        val savedTheme = prefs.getBoolean("is_dark_theme", true)

        return DownloaderUiState(
            outputDir = outputDir,
            currentLanguage = savedLang,
            isDarkTheme = savedTheme
        )
    }

    fun updateLanguage(value: String) {
        updateState { copy(currentLanguage = value) }
        prefs.edit().putString("current_language", value).apply()
        telemetry("language_changed_$value")
    }

    fun toggleTheme() {
        val next = !_uiState.value.isDarkTheme
        updateState { copy(isDarkTheme = next) }
        prefs.edit().putBoolean("is_dark_theme", next).apply()
        telemetry("theme_changed_${if (next) "dark" else "light"}")
    }

    fun toggleBatchMode() {
        val next = !_uiState.value.isBatchMode
        updateState { copy(isBatchMode = next) }
        telemetry("batch_mode_changed_$next")
    }

    fun removeUrlFromBatch(index: Int) {
        val urls = parseUrls(_uiState.value.urlsText)
        if (index in urls.indices) {
            val updatedUrls = urls.toMutableList().apply { removeAt(index) }
            val nextText = updatedUrls.joinToString("\n")
            updateUrlsText(nextText)
        }
    }

    fun checkClipboardForYoutubeLink() {
        try {
            val clipboard = appContext.getSystemService(Context.CLIPBOARD_SERVICE) as? ClipboardManager
            val pasted = clipboard
                ?.primaryClip
                ?.getItemAt(0)
                ?.coerceToText(appContext)
                ?.toString()
                ?.trim()
                .orEmpty()
            if (pasted.isNotEmpty() && isLikelyYoutubeUrl(pasted) && !pasted.contains(_uiState.value.urlsText.trim())) {
                updateState { copy(clipTextDetected = pasted) }
            } else {
                updateState { copy(clipTextDetected = "") }
            }
        } catch (_: Exception) {
            updateState { copy(clipTextDetected = "") }
        }
    }

    fun pasteDetectedClipboardUrl() {
        val detected = _uiState.value.clipTextDetected
        if (detected.isNotEmpty()) {
            val current = _uiState.value.urlsText.trim()
            val nextText = if (current.isEmpty()) {
                detected
            } else {
                if (_uiState.value.isBatchMode) {
                    "$current\n$detected"
                } else {
                    detected
                }
            }
            updateUrlsText(nextText)
            updateState { copy(clipTextDetected = "") }
        }
    }

    fun updateUrlsText(value: String) {
        updateState { copy(urlsText = value, errorText = null) }
        schedulePreview(value)
    }

    fun clearUrl() {
        previewJob?.cancel()
        updateState {
            copy(
                urlsText = "",
                urlValidationState = UrlValidationState.IDLE,
                urlStatusText = "YouTube baglantisini yapistirin.",
                previewTitle = "",
                previewChannel = "",
                previewItemCount = null,
                errorText = null,
            )
        }
    }

    fun pasteUrlFromClipboard() {
        val clipboard = appContext.getSystemService(Context.CLIPBOARD_SERVICE) as? ClipboardManager
        val pasted = clipboard
            ?.primaryClip
            ?.getItemAt(0)
            ?.coerceToText(appContext)
            ?.toString()
            ?.trim()
            .orEmpty()

        if (pasted.isEmpty()) {
            updateState { copy(errorText = "Panoda baglanti bulunamadi.") }
            return
        }
        updateUrlsText(pasted)
    }

    fun updateOutputDir(value: String) {
        val sanitized = value.trim()
        updateState { copy(outputDir = sanitized) }
        if (sanitized.isNotEmpty()) {
            persistOutputDir(sanitized)
        }
    }
    fun updateOutputTemplate(value: String) = updateState { copy(outputTemplate = value) }
    fun updateExecutablePath(value: String) = updateState { copy(executablePath = value) }
    fun updateFfmpegLocation(value: String) = updateState { copy(ffmpegLocation = value) }
    fun updateMode(value: DownloadMode) = updateState { copy(mode = value) }
    fun updateVideoPreset(value: String) = updateState { copy(videoPreset = value) }
    fun updateCustomVideoHeight(value: String) = updateState { copy(customVideoHeight = value) }
    fun updateVideoContainer(value: String) = updateState { copy(videoContainer = value) }
    fun updateVideoAudioCodec(value: String) = updateState { copy(videoAudioCodec = value) }
    fun updateAudioFormat(value: String) = updateState { copy(audioFormat = value) }
    fun updateAudioQualityPreset(value: String) = updateState { copy(audioQualityPreset = value) }
    fun updatePlaylistEnabled(value: Boolean) = updateState { copy(playlistEnabled = value) }
    fun updateMetadata(value: Boolean) = updateState { copy(metadata = value) }
    fun updateThumbnail(value: Boolean) = updateState { copy(thumbnail = value) }
    fun updateSubtitles(value: Boolean) = updateState { copy(subtitles = value) }
    fun updateAutoSubtitles(value: Boolean) = updateState { copy(autoSubtitles = value) }
    fun updateRestrictNames(value: Boolean) = updateState { copy(restrictNames = value) }
    fun updatePlaylistItems(value: String) = updateState { copy(playlistItems = value) }
    fun updateMaxDownloads(value: String) = updateState { copy(maxDownloads = value) }
    fun updateRateLimit(value: String) = updateState { copy(rateLimit = value) }
    fun updateDownloadArchive(value: Boolean) = updateState { copy(downloadArchive = value) }
    fun updateShowAdvanced(value: Boolean) = updateState { copy(showAdvanced = value) }
    fun toggleDiagnostics() = updateState { copy(showDiagnostics = !showDiagnostics) }
    fun toggleFullOutputPath() = updateState { copy(showFullOutputPath = !showFullOutputPath) }
    fun updateCookiesFile(value: String) = updateState { copy(cookiesFile = value) }
    fun updateBrowserCookies(value: String) = updateState { copy(browserCookies = value) }
    fun updateRetries(value: String) = updateState { copy(retries = value) }
    fun updateConcurrentFragments(value: String) = updateState { copy(concurrentFragments = value) }
    fun updateExtraArgs(value: String) = updateState { copy(extraArgs = value) }
    fun updateYoutube403Fallback(value: Boolean) = updateState { copy(youtube403Fallback = value) }
    fun updateMediaPermissionsStatus(value: Boolean) {
        val previous = _uiState.value.mediaPermissionsGranted
        updateState { copy(mediaPermissionsGranted = value) }
        if (value && !previous) {
            telemetry("permission_granted")
        } else if (!value && previous) {
            telemetry("permission_missing")
        }
    }

    fun setIncomingSharedText(sharedText: String?) {
        val incoming = extractFirstUrl(sharedText.orEmpty()) ?: return
        updateState { copy(sharedUrlBuffer = incoming) }
        telemetry("share_url_received")
        updateActiveTab(0) // Automatically select the Downloader tab
        if (_uiState.value.urlsText.isBlank()) {
            updateUrlsText(incoming)
            appendLog("[bilgi] Paylasilan baglanti alindi.\n")
        }
    }

    fun importFromSharedBuffer() {
        val shared = _uiState.value.sharedUrlBuffer
        if (shared.isBlank()) {
            updateState { copy(errorText = "Paylasimdan alinacak baglanti bulunamadi.") }
            return
        }
        updateUrlsText(shared)
    }

    fun useDefaultOutputDir() {
        val app = getApplication<Application>()
        val defaultOutputDir = app
            .getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS)
            ?.resolve("yt-downloads")
            ?.absolutePath
            ?: app.filesDir.resolve("yt-downloads").absolutePath
        updateState { copy(outputDir = defaultOutputDir) }
        persistOutputDir(defaultOutputDir)
    }

    fun updateOutputDirFromTreeUri(uri: Uri?) {
        if (uri == null) {
            return
        }
        takePersistableTreePermission(uri)
        val resolvedPath = resolvePathFromTreeUri(uri)
        if (resolvedPath == null) {
            updateState {
                copy(
                    errorText = "Bu klasor desteklenmiyor. Download veya Documents altindan bir klasor secin.",
                )
            }
            telemetry("output_folder_unsupported")
            return
        }

        val folder = File(resolvedPath)
        if (!folder.exists()) {
            folder.mkdirs()
        }
        updateState {
            copy(
                outputDir = folder.absolutePath,
                showFullOutputPath = true,
                errorText = null,
            )
        }
        persistOutputDir(folder.absolutePath)
        appendLog("[bilgi] Indirme konumu guncellendi: ${folder.absolutePath}\n")
        telemetry("output_folder_changed")
    }

    fun refreshEmbeddedBinary() {
        bootstrapEmbeddedBinaries(forceUpdate = true)
    }

    fun clearLogs() {
        updateState { copy(logs = "", errorText = null) }
    }

    fun importCookiesFromUri(uri: Uri?) {
        if (uri == null) {
            return
        }
        viewModelScope.launch {
            val app = getApplication<Application>()
            val destination = File(app.filesDir, "cookies/cookies.txt").apply {
                parentFile?.mkdirs()
            }
            val copied = copyUriToFile(uri, destination)
            if (copied) {
                updateState { copy(cookiesFile = destination.absolutePath, showAdvanced = true, errorText = null) }
                appendLog("[bilgi] Cookies dosyasi ice aktarildi: ${destination.absolutePath}\n")
            } else {
                updateState { copy(errorText = "Cookies dosyasi okunamadi.") }
            }
        }
    }

    fun importYtDlpBinaryFromUri(uri: Uri?) {
        if (uri == null) {
            return
        }
        viewModelScope.launch {
            val app = getApplication<Application>()
            val destination = File(app.filesDir, "bin/yt-dlp").apply {
                parentFile?.mkdirs()
            }
            val copied = copyUriToFile(uri, destination)
            if (copied) {
                destination.setExecutable(true, false)
                updateState {
                    copy(
                        executablePath = destination.absolutePath,
                        ffmpegLocation = destination.parentFile?.absolutePath ?: ffmpegLocation,
                        binaryStatus = "yt-dlp dosya secici ile guncellendi.",
                        errorText = null,
                        showDiagnostics = true,
                    )
                }
                appendLog("[bilgi] yt-dlp binary guncellendi: ${destination.absolutePath}\n")
            } else {
                updateState { copy(errorText = "yt-dlp binary okunamadi.") }
            }
        }
    }

    fun cancelDownload() {
        if (!_uiState.value.isRunning) {
            return
        }
        runner.cancel()
        appendLog("[bilgi] Duraklatma/iptal istegi gonderildi.\n")
        updateState { copy(status = "Duraklatiliyor...") }
    }

    fun startDownload() {
        val state = _uiState.value
        if (state.isRunning) {
            return
        }

        val validationError = validate(state)
        if (validationError != null) {
            updateState { copy(errorText = validationError, status = "Hazir") }
            telemetry("start_download_blocked")
            return
        }

        val urls = parseUrls(state.urlsText)
        val request = DownloadRequest(
            urls = urls,
            outputDir = state.outputDir,
            outputTemplate = state.outputTemplate,
            executablePath = state.executablePath,
            ffmpegLocation = state.ffmpegLocation,
            mode = state.mode,
            videoPreset = state.videoPreset,
            customVideoHeight = state.customVideoHeight,
            videoContainer = state.videoContainer,
            videoAudioCodec = state.videoAudioCodec,
            audioFormat = state.audioFormat,
            audioQualityPreset = state.audioQualityPreset,
            playlistEnabled = state.playlistEnabled,
            metadata = state.metadata,
            thumbnail = state.thumbnail,
            subtitles = state.subtitles,
            autoSubtitles = state.autoSubtitles,
            restrictNames = state.restrictNames,
            playlistItems = state.playlistItems,
            maxDownloads = state.maxDownloads.trim().toIntOrNull(),
            rateLimit = state.rateLimit,
            downloadArchive = state.downloadArchive,
            cookiesFile = state.cookiesFile,
            browserCookies = state.browserCookies,
            retries = state.retries.trim().toIntOrNull(),
            concurrentFragments = state.concurrentFragments.trim().toIntOrNull(),
            extraArgs = state.extraArgs,
            youtube403Fallback = state.youtube403Fallback,
        )

        updateState {
            copy(
                isRunning = true,
                status = "Indirme baslatildi",
                progress = 0f,
                speedText = "--",
                etaText = "--",
                playlistProgressText = "",
                errorText = null,
            )
        }
        telemetry("start_download")

        val firstUrl = extractFirstUrl(state.urlsText) ?: ""
        val activeTitle = if (state.previewTitle.isNotBlank()) state.previewTitle else firstUrl
        startForegroundDownloadService(activeTitle)

        viewModelScope.launch {
            runner.run(request) { event ->
                when (event) {
                    is DownloadEvent.LogLine -> handleLogLine(event.text)
                    is DownloadEvent.Progress -> {
                        val progressVal = event.value.coerceIn(0f, 1f)
                        updateState { copy(progress = progressVal) }
                        
                        val percentage = (progressVal * 100).toInt()
                        updateForegroundDownloadService(
                            title = if (_uiState.value.previewTitle.isNotBlank()) _uiState.value.previewTitle else "yt-dlp",
                            progress = percentage,
                            speed = _uiState.value.speedText,
                            eta = _uiState.value.etaText
                        )
                    }
                    is DownloadEvent.Status -> updateState { copy(status = event.text) }
                    is DownloadEvent.Finished -> {
                        updateState {
                            copy(
                                isRunning = false,
                                status = if (event.success) "Tamamlandi" else this.status,
                                speedText = if (event.success) "Tamamlandi" else "--",
                                etaText = if (event.success) "00:00" else "--",
                            )
                        }
                        
                        stopForegroundDownloadService()
                        
                        if (event.success) {
                            val finalTitle = if (_uiState.value.previewTitle.isNotBlank()) _uiState.value.previewTitle else firstUrl
                            addToHistory(
                                title = finalTitle,
                                url = firstUrl,
                                format = if (state.mode == DownloadMode.VIDEO) state.videoContainer else state.audioFormat,
                                sizeBytes = 0L
                            )
                            telemetry("download_completed")
                        } else {
                            telemetry("download_failed")
                        }
                    }
                }
            }
        }
    }

    private fun schedulePreview(rawInput: String) {
        previewJob?.cancel()
        val url = extractFirstUrl(rawInput)
        if (url == null) {
            updateState {
                copy(
                    urlValidationState = UrlValidationState.IDLE,
                    urlStatusText = "YouTube baglantisini yapistirin.",
                    previewTitle = "",
                    previewChannel = "",
                    previewItemCount = null,
                )
            }
            return
        }

        if (!isLikelyYoutubeUrl(url)) {
            updateState {
                copy(
                    urlValidationState = UrlValidationState.INVALID,
                    urlStatusText = "Baglanti gecersiz. YouTube URL girin.",
                    previewTitle = "",
                    previewChannel = "",
                    previewItemCount = null,
                )
            }
            telemetry("url_invalid")
            return
        }

        previewJob = viewModelScope.launch {
            delay(450)
            updateState {
                copy(
                    urlValidationState = UrlValidationState.LOADING,
                    urlStatusText = "Baglanti kontrol ediliyor...",
                    previewTitle = "",
                    previewChannel = "",
                    previewItemCount = null,
                )
            }

            val result = withContext(Dispatchers.IO) {
                runCatching { previewResolver.resolve(url) }
            }
            result.onSuccess { preview -> applyPreview(preview) }
                .onFailure { exc ->
                    updateState {
                        copy(
                            urlValidationState = UrlValidationState.ERROR,
                            urlStatusText = mapPreviewError(exc.message),
                            previewTitle = "",
                            previewChannel = "",
                            previewItemCount = null,
                        )
                    }
                    telemetry("url_preview_error")
                }
        }
    }

    private fun applyPreview(preview: UrlPreview) {
        val status = if (preview.isPlaylist) {
            val countText = preview.itemCount?.let { " - $it oge" }.orEmpty()
            "Playlist algilandi$countText"
        } else {
            "Video hazir. Indirmeye baslayabilirsiniz."
        }
        updateState {
            copy(
                urlValidationState = if (preview.isPlaylist) {
                    UrlValidationState.PLAYLIST
                } else {
                    UrlValidationState.VALID
                },
                urlStatusText = status,
                previewTitle = preview.title,
                previewChannel = preview.channel,
                previewItemCount = preview.itemCount,
            )
        }
        if (preview.isPlaylist) {
            telemetry("url_valid_playlist")
        } else {
            telemetry("url_valid_video")
        }
    }

    private fun mapPreviewError(message: String?): String {
        val msg = message.orEmpty().lowercase()
        return when {
            msg.contains("unsupported url") || msg.contains("invalid") ->
                "Baglanti gecersiz."
            msg.contains("private") || msg.contains("members-only") || msg.contains("sign in") ->
                "Videoya erisim sinirli. Gerekirse cookies kullanin."
            msg.contains("403") ->
                "Video erisilemiyor. Uyumluluk modunu (403) deneyin."
            msg.contains("resolve host") || msg.contains("timeout") || msg.contains("timed out") ||
                msg.contains("network") || msg.contains("connection") ->
                "Baglantiya erisilemiyor. Interneti kontrol edin."
            else ->
                "Video bilgisi alinamadi. Tekrar deneyin."
        }
    }

    private fun validate(state: DownloaderUiState): String? {
        val firstUrl = extractFirstUrl(state.urlsText)
            ?: return "err_empty_url"

        if (!isLikelyYoutubeUrl(firstUrl)) {
            return "err_invalid_url"
        }
        if (state.outputTemplate.trim().isEmpty()) {
            return "err_empty_template"
        }
        if (state.outputDir.trim().isEmpty()) {
            return "err_empty_output"
        }
        val targetDir = File(state.outputDir.trim())
        if (!targetDir.exists() && !targetDir.mkdirs()) {
            return "err_write_output"
        }
        if (targetDir.exists() && !targetDir.canWrite()) {
            return "err_write_output"
        }
        if (!validateOptionalInt(state.maxDownloads, min = 1)) {
            return "err_max_dl"
        }
        if (!validateOptionalInt(state.retries, min = 0)) {
            return "err_retries"
        }
        if (!validateOptionalInt(state.concurrentFragments, min = 1)) {
            return "err_fragments"
        }
        if (state.mode == DownloadMode.VIDEO && state.videoPreset == "Ozel") {
            val customHeight = state.customVideoHeight.trim()
            if (customHeight.isEmpty() || customHeight.toIntOrNull() == null) {
                return "err_custom_res"
            }
        }
        return null
    }

    private fun bootstrapEmbeddedBinaries(forceUpdate: Boolean = false) {
        viewModelScope.launch {
            updateState {
                copy(
                    binaryStatus = "yt-dlp kontrol ediliyor...",
                    errorText = null,
                )
            }
            val result = withContext(Dispatchers.IO) {
                binaryInstaller.installOrReuse(forceUpdate = forceUpdate) { step ->
                    _uiState.update { current -> current.copy(binaryStatus = step) }
                }
            }
            updateState {
                copy(
                    executablePath = result.ytDlpPath ?: executablePath,
                    ffmpegLocation = result.ffmpegDir ?: "",
                    binaryStatus = "${result.message} (ABI: ${result.abi})",
                    detectedAbi = result.abi,
                )
            }
            appendLog("[bilgi] ${result.message} (ABI: ${result.abi})\n")
        }
    }

    private suspend fun copyUriToFile(uri: Uri, destination: File): Boolean = withContext(Dispatchers.IO) {
        return@withContext try {
            val app = getApplication<Application>()
            app.contentResolver.openInputStream(uri).use { input ->
                if (input == null) {
                    return@withContext false
                }
                destination.outputStream().use { output ->
                    input.copyTo(output)
                }
            }
            true
        } catch (_: IOException) {
            false
        } catch (_: SecurityException) {
            false
        }
    }

    private fun parseUrls(raw: String): List<String> {
        val lines = raw.lineSequence()
            .map { it.trim() }
            .filter { it.isNotEmpty() }
            .toList()
        if (lines.isNotEmpty()) {
            return lines
        }
        return listOfNotNull(extractFirstUrl(raw))
    }

    private fun persistOutputDir(path: String) {
        prefs.edit().putString(KEY_OUTPUT_DIR, path).apply()
    }

    private fun resolvePathFromTreeUri(uri: Uri): String? {
        return try {
            when (uri.authority) {
                "com.android.externalstorage.documents" -> {
                    val docId = DocumentsContract.getTreeDocumentId(uri)
                    val parts = docId.split(":")
                    if (parts.isEmpty()) {
                        return null
                    }

                    val volume = parts[0].lowercase()
                    val relative = if (parts.size > 1) parts[1] else ""
                    when (volume) {
                        "primary" -> {
                            if (relative.isBlank()) {
                                Environment.getExternalStorageDirectory().absolutePath
                            } else {
                                File(Environment.getExternalStorageDirectory(), relative).absolutePath
                            }
                        }
                        "home" -> {
                            val homeBase = File(Environment.getExternalStorageDirectory(), "Documents")
                            if (relative.isBlank()) {
                                homeBase.absolutePath
                            } else {
                                File(homeBase, relative).absolutePath
                            }
                        }
                        else -> null
                    }
                }
                "com.android.providers.downloads.documents" -> {
                    val docId = DocumentsContract.getTreeDocumentId(uri)
                    when {
                        docId.startsWith("raw:") -> docId.removePrefix("raw:")
                        docId == "downloads" -> {
                            Environment.getExternalStoragePublicDirectory(
                                Environment.DIRECTORY_DOWNLOADS,
                            ).absolutePath
                        }
                        else -> null
                    }
                }
                else -> null
            }
        } catch (_: Exception) {
            null
        }
    }

    private fun takePersistableTreePermission(uri: Uri) {
        try {
            appContext.contentResolver.takePersistableUriPermission(
                uri,
                Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION,
            )
        } catch (_: SecurityException) {
            // Some providers do not support persistable permissions.
        } catch (_: IllegalArgumentException) {
            // Uri may not expose persistable permission flags.
        }
    }

    private fun extractFirstUrl(raw: String): String? {
        return raw
            .lineSequence()
            .map { it.trim() }
            .firstOrNull { it.isNotEmpty() }
            ?: raw.trim().takeIf { it.isNotEmpty() }
    }

    private fun isLikelyYoutubeUrl(url: String): Boolean {
        val normalized = url.trim().lowercase()
        return normalized.contains("youtube.com/") || normalized.contains("youtu.be/")
    }

    private fun validateOptionalInt(raw: String, min: Int): Boolean {
        val value = raw.trim()
        if (value.isEmpty()) {
            return true
        }
        val intValue = value.toIntOrNull() ?: return false
        return intValue >= min
    }

    private fun handleLogLine(line: String) {
        appendLog(line)
        val speed = SPEED_REGEX.find(line)?.groupValues?.getOrNull(1)
        val eta = ETA_REGEX.find(line)?.groupValues?.getOrNull(1)
        val playlistProgress = PLAYLIST_REGEXES.firstNotNullOfOrNull { regex ->
            regex.find(line)?.let { match ->
                "${match.groupValues[1]}/${match.groupValues[2]}"
            }
        }
        val writeAccessError = line.contains("permission denied", ignoreCase = true) ||
            line.contains("errno 13", ignoreCase = true) ||
            line.contains("read-only file system", ignoreCase = true)

        if (writeAccessError) {
            updateState {
                copy(
                    errorText = "Klasore yazilamiyor. Indirme konumunu degistirin veya depolama izni verin.",
                    status = "Depolama hatasi",
                )
            }
            telemetry("error_storage_write_denied")
        }

        if (speed != null || eta != null || playlistProgress != null) {
            updateState {
                copy(
                    speedText = speed ?: speedText,
                    etaText = eta ?: etaText,
                    playlistProgressText = playlistProgress ?: playlistProgressText,
                )
            }
        }
    }

    fun updateActiveTab(index: Int) {
        updateState { copy(activeTab = index) }
        telemetry("tab_swapped_$index")
    }

    fun loadHistory() {
        val list = mutableListOf<com.baynuman.ytdownloader.data.DownloadRecord>()
        try {
            val jsonStr = prefs.getString("download_history", "[]") ?: "[]"
            val array = org.json.JSONArray(jsonStr)
            for (i in 0 until array.length()) {
                val obj = array.getJSONObject(i)
                list.add(com.baynuman.ytdownloader.data.DownloadRecord.fromJsonObject(obj))
            }
        } catch (_: Exception) {}
        updateState { copy(historyRecords = list.sortedByDescending { it.downloadedAt }) }
    }

    fun addToHistory(title: String, url: String, format: String, sizeBytes: Long) {
        val id = java.util.UUID.randomUUID().toString()
        val record = com.baynuman.ytdownloader.data.DownloadRecord(
            id = id,
            title = title,
            url = url,
            format = format,
            downloadedAt = System.currentTimeMillis(),
            fileSizeBytes = sizeBytes
        )
        val currentList = _uiState.value.historyRecords.toMutableList()
        currentList.add(record)
        
        try {
            val array = org.json.JSONArray()
            currentList.forEach { array.put(it.toJsonObject()) }
            prefs.edit().putString("download_history", array.toString()).apply()
        } catch (_: Exception) {}
        
        updateState { copy(historyRecords = currentList.sortedByDescending { it.downloadedAt }) }
    }

    fun clearHistory() {
        prefs.edit().remove("download_history").apply()
        updateState { copy(historyRecords = emptyList()) }
        telemetry("history_cleared")
    }

    private fun startForegroundDownloadService(title: String) {
        try {
            val intent = Intent(appContext, com.baynuman.ytdownloader.service.DownloadService::class.java).apply {
                action = com.baynuman.ytdownloader.service.DownloadService.ACTION_START
                putExtra(com.baynuman.ytdownloader.service.DownloadService.EXTRA_TITLE, title)
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                appContext.startForegroundService(intent)
            } else {
                appContext.startService(intent)
            }
        } catch (_: Exception) {}
    }

    private fun updateForegroundDownloadService(title: String, progress: Int, speed: String, eta: String) {
        try {
            val intent = Intent(appContext, com.baynuman.ytdownloader.service.DownloadService::class.java).apply {
                action = com.baynuman.ytdownloader.service.DownloadService.ACTION_UPDATE
                putExtra(com.baynuman.ytdownloader.service.DownloadService.EXTRA_TITLE, title)
                putExtra(com.baynuman.ytdownloader.service.DownloadService.EXTRA_PROGRESS, progress)
                putExtra(com.baynuman.ytdownloader.service.DownloadService.EXTRA_SPEED, speed)
                putExtra(com.baynuman.ytdownloader.service.DownloadService.EXTRA_ETA, eta)
            }
            appContext.startService(intent)
        } catch (_: Exception) {}
    }

    private fun stopForegroundDownloadService() {
        try {
            val intent = Intent(appContext, com.baynuman.ytdownloader.service.DownloadService::class.java).apply {
                action = com.baynuman.ytdownloader.service.DownloadService.ACTION_STOP
            }
            appContext.startService(intent)
        } catch (_: Exception) {}
    }

    private fun appendLog(line: String) {
        _uiState.update { current ->
            val next = (current.logs + line).takeLast(24_000)
            current.copy(logs = next)
        }
    }

    private inline fun updateState(block: DownloaderUiState.() -> DownloaderUiState) {
        _uiState.update { current -> current.block() }
    }

    private fun telemetry(event: String) {
        val payload = JSONObject()
            .put("event", event)
            .put("source", "ui")
            .put("ts", System.currentTimeMillis())
            .toString()
        Log.i(TELEMETRY_TAG, payload)
    }

    companion object {
        private const val TELEMETRY_TAG = "YTDownloaderTelemetry"
        private const val PREFS_NAME = "downloader_ui"
        private const val KEY_OUTPUT_DIR = "output_dir"
        private val SPEED_REGEX = Regex("""\bat\s+([0-9.]+\s*[KMGT]?i?B/s)""", RegexOption.IGNORE_CASE)
        private val ETA_REGEX = Regex("""ETA\s+([0-9:]+)""", RegexOption.IGNORE_CASE)
        private val PLAYLIST_REGEXES = listOf(
            Regex("""item\s+(\d+)\s+of\s+(\d+)""", RegexOption.IGNORE_CASE),
            Regex("""downloading\s+item\s+(\d+)\s+of\s+(\d+)""", RegexOption.IGNORE_CASE),
            Regex("""\[(\d+)\s*/\s*(\d+)\]""", RegexOption.IGNORE_CASE),
        )
    }
}
