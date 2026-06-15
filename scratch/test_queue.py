import tkinter as tk
import customtkinter as ctk
import time
import sys
from core.app_state import AppState
from ui.main_window import MainWindow

# Set up Tk environment
ctk.set_appearance_mode("Dark")
state = AppState()
root = MainWindow(state)

# Paste a valid URL into the URL field
url = "https://www.youtube.com/watch?v=PnqRoGiSlvk"
root.url_panel.set_url(url)
print("Pasted URL. app_state.url =", state.url)

# Trigger metadata fetch manually (so it updates in-state if needed, though _add_to_queue shouldn't require it)
root._trigger_metadata_fetch()
# Give it a second to fetch in the background
time.sleep(2)

print("current_video_info:", state.current_video_info)
print("queue_list length before:", len(state.queue_list))

# Simulate clicking "İndirmeleri Başlat" (Start Downloads)
try:
    root._start_download()
    print("Called _start_download successfully.")
    print("queue_list length after:", len(state.queue_list))
    if len(state.queue_list) > 0:
        task = state.queue_list[0]
        print("Task 0 title:", task.title)
        print("Task 0 status:", task.status)
        print("Task 0 status_code:", task.status_code)
    else:
        print("Queue is still empty!")
except Exception as e:
    import traceback
    print("Error calling _start_download:")
    traceback.print_exc()

root.destroy()
sys.exit(0)
