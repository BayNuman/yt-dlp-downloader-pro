# yt-dlp Downloader Pro

<p align="center">
  <b>🇺🇸 English</b> &nbsp;·&nbsp;
  <a href="README.tr.md">🇹🇷 Türkçe</a> &nbsp;·&nbsp;
  <a href="README.es.md">🇪🇸 Español</a>
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-0078d4?logo=windows)](https://github.com/BayNuman/yt-dlp-downloader-pro/releases)
[![Platform: Android](https://img.shields.io/badge/Platform-Android%208%2B-3ddc84?logo=android)](https://github.com/BayNuman/yt-dlp-downloader-pro/releases)
[![Android CI](https://github.com/BayNuman/yt-dlp-downloader-pro/actions/workflows/android-ci.yml/badge.svg)](https://github.com/BayNuman/yt-dlp-downloader-pro/actions/workflows/android-ci.yml)
[![Stars](https://img.shields.io/github/stars/BayNuman/yt-dlp-downloader-pro?style=social)](https://github.com/BayNuman/yt-dlp-downloader-pro/stargazers)

> A premium, high-performance video and audio downloader with a semi-translucent glassmorphic interface. It supports time-range clipping, SponsorBlock integration, parallel downloads queue, smart directory structures, and a 9:16 vertical crop generator for Instagram Reels & YouTube Shorts. Powered by `yt-dlp` and `FFmpeg`.

<div align="center">
  <img src="assets/screenshots/preview.gif" alt="yt-dlp Downloader Pro Preview" width="680"/>
</div>

---

## 📥 Fast Downloads

| Platform | Type | Release Package |
| :--- | :--- | :--- |
| **🖥️ Windows** | Installer (Recommended) | [📥 Download Setup.exe](https://github.com/BayNuman/yt-dlp-downloader-pro/releases/latest/download/yt-dlp_Downloader_Pro_Setup.exe) |
| **🖥️ Windows** | Portable | [📥 Download Portable.exe](https://github.com/BayNuman/yt-dlp-downloader-pro/releases/latest/download/yt-dlp.Downloader.Pro.exe) |
| **📱 Android** | APK (Android 8.0+) | [📥 Download App.apk](https://github.com/BayNuman/yt-dlp-downloader-pro/releases/latest/download/app-release.apk) |

---

## 🚀 Key Features

| Feature | Other Frontends | yt-dlp Downloader Pro |
| :--- | :--- | :--- |
| **Time-Range Clipping** | ❌ (Full download only) | ✅ Dual-handle interactive range slider |
| **Smart Multi-Clip** | ❌ | ✅ LeetCode 56 Greedy Interval Merging |
| **Crop to Reels/Shorts** | ❌ | ✅ 9:16 smart center-crop format profile |
| **SponsorBlock** | ❌ | ✅ Auto-skip / cut sponsor segments |
| **403 Client Fallback** | ❌ | ✅ TV Client automatic fallback signature bypass |
| **Smart Audio Waveform** | ❌ | ✅ 1.5s envelope waveform preview |
| **Parallel Queue** | ❌ in most | ✅ High-performance thread-safe queue |

---

## 📦 Installation & Setup

### Platform Prebuilt Binaries

#### 🖥️ Windows Setup
1. Download [yt-dlp_Downloader_Pro_Setup.exe](https://github.com/BayNuman/yt-dlp-downloader-pro/releases/latest/download/yt-dlp_Downloader_Pro_Setup.exe).
2. Double-click the installer and complete the setup wizard (takes ~30 seconds).
3. *SmartScreen Note:* If Windows SmartScreen blocks launch, click **More Info** → **Run Anyway**.

#### 📱 Android Setup
1. Download [app-release.apk](https://github.com/BayNuman/yt-dlp-downloader-pro/releases/latest/download/app-release.apk).
2. Grant **Install from Unknown Sources** in your Android security settings.
3. Open the APK file and tap **Install**.

---

## 🛠️ Building From Source

### Desktop Requirements
- **Python** (v3.10 or higher)
- **FFmpeg** and **FFprobe** (will be automatically downloaded by the builder script if missing)
- **Inno Setup 6** (required only if packaging the Windows Setup Installer)

### Desktop Run & Package Commands
1. **Clone the repository:**
   ```bash
   git clone https://github.com/BayNuman/yt-dlp-downloader-pro.git
   cd yt-dlp-downloader-pro
   ```
2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Launch the application:**
   ```bash
   python app.py
   ```
4. **Compile the standalone EXE and Windows Installer:**
   ```bash
   python build_full_distribution.py
   ```

### Android Requirements & Build
- **Android Studio** Hedgehog (2023.1.1) or higher
- **JDK 17**
- **Android SDK API 26+**

```bash
cd android
./gradlew assembleRelease
```
*The release APK will be generated at: `android/app/build/outputs/apk/release/app-release.apk`*

---

## 🛠️ Usage Examples

### Visual GUI Mode
Simply run the application or double-click the shortcut. Paste the URL, choose your format profile (e.g. *Best Quality*, *Full HD 1080p*, *Instagram Reels*), select clipping ranges if needed, and hit **Start Downloads**.

### Headless CLI Mode (Windows Compiled Binary)
The compiled standalone executable intercepts arguments using a custom CLI bootloader. If run with `-m yt_dlp`, it acts as a headless command-line interface:
```bash
"yt-dlp Downloader Pro.exe" -m yt_dlp "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --format bestvideo+bestaudio
```

### Programmatic Code Hook (Python)
Developers can import modules from `core/` directly. For example, to generate raw command arguments programmatically:
```python
from core.command_builder import build_ytdlp_args
from core.app_state import DownloadTask

# Create state representation of a download task
task = DownloadTask(
    url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    preset="1080p",
    output_dir="downloads"
)

# Generate pure yt-dlp CLI arguments
args = build_ytdlp_args(task)
print("yt-dlp arguments:", args)
```

---

## 📸 Screenshots

<table>
<tr>
<td><img src="assets/screenshots/desktop_dark_main.png" alt="Windows — Dark Mode" width="340"/></td>
<td><img src="assets/screenshots/desktop_light_main.png" alt="Windows — Light Mode" width="340"/></td>
</tr>
<tr>
<td align="center"><em>Windows — Dark Theme</em></td>
<td align="center"><em>Windows — Light Theme</em></td>
</tr>
</table>

<table>
<tr>
<td><img src="assets/screenshots/android_dark.jpg" alt="Android — Download" width="160"/></td>
<td><img src="assets/screenshots/android_queue.png" alt="Android — Queue" width="160"/></td>
<td><img src="assets/screenshots/android_history.png" alt="Android — History" width="160"/></td>
<td><img src="assets/screenshots/android_settings.png" alt="Android — Settings" width="160"/></td>
</tr>
<tr>
<td align="center"><em>Download</em></td>
<td align="center"><em>Queue</em></td>
<td align="center"><em>History</em></td>
<td align="center"><em>Settings</em></td>
</tr>
</table>

---

## 🏗️ Core Architecture

```text
yt-dlp-downloader-pro/
│
├── 🖥️  Desktop (Python + CustomTkinter)
│   ├── app.py                    # Bootstrap entrypoint - only calls main()
│   ├── core/
│   │   ├── app_state.py          # Thread-safe state engine with RLock + auto locale detection
│   │   ├── command_builder.py    # Pure functions - generates yt-dlp CLI arguments
│   │   ├── downloader.py         # ThreadPoolExecutor concurrent queue runner
│   │   ├── clip.py               # LeetCode 56 Greedy Interval Merging + seek selector
│   │   ├── merger.py             # FFmpeg Concat Demuxer lossless joining
│   │   ├── profiles.py           # Polymorphic ffmpeg output conversion profiles
│   │   ├── suggester.py          # Heuristic suggestion engine
│   │   ├── history.py            # SQLite + thread-local connection cache + WAL mode
│   │   ├── presets.py            # JSON presets with in-memory cache layer
│   │   ├── updater.py            # PyPI package version checker
│   │   └── env.py                # Windows registry path reloader
│   └── ui/
│       ├── theme.py              # HSL color palettes + i18n translations (en/tr/es)
│       ├── main_window.py        # Central GUI layout with coalesced UI queue drain
│       ├── components/toast.py   # BaseToast OOP hierarchy
│       └── panels/               # Modular panels (Queue, Advanced, Preview)
│
└── 📱  Android (Kotlin + Jetpack Compose)
    └── android/app/src/main/
        ├── MainActivity.kt
        ├── service/DownloadService.kt  # Foreground service with lifecycle binding
        ├── data/
        │   ├── DownloadModels.kt       # Request/Event/Record models + JSON serialization
        │   ├── YtDlpCommandBuilder.kt  # CLI builder with clip sections optimization
        │   ├── YtDlpRunner.kt          # Regex-based stdout parser + multi-path fallback
        │   └── algorithms/ClipOptimizer.kt  # Greedy interval merging (LeetCode 56)
        └── ui/
            ├── DownloaderScreen.kt
            ├── DownloaderViewModel.kt   # Consolidated RuntimeState architecture
            └── theme/Translations.kt
```

---

## 🌍 Supported Platforms

Powered by `yt-dlp`, this application supports over **1000+ sites**:

YouTube • YouTube Music • Vimeo • SoundCloud • Twitter/X • Instagram • TikTok • Facebook • Dailymotion • Twitch • Reddit • Bandcamp • and more...

→ [Full list of supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)

---

## 🗺️ Roadmap

- [ ] macOS desktop support
- [ ] Android range clip engine (slider selection + conversion profiles)
- [ ] Browser extension (one-click integration)
- [ ] Scheduled downloads (deferred countdown timer)
- [ ] Plex / Jellyfin auto-tagging integration
- [ ] Thumbnail filmstrip slider

---

## 🤝 Contributing

Contributions are welcome!
1. Read our [Contributing Guide](CONTRIBUTING.md)
2. Fork the repository, create your feature branch, and open a Pull Request.

---

## ⚖️ Legal Disclaimer

This software is a GUI client interface for [yt-dlp](https://github.com/yt-dlp/yt-dlp). Users are solely responsible for complying with the terms of service of the respective platforms they download media from.

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 💡 Best Practices (Dos & Don'ts)

| Dos | Don'ts |
| :--- | :--- |
| **Use relative paths** (`./assets/...` or repo-relative links) for files and screenshots. | **Avoid absolute paths** (`C:/Users/name/...`) which fail on other environments. |
| **Specify the exact programming language** in code fence blocks (e.g. ` ```bash `, ` ```python `) to enable code coloring. | **Do not write unformatted blocks** or generic ` ``` ` fences. |
| **Utilize tables and emojis** to split walls of text and reduce cognitive load. | **Avoid writing generic "Works on my machine" instructions** without detailing minimum system requirements. |
| **Keep installation instructions up-to-date** and test commands locally before releasing. | **Do not leave stale setup steps** or undocumented dependencies that break Developer Experience (DX). |

---

<div align="center">

Made with ❤️ by [BayNuman](https://github.com/BayNuman)

[**🧡 Become a Patron on Patreon**](https://patreon.com/BayNuman?utm_medium=unknown&utm_source=join_link&utm_campaign=creatorshare_creator&utm_content=copyLink)

If you find this project useful, don't forget to give it a ⭐ to help others discover it!

</div>
