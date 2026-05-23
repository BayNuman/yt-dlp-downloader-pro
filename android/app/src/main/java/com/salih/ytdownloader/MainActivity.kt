package com.salih.ytdownloader

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.platform.LocalContext
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.salih.ytdownloader.ui.DownloaderScreen
import com.salih.ytdownloader.ui.DownloaderViewModel
import com.salih.ytdownloader.ui.theme.YtDownloaderTheme

class MainActivity : ComponentActivity() {
    private var downloaderViewModelRef: DownloaderViewModel? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContent {
            val downloaderViewModel: DownloaderViewModel = viewModel()
            downloaderViewModelRef = downloaderViewModel
            val state by downloaderViewModel.uiState.collectAsStateWithLifecycle()

            YtDownloaderTheme(darkTheme = state.isDarkTheme) {
                val context = LocalContext.current

                val permissionsLauncher = rememberLauncherForActivityResult(
                    contract = ActivityResultContracts.RequestMultiplePermissions(),
                ) { result ->
                    val granted = result.values.all { it }
                    downloaderViewModel.updateMediaPermissionsStatus(granted)
                }

                val cookiesFileLauncher = rememberLauncherForActivityResult(
                    contract = ActivityResultContracts.GetContent(),
                ) { uri ->
                    downloaderViewModel.importCookiesFromUri(uri)
                }

                val ytDlpFileLauncher = rememberLauncherForActivityResult(
                    contract = ActivityResultContracts.GetContent(),
                ) { uri ->
                    downloaderViewModel.importYtDlpBinaryFromUri(uri)
                }

                val folderLauncher = rememberLauncherForActivityResult(
                    contract = ActivityResultContracts.OpenDocumentTree(),
                ) { uri ->
                    downloaderViewModel.updateOutputDirFromTreeUri(uri)
                }

                LaunchedEffect(Unit) {
                    val hasPerms = hasMediaPermissions(context)
                    downloaderViewModel.updateMediaPermissionsStatus(hasPerms)
                    downloaderViewModel.setIncomingSharedText(extractSharedText(intent))
                    if (!hasPerms) {
                        val permissions = requiredMediaPermissions()
                        if (permissions.isNotEmpty()) {
                            permissionsLauncher.launch(permissions)
                        }
                    }
                }

                DownloaderScreen(
                    state = state,
                    viewModel = downloaderViewModel,
                    onPickCookiesFile = { cookiesFileLauncher.launch("*/*") },
                    onPickYtDlpBinary = { ytDlpFileLauncher.launch("*/*") },
                    onPickOutputFolder = { folderLauncher.launch(null) },
                    onRequestMediaPermissions = {
                        val permissions = requiredMediaPermissions()
                        if (permissions.isEmpty()) {
                            downloaderViewModel.updateMediaPermissionsStatus(true)
                        } else {
                            permissionsLauncher.launch(permissions)
                        }
                    },
                )
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        downloaderViewModelRef?.setIncomingSharedText(extractSharedText(intent))
    }
}

private fun requiredMediaPermissions(): Array<String> {
    val list = mutableListOf<String>()
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        list.add(Manifest.permission.READ_MEDIA_VIDEO)
        list.add(Manifest.permission.READ_MEDIA_AUDIO)
        // Add notification permission on Android 13+ to show background download alerts
        list.add(Manifest.permission.POST_NOTIFICATIONS)
    } else {
        list.add(Manifest.permission.READ_EXTERNAL_STORAGE)
    }
    return list.toTypedArray()
}

private fun hasMediaPermissions(context: Context): Boolean {
    val permissions = requiredMediaPermissions()
    if (permissions.isEmpty()) {
        return true
    }
    return permissions.all { permission ->
        ContextCompat.checkSelfPermission(context, permission) == PackageManager.PERMISSION_GRANTED
    }
}

private fun extractSharedText(intent: Intent?): String? {
    if (intent == null) {
        return null
    }
    if (intent.action != Intent.ACTION_SEND) {
        return null
    }
    if (intent.type != "text/plain") {
        return null
    }
    val rawText = intent.getStringExtra(Intent.EXTRA_TEXT) ?: return null
    // Extract pure HTTP/HTTPS URL from any complex shared description texts
    val regex = Regex("""https?://[\w./\-?=&%+#]+""")
    val match = regex.find(rawText)
    return match?.value ?: rawText
}
