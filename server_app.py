# server_app.py
"""
yt-dlp Downloader Pro - FastAPI Backend Sidecar Entry Point
Imports uvicorn and runs the main server application.
"""
import sys
import uvicorn
from core.env import refresh_path_env

# 1. Refresh paths to ensure ffmpeg and yt-dlp runtimes are in PATH
refresh_path_env()

if __name__ == "__main__":
    # 2. Boot up server on localhost:8765
    uvicorn.run("server.main:app", host="127.0.0.1", port=8765, log_level="info", workers=1)
