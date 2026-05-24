# ui/components/toast.py
import os
import sys
import subprocess
import customtkinter as ctk
import tkinter as tk
from pathlib import Path
from ui.theme import (
    THEME_BG, THEME_CARD_BG, THEME_CARD_BORDER, THEME_TEXT_PRIMARY,
    THEME_TEXT_SECONDARY, THEME_ACCENT_BLUE, THEME_ACCENT_INDIGO,
    THEME_ACCENT_RED
)

class ActionableToast(ctk.CTkToplevel):
    def __init__(self, master, title: str, file_path: str, duration_ms: int = 7000, **kwargs):
        super().__init__(master, **kwargs)
        
        self.file_path = str(Path(file_path).resolve())
        self.duration_ms = duration_ms
        
        # 1. Hide default OS window borders & decorations
        self.overrideredirect(True)
        # Keep on top of all windows
        self.attributes("-topmost", True)
        
        # Frosted glass card border container
        self.frame = ctk.CTkFrame(
            self,
            fg_color=THEME_CARD_BG,
            border_width=2,
            border_color=THEME_ACCENT_BLUE,
            corner_radius=12
        )
        self.frame.pack(fill="both", expand=True)

        # 2. UI Components Building
        self._build_ui(title)
        
        # 3. Geo Positioning & Fade Animation
        self.attributes("-alpha", 0.0) 
        self.update_idletasks() # Force geometry calculations to avoid 1x1 sol-ust bug
        self._position_toast()
        
        # Fade-in and bootstrap lifecycle
        self._fade_in()
        self.timer_id = self.after(self.duration_ms, self._fade_out)

    def _build_ui(self, title: str):
        # Header Row: Title & Close Button
        header_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=12, pady=(12, 4))
        header_frame.grid_columnconfigure(0, weight=1)
        
        lbl_title = ctk.CTkLabel(
            header_frame,
            text=title,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=THEME_TEXT_PRIMARY
        )
        lbl_title.grid(row=0, column=0, sticky="w")
        
        btn_close = ctk.CTkButton(
            header_frame,
            text="✕",
            width=20,
            height=20,
            fg_color="transparent",
            text_color=THEME_TEXT_SECONDARY,
            hover_color=THEME_ACCENT_RED,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            command=self._fade_out
        )
        btn_close.grid(row=0, column=1, sticky="e")

        # Filename Row
        file_name = os.path.basename(self.file_path)
        display_name = file_name if len(file_name) < 38 else file_name[:35] + "..."
        lbl_file = ctk.CTkLabel(
            self.frame,
            text=display_name,
            font=ctk.CTkFont(family="Segoe UI", size=11, slant="italic"),
            text_color=THEME_TEXT_SECONDARY,
            anchor="w",
            justify="left"
        )
        lbl_file.pack(fill="x", padx=12, pady=(0, 10))

        # Bottom Action Bar (3 column grid)
        btn_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=(0, 14))
        btn_frame.grid_columnconfigure((0, 1, 2), weight=1)

        btn_play = ctk.CTkButton(
            btn_frame,
            text="▶ Oynat" if ctk.get_appearance_mode() == "Dark" else "▶ Play",
            width=76,
            height=26,
            fg_color=THEME_ACCENT_INDIGO,
            text_color="#ffffff",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            command=self._action_play
        )
        btn_play.grid(row=0, column=0, padx=2)

        btn_folder = ctk.CTkButton(
            btn_frame,
            text="📂 Göster" if ctk.get_appearance_mode() == "Dark" else "📂 Show",
            width=76,
            height=26,
            fg_color=THEME_BG,
            text_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_CARD_BORDER,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            command=self._action_show_folder
        )
        btn_folder.grid(row=0, column=1, padx=2)

        btn_copy = ctk.CTkButton(
            btn_frame,
            text="📋 Kopyala" if ctk.get_appearance_mode() == "Dark" else "📋 Copy Path",
            width=88,
            height=26,
            fg_color="transparent",
            text_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_CARD_BORDER,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            command=self._action_copy_path
        )
        btn_copy.grid(row=0, column=2, padx=2)

    def _position_toast(self):
        req_width = self.winfo_reqwidth()
        req_height = self.winfo_reqheight()
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Margins to protect Taskbar overlaps
        margin_x = 24
        margin_y = 72 
        
        x = screen_width - req_width - margin_x
        y = screen_height - req_height - margin_y
        
        self.geometry(f"{req_width}x{req_height}+{x}+{y}")

    def _action_play(self):
        try:
            if sys.platform == "win32":
                os.startfile(self.file_path)
            elif sys.platform == "darwin":
                subprocess.call(["open", self.file_path])
            else:
                subprocess.call(["xdg-open", self.file_path])
            self._fade_out()
        except Exception as e:
            print(f"[Toast] Playback error: {e}")

    def _action_show_folder(self):
        try:
            if sys.platform == "win32":
                # Launch Windows Explorer and highlight the file
                subprocess.Popen(rf'explorer /select,"{self.file_path}"')
            elif sys.platform == "darwin":
                subprocess.call(["open", "-R", self.file_path])
            else:
                folder = os.path.dirname(self.file_path)
                subprocess.call(["xdg-open", folder])
            self._fade_out()
        except Exception as e:
            print(f"[Toast] Explorer open error: {e}")

    def _action_copy_path(self):
        self.clipboard_clear()
        self.clipboard_append(self.file_path)
        self.update()
        self._fade_out()

    def _fade_in(self):
        alpha = self.attributes("-alpha")
        if alpha < 1.0:
            alpha += 0.1
            self.attributes("-alpha", min(alpha, 1.0))
            self.after(20, self._fade_in)

    def _fade_out(self):
        if hasattr(self, 'timer_id') and self.timer_id:
            try:
                self.after_cancel(self.timer_id)
            except Exception:
                pass
            self.timer_id = None
            
        alpha = self.attributes("-alpha")
        if alpha > 0.0:
            alpha -= 0.1
            self.attributes("-alpha", max(alpha, 0.0))
            self.after(20, self._fade_out)
        else:
            self.destroy()
