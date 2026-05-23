# ui/panels/queue_panel.py
import tkinter as tk
from tkinter import messagebox
import os
import platform
import subprocess
from pathlib import Path
import time
import customtkinter as ctk
from ui.theme import (
    THEME_BG, THEME_CARD_BG, THEME_CARD_BORDER, THEME_TEXT_PRIMARY,
    THEME_TEXT_SECONDARY, THEME_ACCENT_BLUE, THEME_ACCENT_INDIGO,
    THEME_ACCENT_GREEN, THEME_ACCENT_RED, THEME_CARD_SUBTITLE, TRANSLATIONS
)
from core.app_state import AppState
from core.history import get_all_downloads, clear_all_downloads, delete_download

class QueuePanel(ctk.CTkFrame):
    def __init__(self, parent, state: AppState, on_remove_item_callback, on_redownload_callback, **kwargs):
        super().__init__(
            parent,
            fg_color=THEME_CARD_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            corner_radius=16,
            **kwargs
        )
        self.state = state
        self.on_remove_item = on_remove_item_callback
        self.on_redownload = on_redownload_callback
        
        self.grid_columnconfigure(0, weight=1)
        self._build_ui()

    def _build_ui(self):
        lang = self.state.current_lang

        # Segmented Control Tab Switcher
        self.tab_selector_var = ctk.StringVar(value="active")
        self.tab_selector = ctk.CTkSegmentedButton(
            self,
            values=["Active Queue 📋", "History 📁"], # Will translate dynamically
            variable=self.tab_selector_var,
            selected_color=THEME_ACCENT_INDIGO,
            unselected_color=THEME_BG,
            unselected_hover_color=THEME_CARD_BORDER,
            text_color=THEME_TEXT_PRIMARY,
            command=self._on_tab_changed,
            height=34,
            corner_radius=10
        )
        self.tab_selector.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")

        # Scrollable Frame for listing items
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            height=180,
            fg_color="transparent",
            scrollbar_button_color=THEME_CARD_BORDER
        )
        self.scroll_frame.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        # Clear History button (only shown on History tab)
        self.btn_clear_history = ctk.CTkButton(
            self,
            text="🧹 Clear History",
            height=28,
            corner_radius=8,
            fg_color=THEME_BG,
            text_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_ACCENT_RED,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._clear_history_db
        )
        # Hidden by default

        self.update_list()

    def _on_tab_changed(self, choice):
        # Determine tab kind based on string (tr/en/es segmented values)
        lang = self.state.current_lang
        
        if choice == TRANSLATIONS[lang]["tab_history"]:
            self.tab_selector_var.set("history")
            self.btn_clear_history.grid(row=2, column=0, padx=16, pady=(0, 16), sticky="e")
        else:
            self.tab_selector_var.set("active")
            self.btn_clear_history.grid_forget()
            
        self.update_list()

    def _clear_history_db(self):
        lang = self.state.current_lang
        confirm = messagebox.askyesno(
            TRANSLATIONS[lang]["lbl_dialog_close_title"],
            "Tüm indirme geçmişini silmek istediğinize emin misiniz?" if lang == "tr" else "Are you sure you want to clear all history?"
        )
        if confirm:
            clear_all_downloads()
            self.update_list()

    def update_list(self):
        # Clear existing list UI widgets
        for child in self.scroll_frame.winfo_children():
            child.destroy()

        tab = self.tab_selector_var.get()
        lang = self.state.current_lang

        if tab == "active":
            # RENDER ACTIVE QUEUE
            if not self.state.queue_list:
                placeholder = ctk.CTkLabel(
                    self.scroll_frame,
                    text=TRANSLATIONS[lang]["lbl_queue_item_placeholder"],
                    font=ctk.CTkFont(family="Segoe UI", size=12, slant="italic"),
                    text_color=THEME_TEXT_SECONDARY,
                )
                placeholder.grid(row=0, column=0, pady=40, sticky="ew")
                return

            for idx, item in enumerate(self.state.queue_list):
                card = ctk.CTkFrame(
                    self.scroll_frame,
                    fg_color=THEME_CARD_BG,
                    border_color=THEME_CARD_BORDER,
                    border_width=1,
                    corner_radius=10
                )
                card.grid(row=idx, column=0, padx=6, pady=4, sticky="ew")
                card.grid_columnconfigure(1, weight=1)
                card.grid_columnconfigure((0, 2, 3, 4), weight=0)

                # Dot indicator color
                dot_color = THEME_TEXT_SECONDARY
                status_str = item.get("status", "Pending")
                if "Wait" in status_str or "Bek" in status_str or "Pen" in status_str:
                    dot_color = THEME_ACCENT_BLUE
                elif "İndir" in status_str or "Down" in status_str or "Desc" in status_str:
                    dot_color = THEME_ACCENT_INDIGO
                elif "Tamam" in status_str or "Comp" in status_str or "Exit" in status_str:
                    dot_color = THEME_ACCENT_GREEN
                elif "Hata" in status_str or "Err" in status_str or "Iptal" in status_str or "Canc" in status_str:
                    dot_color = THEME_ACCENT_RED

                ctk.CTkLabel(card, text="●", text_color=dot_color, font=ctk.CTkFont(size=14)).grid(row=0, column=0, padx=(12, 6))

                # Text Title
                title_text = item.get("title", "Unknown Video")
                if len(title_text) > 45:
                    title_text = title_text[:42] + "..."
                title_lbl = ctk.CTkLabel(card, text=title_text, font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=THEME_TEXT_PRIMARY, anchor="w")
                title_lbl.grid(row=0, column=1, padx=6, pady=8, sticky="w")

                # Format preset label badge
                preset_name = item.get("preset", "Custom").upper()
                badge_lbl = ctk.CTkLabel(card, text=f"[{preset_name}]", text_color=THEME_CARD_SUBTITLE, font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"))
                badge_lbl.grid(row=0, column=2, padx=10)

                # Status label
                status_lbl = ctk.CTkLabel(card, text=status_str, font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=THEME_TEXT_SECONDARY)
                status_lbl.grid(row=0, column=3, padx=10)

                # Remove Button (only active if not downloading/processing)
                rem_btn = ctk.CTkButton(
                    card,
                    text=TRANSLATIONS[lang]["lbl_queue_remove"],
                    width=60,
                    height=26,
                    fg_color=THEME_BG,
                    hover_color=THEME_ACCENT_RED,
                    text_color=THEME_TEXT_PRIMARY,
                    border_color=THEME_CARD_BORDER,
                    border_width=1,
                    corner_radius=6,
                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                    command=lambda i=idx: self.on_remove_item(i)
                )
                rem_btn.grid(row=0, column=4, padx=(6, 12))

        else:
            # RENDER PERSISTENT HISTORY FROM SQLITE
            downloads = get_all_downloads()
            if not downloads:
                placeholder = ctk.CTkLabel(
                    self.scroll_frame,
                    text="İndirme geçmişi bulunamadı." if lang == "tr" else "No download history found.",
                    font=ctk.CTkFont(family="Segoe UI", size=12, slant="italic"),
                    text_color=THEME_TEXT_SECONDARY,
                )
                placeholder.grid(row=0, column=0, pady=40, sticky="ew")
                return

            for idx, item in enumerate(downloads):
                card = ctk.CTkFrame(
                    self.scroll_frame,
                    fg_color=THEME_CARD_BG,
                    border_color=THEME_CARD_BORDER,
                    border_width=1,
                    corner_radius=10
                )
                card.grid(row=idx, column=0, padx=6, pady=4, sticky="ew")
                card.grid_columnconfigure(1, weight=1)
                card.grid_columnconfigure((0, 2, 3, 4, 5), weight=0)

                # Status Dot Indicator
                dot_color = THEME_TEXT_SECONDARY
                status_str = item.get("status", "COMPLETED")
                if status_str == "COMPLETED":
                    dot_color = THEME_ACCENT_GREEN
                elif status_str == "DOWNLOADING":
                    dot_color = THEME_ACCENT_INDIGO
                elif status_str == "CANCELLED" or status_str == "FAILED":
                    dot_color = THEME_ACCENT_RED
                else:
                    dot_color = THEME_ACCENT_BLUE

                ctk.CTkLabel(card, text="●", text_color=dot_color, font=ctk.CTkFont(size=14)).grid(row=0, column=0, padx=(12, 6))

                # Text Title
                title_text = item.get("title", "Unknown Video")
                if len(title_text) > 40:
                    title_text = title_text[:37] + "..."
                title_lbl = ctk.CTkLabel(card, text=title_text, font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=THEME_TEXT_PRIMARY, anchor="w")
                title_lbl.grid(row=0, column=1, padx=6, pady=8, sticky="w")

                # Format details
                format_lbl = ctk.CTkLabel(card, text=item.get("format", "Video"), text_color=THEME_CARD_SUBTITLE, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"))
                format_lbl.grid(row=0, column=2, padx=10)

                # Date of download
                timestamp = item.get("downloaded_at", 0)
                time_struct = time.localtime(timestamp)
                date_str = time.strftime("%d/%m/%Y %H:%M", time_struct)
                date_lbl = ctk.CTkLabel(card, text=date_str, font=ctk.CTkFont(family="Segoe UI", size=10), text_color=THEME_TEXT_SECONDARY)
                date_lbl.grid(row=0, column=3, padx=10)

                # 1. Premium "Re-download" Button
                redl_btn = ctk.CTkButton(
                    card,
                    text=TRANSLATIONS[lang]["btn_redownload"],
                    width=90,
                    height=26,
                    fg_color=THEME_BG,
                    hover_color=THEME_ACCENT_BLUE,
                    text_color=THEME_TEXT_PRIMARY,
                    border_color=THEME_CARD_BORDER,
                    border_width=1,
                    corner_radius=6,
                    font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                    command=lambda u=item.get("url"), f=item.get("format"): self.on_redownload(u, f)
                )
                redl_btn.grid(row=0, column=4, padx=4)

                # 2. Premium "Open Folder" Button (only active if file path exists)
                file_path = item.get("file_path", "")
                folder_exists = file_path and os.path.exists(Path(file_path).parent)
                folder_state = "normal" if folder_exists else "disabled"
                
                folder_btn = ctk.CTkButton(
                    card,
                    text=TRANSLATIONS[lang]["btn_open_folder"],
                    width=80,
                    height=26,
                    state=folder_state,
                    fg_color=THEME_BG,
                    hover_color=THEME_CARD_BORDER,
                    text_color=THEME_TEXT_PRIMARY,
                    border_color=THEME_CARD_BORDER,
                    border_width=1,
                    corner_radius=6,
                    font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                    command=lambda p=file_path: self._open_native_folder(p)
                )
                folder_btn.grid(row=0, column=5, padx=(4, 12))

    def _open_native_folder(self, file_path_str: str):
        # Bug Fix 3: Cross-platform native folder opening (instead of os.startfile)
        if not file_path_str:
            return
        
        path = Path(file_path_str).parent
        if not path.exists():
            return
            
        system = platform.system()
        if system == "Windows":
            os.startfile(str(path))
        elif system == "Darwin":
            subprocess.run(["open", str(path)])
        else:
            subprocess.run(["xdg-open", str(path)])

    def refresh_translations(self):
        lang = self.state.current_lang
        
        # Re-build Segmented button values to update translations
        active_tab_txt = TRANSLATIONS[lang]["tab_active"]
        history_tab_txt = TRANSLATIONS[lang]["tab_history"]
        
        curr_selection = self.tab_selector_var.get()
        self.tab_selector.configure(values=[active_tab_txt, history_tab_txt])
        
        if curr_selection == "history":
            self.tab_selector_var.set(history_tab_txt)
        else:
            self.tab_selector_var.set(active_tab_txt)
            
        self.btn_clear_history.configure(
            text="🧹 " + ("Geçmişi Temizle" if lang == "tr" else ("Clear History" if lang == "en" else "Limpiar Historial"))
        )
        
        self.update_list()
