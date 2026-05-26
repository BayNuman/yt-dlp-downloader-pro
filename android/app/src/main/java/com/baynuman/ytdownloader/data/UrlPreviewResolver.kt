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
