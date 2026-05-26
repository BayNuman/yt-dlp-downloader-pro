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
import com.baynuman.ytdownloader.data.DownloadRecord
import com.baynuman.ytdownloader.data.DownloadPreferencesState
import com.baynuman.ytdownloader.data.ActiveTaskState
import com.baynuman.ytdownloader.data.FormValidationState
import com.baynuman.ytdownloader.data.UrlPreview
import com.baynuman.ytdownloader.data.UrlPreviewResolver
import com.baynuman.ytdownloader.data.YtDlpRunner
import com.baynuman.ytdownloader.data.db.DownloadDatabase
import com.baynuman.ytdownloader.data.db.DownloadRecordEntity
import java.io.File
import java.io.IOException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

import android.os.Build

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

data class RuntimeState(
    val historyRecords: List<DownloadRecord> = emptyList(),
    val activeTab: Int = 0,
    val isDarkTheme: Boolean = true,
    val currentLanguage: String = "en",
    val binaryStatus: String = "yt-dlp otomatik hazirlaniyor...",
    val detectedAbi: String = "",
    val executablePath: String = "internal://youtubedl-android",
    val ffmpegLocation: String = "",
    val mediaPermissionsGranted: Boolean = false,
    val showDiagnostics: Boolean = false,
    val showFullOutputPath: Boolean = false,
)

class DownloaderViewModel(application: Application) : AndroidViewModel(application) {
    private val appContext = application.applicationContext
    private val prefs = appContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    private var lastStartedUrl: String = ""
    private val binaryInstaller = BinaryInstaller(appContext)
    private val previewResolver = UrlPreviewResolver(appContext)
    private var previewJob: Job? = null

    // Room database Single Source of Truth for History
    private val database = DownloadDatabase.getDatabase(appContext)
    private val recordDao = database.downloadRecordDao()

    // 1. Atomic Domain States Flow Decompositions
    private val _preferencesState = MutableStateFlow(buildInitialPreferencesState(application))
    val preferencesState = _preferencesState.asStateFlow()

    private val _activeTaskState = MutableStateFlow(ActiveTaskState())
    val activeTaskState = _activeTaskState.asStateFlow()

    private val _formValidationState = MutableStateFlow(FormValidationState())
    val formValidationState = _formValidationState.asStateFlow()

    // Consolidated runtime state
    private val _runtimeState = MutableStateFlow(
        RuntimeState(
            isDarkTheme = prefs.getBoolean("is_dark_theme", true),
            currentLanguage = prefs.getString("current_language", null)
                ?: java.util.Locale.getDefault().language.takeIf { it in listOf("tr", "es") }
                ?: "en"
        )
    )

    // 2. High-performance Selector Unified Flow for Backward Compatibility
    val uiState: StateFlow<DownloaderUiState> = combine(
        _preferencesState,
        _activeTaskState,
        _formValidationState,
        _runtimeState
    ) { prefs, task, validation, runtime ->
        DownloaderUiState(
            urlsText = validation.urlsText,
            outputDir = prefs.outputDir,
            outputTemplate = prefs.outputTemplate,
            executablePath = runtime.executablePath,
            ffmpegLocation = runtime.ffmpegLocation,
            binaryStatus = runtime.binaryStatus,
            detectedAbi = runtime.detectedAbi,
            mediaPermissionsGranted = runtime.mediaPermissionsGranted,
            mode = prefs.mode,
            videoPreset = prefs.videoPreset,
            customVideoHeight = prefs.customVideoHeight,
            videoContainer = prefs.videoContainer,
            videoAudioCodec = prefs.videoAudioCodec,
            audioFormat = prefs.audioFormat,
            audioQualityPreset = prefs.audioQualityPreset,
            playlistEnabled = prefs.playlistEnabled,
            metadata = prefs.metadata,
            thumbnail = prefs.thumbnail,
            subtitles = prefs.subtitles,
            autoSubtitles = prefs.autoSubtitles,
            restrictNames = prefs.restrictNames,
            playlistItems = prefs.playlistItems,
            maxDownloads = prefs.maxDownloads,
            rateLimit = prefs.rateLimit,
            downloadArchive = prefs.downloadArchive,
            showAdvanced = prefs.showAdvanced,
            showDiagnostics = runtime.showDiagnostics,
            showFullOutputPath = runtime.showFullOutputPath,
            cookiesFile = prefs.cookiesFile,
            browserCookies = prefs.browserCookies,
            retries = prefs.retries,
            concurrentFragments = prefs.concurrentFragments,
            extraArgs = prefs.extraArgs,
            youtube403Fallback = prefs.youtube403Fallback,
            urlValidationState = validation.urlValidationState,
            urlStatusText = validation.urlStatusText,
            previewTitle = validation.previewTitle,
            previewChannel = validation.previewChannel,
            previewItemCount = validation.previewItemCount,
            sharedUrlBuffer = validation.sharedUrlBuffer,
            status = task.status,
            progress = task.progress,
            speedText = task.speedText,
            etaText = task.etaText,
            playlistProgressText = task.playlistProgressText,
            logs = task.logs,
            isRunning = task.isRunning,
            errorText = validation.errorText,
            currentLanguage = runtime.currentLanguage,
            isDarkTheme = runtime.isDarkTheme,
            isBatchMode = prefs.isBatchMode,
            clipTextDetected = validation.clipTextDetected,
            activeTab = runtime.activeTab,
            historyRecords = runtime.historyRecords
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.Eagerly,
        initialValue = buildInitialState(application)
    )

    init {
        bootstrapEmbeddedBinaries()
        observeHistoryDatabase()

        // Listen to sharedUrlBuffer
        viewModelScope.launch {
            sharedUrlBuffer.collect { url ->
                setIncomingSharedText(url)
            }
        }

        // Listen to DownloadService's isRunning state
        viewModelScope.launch {
            com.baynuman.ytdownloader.service.DownloadService.isRunning.collect { isServiceRunning ->
                _activeTaskState.update { it.copy(isRunning = isServiceRunning) }
            }
        }

        // Listen to DownloadService's events
        viewModelScope.launch {
            com.baynuman.ytdownloader.service.DownloadService.downloadEvents.collect { event ->
                when (event) {
                    is DownloadEvent.LogLine -> handleLogLine(event.text)
                    is DownloadEvent.Progress -> {
                        val progressVal = event.value.coerceIn(0f, 1f)
                        _activeTaskState.update { it.copy(progress = progressVal) }
                    }
                    is DownloadEvent.Status -> _activeTaskState.update { it.copy(status = event.text) }
                    is DownloadEvent.Finished -> {
                        _activeTaskState.update {
                            it.copy(
                                isRunning = false,
                                status = if (event.success) "Tamamlandi" else it.status,
                                speedText = if (event.success) "Tamamlandi" else "--",
                                etaText = if (event.success) "00:00" else "--",
                            )
                        }
                        if (event.success) {
                            val activeRequest = com.baynuman.ytdownloader.service.DownloadService.activeRequest
                            val currentUrl = lastStartedUrl.ifBlank { activeRequest?.urls?.firstOrNull() ?: "" }
                            val finalTitle = if (_formValidationState.value.previewTitle.isNotBlank()) {
                                _formValidationState.value.previewTitle
                            } else {
                                currentUrl
                            }
                            addToHistory(
                                title = finalTitle,
                                url = currentUrl,
                                format = if (_preferencesState.value.mode == DownloadMode.VIDEO) _preferencesState.value.videoContainer else _preferencesState.value.audioFormat,
                                sizeBytes = event.sizeBytes
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

    private fun defaultOutputDir(application: Application): String {
        val fallback = application
            .getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS)
            ?.resolve("yt-downloads")
            ?.absolutePath
            ?: application.filesDir.resolve("yt-downloads").absolutePath
        val saved = prefs.getString(KEY_OUTPUT_DIR, null)?.trim().orEmpty()
        return if (saved.isNotBlank()) saved else fallback
    }

    private fun buildInitialPreferencesState(application: Application): DownloadPreferencesState {
        return DownloadPreferencesState(
            outputDir = defaultOutputDir(application)
        )
    }

    private fun buildInitialState(application: Application): DownloaderUiState {
        val savedLang = prefs.getString("current_language", null)
            ?: java.util.Locale.getDefault().language.takeIf { it in listOf("tr", "es") }
            ?: "en"
        val savedTheme = prefs.getBoolean("is_dark_theme", true)
        return DownloaderUiState(
            outputDir = defaultOutputDir(application),
            currentLanguage = savedLang,
            isDarkTheme = savedTheme
        )
    }

    // Observe Room DB History in a reactive, asynchronus flow stream
    private fun observeHistoryDatabase() {
        viewModelScope.launch {
            recordDao.getAllRecordsFlow().collect { entities ->
                val records = entities.map { it.toDomainModel() }
                _runtimeState.update { it.copy(historyRecords = records) }
            }
        }
    }

    fun bootstrapEmbeddedBinaries(forceUpdate: Boolean = false) {
        viewModelScope.launch {
            _runtimeState.update { it.copy(binaryStatus = "yt-dlp otomatik hazirlaniyor...") }
            val result = withContext(Dispatchers.IO) {
                binaryInstaller.installOrReuse(forceUpdate = forceUpdate) { status ->
                    _runtimeState.update { it.copy(binaryStatus = status) }
                }
            }
            _runtimeState.update {
                it.copy(
                    executablePath = result.ytDlpPath ?: it.executablePath,
                    ffmpegLocation = result.ffmpegDir ?: "",
                    detectedAbi = result.abi,
                    binaryStatus = result.message,
                    showDiagnostics = true
                )
            }
            
            appendLog("[bilgi] yt-dlp dahili runtime hazir. ABI: ${result.abi}\n")
        }
    }

    fun updateLanguage(value: String) {
        _runtimeState.update { it.copy(currentLanguage = value) }
        prefs.edit().putString("current_language", value).apply()
        telemetry("language_changed_$value")
    }

    fun toggleTheme() {
        val next = !_runtimeState.value.isDarkTheme
        _runtimeState.update { it.copy(isDarkTheme = next) }
        prefs.edit().putBoolean("is_dark_theme", next).apply()
        telemetry("theme_changed_${if (next) "dark" else "light"}")
    }

    fun toggleBatchMode() {
        _preferencesState.update { it.copy(isBatchMode = !it.isBatchMode) }
        telemetry("batch_mode_changed_${_preferencesState.value.isBatchMode}")
    }

    fun removeUrlFromBatch(index: Int) {
        val urls = parseUrls(_formValidationState.value.urlsText)
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
            if (pasted.isNotEmpty() && isLikelyYoutubeUrl(pasted) && !pasted.contains(_formValidationState.value.urlsText.trim())) {
                _formValidationState.update { it.copy(clipTextDetected = pasted) }
            } else {
                _formValidationState.update { it.copy(clipTextDetected = "") }
            }
        } catch (_: Exception) {
            _formValidationState.update { it.copy(clipTextDetected = "") }
        }
    }

    fun pasteDetectedClipboardUrl() {
        val detected = _formValidationState.value.clipTextDetected
        if (detected.isNotEmpty()) {
            val current = _formValidationState.value.urlsText.trim()
            val nextText = if (current.isEmpty()) {
                detected
            } else {
                if (_preferencesState.value.isBatchMode) {
                    "$current\n$detected"
                } else {
                    detected
                }
            }
            updateUrlsText(nextText)
            _formValidationState.update { it.copy(clipTextDetected = "") }
        }
    }

    fun updateUrlsText(value: String) {
        _formValidationState.update { it.copy(urlsText = value, errorText = null) }
        schedulePreview(value)
    }

    fun clearUrl() {
        previewJob?.cancel()
        _formValidationState.update {
            it.copy(
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
            _formValidationState.update { it.copy(errorText = "Panoda baglanti bulunamadi.") }
            return
        }
        updateUrlsText(pasted)
    }

    fun updateOutputDir(value: String) {
        val sanitized = value.trim()
        _preferencesState.update { it.copy(outputDir = sanitized) }
        if (sanitized.isNotEmpty()) {
            persistOutputDir(sanitized)
        }
    }

    fun updateMode(value: DownloadMode) = _preferencesState.update { it.copy(mode = value) }
    fun updateVideoPreset(value: String) = _preferencesState.update { it.copy(videoPreset = value) }
    fun updateCustomVideoHeight(value: String) = _preferencesState.update { it.copy(customVideoHeight = value) }
    fun updateVideoContainer(value: String) = _preferencesState.update { it.copy(videoContainer = value) }
    fun updateVideoAudioCodec(value: String) = _preferencesState.update { it.copy(videoAudioCodec = value) }
    fun updateAudioFormat(value: String) = _preferencesState.update { it.copy(audioFormat = value) }
    fun updateAudioQualityPreset(value: String) = _preferencesState.update { it.copy(audioQualityPreset = value) }
    fun updatePlaylistEnabled(value: Boolean) = _preferencesState.update { it.copy(playlistEnabled = value) }
    fun updateMetadata(value: Boolean) = _preferencesState.update { it.copy(metadata = value) }
    fun updateThumbnail(value: Boolean) = _preferencesState.update { it.copy(thumbnail = value) }
    fun updateSubtitles(value: Boolean) = _preferencesState.update { it.copy(subtitles = value) }
    fun updateAutoSubtitles(value: Boolean) = _preferencesState.update { it.copy(autoSubtitles = value) }
    fun updateRestrictNames(value: Boolean) = _preferencesState.update { it.copy(restrictNames = value) }
    fun updatePlaylistItems(value: String) = _preferencesState.update { it.copy(playlistItems = value) }
    fun updateMaxDownloads(value: String) = _preferencesState.update { it.copy(maxDownloads = value) }
    fun updateRateLimit(value: String) = _preferencesState.update { it.copy(rateLimit = value) }
    fun updateDownloadArchive(value: Boolean) = _preferencesState.update { it.copy(downloadArchive = value) }
    fun updateShowAdvanced(value: Boolean) = _preferencesState.update { it.copy(showAdvanced = value) }
    fun toggleDiagnostics() { _runtimeState.update { it.copy(showDiagnostics = !it.showDiagnostics) } }
    fun toggleFullOutputPath() { _runtimeState.update { it.copy(showFullOutputPath = !it.showFullOutputPath) } }
    fun updateCookiesFile(value: String) = _preferencesState.update { it.copy(cookiesFile = value) }
    fun updateBrowserCookies(value: String) = _preferencesState.update { it.copy(browserCookies = value) }
    fun updateRetries(value: String) = _preferencesState.update { it.copy(retries = value) }
    fun updateConcurrentFragments(value: String) = _preferencesState.update { it.copy(concurrentFragments = value) }
    fun updateExtraArgs(value: String) = _preferencesState.update { it.copy(extraArgs = value) }
    fun updateYoutube403Fallback(value: Boolean) = _preferencesState.update { it.copy(youtube403Fallback = value) }
    fun updateOutputTemplate(value: String) = _preferencesState.update { it.copy(outputTemplate = value) }
    
    fun updateMediaPermissionsStatus(value: Boolean) {
        val previous = _runtimeState.value.mediaPermissionsGranted
        _runtimeState.update { it.copy(mediaPermissionsGranted = value) }
        if (value && !previous) {
            telemetry("permission_granted")
        } else if (!value && previous) {
            telemetry("permission_missing")
        }
    }

    fun setIncomingSharedText(sharedText: String?) {
        val incoming = extractFirstUrl(sharedText.orEmpty()) ?: return
        _formValidationState.update { it.copy(sharedUrlBuffer = incoming) }
        telemetry("share_url_received")
        updateActiveTab(0)
        if (_formValidationState.value.urlsText.isBlank()) {
            updateUrlsText(incoming)
            appendLog("[bilgi] Paylasilan baglanti alindi.\n")
        }
    }

    fun importFromSharedBuffer() {
        val shared = _formValidationState.value.sharedUrlBuffer
        if (shared.isBlank()) {
            _formValidationState.update { it.copy(errorText = "Paylasimdan alinacak baglanti bulunamadi.") }
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
        _preferencesState.update { it.copy(outputDir = defaultOutputDir) }
        persistOutputDir(defaultOutputDir)
    }

    fun updateOutputDirFromTreeUri(uri: Uri?) {
        if (uri == null) return
        takePersistableTreePermission(uri)
        val resolvedPath = resolvePathFromTreeUri(uri)
        if (resolvedPath == null) {
            _formValidationState.update {
                it.copy(
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
        _preferencesState.update { it.copy(outputDir = folder.absolutePath) }
        _runtimeState.update { it.copy(showFullOutputPath = true) }
        _formValidationState.update { it.copy(errorText = null) }
        persistOutputDir(folder.absolutePath)
        appendLog("[bilgi] Indirme konumu guncellendi: ${folder.absolutePath}\n")
        telemetry("output_folder_changed")
    }

    fun refreshEmbeddedBinary() {
        bootstrapEmbeddedBinaries(forceUpdate = true)
    }

    fun clearLogs() {
        _activeTaskState.update { it.copy(logs = "") }
        _formValidationState.update { it.copy(errorText = null) }
    }

    fun importCookiesFromUri(uri: Uri?) {
        if (uri == null) return
        viewModelScope.launch {
            val app = getApplication<Application>()
            val destination = File(app.filesDir, "cookies/cookies.txt").apply {
                parentFile?.mkdirs()
            }
            val copied = copyUriToFile(uri, destination)
            if (copied) {
                _preferencesState.update { it.copy(cookiesFile = destination.absolutePath, showAdvanced = true) }
                _formValidationState.update { it.copy(errorText = null) }
                appendLog("[bilgi] Cookies dosyasi ice aktarildi: ${destination.absolutePath}\n")
            } else {
                _formValidationState.update { it.copy(errorText = "Cookies dosyasi okunamadi.") }
            }
        }
    }

    fun importYtDlpBinaryFromUri(uri: Uri?) {
        if (uri == null) return
        viewModelScope.launch {
            val app = getApplication<Application>()
            val destination = File(app.filesDir, "bin/yt-dlp").apply {
                parentFile?.mkdirs()
            }
            val copied = copyUriToFile(uri, destination)
            if (copied) {
                destination.setExecutable(true, false)
                _runtimeState.update {
                    it.copy(
                        executablePath = destination.absolutePath,
                        ffmpegLocation = destination.parentFile?.absolutePath ?: it.ffmpegLocation,
                        binaryStatus = "yt-dlp dosya secici ile guncellendi.",
                        showDiagnostics = true
                    )
                }
                _formValidationState.update { it.copy(errorText = null) }
                appendLog("[bilgi] yt-dlp binary guncellendi: ${destination.absolutePath}\n")
            } else {
                _formValidationState.update { it.copy(errorText = "yt-dlp binary okunamadi.") }
            }
        }
    }

    fun cancelDownload() {
        if (!_activeTaskState.value.isRunning) return
        try {
            val intent = Intent(appContext, com.baynuman.ytdownloader.service.DownloadService::class.java).apply {
                action = com.baynuman.ytdownloader.service.DownloadService.ACTION_STOP
            }
            appContext.startService(intent)
        } catch (_: Exception) {}
        appendLog("[bilgi] Duraklatma/iptal istegi gonderildi.\n")
        _activeTaskState.update { it.copy(status = "Duraklatiliyor...") }
    }

    fun startDownload() {
        val prefs = _preferencesState.value
        val validation = _formValidationState.value
        if (_activeTaskState.value.isRunning) return

        val validationError = validate(prefs, validation)
        if (validationError != null) {
            _formValidationState.update { it.copy(errorText = validationError) }
            _activeTaskState.update { it.copy(status = "Hazir") }
            telemetry("start_download_blocked")
            return
        }

        val urls = parseUrls(validation.urlsText)
        val runtime = _runtimeState.value
        val request = DownloadRequest(
            urls = urls,
            outputDir = prefs.outputDir,
            executablePath = runtime.executablePath,
            ffmpegLocation = runtime.ffmpegLocation,
            mode = prefs.mode,
            videoPreset = prefs.videoPreset,
            customVideoHeight = prefs.customVideoHeight,
            videoContainer = prefs.videoContainer,
            videoAudioCodec = prefs.videoAudioCodec,
            audioFormat = prefs.audioFormat,
            audioQualityPreset = prefs.audioQualityPreset,
            playlistEnabled = prefs.playlistEnabled,
            metadata = prefs.metadata,
            thumbnail = prefs.thumbnail,
            subtitles = prefs.subtitles,
            autoSubtitles = prefs.autoSubtitles,
            restrictNames = prefs.restrictNames,
            playlistItems = prefs.playlistItems,
            maxDownloads = prefs.maxDownloads.trim().toIntOrNull(),
            rateLimit = prefs.rateLimit,
            downloadArchive = prefs.downloadArchive,
            cookiesFile = prefs.cookiesFile,
            browserCookies = prefs.browserCookies,
            retries = prefs.retries.trim().toIntOrNull(),
            concurrentFragments = prefs.concurrentFragments.trim().toIntOrNull(),
            extraArgs = prefs.extraArgs,
            youtube403Fallback = prefs.youtube403Fallback,
            archiveFile = File(getApplication<Application>().filesDir, "download_archive.txt").absolutePath,
        )

        _activeTaskState.update {
            it.copy(
                isRunning = true,
                status = "Indirme baslatildi",
                progress = 0f,
                speedText = "--",
                etaText = "--",
                playlistProgressText = "",
            )
        }
        _formValidationState.update { it.copy(errorText = null) }
        telemetry("start_download")

        val firstUrl = extractFirstUrl(validation.urlsText) ?: ""
        val activeTitle = if (validation.previewTitle.isNotBlank()) validation.previewTitle else firstUrl
        
        lastStartedUrl = firstUrl

        try {
            val intent = Intent(appContext, com.baynuman.ytdownloader.service.DownloadService::class.java).apply {
                action = com.baynuman.ytdownloader.service.DownloadService.ACTION_START
                putExtra(com.baynuman.ytdownloader.service.DownloadService.EXTRA_TITLE, activeTitle)
                putExtra(com.baynuman.ytdownloader.service.DownloadService.EXTRA_REQUEST_JSON, request.toJsonString())
            }
            appContext.startService(intent)
        } catch (e: Exception) {
            _activeTaskState.update {
                it.copy(
                    isRunning = false,
                    status = "Servis baslatilamadi"
                )
            }
            appendLog("[hata] DownloadService baslatilamadi: ${e.message}\n")
        }
    }

    private fun schedulePreview(rawInput: String) {
        previewJob?.cancel()
        val url = extractFirstUrl(rawInput)
        if (url == null) {
            _formValidationState.update {
                it.copy(
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
            _formValidationState.update {
                it.copy(
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
            _formValidationState.update {
                it.copy(
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
                    _formValidationState.update {
                        it.copy(
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
        _formValidationState.update {
            it.copy(
                urlValidationState = if (preview.isPlaylist) UrlValidationState.PLAYLIST else UrlValidationState.VALID,
                urlStatusText = status,
                previewTitle = preview.title,
                previewChannel = preview.channel,
                previewItemCount = preview.itemCount
            )
        }
        telemetry("url_preview_resolved")
    }

    private fun mapPreviewError(msg: String?): String {
        val text = msg.orEmpty()
        return when {
            text.contains("HTTP Error 403", ignoreCase = true) -> "403 Forbidden: YouTube erisimi engelledi. Cookies kullanmayi deneyin."
            text.contains("HTTP Error 404", ignoreCase = true) -> "404 Not Found: Video bulunamadi."
            text.contains("sign in to confirm", ignoreCase = true) -> "Yas kisitlamali video: Giris yapilmasi gerekiyor."
            else -> "Baglanti cözülemedi: ${msg ?: "Sunucu hatasi"}"
        }
    }

    private fun validate(prefs: DownloadPreferencesState, validation: FormValidationState): String? {
        if (validation.urlsText.trim().isEmpty()) {
            return "Indirmek icin en az bir URL girin."
        }
        if (prefs.outputDir.trim().isEmpty()) {
            return "Gecerli bir indirme konumu secin."
        }
        val targetDir = File(prefs.outputDir.trim())
        if (!targetDir.exists() && !targetDir.mkdirs()) {
            return "Indirme klasörü olusturulamadi: ${prefs.outputDir}"
        }
        if (!validateOptionalInt(prefs.maxDownloads, min = 1)) {
            return "Maksimum indirme adeti pozitif bir sayi olmalidir."
        }
        if (!validateOptionalInt(prefs.retries, min = 0)) {
            return "Tekrar deneme sayisi negatif olamaz."
        }
        if (!validateOptionalInt(prefs.concurrentFragments, min = 1)) {
            return "Es zamanli parca sayisi en az 1 olmalidir."
        }
        if (prefs.mode == DownloadMode.VIDEO && prefs.videoPreset == "Ozel") {
            val customHeight = prefs.customVideoHeight.trim()
            if (customHeight.isEmpty() || customHeight.toIntOrNull() == null || customHeight.toInt() <= 0) {
                return "Ozel video yüksekligi pozitif bir sayi olmalidir."
            }
        }
        return null
    }

    private suspend fun copyUriToFile(uri: Uri, destination: File): Boolean = withContext(Dispatchers.IO) {
        val app = getApplication<Application>()
        try {
            app.contentResolver.openInputStream(uri).use { input ->
                if (input == null) return@withContext false
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
                    if (parts.isEmpty()) return null

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
                        else -> {
                            // Support hex-based volume IDs for SD cards / USB storage (e.g. "12F4-56A8")
                            val volumeRoot = File("/storage/${parts[0]}")
                            if (volumeRoot.exists()) {
                                if (relative.isBlank()) volumeRoot.absolutePath
                                else File(volumeRoot, relative).absolutePath
                            } else null
                        }
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
        } catch (_: IllegalArgumentException) {
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
        if (value.isEmpty()) return true
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
            _activeTaskState.update { it.copy(status = "Depolama hatasi") }
            _formValidationState.update {
                it.copy(
                    errorText = "Klasore yazilamiyor. Indirme konumunu degistirin veya depolama izni verin."
                )
            }
            telemetry("error_storage_write_denied")
        }

        if (speed != null || eta != null || playlistProgress != null) {
            _activeTaskState.update {
                it.copy(
                    speedText = speed ?: it.speedText,
                    etaText = eta ?: it.etaText,
                    playlistProgressText = playlistProgress ?: it.playlistProgressText,
                )
            }
        }
    }

    fun updateActiveTab(index: Int) {
        _runtimeState.update { it.copy(activeTab = index) }
        telemetry("tab_swapped_$index")
    }

    fun addToHistory(title: String, url: String, format: String, sizeBytes: Long) {
        viewModelScope.launch(Dispatchers.IO) {
            val id = java.util.UUID.randomUUID().toString()
            val entity = DownloadRecordEntity(
                id = id,
                title = title,
                url = url,
                format = format,
                downloadedAt = System.currentTimeMillis(),
                fileSizeBytes = sizeBytes
            )
            recordDao.insertRecord(entity)
        }
    }

    fun clearHistory() {
        viewModelScope.launch(Dispatchers.IO) {
            recordDao.clearAll()
        }
        telemetry("history_cleared")
    }

    private fun appendLog(line: String) {
        _activeTaskState.update { current ->
            val combined = current.logs + line
            val lines = combined.lineSequence().toList()
            val next = if (lines.size > 300) {
                lines.takeLast(300).joinToString("\n") + "\n"
            } else {
                combined
            }
            current.copy(logs = next)
        }
    }

    private fun telemetry(event: String) {
        Log.d(TELEMETRY_TAG, "event=$event source=ui ts=${System.currentTimeMillis()}")
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
        val sharedUrlBuffer: MutableSharedFlow<String> = MutableSharedFlow(extraBufferCapacity = 8)
    }
}
