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
