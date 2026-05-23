package com.salih.ytdownloader.data

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
