# ui/panels/url_panel.py
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
import customtkinter as ctk
from ui.theme import THEME_BG, THEME_CARD_BORDER, THEME_TEXT_PRIMARY, THEME_TEXT_SECONDARY, TRANSLATIONS
from core.app_state import AppState

class UrlPanel(ctk.CTkFrame):
    def __init__(self, parent, state: AppState, on_url_changed_callback, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.app_state = state
        self.on_url_changed = on_url_changed_callback
        
        self.grid_columnconfigure(0, weight=1)
        self._build_ui()

    def _build_ui(self):
        lang = self.app_state.current_lang
        
        # Header Row: Label & Paste Button & Switch
        header_row = ctk.CTkFrame(self, fg_color="transparent")
        header_row.grid(row=0, column=0, pady=(16, 8), sticky="ew")
        header_row.grid_columnconfigure(0, weight=1)
        header_row.grid_columnconfigure(1, weight=0)
        header_row.grid_columnconfigure(2, weight=0)

        self.url_label = ctk.CTkLabel(
            header_row,
            text=TRANSLATIONS[lang]["url_label"],
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=THEME_TEXT_PRIMARY,
        )
        self.url_label.grid(row=0, column=0, sticky="w")

        self.paste_btn = ctk.CTkButton(
            header_row,
            text=TRANSLATIONS[lang]["paste_btn"],
            width=150,
            height=30,
            corner_radius=10,
            fg_color=THEME_BG,
            text_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_CARD_BORDER,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._paste_from_clipboard,
        )
        self.paste_btn.grid(row=0, column=1, padx=(0, 16), sticky="e")

        self.batch_mode_var = ctk.BooleanVar(value=self.app_state.is_batch_mode)
        self.batch_mode_switch = ctk.CTkSwitch(
            header_row,
            text=TRANSLATIONS[lang]["batch_switch"],
            variable=self.batch_mode_var,
            onvalue=True,
            offvalue=False,
            command=self._toggle_batch_mode,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME_TEXT_SECONDARY,
            progress_color="#4f46e5",
            button_color="#6366f1",
            button_hover_color="#4f46e5",
        )
        self.batch_mode_switch.grid(row=0, column=2, sticky="e")

        # URL Inputs Frame
        self.url_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.url_frame.grid(row=1, column=0, pady=(0, 10), sticky="ew")
        self.url_frame.grid_columnconfigure(0, weight=1)

        # Single-line URL Input
        self.url_entry = ctk.CTkEntry(
            self.url_frame,
            placeholder_text=TRANSLATIONS[lang]["url_placeholder"],
            height=38,
            corner_radius=10,
            fg_color=THEME_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            text_color=THEME_TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self.url_entry.grid(row=0, column=0, sticky="ew")
        self.url_entry.insert(0, self.app_state.url)
        self.url_entry.bind("<KeyRelease>", self._on_url_keyrelease)

        # Multi-line URL Input (hidden by default)
        self.url_textbox = ctk.CTkTextbox(
            self.url_frame,
            height=86,
            corner_radius=10,
            fg_color=THEME_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            text_color=THEME_TEXT_PRIMARY,
            font=ctk.CTkFont(family="Consolas", size=12),
        )
        self.url_textbox.grid(row=0, column=0, sticky="ew")
        self.url_textbox.grid_remove()

        # Output Folder Section
        self.save_folder_lbl = ctk.CTkLabel(
            self,
            text=TRANSLATIONS[lang]["save_folder_label"],
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=THEME_TEXT_PRIMARY,
        )
        self.save_folder_lbl.grid(row=2, column=0, pady=(8, 4), sticky="w")

        folder_row = ctk.CTkFrame(self, fg_color="transparent")
        folder_row.grid(row=3, column=0, pady=(0, 16), sticky="ew")
        folder_row.grid_columnconfigure(0, weight=1)
        folder_row.grid_columnconfigure(1, weight=0)

        # Output Entry
        self.output_entry = ctk.CTkEntry(
            folder_row,
            placeholder_text="Output Directory...",
            height=38,
            corner_radius=10,
            fg_color=THEME_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            text_color=THEME_TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self.output_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.output_entry.insert(0, self.app_state.output_dir)
        self.output_entry.bind("<KeyRelease>", self._on_output_dir_keyrelease)

        self.browse_btn = ctk.CTkButton(
            folder_row,
            text=TRANSLATIONS[lang]["browse_btn"],
            width=130,
            height=38,
            corner_radius=10,
            fg_color=THEME_BG,
            text_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_CARD_BORDER,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self._pick_output_dir,
        )
        self.browse_btn.grid(row=0, column=1, sticky="e")

        # Setup Drag and Drop
        self._setup_dnd()

    def _setup_dnd(self):
        # Feature 3.5: Drag and Drop URL Support using TkinterDnD (if available)
        try:
            from tkinterdnd2 import DND_TEXT
            self.url_entry.drop_target_register(DND_TEXT)
            self.url_entry.dnd_bind("<<Drop>>", self._on_url_drop)
            self.url_textbox.drop_target_register(DND_TEXT)
            self.url_textbox.dnd_bind("<<Drop>>", self._on_url_drop)
        except ImportError:
            pass # Silent fail if tkinterdnd2 is not installed

    def _on_url_drop(self, event):
        url_data = event.data.strip()
        # Clean brackets if dropped from some browsers
        if url_data.startswith("{") and url_data.endswith("}"):
            url_data = url_data[1:-1]
        
        if self.batch_mode_var.get():
            self.url_textbox.insert("insert", f"{url_data}\n")
            self._on_textbox_change()
        else:
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, url_data)
            self.app_state.url = url_data
            self.on_url_changed()

    def _paste_from_clipboard(self):
        try:
            clipboard = self.clipboard_get().strip()
            if clipboard:
                if self.batch_mode_var.get():
                    self.url_textbox.insert("insert", f"{clipboard}\n")
                    self._on_textbox_change()
                else:
                    self.url_entry.delete(0, "end")
                    self.url_entry.insert(0, clipboard)
                    self.app_state.url = clipboard
                    self.on_url_changed()
        except Exception:
            pass

    def _toggle_batch_mode(self):
        is_batch = self.batch_mode_var.get()
        self.app_state.is_batch_mode = is_batch
        if is_batch:
            self.url_entry.grid_remove()
            self.url_textbox.grid()
            self.url_textbox.delete("1.0", "end")
            self.url_textbox.insert("1.0", self.url_entry.get())
            self._on_textbox_change()
        else:
            self.url_textbox.grid_remove()
            self.url_entry.grid()
            lines = self.url_textbox.get("1.0", "end-1c").splitlines()
            first_line = lines[0] if (lines and lines[0].strip()) else ""
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, first_line)
            self.app_state.url = first_line
            self.app_state.batch_urls = [l.strip() for l in lines if l.strip()]
            self.on_url_changed()

    def _on_url_keyrelease(self, event):
        self.app_state.url = self.url_entry.get().strip()
        self.on_url_changed()

    def _on_textbox_change(self):
        lines = self.url_textbox.get("1.0", "end-1c").splitlines()
        self.app_state.batch_urls = [l.strip() for l in lines if l.strip()]
        if self.app_state.batch_urls:
            self.app_state.url = self.app_state.batch_urls[0]
        else:
            self.app_state.url = ""
        self.on_url_changed()

    def _on_output_dir_keyrelease(self, event):
        self.app_state.output_dir = self.output_entry.get().strip()

    def _pick_output_dir(self):
        chosen = filedialog.askdirectory(initialdir=self.app_state.output_dir)
        if chosen:
            self.app_state.output_dir = chosen
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, chosen)

    def set_url(self, val: str):
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, val)
        self.app_state.url = val
        if self.batch_mode_var.get():
            self.url_textbox.delete("1.0", "end")
            self.url_textbox.insert("1.0", val)
            self._on_textbox_change()
        else:
            self.on_url_changed()

    def refresh_translations(self):
        lang = self.app_state.current_lang
        self.url_label.configure(text=TRANSLATIONS[lang]["url_label"])
        self.paste_btn.configure(text=TRANSLATIONS[lang]["paste_btn"])
        self.batch_mode_switch.configure(text=TRANSLATIONS[lang]["batch_switch"])
        self.url_entry.configure(placeholder_text=TRANSLATIONS[lang]["url_placeholder"])
        self.save_folder_lbl.configure(text=TRANSLATIONS[lang]["save_folder_label"])
        self.browse_btn.configure(text=TRANSLATIONS[lang]["browse_btn"])
