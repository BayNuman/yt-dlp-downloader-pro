package com.salih.ytdownloader.ui.theme

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
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    val colors = if (darkTheme) DarkColors else LightColors

    MaterialTheme(
        colorScheme = colors,
        typography = AppTypography,
        content = content,
    )
}

