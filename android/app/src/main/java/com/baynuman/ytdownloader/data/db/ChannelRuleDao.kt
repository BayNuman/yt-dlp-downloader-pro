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
