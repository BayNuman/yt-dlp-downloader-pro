package com.baynuman.ytdownloader.ui

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.ArrowDropDown
import androidx.compose.material.icons.outlined.Clear
import androidx.compose.material.icons.outlined.ContentPaste
import androidx.compose.material.icons.outlined.Info
import android.content.Context
import android.content.Intent
import androidx.compose.material.icons.outlined.Share
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
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
    val lang = state.currentLanguage
    val haptic = LocalHapticFeedback.current
    val context = LocalContext.current

    // Smart auto-paste and clipboard monitor on resume/focus
    val lifecycleOwner = androidx.lifecycle.compose.LocalLifecycleOwner.current
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
                        item { PresetSection(state = state, viewModel = viewModel, lang = lang) }
                        item { StorageSection(state = state, viewModel = viewModel, lang = lang, onPickOutputFolder = onPickOutputFolder, onRequestMediaPermissions = onRequestMediaPermissions) }
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
                            items(urlsList.size) { index ->
                                val url = urlsList[index]
                                val activeIndex = state.playlistProgressText.substringBefore("/").toIntOrNull()?.let { it - 1 } ?: 0
                                val isActive = state.isRunning && activeIndex == index
                                
                                Row(
                                    modifier = Modifier
                                        .fillMaxWidth()
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
                                        .padding(horizontal = AppSpacing.sm, vertical = AppSpacing.sm),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.SpaceBetween
                                ) {
                                    Row(
                                        modifier = Modifier.weight(1f),
                                        verticalAlignment = Alignment.CenterVertically,
                                        horizontalArrangement = Arrangement.spacedBy(AppSpacing.xs)
                                    ) {
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
                                val formatter = java.text.SimpleDateFormat("dd/MM/yyyy HH:mm", java.util.Locale.getDefault())
                                val recordDate: java.util.Date = java.util.Date(record.downloadedAt)
                                val dateStr = formatter.format(recordDate)
                                
                                Card(
                                    modifier = Modifier.fillMaxWidth(),
                                    shape = RoundedCornerShape(AppRadius.md),
                                    border = BorderStroke(1.dp, MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.2f)),
                                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.5f))
                                ) {
                                    Column(modifier = Modifier.padding(AppSpacing.md), verticalArrangement = Arrangement.spacedBy(4.dp)) {
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
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(min = AppSpacing.lg * 7 + AppSpacing.sm)
                        .background(
                            color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.25f),
                            shape = RoundedCornerShape(AppRadius.md),
                        )
                        .border(
                            1.dp,
                            MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.2f),
                            RoundedCornerShape(AppRadius.md)
                        )
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
            val tabs = listOf("tab_codecs", "tab_limits", "tab_flags")
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
                    Text(
                        text = Translations.get(state.statusLabel(), lang),
                        style = MaterialTheme.typography.titleMedium,
                        color = if (state.errorText != null) {
                            MaterialTheme.colorScheme.error
                        } else {
                            MaterialTheme.colorScheme.primary
                        },
                    )
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
                LinearProgressIndicator(
                    progress = { progress },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(6.dp),
                    color = AccentCyan,
                    trackColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
                )
            }
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

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun OptionPicker(
    label: String,
    selected: String,
    options: List<String>,
    enabled: Boolean = true,
    onSelect: (String) -> Unit,
) {
    var showBottomSheet by remember { mutableStateOf(false) }
    val haptic = LocalHapticFeedback.current

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
                        showBottomSheet = true
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

            if (showBottomSheet && enabled) {
                ModalBottomSheet(
                    onDismissRequest = { showBottomSheet = false },
                    containerColor = MaterialTheme.colorScheme.background.copy(alpha = 0.95f)
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .navigationBarsPadding()
                            .padding(bottom = AppSpacing.lg)
                    ) {
                        Text(
                            text = label,
                            style = MaterialTheme.typography.titleMedium,
                            color = MaterialTheme.colorScheme.primary,
                            modifier = Modifier.padding(horizontal = AppSpacing.md, vertical = AppSpacing.sm)
                        )
                        HorizontalDivider(color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f))
                        
                        LazyColumn {
                            items(options.size) { index ->
                                val option = options[index]
                                Row(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .clickable {
                                            haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                            onSelect(option)
                                            showBottomSheet = false
                                        }
                                        .padding(horizontal = AppSpacing.md, vertical = AppSpacing.md),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Text(
                                        text = option,
                                        style = MaterialTheme.typography.bodyLarge,
                                        color = if (option == selected) MaterialTheme.colorScheme.primary 
                                                else MaterialTheme.colorScheme.onSurface
                                    )
                                }
                            }
                        }
                    }
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
    try {
        val normalized = outputDir.replace('\\', '/')
        val isDownloadDir = normalized.contains("/Download", ignoreCase = true)
        
        val uri = if (isDownloadDir) {
            android.net.Uri.parse("content://com.android.externalstorage.documents/document/primary%3ADownload")
        } else {
            android.net.Uri.parse("content://com.android.externalstorage.documents/document/primary%3ADocuments")
        }
        
        val intent = android.content.Intent(android.content.Intent.ACTION_VIEW).apply {
            setDataAndType(uri, "vnd.android.document/directory")
            flags = android.content.Intent.FLAG_ACTIVITY_NEW_TASK or android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION
        }
        context.startActivity(intent)
    } catch (e: Exception) {
        try {
            val intent = android.content.Intent(android.content.Intent.ACTION_VIEW).apply {
                setDataAndType(android.net.Uri.parse("content://com.android.providers.downloads.documents/document/downloads"), "vnd.android.document/directory")
                flags = android.content.Intent.FLAG_ACTIVITY_NEW_TASK
            }
            context.startActivity(intent)
        } catch (e2: Exception) {
            try {
                val intent = android.content.Intent(android.content.Intent.ACTION_VIEW).apply {
                    setDataAndType(android.net.Uri.parse("content://media/external/file"), "vnd.android.document/directory")
                    flags = android.content.Intent.FLAG_ACTIVITY_NEW_TASK
                }
                context.startActivity(intent)
            } catch (e3: Exception) {
                try {
                    val intent = android.content.Intent(android.content.Intent.ACTION_GET_CONTENT).apply {
                        type = "*/*"
                        flags = android.content.Intent.FLAG_ACTIVITY_NEW_TASK
                    }
                    context.startActivity(intent)
                } catch (e4: Exception) {
                    android.widget.Toast.makeText(context, "Klasor acilamadi", android.widget.Toast.LENGTH_LONG).show()
                }
            }
        }
    }
}
