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
        super.onCreate(savedInstanceState)

        setContent {
            val downloaderViewModel: DownloaderViewModel = viewModel()
            val state by downloaderViewModel.uiState.collectAsStateWithLifecycle()

            YtDownloaderTheme(themeMode = state.themeMode) {
                val context = LocalContext.current

                val permissionsLauncher = rememberLauncherForActivityResult(
                    contract = ActivityResultContracts.RequestMultiplePermissions(),
                ) { result ->
                    val granted = result.values.all { it }
                    downloaderViewModel.updateMediaPermissionsStatus(granted)
                }

                val cookiesFileLauncher = rememberLauncherForActivityResult(
                    contract = ActivityResultContracts.GetContent(),
                ) { uri ->
                    downloaderViewModel.importCookiesFromUri(uri)
                }

                val ytDlpFileLauncher = rememberLauncherForActivityResult(
                    contract = ActivityResultContracts.GetContent(),
                ) { uri ->
                    downloaderViewModel.importYtDlpBinaryFromUri(uri)
                }

                val folderLauncher = rememberLauncherForActivityResult(
                    contract = ActivityResultContracts.OpenDocumentTree(),
                ) { uri ->
                    downloaderViewModel.updateOutputDirFromTreeUri(uri)
                }

                LaunchedEffect(Unit) {
                    val hasPerms = hasMediaPermissions(context)
                    downloaderViewModel.updateMediaPermissionsStatus(hasPerms)
                    downloaderViewModel.setIncomingSharedText(extractSharedText(intent))
                    if (!hasPerms) {
                        val permissions = requiredMediaPermissions()
                        if (permissions.isNotEmpty()) {
                            permissionsLauncher.launch(permissions)
                        }
                    }
                }

                DownloaderScreen(
                    state = state,
                    viewModel = downloaderViewModel,
                    onPickCookiesFile = { cookiesFileLauncher.launch("*/*") },
                    onPickYtDlpBinary = { ytDlpFileLauncher.launch("*/*") },
                    onPickOutputFolder = { folderLauncher.launch(null) },
                    onRequestMediaPermissions = {
                        val permissions = requiredMediaPermissions()
                        if (permissions.isEmpty()) {
                            downloaderViewModel.updateMediaPermissionsStatus(true)
                        } else {
                            permissionsLauncher.launch(permissions)
                        }
                    },
                )
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        extractSharedText(intent)?.let { text ->
            DownloaderViewModel.sharedUrlBuffer.tryEmit(text)
        }
    }
}

private fun requiredMediaPermissions(): Array<String> {
    val list = mutableListOf<String>()
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        list.add(Manifest.permission.READ_MEDIA_VIDEO)
        list.add(Manifest.permission.READ_MEDIA_AUDIO)
        // Add notification permission on Android 13+ to show background download alerts
        list.add(Manifest.permission.POST_NOTIFICATIONS)
    } else {
        list.add(Manifest.permission.READ_EXTERNAL_STORAGE)
    }
    return list.toTypedArray()
}

private fun hasMediaPermissions(context: Context): Boolean {
    val permissions = requiredMediaPermissions()
    if (permissions.isEmpty()) {
        return true
    }
    return permissions.all { permission ->
        ContextCompat.checkSelfPermission(context, permission) == PackageManager.PERMISSION_GRANTED
    }
}

private fun extractSharedText(intent: Intent?): String? {
    if (intent == null) {
        return null
    }
    if (intent.action != Intent.ACTION_SEND) {
        return null
    }
    if (intent.type != "text/plain") {
        return null
    }
    val rawText = intent.getStringExtra(Intent.EXTRA_TEXT) ?: return null
    // Extract pure HTTP/HTTPS URL from any complex shared description texts
    val regex = Regex("""https?://[\w./\-?=&%+#]+""")
    val match = regex.find(rawText) ?: return null
    val urlStr = match.value
    
    // Parse URL and validate host (whitelist gateway security verification - S2)
    try {
        val uri = android.net.Uri.parse(urlStr)
        val host = uri.host?.lowercase() ?: ""
        val whitelist = listOf("youtube.com", "youtu.be", "vimeo.com", "tiktok.com", "instagram.com")
        val isValid = whitelist.any { allowed -> host == allowed || host.endsWith(".$allowed") }
        if (isValid) {
            return urlStr
        }
    } catch (_: Exception) {}
    
    return null
}

```

---

## <a name="file-datadownloadmodelskt"></a> 📄 File: `data/DownloadModels.kt`
**Responsibility**: Dataclasses for download tasks, states, download formats, and app preferences.

```kotlin
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
)

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
    val errorText: String? = null,
    val sponsorSegments: List<SponsorSegment> = emptyList()
)

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
            _activeRunner = value
        }
        
    var activeRequest: DownloadRequest?
        @Synchronized get() = _activeRequest
        @Synchronized set(value) {
            _activeRequest = value
        }
}

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
) {
    fun toDomainModel(): DownloadRecord {
        return DownloadRecord(
            id = id,
            title = title,
            url = url,
            format = format,
            downloadedAt = downloadedAt,
            fileSizeBytes = fileSizeBytes,
            thumbnailPath = thumbnailPath
        )
    }

    companion object {
        fun fromDomainModel(record: DownloadRecord): DownloadRecordEntity {
            return DownloadRecordEntity(
                id = record.id,
                title = record.title,
                url = record.url,
                format = record.format,
                downloadedAt = record.downloadedAt,
                fileSizeBytes = record.fileSizeBytes,
                thumbnailPath = record.thumbnailPath
            )
        }
    }
}

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
}

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
)

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
}

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
abstract class DownloadDatabase : RoomDatabase() {
    abstract fun downloadRecordDao(): DownloadRecordDao
    abstract fun channelRuleDao(): ChannelRuleDao

    companion object {
        @Volatile
        private var INSTANCE: DownloadDatabase? = null

        val MIGRATION_1_2 = object : Migration(1, 2) {
            override fun migrate(db: SupportSQLiteDatabase) {
                db.execSQL("ALTER TABLE download_history ADD COLUMN thumbnail_path TEXT DEFAULT NULL")
            }
        }

        val MIGRATION_2_3 = object : Migration(2, 3) {
            override fun migrate(db: SupportSQLiteDatabase) {
                db.execSQL("""
                    CREATE TABLE IF NOT EXISTS channel_rules (
                        channelId TEXT NOT NULL PRIMARY KEY,
                        channel_name TEXT NOT NULL,
                        settings_json TEXT NOT NULL,
                        created_at INTEGER NOT NULL DEFAULT 0,
                        updated_at INTEGER NOT NULL DEFAULT 0
                    )
                """.trimIndent())
            }
        }

        fun getDatabase(context: Context): DownloadDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    DownloadDatabase::class.java,
                    "download_records_database"
                )
                .addMigrations(MIGRATION_1_2, MIGRATION_2_3)
                .build()
                INSTANCE = instance
                instance
            }
        }
    }
}

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
)

data class MacroClip(
    val start: Float,
    val end: Float,
    val subClips: List<MicroClip>
)

object ClipOptimizer {
    /**
     * Greedy Interval Merging (LeetCode 56) algorithm implementation in Kotlin.
     * Merges micro-clips whose start times are close within thresholdSec to minimize download network requests.
     */
    fun optimizeClipIntervals(clips: List<MicroClip>, thresholdSec: Float = 30f): List<MacroClip> {
        if (clips.isEmpty()) return emptyList()
        val sorted = clips.sortedBy { it.start }
        val merged = mutableListOf<MacroClip>()

        var currentStart = sorted[0].start
        var currentEnd = sorted[0].end
        val currentSubClips = mutableListOf(sorted[0])

        for (i in 1 until sorted.size) {
            val next = sorted[i]
            if (next.start <= currentEnd + thresholdSec) {
                // Merge overlapping or close interval ranges
                currentEnd = maxOf(currentEnd, next.end)
                currentSubClips.add(next)
            } else {
                // Emit current MacroClip and initialize a new range
                merged.add(MacroClip(currentStart, currentEnd, currentSubClips.toList()))
                currentSubClips.clear()
                currentStart = next.start
                currentEnd = next.end
                currentSubClips.add(next)
            }
        }
        merged.add(MacroClip(currentStart, currentEnd, currentSubClips.toList()))
        return merged
    }

    fun parseTimeToSeconds(s: String): Float? {
        val clean = s.trim()
        if (clean.isEmpty()) return null
        if (":" in clean) {
            val parts = clean.split(":")
            return try {
                if (parts.size == 2) {
                    parts[0].toInt() * 60f + parts[1].toFloat()
                } else if (parts.size == 3) {
                    parts[0].toInt() * 3600f + parts[1].toInt() * 60f + parts[2].toFloat()
                } else {
                    null
                }
            } catch (e: NumberFormatException) {
                null
            }
        }
        return try {
            clean.toFloat()
        } catch (e: NumberFormatException) {
            null
        }
    }
}

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
    /**
     * Natively scans local downloaded files into Android MediaStore.
     * This ensures the files immediately appear inside native apps like Gallery, Photos, or Music players.
     */
    fun scanFile(context: Context, filePath: String, onScanComplete: (Uri?) -> Unit = {}) {
        try {
            MediaScannerConnection.scanFile(
                context.applicationContext,
                arrayOf(filePath),
                null
            ) { _, uri ->
                onScanComplete(uri)
            }
        } catch (e: Exception) {
            Log.e("MediaStoreScanner", "Failed to scan file via MediaScanner", e)
            onScanComplete(null)
        }
    }
}

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
)

class UrlPreviewResolver(
    private val appContext: Context,
) {
    fun resolve(url: String): UrlPreview {
        val youtubeDL = YoutubeDL.getInstance()

        val request = YoutubeDLRequest(url).addCommands(
            listOf(
                "--dump-single-json",
                "--skip-download",
                "--no-warnings",
                "--no-call-home",
            ),
        )
        val response = youtubeDL.execute(request, "preview-${UUID.randomUUID()}")
        if (response.exitCode != 0) {
            val error = (response.err + "\n" + response.out).trim()
            throw YoutubeDLException(
                if (error.isEmpty()) "Baglanti bilgiisi alinamadi." else error,
            )
        }

        val json = extractJson(response.out)
        val title = json.optString("title").ifEmpty {
            json.optString("fulltitle")
        }.ifEmpty {
            "Baslik alinamadi"
        }
        val channel = json.optString("uploader").ifEmpty {
            json.optString("channel")
        }.ifEmpty {
            "Kanal alinamadi"
        }

        val thumbnailUrl = json.optString("thumbnail").takeIf { it.isNotBlank() }
            ?: json.optJSONArray("thumbnails")?.optJSONObject(0)?.optString("url")

        val channelId = json.optString("channel_id").takeIf { it.isNotBlank() }
            ?: json.optString("uploader_id").takeIf { it.isNotBlank() }

        val entries = json.optJSONArray("entries")
        val isPlaylist = json.optString("_type").equals("playlist", ignoreCase = true) ||
            url.contains("list=", ignoreCase = true)
        val itemCount = when {
            entries != null -> entries.length()
            json.has("playlist_count") -> json.optInt("playlist_count").takeIf { it > 0 }
            else -> null
        }

        return UrlPreview(
            title = title,
            channel = channel,
            isPlaylist = isPlaylist,
            itemCount = itemCount,
            thumbnailUrl = thumbnailUrl,
            channelId = channelId
        )
    }

    private fun extractJson(output: String): JSONObject {
        try {
            // Find the line that begins the JSON output to bypass warning prefixes
            val lines = output.lineSequence().map { it.trim() }
            val firstJsonLine = lines.firstOrNull { it.startsWith("{") }
            if (firstJsonLine != null) {
                val start = output.indexOf(firstJsonLine)
                val end = output.lastIndexOf('}')
                if (start >= 0 && end > start) {
                    return JSONObject(output.substring(start, end + 1))
                }
            }
        } catch (_: Exception) {}

        // Fallback robust brace-matching
        val start = output.indexOf('{')
        val end = output.lastIndexOf('}')
        if (start >= 0 && end > start) {
            try {
                return JSONObject(output.substring(start, end + 1))
            } catch (e: Exception) {
                throw YoutubeDLException("Baglanti verisi okunamadi: ${e.message}")
            }
        }

        throw YoutubeDLException("Baglanti verisi okunamadi.")
    }
}

```

---

## <a name="file-dataytdlpcommandbuilderkt"></a> 📄 File: `data/YtDlpCommandBuilder.kt`
**Responsibility**: Pure Kotlin builder translating preferences into yt-dlp arguments lists.

```kotlin
package com.baynuman.ytdownloader.data

class YtDlpCommandBuilder {
    fun buildPrimaryCommand(request: DownloadRequest): List<String> {
        val effectiveTemplate = if (request.folderOrg != "None") {
            when (request.folderOrg) {
                "Channel" -> "%(uploader).30s/%(title).70s [%(id)s].%(ext)s"
                "Year" -> "%(upload_date>%Y)s/%(title).70s [%(id)s].%(ext)s"
                "Format" -> "%(ext)s/%(title).70s [%(id)s].%(ext)s"
                "Channel_Year" -> "%(uploader).30s/%(upload_date>%Y)s/%(title).70s [%(id)s].%(ext)s"
                else -> request.outputTemplate.ifBlank { DEFAULT_OUTPUT_TEMPLATE }
            }
        } else {
            request.outputTemplate.ifBlank { DEFAULT_OUTPUT_TEMPLATE }
        }

        val cmd = mutableListOf(
            "--newline",
            "-P",
            request.outputDir,
            "-o",
            effectiveTemplate,
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
        if (request.restrictNames || request.folderOrg != "None") {
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
)

class BinaryInstaller(
    private val context: Context,
) {
    private val prefs by lazy {
        context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)
    }

    fun installOrReuse(
        forceUpdate: Boolean = false,
        onStatus: (String) -> Unit = {},
    ): BinaryInstallResult {
        val abi = Build.SUPPORTED_ABIS.firstOrNull() ?: "unknown"
        val youtubeDL = YoutubeDL.getInstance()

        return try {
            onStatus("yt-dlp runtime baslatiliyor...")
            youtubeDL.init(context)
            FFmpeg.getInstance().init(context)
            onStatus("yt-dlp runtime hazir.")
            val updateMessage = maybeUpdateRuntime(
                youtubeDL = youtubeDL,
                forceUpdate = forceUpdate,
                onStatus = onStatus,
            )

            BinaryInstallResult(
                ytDlpPath = "internal://youtubedl-android",
                ffmpegDir = null,
                abi = abi,
                message = "yt-dlp dahili runtime hazir. $updateMessage",
            )
        } catch (exc: YoutubeDLException) {
            BinaryInstallResult(
                ytDlpPath = null,
                ffmpegDir = null,
                abi = abi,
                message = "yt-dlp hazirlanamadi: ${exc.message ?: "bilinmeyen hata"}",
            )
        } catch (exc: Exception) {
            BinaryInstallResult(
                ytDlpPath = null,
                ffmpegDir = null,
                abi = abi,
                message = "yt-dlp hazirlanamadi: ${exc.message ?: "bilinmeyen hata"}",
            )
        }
    }

    private fun maybeUpdateRuntime(
        youtubeDL: YoutubeDL,
        forceUpdate: Boolean,
        onStatus: (String) -> Unit,
    ): String {
        val nowMs = System.currentTimeMillis()
        val lastCheckMs = prefs.getLong(KEY_LAST_UPDATE_CHECK_MS, 0L)
        val shouldCheck = forceUpdate || (nowMs - lastCheckMs >= AUTO_UPDATE_INTERVAL_MS)
        if (!shouldCheck) {
            val version = safeVersionName(youtubeDL)
            return if (version != null) {
                "Surum: $version"
            } else {
                "Surum bilgisi alinamadi."
            }
        }

        onStatus("yt-dlp guncelleme kontrolu...")
        val updateResult = try {
            when (youtubeDL.updateYoutubeDL(context, YoutubeDL.UpdateChannel._STABLE)) {
                YoutubeDL.UpdateStatus.DONE -> "yt-dlp guncellendi."
                YoutubeDL.UpdateStatus.ALREADY_UP_TO_DATE -> "yt-dlp guncel."
                else -> "yt-dlp guncelleme sonucu alinmadi."
            }
        } catch (exc: Exception) {
            val message = exc.message?.lineSequence()?.firstOrNull()?.trim().orEmpty()
            if (message.isNotEmpty()) {
                "yt-dlp guncelleme denemesi basarisiz: $message"
            } else {
                "yt-dlp guncelleme denemesi basarisiz."
            }
        }

        prefs.edit().putLong(KEY_LAST_UPDATE_CHECK_MS, nowMs).apply()

        val version = safeVersionName(youtubeDL)
        val versionSuffix = if (version != null) " Surum: $version" else ""
        return "$updateResult$versionSuffix"
    }

    private fun safeVersionName(youtubeDL: YoutubeDL): String? {
        return try {
            youtubeDL.versionName(context)?.trim()?.takeIf { it.isNotEmpty() }
        } catch (_: Exception) {
            null
        }
    }

    companion object {
        private const val PREF_NAME = "yt_dlp_runtime"
        private const val KEY_LAST_UPDATE_CHECK_MS = "last_update_check_ms"
        private const val AUTO_UPDATE_INTERVAL_MS = 24L * 60L * 60L * 1000L
    }
}

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

        var outputDir = File(request.outputDir)
        
        // Write permission self-healing pre-flight check (fixes Scoped Storage Errno 1 Operation not permitted)
        var isWritable = false
        try {
            if (!outputDir.exists()) {
                outputDir.mkdirs()
            }
            if (outputDir.exists() && outputDir.isDirectory) {
                // Perform physical write test
                val testFile = File(outputDir, ".write_test_${UUID.randomUUID()}")
                if (testFile.createNewFile()) {
                    testFile.delete()
                    isWritable = true
                }
            }
        } catch (e: Exception) {
            isWritable = false
        }

        if (!isWritable) {
            // Self-healing fallback to safe private external files directory where raw POSIX open() is ALWAYS permitted
            val safeDir = appContext.getExternalFilesDir(android.os.Environment.DIRECTORY_DOWNLOADS)
                ?.resolve("yt-downloads")
                ?: appContext.filesDir.resolve("yt-downloads")
            
            safeDir.mkdirs()
            onEvent(DownloadEvent.LogLine("[uyari] '${outputDir.absolutePath}' klasorune yazma izni yok (Scoped Storage engeli). Guvenli klasore yonlendiriliyor: '${safeDir.absolutePath}'\n"))
            outputDir = safeDir
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
            result.lastDownloadedFilePath?.let { tempFile = File(it) }
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
                result.lastDownloadedFilePath?.let { tempFile = File(it) }
            }

            if (result.sawOutdatedWarning) {
                onEvent(DownloadEvent.LogLine("[bilgi] yt-dlp runtime guncellenebilir.\n"))
            }

            if (cancelRequested || result.canceled) {
                tempFile?.let { cleanEmptyDirectories(it, outputDir) }
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
            var finalPath = ""

            // Stage 3: FFmpeg Slicing & Profiling (LeetCode 56 Consolidated Clips)
            if (isClipsOperation) {
                onEvent(DownloadEvent.Status("Videolar kesiliyor..."))
                
                // Check storage capacity for slicing (Estimated requirement: 2 * size of downloaded file)
                val expectedSizeMb = (downloadedFile.length() / (1024 * 1024)) * 2
                checkStorageCapacity(normalizedRequest.outputDir, minMbRequired = maxOf(50, expectedSizeMb))

                val microFiles = runFFmpegSlicing(downloadedFile, macroClips, normalizedRequest, onEvent)
                
                // Lossless Merge of Sliced Clips
                val mergedFile = runFFmpegConcat(microFiles, outputDir, onEvent)
                finalSize = mergedFile.length()
                finalPath = mergedFile.absolutePath
                
                // Cleanup sliced parts if merge was successful
                microFiles.forEach { f -> if (f.exists()) f.delete() }
                
                // Notify scan for the final merged file
                scanToMediaStore(mergedFile, onEvent)
            } else {
                finalSize = downloadedFile.length()
                finalPath = downloadedFile.absolutePath
                // Single standard file download completion
                scanToMediaStore(downloadedFile, onEvent)
            }

            onEvent(DownloadEvent.Progress(1f))
            onEvent(DownloadEvent.Status("Indirme tamamlandi"))
            onEvent(DownloadEvent.Finished(success = true, exitCode = 0, sizeBytes = finalSize, filePath = finalPath))
            logRunnerEvent("download_pipeline_success")

        } catch (e: PipelineException.InsufficientStorageException) {
            tempFile?.let { cleanEmptyDirectories(it, outputDir) }
            onEvent(DownloadEvent.LogLine("[hata] Disk doldu! ${e.message}\n"))
            onEvent(DownloadEvent.Status("Depolama Hatasi"))
            onEvent(DownloadEvent.Finished(success = false, exitCode = -2))
            logRunnerEvent("pipeline_storage_error", level = Log.ERROR)
        } catch (e: PipelineException.FFmpegSlicingException) {
            tempFile?.let { cleanEmptyDirectories(it, outputDir) }
            onEvent(DownloadEvent.LogLine("[hata] Video kesme hatasi: ${e.message}\n"))
            onEvent(DownloadEvent.Status("FFmpeg Hatasi"))
            onEvent(DownloadEvent.Finished(success = false, exitCode = -3))
            logRunnerEvent("pipeline_ffmpeg_error", level = Log.ERROR)
        } catch (e: PipelineException.YtDlpExecutionException) {
            tempFile?.let { cleanEmptyDirectories(it, outputDir) }
            onEvent(DownloadEvent.LogLine("[hata] Basarisiz: ${e.message}\n"))
            onEvent(DownloadEvent.Status("Indirme Hatasi"))
            onEvent(DownloadEvent.Finished(success = false, exitCode = -4))
            logRunnerEvent("pipeline_ytdlp_error", level = Log.ERROR)
        } catch (e: Exception) {
            tempFile?.let { cleanEmptyDirectories(it, outputDir) }
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

    fun getFFmpegFile(): File {
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
        request: DownloadRequest,
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
                
                val preciseCut = request.clipPrecise
                val isAudio = request.mode == DownloadMode.AUDIO

                val cmd = if (preciseCut) {
                    if (isAudio) {
                        val audFmt = request.audioFormat.lowercase()
                        if (audFmt == "mp3") {
                            listOf(
                                ffmpegBin.absolutePath, "-y",
                                "-i", downloadedFile.absolutePath,
                                "-ss", micro.start.toString(),
                                "-t", duration.toString(),
                                "-c:a", "libmp3lame", "-b:a", "192k",
                                slicedFile.absolutePath
                            )
                        } else if (audFmt == "m4a" || audFmt == "aac") {
                            listOf(
                                ffmpegBin.absolutePath, "-y",
                                "-i", downloadedFile.absolutePath,
                                "-ss", micro.start.toString(),
                                "-t", duration.toString(),
                                "-c:a", "aac", "-b:a", "192k",
                                slicedFile.absolutePath
                            )
                        } else {
                            listOf(
                                ffmpegBin.absolutePath, "-y",
                                "-ss", micro.start.toString(),
                                "-i", downloadedFile.absolutePath,
                                "-t", duration.toString(),
                                "-c", "copy",
                                "-avoid_negative_ts", "make_zero",
                                slicedFile.absolutePath
                            )
                        }
                    } else {
                        listOf(
                            ffmpegBin.absolutePath, "-y",
                            "-i", downloadedFile.absolutePath,
                            "-ss", micro.start.toString(),
                            "-t", duration.toString(),
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                            "-c:a", "aac", "-b:a", "192k",
                            slicedFile.absolutePath
                        )
                    }
                } else {
                    listOf(
                        ffmpegBin.absolutePath,
                        "-y",
                        "-ss", micro.start.toString(),
                        "-i", downloadedFile.absolutePath,
                        "-t", duration.toString(),
                        "-c", "copy",
                        "-avoid_negative_ts", "make_zero",
                        slicedFile.absolutePath
                    )
                }
                
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

    private fun cleanEmptyDirectories(path: File, baseDir: File) {
        try {
            val resolvedPath = path.canonicalFile
            val resolvedBase = baseDir.canonicalFile
            
            var folder = if (resolvedPath.isFile) resolvedPath.parentFile else resolvedPath
            
            while (folder != null && folder != resolvedBase && folder.absolutePath.startsWith(resolvedBase.absolutePath)) {
                if (folder.exists() && folder.isDirectory) {
                    val children = folder.listFiles()
                    if (children.isNullOrEmpty()) {
                        try {
                            folder.delete()
                        } catch (e: Exception) {
                            Log.e(RUNNER_TAG, "Failed to remove folder ${folder.absolutePath}: ${e.message}")
                            break
                        }
                    } else {
                        break // not empty, stop traversal
                    }
                } else {
                    break
                }
                folder = folder.parentFile
            }
        } catch (e: Exception) {
            Log.e(RUNNER_TAG, "Error in cleanEmptyDirectories: ${e.message}", e)
        }
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
                    if (safeLine.contains("HTTP Error 403: Forbidden") || safeLine.contains("HTTP Error 429") || safeLine.contains("429")) {
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
                if (line.contains("HTTP Error 403: Forbidden") || line.contains("HTTP Error 429") || line.contains("429")) {
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
            if (text.contains("HTTP Error 403: Forbidden") || text.contains("HTTP Error 429") || text.contains("429")) {
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
        super.onCreate()
        createNotificationChannel()
    }

    private var networkCallback: android.net.ConnectivityManager.NetworkCallback? = null

    override fun onDestroy() {
        unregisterWifiOnlyKillSwitch()
        serviceScope.cancel()
        super.onDestroy()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent == null) {
            stopForegroundService()
            return START_NOT_STICKY
        }

        val action = intent.action ?: ACTION_STOP
        when (action) {
            ACTION_START -> {
                val requestJson = intent.getStringExtra(EXTRA_REQUEST_JSON)
                if (requestJson != null) {
                    val title = intent.getStringExtra(EXTRA_TITLE) ?: "Downloading..."
                    val notification = buildProgressNotification(title, 0, "--", "--")
                    startForeground(NOTIFICATION_ID, notification)

                    try {
                        val request = DownloadRequest.fromJsonString(requestJson)
                        startDownloadJob(request, title)
                    } catch (e: Exception) {
                        Log.e("DownloadService", "Failed to parse request JSON", e)
                        serviceScope.launch {
                            downloadEvents.emit(DownloadEvent.Finished(success = false, exitCode = -1))
                        }
                        stopForegroundService()
                    }
                } else {
                    stopForegroundService()
                }
            }
            ACTION_UPDATE -> {
                val title = intent.getStringExtra(EXTRA_TITLE) ?: "Downloading..."
                val progress = intent.getIntExtra(EXTRA_PROGRESS, 0)
                val speed = intent.getStringExtra(EXTRA_SPEED) ?: "--"
                val eta = intent.getStringExtra(EXTRA_ETA) ?: "--"
                updateNotification(title, progress, speed, eta)
            }
            ACTION_STOP -> {
                cancelActiveDownload()
                stopForegroundService()
            }
        }

        return START_NOT_STICKY
    }

    private fun registerWifiOnlyKillSwitch() {
        unregisterWifiOnlyKillSwitch() // Clean up any active callback first to prevent leak!
        val cm = getSystemService(Context.CONNECTIVITY_SERVICE) as android.net.ConnectivityManager
        val request = android.net.NetworkRequest.Builder()
            .addCapability(android.net.NetworkCapabilities.NET_CAPABILITY_INTERNET)
            .build()
        
        val callback = object : android.net.ConnectivityManager.NetworkCallback() {
            override fun onCapabilitiesChanged(
                network: android.net.Network,
                networkCapabilities: android.net.NetworkCapabilities
            ) {
                super.onCapabilitiesChanged(network, networkCapabilities)
                val isMetered = !networkCapabilities.hasCapability(android.net.NetworkCapabilities.NET_CAPABILITY_NOT_METERED)
                val isCellular = networkCapabilities.hasTransport(android.net.NetworkCapabilities.TRANSPORT_CELLULAR)
                if (isMetered || isCellular) {
                    Log.w("DownloadService", "Wifi-Only: Switched to cellular network. Aborting download to prevent network bleeding.")
                    serviceScope.launch {
                        downloadEvents.emit(DownloadEvent.LogLine("[hata] WiFi bağlantısı kesildi! Hücresel veri kullanımını önlemek için indirme iptal edildi.\n"))
                    }
                    cancelActiveDownload()
                    stopForegroundService()
                }
            }

            override fun onLost(network: android.net.Network) {
                super.onLost(network)
                Log.w("DownloadService", "Wifi-Only: Network connection lost completely.")
                serviceScope.launch {
                    downloadEvents.emit(DownloadEvent.LogLine("[hata] Ağ bağlantısı tamamen kesildi! İndirme durduruldu.\n"))
                }
                cancelActiveDownload()
                stopForegroundService()
            }
        }
        
        try {
            cm.registerNetworkCallback(request, callback)
            networkCallback = callback
            Log.d("DownloadService", "Registered Wifi-Only Connectivity NetworkCallback Kill-Switch")
        } catch (e: Exception) {
            Log.e("DownloadService", "Failed to register network callback", e)
        }
    }

    private fun unregisterWifiOnlyKillSwitch() {
        networkCallback?.let { callback ->
            try {
                val cm = getSystemService(Context.CONNECTIVITY_SERVICE) as android.net.ConnectivityManager
                cm.unregisterNetworkCallback(callback)
                Log.d("DownloadService", "Unregistered Wifi-Only Connectivity NetworkCallback")
            } catch (e: Exception) {
                Log.e("DownloadService", "Failed to unregister network callback", e)
            }
            networkCallback = null
        }
    }

    private fun startDownloadJob(request: DownloadRequest, title: String) {
        isRunning.value = true
        activeRequest = request
        
        if (request.wifiOnly) {
            registerWifiOnlyKillSwitch()
        }

        serviceScope.launch {
            try {
                val runner = YtDlpRunner(applicationContext)
                activeRunner = runner
                
                // Speed & ETA regex for parsing inside the service to update notification
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

                runner.run(request) { event ->
                    // Emit event to shared flow
                    serviceScope.launch {
                        downloadEvents.emit(event)
                    }

                    // Update local service notification
                    when (event) {
                        is DownloadEvent.Progress -> {
                            val percent = (event.value * 100).toInt().coerceIn(0, 100)
                            currentProgressPercent = percent
                            updateNotification(
                                title = title,
                                progress = currentProgressPercent,
                                speed = currentSpeed,
                                eta = currentEta,
                                force = false,
                                batchCurrentIndex = batchCurrentIndex,
                                batchTotalCount = batchTotalCount,
                                batchCompletedCount = batchCompletedCount,
                                batchActiveTitle = batchActiveTitle
                            )
                        }
                        is DownloadEvent.LogLine -> {
                            val line = event.text
                            
                            batchProgressRegex.find(line)?.let { match ->
                                val curr = match.groupValues[1].toIntOrNull()
                                val total = match.groupValues[2].toIntOrNull()
                                if (curr != null && total != null) {
                                    batchCurrentIndex = curr - 1
                                    batchTotalCount = total
                                    batchCompletedCount = batchCurrentIndex
                                }
                            }

                            val destMatch = destRegex.find(line)?.groupValues?.getOrNull(1)
                                ?: alreadyRegex.find(line)?.groupValues?.getOrNull(1)
                                ?: mergerRegex.find(line)?.groupValues?.getOrNull(1)
                            if (destMatch != null) {
                                val file = java.io.File(destMatch)
                                batchActiveTitle = file.name
                            }

                            val speedMatch = speedRegex.find(line)?.groupValues?.getOrNull(1)
                            val etaMatch = etaRegex.find(line)?.groupValues?.getOrNull(1)
                            if (speedMatch != null || etaMatch != null || line.contains("Destination:") || line.contains("has already been downloaded")) {
                                currentSpeed = speedMatch ?: currentSpeed
                                currentEta = etaMatch ?: currentEta
                                updateNotification(
                                    title = title,
                                    progress = currentProgressPercent,
                                    speed = currentSpeed,
                                    eta = currentEta,
                                    force = false,
                                    batchCurrentIndex = batchCurrentIndex,
                                    batchTotalCount = batchTotalCount,
                                    batchCompletedCount = batchCompletedCount,
                                    batchActiveTitle = batchActiveTitle
                                )
                            }
                        }
                        is DownloadEvent.Status -> {
                            // Update status if needed
                        }
                        is DownloadEvent.Finished -> {
                            if (event.success && request.mode == com.baynuman.ytdownloader.data.DownloadMode.AUDIO && event.filePath.isNotBlank()) {
                                enqueueWaveformGeneration(request, event.filePath)
                            }
                            stopForegroundService()
                        }
                    }
                }
            } catch (e: Exception) {
                serviceScope.launch {
                    downloadEvents.emit(DownloadEvent.Finished(success = false, exitCode = -1))
                }
                stopForegroundService()
            } finally {
                activeRunner = null
                activeRequest = null
                isRunning.value = false
                if (request.wifiOnly) {
                    unregisterWifiOnlyKillSwitch()
                }
            }
        }
    }

    private fun cancelActiveDownload() {
        activeRunner?.cancel()
        activeRunner = null
        activeRequest = null
        isRunning.value = false
    }

    private fun stopForegroundService() {
        ServiceCompat.stopForeground(this, ServiceCompat.STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    private var lastNotificationTime = 0L

    private fun updateNotification(
        title: String,
        progress: Int,
        speed: String,
        eta: String,
        force: Boolean = false,
        batchCurrentIndex: Int = 0,
        batchTotalCount: Int = 1,
        batchCompletedCount: Int = 0,
        batchActiveTitle: String = ""
    ) {
        val now = System.currentTimeMillis()
        if (!force && now - lastNotificationTime < 1000L) {
            return
        }
        lastNotificationTime = now
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val notification = buildProgressNotification(
            title = title,
            progress = progress,
            speed = speed,
            valEta = eta,
            batchCurrentIndex = batchCurrentIndex,
            batchTotalCount = batchTotalCount,
            batchCompletedCount = batchCompletedCount,
            batchActiveTitle = batchActiveTitle
        )
        manager.notify(NOTIFICATION_ID, notification)
    }

    private fun buildProgressNotification(
        title: String,
        progress: Int,
        speed: String,
        valEta: String,
        batchCurrentIndex: Int = 0,
        batchTotalCount: Int = 1,
        batchCompletedCount: Int = 0,
        batchActiveTitle: String = ""
    ): Notification {
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val builder = NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.stat_sys_download)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setSilent(true)
            .setOnlyAlertOnce(true)

        if (batchTotalCount > 1) {
            val currentIdxHuman = (batchCurrentIndex + 1).coerceAtMost(batchTotalCount)
            val headline = "İndiriliyor ($currentIdxHuman/$batchTotalCount)"
            val activeText = "▶ $batchActiveTitle: $progress% ($speed)"
            val remaining = batchTotalCount - currentIdxHuman
            val summaryText = "✓ $batchCompletedCount tamamlandı, $remaining bekliyor"

            builder.setContentTitle(headline)
            builder.setContentText(activeText)
            builder.setProgress(100, progress, false)

            val inboxStyle = NotificationCompat.InboxStyle()
                .setBigContentTitle(headline)
                .addLine(activeText)
                .addLine(summaryText)
            if (valEta != "--" && valEta.isNotBlank()) {
                inboxStyle.setSummaryText("Kalan süre: $valEta")
            }
            builder.setStyle(inboxStyle)
        } else {
            val speedEta = if (speed != "--" || valEta != "--") {
                "Speed: $speed  •  ETA: $valEta"
            } else {
                "Downloading..."
            }
            builder.setContentTitle(title)
            builder.setContentText(speedEta)
            builder.setProgress(100, progress, false)
        }

        return builder.build()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Download Progress",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Shows progress of active media downloads"
                setShowBadge(false)
            }
            val manager = getSystemService(NotificationManager::class.java)
            manager?.createNotificationChannel(channel)
        }
    }

    private fun enqueueWaveformGeneration(request: DownloadRequest, filePath: String) {
        val context = applicationContext
        serviceScope.launch(Dispatchers.Default) {
            try {
                val audioFile = java.io.File(filePath)
                if (!audioFile.exists() || !audioFile.isFile) return@launch

                val waveformsDir = java.io.File(context.filesDir, "waveforms")
                if (!waveformsDir.exists()) {
                    waveformsDir.mkdirs()
                }
                val uuid = java.util.UUID.randomUUID().toString()
                val outputPng = java.io.File(waveformsDir, "waveform_$uuid.png")

                // Resolve FFmpeg path
                val runner = YtDlpRunner(context)
                val ffmpegBin = runner.getFFmpegFile()
                if (!ffmpegBin.exists()) {
                    Log.w("DownloadService", "FFmpeg binary not found for waveform generation.")
                    return@launch
                }

                // Command: ffmpeg -i input.mp3 -filter_complex "aresample=1000,showwavespic=s=320x60:colors=#6366f1" -frames:v 1 output.png
                val cmd = listOf(
                    ffmpegBin.absolutePath,
                    "-y",
                    "-i", audioFile.absolutePath,
                    "-filter_complex", "aresample=1000,showwavespic=s=320x60:colors=#6366f1",
                    "-frames:v", "1",
                    outputPng.absolutePath
                )

                Log.d("DownloadService", "Enqueuing waveform: $cmd")
                val process = ProcessBuilder(cmd)
                    .redirectErrorStream(true)
                    .start()

                // Read output to avoid process block (running on Dispatchers.IO for blocking I/O)
                withContext(Dispatchers.IO) {
                    process.inputStream.bufferedReader().use { reader ->
                        while (reader.readLine() != null) { /* no-op */ }
                    }
                }

                val exitCode = withContext(Dispatchers.IO) {
                    process.waitFor()
                }

                if (exitCode == 0 && outputPng.exists()) {
                    Log.i("DownloadService", "Waveform successfully generated at: ${outputPng.absolutePath}")
                    // Update SQLite database record using taskId directly with a non-blocking delay block (suspend)
                    val db = com.baynuman.ytdownloader.data.db.DownloadDatabase.getDatabase(context)
                    val dao = db.downloadRecordDao()
                    
                    var rowsUpdated = 0
                    withContext(Dispatchers.IO) {
                        for (i in 1..20) {
                            rowsUpdated = dao.updateThumbnailPath(request.taskId, outputPng.absolutePath)
                            if (rowsUpdated > 0) {
                                Log.i("DownloadService", "Waveform path updated in DB for taskId: ${request.taskId}")
                                break
                            }
                            delay(500) // Suspend instead of Thread.sleep! Non-blocking.
                        }
                    }
                    if (rowsUpdated == 0) {
                        Log.w("DownloadService", "Failed to update waveform path in DB: record not found for taskId: ${request.taskId}")
                    }
                } else {
                    Log.w("DownloadService", "FFmpeg waveform process failed (exit code: $exitCode)")
                }
            } catch (e: Exception) {
                Log.e("DownloadService", "Error during sequential waveform generation", e)
            }
        }
    }

    companion object {
        private const val NOTIFICATION_ID = 4040
        private const val CHANNEL_ID = "download_progress_channel"

        const val ACTION_START = "com.baynuman.ytdownloader.action.START"
        const val ACTION_UPDATE = "com.baynuman.ytdownloader.action.UPDATE"
        const val ACTION_STOP = "com.baynuman.ytdownloader.action.STOP"

        const val EXTRA_TITLE = "extra_title"
        const val EXTRA_PROGRESS = "extra_progress"
        const val EXTRA_SPEED = "extra_speed"
        const val EXTRA_ETA = "extra_eta"
        const val EXTRA_REQUEST_JSON = "extra_request_json"

        // Delegate to thread-safe Application-scoped Repository Singleton (A1)
        val downloadEvents get() = com.baynuman.ytdownloader.data.DownloadRepository.downloadEvents
        val isRunning get() = com.baynuman.ytdownloader.data.DownloadRepository.isRunning
        
        var activeRunner: YtDlpRunner?
            get() = com.baynuman.ytdownloader.data.DownloadRepository.activeRunner
            set(value) { com.baynuman.ytdownloader.data.DownloadRepository.activeRunner = value }
            
        var activeRequest: DownloadRequest?
            get() = com.baynuman.ytdownloader.data.DownloadRepository.activeRequest
            set(value) { com.baynuman.ytdownloader.data.DownloadRepository.activeRequest = value }
    }
}

```

---

## <a name="file-uithemecolorkt"></a> 📄 File: `ui/theme/Color.kt`
**Responsibility**: Custom palette definitions representing HSL dark and light tokens.

```kotlin
package com.baynuman.ytdownloader.ui.theme

import androidx.compose.ui.graphics.Color

// Obsidian Deep Space Dark Theme Colors
val ObsidianBg = Color(0xFF090D16)
val ObsidianCard = Color(0xCD121B2D)     // Translucent dark glass
val ObsidianBorder = Color(0xFF22334F)   // Dark border glow
val SoftTextDark = Color(0xFFF8FAFC)
val MutedTextDark = Color(0xFF94A3B8)

// Soft Pastel / Ice-Blue Light Theme Colors
val PastelBg = Color(0xFFF1F5F9)
val PastelCard = Color(0xCDEFEFFF)       // Translucent light glass
val PastelBorder = Color(0xFFCBD5E1)     // Light border glow
val SoftTextLight = Color(0xFF0F172A)
val MutedTextLight = Color(0xFF475569)

// Shared Vibrant Accents
val AccentCyan = Color(0xFF00D2FF)
val AccentIndigo = Color(0xFF6366F1)
val AccentBlue = Color(0xFF2563EB)
val AccentGreen = Color(0xFF10B981)
val AccentRed = Color(0xFFF43F5E)

// Legacy Mappings for compatibility during incremental compilation
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
    primary = AccentCyan,
    secondary = AccentGreen,
    tertiary = AccentIndigo,
    background = ObsidianBg,
    surface = ObsidianCard,
    surfaceVariant = ObsidianBorder,
    onPrimary = ObsidianBg,
    onSecondary = ObsidianBg,
    onTertiary = ObsidianBg,
    onBackground = SoftTextDark,
    onSurface = SoftTextDark,
    onSurfaceVariant = MutedTextDark,
    error = AccentRed,
)

private val AmoledColors = darkColorScheme(
    primary = AccentCyan,
    secondary = AccentGreen,
    tertiary = AccentIndigo,
    background = Color(0xFF000000),      // Pure AMOLED Black
    surface = Color(0xFF0D0D0D),         // Slightly elevated card for depth
    surfaceVariant = Color(0xFF1F1F1F),  // Elevated dark border
    onPrimary = Color.Black,
    onSecondary = Color.Black,
    onTertiary = Color.Black,
    onBackground = SoftTextDark,
    onSurface = SoftTextDark,
    onSurfaceVariant = MutedTextDark,
    error = AccentRed,
)

private val LightColors = lightColorScheme(
    primary = AccentIndigo,
    secondary = AccentBlue,
    tertiary = AccentCyan,
    background = PastelBg,
    surface = PastelCard,
    surfaceVariant = PastelBorder,
    onPrimary = Color.White,
    onSecondary = Color.White,
    onTertiary = Color.White,
    onBackground = SoftTextLight,
    onSurface = SoftTextLight,
    onSurfaceVariant = MutedTextLight,
    error = AccentRed,
)

@Composable
fun YtDownloaderTheme(
    themeMode: String = "DARK",
    content: @Composable () -> Unit,
) {
    val colors = when (themeMode) {
        "LIGHT" -> LightColors
        "AMOLED" -> AmoledColors
        else -> DarkColors
    }

    MaterialTheme(
        colorScheme = colors,
        typography = AppTypography,
        content = content,
    )
}


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
}

object AppRadius {
    val md = 12.dp
    val lg = 16.dp
}

```

---

## <a name="file-uithemetranslationskt"></a> 📄 File: `ui/theme/Translations.kt`
**Responsibility**: Comprehensive three-tiered localization translations (EN, TR, ES).

```kotlin
package com.baynuman.ytdownloader.ui.theme

object Translations { /* Android Translation tokens stripped for token optimization */ }
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
)

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
)

class DownloaderViewModel(application: Application) : AndroidViewModel(application) {
    private val appContext = application.applicationContext
    private val prefs = appContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    private var lastStartedUrl: String = ""
    private val binaryInstaller = BinaryInstaller(appContext)
    private val previewResolver = UrlPreviewResolver(appContext)
    private var previewJob: Job? = null
    private var latestThumbnailPath: String? = null

    // Room database Single Source of Truth for History
    private val database = DownloadDatabase.getDatabase(appContext)
    private val recordDao = database.downloadRecordDao()
    private val channelRuleDao = database.channelRuleDao()
    private var previewChannelId: String? = null
    private val queueMutex = Mutex()
    private val logBuffer = java.util.ArrayDeque<String>(300)
    private val logMutex = Mutex()

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
            themeMode = prefs.getString("theme_mode", null) ?: if (prefs.getBoolean("is_dark_theme", true)) "DARK" else "LIGHT",
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
            themeMode = runtime.themeMode,
            isBatchMode = prefs.isBatchMode,
            clipTextDetected = validation.clipTextDetected,
            activeTab = runtime.activeTab,
            historyRecords = runtime.historyRecords,
            clipEnabled = prefs.clipEnabled,
            clipStart = prefs.clipStart,
            clipEnd = prefs.clipEnd,
            wifiOnly = prefs.wifiOnly,
            schedulerEnabled = prefs.schedulerEnabled,
            schedulerTime = prefs.schedulerTime,
            showDuplicateDialog = runtime.showDuplicateDialog,
            duplicateTaskRequest = runtime.duplicateTaskRequest,
            folderOrg = prefs.folderOrg,
            clipPrecise = prefs.clipPrecise,
            compactMode = prefs.compactMode
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
            com.baynuman.ytdownloader.data.DownloadRepository.isRunning.collect { isServiceRunning ->
                _activeTaskState.update { it.copy(isRunning = isServiceRunning) }
            }
        }

        // Listen to DownloadService's events
        viewModelScope.launch {
            com.baynuman.ytdownloader.data.DownloadRepository.downloadEvents.collect { event ->
                when (event) {
                    is DownloadEvent.LogLine -> handleLogLine(event.text)
                    is DownloadEvent.Progress -> {
                        val progressVal = event.value.coerceIn(0f, 1f)
                        _activeTaskState.update { it.copy(progress = progressVal) }
                    }
                    is DownloadEvent.Status -> _activeTaskState.update { it.copy(status = event.text) }
                    is DownloadEvent.Finished -> {
                        resetSpeedHistory()
                        _activeTaskState.update {
                            it.copy(
                                isRunning = false,
                                status = if (event.success) "Tamamlandi" else it.status,
                                speedText = if (event.success) "Tamamlandi" else "--",
                                etaText = if (event.success) "00:00" else "--",
                            )
                        }
                        if (event.success) {
                            val activeRequest = com.baynuman.ytdownloader.data.DownloadRepository.activeRequest
                            val currentUrl = lastStartedUrl.ifBlank { activeRequest?.urls?.firstOrNull() ?: "" }
                            val finalTitle = if (_formValidationState.value.previewTitle.isNotBlank()) {
                                _formValidationState.value.previewTitle
                            } else {
                                currentUrl
                            }
                            val taskId = activeRequest?.taskId ?: java.util.UUID.randomUUID().toString()
                            addToHistory(
                                title = finalTitle,
                                url = currentUrl,
                                format = if (_preferencesState.value.mode == DownloadMode.VIDEO) _preferencesState.value.videoContainer else _preferencesState.value.audioFormat,
                                sizeBytes = event.sizeBytes,
                                thumbnailPath = activeRequest?.thumbnailPath ?: latestThumbnailPath,
                                id = taskId
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
            outputDir = defaultOutputDir(application),
            clipPrecise = prefs.getBoolean("clip_precise", false),
            compactMode = prefs.getBoolean("compact_mode", false)
        )
    }

    private fun buildInitialState(application: Application): DownloaderUiState {
        val savedLang = prefs.getString("current_language", null)
            ?: java.util.Locale.getDefault().language.takeIf { it in listOf("tr", "es") }
            ?: "en"
        val savedTheme = prefs.getBoolean("is_dark_theme", true)
        val savedThemeMode = prefs.getString("theme_mode", null) ?: if (savedTheme) "DARK" else "LIGHT"
        return DownloaderUiState(
            outputDir = defaultOutputDir(application),
            currentLanguage = savedLang,
            isDarkTheme = savedTheme,
            themeMode = savedThemeMode
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
        val current = _runtimeState.value.themeMode
        val next = when (current) {
            "LIGHT" -> "DARK"
            "DARK" -> "AMOLED"
            else -> "LIGHT"
        }
        _runtimeState.update { it.copy(
            themeMode = next,
            isDarkTheme = (next == "DARK" || next == "AMOLED")
        ) }
        prefs.edit().putString("theme_mode", next).apply()
        telemetry("theme_changed_$next")
    }

    fun toggleBatchMode() {
        _preferencesState.update { it.copy(isBatchMode = !it.isBatchMode) }
        telemetry("batch_mode_changed_${_preferencesState.value.isBatchMode}")
    }

    fun toggleCompactMode() {
        val next = !_preferencesState.value.compactMode
        _preferencesState.update { it.copy(compactMode = next) }
        prefs.edit().putBoolean("compact_mode", next).apply()
        telemetry("toggle_compact_mode_$next")
    }

    fun toggleClipPrecise() {
        val next = !_preferencesState.value.clipPrecise
        _preferencesState.update { it.copy(clipPrecise = next) }
        prefs.edit().putBoolean("clip_precise", next).apply()
        telemetry("toggle_clip_precise_$next")
    }

    fun addToQueueWithoutStarting() {
        val currentInput = _formValidationState.value.urlsText.trim()
        if (currentInput.isBlank()) return
        
        if (!_preferencesState.value.isBatchMode) {
            _preferencesState.update { it.copy(isBatchMode = true) }
        }
        
        val nextText = if (currentInput.endsWith("\n")) {
            currentInput
        } else {
            currentInput + "\n"
        }
        updateUrlsText(nextText)
        telemetry("add_to_queue_without_starting")
    }

    fun removeUrlFromBatch(index: Int) {
        val urls = parseUrls(_formValidationState.value.urlsText)
        if (index in urls.indices) {
            val updatedUrls = urls.toMutableList().apply { removeAt(index) }
            val nextText = updatedUrls.joinToString("\n")
            updateUrlsText(nextText)
        }
    }

    fun reorderBatchUrls(fromIndex: Int, toIndex: Int) {
        val urls = parseUrls(_formValidationState.value.urlsText).toMutableList()
        val activeIndex = _activeTaskState.value.playlistProgressText.substringBefore("/").toIntOrNull()?.let { it - 1 } ?: 0
        val isDownloading = _activeTaskState.value.isRunning
        
        // Pinned Active Item: Lock currently active or completed tasks
        if (isDownloading) {
            if (fromIndex <= activeIndex || toIndex <= activeIndex) {
                return
            }
        }
        
        if (fromIndex in urls.indices && toIndex in urls.indices) {
            val item = urls.removeAt(fromIndex)
            urls.add(toIndex, item)
            val nextText = urls.joinToString("\n")
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
        _preferencesState.update { it.copy(userExplicit = false) }
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

    private fun extractVideoId(url: String): String? {
        val regexes = listOf(
            Regex("""(?:v=|\/v\/|embed\/|shorts\/|youtu\.be\/|\/embed\/|\/shorts\/)([a-zA-Z0-9_-]{11})"""),
            Regex("""(?:\/shorts\/|youtu\.be\/|v\/|embed\/)([a-zA-Z0-9_-]{11})""")
        )
        for (regex in regexes) {
            val match = regex.find(url)
            if (match != null && match.groupValues.size > 1) {
                return match.groupValues[1]
            }
        }
        return null
    }

    fun startDownload() {
        if (_activeTaskState.value.isRunning) return
        val prefs = _preferencesState.value
        val validation = _formValidationState.value

        val validationError = validate(prefs, validation)
        if (validationError != null) {
            _formValidationState.update { it.copy(errorText = validationError) }
            _activeTaskState.update { it.copy(status = "Hazir") }
            telemetry("start_download_blocked")
            return
        }

        val urls = parseUrls(validation.urlsText)
        val runtime = _runtimeState.value

        // Parse micro clips if enabled
        val clipsList = if (prefs.clipEnabled) {
            val startSec = com.baynuman.ytdownloader.data.algorithms.ClipOptimizer.parseTimeToSeconds(prefs.clipStart)
            val endSec = com.baynuman.ytdownloader.data.algorithms.ClipOptimizer.parseTimeToSeconds(prefs.clipEnd)
            if (startSec == null || endSec == null || startSec >= endSec) {
                val errorMsg = com.baynuman.ytdownloader.ui.theme.Translations.get("err_trim_invalid", runtime.currentLanguage)
                _formValidationState.update { it.copy(errorText = errorMsg) }
                _activeTaskState.update { it.copy(status = "Hazir") }
                telemetry("start_download_blocked_trim")
                return
            }
            listOf(com.baynuman.ytdownloader.data.algorithms.MicroClip(start = startSec, end = endSec, title = "Clip"))
        } else {
            emptyList()
        }

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
            clips = clipsList,
            wifiOnly = prefs.wifiOnly,
            schedulerEnabled = prefs.schedulerEnabled,
            schedulerTime = prefs.schedulerTime,
            folderOrg = prefs.folderOrg,
            clipPrecise = prefs.clipPrecise
        )

        viewModelScope.launch {
            queueMutex.withLock {
                val firstUrl = urls.firstOrNull() ?: ""
                val videoId = extractVideoId(firstUrl) ?: ""
                val format = if (prefs.mode == DownloadMode.AUDIO) prefs.audioFormat else prefs.videoContainer

                // Tier A Check: RAM / Active tasks
                val isAlreadyRunning = _activeTaskState.value.isRunning && 
                    (lastStartedUrl == firstUrl || com.baynuman.ytdownloader.data.DownloadRepository.activeRequest?.urls?.contains(firstUrl) == true)

                // Tier B Check: Room DB
                val record = if (firstUrl.isNotBlank()) {
                    withContext(Dispatchers.IO) {
                        recordDao.findRecordByUrlAndFormat(
                            url = firstUrl,
                            urlLike = if (videoId.isNotBlank()) "%$videoId%" else "NOT_FOUND",
                            format = format
                        )
                    }
                } else null

                // Tier C Check: Physical presence (O(1))
                var fileExists = false
                if (record != null) {
                    val possiblePaths = listOf(
                        File(prefs.outputDir, "${record.title}.$format"),
                        File(prefs.outputDir, "${record.title} [$videoId].$format"),
                        File(prefs.outputDir, "${record.title}-$videoId.$format")
                    )
                    for (path in possiblePaths) {
                        if (path.exists()) {
                            fileExists = true
                            break
                        }
                    }
                }

                if (isAlreadyRunning || (record != null && fileExists)) {
                    // Duplicate found! Open warning popup
                    _runtimeState.update {
                        it.copy(
                            showDuplicateDialog = true,
                            duplicateTaskRequest = request
                        )
                    }
                    telemetry("duplicate_detected")
                } else {
                    // Start download
                    // Headless Channel Rule Engine
                    var finalRequest = request
                    if (!prefs.userExplicit && previewChannelId != null) {
                        val rule = withContext(Dispatchers.IO) {
                            channelRuleDao.getRuleByChannelId(previewChannelId!!)
                        }
                        if (rule != null) {
                            try {
                                val ruleJson = org.json.JSONObject(rule.settingsJson)
                                finalRequest = request.copy(
                                    mode = ruleJson.optString("mode", request.mode.name).let {
                                        try { DownloadMode.valueOf(it) } catch (_: Exception) { request.mode }
                                    },
                                    videoPreset = ruleJson.optString("videoPreset", request.videoPreset),
                                    customVideoHeight = ruleJson.optString("customVideoHeight", request.customVideoHeight),
                                    videoContainer = ruleJson.optString("videoContainer", request.videoContainer),
                                    videoAudioCodec = ruleJson.optString("videoAudioCodec", request.videoAudioCodec),
                                    audioFormat = ruleJson.optString("audioFormat", request.audioFormat),
                                    audioQualityPreset = ruleJson.optString("audioQualityPreset", request.audioQualityPreset),
                                    metadata = ruleJson.optString("metadata", request.metadata.toString()).toBoolean(),
                                    thumbnail = ruleJson.optString("thumbnail", request.thumbnail.toString()).toBoolean(),
                                    subtitles = ruleJson.optString("subtitles", request.subtitles.toString()).toBoolean(),
                                    autoSubtitles = ruleJson.optString("autoSubtitles", request.autoSubtitles.toString()).toBoolean(),
                                    restrictNames = ruleJson.optString("restrictNames", request.restrictNames.toString()).toBoolean(),
                                    playlistEnabled = ruleJson.optString("playlistEnabled", request.playlistEnabled.toString()).toBoolean()
                                )
                                appendLog("[kanal-kurali] Uygulandı: ${rule.channelName} (${rule.channelId})\n")
                            } catch (e: Exception) {
                                Log.w("ChannelRules", "Failed to apply rule", e)
                            }
                        }
                    }
                    startDownloadActual(finalRequest)
                }
            }
        }
    }

    fun startDownloadActual(request: DownloadRequest) {
        _runtimeState.update { it.copy(showDuplicateDialog = false, duplicateTaskRequest = null) }

        if (request.schedulerEnabled) {
            // Cancel previous WorkManager job with the same ID
            androidx.work.WorkManager.getInstance(appContext).cancelUniqueWork("deferred_ytdlp_download")
            
            val timeParts = request.schedulerTime.split(":")
            val hour = timeParts.getOrNull(0)?.toIntOrNull() ?: 3
            val minute = timeParts.getOrNull(1)?.toIntOrNull() ?: 0
            
            val calendar = java.util.Calendar.getInstance()
            val now = calendar.timeInMillis
            
            val target = java.util.Calendar.getInstance().apply {
                set(java.util.Calendar.HOUR_OF_DAY, hour)
                set(java.util.Calendar.MINUTE, minute)
                set(java.util.Calendar.SECOND, 0)
                set(java.util.Calendar.MILLISECOND, 0)
            }
            if (target.timeInMillis <= now) {
                target.add(java.util.Calendar.DAY_OF_YEAR, 1)
            }
            val delayMs = target.timeInMillis - now
            
            val constraints = androidx.work.Constraints.Builder().apply {
                if (request.wifiOnly) {
                    setRequiredNetworkType(androidx.work.NetworkType.UNMETERED)
                } else {
                    setRequiredNetworkType(androidx.work.NetworkType.CONNECTED)
                }
            }.build()

            val inputData = androidx.work.Data.Builder()
                .putString("request_json", request.toJsonString())
                .putString("title", if (request.urls.isNotEmpty()) request.urls.first() else "Scheduled Download")
                .build()

            val workRequest = androidx.work.OneTimeWorkRequestBuilder<com.baynuman.ytdownloader.service.DownloadWorker>()
                .setInitialDelay(delayMs, java.util.concurrent.TimeUnit.MILLISECONDS)
                .setConstraints(constraints)
                .setInputData(inputData)
                .build()

            androidx.work.WorkManager.getInstance(appContext).enqueueUniqueWork(
                "deferred_ytdlp_download",
                androidx.work.ExistingWorkPolicy.REPLACE,
                workRequest
            )

            appendLog("[bilgi] İndirme zamanlandı: ${request.schedulerTime} (Gecikme: ${delayMs / 1000 / 60} dakika)\n")
            _activeTaskState.update { it.copy(status = "Zamanlandi: ${request.schedulerTime}") }
            telemetry("download_scheduled")
            return
        }

        viewModelScope.launch(Dispatchers.Default) {
            logMutex.lock()
            try {
                logBuffer.clear()
            } finally {
                logMutex.unlock()
            }
        }

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

        val firstUrl = request.urls.firstOrNull() ?: ""
        val activeTitle = if (_formValidationState.value.previewTitle.isNotBlank()) _formValidationState.value.previewTitle else firstUrl
        
        lastStartedUrl = firstUrl

        try {
            val intent = Intent(appContext, com.baynuman.ytdownloader.service.DownloadService::class.java).apply {
                action = com.baynuman.ytdownloader.service.DownloadService.ACTION_START
                putExtra(com.baynuman.ytdownloader.service.DownloadService.EXTRA_TITLE, activeTitle)
                putExtra(com.baynuman.ytdownloader.service.DownloadService.EXTRA_REQUEST_JSON, request.toJsonString())
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                appContext.startForegroundService(intent)
            } else {
                appContext.startService(intent)
            }
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

    private fun downloadAndCompressThumbnail(urlString: String): String? {
        try {
            val secureUrlString = if (urlString.startsWith("http://", ignoreCase = true)) {
                "https://" + urlString.substring(7)
            } else {
                urlString
            }
            val url = URL(secureUrlString)
            val connection = url.openConnection() as HttpURLConnection
            connection.doInput = true
            connection.connectTimeout = 5000
            connection.readTimeout = 5000
            connection.connect()
            val input = connection.inputStream
            val bitmap = BitmapFactory.decodeStream(input) ?: return null
            
            // Resize to 320x180 px (16:9 ratio)
            val resizedBitmap = Bitmap.createScaledBitmap(bitmap, 320, 180, true)
            
            // Ensure thumbnails folder exists
            val thumbsDir = File(appContext.filesDir, "thumbnails")
            if (!thumbsDir.exists()) {
                thumbsDir.mkdirs()
            }
            
            // Create filename based on md5 of the thumbnail URL
            val hash = MessageDigest.getInstance("MD5").digest(urlString.toByteArray()).joinToString("") { "%02x".format(it) }
            val outputFile = File(thumbsDir, "thumb_$hash.webp")
            
            FileOutputStream(outputFile).use { out ->
                if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.R) {
                    resizedBitmap.compress(Bitmap.CompressFormat.WEBP_LOSSY, 75, out)
                } else {
                    @Suppress("DEPRECATION")
                    resizedBitmap.compress(Bitmap.CompressFormat.WEBP, 75, out)
                }
            }
            
            // Clean up bitmaps
            if (bitmap != resizedBitmap) {
                bitmap.recycle()
            }
            resizedBitmap.recycle()
            
            return outputFile.absolutePath
        } catch (e: Exception) {
            android.util.Log.e("DownloaderViewModel", "Thumbnail download/compress failed: ${e.message}", e)
        }
        return null
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

        // Asynchronously download and compress thumbnail in background coroutine!
        val thumbUrl = preview.thumbnailUrl
        if (!thumbUrl.isNullOrBlank()) {
            viewModelScope.launch(Dispatchers.IO) {
                latestThumbnailPath = downloadAndCompressThumbnail(thumbUrl)
            }
        } else {
            latestThumbnailPath = null
        }

        // Fetch SponsorBlock segments asynchronously (SponsorBlock)
        val firstUrl = extractFirstUrl(_formValidationState.value.urlsText)
        if (firstUrl != null && !preview.isPlaylist) {
            val videoId = extractYoutubeVideoId(firstUrl)
            if (videoId != null) {
                viewModelScope.launch(Dispatchers.IO) {
                    val segments = fetchSponsorBlockSegments(videoId)
                    _formValidationState.update { it.copy(sponsorSegments = segments) }
                    if (segments.isNotEmpty()) {
                        appendLog("[sponsorblock] ${segments.size} sponsor segmenti algilandi!\n")
                    }
                }
            } else {
                _formValidationState.update { it.copy(sponsorSegments = emptyList()) }
            }
        } else {
            _formValidationState.update { it.copy(sponsorSegments = emptyList()) }
        }

        // Cache previewChannelId for headless channel rule engine
        previewChannelId = preview.channelId

        telemetry("url_preview_resolved")
    }

    private fun extractYoutubeVideoId(url: String): String? {
        val cleanedUrl = url.trim()
        
        // 1. Standard watch URL query parameter (?v=... or &v=...)
        val queryPattern = Regex("[?&]v=([a-zA-Z0-9_-]{11})")
        queryPattern.find(cleanedUrl)?.let { return it.groupValues[1] }
        
        // 2. Short URL (youtu.be/...)
        val shortPattern = Regex("youtu\\.be/([a-zA-Z0-9_-]{11})")
        shortPattern.find(cleanedUrl)?.let { return it.groupValues[1] }
        
        // 3. Common path-based patterns (embed/..., v/..., shorts/...)
        val pathPattern = Regex("(?:embed|v|shorts)/([a-zA-Z0-9_-]{11})")
        pathPattern.find(cleanedUrl)?.let { return it.groupValues[1] }
        
        // 4. Custom lookbehind fallback without using regular expression lookbehinds
        if (cleanedUrl.contains("youtube") || cleanedUrl.contains("youtu.be")) {
            val generalPattern = Regex("(?:/|=)([a-zA-Z0-9_-]{11})(?:[?&/]|$)")
            generalPattern.findAll(cleanedUrl).forEach { match ->
                val id = match.groupValues[1]
                if (id.length == 11) {
                    return id
                }
            }
        }
        
        return null
    }

    private fun fetchSponsorBlockSegments(videoId: String): List<com.baynuman.ytdownloader.data.SponsorSegment> {
        val segments = mutableListOf<com.baynuman.ytdownloader.data.SponsorSegment>()
        try {
            val url = URL("https://sponsor.ajay.app/api/skipSegments?videoID=$videoId")
            val connection = url.openConnection() as HttpURLConnection
            connection.requestMethod = "GET"
            connection.connectTimeout = 3000
            connection.readTimeout = 3000
            
            val responseCode = connection.responseCode
            if (responseCode == HttpURLConnection.HTTP_OK) {
                val response = connection.inputStream.bufferedReader().use { it.readText() }
                val array = org.json.JSONArray(response)
                for (i in 0 until array.length()) {
                    val obj = array.getJSONObject(i)
                    val segmentArr = obj.getJSONArray("segment")
                    val start = segmentArr.getDouble(0).toFloat()
                    val end = segmentArr.getDouble(1).toFloat()
                    val category = obj.optString("category", "sponsor")
                    segments.add(com.baynuman.ytdownloader.data.SponsorSegment(start = start, end = end, category = category))
                }
            } else {
                Log.d("DownloaderViewModel", "SponsorBlock API returned response code: $responseCode")
            }
        } catch (e: Exception) {
            Log.e("DownloaderViewModel", "Failed to fetch SponsorBlock segments", e)
        }
        return segments
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

        if (speed != null) {
            pushSpeedHistory(speed)
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

    fun addToHistory(title: String, url: String, format: String, sizeBytes: Long, thumbnailPath: String? = null, id: String? = null) {
        viewModelScope.launch(Dispatchers.IO) {
            val recordId = id ?: java.util.UUID.randomUUID().toString()
            val entity = DownloadRecordEntity(
                id = recordId,
                title = title,
                url = url,
                format = format,
                downloadedAt = System.currentTimeMillis(),
                fileSizeBytes = sizeBytes,
                thumbnailPath = thumbnailPath
            )
            recordDao.insertRecord(entity)
        }
    }

    fun clearHistory() {
        viewModelScope.launch(Dispatchers.IO) {
            recordDao.clearAll()
            val thumbsDir = File(appContext.filesDir, "thumbnails")
            if (thumbsDir.exists()) {
                thumbsDir.deleteRecursively()
            }
        }
        telemetry("history_cleared")
    }

    fun saveChannelRule(channelId: String, channelName: String) {
        val prefs = _preferencesState.value
        val settingsMap = mapOf(
            "mode" to prefs.mode.name,
            "videoPreset" to prefs.videoPreset,
            "customVideoHeight" to prefs.customVideoHeight,
            "videoContainer" to prefs.videoContainer,
            "videoAudioCodec" to prefs.videoAudioCodec,
            "audioFormat" to prefs.audioFormat,
            "audioQualityPreset" to prefs.audioQualityPreset,
            "metadata" to prefs.metadata.toString(),
            "thumbnail" to prefs.thumbnail.toString(),
            "subtitles" to prefs.subtitles.toString(),
            "autoSubtitles" to prefs.autoSubtitles.toString(),
            "restrictNames" to prefs.restrictNames.toString(),
            "playlistEnabled" to prefs.playlistEnabled.toString()
        )
        val settingsJson = org.json.JSONObject(settingsMap).toString()
        viewModelScope.launch(Dispatchers.IO) {
            channelRuleDao.insertOrUpdate(
                ChannelRuleEntity(
                    channelId = channelId,
                    channelName = channelName,
                    settingsJson = settingsJson,
                    updatedAt = System.currentTimeMillis()
                )
            )
        }
        appendLog("[kanal-kurali] Kural kaydedildi: $channelName ($channelId)\n")
        telemetry("channel_rule_saved")
    }

    fun deleteChannelRule(channelId: String) {
        viewModelScope.launch(Dispatchers.IO) {
            channelRuleDao.deleteByChannelId(channelId)
        }
        telemetry("channel_rule_deleted")
    }

    fun hasChannelRule(): Boolean {
        return previewChannelId != null
    }

    fun getPreviewChannelId(): String? = previewChannelId
    fun getPreviewChannelName(): String = _formValidationState.value.previewChannel

    private fun pushSpeedHistory(rawSpeedStr: String) {
        val rawMbps = parseSpeedToMbps(rawSpeedStr)
        val currentEma = _activeTaskState.value.emaSmoothed
        val smoothed = (rawMbps * 0.2f) + (currentEma * 0.8f)
        val history = _activeTaskState.value.speedHistory.toMutableList()
        val idx = _activeTaskState.value.speedWriteIdx
        history[idx] = smoothed
        _activeTaskState.update {
            it.copy(
                speedHistory = history,
                speedWriteIdx = (idx + 1) % 60,
                emaSmoothed = smoothed
            )
        }
    }

    private fun parseSpeedToMbps(s: String): Float {
        val cleaned = s.trim().lowercase()
        val regex = Regex("""([0-9.]+)\s*(gib|mib|kib|gb|mb|kb|b)/s""")
        val match = regex.find(cleaned) ?: return 0f
        val value = match.groupValues[1].toFloatOrNull() ?: return 0f
        val unit = match.groupValues[2]
        return when (unit) {
            "gib", "gb" -> value * 1024f
            "mib", "mb" -> value
            "kib", "kb" -> value / 1024f
            "b" -> value / (1024f * 1024f)
            else -> value
        }
    }

    fun resetSpeedHistory() {
        _activeTaskState.update {
            it.copy(
                speedHistory = List(60) { 0f },
                speedWriteIdx = 0,
                emaSmoothed = 0f
            )
        }
    }

    fun deleteHistoryRecord(id: String, thumbnailPath: String?) {
        viewModelScope.launch(Dispatchers.IO) {
            recordDao.deleteRecordById(id)
            if (!thumbnailPath.isNullOrBlank()) {
                val file = File(thumbnailPath)
                if (file.exists()) {
                    file.delete()
                }
            }
        }
    }

    private fun appendLog(line: String) {
        viewModelScope.launch(Dispatchers.Default) {
            logMutex.lock()
            try {
                val lines = line.split("\n")
                for (l in lines) {
                    if (l.isNotEmpty() || lines.size == 1) {
                        logBuffer.addLast(l)
                    }
                }
                while (logBuffer.size > 300) {
                    logBuffer.removeFirst()
                }
                val newLogs = logBuffer.joinToString("\n") + if (logBuffer.isNotEmpty()) "\n" else ""
                _activeTaskState.update { current ->
                    current.copy(logs = newLogs)
                }
            } finally {
                logMutex.unlock()
            }
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
)

val LocalShowPicker = androidx.compose.runtime.staticCompositionLocalOf<(PickerData) -> Unit> { { } }

@Composable
@OptIn(ExperimentalMaterial3Api::class)
fun DownloaderScreen(
    state: DownloaderUiState,
    viewModel: DownloaderViewModel,
    onPickCookiesFile: () -> Unit,
    onPickYtDlpBinary: () -> Unit,
    onPickOutputFolder: () -> Unit,
    onRequestMediaPermissions: () -> Unit,
) {
    val animatedProgress by animateFloatAsState(
        targetValue = state.progress.coerceIn(0f, 1f),
        label = "download-progress",
    )
    var showLogSheet by remember { mutableStateOf(false) }
    var activePickerData by remember { mutableStateOf<PickerData?>(null) }
    val lang = state.currentLanguage
    val haptic = LocalHapticFeedback.current
    val context = LocalContext.current

    // Smart auto-paste and clipboard monitor on resume/focus
    val lifecycleOwner = androidx.lifecycle.compose.LocalLifecycleOwner.current
    androidx.compose.runtime.CompositionLocalProvider(LocalShowPicker provides { data -> activePickerData = data }) {
    DisposableEffect(lifecycleOwner) {
        val observer = androidx.lifecycle.LifecycleEventObserver { _, event ->
            if (event == androidx.lifecycle.Lifecycle.Event.ON_RESUME) {
                viewModel.checkClipboardForYoutubeLink()
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose {
            lifecycleOwner.lifecycle.removeObserver(observer)
        }
    }

    // Modern Soft Mesh Gradient simulated via vertical brushes
    val bgBrush = Brush.verticalGradient(
        colors = if (state.isDarkTheme) {
            listOf(MaterialTheme.colorScheme.background, ObsidianBg.copy(alpha = 0.95f))
        } else {
            listOf(MaterialTheme.colorScheme.background, PastelBg.copy(alpha = 0.95f))
        }
    )

    if (state.showDuplicateDialog && state.duplicateTaskRequest != null) {
        val req = state.duplicateTaskRequest
        val titleVal = state.previewTitle.takeIf { it.isNotBlank() } ?: req.urls.firstOrNull() ?: ""
        val formatVal = if (req.mode == DownloadMode.AUDIO) req.audioFormat else req.videoContainer
        
        AlertDialog(
            onDismissRequest = { viewModel.dismissDuplicateDialog() },
            title = {
                Text(
                    text = Translations.get("lbl_duplicate_title", lang),
                    style = MaterialTheme.typography.titleMedium
                )
            },
            text = {
                val rawBody = Translations.get("lbl_duplicate_body", lang)
                val body = rawBody
                    .replace("{title}", titleVal)
                    .replace("{format}", formatVal)
                Text(
                    text = body,
                    style = MaterialTheme.typography.bodyMedium
                )
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        viewModel.startDownloadActual(req)
                    }
                ) {
                    Text(text = if (lang == "tr") "Evet" else if (lang == "es") "Sí" else "Yes")
                }
            },
            dismissButton = {
                TextButton(
                    onClick = { viewModel.dismissDuplicateDialog() }
                ) {
                    Text(text = if (lang == "tr") "Hayır" else if (lang == "es") "No" else "No")
                }
            }
        )
    }

    Scaffold(
        modifier = Modifier.fillMaxSize(),
        containerColor = Color.Transparent,
        bottomBar = {
            Column {
                // Persistent bottom status capsule (only displayed in Download tab)
                if (state.activeTab == 0) {
                    StickyDownloadBar(
                        state = state,
                        progress = animatedProgress,
                        lang = lang,
                        viewModel = viewModel,
                        onPrimaryAction = {
                            haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                            if (state.isRunning) {
                                viewModel.cancelDownload()
                            } else {
                                viewModel.startDownload()
                            }
                        },
                        onLogClick = {
                            haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                            showLogSheet = true
                        },
                    )
                }

                // Native Mobile Bottom Navigation Bar (4 Central Tabs)
                NavigationBar(
                    containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.85f),
                    tonalElevation = 8.dp,
                    modifier = Modifier.height(72.dp)
                ) {
                    NavigationBarItem(
                        selected = state.activeTab == 0,
                        onClick = {
                            haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                            viewModel.updateActiveTab(0)
                        },
                        icon = { Text("📥", style = MaterialTheme.typography.titleLarge) },
                        label = { Text(Translations.get("tab_download", lang), style = MaterialTheme.typography.labelSmall) }
                    )
                    NavigationBarItem(
                        selected = state.activeTab == 1,
                        onClick = {
                            haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                            viewModel.updateActiveTab(1)
                        },
                        icon = { Text("📋", style = MaterialTheme.typography.titleLarge) },
                        label = { Text(Translations.get("tab_queue", lang), style = MaterialTheme.typography.labelSmall) }
                    )
                    NavigationBarItem(
                        selected = state.activeTab == 2,
                        onClick = {
                            haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                            viewModel.updateActiveTab(2)
                        },
                        icon = { Text("📜", style = MaterialTheme.typography.titleLarge) },
                        label = { Text(Translations.get("tab_history", lang), style = MaterialTheme.typography.labelSmall) }
                    )
                    NavigationBarItem(
                        selected = state.activeTab == 3,
                        onClick = {
                            haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                            viewModel.updateActiveTab(3)
                        },
                        icon = { Text("⚙️", style = MaterialTheme.typography.titleLarge) },
                        label = { Text(Translations.get("tab_settings", lang), style = MaterialTheme.typography.labelSmall) }
                    )
                }
            }
        },
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(bgBrush)
                .padding(innerPadding)
        ) {
            when (state.activeTab) {
                0 -> { // TAB 0: DOWNLOADER HOME
                    LazyColumn(
                        modifier = Modifier.fillMaxSize(),
                        contentPadding = PaddingValues(
                            start = AppSpacing.md,
                            end = AppSpacing.md,
                            top = AppSpacing.md,
                            bottom = AppSpacing.lg * 2,
                        ),
                        verticalArrangement = Arrangement.spacedBy(AppSpacing.sm),
                    ) {
                        item { HeaderCard(state = state, viewModel = viewModel, lang = lang) }
                        item { SourceSection(state = state, viewModel = viewModel, lang = lang) }
                        if (!state.compactMode) {
                            item { PresetSection(state = state, viewModel = viewModel, lang = lang) }
                            item { StorageSection(state = state, viewModel = viewModel, lang = lang, onPickOutputFolder = onPickOutputFolder, onRequestMediaPermissions = onRequestMediaPermissions) }
                        }
                    }
                }
                1 -> { // TAB 1: QUEUE MANAGER
                    val urlsList = remember(state.urlsText) {
                        state.urlsText.lineSequence()
                            .map { it.trim() }
                            .filter { it.isNotEmpty() }
                            .toList()
                    }
                    LazyColumn(
                        modifier = Modifier.fillMaxSize(),
                        contentPadding = PaddingValues(AppSpacing.md),
                        verticalArrangement = Arrangement.spacedBy(AppSpacing.sm),
                    ) {
                        item {
                            Row(
                                modifier = Modifier.fillMaxWidth().padding(bottom = AppSpacing.xs),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    text = Translations.get("queue_title", lang) + " (${urlsList.size})",
                                    style = MaterialTheme.typography.titleLarge,
                                    color = MaterialTheme.colorScheme.onSurface
                                )
                                TextButton(
                                    onClick = {
                                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                        viewModel.checkClipboardForYoutubeLink()
                                    }
                                ) {
                                    Text("🔄 " + if (lang == "tr") "Yenile" else if (lang == "es") "Actualizar" else "Refresh")
                                }
                            }
                        }

                        if (urlsList.isNotEmpty()) {
                            item {
                                Button(
                                    onClick = {
                                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                        viewModel.startDownload()
                                    },
                                    modifier = Modifier.fillMaxWidth().padding(vertical = AppSpacing.xs).heightIn(min = 48.dp),
                                    colors = ButtonDefaults.buttonColors(containerColor = AccentIndigo)
                                ) {
                                    Text(
                                        text = if (lang == "tr") "🚀 Sıradakileri İndir" else if (lang == "es") "🚀 Descargar Cola" else "🚀 Start Downloading Queue",
                                        style = MaterialTheme.typography.titleSmall
                                    )
                                }
                            }
                        }

                        if (urlsList.isEmpty()) {
                            item {
                                Card(
                                    modifier = Modifier.fillMaxWidth().padding(top = AppSpacing.lg),
                                    shape = RoundedCornerShape(AppRadius.lg),
                                    border = BorderStroke(1.dp, MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.25f)),
                                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.45f)),
                                ) {
                                    Box(
                                        modifier = Modifier.fillMaxWidth().padding(vertical = 48.dp),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        Column(
                                            horizontalAlignment = Alignment.CenterHorizontally,
                                            verticalArrangement = Arrangement.spacedBy(AppSpacing.xs)
                                        ) {
                                            Text("📋", style = MaterialTheme.typography.headlineLarge)
                                            Text(
                                                text = Translations.get("empty_queue", lang),
                                                style = MaterialTheme.typography.bodyMedium,
                                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                                textAlign = TextAlign.Center,
                                                modifier = Modifier.padding(horizontal = AppSpacing.md)
                                            )
                                        }
                                    }
                                }
                            }
                        } else {
                            items(urlsList.size, key = { index -> index }) { index ->
                                val url = urlsList[index]
                                val activeIndex = state.playlistProgressText.substringBefore("/").toIntOrNull()?.let { it - 1 } ?: 0
                                val isActive = state.isRunning && activeIndex == index
                                val isPinned = state.isRunning && index <= activeIndex
                                
                                var offsetY by remember { mutableStateOf(0f) }
                                val density = androidx.compose.ui.platform.LocalDensity.current.density
                                
                                Row(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .offset(y = offsetY.dp)
                                        .background(
                                            color = if (isActive) MaterialTheme.colorScheme.primary.copy(alpha = 0.08f)
                                            else MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.15f),
                                            shape = RoundedCornerShape(AppRadius.md)
                                        )
                                        .border(
                                            width = 1.dp,
                                            color = if (isActive) MaterialTheme.colorScheme.primary.copy(alpha = 0.3f)
                                            else Color.Transparent,
                                            shape = RoundedCornerShape(AppRadius.md)
                                        )
                                        .pointerInput(isPinned) {
                                            if (isPinned) return@pointerInput
                                            detectDragGesturesAfterLongPress(
                                                onDragStart = { /* Drag feedback */ },
                                                onDragEnd = { offsetY = 0f },
                                                onDragCancel = { offsetY = 0f },
                                                onDrag = { change: PointerInputChange, dragAmount: androidx.compose.ui.geometry.Offset ->
                                                    change.consume()
                                                    offsetY += dragAmount.y / density
                                                    val threshold = 56f
                                                    if (offsetY > threshold && index < urlsList.size - 1) {
                                                        viewModel.reorderBatchUrls(index, index + 1)
                                                        offsetY -= threshold
                                                    } else if (offsetY < -threshold && index > 0 && !(state.isRunning && index - 1 <= activeIndex)) {
                                                        viewModel.reorderBatchUrls(index, index - 1)
                                                        offsetY += threshold
                                                    }
                                                }
                                            )
                                        }
                                        .padding(horizontal = AppSpacing.sm, vertical = AppSpacing.sm),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.SpaceBetween
                                ) {
                                    Row(
                                        modifier = Modifier.weight(1f),
                                        verticalAlignment = Alignment.CenterVertically,
                                        horizontalArrangement = Arrangement.spacedBy(AppSpacing.xs)
                                    ) {
                                        if (!isPinned) {
                                            Icon(
                                                imageVector = Icons.Default.DragHandle,
                                                contentDescription = "Sürükle",
                                                tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f),
                                                modifier = Modifier.padding(end = 4.dp).size(20.dp)
                                            )
                                        }
                                        Box(
                                            modifier = Modifier
                                                .size(10.dp)
                                                .background(
                                                    color = when {
                                                        isActive -> MaterialTheme.colorScheme.primary
                                                        state.status.contains("tamam", ignoreCase = true) && index < activeIndex -> AccentGreen
                                                        state.status.contains("hata", ignoreCase = true) && index == activeIndex -> AccentRed
                                                        else -> MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.4f)
                                                    },
                                                    shape = RoundedCornerShape(50)
                                                )
                                        )
                                        Text(
                                            text = "${index + 1}. $url",
                                            style = MaterialTheme.typography.bodyMedium,
                                            maxLines = 1,
                                            overflow = TextOverflow.Ellipsis,
                                            color = if (isActive) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface
                                        )
                                    }
                                    IconButton(
                                        onClick = {
                                            haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                            viewModel.removeUrlFromBatch(index)
                                        },
                                        modifier = Modifier.size(36.dp)
                                    ) {
                                        Text(text = "🗑️", style = MaterialTheme.typography.bodyLarge)
                                    }
                                }
                            }
                        }
                    }
                }
                2 -> { // TAB 2: HISTORY RECORD LIST
                    val formatter = remember { java.text.SimpleDateFormat("dd/MM/yyyy HH:mm", java.util.Locale.getDefault()) }
                    LazyColumn(
                        modifier = Modifier.fillMaxSize(),
                        contentPadding = PaddingValues(AppSpacing.md),
                        verticalArrangement = Arrangement.spacedBy(AppSpacing.sm),
                    ) {
                        item {
                            Row(
                                modifier = Modifier.fillMaxWidth().padding(bottom = AppSpacing.xs),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    text = Translations.get("tab_history", lang) + " (${state.historyRecords.size})",
                                    style = MaterialTheme.typography.titleLarge,
                                    color = MaterialTheme.colorScheme.onSurface
                                )
                                if (state.historyRecords.isNotEmpty()) {
                                    TextButton(
                                        onClick = {
                                            haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                            viewModel.clearHistory()
                                        }
                                    ) {
                                        Text("🧹 " + Translations.get("clear_history_btn", lang))
                                    }
                                }
                            }
                        }

                        if (state.historyRecords.isEmpty()) {
                            item {
                                Card(
                                    modifier = Modifier.fillMaxWidth().padding(top = AppSpacing.lg),
                                    shape = RoundedCornerShape(AppRadius.lg),
                                    border = BorderStroke(1.dp, MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.25f)),
                                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.45f)),
                                ) {
                                    Box(
                                        modifier = Modifier.fillMaxWidth().padding(vertical = 48.dp),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        Column(
                                            horizontalAlignment = Alignment.CenterHorizontally,
                                            verticalArrangement = Arrangement.spacedBy(AppSpacing.xs)
                                        ) {
                                            Text("📜", style = MaterialTheme.typography.headlineLarge)
                                            Text(
                                                text = Translations.get("no_history", lang),
                                                style = MaterialTheme.typography.bodyMedium,
                                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                                textAlign = TextAlign.Center
                                            )
                                        }
                                    }
                                }
                            }
                        } else {
                            items(state.historyRecords.size) { index ->
                                val record = state.historyRecords[index]
                                val recordDate: java.util.Date = java.util.Date(record.downloadedAt)
                                val dateStr = formatter.format(recordDate)
                                
                                Card(
                                    modifier = Modifier.fillMaxWidth(),
                                    shape = RoundedCornerShape(AppRadius.md),
                                    border = BorderStroke(1.dp, MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.2f)),
                                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.5f))
                                ) {
                                    Row(
                                        modifier = Modifier.fillMaxWidth().padding(AppSpacing.md),
                                        horizontalArrangement = Arrangement.spacedBy(AppSpacing.md),
                                        verticalAlignment = Alignment.Top
                                    ) {
                                        if (!record.thumbnailPath.isNullOrBlank() && java.io.File(record.thumbnailPath).exists()) {
                                            val isWaveform = record.thumbnailPath.contains("waveform_")
                                            val imageWidth = 100.dp
                                            val imageHeight = if (isWaveform) 19.dp else 56.dp
                                            val imageScale = if (isWaveform) ContentScale.FillBounds else ContentScale.Crop
                                            AsyncImage(
                                                model = java.io.File(record.thumbnailPath),
                                                contentDescription = "Thumbnail",
                                                modifier = Modifier
                                                    .width(imageWidth)
                                                    .height(imageHeight)
                                                    .clip(RoundedCornerShape(if (isWaveform) 4.dp else 8.dp)),
                                                contentScale = imageScale
                                            )
                                        } else {
                                            Box(
                                                modifier = Modifier
                                                    .width(100.dp)
                                                    .height(56.dp)
                                                    .background(
                                                        brush = Brush.linearGradient(
                                                            colors = listOf(
                                                                MaterialTheme.colorScheme.surfaceVariant,
                                                                MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
                                                            )
                                                        ),
                                                        shape = RoundedCornerShape(8.dp)
                                                    ),
                                                contentAlignment = Alignment.Center
                                            ) {
                                                Icon(
                                                    imageVector = Icons.Default.PlayCircle,
                                                    contentDescription = "No Thumbnail",
                                                    tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f)
                                                )
                                            }
                                        }

                                        Column(
                                            modifier = Modifier.weight(1f),
                                            verticalArrangement = Arrangement.spacedBy(4.dp)
                                        ) {
                                            Row(
                                                modifier = Modifier.fillMaxWidth(),
                                                horizontalArrangement = Arrangement.SpaceBetween,
                                                verticalAlignment = Alignment.Top
                                            ) {
                                                Text(
                                                    text = record.title,
                                                    style = MaterialTheme.typography.bodyMedium,
                                                    color = MaterialTheme.colorScheme.onSurface,
                                                    maxLines = 2,
                                                    overflow = TextOverflow.Ellipsis,
                                                    modifier = Modifier.weight(1f).padding(end = AppSpacing.sm)
                                                )
                                                Box(
                                                    modifier = Modifier
                                                        .background(MaterialTheme.colorScheme.primary.copy(alpha = 0.15f), RoundedCornerShape(4.dp))
                                                        .padding(horizontal = 6.dp, vertical = 2.dp)
                                                ) {
                                                    Text(
                                                        text = record.format.uppercase(),
                                                        style = MaterialTheme.typography.labelSmall,
                                                        color = MaterialTheme.colorScheme.primary
                                                    )
                                                }
                                            }
                                            Text(
                                                text = record.url,
                                                style = MaterialTheme.typography.bodySmall,
                                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                                maxLines = 1,
                                                overflow = TextOverflow.Ellipsis
                                            )
                                            Row(
                                                modifier = Modifier.fillMaxWidth().padding(top = 4.dp),
                                                horizontalArrangement = Arrangement.SpaceBetween,
                                                verticalAlignment = Alignment.CenterVertically
                                            ) {
                                                Text(
                                                    text = dateStr,
                                                    style = MaterialTheme.typography.bodySmall,
                                                    color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f)
                                                )
                                                Row(horizontalArrangement = Arrangement.spacedBy(AppSpacing.xs)) {
                                                    TextButton(
                                                        onClick = {
                                                            haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                                            val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as? android.content.ClipboardManager
                                                            val clip = android.content.ClipData.newPlainText("Copied URL", record.url)
                                                            clipboard?.setPrimaryClip(clip)
                                                        },
                                                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 4.dp)
                                                    ) {
                                                        Text(Translations.get("share_path", lang), style = MaterialTheme.typography.labelSmall)
                                                    }
                                                    TextButton(
                                                        onClick = {
                                                            haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                                            val intent = Intent(Intent.ACTION_SEND).apply {
                                                                type = "text/plain"
                                                                putExtra(Intent.EXTRA_SUBJECT, record.title)
                                                                putExtra(Intent.EXTRA_TEXT, "${record.title}\n${record.url}")
                                                            }
                                                            context.startActivity(Intent.createChooser(intent, "Share media link"))
                                                        },
                                                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 4.dp)
                                                    ) {
                                                        Text(Translations.get("share_file", lang), style = MaterialTheme.typography.labelSmall)
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                3 -> { // TAB 3: SETTINGS & ACCORDIONS
                    LazyColumn(
                        modifier = Modifier.fillMaxSize(),
                        contentPadding = PaddingValues(AppSpacing.md),
                        verticalArrangement = Arrangement.spacedBy(AppSpacing.sm),
                    ) {
                        item {
                            Text(
                                text = Translations.get("tab_settings", lang),
                                style = MaterialTheme.typography.titleLarge,
                                color = MaterialTheme.colorScheme.onSurface,
                                modifier = Modifier.padding(bottom = AppSpacing.xs)
                            )
                        }
                        item {
                            Card(
                                modifier = Modifier.fillMaxWidth().padding(bottom = AppSpacing.xs),
                                shape = RoundedCornerShape(AppRadius.lg),
                                border = BorderStroke(1.dp, MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.25f)),
                                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.65f)),
                            ) {
                                Column(
                                    modifier = Modifier.padding(AppSpacing.md),
                                    verticalArrangement = Arrangement.spacedBy(AppSpacing.sm)
                                ) {
                                    Text(
                                        text = if (lang == "tr") "Görünüm ve Dil" else if (lang == "es") "Apariencia e Idioma" else "Appearance & Language",
                                        style = MaterialTheme.typography.titleMedium,
                                        color = MaterialTheme.colorScheme.primary
                                    )
                                    Row(
                                        modifier = Modifier.fillMaxWidth(),
                                        horizontalArrangement = Arrangement.SpaceBetween,
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Text(
                                            text = if (lang == "tr") "Koyu Tema" else if (lang == "es") "Tema Oscuro" else "Dark Theme",
                                            style = MaterialTheme.typography.bodyMedium,
                                            color = MaterialTheme.colorScheme.onSurface
                                        )
                                        Switch(
                                            checked = state.isDarkTheme,
                                            onCheckedChange = {
                                                haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                                viewModel.toggleTheme()
                                            }
                                        )
                                    }
                                    HorizontalDivider(color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.25f))
                                    Row(
                                        modifier = Modifier.fillMaxWidth(),
                                        horizontalArrangement = Arrangement.SpaceBetween,
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Text(
                                            text = if (lang == "tr") "Dil" else if (lang == "es") "Idioma" else "Language",
                                            style = MaterialTheme.typography.bodyMedium,
                                            color = MaterialTheme.colorScheme.onSurface
                                        )
                                        Row(
                                            modifier = Modifier
                                                .background(
                                                    color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.4f),
                                                    shape = RoundedCornerShape(AppRadius.md)
                                                )
                                                .padding(2.dp),
                                            horizontalArrangement = Arrangement.spacedBy(2.dp)
                                        ) {
                                            Translations.languages.forEach { code ->
                                                val isSelected = code == lang
                                                Box(
                                                    modifier = Modifier
                                                        .background(
                                                            color = if (isSelected) MaterialTheme.colorScheme.primary else Color.Transparent,
                                                            shape = RoundedCornerShape(AppRadius.md)
                                                        )
                                                        .clickable {
                                                            haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                                            viewModel.updateLanguage(code)
                                                        }
                                                        .padding(horizontal = 12.dp, vertical = 6.dp),
                                                    contentAlignment = Alignment.Center
                                                ) {
                                                    Text(
                                                        text = code.uppercase(),
                                                        style = MaterialTheme.typography.labelSmall,
                                                        color = if (isSelected) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurfaceVariant
                                                    )
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        item {
                            AdvancedSection(
                                state = state,
                                viewModel = viewModel,
                                lang = lang,
                                onPickCookiesFile = onPickCookiesFile
                            )
                        }
                        item {
                            DiagnosticsSection(
                                state = state,
                                viewModel = viewModel,
                                lang = lang,
                                onPickYtDlpBinary = onPickYtDlpBinary
                            )
                        }
                    }
                }
            }
        }
    }

    if (showLogSheet) {
        ModalBottomSheet(
            onDismissRequest = { showLogSheet = false },
            containerColor = MaterialTheme.colorScheme.background.copy(alpha = 0.95f)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = AppSpacing.lg * 10)
                    .padding(horizontal = AppSpacing.md, vertical = AppSpacing.sm),
                verticalArrangement = Arrangement.spacedBy(AppSpacing.sm),
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        text = Translations.get("live_log", lang),
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                    TextButton(onClick = viewModel::clearLogs) {
                        Text(Translations.get("clear_log_btn", lang))
                    }
                }
                val scrollState = rememberScrollState()
                LaunchedEffect(state.logs) {
                    scrollState.animateScrollTo(scrollState.maxValue)
                }
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(min = AppSpacing.lg * 7 + AppSpacing.sm, max = 400.dp)
                        .background(
                            color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.25f),
                            shape = RoundedCornerShape(AppRadius.md),
                        )
                        .border(
                            1.dp,
                            MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.2f),
                            RoundedCornerShape(AppRadius.md)
                        )
                        .verticalScroll(scrollState)
                        .padding(AppSpacing.sm),
                ) {
                    Text(
                        text = state.logs.ifBlank { Translations.get("no_logs", lang) },
                        style = MaterialTheme.typography.bodySmall.copy(fontFamily = FontFamily.Monospace),
                        color = MaterialTheme.colorScheme.onSurface
                    )
                }
            }
        }
    }
    }

    activePickerData?.let { data ->
        ModalBottomSheet(
            onDismissRequest = { activePickerData = null },
            containerColor = MaterialTheme.colorScheme.background.copy(alpha = 0.95f)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .navigationBarsPadding()
                    .padding(bottom = AppSpacing.lg)
            ) {
                Text(
                    text = data.title,
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.padding(horizontal = AppSpacing.md, vertical = AppSpacing.sm)
                )
                HorizontalDivider(color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f))
                
                LazyColumn {
                    items(data.options.size) { index ->
                        val option = data.options[index]
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable {
                                    haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                    data.onSelect(option)
                                    activePickerData = null
                                }
                                .padding(horizontal = AppSpacing.md, vertical = AppSpacing.md),
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Text(
                                text = option,
                                style = MaterialTheme.typography.bodyLarge,
                                color = MaterialTheme.colorScheme.onSurface,
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun HeaderCard(
    state: DownloaderUiState,
    viewModel: DownloaderViewModel,
    lang: String
) {
    val haptic = LocalHapticFeedback.current
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(AppRadius.lg),
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.25f)),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.65f)),
    ) {
        Column(
            modifier = Modifier.padding(AppSpacing.md),
            verticalArrangement = Arrangement.spacedBy(AppSpacing.sm),
        ) {
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(AppSpacing.xs)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = Translations.get("title", lang),
                        style = MaterialTheme.typography.titleLarge,
                        color = MaterialTheme.colorScheme.onSurface,
                    )
                    IconButton(onClick = {
                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                        viewModel.toggleTheme()
                    }) {
                        Text(
                            text = if (state.isDarkTheme) "🌙" else "☀️",
                            style = MaterialTheme.typography.titleMedium
                        )
                    }
                }
                
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = if (lang == "tr") "Uygulama Dili" else if (lang == "es") "Idioma de la App" else "App Language",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Row(
                        modifier = Modifier
                            .background(
                                color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.4f),
                                shape = RoundedCornerShape(AppRadius.md)
                            )
                            .padding(2.dp),
                        horizontalArrangement = Arrangement.spacedBy(2.dp)
                    ) {
                        Translations.languages.forEach { code ->
                            val isSelected = code == lang
                            Box(
                                modifier = Modifier
                                    .background(
                                        color = if (isSelected) MaterialTheme.colorScheme.primary else Color.Transparent,
                                        shape = RoundedCornerShape(AppRadius.md)
                                    )
                                    .clickable {
                                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                        viewModel.updateLanguage(code)
                                    }
                                    .padding(horizontal = 12.dp, vertical = 6.dp),
                                contentAlignment = Alignment.Center
                            ) {
                                Text(
                                    text = code.uppercase(),
                                    style = MaterialTheme.typography.labelSmall,
                                    color = if (isSelected) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }
                    }
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = if (lang == "tr") "Kompakt Arayüz" else if (lang == "es") "Interfaz Compacta" else "Compact Interface",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Switch(
                        checked = state.compactMode,
                        onCheckedChange = {
                            haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                            viewModel.toggleCompactMode()
                        }
                    )
                }
            }
            Text(
                text = Translations.get("subtitle", lang),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun SourceSection(
    state: DownloaderUiState,
    viewModel: DownloaderViewModel,
    lang: String
) {
    val haptic = LocalHapticFeedback.current
    SectionCard(title = "source", lang = lang) {
        AnimatedVisibility(visible = state.clipTextDetected.isNotEmpty()) {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable {
                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                        viewModel.pasteDetectedClipboardUrl()
                    },
                shape = RoundedCornerShape(AppRadius.md),
                border = BorderStroke(1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.5f)),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.15f),
                ),
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = AppSpacing.sm, vertical = AppSpacing.sm),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(AppSpacing.xs),
                ) {
                    Text(
                        text = "📋 " + Translations.get("clip_toast", lang),
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.weight(1f)
                    )
                    Text(
                        text = Translations.get("clip_action", lang),
                        style = MaterialTheme.typography.labelLarge,
                        color = MaterialTheme.colorScheme.primary,
                    )
                }
            }
        }

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = Translations.get("batch_switch", lang),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Switch(
                checked = state.isBatchMode,
                onCheckedChange = {
                    haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                    viewModel.toggleBatchMode()
                }
            )
        }

        OutlinedTextField(
            value = state.urlsText,
            onValueChange = viewModel::updateUrlsText,
            modifier = Modifier.fillMaxWidth().heightIn(min = 56.dp),
            singleLine = !state.isBatchMode,
            minLines = if (state.isBatchMode) 3 else 1,
            maxLines = if (state.isBatchMode) 6 else 1,
            label = { Text(Translations.get("url_label", lang)) },
            placeholder = { Text(Translations.get("url_placeholder", lang)) },
            isError = state.urlValidationState == UrlValidationState.INVALID ||
                state.urlValidationState == UrlValidationState.ERROR,
            trailingIcon = {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    IconButton(onClick = {
                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                        viewModel.pasteUrlFromClipboard()
                    }) {
                        Icon(
                            imageVector = Icons.Outlined.ContentPaste,
                            contentDescription = Translations.get("paste_btn", lang),
                        )
                    }
                    IconButton(onClick = {
                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                        viewModel.clearUrl()
                    }) {
                        Icon(
                            imageVector = Icons.Outlined.Clear,
                            contentDescription = Translations.get("clear_btn", lang),
                        )
                    }
                    IconButton(onClick = {
                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                        viewModel.importFromSharedBuffer()
                    }) {
                        Icon(
                            imageVector = Icons.Outlined.Share,
                            contentDescription = Translations.get("share_btn", lang),
                        )
                    }
                }
            },
            supportingText = {
                val errorMsg = state.errorText?.let { Translations.get(it, lang) }
                Text(
                    text = errorMsg ?: state.urlStatusText,
                    color = when {
                        state.errorText != null -> MaterialTheme.colorScheme.error
                        state.urlValidationState == UrlValidationState.INVALID ||
                            state.urlValidationState == UrlValidationState.ERROR -> MaterialTheme.colorScheme.error
                        state.urlValidationState == UrlValidationState.PLAYLIST ||
                            state.urlValidationState == UrlValidationState.VALID -> AccentGreen
                        else -> MaterialTheme.colorScheme.onSurfaceVariant
                    },
                )
            },
        )

        Spacer(modifier = Modifier.height(AppSpacing.xs))
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(AppSpacing.sm)
        ) {
            Button(
                onClick = {
                    haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                    viewModel.startDownload()
                },
                modifier = Modifier.weight(1f).heightIn(min = 40.dp),
                colors = ButtonDefaults.buttonColors(containerColor = AccentIndigo)
            ) {
                Text(
                    text = if (lang == "tr") "📥 Hemen İndir" else if (lang == "es") "📥 Descargar" else "📥 Download Now",
                    style = MaterialTheme.typography.labelLarge
                )
            }

            Button(
                onClick = {
                    haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                    viewModel.addToQueueWithoutStarting()
                },
                modifier = Modifier.weight(1f).heightIn(min = 40.dp),
                colors = ButtonDefaults.buttonColors(containerColor = AccentCyan)
            ) {
                Text(
                    text = if (lang == "tr") "➕ Sıraya Ekle" else if (lang == "es") "➕ Añadir a Cola" else "➕ Add to Queue",
                    style = MaterialTheme.typography.labelLarge
                )
            }
        }

        AnimatedVisibility(visible = state.previewTitle.isNotBlank()) {
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(AppRadius.md),
                border = BorderStroke(1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.2f)),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.05f),
                ),
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = AppSpacing.sm, vertical = AppSpacing.sm),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(AppSpacing.xs),
                ) {
                    Icon(
                        imageVector = Icons.Outlined.Info,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.primary,
                    )
                    val count = state.previewItemCount?.let { " - $it oge" }.orEmpty()
                    Text(
                        text = "${state.previewTitle} - ${state.previewChannel}$count",
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                }
                // Channel Rule Button
                if (viewModel.getPreviewChannelId() != null) {
                    TextButton(
                        onClick = {
                            val chId = viewModel.getPreviewChannelId() ?: return@TextButton
                            val chName = viewModel.getPreviewChannelName()
                            viewModel.saveChannelRule(chId, chName)
                        }
                    ) {
                        Text(
                            text = "\uD83D\uDCCC " + Translations.get("btn_create_channel_rule", lang),
                            style = MaterialTheme.typography.labelSmall
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun PresetSection(
    state: DownloaderUiState,
    viewModel: DownloaderViewModel,
    lang: String
) {
    val haptic = LocalHapticFeedback.current
    SectionCard(title = "preset_label", lang = lang) {
        Column(verticalArrangement = Arrangement.spacedBy(AppSpacing.sm)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(AppSpacing.xs)
            ) {
                PresetButton(
                    title = if (lang == "tr") "En İyi Kalite" else if (lang == "es") "Mejor Calidad" else "Best Quality",
                    icon = "🚀",
                    selected = state.videoPreset == "Maksimum (Best)" && state.mode == DownloadMode.VIDEO,
                    onClick = {
                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                        viewModel.updateMode(DownloadMode.VIDEO)
                        viewModel.updateVideoPreset("Maksimum (Best)")
                    },
                    modifier = Modifier.weight(1f)
                )
                PresetButton(
                    title = "Full HD 1080p",
                    icon = "📺",
                    selected = state.videoPreset == "Full HD (1080p)" && state.mode == DownloadMode.VIDEO,
                    onClick = {
                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                        viewModel.updateMode(DownloadMode.VIDEO)
                        viewModel.updateVideoPreset("Full HD (1080p)")
                    },
                    modifier = Modifier.weight(1f)
                )
            }
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(AppSpacing.xs)
            ) {
                PresetButton(
                    title = if (lang == "tr") "Dengeli 720p" else if (lang == "es") "Equilibrado 720p" else "Speedy 720p",
                    icon = "⚡",
                    selected = state.videoPreset == "Dengeli (720p)" && state.mode == DownloadMode.VIDEO,
                    onClick = {
                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                        viewModel.updateMode(DownloadMode.VIDEO)
                        viewModel.updateVideoPreset("Dengeli (720p)")
                    },
                    modifier = Modifier.weight(1f)
                )
                PresetButton(
                    title = if (lang == "tr") "MP3 Müzik" else if (lang == "es") "Música MP3" else "MP3 Music",
                    icon = "🎵",
                    selected = state.mode == DownloadMode.AUDIO && state.audioFormat == "mp3",
                    onClick = {
                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                        viewModel.updateMode(DownloadMode.AUDIO)
                        viewModel.updateAudioFormat("mp3")
                        viewModel.updateAudioQualityPreset("Dengeli (192K)")
                    },
                    modifier = Modifier.weight(1f)
                )
            }
        }
    }
}

@Composable
private fun PresetButton(
    title: String,
    icon: String,
    selected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier
            .height(56.dp)
            .clickable(onClick = onClick),
        shape = RoundedCornerShape(AppRadius.md),
        border = BorderStroke(
            width = 1.dp,
            color = if (selected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.25f)
        ),
        colors = CardDefaults.cardColors(
            containerColor = if (selected) MaterialTheme.colorScheme.primary.copy(alpha = 0.12f)
                             else MaterialTheme.colorScheme.surface.copy(alpha = 0.45f)
        )
    ) {
        Row(
            modifier = Modifier.fillMaxSize().padding(horizontal = AppSpacing.sm),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(AppSpacing.xs)
        ) {
            Text(text = icon, style = MaterialTheme.typography.titleMedium)
            Text(
                text = title,
                style = MaterialTheme.typography.labelMedium,
                color = if (selected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
        }
    }
}

@Composable
private fun OutputSection(
    state: DownloaderUiState,
    viewModel: DownloaderViewModel,
    lang: String
) {
    SectionCard(title = "output", lang = lang) {
        SingleChoiceSegmentedButtonRow(modifier = Modifier.fillMaxWidth()) {
            SegmentedButton(
                selected = state.mode == DownloadMode.VIDEO,
                onClick = { viewModel.updateMode(DownloadMode.VIDEO) },
                shape = SegmentedButtonDefaults.itemShape(index = 0, count = 2),
            ) {
                Text(Translations.get("video", lang))
            }
            SegmentedButton(
                selected = state.mode == DownloadMode.AUDIO,
                onClick = { viewModel.updateMode(DownloadMode.AUDIO) },
                shape = SegmentedButtonDefaults.itemShape(index = 1, count = 2),
            ) {
                Text(Translations.get("audio", lang))
            }
        }

        val videoOptionsEnabled = state.mode == DownloadMode.VIDEO
        val alphaVideo = if (videoOptionsEnabled) 1f else 0.45f

        Column(
            modifier = Modifier.fillMaxWidth().alpha(alphaVideo),
            verticalArrangement = Arrangement.spacedBy(AppSpacing.sm)
        ) {
            OptionPicker(
                label = Translations.get("profile", lang),
                selected = state.videoPreset,
                options = VIDEO_PRESET_HEIGHT.keys.toList(),
                enabled = videoOptionsEnabled,
                onSelect = viewModel::updateVideoPreset,
            )

            val customHeightEnabled = videoOptionsEnabled && state.videoPreset == "Ozel"
            val alphaCustom = if (customHeightEnabled) 1f else 0.45f
            Column(modifier = Modifier.alpha(alphaCustom)) {
                OptionPicker(
                    label = Translations.get("max_res", lang),
                    selected = state.customVideoHeight,
                    options = VIDEO_LIMIT_OPTIONS,
                    enabled = customHeightEnabled,
                    onSelect = viewModel::updateCustomVideoHeight,
                )
            }

            OptionPicker(
                label = Translations.get("format", lang),
                selected = state.videoContainer,
                options = VIDEO_CONTAINER_OPTIONS,
                enabled = videoOptionsEnabled,
                onSelect = viewModel::updateVideoContainer,
            )
            OptionPicker(
                label = Translations.get("codec", lang),
                selected = state.videoAudioCodec,
                options = VIDEO_AUDIO_CODEC_OPTIONS,
                enabled = videoOptionsEnabled,
                onSelect = viewModel::updateVideoAudioCodec,
            )
        }

        val audioOptionsEnabled = state.mode == DownloadMode.AUDIO
        val alphaAudio = if (audioOptionsEnabled) 1f else 0.45f

        Column(
            modifier = Modifier.fillMaxWidth().alpha(alphaAudio),
            verticalArrangement = Arrangement.spacedBy(AppSpacing.sm)
        ) {
            OptionPicker(
                label = Translations.get("audio_qual", lang),
                selected = state.audioQualityPreset,
                options = AUDIO_PRESET_QUALITY.keys.toList(),
                enabled = audioOptionsEnabled,
                onSelect = viewModel::updateAudioQualityPreset,
            )
            OptionPicker(
                label = Translations.get("audio_format", lang),
                selected = state.audioFormat,
                options = AUDIO_FORMAT_OPTIONS,
                enabled = audioOptionsEnabled,
                onSelect = viewModel::updateAudioFormat,
            )
        }

        HorizontalDivider(color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.25f))

        Text(
            text = buildOutputSummary(state, lang),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@Composable
private fun StorageSection(
    state: DownloaderUiState,
    viewModel: DownloaderViewModel,
    lang: String,
    onPickOutputFolder: () -> Unit,
    onRequestMediaPermissions: () -> Unit,
) {
    SectionCard(title = "storage", lang = lang) {
        Text(
            text = "${Translations.get("output_folder", lang)}: ${shortPath(state.outputDir)}",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurface
        )
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(AppSpacing.xs),
        ) {
            OutlinedButton(
                onClick = onPickOutputFolder,
                modifier = Modifier.weight(1f).heightIn(min = 48.dp),
            ) {
                Text(Translations.get("change_btn", lang))
            }
            OutlinedButton(
                onClick = viewModel::useDefaultOutputDir,
                modifier = Modifier.weight(1f).heightIn(min = 48.dp),
            ) {
                Text(Translations.get("default_btn", lang))
            }
        }

        val context = LocalContext.current
        Button(
            onClick = {
                openDownloadFolder(context, state.outputDir)
            },
            modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp),
            colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
        ) {
            Text("📂 " + Translations.get("open_folder_btn", lang))
        }

        OutlinedButton(
            onClick = viewModel::toggleFullOutputPath,
            modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp),
        ) {
            Text(Translations.get(if (state.showFullOutputPath) "hide_full" else "show_full", lang))
        }

        AnimatedVisibility(visible = state.showFullOutputPath) {
            Text(
                text = state.outputDir,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }

        if (!state.mediaPermissionsGranted) {
            Text(
                text = Translations.get("perm_req", lang),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Button(
                onClick = onRequestMediaPermissions,
                modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp),
                colors = ButtonDefaults.buttonColors(containerColor = AccentIndigo)
            ) {
                Text(Translations.get("perm_grant", lang))
            }
        } else {
            Text(
                text = Translations.get("perm_ok", lang),
                style = MaterialTheme.typography.bodySmall,
                color = AccentGreen,
            )
        }
    }
}

@Composable
private fun AdvancedSection(
    state: DownloaderUiState,
    viewModel: DownloaderViewModel,
    lang: String,
    onPickCookiesFile: () -> Unit,
) {
    var activeTab by remember { mutableStateOf(0) }
    val haptic = LocalHapticFeedback.current

    ExpandableSectionCard(
        title = "advanced",
        lang = lang,
        expanded = state.showAdvanced,
        onToggle = { viewModel.updateShowAdvanced(!state.showAdvanced) },
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .background(
                    MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f),
                    RoundedCornerShape(AppRadius.md)
                )
                .padding(4.dp),
            horizontalArrangement = Arrangement.spacedBy(4.dp)
        ) {
            val tabs = listOf("tab_codecs", "tab_limits", "tab_flags", "sec_trimming", "tab_scheduling")
            tabs.forEachIndexed { index, tabKey ->
                val selected = activeTab == index
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .background(
                            color = if (selected) MaterialTheme.colorScheme.primary else Color.Transparent,
                            shape = RoundedCornerShape(AppRadius.md)
                        )
                        .clickable {
                            haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                            activeTab = index
                        }
                        .padding(vertical = AppSpacing.xs),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = Translations.get(tabKey, lang),
                        style = MaterialTheme.typography.labelMedium,
                        color = if (selected) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurfaceVariant,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(4.dp))

        when (activeTab) {
            0 -> { // Formats & Codecs Setup screen
                OutputSection(state = state, viewModel = viewModel, lang = lang)
                LabeledTextField(
                    label = Translations.get("lbl_template", lang),
                    value = state.outputTemplate,
                    onValueChange = viewModel::updateOutputTemplate,
                )
                LabeledTextField(
                    label = Translations.get("lbl_range", lang),
                    value = state.playlistItems,
                    placeholder = Translations.get("lbl_placeholder_range", lang),
                    onValueChange = viewModel::updatePlaylistItems,
                )
            }
            1 -> { // Limits, Speed, and Cookies setup
                LabeledTextField(
                    label = Translations.get("lbl_max_dl", lang),
                    value = state.maxDownloads,
                    keyboardType = KeyboardType.Number,
                    placeholder = Translations.get("lbl_placeholder_max", lang),
                    onValueChange = viewModel::updateMaxDownloads,
                )
                LabeledTextField(
                    label = Translations.get("lbl_speed", lang),
                    value = state.rateLimit,
                    placeholder = Translations.get("lbl_placeholder_speed", lang),
                    onValueChange = viewModel::updateRateLimit,
                )
                LabeledTextField(
                    label = Translations.get("lbl_retry", lang),
                    value = state.retries,
                    keyboardType = KeyboardType.Number,
                    placeholder = Translations.get("lbl_placeholder_retry", lang),
                    onValueChange = viewModel::updateRetries,
                )
                LabeledTextField(
                    label = Translations.get("lbl_concurrent", lang),
                    value = state.concurrentFragments,
                    keyboardType = KeyboardType.Number,
                    placeholder = Translations.get("lbl_placeholder_fragments", lang),
                    onValueChange = viewModel::updateConcurrentFragments,
                )
                OptionPicker(
                    label = Translations.get("lbl_cookies", lang),
                    selected = state.browserCookies,
                    options = BROWSER_COOKIE_SOURCES,
                    onSelect = viewModel::updateBrowserCookies,
                )
                LabeledTextField(
                    label = Translations.get("lbl_cookies_file", lang),
                    value = state.cookiesFile,
                    placeholder = "cookies.txt",
                    onValueChange = viewModel::updateCookiesFile,
                )
                OutlinedButton(
                    onClick = onPickCookiesFile,
                    modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp),
                ) {
                    Text(Translations.get("cookies_btn", lang))
                }
                LabeledTextField(
                    label = Translations.get("lbl_extra", lang),
                    value = state.extraArgs,
                    placeholder = Translations.get("lbl_placeholder_extra", lang),
                    onValueChange = viewModel::updateExtraArgs,
                )
            }
            2 -> { // Download Behavior toggle settings
                ToggleRow(
                    text = Translations.get("chk_thumb", lang),
                    helper = Translations.get("chk_thumb_desc", lang),
                    checked = state.thumbnail,
                    onCheckedChange = viewModel::updateThumbnail,
                )
                ToggleRow(
                    text = Translations.get("chk_subs", lang),
                    helper = Translations.get("chk_subs_desc", lang),
                    checked = state.subtitles,
                    onCheckedChange = viewModel::updateSubtitles,
                )
                ToggleRow(
                    text = Translations.get("chk_auto_subs", lang),
                    helper = Translations.get("chk_auto_subs_desc", lang),
                    checked = state.autoSubtitles,
                    onCheckedChange = viewModel::updateAutoSubtitles,
                )
                ToggleRow(
                    text = Translations.get("chk_metadata", lang),
                    helper = Translations.get("chk_metadata_desc", lang),
                    checked = state.metadata,
                    onCheckedChange = viewModel::updateMetadata,
                )
                ToggleRow(
                    text = Translations.get("chk_archive", lang),
                    helper = Translations.get("chk_archive_desc", lang),
                    checked = state.downloadArchive,
                    onCheckedChange = viewModel::updateDownloadArchive,
                )
                ToggleRow(
                    text = Translations.get("chk_restrict", lang),
                    helper = Translations.get("chk_restrict_desc", lang),
                    checked = state.restrictNames,
                    onCheckedChange = viewModel::updateRestrictNames,
                )
                ToggleRow(
                    text = Translations.get("chk_playlist", lang),
                    helper = Translations.get("chk_playlist_desc", lang),
                    checked = state.playlistEnabled,
                    onCheckedChange = viewModel::updatePlaylistEnabled,
                )
                ToggleRow(
                    text = Translations.get("chk_403", lang),
                    helper = Translations.get("chk_403_desc", lang),
                    checked = state.youtube403Fallback,
                    onCheckedChange = viewModel::updateYoutube403Fallback,
                )
                
                val folderOrgKeys = listOf("None", "Channel", "Year", "Format", "Channel_Year")
                val folderOrgOptions = folderOrgKeys.map { key ->
                    when (key) {
                        "None" -> Translations.get("folder_org_none", lang)
                        "Channel" -> Translations.get("folder_org_channel", lang)
                        "Year" -> Translations.get("folder_org_year", lang)
                        "Format" -> Translations.get("folder_org_format", lang)
                        "Channel_Year" -> Translations.get("folder_org_channel_year", lang)
                        else -> key
                    }
                }
                val currentFolderOrgText = when (state.folderOrg) {
                    "None" -> Translations.get("folder_org_none", lang)
                    "Channel" -> Translations.get("folder_org_channel", lang)
                    "Year" -> Translations.get("folder_org_year", lang)
                    "Format" -> Translations.get("folder_org_format", lang)
                    "Channel_Year" -> Translations.get("folder_org_channel_year", lang)
                    else -> Translations.get("folder_org_none", lang)
                }

                androidx.compose.foundation.layout.Spacer(modifier = Modifier.height(AppSpacing.sm))
                OptionPicker(
                    label = Translations.get("lbl_folder_org", lang),
                    selected = currentFolderOrgText,
                    options = folderOrgOptions,
                    enabled = true,
                    onSelect = { selectedText ->
                        val idx = folderOrgOptions.indexOf(selectedText)
                        if (idx >= 0) {
                            viewModel.updateFolderOrg(folderOrgKeys[idx])
                        }
                    }
                )
            }
            3 -> { // Video Trimming section
                ToggleRow(
                    text = Translations.get("lbl_trim_enable", lang),
                    helper = Translations.get("sec_trimming", lang),
                    checked = state.clipEnabled,
                    onCheckedChange = viewModel::updateClipEnabled,
                )
                if (state.clipEnabled) {
                    LabeledTextField(
                        label = Translations.get("lbl_trim_start", lang),
                        value = state.clipStart,
                        placeholder = "00:00",
                        onValueChange = viewModel::updateClipStart,
                    )
                    LabeledTextField(
                        label = Translations.get("lbl_trim_end", lang),
                        value = state.clipEnd,
                        placeholder = "00:00",
                        onValueChange = viewModel::updateClipEnd,
                    )
                }
            }
            4 -> { // Network & Scheduler Tab
                ToggleRow(
                    text = Translations.get("lbl_wifi_only", lang),
                    helper = Translations.get("lbl_wifi_only_desc", lang),
                    checked = state.wifiOnly,
                    onCheckedChange = viewModel::updateWifiOnly,
                )
                ToggleRow(
                    text = Translations.get("lbl_schedule_enable", lang),
                    helper = Translations.get("lbl_schedule_desc", lang),
                    checked = state.schedulerEnabled,
                    onCheckedChange = viewModel::updateSchedulerEnabled,
                )
                if (state.schedulerEnabled) {
                    LabeledTextField(
                        label = Translations.get("lbl_schedule_time", lang),
                        value = state.schedulerTime,
                        placeholder = "03:00",
                        onValueChange = viewModel::updateSchedulerTime,
                    )
                }
            }
        }
    }
}

@Composable
private fun DiagnosticsSection(
    state: DownloaderUiState,
    viewModel: DownloaderViewModel,
    lang: String,
    onPickYtDlpBinary: () -> Unit,
) {
    ExpandableSectionCard(
        title = "diagnostics",
        lang = lang,
        expanded = state.showDiagnostics,
        onToggle = viewModel::toggleDiagnostics,
    ) {
        Text(
            text = state.binaryStatus,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Text(
            text = "${Translations.get("device_abi", lang)}: ${state.detectedAbi.ifBlank { "..." }}",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Text(
            text = "${Translations.get("runtime_path", lang)}: ${state.executablePath}",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        if (state.ffmpegLocation.isNotBlank()) {
            Text(
                text = "${Translations.get("ffmpeg_path", lang)}: ${state.ffmpegLocation}",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(AppSpacing.xs),
        ) {
            OutlinedButton(
                onClick = viewModel::refreshEmbeddedBinary,
                modifier = Modifier.weight(1f).heightIn(min = 48.dp),
            ) {
                Text(Translations.get("update_btn", lang))
            }
            val runtimeFailed = state.binaryStatus.contains("hazirlanamadi", ignoreCase = true) ||
                state.binaryStatus.contains("basarisiz", ignoreCase = true)
            if (runtimeFailed) {
                OutlinedButton(
                    onClick = onPickYtDlpBinary,
                    modifier = Modifier.weight(1f).heightIn(min = 48.dp),
                ) {
                    Text(Translations.get("pick_btn", lang))
                }
            }
        }
    }
}

@Composable
private fun StickyDownloadBar(
    state: DownloaderUiState,
    progress: Float,
    lang: String,
    viewModel: DownloaderViewModel,
    onPrimaryAction: () -> Unit,
    onLogClick: () -> Unit,
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = AppSpacing.md, vertical = AppSpacing.xs),
        shape = RoundedCornerShape(AppRadius.lg),
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.35f)),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.85f)
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 8.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = AppSpacing.md, vertical = AppSpacing.sm),
            verticalArrangement = Arrangement.spacedBy(AppSpacing.xs),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(
                    modifier = Modifier.weight(1f),
                    verticalArrangement = Arrangement.spacedBy(AppSpacing.xs / 4),
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = Translations.get(state.statusLabel(), lang),
                            style = MaterialTheme.typography.titleMedium,
                            color = if (state.errorText != null) {
                                MaterialTheme.colorScheme.error
                            } else if (!state.isRunning && state.progress >= 1f) {
                                AccentGreen
                            } else {
                                MaterialTheme.colorScheme.primary
                            },
                        )
                        AnimatedVisibility(
                            visible = !state.isRunning && state.progress >= 1f,
                            enter = androidx.compose.animation.expandHorizontally() + androidx.compose.animation.fadeIn(),
                            exit = androidx.compose.animation.shrinkHorizontally() + androidx.compose.animation.fadeOut()
                        ) {
                            Icon(
                                imageVector = Icons.Default.CheckCircle,
                                contentDescription = "Done",
                                tint = AccentGreen,
                                modifier = Modifier.padding(start = 6.dp).size(18.dp)
                            )
                        }
                    }
                    Text(
                        text = state.progressMeta(lang),
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
                
                TextButton(onClick = onLogClick) {
                    Text("LOG")
                }
                
                Button(
                    onClick = onPrimaryAction,
                    modifier = Modifier.width(112.dp).heightIn(min = 48.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = when {
                            state.isRunning -> AccentRed
                            state.errorText != null -> AccentCyan
                            else -> AccentIndigo
                        }
                    )
                ) {
                    Text(
                        text = Translations.get(state.primaryCtaLabel(), lang),
                        textAlign = TextAlign.Center
                    )
                }
            }

            if (state.isRunning || state.progress > 0f) {
                val cf = state.concurrentFragments.toIntOrNull() ?: 1
                SegmentedProgressBar(
                    progress = state.progress,
                    segmentsCount = cf,
                    isRunning = state.isRunning,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(8.dp)
                )
            }

            // Live Speed Sparkline Graph
            if (state.isRunning) {
                val taskStateForGraph = viewModel.activeTaskState.collectAsState()
                SpeedSparkline(
                    taskState = taskStateForGraph,
                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                )
            }
        }
    }
}

@Composable
private fun SpeedSparkline(
    taskState: State<com.baynuman.ytdownloader.data.ActiveTaskState>,
    modifier: Modifier = Modifier
) {
    val accentColor = AccentCyan
    val gridColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f)

    Canvas(modifier = modifier
        .fillMaxWidth()
        .height(48.dp)
        .clip(RoundedCornerShape(8.dp))
        .background(MaterialTheme.colorScheme.surface.copy(alpha = 0.3f))
    ) {
        // DrawPhase isolation: read state ONLY inside draw lambda
        val state = taskState.value
        val history = state.speedHistory
        val writeIdx = state.speedWriteIdx

        // Linearize circular buffer from write pointer
        val ordered = if (writeIdx < history.size) {
            history.subList(writeIdx, history.size) + history.subList(0, writeIdx)
        } else {
            history
        }
        val maxVal = (ordered.maxOrNull() ?: 0f).coerceAtLeast(0.01f)

        // Grid reference lines (25%, 50%, 75%)
        for (i in 1..3) {
            val y = size.height * (1f - i / 4f)
            drawLine(
                color = gridColor,
                start = Offset(0f, y),
                end = Offset(size.width, y),
                strokeWidth = 1f,
                pathEffect = PathEffect.dashPathEffect(floatArrayOf(4f, 4f))
            )
        }

        // Speed line path
        if (ordered.size >= 2) {
            val linePath = Path()
            ordered.forEachIndexed { idx, value ->
                val x = (idx.toFloat() / (ordered.size - 1).coerceAtLeast(1).toFloat()) * size.width
                val y = size.height - (value / maxVal) * (size.height - 4f)
                if (idx == 0) linePath.moveTo(x, y) else linePath.lineTo(x, y)
            }
            drawPath(
                path = linePath,
                color = accentColor,
                style = Stroke(
                    width = 2.dp.toPx(),
                    cap = StrokeCap.Round
                )
            )

            // Fill area beneath the line
            val fillPath = Path().apply {
                addPath(linePath)
                lineTo(size.width, size.height)
                lineTo(0f, size.height)
                close()
            }
            drawPath(fillPath, accentColor.copy(alpha = 0.08f))
        }
    }
}

@Composable
private fun SectionCard(
    title: String,
    lang: String,
    modifier: Modifier = Modifier,
    alpha: Float = 1f,
    content: @Composable ColumnScope.() -> Unit,
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(AppRadius.lg),
        border = BorderStroke(
            1.dp,
            MaterialTheme.colorScheme.surfaceVariant.copy(alpha = if (alpha < 1f) 0.12f else 0.25f)
        ),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface.copy(alpha = if (alpha < 1f) 0.35f else 0.65f)
        ),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(AppSpacing.md),
            verticalArrangement = Arrangement.spacedBy(AppSpacing.sm),
        ) {
            Text(
                text = Translations.get(title, lang),
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = alpha),
            )
            content()
        }
    }
}

@Composable
private fun ExpandableSectionCard(
    title: String,
    lang: String,
    expanded: Boolean,
    onToggle: () -> Unit,
    content: @Composable ColumnScope.() -> Unit,
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(AppRadius.lg),
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.25f)),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.65f)
        ),
    ) {
        Column(modifier = Modifier.fillMaxWidth()) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable(onClick = onToggle)
                    .padding(horizontal = AppSpacing.md, vertical = AppSpacing.sm),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = Translations.get(title, lang),
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onSurface,
                )
                Icon(
                    imageVector = Icons.Outlined.ArrowDropDown,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            AnimatedVisibility(visible = expanded) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(start = AppSpacing.md, end = AppSpacing.md, bottom = AppSpacing.md),
                    verticalArrangement = Arrangement.spacedBy(AppSpacing.sm),
                ) {
                    content()
                }
            }
        }
    }
}

@Composable
private fun LabeledTextField(
    label: String,
    value: String,
    onValueChange: (String) -> Unit,
    keyboardType: KeyboardType = KeyboardType.Text,
    readOnly: Boolean = false,
    placeholder: String? = null,
) {
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        modifier = Modifier.fillMaxWidth().heightIn(min = 56.dp),
        singleLine = true,
        readOnly = readOnly,
        label = { Text(label) },
        placeholder = if (placeholder != null) {
            { Text(placeholder) }
        } else {
            null
        },
        keyboardOptions = KeyboardOptions(keyboardType = keyboardType),
    )
}

@Composable
private fun ToggleRow(
    text: String,
    helper: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
) {
    Row(
        modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(
            modifier = Modifier
                .weight(1f)
                .padding(end = AppSpacing.sm),
            verticalArrangement = Arrangement.spacedBy(AppSpacing.xs / 4),
        ) {
            Text(
                text = text,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurface
            )
            Text(
                text = helper,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        Switch(checked = checked, onCheckedChange = onCheckedChange)
    }
}

@Composable
private fun OptionPicker(
    label: String,
    selected: String,
    options: List<String>,
    enabled: Boolean = true,
    onSelect: (String) -> Unit,
) {
    val haptic = LocalHapticFeedback.current
    val showPicker = LocalShowPicker.current

    Column(verticalArrangement = Arrangement.spacedBy(AppSpacing.xs - AppSpacing.xs / 4)) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Box {
            OutlinedButton(
                onClick = {
                    if (enabled) {
                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                        showPicker(PickerData(title = label, options = options, onSelect = onSelect))
                    }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = 52.dp),
                enabled = enabled
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        text = selected,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                    Icon(
                        imageVector = Icons.Outlined.ArrowDropDown,
                        contentDescription = null,
                    )
                }
            }
        }
    }
}

private fun buildOutputSummary(state: DownloaderUiState, lang: String): String {
    val selectedText = if (lang == "tr") "Seçilen" else if (lang == "es") "Seleccionado" else "Selected"
    return if (state.mode == DownloadMode.VIDEO) {
        val quality = VIDEO_PRESET_HEIGHT[state.videoPreset]?.let {
            if (it == "CUSTOM") state.customVideoHeight else it
        } ?: "1080"
        val qualityText = if (quality == "Best") "Best" else "${quality}p"
        "$selectedText: $qualityText - ${state.videoContainer.uppercase()} - ${state.videoAudioCodec}"
    } else {
        "$selectedText: ${state.audioQualityPreset} - ${state.audioFormat.uppercase()}"
    }
}

private fun shortPath(path: String): String {
    val normalized = path.replace('\\', '/')
    val marker = "/Download/"
    return if (normalized.contains(marker, ignoreCase = true)) {
        "Download/" + normalized.substringAfter(marker)
    } else {
        normalized.split('/').takeLast(2).joinToString("/")
    }
}

private fun DownloaderUiState.statusLabel(): String {
    return when {
        isRunning -> "sticky_dl"
        errorText != null -> "sticky_err"
        status.contains("tamam", ignoreCase = true) -> "sticky_done"
        else -> "sticky_ready"
    }
}

private fun DownloaderUiState.primaryCtaLabel(): String {
    return when {
        isRunning -> "btn_pause"
        errorText != null -> "btn_retry"
        else -> "btn_start"
    }
}

private fun DownloaderUiState.progressMeta(lang: String): String {
    val percent = "${(progress * 100).toInt()}%"
    return when {
        isRunning -> {
            val etaValue = if (etaText == "--") "ETA --" else "ETA $etaText"
            val playlist = if (playlistProgressText.isNotBlank()) " - $playlistProgressText" else ""
            "$percent - $speedText - $etaValue$playlist"
        }
        status.contains("tamam", ignoreCase = true) -> Translations.get("info_pasted", lang)
        errorText != null -> Translations.get(errorText, lang)
        else -> Translations.get("sticky_ready", lang)
    }
}

private fun openDownloadFolder(context: android.content.Context, outputDir: String) {
    val normalized = outputDir.replace('\\', '/')
    val isDownloadDir = normalized.contains("/Download", ignoreCase = true)
    
    val primaryUri = if (isDownloadDir) {
        android.net.Uri.parse("content://com.android.externalstorage.documents/document/primary%3ADownload")
    } else {
        android.net.Uri.parse("content://com.android.externalstorage.documents/document/primary%3ADocuments")
    }

    val strategies = listOf(
        {
            android.content.Intent(android.content.Intent.ACTION_VIEW).apply {
                setDataAndType(primaryUri, "vnd.android.document/directory")
                flags = android.content.Intent.FLAG_ACTIVITY_NEW_TASK or android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION
            }
        },
        {
            android.content.Intent(android.content.Intent.ACTION_VIEW).apply {
                setDataAndType(android.net.Uri.parse("content://com.android.providers.downloads.documents/document/downloads"), "vnd.android.document/directory")
                flags = android.content.Intent.FLAG_ACTIVITY_NEW_TASK
            }
        },
        {
            android.content.Intent(android.content.Intent.ACTION_VIEW).apply {
                setDataAndType(android.net.Uri.parse("content://media/external/file"), "vnd.android.document/directory")
                flags = android.content.Intent.FLAG_ACTIVITY_NEW_TASK
            }
        },
        {
            android.content.Intent(android.content.Intent.ACTION_GET_CONTENT).apply {
                type = "*/*"
                flags = android.content.Intent.FLAG_ACTIVITY_NEW_TASK
            }
        }
    )

    for (strategy in strategies) {
        try {
            val intent = strategy()
            context.startActivity(intent)
            return // Success!
        } catch (e: Exception) {
            android.util.Log.d("DownloaderScreen", "openDownloadFolder strategy failed", e)
        }
    }
    
    android.widget.Toast.makeText(context, "Klasor acilamadi", android.widget.Toast.LENGTH_LONG).show()
}

@Composable
fun SegmentedProgressBar(
    progress: Float,
    segmentsCount: Int,
    isRunning: Boolean,
    modifier: Modifier = Modifier
) {
    val isCompleted = !isRunning && progress >= 1f
    val barColor by animateColorAsState(
        targetValue = if (isCompleted) AccentGreen else AccentCyan,
        animationSpec = tween(durationMillis = 800),
        label = "progressBarColor"
    )
    
    val trackColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)

    Canvas(
        modifier = modifier
            .fillMaxWidth()
            .height(8.dp)
            .clip(RoundedCornerShape(4.dp))
    ) {
        val width = size.width
        val height = size.height

        if (segmentsCount <= 1) {
            drawRect(
                color = trackColor,
                topLeft = Offset.Zero,
                size = size
            )
            val fillWidth = width * progress
            if (fillWidth > 0f) {
                drawRect(
                    color = barColor,
                    topLeft = Offset.Zero,
                    size = Size(fillWidth, height)
                )
            }
        } else {
            val gap = 4.dp.toPx()
            val segWidth = (width - (segmentsCount - 1) * gap) / segmentsCount

            for (i in 0 until segmentsCount) {
                val segProgress = ((progress - (i.toFloat() / segmentsCount)) * segmentsCount).coerceIn(0f, 1f)
                val x0 = i * (segWidth + gap)
                
                drawRect(
                    color = trackColor,
                    topLeft = Offset(x0, 0f),
                    size = Size(segWidth, height)
                )

                if (segProgress > 0f) {
                    val filledW = segWidth * segProgress
                    val segColor = if (isCompleted) {
                        AccentGreen
                    } else {
                        when (i % 4) {
                            0 -> AccentCyan
                            1 -> AccentIndigo
                            2 -> Color(0xFF8B5CF6)
                            3 -> Color(0xFFEC4899)
                            else -> AccentCyan
                        }
                    }
                    drawRect(
                        color = segColor,
                        topLeft = Offset(x0, 0f),
                        size = Size(filledW, height)
                    )
                }
            }
        }
    }
}

```

---
