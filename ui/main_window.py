# ui/main_window.py
import os
import queue
import re
import shutil
import threading
import urllib.request
import hashlib
import platform
import subprocess
from pathlib import Path
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image, ImageTk

# Core imports
from core.app_state import AppState
from core.downloader import run_queue_executor, resolve_ffmpeg_path
from core.history import init_db, add_download_record, get_all_downloads
from core.clip import decide_clip_strategy

# UI imports
from ui.theme import (
    THEME_BG, THEME_CARD_BG, THEME_CARD_BORDER, THEME_TEXT_PRIMARY,
    THEME_TEXT_SECONDARY, THEME_ACCENT_BLUE, THEME_ACCENT_INDIGO,
    THEME_ACCENT_GREEN, THEME_ACCENT_RED, TRANSLATIONS
)
from ui.panels.url_panel import UrlPanel
from ui.panels.preview_panel import PreviewPanel
from ui.panels.advanced_panel import AdvancedPanel
from ui.panels.queue_panel import QueuePanel
from ui.panels.progress_panel import ProgressPanel

class MainWindow(ctk.CTk):
    def __init__(self, state: AppState):
        super().__init__()
        self.app_state = state
        self.ui_queue = queue.Queue()
        self.cancel_event = threading.Event()
        self.last_fetched_url = ""
        
        # Setup paths
        self.app_state.output_dir = str(Path.home() / "Downloads" / "yt-downloads")
        self.scratch_dir = Path.home() / ".yt-downloader-scratch"
        self.scratch_dir.mkdir(parents=True, exist_ok=True)
        
        # Init SQLite History database
        init_db()

        # Premium Glassmorphic Configuration
        self.title("yt-dlp Downloader Pro")
        self.geometry("640x880")
        self.resizable(False, False)
        
        self.configure(fg_color=THEME_BG)
        ctk.set_appearance_mode(self.app_state.current_theme)

        # Setup layout configurations
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Main Scrollable Viewport to container layout
        self.main_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=THEME_CARD_BORDER
        )
        self.main_scroll.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.main_scroll.grid_columnconfigure(0, weight=1)

        self._build_header_card()
        self._build_panels()
        
        # Start the async UI metric queue draining loop
        self._drain_ui_queue()

    def _build_header_card(self):
        lang = self.app_state.current_lang
        
        # Header frosted glass card
        header_card = ctk.CTkFrame(
            self.main_scroll,
            fg_color=THEME_CARD_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            corner_radius=16
        )
        header_card.grid(row=0, column=0, padx=4, pady=6, sticky="ew")
        header_card.grid_columnconfigure(0, weight=1)
        header_card.grid_columnconfigure(1, weight=0)

        title_info = ctk.CTkFrame(header_card, fg_color="transparent")
        title_info.grid(row=0, column=0, padx=20, pady=16, sticky="w")

        self.title_lbl = ctk.CTkLabel(
            title_info,
            text=TRANSLATIONS[lang]["title"],
            font=ctk.CTkFont(family="Georgia", size=24, weight="bold"),
            text_color=THEME_TEXT_PRIMARY,
        )
        self.title_lbl.grid(row=0, column=0, sticky="w")

        self.subtitle_lbl = ctk.CTkLabel(
            title_info,
            text=TRANSLATIONS[lang]["subtitle"],
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=THEME_TEXT_SECONDARY,
            wraplength=400,
            justify="left"
        )
        self.subtitle_lbl.grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Theme & Language Panel (Right Aligned)
        config_frame = ctk.CTkFrame(header_card, fg_color="transparent")
        config_frame.grid(row=0, column=1, padx=20, pady=16, sticky="e")

        self.theme_btn = ctk.CTkButton(
            config_frame,
            text=TRANSLATIONS[lang]["theme_dark"] if self.app_state.current_theme == "Dark" else TRANSLATIONS[lang]["theme_light"],
            width=110,
            height=30,
            corner_radius=8,
            fg_color=THEME_BG,
            text_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_CARD_BORDER,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._toggle_theme_mode,
        )
        self.theme_btn.grid(row=0, column=0, padx=4, pady=4, sticky="e")

        self.lang_menu = ctk.CTkOptionMenu(
            config_frame,
            values=["EN", "TR", "ES"],
            width=65,
            height=30,
            corner_radius=8,
            fg_color=THEME_BG,
            button_color=THEME_BG,
            button_hover_color=THEME_CARD_BORDER,
            text_color=THEME_TEXT_PRIMARY,
            dropdown_fg_color=THEME_CARD_BG,
            dropdown_hover_color=THEME_CARD_BORDER,
            dropdown_text_color=THEME_TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._toggle_language,
        )
        self.lang_menu.grid(row=0, column=1, padx=4, pady=4, sticky="e")
        self.lang_menu.set(lang.upper())

    def _build_panels(self):
        # 1. URL Panel (Inputs)
        self.url_panel = UrlPanel(self.main_scroll, self.app_state, self._trigger_metadata_fetch)
        self.url_panel.grid(row=1, column=0, padx=4, pady=6, sticky="ew")

        # 2. Preview Panel (Metadata Viewer)
        self.preview_panel = PreviewPanel(self.main_scroll, self.app_state, self._on_chapter_clicked)
        self.preview_panel.grid(row=2, column=0, padx=4, pady=6, sticky="ew")
        self.preview_panel.hide()

        # 3. Advanced Panel (Gelişmiş Ayarlar)
        self.advanced_panel = AdvancedPanel(self.main_scroll, self.app_state, self._on_preset_applied)
        self.advanced_panel.grid(row=3, column=0, padx=4, pady=6, sticky="ew")

        # 4. Queue Panel (Kuyruk listesi & Geçmiş)
        self.queue_panel = QueuePanel(self.main_scroll, self.app_state, self._remove_from_queue, self._redownload_historic_item)
        self.queue_panel.grid(row=4, column=0, padx=4, pady=6, sticky="ew")

        # 5. Progress Dashboard Panel (İndirme İlerleme Paneli)
        self.progress_panel = ProgressPanel(self.main_scroll, self.app_state, self._start_download, self._cancel_download, self._open_output_dir)
        self.progress_panel.grid(row=5, column=0, padx=4, pady=6, sticky="ew")

        # Bind close handler
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ================== METADATA FETCH IMPLEMENTATIONS ==================
    def _trigger_metadata_fetch(self) -> None:
        if self.app_state.is_batch_mode:
            self.preview_panel.hide()
            return

        url = self.app_state.url.strip()
        if not url or not url.startswith(("http://", "https://")):
            self.preview_panel.hide()
            return

        if url == self.last_fetched_url:
            return

        self.last_fetched_url = url
        self.preview_panel.show_loading()

        # Spawn async metadata fetch thread
        threading.Thread(target=self._run_metadata_fetch, args=(url,), daemon=True).start()

    def _run_metadata_fetch(self, url: str) -> None:
        try:
            import yt_dlp
            # We skip downloading, but extract full details (including chapters and formats)
            ydl_opts = {
                'skip_download': True,
                'quiet': True,
                'no_warnings': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            if not info:
                raise ValueError("No info extracted")

            title = info.get("title", "Unknown Title")
            uploader = info.get("uploader", info.get("channel", "Unknown Channel"))
            duration_sec = info.get("duration", 0.0)

            thumbnail_url = info.get("thumbnail")
            local_thumb_img = None

            if thumbnail_url:
                try:
                    url_hash = hashlib.md5(url.encode()).hexdigest()
                    local_thumb_path = self.scratch_dir / f"thumb_{url_hash}.jpg"
                    
                    req = urllib.request.Request(thumbnail_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req) as response:
                        with open(local_thumb_path, 'wb') as out_file:
                            out_file.write(response.read())

                    pil_img = Image.open(local_thumb_path)
                    pil_img = pil_img.resize((160, 90), Image.Resampling.LANCZOS)
                    local_thumb_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(160, 90))
                except Exception as e:
                    print(f"Thumbnail download failed: {e}")

            # Cache the extracted info inside state
            self.app_state.current_video_info = info

            fetched_metadata = {
                "url": url,
                "title": title,
                "uploader": uploader,
                "duration": duration_sec,
                "thumbnail_img": local_thumb_img,
                "chapters": info.get("chapters", []),
                "filesize": info.get("filesize"),
                "filesize_approx": info.get("filesize_approx")
            }
            self.ui_queue.put(("metadata_ready", fetched_metadata))

        except Exception as e:
            print(f"[!] Metadata fetch failed: {e}")
            self.ui_queue.put(("metadata_error", str(e)))

    def _on_chapter_clicked(self, start_seconds: float, end_seconds: float, chapter_title: str):
        # Feature 3.4 Chapters auto-clipping selection integration
        self.advanced_panel.clip_enabled_var.set(True)
        self.advanced_panel.clip_start_var.set(format_seconds_to_mmss(start_seconds))
        self.advanced_panel.clip_end_var.set(format_seconds_to_mmss(end_seconds))
        self.advanced_panel._on_clip_toggled()
        self.advanced_panel._validate_clip_entries()
        
        # Focus on advanced panel
        self.advanced_panel.tabview.set(TRANSLATIONS[self.app_state.current_lang]["tab_clip"])

    def _on_preset_applied(self):
        # Refresh current profile preview hint
        pass

    # ================== QUEUE ACTION IMPLEMENTATIONS ==================
    def _add_to_queue(self) -> None:
        url = self.app_state.url.strip()
        if not url:
            messagebox.showwarning(TRANSLATIONS[self.app_state.current_lang]["lbl_dialog_warning_title"], TRANSLATIONS[self.app_state.current_lang]["lbl_dialog_warning_url"])
            return

        lang = self.app_state.current_lang
        # Gather active configurations from advanced panel
        item_cfg = self.advanced_panel.get_settings_dict()
        
        # Decide seek strategy if clipping is enabled
        clip_strategy = "stream_seek"
        if item_cfg.get("clip_enabled") and self.app_state.current_video_info:
            start = parse_time_to_seconds(item_cfg.get("clip_start", "00:00")) or 0.0
            end = parse_time_to_seconds(item_cfg.get("clip_end", "00:00")) or 0.0
            clip_strategy = decide_clip_strategy(self.app_state.current_video_info, start, end)

        if self.app_state.is_batch_mode:
            # Multi-line batch processing
            added_count = 0
            for raw_url in self.app_state.batch_urls:
                if raw_url.startswith(("http://", "https://")):
                    item_id = hashlib.md5(raw_url.encode()).hexdigest()
                    item = {
                        "id": item_id,
                        "url": raw_url,
                        "title": f"Batch Link [{item_id[:6]}]",
                        "duration": "00:00",
                        "preset": item_cfg.get("video_profile", "Custom"),
                        "status": "Bekliyor" if lang == "tr" else ("Esperando" if lang == "es" else "Waiting"),
                        "clip_strategy": clip_strategy
                    }
                    item.update(item_cfg)
                    self.app_state.queue_list.append(item)
                    added_count += 1
            
            self.url_panel.set_url("")
            self.progress_panel.update_status("●", THEME_ACCENT_BLUE, TRANSLATIONS[self.app_state.current_lang]["lbl_status_added"].format(count=added_count))
        else:
            # Single item queueing
            title = self.app_state.current_video_info.get("title", "Video Title") if self.app_state.current_video_info else "Downloading video"
            duration = format_seconds_to_mmss(self.app_state.current_video_info.get("duration", 0)) if self.app_state.current_video_info else "00:00"
            item_id = hashlib.md5(url.encode()).hexdigest()
            
            item = {
                "id": item_id,
                "url": url,
                "title": title,
                "duration": duration,
                "preset": item_cfg.get("video_profile", "Custom"),
                "status": "Bekliyor" if lang == "tr" else ("Esperando" if lang == "es" else "Waiting"),
                "clip_strategy": clip_strategy
            }
            item.update(item_cfg)
            self.app_state.queue_list.append(item)
            
            self.url_panel.set_url("")
            self.preview_panel.hide()
            self.progress_panel.update_status("●", THEME_ACCENT_BLUE, TRANSLATIONS[self.app_state.current_lang]["lbl_status_ready"])

        self.queue_panel.update_list()

    def _remove_from_queue(self, idx: int):
        if idx >= 0 and idx < len(self.app_state.queue_list):
            item = self.app_state.queue_list[idx]
            # Don't delete active downloading item
            if "İndir" in item["status"] or "Down" in item["status"] or "Desc" in item["status"]:
                return
            del self.app_state.queue_list[idx]
            self.queue_panel.update_list()

    def _redownload_historic_item(self, url: str, format_desc: str):
        # Feature 3.2: Re-download callback
        self.url_panel.set_url(url)
        self.app_state.url = url
        # Toggle mode based on history format description
        if "Audio" in format_desc or "mp3" in format_desc:
            self.advanced_panel.mode_var.set("Audio")
        else:
            self.advanced_panel.mode_var.set("Video")
        self.advanced_panel._on_mode_changed(self.advanced_panel.mode_var.get())
        
        # Trigger queue panel tab view switch back to Active Queue
        self.queue_panel.tab_selector.set(TRANSLATIONS[self.app_state.current_lang]["tab_active"])
        self.queue_panel._on_tab_changed(TRANSLATIONS[self.app_state.current_lang]["tab_active"])
        
        # Auto-trigger preview metadata fetch
        self._trigger_metadata_fetch()

    # ================== RUN EXECUTION ACTIONS ==================
    def _start_download(self) -> None:
        if self.app_state.is_executor_running:
            messagebox.showinfo(TRANSLATIONS[self.app_state.current_lang]["lbl_dialog_info_title"], TRANSLATIONS[self.app_state.current_lang]["lbl_dialog_info_running"])
            return

        # Auto queue URL input if queue list empty
        if not self.app_state.queue_list:
            url = self.app_state.url.strip()
            if url:
                self._add_to_queue()
            else:
                messagebox.showwarning(TRANSLATIONS[self.app_state.current_lang]["lbl_dialog_warning_title"], TRANSLATIONS[self.app_state.current_lang]["lbl_dialog_warning_url"])
                return

        self.cancel_event.clear()
        self.app_state.current_item_index = 0
        self.progress_panel.set_running_state(True)
        
        # Spawn queue background execution worker thread
        threading.Thread(target=run_queue_executor, args=(self.app_state, self.ui_queue, self.cancel_event), daemon=True).start()

    def _cancel_download(self):
        self.cancel_event.set()
        self.progress_panel.update_status("●", THEME_ACCENT_RED, TRANSLATIONS[self.app_state.current_lang]["lbl_status_cancelled"])
        self.progress_panel.set_running_state(False)

    def _open_output_dir(self):
        # Bug Fix 3: Cross-platform output directory opening (Windows, macOS, Linux)
        path = Path(self.app_state.output_dir).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        
        system = platform.system()
        if system == "Windows":
            os.startfile(str(path))
        elif system == "Darwin":
            subprocess.run(["open", str(path)])
        else:
            subprocess.run(["xdg-open", str(path)])

    # ================== METRIC DRAINING & LIFECYCLE ==================
    def _drain_ui_queue(self) -> None:
        while True:
            try:
                kind, payload = self.ui_queue.get_nowait()
            except queue.Empty:
                break

            if kind == "log":
                self.progress_panel.append_log(str(payload))
            elif kind == "stats":
                stats = payload
                percent_val = float(stats["percent"])
                self.progress_panel.set_progress(percent_val / 100.0)
                self.progress_panel.set_stats(
                    speed=str(stats["speed"]),
                    eta=str(stats["eta"]),
                    size=str(stats["size"])
                )
            elif kind == "active_file":
                self.progress_panel.active_file_var.set(str(payload))
            elif kind == "percent_complete":
                self.progress_panel.set_progress(float(payload))
            elif kind == "status":
                dot, color, message = payload
                self.progress_panel.update_status(dot, color, message)
            elif kind == "queue_sync":
                self.queue_panel.update_list()
            elif kind == "metadata_ready":
                meta = payload
                self.preview_panel.show_metadata(meta, meta["thumbnail_img"])
            elif kind == "metadata_error":
                self.preview_panel.show_error()
            elif kind == "toast_outdated":
                # Bug Fix 2: Outdated warning trigger display
                self._show_toast(TRANSLATIONS[self.app_state.current_lang]["lbl_toast_outdated_title"], TRANSLATIONS[self.app_state.current_lang]["lbl_toast_outdated_desc"])
            elif kind == "toast_success":
                self._show_toast(TRANSLATIONS[self.app_state.current_lang]["lbl_toast_success_title"], TRANSLATIONS[self.app_state.current_lang]["lbl_toast_success_desc"].format(title=payload))
            elif kind == "toast_cancel":
                self._show_toast(TRANSLATIONS[self.app_state.current_lang]["lbl_dialog_close_title"], f"Download queue cancelled for '{payload}'")
            elif kind == "toast_error":
                err_data = payload
                self._show_toast(TRANSLATIONS[self.app_state.current_lang]["lbl_toast_err_title"], TRANSLATIONS[self.app_state.current_lang]["lbl_toast_err_desc"].format(code=err_data["code"], title=err_data["title"]))
            elif kind == "queue_done":
                self.progress_panel.set_running_state(False)
                self.progress_panel.active_file_var.set(TRANSLATIONS[self.app_state.current_lang]["lbl_active_dl"])
                
                if self.cancel_event.is_set():
                    self.progress_panel.update_status("●", THEME_ACCENT_RED, TRANSLATIONS[self.app_state.current_lang]["lbl_status_cancelled"])
                else:
                    self.progress_panel.update_status("●", THEME_ACCENT_GREEN, TRANSLATIONS[self.app_state.current_lang]["lbl_status_completed"])
                    self._show_toast(TRANSLATIONS[self.app_state.current_lang]["lbl_toast_all_title"], TRANSLATIONS[self.app_state.current_lang]["lbl_toast_all_desc"])

        self.after(100, self._drain_ui_queue)

    def _show_toast(self, title: str, desc: str):
        # Show premium Tkinter messagebox toast
        messagebox.showinfo(title, desc)

    def _toggle_theme_mode(self):
        if self.app_state.current_theme == "Dark":
            self.app_state.current_theme = "Light"
            ctk.set_appearance_mode("Light")
            self.theme_btn.configure(text=TRANSLATIONS[self.app_state.current_lang]["theme_light"])
        else:
            self.app_state.current_theme = "Dark"
            ctk.set_appearance_mode("Dark")
            self.theme_btn.configure(text=TRANSLATIONS[self.app_state.current_lang]["theme_dark"])

    def _toggle_language(self, choice: str):
        self.app_state.current_lang = choice.lower()
        lang = self.app_state.current_lang
        
        # Update Header Card labels
        self.title_lbl.configure(text=TRANSLATIONS[lang]["title"])
        self.subtitle_lbl.configure(text=TRANSLATIONS[lang]["subtitle"])
        self.theme_btn.configure(
            text=TRANSLATIONS[lang]["theme_dark"] if self.app_state.current_theme == "Dark" else TRANSLATIONS[lang]["theme_light"]
        )

        # Refresh all sub-panels' translations dynamically
        self.url_panel.refresh_translations()
        self.preview_panel.refresh_translations()
        self.advanced_panel.refresh_translations()
        self.queue_panel.refresh_translations()
        self.progress_panel.refresh_translations()

    def _on_close(self):
        if self.app_state.is_executor_running:
            if not messagebox.askyesno(TRANSLATIONS[self.app_state.current_lang]["lbl_dialog_close_title"], TRANSLATIONS[self.app_state.current_lang]["lbl_dialog_close_desc"]):
                return
            self._cancel_download()
        
        try:
            shutil.rmtree(self.scratch_dir, ignore_errors=True)
        except Exception:
            pass

        self.destroy()
