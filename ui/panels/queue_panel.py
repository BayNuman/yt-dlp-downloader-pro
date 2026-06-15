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
from core.app_state import AppState, TaskStatus
from core.history import get_all_downloads, clear_all_downloads, delete_download

class QueuePanel(ctk.CTkFrame):
    def __init__(self, parent, state: AppState, on_remove_item_callback, on_redownload_callback, on_cancel_task_callback=None, **kwargs):
        super().__init__(
            parent,
            fg_color=THEME_CARD_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            corner_radius=16,
            **kwargs
        )
        self.app_state = state
        self.on_remove_item = on_remove_item_callback
        self.on_redownload = on_redownload_callback
        self.on_cancel_task = on_cancel_task_callback

        # Dynamic trackers to allow high-performance in-memory progress updates
        self.card_status_labels = {}
        self.card_dot_labels = {}
        # Smart diffing: track current card composition to avoid unnecessary rebuilds
        self._active_card_ids = []
        self._active_tab_snapshot = None
        
        # Asynchronous thumbnail caching and worker pool to prevent scroll jank!
        self.image_cache = {}
        from concurrent.futures import ThreadPoolExecutor
        self.image_loader_pool = ThreadPoolExecutor(max_workers=4)
        
        self.grid_columnconfigure(0, weight=1)
        self._build_ui()

    def destroy(self):
        try:
            self.image_loader_pool.shutdown(wait=False)
        except Exception:
            pass
        super().destroy()

    def _async_load_thumbnail(self, thumb_path: str, label_widget):
        if not thumb_path or not os.path.exists(thumb_path):
            return
            
        def load_thread():
            try:
                from PIL import Image
                with Image.open(thumb_path) as pil_img:
                    img_width = pil_img.width
                    img_height = pil_img.height
                    aspect = img_width / img_height if img_height > 0 else 1.0

                    if aspect > 2.5:  # Waveform (320x60 = 5.3:1)
                        target_w, target_h = 80, 15
                    else:  # Normal thumbnail (16:9 = 1.78:1)
                        target_w, target_h = 80, 45

                    # Support Pillow versions with Resampling or legacy ANTIALIAS fallback
                    resample_filter = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.ANTIALIAS
                    resized = pil_img.resize((target_w, target_h), resample_filter).copy()
                    size = (target_w, target_h)
                self.after(0, self._set_loaded_image, thumb_path, resized, label_widget, size)
            except Exception as e:
                print(f"[!] Async thumbnail load error: {e}")
                
        self.image_loader_pool.submit(load_thread)

    def _set_loaded_image(self, thumb_path: str, pil_img, label_widget, size=(80, 45)):
        try:
            # Create CTkImage inside main thread to be fully thread-safe
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
            self.image_cache[thumb_path] = ctk_img
            if label_widget.winfo_exists():
                label_widget.configure(image=ctk_img, text="")
        except Exception:
            pass

    def _build_ui(self):
        lang = self.app_state.current_lang

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
        # Determine tab kind based on deterministic language-agnostic index
        values = self.tab_selector.cget("values")
        try:
            idx = values.index(choice)
        except ValueError:
            idx = 0
            
        if idx == 1:
            self.tab_selector_var.set("history")
            self.btn_clear_history.grid(row=2, column=0, padx=16, pady=(0, 16), sticky="e")
        else:
            self.tab_selector_var.set("active")
            self.btn_clear_history.grid_forget()
            
        self.update_list()

    def _clear_history_db(self):
        lang = self.app_state.current_lang
        title = TRANSLATIONS[lang].get("lbl_dialog_close_title", "Exit")
        msg = TRANSLATIONS[lang].get("msg_confirm_clear_history", "Are you sure you want to clear all history?")
        confirm = messagebox.askyesno(title, msg)
        if confirm:
            clear_all_downloads()
            self.update_list()

    def update_task_progress(self, task_id: str, percent: float, speed: str, eta: str, size: str):
        """High-performance direct in-memory widget text configuration."""
        if task_id in self.card_status_labels:
            lbl = self.card_status_labels[task_id]
            if lbl.winfo_exists():
                try:
                    lang = self.app_state.current_lang
                    active_str = TRANSLATIONS[lang].get("lbl_task_downloading", "Downloading")
                    lbl.configure(text=f"{active_str} ({percent:.1f}% - {speed})")
                except Exception:
                    pass

            # Update dot color to active indigo dynamically
            if task_id in self.card_dot_labels:
                dot = self.card_dot_labels[task_id]
                if dot.winfo_exists():
                    try:
                        dot.configure(text_color=THEME_ACCENT_INDIGO)
                    except Exception:
                        pass

    def _get_translated_status(self, item, lang: str) -> str:
        """Return localized status string using lbl_task_ keys from TRANSLATIONS."""
        key = f"lbl_task_{item.status_code.value}"
        return TRANSLATIONS[lang].get(key, item.status)

    def update_list(self):
        tab = self.tab_selector_var.get()
        lang = self.app_state.current_lang

        if tab == "active":
            # Smart diffing: compute current card IDs and status codes to avoid unnecessary rebuilds
            current_states = [(item.id, item.status_code) for item in self.app_state.queue_list]
            if current_states == self._active_card_ids and self._active_tab_snapshot == "active":
                # Composition unchanged — only update text content of existing cards
                for item in self.app_state.queue_list:
                    status_text = self._get_translated_status(item, lang)
                    dot_color = self._dot_color_for_status(item.status_code)
                    if item.status_code == TaskStatus.DOWNLOADING:
                        dl_str = TRANSLATIONS[lang].get("lbl_task_downloading", "Downloading")
                        status_text = f"{dl_str} ({item.percent:.1f}% - {item.speed})"
                    elif item.status_code == TaskStatus.PAUSED:
                        status_text = TRANSLATIONS[lang].get("lbl_task_paused", "Paused")
                    if item.id in self.card_status_labels:
                        lbl = self.card_status_labels[item.id]
                        if lbl.winfo_exists():
                            try:
                                lbl.configure(text=status_text)
                            except Exception:
                                pass
                    if item.id in self.card_dot_labels:
                        dot = self.card_dot_labels[item.id]
                        if dot.winfo_exists():
                            try:
                                dot.configure(text_color=dot_color)
                            except Exception:
                                pass
                return

            # Composition changed — full rebuild required
            for child in self.scroll_frame.winfo_children():
                child.destroy()
            self.card_status_labels.clear()
            self.card_dot_labels.clear()
            self._active_card_ids = current_states
            self._active_tab_snapshot = "active"

            # RENDER ACTIVE QUEUE
            if not self.app_state.queue_list:
                placeholder = ctk.CTkLabel(
                    self.scroll_frame,
                    text=TRANSLATIONS[lang]["lbl_queue_item_placeholder"],
                    font=ctk.CTkFont(family="Segoe UI", size=12, slant="italic"),
                    text_color=THEME_TEXT_SECONDARY,
                )
                placeholder.grid(row=0, column=0, pady=40, sticky="ew")
                return

            for idx, item in enumerate(self.app_state.queue_list):
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
                dot_color = self._dot_color_for_status(item.status_code)

                dot_lbl = ctk.CTkLabel(card, text="●", text_color=dot_color, font=ctk.CTkFont(size=14))
                dot_lbl.grid(row=0, column=0, padx=(12, 6))
                self.card_dot_labels[item.id] = dot_lbl

                # Text Title
                title_text = item.title
                if len(title_text) > 40:
                    title_text = title_text[:37] + "..."
                title_lbl = ctk.CTkLabel(card, text=title_text, font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=THEME_TEXT_PRIMARY, anchor="w")
                title_lbl.grid(row=0, column=1, padx=6, pady=8, sticky="w")

                # Format preset label badge
                preset_name = str(item.preset).upper()
                badge_lbl = ctk.CTkLabel(card, text=f"[{preset_name}]", text_color=THEME_CARD_SUBTITLE, font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"))
                badge_lbl.grid(row=0, column=2, padx=10)

                # Status label (using translations)
                display_status = self._get_translated_status(item, lang)
                if item.status_code == TaskStatus.DOWNLOADING:
                    dl_str = TRANSLATIONS[lang].get("lbl_task_downloading", "Downloading")
                    display_status = f"{dl_str} ({item.percent:.1f}% - {item.speed})"
                elif item.status_code == TaskStatus.PAUSED:
                    display_status = TRANSLATIONS[lang].get("lbl_task_paused", "Paused")

                status_lbl = ctk.CTkLabel(card, text=display_status, font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=THEME_TEXT_SECONDARY)
                status_lbl.grid(row=0, column=3, padx=10)
                self.card_status_labels[item.id] = status_lbl

                # Remove or Cancel Button based on active downloading state
                is_active = item.status_code == TaskStatus.DOWNLOADING
                if is_active and self.on_cancel_task:
                    btn_text = TRANSLATIONS[lang]["btn_cancel"]
                    btn_color = THEME_BG
                    hover_color = THEME_ACCENT_RED
                    text_color = THEME_ACCENT_RED
                    cmd = lambda t_id=item.id: self.on_cancel_task(t_id)
                else:
                    btn_text = TRANSLATIONS[lang]["lbl_queue_remove"]
                    btn_color = THEME_BG
                    hover_color = THEME_ACCENT_RED
                    text_color = THEME_TEXT_PRIMARY
                    cmd = lambda i=idx: self.on_remove_item(i)

                rem_btn = ctk.CTkButton(
                    card,
                    text=btn_text,
                    width=75 if is_active else 60,
                    height=26,
                    fg_color=btn_color,
                    hover_color=hover_color,
                    text_color=text_color,
                    border_color=THEME_CARD_BORDER,
                    border_width=1,
                    corner_radius=6,
                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                    command=cmd
                )
                rem_btn.grid(row=0, column=4, padx=(6, 12))

        else:
            # History tab — always reset diffing state
            self._active_card_ids = []
            self._active_tab_snapshot = "history"
            for child in self.scroll_frame.winfo_children():
                child.destroy()

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
                card.grid_columnconfigure(2, weight=1)
                card.grid_columnconfigure((0, 1, 3, 4, 5, 6), weight=0)

                # Status Dot Indicator
                dot_color = THEME_TEXT_SECONDARY
                status_str = item.get("status", "COMPLETED")
                if status_str == "COMPLETED":
                    dot_color = THEME_ACCENT_GREEN
                elif status_str == "DOWNLOADING":
                    dot_color = THEME_ACCENT_INDIGO
                elif status_str in ("PAUSED", "Paused"):
                    dot_color = "#d97706"
                elif status_str in ("CANCELLED", "FAILED"):
                    dot_color = THEME_ACCENT_RED
                else:
                    dot_color = THEME_ACCENT_BLUE

                ctk.CTkLabel(card, text="●", text_color=dot_color, font=ctk.CTkFont(size=14)).grid(row=0, column=0, padx=(12, 4))

                # Thumbnail Column 1 (Async Cache Loaded)
                thumb_path = item.get("thumbnail_path")
                thumb_lbl = ctk.CTkLabel(card, text="🎬", width=80, height=45, fg_color=THEME_BG, corner_radius=6)
                thumb_lbl.grid(row=0, column=1, padx=6, pady=4)
                
                if thumb_path:
                    if thumb_path in self.image_cache:
                        thumb_lbl.configure(image=self.image_cache[thumb_path], text="")
                    else:
                        self._async_load_thumbnail(thumb_path, thumb_lbl)

                # Text Title on Column 2
                title_text = item.get("title", "Unknown Video")
                if len(title_text) > 40:
                    title_text = title_text[:37] + "..."
                title_lbl = ctk.CTkLabel(card, text=title_text, font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=THEME_TEXT_PRIMARY, anchor="w")
                title_lbl.grid(row=0, column=2, padx=6, pady=8, sticky="w")

                # Format details on Column 3
                format_lbl = ctk.CTkLabel(card, text=item.get("format", "Video"), text_color=THEME_CARD_SUBTITLE, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"))
                format_lbl.grid(row=0, column=3, padx=10)

                # Date of download on Column 4
                timestamp = item.get("downloaded_at", 0)
                time_struct = time.localtime(timestamp)
                date_str = time.strftime("%d/%m/%Y %H:%M", time_struct)
                date_lbl = ctk.CTkLabel(card, text=date_str, font=ctk.CTkFont(family="Segoe UI", size=10), text_color=THEME_TEXT_SECONDARY)
                date_lbl.grid(row=0, column=4, padx=10)

                # 1. Premium "Re-download" Button on Column 5
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
                redl_btn.grid(row=0, column=5, padx=4)

                # 2. Premium "Open Folder" Button (only active if file path exists) on Column 6
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
                folder_btn.grid(row=0, column=6, padx=(4, 12))

    @staticmethod
    def _dot_color_for_status(status_code: TaskStatus) -> str:
        """Map TaskStatus enum to dot indicator color."""
        if status_code == TaskStatus.PENDING:
            return THEME_ACCENT_BLUE
        elif status_code == TaskStatus.DOWNLOADING:
            return THEME_ACCENT_INDIGO
        elif status_code == TaskStatus.COMPLETED:
            return THEME_ACCENT_GREEN
        elif status_code in (TaskStatus.FAILED, TaskStatus.CANCELLED):
            return THEME_ACCENT_RED
        return THEME_TEXT_SECONDARY

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
        lang = self.app_state.current_lang
        
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
