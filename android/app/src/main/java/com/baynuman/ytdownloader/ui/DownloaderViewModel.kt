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
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
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

class DownloaderViewModel(application: Application) : AndroidViewModel(application) {
    private val appContext = application.applicationContext
    private val prefs = appContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    private val runner = YtDlpRunner(appContext)
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

    // Additional global state elements
    private val _historyRecords = MutableStateFlow<List<DownloadRecord>>(emptyList())
    private val _activeTab = MutableStateFlow(0)
    private val _isDarkTheme = MutableStateFlow(prefs.getBoolean("is_dark_theme", true))
    private val _currentLanguage = MutableStateFlow(prefs.getString("current_language", "en") ?: "en")
    private val _binaryStatus = MutableStateFlow("yt-dlp otomatik hazirlaniyor...")
    private val _detectedAbi = MutableStateFlow("")
    private val _executablePath = MutableStateFlow("internal://youtubedl-android")
    private val _ffmpegLocation = MutableStateFlow("")
    private val _mediaPermissionsGranted = MutableStateFlow(false)
    private val _showDiagnostics = MutableStateFlow(false)
    private val _showFullOutputPath = MutableStateFlow(false)

    // 2. High-performance Selector Unified Flow for Backward Compatibility
    val uiState: StateFlow<DownloaderUiState> = combine(
        _preferencesState,
        _activeTaskState,
        _formValidationState,
        _historyRecords,
        _activeTab,
        _isDarkTheme,
        _currentLanguage,
        _binaryStatus,
        _detectedAbi,
        _executablePath,
        _ffmpegLocation,
        _mediaPermissionsGranted,
        _showDiagnostics,
        _showFullOutputPath
    ) { combined ->
        val prefs = combined[0] as DownloadPreferencesState
        val task = combined[1] as ActiveTaskState
        val validation = combined[2] as FormValidationState
        val history = combined[3] as List<DownloadRecord>
        val tab = combined[4] as Int
        val dark = combined[5] as Boolean
        val lang = combined[6] as String
        val binStat = combined[7] as String
        val abi = combined[8] as String
        val exePath = combined[9] as String
        val ffmLocation = combined[10] as String
        val perm = combined[11] as Boolean
        val diag = combined[12] as Boolean
        val fullPath = combined[13] as Boolean

        DownloaderUiState(
            urlsText = validation.urlsText,
            outputDir = prefs.outputDir,
            outputTemplate = DEFAULT_OUTPUT_TEMPLATE,
            executablePath = exePath,
            ffmpegLocation = ffmLocation,
            binaryStatus = binStat,
            detectedAbi = abi,
            mediaPermissionsGranted = perm,
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
            showDiagnostics = diag,
            showFullOutputPath = fullPath,
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
            currentLanguage = lang,
            isDarkTheme = dark,
            isBatchMode = prefs.isBatchMode,
            clipTextDetected = validation.clipTextDetected,
            activeTab = tab,
            historyRecords = history
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.Eagerly,
        initialValue = buildInitialState(application)
    )

    init {
        bootstrapEmbeddedBinaries()
        observeHistoryDatabase()
    }

    private fun buildInitialPreferencesState(application: Application): DownloadPreferencesState {
        val fallbackOutputDir = application
            .getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS)
            ?.resolve("yt-downloads")
            ?.absolutePath
            ?: application.filesDir.resolve("yt-downloads").absolutePath
        val savedOutputDir = prefs.getString(KEY_OUTPUT_DIR, null)?.trim().orEmpty()
        val outputDir = if (savedOutputDir.isNotBlank()) savedOutputDir else fallbackOutputDir

        return DownloadPreferencesState(
            outputDir = outputDir
        )
    }

    private fun buildInitialState(application: Application): DownloaderUiState {
        val fallbackOutputDir = application
            .getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS)
            ?.resolve("yt-downloads")
            ?.absolutePath
            ?: application.filesDir.resolve("yt-downloads").absolutePath
        val savedOutputDir = prefs.getString(KEY_OUTPUT_DIR, null)?.trim().orEmpty()
        val outputDir = if (savedOutputDir.isNotBlank()) savedOutputDir else fallbackOutputDir
        
        val savedLang = prefs.getString("current_language", "en") ?: "en"
        val savedTheme = prefs.getBoolean("is_dark_theme", true)

        return DownloaderUiState(
            outputDir = outputDir,
            currentLanguage = savedLang,
            isDarkTheme = savedTheme
        )
    }

    // Observe Room DB History in a reactive, asynchronus flow stream
    private fun observeHistoryDatabase() {
        viewModelScope.launch {
            recordDao.getAllRecordsFlow().collect { entities ->
                val records = entities.map { it.toDomainModel() }
                _historyRecords.value = records
            }
        }
    }

    fun bootstrapEmbeddedBinaries(forceUpdate: Boolean = false) {
        viewModelScope.launch {
            _binaryStatus.value = "yt-dlp otomatik hazirlaniyor..."
            val result = withContext(Dispatchers.IO) {
                binaryInstaller.installOrReuse(forceUpdate = forceUpdate) { status ->
                    _binaryStatus.value = status
                }
            }
            _executablePath.value = result.ytDlpPath ?: _executablePath.value
            _ffmpegLocation.value = result.ffmpegDir ?: ""
            _detectedAbi.value = result.abi
            _binaryStatus.value = result.message
            _showDiagnostics.value = true
            
            appendLog("[bilgi] yt-dlp dahili runtime hazir. ABI: ${result.abi}\n")
        }
    }

    fun updateLanguage(value: String) {
        _currentLanguage.value = value
        prefs.edit().putString("current_language", value).apply()
        telemetry("language_changed_$value")
    }

    fun toggleTheme() {
        val next = !_isDarkTheme.value
        _isDarkTheme.value = next
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
    fun toggleDiagnostics() { _showDiagnostics.value = !_showDiagnostics.value }
    fun toggleFullOutputPath() { _showFullOutputPath.value = !_showFullOutputPath.value }
    fun updateCookiesFile(value: String) = _preferencesState.update { it.copy(cookiesFile = value) }
    fun updateBrowserCookies(value: String) = _preferencesState.update { it.copy(browserCookies = value) }
    fun updateRetries(value: String) = _preferencesState.update { it.copy(retries = value) }
    fun updateConcurrentFragments(value: String) = _preferencesState.update { it.copy(concurrentFragments = value) }
    fun updateExtraArgs(value: String) = _preferencesState.update { it.copy(extraArgs = value) }
    fun updateYoutube403Fallback(value: Boolean) = _preferencesState.update { it.copy(youtube403Fallback = value) }
    
    fun updateMediaPermissionsStatus(value: Boolean) {
        val previous = _mediaPermissionsGranted.value
        _mediaPermissionsGranted.value = value
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
        _showFullOutputPath.value = true
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
                _executablePath.value = destination.absolutePath
                _ffmpegLocation.value = destination.parentFile?.absolutePath ?: _ffmpegLocation.value
                _binaryStatus.value = "yt-dlp dosya secici ile guncellendi."
                _formValidationState.update { it.copy(errorText = null) }
                _showDiagnostics.value = true
                appendLog("[bilgi] yt-dlp binary guncellendi: ${destination.absolutePath}\n")
            } else {
                _formValidationState.update { it.copy(errorText = "yt-dlp binary okunamadi.") }
            }
        }
    }

    fun cancelDownload() {
        if (!_activeTaskState.value.isRunning) return
        runner.cancel()
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
        val request = DownloadRequest(
            urls = urls,
            outputDir = prefs.outputDir,
            executablePath = _executablePath.value,
            ffmpegLocation = _ffmpegLocation.value,
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
        startForegroundDownloadService(activeTitle)

        viewModelScope.launch {
            runner.run(request) { event ->
                when (event) {
                    is DownloadEvent.LogLine -> handleLogLine(event.text)
                    is DownloadEvent.Progress -> {
                        val progressVal = event.value.coerceIn(0f, 1f)
                        _activeTaskState.update { it.copy(progress = progressVal) }
                        
                        val percentage = (progressVal * 100).toInt()
                        updateForegroundDownloadService(
                            title = if (_formValidationState.value.previewTitle.isNotBlank()) _formValidationState.value.previewTitle else "yt-dlp",
                            progress = percentage,
                            speed = _activeTaskState.value.speedText,
                            eta = _activeTaskState.value.etaText
                        )
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
                        
                        stopForegroundDownloadService()
                        
                        if (event.success) {
                            val finalTitle = if (_formValidationState.value.previewTitle.isNotBlank()) _formValidationState.value.previewTitle else firstUrl
                            addToHistory(
                                title = finalTitle,
                                url = firstUrl,
                                format = if (prefs.mode == DownloadMode.VIDEO) prefs.videoContainer else prefs.audioFormat,
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
        _activeTab.value = index
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
        _activeTaskState.update { current ->
            val next = (current.logs + line).takeLast(24_000)
            current.copy(logs = next)
        }
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
