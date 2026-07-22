# server_app.py
"""
yt-dlp Downloader Pro - FastAPI Backend Sidecar Entry Point & CLI Dispatcher
"""
import sys
import uvicorn
from core.env import refresh_path_env

# 1. Refresh paths to ensure ffmpeg and yt-dlp runtimes are in PATH
refresh_path_env()

if __name__ == "__main__":
    # 2. Check if invoked as CLI wrapper (e.g. server-sidecar.exe -m yt_dlp ...)
    if len(sys.argv) > 2 and sys.argv[1] == "-m" and sys.argv[2] == "yt_dlp":
        import yt_dlp
        sys.argv = [sys.argv[0]] + sys.argv[3:]
        sys.exit(yt_dlp.main())
    else:
        # 3. Boot up FastAPI server on localhost:8765
        uvicorn.run("server.main:app", host="127.0.0.1", port=8765, log_level="info", workers=1)

