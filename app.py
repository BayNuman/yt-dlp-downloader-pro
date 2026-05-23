# app.py
"""
yt-dlp Downloader Pro - Desktop Entry Point
A zero-config, premium glassmorphic media downloader powered by yt-dlp + ffmpeg.
"""

from core.app_state import AppState
from ui.main_window import MainWindow

def main() -> None:
    # 1. Initialize central application state configuration
    state = AppState()
    
    # 2. Boot up the main graphical window layout orchestrator
    app = MainWindow(state)
    
    # 3. Fire up the Tkinter main event thread loop
    app.mainloop()

if __name__ == "__main__":
    main()
