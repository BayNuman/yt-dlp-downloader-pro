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

