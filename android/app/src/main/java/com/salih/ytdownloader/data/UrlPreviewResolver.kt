package com.salih.ytdownloader.data

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
)

class UrlPreviewResolver(
    private val appContext: Context,
) {
    fun resolve(url: String): UrlPreview {
        val youtubeDL = YoutubeDL.getInstance()
        youtubeDL.init(appContext)

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
                if (error.isEmpty()) "Baglanti bilgisi alinamadi." else error,
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
        )
    }

    private fun extractJson(output: String): JSONObject {
        val trimmed = output.trim()
        if (trimmed.startsWith("{") && trimmed.endsWith("}")) {
            return JSONObject(trimmed)
        }

        val start = trimmed.indexOf('{')
        val end = trimmed.lastIndexOf('}')
        if (start >= 0 && end > start) {
            return JSONObject(trimmed.substring(start, end + 1))
        }

        throw YoutubeDLException("Baglanti verisi okunamadi.")
    }
}
