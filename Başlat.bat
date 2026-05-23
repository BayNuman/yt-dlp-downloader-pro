@echo off
:: yt-dlp Downloader Pro - Background Quiet Launcher
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
    echo [HATA] .venv sanal ortamı veya pythonw.exe bulunamadı!
    echo Lütfen önce bağımlılıkların kurulu olduğundan emin olun.
    pause
    exit /b
)
start "" ".venv\Scripts\pythonw.exe" app.py
