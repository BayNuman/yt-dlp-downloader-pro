import tkinter as tk
import customtkinter as ctk
from core.app_state import AppState
from ui.panels.url_panel import UrlPanel

# Initialize custom tkinter and state
root = ctk.CTk()
state = AppState()
panel = UrlPanel(root, state, lambda: None)
panel.pack()

# Simulate toggle batch mode
print("is_batch_mode initially:", state.is_batch_mode)
panel.batch_mode_var.set(True)
try:
    panel._toggle_batch_mode()
    print("Toggle to True succeeded. is_batch_mode:", state.is_batch_mode)
    print("url_entry in_state:", panel.url_entry.winfo_manager())
    print("url_textbox in_state:", panel.url_textbox.winfo_manager())
except Exception as e:
    print("Toggle to True failed:", e)

panel.batch_mode_var.set(False)
try:
    panel._toggle_batch_mode()
    print("Toggle to False succeeded. is_batch_mode:", state.is_batch_mode)
except Exception as e:
    print("Toggle to False failed:", e)
