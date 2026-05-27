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
