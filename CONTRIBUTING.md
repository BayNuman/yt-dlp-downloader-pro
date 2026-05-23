# Contributing to yt-dlp Downloader Pro

Thank you for considering contributing! 🎉 Every improvement, bug report, and feature idea helps make this project better for everyone.

---

## 📋 Table of Contents
- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Commit Message Convention](#commit-message-convention)

---

## Code of Conduct

By participating, you agree to be respectful and constructive. Harassment of any kind will not be tolerated.

---

## How Can I Contribute?

### 🐛 Reporting Bugs
- Check [existing issues](../../issues) first to avoid duplicates.
- Use the **Bug Report** template when opening a new issue.
- Include OS version, app version, and steps to reproduce.

### 💡 Suggesting Features
- Open a **Feature Request** issue with the template provided.
- Explain the use case — why would this help users?

### 🌍 Adding Translations
The app supports multiple languages via `Translations.kt` (Android) and the settings panel (Desktop).
1. Fork the repository.
2. Add your language code and translations to `Translations.kt`.
3. Test that all UI strings display correctly.
4. Submit a PR with the title: `i18n: Add [Language] translation`.

### 💻 Code Contributions
See [Development Setup](#development-setup) below.

---

## Development Setup

### Desktop (Python + CustomTkinter)

**Requirements:**
- Python 3.10+
- pip

```bash
# 1. Clone the repository
git clone https://github.com/BayNuman/yt-dlp-downloader-pro.git
cd yt-dlp-downloader-pro

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install customtkinter yt-dlp pillow requests

# 4. Run the app
python app.py
```

### Android (Kotlin + Jetpack Compose)

**Requirements:**
- Android Studio Hedgehog or newer
- JDK 17+
- Android SDK 26+

```bash
# 1. Open the /android folder in Android Studio
# 2. Wait for Gradle sync to complete
# 3. Connect a device or start an emulator
# 4. Run the app via the Run button or:
cd android
./gradlew installDebug
```

### Building a Release

```bash
# Desktop installer
python build_full_distribution.py

# Android debug APK
cd android && ./gradlew assembleDebug
```

---

## Pull Request Process

1. Fork the repo and create a branch: `git checkout -b feature/your-feature-name`
2. Make your changes with clear, focused commits.
3. Test your changes on your target platform.
4. Update `CHANGELOG.md` under `[Unreleased]`.
5. Open a PR against the `main` branch using the PR template.
6. A maintainer will review and merge within 5 business days.

---

## Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add subtitle download support
fix: resolve crash on Android 8 when opening folder
i18n: add French translation
docs: update Quick Start section in README
chore: upgrade yt-dlp to 2025.x.x
```

| Prefix | Use for |
|--------|---------|
| `feat` | New features |
| `fix` | Bug fixes |
| `i18n` | Translations |
| `docs` | Documentation only |
| `chore` | Build, deps, refactor |
| `style` | Formatting, UI tweaks |
