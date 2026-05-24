<div align="center">

<img src="assets/screenshots/preview.gif" alt="yt-dlp Downloader Pro" width="680"/>

# yt-dlp Downloader Pro

**One-click video and music downloader — Windows & Android**

<p align="center">
  <b>🇺🇸 English</b> &nbsp;·&nbsp;
  <a href="README.tr.md">🇹🇷 Türkçe</a> &nbsp;·&nbsp;
  <a href="README.es.md">🇪🇸 Español</a>
</p>

Download videos, music, and playlists from YouTube, Vimeo, SoundCloud, and 1000+ other sites.  
Trimming, format conversion, queue management — all in one powerful application.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-0078d4?logo=windows)](https://github.com/BayNuman/yt-dlp-downloader-pro/releases)
[![Platform: Android](https://img.shields.io/badge/Platform-Android%208%2B-3ddc84?logo=android)](https://github.com/BayNuman/yt-dlp-downloader-pro/releases)
[![Android CI](https://github.com/BayNuman/yt-dlp-downloader-pro/actions/workflows/android-ci.yml/badge.svg)](https://github.com/BayNuman/yt-dlp-downloader-pro/actions/workflows/android-ci.yml)
[![Stars](https://img.shields.io/github/stars/BayNuman/yt-dlp-downloader-pro?style=social)](https://github.com/BayNuman/yt-dlp-downloader-pro/stargazers)

[**⬇️ Download Windows**](https://github.com/BayNuman/yt-dlp-downloader-pro/releases/latest/download/yt-dlp_Downloader_Pro_Setup.exe) &nbsp;·&nbsp;
[**📱 Android APK**](https://github.com/BayNuman/yt-dlp-downloader-pro/releases/latest/download/app-release.apk) &nbsp;·&nbsp;
[**🐛 Report Bug**](https://github.com/BayNuman/yt-dlp-downloader-pro/issues/new?template=bug_report.md) &nbsp;·&nbsp;
[**💡 Request Feature**](https://github.com/BayNuman/yt-dlp-downloader-pro/issues/new?template=feature_request.md)

</div>

---

## ✨ Why is it different?

There are dozens of yt-dlp frontends. This project is different because it offers:

| Feature | Other GUIs | This Application |
|---|---|---|
| Range clipping (trimming) | ❌ | ✅ Double-handle range slider |
| Chapter clipping | ❌ | ✅ One-click auto fill range |
| Multi-clip from same video | ❌ | ✅ Greedy interval merging |
| Instagram Reels / Shorts export | ❌ | ✅ 9:16 center auto-crop |
| Discord/WhatsApp size limit | ❌ | ✅ Automatic bitrate calculation |
| YouTube 403 auto fallback | ❌ | ✅ TV Client automatic retry |
| Smart format suggestion | ❌ | ✅ Automatic metadata analysis |
| Parallel queue downloads | ❌ in most | ✅ ThreadPoolExecutor |

---

## ⬇️ Installation

> You do not need to install Python, ffmpeg, or use a terminal. Everything is packaged and ready to run.

| Platform | Package | Download |
|---|---|---|
| 🖥️ Windows | Installer (.exe) — Recommended | [📥 Download Setup](https://github.com/BayNuman/yt-dlp-downloader-pro/releases/latest/download/yt-dlp_Downloader_Pro_Setup.exe) |
| 🖥️ Windows | Portable (.exe) — No Install | [📥 Download Portable](https://github.com/BayNuman/yt-dlp-downloader-pro/releases/latest/download/yt-dlp.Downloader.Pro.exe) |
| 📱 Android | APK (Android 8.0+) | [📥 Download APK](https://github.com/BayNuman/yt-dlp-downloader-pro/releases/latest/download/app-release.apk) |

**Windows SmartScreen Warning:** If you get a SmartScreen alert, click "More Info" → "Run Anyway". The application is completely open source; you can review the codebase yourself.

**Android Installation:** Go to Settings → Apps → Allow installation from unknown sources → Tap the downloaded APK to install.

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

## 🎯 Features

### ✂️ Clip Engine — Unique to this App

Download only the part of the video you want. Extract a 30-second highlight from a 30-minute video in seconds.

- **Double-handle slider** — drag the left and right handles to select start/end times.
- **Chapter support** — clicking a video chapter automatically fills the range fields.
- **Multi-clip download** — select multiple time ranges from the same URL and queue them all at once.
- **Accurate/Fast cuts** — supports both keyframe snap (instant) or millisecond accuracy (local re-encoding).
- **Hybrid strategy** — optimizes downloads using stream seeking if you select less than 15% of the video, and buffered downloads + local trims for larger selections.

### 🎨 Export Profiles

| Profile | Output |
|---|---|
| Instagram Reels (max 90s) | Center crop to 9:16 vertical MP4 |
| YouTube Shorts (max 60s) | Center crop to 9:16 vertical MP4 |
| Discord (max 25MB) | Automatically calculates target video bitrate |
| WhatsApp (max 16MB) | Automatically calculates target video bitrate |
| Meme/GIF Creator | 15fps, 480px width, high-quality palette optimizer |
| Voice Note / Audiobook | Mono channel, 48kbps speech optimized M4A |

### 📋 Queue Management

- Parallel downloads using Python's `ThreadPoolExecutor` (configurable `max_workers`).
- Persistent download history (SQLite) — re-download with a single click.
- Saved custom templates (e.g. Podcast MP3, 4K Archive).
- Configuration options: playlist range, bandwidth speed limits, concurrent fragments.

### 🔧 Advanced Capabilities

- **SponsorBlock** — automatically skip sponsor segments.
- **Cookie Support** — load cookies from a text file or import them from browsers (Chrome, Edge, Firefox, etc.).
- **Auto-fallback 403** — automatically switches client to TV interface on HTTP 403 signature errors.
- Metadata embedding, high-res thumbnail downscaling, and subtitles downloading.
- **Smart Suggester** — profiles videos by dimensions, length, and tags to recommend vertical crop, standard MP4, or audiobook MP3.
- Extra yt-dlp parameter fields for full CLI command flexibility.

### 🌍 Platform Overview

| Feature | Windows | Android |
|---|---|---|
| Dark / Light Theme | ✅ | ✅ |
| Turkish / English / Spanish | ✅ | ✅ |
| Background Downloads | ✅ | ✅ ForegroundService |
| Direct Share Menu Import | — | ✅ Share Intent |
| Notifications | ✅ Sliding Toast | ✅ Native Notifications |

---

## 🚀 Quick Start

### Windows

```
1. Download the "yt-dlp_Downloader_Pro_Setup.exe" installer.
2. Double-click it and click "Next" → "Install" (takes ~30 seconds).
3. Open the desktop shortcut, paste a URL, and click Download!
```

### Android

```
1. Download the "app-release.apk" file to your phone.
2. Grant "Install from Unknown Sources" permission.
3. Open the APK file, approve permissions, and start downloading!
```

---

## 🛠️ Build from Source

### Requirements (Windows)

- Python 3.10+
- Inno Setup 6 (for packaging the setup installer)

```bash
git clone https://github.com/BayNuman/yt-dlp-downloader-pro.git
cd yt-dlp-downloader-pro

pip install customtkinter yt-dlp pillow requests pyinstaller tkinterdnd2

# Run the app
python app.py

# Package the standalone EXE + setup installer
python build_full_distribution.py
```

The build script automatically downloads bundled dependencies (ffmpeg.exe, ffprobe.exe), wraps them using PyInstaller, and compiles the Inno Setup installer.

### Requirements (Android)

- Android Studio Hedgehog (2023.1.1)+
- JDK 17+
- Android SDK API 26+

```bash
cd android
./gradlew assembleRelease
# Output will be generated at: android/app/build/outputs/apk/release/app-release.apk
```

---

## 🏗️ Architecture

```
yt-dlp-downloader-pro/
│
├── 🖥️  Desktop (Python + CustomTkinter)
│   ├── app.py                    # Bootstrap entrypoint - only calls main()
│   ├── core/
│   │   ├── app_state.py          # State engine (AppState, DownloadTask, TaskStatus enum)
│   │   ├── command_builder.py    # Pure functions - generates yt-dlp CLI arguments
│   │   ├── downloader.py         # ThreadPoolExecutor concurrent queue runner
│   │   ├── clip.py               # LeetCode 56 Greedy Interval Merging + seek selector
│   │   ├── merger.py             # FFmpeg Concat Demuxer lossless joining
│   │   ├── profiles.py           # Polymorphic ffmpeg output conversion profiles
│   │   ├── suggester.py          # Heuristic suggestion engine
│   │   ├── history.py            # SQLite db schema + asynchronous DatabaseWriter queue
│   │   ├── presets.py            # JSON download presets loading/saving
│   │   ├── updater.py            # PyPI package version checker
│   │   └── env.py                # Live Windows registry path reloader
│   └── ui/
│       ├── theme.py              # HSL Colors palettes + translations
│       ├── main_window.py        # Central GUI Layout & event dispatcher
│       └── panels/               # Modular panel frames (Queue, Advanced, Preview)
│
└── 📱  Android (Kotlin + Jetpack Compose)
    └── android/app/src/main/
        ├── MainActivity.kt
        ├── DownloadService.kt    # Foreground service wrapper
        └── ui/
            ├── DownloaderScreen.kt
            ├── DownloaderViewModel.kt
            └── theme/Translations.kt
```

**Key Architectural Choices:**
- Decoupled `core/` architecture — maintains no GUI states, easily portable.
- `command_builder.py` contains only pure functions with no `self` references, ideal for testing.
- Singleton `DatabaseWriter` writes sequentially via a thread-safe asynchronous queue.
- Smart `--load-info-json` logic loads metadata once and passes it via arguments, preventing double-scraping.

---

## 🌍 Supported Platforms

Powered by yt-dlp, this application supports over **1000+ sites**:

YouTube • YouTube Music • Vimeo • SoundCloud • Twitter/X • Instagram • TikTok • Facebook • Dailymotion • Twitch • Reddit • Bandcamp • and more...

→ [Full list of supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)

---

## 🗺️ Roadmap

- [ ] macOS desktop support
- [ ] Android range clip engine (slider selection + conversion profiles)
- [ ] Browser extension (Chrome/Firefox one-click integration)
- [ ] Scheduled downloads (e.g., start at 2:00 AM)
- [ ] Plex / Jellyfin integration (auto-tagging media library directories)
- [ ] Thumbnail filmstrip slider

Have a suggestion? [Open a feature request!](https://github.com/BayNuman/yt-dlp-downloader-pro/issues/new?template=feature_request.md)

---

## 🤝 Contributing

Contributions are welcome — bug fixes, translations, or new profile ideas!

1. Read our [Contributing Guide](CONTRIBUTING.md)
2. Browse our [Open Issues](https://github.com/BayNuman/yt-dlp-downloader-pro/issues)
3. Fork the repository, create your branch, and open a Pull Request!

---

## ⚖️ Legal Disclaimer

This software is a GUI client interface for [yt-dlp](https://github.com/yt-dlp/yt-dlp). Users are solely responsible for complying with the terms of service of the respective platforms they download media from. Please download only materials you have legal rights to access.

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.

---

<div align="center">

Made with ❤️ by [BayNuman](https://github.com/BayNuman)

If you find this project useful, don't forget to give it a ⭐ to help others discover it!

</div>
