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
}
