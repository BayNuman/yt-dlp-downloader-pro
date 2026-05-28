# app.py
"""
yt-dlp Downloader Pro - Desktop Entry Point
A zero-config, premium glassmorphic media downloader powered by yt-dlp + ffmpeg.
"""

from core.env import refresh_path_env
# Refresh path environment variables on startup before importing anything else to pick up runtime updates like Deno
refresh_path_env()

import sys
if len(sys.argv) > 2 and sys.argv[1] == "-m" and sys.argv[2] == "yt_dlp":
    import yt_dlp
    sys.exit(yt_dlp.main(sys.argv[3:]))

from core.app_state import AppState
from ui.main_window import MainWindow

from core.logging_setup import setup_logging

def purge_scratch_directory():
    """
    Deterministik olarak önceki oturumlardan kalan tüm geçici 
    dosyaları başlangıç anında temizler.
    """
    import shutil
    from pathlib import Path
    scratch_dir = Path.home() / ".yt-downloader-scratch"
    
    if scratch_dir.exists():
        try:
            shutil.rmtree(scratch_dir, ignore_errors=True)
        except Exception as e:
            import logging
            logging.error(f"[Garbage Collection] I/O Error: {e}")
            
    # Temiz bir başlangıç için klasörü yeniden oluştur
    scratch_dir.mkdir(parents=True, exist_ok=True)

def main() -> None:
    # 0. Initialize central logging system
    setup_logging()
    
    # 1. Deterministik başlangıç çöp toplama (Garbage Collection)
    purge_scratch_directory()
    
    # 2. Initialize central application state configuration
    state = AppState()
    
    # 2. Boot up the main graphical window layout orchestrator
    app = MainWindow(state)
    
    # 3. Fire up the Tkinter main event thread loop
    app.mainloop()

if __name__ == "__main__":
    main()
