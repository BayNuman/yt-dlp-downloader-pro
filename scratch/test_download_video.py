# scratch/test_download_video.py
import sys
import os
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

import time
import queue
from pathlib import Path

# Add root folder to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.app_state import AppState, DownloadTask, TaskStatus
from core.downloader import run_queue_executor

def main():
    print("[*] Initializing test download...")
    
    exe_path = Path(__file__).parent.parent / "dist" / "yt-dlp Downloader Pro.exe"
    if exe_path.exists():
        print(f"[+] Compiled executable found: {exe_path.absolute()}")
        print("[*] Monkeypatching sys.executable to test the standalone compiled binary...")
        sys.executable = str(exe_path.resolve())
    else:
        print("[*] Compiled executable not found, testing in development environment...")

    state = AppState()
    
    # Configure test output directory
    output_dir = Path(__file__).parent.parent / "scratch" / "downloads"
    output_dir.mkdir(parents=True, exist_ok=True)
    state.preferences.output_dir = str(output_dir)
    state.preferences.max_workers = 1
    
    print("[*] Output directory configured:", state.preferences.output_dir)
    
    # Create the test download task
    url = "https://www.youtube.com/watch?v=5Nrq1tJiGiA"
    task = DownloadTask(
        id="test_task_123",
        url=url,
        title="Test YouTube Video",
        duration="00:00",
        preset="Custom",
        status="Bekliyor",
        status_code=TaskStatus.PENDING,
        mode="Video",
        video_profile="Full HD (1080p)",
        video_limit="1080",
        archive=False
    )
    
    state.queue_list.append(task)
    print("[*] Task appended to queue list. Queue size:", len(state.queue_list))
    
    # UI queue for receiving notifications
    ui_queue = queue.Queue()
    cancel_event = task.cancel_event
    
    print("[*] Starting queue executor...")
    # Spawn the executor
    run_queue_executor(state, ui_queue, cancel_event)
    
    print("[*] Executor finished. Processing UI queue messages...")
    
    # Drain UI Queue and print messages
    logs = []
    status = None
    percent = 0.0
    while not ui_queue.empty():
        msg_type, payload = ui_queue.get()
        if msg_type == "log":
            logs.append(payload)
            print(f"[Log] {payload.strip()}")
        elif msg_type == "status":
            status = payload
            print(f"[Status] {payload}")
        elif msg_type == "stats":
            percent = payload.get("percent", percent)
            print(f"[Stats] {payload}")
        elif msg_type == "toast_success":
            print(f"[Success] {payload}")
        elif msg_type == "toast_error":
            print(f"[Error] {payload}")
            
    print("\n" + "="*50)
    print("TEST RESULTS:")
    print("="*50)
    print("Task Status Code:", task.status_code)
    print("Task Status Text:", task.status)
    print("Task Final Percent:", task.percent)
    print("Task File Path:", task.file_path)
    
    # Check if file exists on disk
    downloaded_file = Path(task.file_path) if task.file_path else None
    file_exists = downloaded_file and downloaded_file.exists()
    print("File Exists on Disk:", file_exists)
    if file_exists:
        print("Downloaded File Path:", downloaded_file.absolute())
        print("Downloaded File Size:", downloaded_file.stat().st_size, "bytes")
        print("[+] SUCCESS: The video was successfully downloaded!")
        sys.exit(0)
    else:
        print("[-] FAILURE: The video file does not exist on disk!")
        sys.exit(1)

if __name__ == "__main__":
    main()
