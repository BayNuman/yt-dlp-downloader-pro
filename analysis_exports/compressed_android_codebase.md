# yt-dlp Downloader Pro - Android Codebase Anthology

This document compiles the complete Kotlin + Jetpack Compose Android codebase of **yt-dlp Downloader Pro** into a single, beautifully structured reference file. It is optimized for engineering comparative review, codebase auditing, and architecture inspection.

## 🏗️ Android Architecture & Design Patterns

The Android application is a native download manager built on **Kotlin**, **Jetpack Compose** (Declarative UI), and **youtubedl-android** (C++ NDK wrapper). It implements elegant mobile patterns that mirror the premium features of the Desktop version:

1. **Declarative Compose UI in `ui/DownloaderScreen.kt`**:
   - Implements a modern, glassmorphic layout using tailored HSL color tokens.
   - Leverages Compose animation APIs for smooth UI card expansions and sliding notification banners.
   
2. **Dynamic JNI Core Runner in `data/YtDlpRunner.kt`**:
   - Interacts with C++ NDK library `YoutubeDL` to parse commands, launch downloads, and catch progress callbacks natively.
   
3. **Foreground Service in `service/DownloadService.kt`**:
   - Ensures download processes survive application closures or background switches, pushing native system progress notifications.
   
4. **Multi-Language Architecture in `ui/theme/Translations.kt`**:
   - Localization dictionaries supporting Turkish, English, and Spanish natively.

## 📂 Codebase Table of Contents
- [MainActivity.kt](#file-mainactivitykt)
- [data/DownloadModels.kt](#file-datadownloadmodelskt)
- [data/DownloadStates.kt](#file-datadownloadstateskt)
- [data/DownloadRepository.kt](#file-datadownloadrepositorykt)
- [data/db/DownloadRecordEntity.kt](#file-datadbdownloadrecordentitykt)
- [data/db/DownloadRecordDao.kt](#file-datadbdownloadrecorddaokt)
- [data/db/ChannelRuleEntity.kt](#file-datadbchannelruleentitykt)
- [data/db/ChannelRuleDao.kt](#file-datadbchannelruledaokt)
- [data/db/DownloadDatabase.kt](#file-datadbdownloaddatabasekt)
- [data/algorithms/ClipOptimizer.kt](#file-dataalgorithmsclipoptimizerkt)
- [data/storage/MediaStoreScanner.kt](#file-datastoragemediastorescannerkt)
- [data/UrlPreviewResolver.kt](#file-dataurlpreviewresolverkt)
- [data/YtDlpCommandBuilder.kt](#file-dataytdlpcommandbuilderkt)
- [data/BinaryInstaller.kt](#file-databinaryinstallerkt)
- [data/YtDlpRunner.kt](#file-dataytdlprunnerkt)
- [service/DownloadService.kt](#file-servicedownloadservicekt)
- [ui/theme/Color.kt](#file-uithemecolorkt)
- [ui/theme/Theme.kt](#file-uithemethemekt)
- [ui/theme/Tokens.kt](#file-uithemetokenskt)
- [ui/theme/Translations.kt](#file-uithemetranslationskt)
- [ui/theme/Type.kt](#file-uithemetypekt)
- [ui/DownloaderViewModel.kt](#file-uidownloaderviewmodelkt)
- [ui/DownloaderScreen.kt](#file-uidownloaderscreenkt)

---

## <a name="file-mainactivitykt"></a> 📄 File: `MainActivity.kt`
**Responsibility**: App entrypoint. Sets up window bounds, registers DND features, handles share intent incoming URLs.

```kotlin
package com.baynuman.ytdownloader

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.platform.LocalContext
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.baynuman.ytdownloader.ui.DownloaderScreen
import com.baynuman.ytdownloader.ui.DownloaderViewModel
import com.baynuman.ytdownloader.ui.theme.YtDownloaderTheme

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {

            val downloaderViewModel: DownloaderViewModel = viewModel()
            val state by downloaderViewModel.uiState.collectAsStateWithLifecycle()

                val context = LocalContext.current

                val permissionsLauncher = rememberLauncherForActivityResult(
                    val granted = result.values.all { it }

                val cookiesFileLauncher = rememberLauncherForActivityResult(

                val ytDlpFileLauncher = rememberLauncherForActivityResult(

                val folderLauncher = rememberLauncherForActivityResult(

                    val hasPerms = hasMediaPermissions(context)
                        val permissions = requiredMediaPermissions()

                        val permissions = requiredMediaPermissions()

    override fun onNewIntent(intent: Intent) {

private fun requiredMediaPermissions(): Array<String> {
    val list = mutableListOf<String>()

private fun hasMediaPermissions(context: Context): Boolean {
    val permissions = requiredMediaPermissions()

private fun extractSharedText(intent: Intent?): String? {
    val rawText = intent.getStringExtra(Intent.EXTRA_TEXT) ?: return null
    val regex = Regex("""https?://[\w./\-?=&%+#]+""")
    val match = regex.find(rawText) ?: return null
    val urlStr = match.value
    
        val uri = android.net.Uri.parse(urlStr)
        val host = uri.host?.lowercase() ?: ""
        val whitelist = listOf("youtube.com", "youtu.be", "vimeo.com", "tiktok.com", "instagram.com")
        val isValid = whitelist.any { allowed -> host == allowed || host.endsWith(".$allowed") }
    

```

---

## <a name="file-datadownloadmodelskt"></a> 📄 File: `data/DownloadModels.kt`
**Responsibility**: Dataclasses for download tasks, states, download formats, and app preferences.

```kotlin
package com.baynuman.ytdownloader.data

import com.baynuman.ytdownloader.data.algorithms.MicroClip


val VIDEO_PRESET_HEIGHT = linkedMapOf(

val AUDIO_PRESET_QUALITY = linkedMapOf(

val VIDEO_AUDIO_CODEC_OPTIONS = listOf(

val BROWSER_COOKIE_SOURCES = listOf(

val VIDEO_CONTAINER_OPTIONS = listOf("mp4", "mkv", "webm")
val AUDIO_FORMAT_OPTIONS = listOf("aac", "opus", "mp3", "m4a", "wav", "flac")
val VIDEO_LIMIT_OPTIONS = listOf("2160", "1440", "1080", "720", "480", "360")


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
    fun toJsonString(): String {
        val obj = org.json.JSONObject()
        
        val clipsArray = org.json.JSONArray()

        fun fromJsonString(jsonStr: String): DownloadRequest {
            val obj = org.json.JSONObject(jsonStr)
            val urlsArr = obj.getJSONArray("urls")
            val urls = mutableListOf<String>()
            val mode = DownloadMode.valueOf(obj.getString("mode"))
            val maxD = obj.getInt("maxDownloads")
            val ret = obj.getInt("retries")
            val conc = obj.getInt("concurrentFragments")
            
            val clipsArr = obj.optJSONArray("clips")
            val clips = mutableListOf<MicroClip>()
                    val cObj = clipsArr.getJSONObject(i)


    data class LogLine(val text: String) : DownloadEvent
    data class Progress(val value: Float) : DownloadEvent
    data class Status(val text: String) : DownloadEvent
    data class Finished(val success: Boolean, val exitCode: Int, val sizeBytes: Long = 0L, val filePath: String = "") : DownloadEvent

data class SponsorSegment(val start: Float, val end: Float, val category: String)

data class DownloadRecord(
    val id: String,
    val title: String,
    val url: String,
    val format: String,
    val downloadedAt: Long,
    val fileSizeBytes: Long,
    val thumbnailPath: String? = null


```

---

## <a name="file-datadownloadstateskt"></a> 📄 File: `data/DownloadStates.kt`
**Responsibility**: 

```kotlin
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
    val outputTemplate: String = "",
    val clipEnabled: Boolean = false,
    val clipStart: String = "00:00",
    val clipEnd: String = "00:00",
    val wifiOnly: Boolean = false,
    val schedulerEnabled: Boolean = false,
    val schedulerTime: String = "03:00",
    val userExplicit: Boolean = false,
    val folderOrg: String = "None",
    val clipPrecise: Boolean = false,
    val compactMode: Boolean = false

data class ActiveTaskState(
    val isRunning: Boolean = false,
    val status: String = "Hazir",
    val progress: Float = 0f,
    val speedText: String = "--",
    val etaText: String = "--",
    val logs: String = "Uygulama hazir.\n",
    val playlistProgressText: String = "",
    val speedHistory: List<Float> = List(60) { 0f },
    val speedWriteIdx: Int = 0,
    val emaSmoothed: Float = 0f

data class FormValidationState(
    val urlsText: String = "",
    val urlValidationState: UrlValidationState = UrlValidationState.IDLE,
    val urlStatusText: String = "YouTube baglantisini yapistirin.",
    val previewTitle: String = "",
    val previewChannel: String = "",
    val previewItemCount: Int? = null,
    val sharedUrlBuffer: String = "",
    val clipTextDetected: String = "",
    val errorText: String? = null,
    val sponsorSegments: List<SponsorSegment> = emptyList()

```

---

## <a name="file-datadownloadrepositorykt"></a> 📄 File: `data/DownloadRepository.kt`
**Responsibility**: 

```kotlin
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
        
    var activeRequest: DownloadRequest?
        @Synchronized get() = _activeRequest
        @Synchronized set(value) {

```

---

## <a name="file-datadbdownloadrecordentitykt"></a> 📄 File: `data/db/DownloadRecordEntity.kt`
**Responsibility**: 

```kotlin
package com.baynuman.ytdownloader.data.db

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey
import com.baynuman.ytdownloader.data.DownloadRecord

@Entity(tableName = "download_history")
data class DownloadRecordEntity(
    @PrimaryKey val id: String,
    val title: String,
    val url: String,
    val format: String,
    val downloadedAt: Long,
    val fileSizeBytes: Long,
    @ColumnInfo(name = "thumbnail_path") val thumbnailPath: String? = null
    fun toDomainModel(): DownloadRecord {

        fun fromDomainModel(record: DownloadRecord): DownloadRecordEntity {

```

---

## <a name="file-datadbdownloadrecorddaokt"></a> 📄 File: `data/db/DownloadRecordDao.kt`
**Responsibility**: 

```kotlin
package com.baynuman.ytdownloader.data.db

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface DownloadRecordDao {
    @Query("SELECT * FROM download_history ORDER BY downloadedAt DESC")
    fun getAllRecordsFlow(): Flow<List<DownloadRecordEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    fun insertRecord(record: DownloadRecordEntity)

    @Query("DELETE FROM download_history WHERE id = :id")
    fun deleteRecordById(id: String)

    @Query("DELETE FROM download_history")
    fun clearAll()

    @Query("SELECT * FROM download_history WHERE (url = :url OR url LIKE :urlLike) AND format = :format LIMIT 1")
    fun findRecordByUrlAndFormat(url: String, urlLike: String, format: String): DownloadRecordEntity?

    @Query("UPDATE download_history SET thumbnail_path = :thumbnailPath WHERE id = :id")
    fun updateThumbnailPath(id: String, thumbnailPath: String): Int

```

---

## <a name="file-datadbchannelruleentitykt"></a> 📄 File: `data/db/ChannelRuleEntity.kt`
**Responsibility**: 

```kotlin
package com.baynuman.ytdownloader.data.db

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "channel_rules")
data class ChannelRuleEntity(
    @PrimaryKey val channelId: String,
    @ColumnInfo(name = "channel_name") val channelName: String,
    @ColumnInfo(name = "settings_json") val settingsJson: String,
    @ColumnInfo(name = "created_at") val createdAt: Long = System.currentTimeMillis(),
    @ColumnInfo(name = "updated_at") val updatedAt: Long = System.currentTimeMillis()

```

---

## <a name="file-datadbchannelruledaokt"></a> 📄 File: `data/db/ChannelRuleDao.kt`
**Responsibility**: 

```kotlin
package com.baynuman.ytdownloader.data.db

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query

@Dao
interface ChannelRuleDao {
    @Query("SELECT * FROM channel_rules WHERE channelId = :channelId LIMIT 1")
    fun getRuleByChannelId(channelId: String): ChannelRuleEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    fun insertOrUpdate(rule: ChannelRuleEntity)

    @Query("DELETE FROM channel_rules WHERE channelId = :channelId")
    fun deleteByChannelId(channelId: String)

    @Query("SELECT * FROM channel_rules ORDER BY updated_at DESC")
    fun getAllRules(): List<ChannelRuleEntity>

```

---

## <a name="file-datadbdownloaddatabasekt"></a> 📄 File: `data/db/DownloadDatabase.kt`
**Responsibility**: 

```kotlin
package com.baynuman.ytdownloader.data.db

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase

@Database(entities = [DownloadRecordEntity::class, ChannelRuleEntity::class], version = 3, exportSchema = false)

        @Volatile
        private var INSTANCE: DownloadDatabase? = null

        val MIGRATION_1_2 = object : Migration(1, 2) {
            override fun migrate(db: SupportSQLiteDatabase) {

        val MIGRATION_2_3 = object : Migration(2, 3) {
            override fun migrate(db: SupportSQLiteDatabase) {
                """.trimIndent())

        fun getDatabase(context: Context): DownloadDatabase {
                val instance = Room.databaseBuilder(

```

---

## <a name="file-dataalgorithmsclipoptimizerkt"></a> 📄 File: `data/algorithms/ClipOptimizer.kt`
**Responsibility**: 

```kotlin
package com.baynuman.ytdownloader.data.algorithms

data class MicroClip(
    val start: Float,
    val end: Float,
    val title: String

data class MacroClip(
    val start: Float,
    val end: Float,
    val subClips: List<MicroClip>

object ClipOptimizer {
    fun optimizeClipIntervals(clips: List<MicroClip>, thresholdSec: Float = 30f): List<MacroClip> {
        val sorted = clips.sortedBy { it.start }
        val merged = mutableListOf<MacroClip>()

        var currentStart = sorted[0].start
        var currentEnd = sorted[0].end
        val currentSubClips = mutableListOf(sorted[0])

            val next = sorted[i]

    fun parseTimeToSeconds(s: String): Float? {
        val clean = s.trim()
            val parts = clean.split(":")

```

---

## <a name="file-datastoragemediastorescannerkt"></a> 📄 File: `data/storage/MediaStoreScanner.kt`
**Responsibility**: 

```kotlin
package com.baynuman.ytdownloader.data.storage

import android.content.Context
import android.media.MediaScannerConnection
import android.net.Uri
import android.util.Log

object MediaStoreScanner {
    fun scanFile(context: Context, filePath: String, onScanComplete: (Uri?) -> Unit = {}) {

```

---

## <a name="file-dataurlpreviewresolverkt"></a> 📄 File: `data/UrlPreviewResolver.kt`
**Responsibility**: Extracts thumbnails, platform origins, and basic metadata previews dynamically.

```kotlin
package com.baynuman.ytdownloader.data

import android.content.Context
import com.yausername.youtubedl_android.YoutubeDL
import com.yausername.youtubedl_android.YoutubeDLException
import com.yausername.youtubedl_android.YoutubeDLRequest
import java.util.UUID
import org.json.JSONObject

data class UrlPreview(
    val title: String,
    val channel: String,
    val isPlaylist: Boolean,
    val itemCount: Int?,
    val thumbnailUrl: String? = null,
    val channelId: String? = null

class UrlPreviewResolver(
    private val appContext: Context,
    fun resolve(url: String): UrlPreview {
        val youtubeDL = YoutubeDL.getInstance()

        val request = YoutubeDLRequest(url).addCommands(
        val response = youtubeDL.execute(request, "preview-${UUID.randomUUID()}")
            val error = (response.err + "\n" + response.out).trim()

        val json = extractJson(response.out)
        val title = json.optString("title").ifEmpty {
        val channel = json.optString("uploader").ifEmpty {

        val thumbnailUrl = json.optString("thumbnail").takeIf { it.isNotBlank() }

        val channelId = json.optString("channel_id").takeIf { it.isNotBlank() }

        val entries = json.optJSONArray("entries")
        val isPlaylist = json.optString("_type").equals("playlist", ignoreCase = true) ||
        val itemCount = when {


    private fun extractJson(output: String): JSONObject {
            val lines = output.lineSequence().map { it.trim() }
            val firstJsonLine = lines.firstOrNull { it.startsWith("{") }
                val start = output.indexOf(firstJsonLine)
                val end = output.lastIndexOf('}')

        val start = output.indexOf('{')
        val end = output.lastIndexOf('}')


```

---

## <a name="file-dataytdlpcommandbuilderkt"></a> 📄 File: `data/YtDlpCommandBuilder.kt`
**Responsibility**: Pure Kotlin builder translating preferences into yt-dlp arguments lists.

```kotlin
package com.baynuman.ytdownloader.data

class YtDlpCommandBuilder {
    fun buildPrimaryCommand(request: DownloadRequest): List<String> {
        val effectiveTemplate = if (request.folderOrg != "None") {

        val cmd = mutableListOf(

            val quality = effectiveVideoHeight(request)
            val audioCodec = request.videoAudioCodec.trim().uppercase()
            val preferredAudioSelector: String
            val secondaryAudioSelector: String

            val videoSelector: String
            val fallbackSelector: String

            val selector = buildString {
            val audioQuality = AUDIO_PRESET_QUALITY[request.audioQualityPreset] ?: "0"




            val archivePath = request.archiveFile.takeIf { it.isNotBlank() }

            val optimized = com.baynuman.ytdownloader.data.algorithms.ClipOptimizer.optimizeClipIntervals(request.clips)


        val cookiesFile = request.cookiesFile.trim()
            val browserCookies = request.browserCookies.trim().lowercase()

        val extraArgs = parseExtraArgs(request.extraArgs)


    fun buildFallbackCommand(request: DownloadRequest): List<String> {
        val primary = buildPrimaryCommand(request)

    fun containsYoutubeUrls(urls: List<String>): Boolean {
            val lower = url.lowercase()

    fun formatForLog(cmd: List<String>): String {

    private fun effectiveVideoHeight(request: DownloadRequest): String {
        val selected = VIDEO_PRESET_HEIGHT[request.videoPreset] ?: "1080"

    private fun appendOptionsBeforeUrls(
        val optionArea = command.dropLast(urls.size)
        val urlArea = command.takeLast(urls.size)

    private fun parseExtraArgs(rawArgs: String): List<String> {
        val args = rawArgs.trim()

        val tokens = mutableListOf<String>()
        val current = StringBuilder()
        var quote: Char? = null

        fun flush() {


```

---

## <a name="file-databinaryinstallerkt"></a> 📄 File: `data/BinaryInstaller.kt`
**Responsibility**: Orchestrates JNI library initialization, checks updates on BFF update broker with PyPI fallback, and verifies package integrity.

```kotlin
package com.baynuman.ytdownloader.data

import android.content.Context
import android.os.Build
import com.yausername.ffmpeg.FFmpeg
import com.yausername.youtubedl_android.YoutubeDL
import com.yausername.youtubedl_android.YoutubeDLException

data class BinaryInstallResult(
    val ytDlpPath: String?,
    val ffmpegDir: String?,
    val abi: String,
    val message: String,

class BinaryInstaller(
    private val context: Context,
    private val prefs by lazy {

    fun installOrReuse(
        val abi = Build.SUPPORTED_ABIS.firstOrNull() ?: "unknown"
        val youtubeDL = YoutubeDL.getInstance()

            val updateMessage = maybeUpdateRuntime(


    private fun maybeUpdateRuntime(
        val nowMs = System.currentTimeMillis()
        val lastCheckMs = prefs.getLong(KEY_LAST_UPDATE_CHECK_MS, 0L)
        val shouldCheck = forceUpdate || (nowMs - lastCheckMs >= AUTO_UPDATE_INTERVAL_MS)
            val version = safeVersionName(youtubeDL)

        val updateResult = try {
            val message = exc.message?.lineSequence()?.firstOrNull()?.trim().orEmpty()


        val version = safeVersionName(youtubeDL)
        val versionSuffix = if (version != null) " Surum: $version" else ""

    private fun safeVersionName(youtubeDL: YoutubeDL): String? {

        private const val PREF_NAME = "yt_dlp_runtime"
        private const val KEY_LAST_UPDATE_CHECK_MS = "last_update_check_ms"
        private const val AUTO_UPDATE_INTERVAL_MS = 24L * 60L * 60L * 1000L

```

---

## <a name="file-dataytdlprunnerkt"></a> 📄 File: `data/YtDlpRunner.kt`
**Responsibility**: Native execution runner. Wraps NDK process, manages cancellation, and translates stdout stream into download events.

```kotlin
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

    class InsufficientStorageException(message: String) : PipelineException(message)
    class FFmpegSlicingException(message: String, cause: Throwable? = null) : PipelineException(message, cause)
    class YtDlpExecutionException(message: String) : PipelineException(message)

class YtDlpRunner(
    private val appContext: Context,
    private val commandBuilder: YtDlpCommandBuilder = YtDlpCommandBuilder(),
    @Volatile
    private var cancelRequested = false

    @Volatile
    private var activeProcessId: String? = null

    @Volatile
    private var activeSubprocess: Process? = null


        var outputDir = File(request.outputDir)
        
        var isWritable = false
                val testFile = File(outputDir, ".write_test_${UUID.randomUUID()}")

            val safeDir = appContext.getExternalFilesDir(android.os.Environment.DIRECTORY_DOWNLOADS)
            

        val normalizedRequest = request.copy(


        val initError = ensureRuntimeInitialized()

        var tempFile: File? = null

            val isClipsOperation = normalizedRequest.clips.isNotEmpty()
            val macroClips = if (isClipsOperation) {


            val primaryCommand = commandBuilder.buildPrimaryCommand(normalizedRequest)

            var result = runCommand(primaryCommand, normalizedRequest.urls, onEvent)
            val shouldFallback = (

                val fallbackCommand = commandBuilder.buildFallbackCommand(normalizedRequest)




            val downloadedFile = findDownloadedFile(outputDir, result.lastDownloadedFilePath)

            var finalSize = 0L
            var finalPath = ""

                
                val expectedSizeMb = (downloadedFile.length() / (1024 * 1024)) * 2

                val microFiles = runFFmpegSlicing(downloadedFile, macroClips, normalizedRequest, onEvent)
                
                val mergedFile = runFFmpegConcat(microFiles, outputDir, onEvent)
                
                



    fun cancel() {

    private fun ensureRuntimeInitialized(): String? {

    private fun checkStorageCapacity(outputDir: String, minMbRequired: Long) {
        val file = File(outputDir)
        val freeSpace = file.freeSpace // in bytes
        val freeMb = freeSpace / (1024 * 1024)

    private fun findDownloadedFile(outputDir: File, parsedPath: String?): File? {
            val file = File(parsedPath)
            val absoluteFile = if (file.isAbsolute) file else File(outputDir, parsedPath)

    fun getFFmpegFile(): File {
            val youtubeDLClass = com.yausername.youtubedl_android.YoutubeDL::class.java
            val ffmpegPathField = youtubeDLClass.getDeclaredField("ffmpegPath")
            val file = ffmpegPathField.get(null) as? File

        val possiblePaths = listOf(


    private suspend fun runFFmpegCommand(cmd: List<String>, onEvent: (DownloadEvent) -> Unit): Int = withContext(Dispatchers.IO) {
            val process = ProcessBuilder(cmd)
            
            
                var line: String?
            
            val exitCode = process.waitFor()

    private suspend fun runFFmpegSlicing(
        val ffmpegBin = getFFmpegFile()

        val slicedFiles = mutableListOf<File>()
        var clipIndex = 1

                
                val ext = downloadedFile.extension
                val nameWithoutExt = downloadedFile.nameWithoutExtension
                val slicedFile = File(downloadedFile.parentFile, "${nameWithoutExt}_slice_${clipIndex}.$ext")
                
                val duration = micro.end - micro.start
                
                val preciseCut = request.clipPrecise
                val isAudio = request.mode == DownloadMode.AUDIO

                val cmd = if (preciseCut) {
                        val audFmt = request.audioFormat.lowercase()
                
                val exitCode = runFFmpegCommand(cmd, onEvent)
                
        

    private suspend fun runFFmpegConcat(
            val finalFile = File(outputDir, slicedFiles[0].name.replace(Regex("_slice_\\d+"), "_merged"))

        val ffmpegBin = getFFmpegFile()
        val ext = slicedFiles[0].extension
        val firstSlicedName = slicedFiles[0].nameWithoutExtension
        val finalFile = File(outputDir, firstSlicedName.replace(Regex("_slice_\\d+"), "_merged") + ".$ext")
        
        val listFile = File(outputDir, "concat_list_${UUID.randomUUID()}.txt")
                val escapedPath = file.absolutePath.replace("'", "\\'")

            val cmd = listOf(
            
            val exitCode = runFFmpegCommand(cmd, onEvent)


    private fun cleanEmptyDirectories(path: File, baseDir: File) {
            val resolvedPath = path.canonicalFile
            val resolvedBase = baseDir.canonicalFile
            
            var folder = if (resolvedPath.isFile) resolvedPath.parentFile else resolvedPath
            
                    val children = folder.listFiles()

    private fun scanToMediaStore(file: File, onEvent: (DownloadEvent) -> Unit) {

    private fun parsePathFromLine(line: String): String? {

    private fun runCommand(
        val processId = UUID.randomUUID().toString()

        var sawHttp403 = false
        var sawOutdatedWarning = false
        var canceled = false
        var lastDownloadedFilePath: String? = null

        val options = if (urls.isEmpty()) {
        val request = YoutubeDLRequest(urls).addCommands(options)

            val response = YoutubeDL.getInstance().execute(
                val safeLine = line ?: ""
                    val parsedPath = parsePathFromLine(safeLine)

            val mergedLogs = buildString {
                val parsedPath = parsePathFromLine(line)

            val text = exc.message ?: "yt-dlp calistirilamadi"

    private data class ProcessResult(
        val exitCode: Int,
        val sawHttp403: Boolean,
        val sawOutdatedWarning: Boolean,
        val canceled: Boolean,
        val lastDownloadedFilePath: String? = null,

    private fun logRunnerEvent(event: String, level: Int = Log.INFO) {
        val payload = JSONObject()


        private const val RUNNER_TAG = "YTDownloaderRunner"
        private const val YOUTUBE_FALLBACK_EXTRACTOR_ARGS = "youtube:player-client=tv"

```

---

## <a name="file-servicedownloadservicekt"></a> 📄 File: `service/DownloadService.kt`
**Responsibility**: Android ForegroundService. Wraps worker threads in persistent notification layers for background survivability.

```kotlin
package com.baynuman.ytdownloader.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.core.app.ServiceCompat
import com.baynuman.ytdownloader.MainActivity
import com.baynuman.ytdownloader.data.DownloadEvent
import com.baynuman.ytdownloader.data.DownloadRequest
import com.baynuman.ytdownloader.data.YtDlpRunner
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlinx.coroutines.delay

class DownloadService : Service() {

    private val serviceScope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {

    private var networkCallback: android.net.ConnectivityManager.NetworkCallback? = null

    override fun onDestroy() {

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {

        val action = intent.action ?: ACTION_STOP
                val requestJson = intent.getStringExtra(EXTRA_REQUEST_JSON)
                    val title = intent.getStringExtra(EXTRA_TITLE) ?: "Downloading..."
                    val notification = buildProgressNotification(title, 0, "--", "--")

                        val request = DownloadRequest.fromJsonString(requestJson)
                val title = intent.getStringExtra(EXTRA_TITLE) ?: "Downloading..."
                val progress = intent.getIntExtra(EXTRA_PROGRESS, 0)
                val speed = intent.getStringExtra(EXTRA_SPEED) ?: "--"
                val eta = intent.getStringExtra(EXTRA_ETA) ?: "--"


    private fun registerWifiOnlyKillSwitch() {
        val cm = getSystemService(Context.CONNECTIVITY_SERVICE) as android.net.ConnectivityManager
        val request = android.net.NetworkRequest.Builder()
        
        val callback = object : android.net.ConnectivityManager.NetworkCallback() {
            override fun onCapabilitiesChanged(
                val isMetered = !networkCapabilities.hasCapability(android.net.NetworkCapabilities.NET_CAPABILITY_NOT_METERED)
                val isCellular = networkCapabilities.hasTransport(android.net.NetworkCapabilities.TRANSPORT_CELLULAR)

            override fun onLost(network: android.net.Network) {
        

    private fun unregisterWifiOnlyKillSwitch() {
                val cm = getSystemService(Context.CONNECTIVITY_SERVICE) as android.net.ConnectivityManager

    private fun startDownloadJob(request: DownloadRequest, title: String) {
        

                val runner = YtDlpRunner(applicationContext)
                
                val speedRegex = Regex("""\bat\s+([0-9.]+\s*[KMGT]?i?B/s)""", RegexOption.IGNORE_CASE)
                val etaRegex = Regex("""\bETA\s+([0-9:.]+)""", RegexOption.IGNORE_CASE)
                val batchProgressRegex = Regex("""\[download\]\s+Downloading\s+video\s+(\d+)\s+of\s+(\d+)""", RegexOption.IGNORE_CASE)
                val destRegex = Regex("""\[download\]\s+Destination:\s+(.+)""", RegexOption.IGNORE_CASE)
                val alreadyRegex = Regex("""\[download\]\s+(.+)\s+has already been downloaded""", RegexOption.IGNORE_CASE)
                val mergerRegex = Regex("""\[Merger\]\s+Merging\s+formats\s+into\s+"(.+)"""", RegexOption.IGNORE_CASE)
                
                var currentSpeed = "--"
                var currentEta = "--"
                var currentProgressPercent = 0

                val urls = request.urls
                var batchTotalCount = urls.size
                var batchCurrentIndex = 0
                var batchCompletedCount = 0
                var batchActiveTitle = if (urls.isNotEmpty()) "İndiriliyor..." else ""


                            val percent = (event.value * 100).toInt().coerceIn(0, 100)
                            val line = event.text
                            
                                val curr = match.groupValues[1].toIntOrNull()
                                val total = match.groupValues[2].toIntOrNull()

                            val destMatch = destRegex.find(line)?.groupValues?.getOrNull(1)
                                val file = java.io.File(destMatch)

                            val speedMatch = speedRegex.find(line)?.groupValues?.getOrNull(1)
                            val etaMatch = etaRegex.find(line)?.groupValues?.getOrNull(1)

    private fun cancelActiveDownload() {

    private fun stopForegroundService() {

    private var lastNotificationTime = 0L

    private fun updateNotification(
        val now = System.currentTimeMillis()
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val notification = buildProgressNotification(

    private fun buildProgressNotification(
        val intent = Intent(this, MainActivity::class.java).apply {
        val pendingIntent = PendingIntent.getActivity(

        val builder = NotificationCompat.Builder(this, CHANNEL_ID)

            val currentIdxHuman = (batchCurrentIndex + 1).coerceAtMost(batchTotalCount)
            val headline = "İndiriliyor ($currentIdxHuman/$batchTotalCount)"
            val activeText = "▶ $batchActiveTitle: $progress% ($speed)"
            val remaining = batchTotalCount - currentIdxHuman
            val summaryText = "✓ $batchCompletedCount tamamlandı, $remaining bekliyor"


            val inboxStyle = NotificationCompat.InboxStyle()
            val speedEta = if (speed != "--" || valEta != "--") {


    private fun createNotificationChannel() {
            val channel = NotificationChannel(
            val manager = getSystemService(NotificationManager::class.java)

    private fun enqueueWaveformGeneration(request: DownloadRequest, filePath: String) {
        val context = applicationContext
                val audioFile = java.io.File(filePath)

                val waveformsDir = java.io.File(context.filesDir, "waveforms")
                val uuid = java.util.UUID.randomUUID().toString()
                val outputPng = java.io.File(waveformsDir, "waveform_$uuid.png")

                val runner = YtDlpRunner(context)
                val ffmpegBin = runner.getFFmpegFile()

                val cmd = listOf(

                val process = ProcessBuilder(cmd)


                val exitCode = withContext(Dispatchers.IO) {

                    val db = com.baynuman.ytdownloader.data.db.DownloadDatabase.getDatabase(context)
                    val dao = db.downloadRecordDao()
                    
                    var rowsUpdated = 0

        private const val NOTIFICATION_ID = 4040
        private const val CHANNEL_ID = "download_progress_channel"



        val downloadEvents get() = com.baynuman.ytdownloader.data.DownloadRepository.downloadEvents
        val isRunning get() = com.baynuman.ytdownloader.data.DownloadRepository.isRunning
        
        var activeRunner: YtDlpRunner?
            
        var activeRequest: DownloadRequest?

```

---

## <a name="file-uithemecolorkt"></a> 📄 File: `ui/theme/Color.kt`
**Responsibility**: Custom palette definitions representing HSL dark and light tokens.

```kotlin
package com.baynuman.ytdownloader.ui.theme

import androidx.compose.ui.graphics.Color

val ObsidianBg = Color(0xFF090D16)
val ObsidianCard = Color(0xCD121B2D)     // Translucent dark glass
val ObsidianBorder = Color(0xFF22334F)   // Dark border glow
val SoftTextDark = Color(0xFFF8FAFC)
val MutedTextDark = Color(0xFF94A3B8)

val PastelBg = Color(0xFFF1F5F9)
val PastelCard = Color(0xCDEFEFFF)       // Translucent light glass
val PastelBorder = Color(0xFFCBD5E1)     // Light border glow
val SoftTextLight = Color(0xFF0F172A)
val MutedTextLight = Color(0xFF475569)

val AccentCyan = Color(0xFF00D2FF)
val AccentIndigo = Color(0xFF6366F1)
val AccentBlue = Color(0xFF2563EB)
val AccentGreen = Color(0xFF10B981)
val AccentRed = Color(0xFFF43F5E)

val SlateDark = ObsidianBg
val SurfaceBase = ObsidianCard
val SurfaceAlt = Color(0xFF1B2430)
val SurfaceSoft = Color(0xFF253142)
val AquaAccent = AccentCyan
val MintAccent = AccentGreen
val SoftText = SoftTextDark
val MutedText = MutedTextDark
val WarningRed = AccentRed


```

---

## <a name="file-uithemethemekt"></a> 📄 File: `ui/theme/Theme.kt`
**Responsibility**: Compose Material Theme wrapper implementing localized dark/light color schemes.

```kotlin
package com.baynuman.ytdownloader.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val DarkColors = darkColorScheme(

private val AmoledColors = darkColorScheme(

private val LightColors = lightColorScheme(

@Composable
fun YtDownloaderTheme(
    val colors = when (themeMode) {



```

---

## <a name="file-uithemetokenskt"></a> 📄 File: `ui/theme/Tokens.kt`
**Responsibility**: Visual design tokens such as corner shapes, elevation levels, and glassmorphic blur properties.

```kotlin
package com.baynuman.ytdownloader.ui.theme

import androidx.compose.ui.unit.dp

object AppSpacing {
    val xs = 8.dp
    val sm = 12.dp
    val md = 16.dp
    val lg = 24.dp

object AppRadius {
    val md = 12.dp
    val lg = 16.dp

```

---

## <a name="file-uithemetranslationskt"></a> 📄 File: `ui/theme/Translations.kt`
**Responsibility**: Comprehensive three-tiered localization translations (EN, TR, ES).

```kotlin
package com.baynuman.ytdownloader.ui.theme

object Translations { /* Android Translation tokens stripped */ }
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
    
    val currentLanguage: String = "en",
    val isDarkTheme: Boolean = true,
    val themeMode: String = "DARK",
    val isBatchMode: Boolean = false,
    val clipTextDetected: String = "",
    val activeTab: Int = 0,
    val historyRecords: List<DownloadRecord> = emptyList(),
    val clipEnabled: Boolean = false,
    val clipStart: String = "00:00",
    val clipEnd: String = "00:00",
    val wifiOnly: Boolean = false,
    val schedulerEnabled: Boolean = false,
    val schedulerTime: String = "03:00",
    val showDuplicateDialog: Boolean = false,
    val duplicateTaskRequest: DownloadRequest? = null,
    val folderOrg: String = "None",
    val clipPrecise: Boolean = false,
    val compactMode: Boolean = false

data class RuntimeState(
    val historyRecords: List<DownloadRecord> = emptyList(),
    val activeTab: Int = 0,
    val isDarkTheme: Boolean = true,
    val themeMode: String = "DARK",
    val currentLanguage: String = "en",
    val binaryStatus: String = "yt-dlp otomatik hazirlaniyor...",
    val detectedAbi: String = "",
    val executablePath: String = "internal://youtubedl-android",
    val ffmpegLocation: String = "",
    val mediaPermissionsGranted: Boolean = false,
    val showDiagnostics: Boolean = false,
    val showFullOutputPath: Boolean = false,
    val showDuplicateDialog: Boolean = false,
    val duplicateTaskRequest: DownloadRequest? = null,

class DownloaderViewModel(application: Application) : AndroidViewModel(application) {
    private val appContext = application.applicationContext
    private val prefs = appContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    private var lastStartedUrl: String = ""
    private val binaryInstaller = BinaryInstaller(appContext)
    private val previewResolver = UrlPreviewResolver(appContext)
    private var previewJob: Job? = null
    private var latestThumbnailPath: String? = null

    private val database = DownloadDatabase.getDatabase(appContext)
    private val recordDao = database.downloadRecordDao()
    private val channelRuleDao = database.channelRuleDao()
    private var previewChannelId: String? = null
    private val queueMutex = Mutex()
    private val logBuffer = java.util.ArrayDeque<String>(300)
    private val logMutex = Mutex()

    private val _preferencesState = MutableStateFlow(buildInitialPreferencesState(application))
    val preferencesState = _preferencesState.asStateFlow()

    private val _activeTaskState = MutableStateFlow(ActiveTaskState())
    val activeTaskState = _activeTaskState.asStateFlow()

    private val _formValidationState = MutableStateFlow(FormValidationState())
    val formValidationState = _formValidationState.asStateFlow()

    private val _runtimeState = MutableStateFlow(

    val uiState: StateFlow<DownloaderUiState> = combine(




                        val progressVal = event.value.coerceIn(0f, 1f)
                            val activeRequest = com.baynuman.ytdownloader.data.DownloadRepository.activeRequest
                            val currentUrl = lastStartedUrl.ifBlank { activeRequest?.urls?.firstOrNull() ?: "" }
                            val finalTitle = if (_formValidationState.value.previewTitle.isNotBlank()) {
                            val taskId = activeRequest?.taskId ?: java.util.UUID.randomUUID().toString()

    private fun defaultOutputDir(application: Application): String {
        val fallback = application
        val saved = prefs.getString(KEY_OUTPUT_DIR, null)?.trim().orEmpty()

    private fun buildInitialPreferencesState(application: Application): DownloadPreferencesState {

    private fun buildInitialState(application: Application): DownloaderUiState {
        val savedLang = prefs.getString("current_language", null)
        val savedTheme = prefs.getBoolean("is_dark_theme", true)
        val savedThemeMode = prefs.getString("theme_mode", null) ?: if (savedTheme) "DARK" else "LIGHT"

    private fun observeHistoryDatabase() {
                val records = entities.map { it.toDomainModel() }

    fun bootstrapEmbeddedBinaries(forceUpdate: Boolean = false) {
            val result = withContext(Dispatchers.IO) {
            

    fun updateLanguage(value: String) {

    fun toggleTheme() {
        val current = _runtimeState.value.themeMode
        val next = when (current) {

    fun toggleBatchMode() {

    fun toggleCompactMode() {
        val next = !_preferencesState.value.compactMode

    fun toggleClipPrecise() {
        val next = !_preferencesState.value.clipPrecise

    fun addToQueueWithoutStarting() {
        val currentInput = _formValidationState.value.urlsText.trim()
        
        
        val nextText = if (currentInput.endsWith("\n")) {

    fun removeUrlFromBatch(index: Int) {
        val urls = parseUrls(_formValidationState.value.urlsText)
            val updatedUrls = urls.toMutableList().apply { removeAt(index) }
            val nextText = updatedUrls.joinToString("\n")

    fun reorderBatchUrls(fromIndex: Int, toIndex: Int) {
        val urls = parseUrls(_formValidationState.value.urlsText).toMutableList()
        val activeIndex = _activeTaskState.value.playlistProgressText.substringBefore("/").toIntOrNull()?.let { it - 1 } ?: 0
        val isDownloading = _activeTaskState.value.isRunning
        
        
            val item = urls.removeAt(fromIndex)
            val nextText = urls.joinToString("\n")

    fun checkClipboardForYoutubeLink() {
            val clipboard = appContext.getSystemService(Context.CLIPBOARD_SERVICE) as? ClipboardManager
            val pasted = clipboard

    fun pasteDetectedClipboardUrl() {
        val detected = _formValidationState.value.clipTextDetected
            val current = _formValidationState.value.urlsText.trim()
            val nextText = if (current.isEmpty()) {

    fun updateUrlsText(value: String) {

    fun clearUrl() {

    fun pasteUrlFromClipboard() {
        val clipboard = appContext.getSystemService(Context.CLIPBOARD_SERVICE) as? ClipboardManager
        val pasted = clipboard


    fun updateOutputDir(value: String) {
        val sanitized = value.trim()

    fun updateMode(value: DownloadMode) { _preferencesState.update { it.copy(mode = value, userExplicit = true) } }
    fun updateVideoPreset(value: String) { _preferencesState.update { it.copy(videoPreset = value, userExplicit = true) } }
    fun updateCustomVideoHeight(value: String) = _preferencesState.update { it.copy(customVideoHeight = value) }
    fun updateVideoContainer(value: String) { _preferencesState.update { it.copy(videoContainer = value, userExplicit = true) } }
    fun updateVideoAudioCodec(value: String) { _preferencesState.update { it.copy(videoAudioCodec = value, userExplicit = true) } }
    fun updateAudioFormat(value: String) { _preferencesState.update { it.copy(audioFormat = value, userExplicit = true) } }
    fun updateAudioQualityPreset(value: String) { _preferencesState.update { it.copy(audioQualityPreset = value, userExplicit = true) } }
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
    fun updateFolderOrg(value: String) = _preferencesState.update { it.copy(folderOrg = value, userExplicit = true) }
    fun updateClipEnabled(value: Boolean) = _preferencesState.update { it.copy(clipEnabled = value) }
    fun updateClipStart(value: String) = _preferencesState.update { it.copy(clipStart = value) }
    fun updateClipEnd(value: String) = _preferencesState.update { it.copy(clipEnd = value) }
    fun updateWifiOnly(value: Boolean) = _preferencesState.update { it.copy(wifiOnly = value) }
    fun updateSchedulerEnabled(value: Boolean) = _preferencesState.update { it.copy(schedulerEnabled = value) }
    fun updateSchedulerTime(value: String) = _preferencesState.update { it.copy(schedulerTime = value) }
    fun dismissDuplicateDialog() = _runtimeState.update { it.copy(showDuplicateDialog = false, duplicateTaskRequest = null) }
    
    fun updateMediaPermissionsStatus(value: Boolean) {
        val previous = _runtimeState.value.mediaPermissionsGranted

    fun setIncomingSharedText(sharedText: String?) {
        val incoming = extractFirstUrl(sharedText.orEmpty()) ?: return

    fun importFromSharedBuffer() {
        val shared = _formValidationState.value.sharedUrlBuffer

    fun useDefaultOutputDir() {
        val app = getApplication<Application>()
        val defaultOutputDir = app

    fun updateOutputDirFromTreeUri(uri: Uri?) {
        val resolvedPath = resolvePathFromTreeUri(uri)

        val folder = File(resolvedPath)

    fun refreshEmbeddedBinary() {

    fun clearLogs() {

    fun importCookiesFromUri(uri: Uri?) {
            val app = getApplication<Application>()
            val destination = File(app.filesDir, "cookies/cookies.txt").apply {
            val copied = copyUriToFile(uri, destination)

    fun importYtDlpBinaryFromUri(uri: Uri?) {
            val app = getApplication<Application>()
            val destination = File(app.filesDir, "bin/yt-dlp").apply {
            val copied = copyUriToFile(uri, destination)

    fun cancelDownload() {
            val intent = Intent(appContext, com.baynuman.ytdownloader.service.DownloadService::class.java).apply {

    private fun extractVideoId(url: String): String? {
        val regexes = listOf(
            val match = regex.find(url)

    fun startDownload() {
        val prefs = _preferencesState.value
        val validation = _formValidationState.value

        val validationError = validate(prefs, validation)

        val urls = parseUrls(validation.urlsText)
        val runtime = _runtimeState.value

        val clipsList = if (prefs.clipEnabled) {
            val startSec = com.baynuman.ytdownloader.data.algorithms.ClipOptimizer.parseTimeToSeconds(prefs.clipStart)
            val endSec = com.baynuman.ytdownloader.data.algorithms.ClipOptimizer.parseTimeToSeconds(prefs.clipEnd)
                val errorMsg = com.baynuman.ytdownloader.ui.theme.Translations.get("err_trim_invalid", runtime.currentLanguage)

        val request = DownloadRequest(

                val firstUrl = urls.firstOrNull() ?: ""
                val videoId = extractVideoId(firstUrl) ?: ""
                val format = if (prefs.mode == DownloadMode.AUDIO) prefs.audioFormat else prefs.videoContainer

                val isAlreadyRunning = _activeTaskState.value.isRunning && 

                val record = if (firstUrl.isNotBlank()) {

                var fileExists = false
                    val possiblePaths = listOf(

                    var finalRequest = request
                        val rule = withContext(Dispatchers.IO) {
                                val ruleJson = org.json.JSONObject(rule.settingsJson)

    fun startDownloadActual(request: DownloadRequest) {

            
            val timeParts = request.schedulerTime.split(":")
            val hour = timeParts.getOrNull(0)?.toIntOrNull() ?: 3
            val minute = timeParts.getOrNull(1)?.toIntOrNull() ?: 0
            
            val calendar = java.util.Calendar.getInstance()
            val now = calendar.timeInMillis
            
            val target = java.util.Calendar.getInstance().apply {
            val delayMs = target.timeInMillis - now
            
            val constraints = androidx.work.Constraints.Builder().apply {

            val inputData = androidx.work.Data.Builder()

            val workRequest = androidx.work.OneTimeWorkRequestBuilder<com.baynuman.ytdownloader.service.DownloadWorker>()





        val firstUrl = request.urls.firstOrNull() ?: ""
        val activeTitle = if (_formValidationState.value.previewTitle.isNotBlank()) _formValidationState.value.previewTitle else firstUrl
        

            val intent = Intent(appContext, com.baynuman.ytdownloader.service.DownloadService::class.java).apply {

    private fun schedulePreview(rawInput: String) {
        val url = extractFirstUrl(rawInput)



            val result = withContext(Dispatchers.IO) {

    private fun downloadAndCompressThumbnail(urlString: String): String? {
            val secureUrlString = if (urlString.startsWith("http://", ignoreCase = true)) {
            val url = URL(secureUrlString)
            val connection = url.openConnection() as HttpURLConnection
            val input = connection.inputStream
            val bitmap = BitmapFactory.decodeStream(input) ?: return null
            
            val resizedBitmap = Bitmap.createScaledBitmap(bitmap, 320, 180, true)
            
            val thumbsDir = File(appContext.filesDir, "thumbnails")
            
            val hash = MessageDigest.getInstance("MD5").digest(urlString.toByteArray()).joinToString("") { "%02x".format(it) }
            val outputFile = File(thumbsDir, "thumb_$hash.webp")
            
                    @Suppress("DEPRECATION")
            
            

    private fun applyPreview(preview: UrlPreview) {
        val status = if (preview.isPlaylist) {
            val countText = preview.itemCount?.let { " - $it oge" }.orEmpty()

        val thumbUrl = preview.thumbnailUrl

        val firstUrl = extractFirstUrl(_formValidationState.value.urlsText)
            val videoId = extractYoutubeVideoId(firstUrl)
                    val segments = fetchSponsorBlockSegments(videoId)



    private fun extractYoutubeVideoId(url: String): String? {
        val cleanedUrl = url.trim()
        
        val queryPattern = Regex("[?&]v=([a-zA-Z0-9_-]{11})")
        
        val shortPattern = Regex("youtu\\.be/([a-zA-Z0-9_-]{11})")
        
        val pathPattern = Regex("(?:embed|v|shorts)/([a-zA-Z0-9_-]{11})")
        
            val generalPattern = Regex("(?:/|=)([a-zA-Z0-9_-]{11})(?:[?&/]|$)")
                val id = match.groupValues[1]
        

    private fun fetchSponsorBlockSegments(videoId: String): List<com.baynuman.ytdownloader.data.SponsorSegment> {
        val segments = mutableListOf<com.baynuman.ytdownloader.data.SponsorSegment>()
            val url = URL("https://sponsor.ajay.app/api/skipSegments?videoID=$videoId")
            val connection = url.openConnection() as HttpURLConnection
            
            val responseCode = connection.responseCode
                val response = connection.inputStream.bufferedReader().use { it.readText() }
                val array = org.json.JSONArray(response)
                    val obj = array.getJSONObject(i)
                    val segmentArr = obj.getJSONArray("segment")
                    val start = segmentArr.getDouble(0).toFloat()
                    val end = segmentArr.getDouble(1).toFloat()
                    val category = obj.optString("category", "sponsor")

    private fun mapPreviewError(msg: String?): String {
        val text = msg.orEmpty()

    private fun validate(prefs: DownloadPreferencesState, validation: FormValidationState): String? {
        val targetDir = File(prefs.outputDir.trim())
            val customHeight = prefs.customVideoHeight.trim()

    private suspend fun copyUriToFile(uri: Uri, destination: File): Boolean = withContext(Dispatchers.IO) {
        val app = getApplication<Application>()

    private fun parseUrls(raw: String): List<String> {
        val lines = raw.lineSequence()

    private fun persistOutputDir(path: String) {

    private fun resolvePathFromTreeUri(uri: Uri): String? {
                    val docId = DocumentsContract.getTreeDocumentId(uri)
                    val parts = docId.split(":")

                    val volume = parts[0].lowercase()
                    val relative = if (parts.size > 1) parts[1] else ""
                            val homeBase = File(Environment.getExternalStorageDirectory(), "Documents")
                            val volumeRoot = File("/storage/${parts[0]}")
                    val docId = DocumentsContract.getTreeDocumentId(uri)

    private fun takePersistableTreePermission(uri: Uri) {

    private fun extractFirstUrl(raw: String): String? {

    private fun isLikelyYoutubeUrl(url: String): Boolean {
        val normalized = url.trim().lowercase()

    private fun validateOptionalInt(raw: String, min: Int): Boolean {
        val value = raw.trim()
        val intValue = value.toIntOrNull() ?: return false

    private fun handleLogLine(line: String) {
        val speed = SPEED_REGEX.find(line)?.groupValues?.getOrNull(1)
        val eta = ETA_REGEX.find(line)?.groupValues?.getOrNull(1)
        val playlistProgress = PLAYLIST_REGEXES.firstNotNullOfOrNull { regex ->
        val writeAccessError = line.contains("permission denied", ignoreCase = true) ||




    fun updateActiveTab(index: Int) {

    fun addToHistory(title: String, url: String, format: String, sizeBytes: Long, thumbnailPath: String? = null, id: String? = null) {
            val recordId = id ?: java.util.UUID.randomUUID().toString()
            val entity = DownloadRecordEntity(

    fun clearHistory() {
            val thumbsDir = File(appContext.filesDir, "thumbnails")

    fun saveChannelRule(channelId: String, channelName: String) {
        val prefs = _preferencesState.value
        val settingsMap = mapOf(
        val settingsJson = org.json.JSONObject(settingsMap).toString()

    fun deleteChannelRule(channelId: String) {

    fun hasChannelRule(): Boolean {

    fun getPreviewChannelId(): String? = previewChannelId
    fun getPreviewChannelName(): String = _formValidationState.value.previewChannel

    private fun pushSpeedHistory(rawSpeedStr: String) {
        val rawMbps = parseSpeedToMbps(rawSpeedStr)
        val currentEma = _activeTaskState.value.emaSmoothed
        val smoothed = (rawMbps * 0.2f) + (currentEma * 0.8f)
        val history = _activeTaskState.value.speedHistory.toMutableList()
        val idx = _activeTaskState.value.speedWriteIdx

    private fun parseSpeedToMbps(s: String): Float {
        val cleaned = s.trim().lowercase()
        val regex = Regex("""([0-9.]+)\s*(gib|mib|kib|gb|mb|kb|b)/s""")
        val match = regex.find(cleaned) ?: return 0f
        val value = match.groupValues[1].toFloatOrNull() ?: return 0f
        val unit = match.groupValues[2]

    fun resetSpeedHistory() {

    fun deleteHistoryRecord(id: String, thumbnailPath: String?) {
                val file = File(thumbnailPath)

    private fun appendLog(line: String) {
                val lines = line.split("\n")
                val newLogs = logBuffer.joinToString("\n") + if (logBuffer.isNotEmpty()) "\n" else ""

    private fun telemetry(event: String) {

        private const val TELEMETRY_TAG = "YTDownloaderTelemetry"
        private const val PREFS_NAME = "downloader_ui"
        private const val KEY_OUTPUT_DIR = "output_dir"
        private val SPEED_REGEX = Regex("""\bat\s+([0-9.]+\s*[KMGT]?i?B/s)""", RegexOption.IGNORE_CASE)
        private val ETA_REGEX = Regex("""ETA\s+([0-9:]+)""", RegexOption.IGNORE_CASE)
        private val PLAYLIST_REGEXES = listOf(
        val sharedUrlBuffer: MutableSharedFlow<String> = MutableSharedFlow(extraBufferCapacity = 8)

```

---

## <a name="file-uidownloaderscreenkt"></a> 📄 File: `ui/DownloaderScreen.kt`
**Responsibility**: Main declarative layout screen containing URL fields, preview cards, queue selectors, settings sheet, and toast notifications.

```kotlin
package com.baynuman.ytdownloader.ui

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.gestures.detectDragGesturesAfterLongPress
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PlayCircle
import androidx.compose.material.icons.filled.DragHandle
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.outlined.ArrowDropDown
import androidx.compose.material.icons.outlined.Clear
import androidx.compose.material.icons.outlined.ContentPaste
import androidx.compose.material.icons.outlined.Info
import android.content.Context
import android.content.Intent
import androidx.compose.material.icons.outlined.Share
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.input.pointer.PointerInputChange
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.State
import androidx.compose.runtime.collectAsState
import coil.compose.AsyncImage
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.draw.clip
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.baynuman.ytdownloader.data.AUDIO_FORMAT_OPTIONS
import com.baynuman.ytdownloader.data.AUDIO_PRESET_QUALITY
import com.baynuman.ytdownloader.data.BROWSER_COOKIE_SOURCES
import com.baynuman.ytdownloader.data.DownloadMode
import com.baynuman.ytdownloader.data.VIDEO_AUDIO_CODEC_OPTIONS
import com.baynuman.ytdownloader.data.VIDEO_CONTAINER_OPTIONS
import com.baynuman.ytdownloader.data.VIDEO_LIMIT_OPTIONS
import com.baynuman.ytdownloader.data.VIDEO_PRESET_HEIGHT
import com.baynuman.ytdownloader.ui.theme.AppRadius
import com.baynuman.ytdownloader.ui.theme.AppSpacing
import com.baynuman.ytdownloader.ui.theme.Translations
import com.baynuman.ytdownloader.ui.theme.AccentCyan
import com.baynuman.ytdownloader.ui.theme.AccentIndigo
import com.baynuman.ytdownloader.ui.theme.AccentBlue
import com.baynuman.ytdownloader.ui.theme.AccentGreen
import com.baynuman.ytdownloader.ui.theme.AccentRed
import com.baynuman.ytdownloader.ui.theme.ObsidianBg
import com.baynuman.ytdownloader.ui.theme.PastelBg

data class PickerData(
    val title: String,
    val options: List<String>,
    val onSelect: (String) -> Unit

val LocalShowPicker = androidx.compose.runtime.staticCompositionLocalOf<(PickerData) -> Unit> { { } }

@Composable
@OptIn(ExperimentalMaterial3Api::class)
fun DownloaderScreen(
    val animatedProgress by animateFloatAsState(
    var showLogSheet by remember { mutableStateOf(false) }
    var activePickerData by remember { mutableStateOf<PickerData?>(null) }
    val lang = state.currentLanguage
    val haptic = LocalHapticFeedback.current
    val context = LocalContext.current

    val lifecycleOwner = androidx.lifecycle.compose.LocalLifecycleOwner.current
        val observer = androidx.lifecycle.LifecycleEventObserver { _, event ->

    val bgBrush = Brush.verticalGradient(

        val req = state.duplicateTaskRequest
        val titleVal = state.previewTitle.takeIf { it.isNotBlank() } ?: req.urls.firstOrNull() ?: ""
        val formatVal = if (req.mode == DownloadMode.AUDIO) req.audioFormat else req.videoContainer
        
                val rawBody = Translations.get("lbl_duplicate_body", lang)
                val body = rawBody


                    val urlsList = remember(state.urlsText) {


                                val url = urlsList[index]
                                val activeIndex = state.playlistProgressText.substringBefore("/").toIntOrNull()?.let { it - 1 } ?: 0
                                val isActive = state.isRunning && activeIndex == index
                                val isPinned = state.isRunning && index <= activeIndex
                                
                                var offsetY by remember { mutableStateOf(0f) }
                                val density = androidx.compose.ui.platform.LocalDensity.current.density
                                
                                                    val threshold = 56f
                    val formatter = remember { java.text.SimpleDateFormat("dd/MM/yyyy HH:mm", java.util.Locale.getDefault()) }

                                val record = state.historyRecords[index]
                                val recordDate: java.util.Date = java.util.Date(record.downloadedAt)
                                val dateStr = formatter.format(recordDate)
                                
                                            val isWaveform = record.thumbnailPath.contains("waveform_")
                                            val imageWidth = 100.dp
                                            val imageHeight = if (isWaveform) 19.dp else 56.dp
                                            val imageScale = if (isWaveform) ContentScale.FillBounds else ContentScale.Crop

                                                            val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as? android.content.ClipboardManager
                                                            val clip = android.content.ClipData.newPlainText("Copied URL", record.url)
                                                            val intent = Intent(Intent.ACTION_SEND).apply {
                                                val isSelected = code == lang

                val scrollState = rememberScrollState()

                
                        val option = data.options[index]

@Composable
private fun HeaderCard(
    val haptic = LocalHapticFeedback.current
                
                            val isSelected = code == lang


@Composable
private fun SourceSection(
    val haptic = LocalHapticFeedback.current


                val errorMsg = state.errorText?.let { Translations.get(it, lang) }



                    val count = state.previewItemCount?.let { " - $it oge" }.orEmpty()
                            val chId = viewModel.getPreviewChannelId() ?: return@TextButton
                            val chName = viewModel.getPreviewChannelName()

@Composable
private fun PresetSection(
    val haptic = LocalHapticFeedback.current

@Composable
private fun PresetButton(

@Composable
private fun OutputSection(

        val videoOptionsEnabled = state.mode == DownloadMode.VIDEO
        val alphaVideo = if (videoOptionsEnabled) 1f else 0.45f


            val customHeightEnabled = videoOptionsEnabled && state.videoPreset == "Ozel"
            val alphaCustom = if (customHeightEnabled) 1f else 0.45f


        val audioOptionsEnabled = state.mode == DownloadMode.AUDIO
        val alphaAudio = if (audioOptionsEnabled) 1f else 0.45f




@Composable
private fun StorageSection(

        val context = LocalContext.current




@Composable
private fun AdvancedSection(
    var activeTab by remember { mutableStateOf(0) }
    val haptic = LocalHapticFeedback.current

            val tabs = listOf("tab_codecs", "tab_limits", "tab_flags", "sec_trimming", "tab_scheduling")
                val selected = activeTab == index


                
                val folderOrgKeys = listOf("None", "Channel", "Year", "Format", "Channel_Year")
                val folderOrgOptions = folderOrgKeys.map { key ->
                val currentFolderOrgText = when (state.folderOrg) {

                        val idx = folderOrgOptions.indexOf(selectedText)

@Composable
private fun DiagnosticsSection(
            val runtimeFailed = state.binaryStatus.contains("hazirlanamadi", ignoreCase = true) ||

@Composable
private fun StickyDownloadBar(
                
                

                val cf = state.concurrentFragments.toIntOrNull() ?: 1

                val taskStateForGraph = viewModel.activeTaskState.collectAsState()

@Composable
private fun SpeedSparkline(
    val accentColor = AccentCyan
    val gridColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f)

        val state = taskState.value
        val history = state.speedHistory
        val writeIdx = state.speedWriteIdx

        val ordered = if (writeIdx < history.size) {
        val maxVal = (ordered.maxOrNull() ?: 0f).coerceAtLeast(0.01f)

            val y = size.height * (1f - i / 4f)

            val linePath = Path()
                val x = (idx.toFloat() / (ordered.size - 1).coerceAtLeast(1).toFloat()) * size.width
                val y = size.height - (value / maxVal) * (size.height - 4f)

            val fillPath = Path().apply {

@Composable
private fun SectionCard(

@Composable
private fun ExpandableSectionCard(

@Composable
private fun LabeledTextField(

@Composable
private fun ToggleRow(

@Composable
private fun OptionPicker(
    val haptic = LocalHapticFeedback.current
    val showPicker = LocalShowPicker.current


private fun buildOutputSummary(state: DownloaderUiState, lang: String): String {
    val selectedText = if (lang == "tr") "Seçilen" else if (lang == "es") "Seleccionado" else "Selected"
        val quality = VIDEO_PRESET_HEIGHT[state.videoPreset]?.let {
        val qualityText = if (quality == "Best") "Best" else "${quality}p"

private fun shortPath(path: String): String {
    val normalized = path.replace('\\', '/')
    val marker = "/Download/"

private fun DownloaderUiState.statusLabel(): String {

private fun DownloaderUiState.primaryCtaLabel(): String {

private fun DownloaderUiState.progressMeta(lang: String): String {
    val percent = "${(progress * 100).toInt()}%"
            val etaValue = if (etaText == "--") "ETA --" else "ETA $etaText"
            val playlist = if (playlistProgressText.isNotBlank()) " - $playlistProgressText" else ""

private fun openDownloadFolder(context: android.content.Context, outputDir: String) {
    val normalized = outputDir.replace('\\', '/')
    val isDownloadDir = normalized.contains("/Download", ignoreCase = true)
    
    val primaryUri = if (isDownloadDir) {

    val strategies = listOf(

            val intent = strategy()
    

@Composable
fun SegmentedProgressBar(
    val isCompleted = !isRunning && progress >= 1f
    val barColor by animateColorAsState(
    
    val trackColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)

        val width = size.width
        val height = size.height

            val fillWidth = width * progress
            val gap = 4.dp.toPx()
            val segWidth = (width - (segmentsCount - 1) * gap) / segmentsCount

                val segProgress = ((progress - (i.toFloat() / segmentsCount)) * segmentsCount).coerceIn(0f, 1f)
                val x0 = i * (segWidth + gap)
                

                    val filledW = segWidth * segProgress
                    val segColor = if (isCompleted) {

```

---