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
    suspend fun insertRecord(record: DownloadRecordEntity)

    @Query("DELETE FROM download_history WHERE id = :id")
    suspend fun deleteRecordById(id: String)

    @Query("DELETE FROM download_history")
    suspend fun clearAll()
}
