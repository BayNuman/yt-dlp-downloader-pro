# ui/main_window.py
import os
import sys
import queue
import re
import shutil
import threading
import urllib.request
import hashlib
import platform
import uuid
import subprocess
import datetime
import time
from pathlib import Path
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image, ImageTk

# Core imports
from core.app_state import AppState, TaskStatus, save_app_preferences
from core.downloader import run_queue_executor, resolve_ffmpeg_path, kill_all_active_subprocesses
from core.history import init_db, add_download_record, get_all_downloads, shutdown_db, get_channel_rule
from core.clip import decide_clip_strategy, parse_time_to_seconds, format_seconds_to_mmss
from core.controller import AppController

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
        self.ui_queue = queue.Queue(maxsize=500)
        self.cancel_event = threading.Event()
        self._queue_lock = threading.RLock()
        self.last_fetched_url = ""
        self.controller = AppController(state)
        
        # Setup paths
        self.app_state.output_dir = str(Path.home() / "Downloads" / "yt-downloads")
        self.scratch_dir = Path.home() / ".yt-downloader-scratch"
        self.scratch_dir.mkdir(parents=True, exist_ok=True)
        
        # Init SQLite History database
        init_db()

        # Premium Glassmorphic Configuration
        self.title("yt-dlp Downloader Pro")
        self.geometry("1100x820")
        self.resizable(True, True)
        self.minsize(1000, 750)
        
        # Load and set the high-fidelity window icon dynamically at runtime
        logo_png_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "logo.png")
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            logo_png_path = os.path.join(sys._MEIPASS, "assets", "logo.png")
            
        if os.path.exists(logo_png_path):
            try:
                from PIL import ImageTk
                icon_img = ImageTk.PhotoImage(file=logo_png_path)
                self.wm_iconphoto(True, icon_img)
            except Exception as e:
                print(f"Failed to set window icon: {e}")
        
        self.configure(fg_color=THEME_BG)
        ctk.set_appearance_mode(self.app_state.current_theme)
 
        # Setup layout configurations
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
 
        # Main Container Frame (instead of scrollable frame)
        self.main_container = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(0, weight=0) # Header Card
        self.main_container.grid_rowconfigure(1, weight=1) # Columns row
 
        # Side-by-side Columns
        self.left_column = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.left_column.grid(row=1, column=0, padx=(0, 6), pady=(6, 0), sticky="nsew")
        self.left_column.grid_columnconfigure(0, weight=1)
        self.left_column.grid_rowconfigure(0, weight=0) # URL Panel
        self.left_column.grid_rowconfigure(1, weight=1) # Preview Panel
        self.left_column.grid_rowconfigure(2, weight=0) # Advanced Panel

        self.right_column = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.right_column.grid(row=1, column=1, padx=(6, 0), pady=(6, 0), sticky="nsew")
        self.right_column.grid_columnconfigure(0, weight=1)
        self.right_column.grid_rowconfigure(0, weight=1) # Queue Panel
        self.right_column.grid_rowconfigure(1, weight=0) # Progress Panel

        self._build_header_card()
        self._build_panels()
        
        # Start PyPI update checker silently in background
        from core.updater import UpdateChecker
        self.updater = UpdateChecker(ui_callback=self._on_update_found)
        self.updater.check_in_background()

        # Start the async UI metric queue draining loop
        self._drain_ui_queue()

        # Check and prompt to install JS runtime Deno dynamically after a 2-second UI load buffer
        self.after(2000, self._check_and_prompt_deno)

    def _check_and_prompt_deno(self) -> None:
        if platform.system() != "Windows":
            return

        def bg_check():
            import shutil
            if shutil.which('deno') or shutil.which('node'):
                return
            
            self.after(0, self._show_deno_prompt)

        threading.Thread(target=bg_check, daemon=True, name="deno-env-checker").start()

    def _show_deno_prompt(self) -> None:
        import shutil
        from core.env import refresh_path_env
        lang = self.app_state.current_lang
        title = "Sistem Gereksinimi" if lang == "tr" else ("Requisito del Sistema" if lang == "es" else "System Requirement")
        msg = (
            "YouTube videolarını yüksek hızda ve sınırsız formatta indirebilmek için gerekli olan şifre çözme motoru (Deno) bilgisayarınızda bulunamadı.\n\n"
            "Arka planda otomatik olarak kurulmasını ister misiniz?"
        ) if lang == "tr" else (
            "No se encontró el motor de descifrado (Deno) necesario para descargar videos de YouTube a alta velocidad.\n\n"
            "¿Desea instalarlo automáticamente en segundo plano?"
        ) if lang == "es" else (
            "The decryption engine (Deno) required to download YouTube videos at high speed was not found on your system.\n\n"
            "Would you like to install it automatically in the background?"
        )
        
        if messagebox.askyesno(title, msg):
            def installer_thread():
                try:
                    import subprocess
                    startupinfo = None
                    if os.name == 'nt':
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    
                    # Execute Winget install
                    subprocess.run(
                        ["winget", "install", "DenoLand.Deno", "--scope", "user", "--accept-package-agreements", "--accept-source-agreements"],
                        startupinfo=startupinfo,
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    
                    # Refresh PATH
                    refresh_path_env()
                    
                    if shutil.which('deno'):
                        self.after(0, lambda: messagebox.showinfo(
                            "Kurulum Başarılı" if lang == "tr" else ("Instalación Exitosa" if lang == "es" else "Installation Successful"),
                            "YouTube şifre çözme motoru (Deno) başarıyla kuruldu! Artık yüksek hızda indirebilirsiniz." if lang == "tr" else ("El motor de descifrado (Deno) se ha instalado correctamente." if lang == "es" else "Decryption engine (Deno) installed successfully!")
                        ))
                    else:
                        self.after(0, lambda: messagebox.showwarning(
                            "Kurulum Başarısız" if lang == "tr" else ("Instalación Fallida" if lang == "es" else "Installation Failed"),
                            "Kurulum tamamlanamadı. Lütfen daha sonra tekrar deneyin veya Deno'yu manuel kurun." if lang == "tr" else ("No se pudo completar la instalación." if lang == "es" else "Installation could not be completed.")
                        ))
                except FileNotFoundError:
                    self.after(0, lambda: messagebox.showwarning(
                        "Paket Yöneticisi Bulunamadı" if lang == "tr" else ("Package Manager Not Found" if lang == "es" else "Package Manager Not Found"),
                        "Windows Paket Yöneticisi (winget) bulunamadı. Lütfen Deno'yu https://deno.com/ adresinden manuel olarak kurun." if lang == "tr" else "Windows Package Manager (winget) was not found. Please install Deno manually."
                    ))
                except Exception as e:
                    print(f"Deno auto-install failed: {e}")
                    self.after(0, lambda: messagebox.showwarning(
                        "Kurulum Başarısız" if lang == "tr" else ("Instalación Fallida" if lang == "es" else "Installation Failed"),
                        f"Deno kurulumu sırasında hata oluştu: {e}\nLütfen Deno'yu manuel olarak kurun." if lang == "tr" else f"Error during installation: {e}"
                    ))
                    
            threading.Thread(target=installer_thread, daemon=True, name="deno-installer").start()

    def _build_header_card(self):
        lang = self.app_state.current_lang
        
        # Header frosted glass card
        header_card = ctk.CTkFrame(
            self.main_container,
            fg_color=THEME_CARD_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            corner_radius=16
        )
        header_card.grid(row=0, column=0, columnspan=2, padx=4, pady=6, sticky="ew")
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

        self.btn_compact_mode = ctk.CTkButton(
            config_frame,
            text="",
            width=110,
            height=30,
            corner_radius=8,
            fg_color=THEME_BG,
            text_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_CARD_BORDER,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._toggle_compact_mode,
        )
        self.btn_compact_mode.grid(row=0, column=2, padx=4, pady=4, sticky="e")

        # Hidden update warning button
        self.btn_update_warning = ctk.CTkButton(
            header_card,
            text="",
            fg_color="#dc2626",
            hover_color="#b91c1c",
            text_color="#ffffff",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self.perform_update,
            height=32,
            corner_radius=8
        )

    def _build_panels(self):
        # 1. URL Panel (Inputs)
        self.url_panel = UrlPanel(self.left_column, self.app_state, self._trigger_metadata_fetch)
        self.url_panel.grid(row=0, column=0, padx=4, pady=6, sticky="ew")

        # 2. Preview Panel (Metadata Viewer)
        self.preview_panel = PreviewPanel(self.left_column, self.app_state, self._on_chapter_clicked, self._on_create_channel_rule)
        self.preview_panel.grid(row=1, column=0, padx=4, pady=6, sticky="nsew")
        self.preview_panel.hide()

        # 3. Advanced Panel (Gelişmiş Ayarlar)
        self.advanced_panel = AdvancedPanel(self.left_column, self.app_state, self._on_preset_applied)
        self.advanced_panel.grid(row=2, column=0, padx=4, pady=6, sticky="ew")

        # 4. Queue Panel (Kuyruk listesi & Geçmiş)
        self.queue_panel = QueuePanel(self.right_column, self.app_state, self._remove_from_queue, self._redownload_historic_item, self._cancel_single_task)
        self.queue_panel.grid(row=0, column=0, padx=4, pady=6, sticky="nsew")

        # 5. Progress Dashboard Panel (İndirme İlerleme Paneli)
        self.progress_panel = ProgressPanel(self.right_column, self.app_state, self._start_download, self._cancel_download, self._open_output_dir)
        self.progress_panel.grid(row=1, column=0, padx=4, pady=6, sticky="ew")

        # Bind close handler
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Initialize context-aware cross-platform keyboard shortcuts
        self._setup_shortcuts()

        # Apply initial compact mode layout state
        self._apply_compact_mode()

    def _setup_shortcuts(self):
        import sys
        from core.app_state import TaskStatus
        modifier = "Command" if sys.platform == "darwin" else "Control"
        
        # 1. Paste & Fetch: Ctrl+V or Cmd+V
        self.bind_all(f"<{modifier}-v>", self._handle_shortcut_paste)
        # 2. Start Download: Ctrl+Enter or Cmd+Return
        self.bind_all(f"<{modifier}-Return>", self._handle_shortcut_start_download)
        # 3. Pause/Resume active download task: Space
        self.bind_all("<space>", self._handle_shortcut_space)
        # 4. Cancel active queue download: Escape
        self.bind_all("<Escape>", self._handle_shortcut_escape)

    def _handle_shortcut_paste(self, event):
        focused = self.focus_get()
        # If user is in an entry or text field, bypass global hook
        if isinstance(focused, (ctk.CTkEntry, ctk.CTkTextbox)) or (focused and "entry" in str(focused).lower()) or (focused and "text" in str(focused).lower()):
            return
        try:
            clipboard_text = self.clipboard_get()
            if clipboard_text and clipboard_text.strip().startswith(("http://", "https://")):
                self.url_panel.set_url(clipboard_text.strip())
                self._trigger_metadata_fetch()
                return "break"
        except Exception:
            pass

    def _handle_shortcut_start_download(self, event):
        focused = self.focus_get()
        if isinstance(focused, ctk.CTkTextbox) or (focused and "text" in str(focused).lower()):
            return
        url = self.app_state.url.strip()
        if url.startswith(("http://", "https://")) or self.app_state.queue_list:
            self._start_download()
            return "break"

    def _handle_shortcut_space(self, event):
        from core.app_state import TaskStatus
        focused = self.focus_get()
        if isinstance(focused, (ctk.CTkEntry, ctk.CTkTextbox)) or (focused and "entry" in str(focused).lower()) or (focused and "text" in str(focused).lower()):
            return
            
        # Space pauses/resumes active download
        active_task = None
        for task in self.app_state.queue_list:
            if task.status_code == TaskStatus.DOWNLOADING or getattr(task, "is_paused", False):
                active_task = task
                break
        if active_task:
            from core.downloader import toggle_pause_task
            toggle_pause_task(active_task)
            self.queue_panel.update_list()
            return "break"

    def _handle_shortcut_escape(self, event):
        focused = self.focus_get()
        if isinstance(focused, (ctk.CTkEntry, ctk.CTkTextbox)) or (focused and "entry" in str(focused).lower()) or (focused and "text" in str(focused).lower()):
            return
        if self.app_state.is_executor_running:
            self._cancel_download()
            return "break"

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
        
        # Reset the manual override track on new preview
        self.advanced_panel.reset_user_explicit()

        # Call async metadata fetch (controller handles background thread execution)
        self._run_metadata_fetch(url)

    def _on_create_channel_rule(self, channel_id: str, channel_name: str):
        settings_dict = self.advanced_panel.get_settings_dict()
        # Keep clean patch: remove output_dir and transient fields
        keys_to_remove = ["cookies", "scheduler_time", "scheduler_enabled", "options_source"]
        for k in keys_to_remove:
            if k in settings_dict:
                del settings_dict[k]
                
        from core.history import save_channel_rule
        save_channel_rule(channel_id, channel_name, settings_dict)
        
        lang = self.app_state.current_lang
        msg = f"Kanal kuralı kaydedildi: {channel_name}" if lang == "tr" else (f"Regla de canal guardada: {channel_name}" if lang == "es" else f"Channel rule saved: {channel_name}")
        self.progress_panel.append_log_batch([f"[Kanal Kuralı] {msg}\n"])
        messagebox.showinfo("Başarılı" if lang == "tr" else ("Éxito" if lang == "es" else "Success"), msg)

    def _run_metadata_fetch(self, url: str) -> None:
        settings = self.advanced_panel.get_settings_dict()
        cookies_file = settings.get("cookies", "").strip()
        browser_cookies = settings.get("browser_cookies", "").strip().lower()

        def on_success(metadata):
            local_thumb_img = None
            thumb_path = metadata.get("thumbnail_path")
            if thumb_path:
                try:
                    with Image.open(thumb_path) as pil_img:
                        resized_ui = pil_img.resize((160, 90), Image.Resampling.LANCZOS).copy()
                    local_thumb_img = ctk.CTkImage(light_image=resized_ui, dark_image=resized_ui, size=(160, 90))
                except Exception as e:
                    print(f"Error loading thumbnail in UI: {e}")

            fetched_metadata = {
                "url": url,
                "title": metadata["title"],
                "uploader": metadata["uploader"],
                "duration": metadata["duration"],
                "thumbnail_img": local_thumb_img,
                "chapters": metadata["chapters"],
                "filesize": metadata["filesize"],
                "filesize_approx": metadata["filesize_approx"],
                "channel_id": metadata["channel_id"],
                "channel_name": metadata["channel_name"]
            }
            self.ui_queue.put(("metadata_ready", fetched_metadata))

        def on_error(err_str):
            print(f"[!] Metadata fetch failed: {err_str}")
            self.ui_queue.put(("metadata_error", err_str))

        from core.history import get_app_data_dir
        self.controller.run_metadata_fetch(
            url=url,
            cookies_file=cookies_file,
            browser_cookies=browser_cookies,
            scratch_dir=self.scratch_dir,
            app_data_dir=get_app_data_dir(),
            on_success_callback=on_success,
            on_error_callback=on_error
        )

    def _on_chapter_clicked(self, start_seconds: float, end_seconds: float, chapter_title: str):
        # Feature 3.4 Chapters auto-clipping selection integration directly inside PreviewPanel
        self.preview_panel.clip_enabled_var.set(True)
        self.preview_panel._on_clip_toggled()
        self.preview_panel.add_clip_row(start_seconds, end_seconds)

    def _on_preset_applied(self):
        # Refresh current profile preview hint
        pass

    # extract_video_id is unused in MainWindow and now imported from core.utils where needed

    def _add_to_queue(self) -> None:
        # Synchronize app_state.url with the UI before queueing to avoid empty/stale values
        if self.url_panel.batch_mode_var.get():
            lines = self.url_panel.url_textbox.get("1.0", "end-1c").splitlines()
            self.app_state.batch_urls = [l.strip() for l in lines if l.strip()]
            self.app_state.url = self.app_state.batch_urls[0] if self.app_state.batch_urls else ""
        else:
            self.app_state.url = self.url_panel.url_entry.get().strip()

        url = self.app_state.url.strip()
        if not url:
            messagebox.showwarning(TRANSLATIONS[self.app_state.current_lang]["lbl_dialog_warning_title"], TRANSLATIONS[self.app_state.current_lang]["lbl_dialog_warning_url"])
            return

        lang = self.app_state.current_lang
        item_cfg = self.advanced_panel.get_settings_dict()

        # 1. Check for duplicates using Controller
        is_duplicate, dup_title, dup_format = self.controller.check_duplicate(url, item_cfg)
        if is_duplicate:
            title_msg = TRANSLATIONS[lang]["lbl_duplicate_title"]
            body_template = TRANSLATIONS[lang]["lbl_duplicate_body"]
            body_msg = body_template.replace("{title}", dup_title).replace("{format}", dup_format)
            confirm = messagebox.askyesno(title_msg, body_msg)
            if not confirm:
                return

        # 2. Merge clipping parameters directly from PreviewPanel if not in batch mode
        if not self.app_state.is_batch_mode:
            item_cfg.update(self.preview_panel.get_clip_settings())
        else:
            item_cfg.update({
                "clip_enabled": False,
                "clip_start": "00:00",
                "clip_end": "00:00",
                "clip_precise": False,
                "export_profile": "Default (No Profile)"
            })

        # 3. Prepare multi-clip selections
        if item_cfg.get("clip_enabled") and not self.app_state.is_batch_mode:
            multi_clips = self.preview_panel.get_multi_clips()
        else:
            multi_clips = []

        # Ensure current thumbnail path is passed to task config
        item_cfg["thumbnail_path"] = getattr(self.app_state, "current_thumbnail_path", None)

        # 4. Delegate task creation and state append to Controller
        success, error, added_count = self.controller.validate_and_add_tasks(url, item_cfg, multi_clips, lang)
        
        if success:
            if self.app_state.is_batch_mode:
                self.url_panel.set_url("")
                self.progress_panel.update_status("●", THEME_ACCENT_BLUE, TRANSLATIONS[self.app_state.current_lang]["lbl_status_added"].format(count=added_count))
            else:
                self.url_panel.set_url("")
                self.preview_panel.hide()
                self.progress_panel.update_status("●", THEME_ACCENT_BLUE, TRANSLATIONS[self.app_state.current_lang]["lbl_status_ready"])
            
            # Post updates to progress panel if automated rules were applied
            if item_cfg.get("options_source") == "Default" and self.app_state.current_video_info and not self.app_state.is_batch_mode:
                ch_id = self.app_state.current_video_info.get("channel_id")
                if ch_id:
                    rule = get_channel_rule(ch_id)
                    if rule and rule.get("settings_dict"):
                        ch_name = rule.get("channel_name") or ch_id
                        msg = f"[Kanal Kuralı] {ch_name} için otomatik kural uygulandı.\n"
                        self.progress_panel.append_log_batch([msg])
        else:
            messagebox.showwarning(TRANSLATIONS[self.app_state.current_lang]["lbl_dialog_warning_title"], error)

        self.queue_panel.update_list()

    def _remove_from_queue(self, idx: int):
        with self.app_state._lock:
            if idx >= 0 and idx < len(self.app_state.queue_list):
                item = self.app_state.queue_list[idx]
                # Don't delete active downloading item
                if item.status_code == TaskStatus.DOWNLOADING:
                    return
                del self.app_state.queue_list[idx]
        self.queue_panel.update_list()

    def _cancel_single_task(self, task_id: str):
        with self.app_state._lock:
            for task in self.app_state.queue_list:
                if task.id == task_id:
                    task.cancel_event.set()
                    proc = getattr(task, "_process", None)
                    if proc:
                        try:
                            if getattr(task, "is_paused", False):
                                if os.name == 'nt':
                                    import ctypes
                                    ctypes.windll.ntdll.NtResumeProcess(proc._handle)
                                else:
                                    import signal
                                    os.kill(proc.pid, signal.SIGCONT)
                                task.is_paused = False
                            proc.terminate()
                        except Exception:
                            pass
                    lang = self.app_state.current_lang
                    task.status = "İptal Ediliyor" if lang == "tr" else ("Cancelando" if lang == "es" else "Cancelling")
                    task.status_code = TaskStatus.CANCELLED
                    self.queue_panel.update_list()
                    break

    def _redownload_historic_item(self, url: str, format_desc: str):
        # Feature 3.2: Re-download callback
        self.url_panel.set_url(url)
        self.app_state.url = url
        # Toggle mode based on history format description via Controller
        mode = self.controller.get_mode_from_format(format_desc)
        self.advanced_panel.mode_var.set(mode)
        self.advanced_panel._on_mode_changed(mode)
        
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

        # Synchronize app_state.url with the UI before starting to avoid empty/stale values
        if self.url_panel.batch_mode_var.get():
            lines = self.url_panel.url_textbox.get("1.0", "end-1c").splitlines()
            self.app_state.batch_urls = [l.strip() for l in lines if l.strip()]
            self.app_state.url = self.app_state.batch_urls[0] if self.app_state.batch_urls else ""
        else:
            self.app_state.url = self.url_panel.url_entry.get().strip()

        # Auto queue URL input if queue list empty
        if not self.app_state.queue_list:
            url = self.app_state.url.strip()
            if url:
                self._add_to_queue()
                if not self.app_state.queue_list:
                    return
            else:
                messagebox.showwarning(TRANSLATIONS[self.app_state.current_lang]["lbl_dialog_warning_title"], TRANSLATIONS[self.app_state.current_lang]["lbl_dialog_warning_url"])
                return

        self.cancel_event.clear()
        self.app_state.current_item_index = 0
        self.progress_panel.set_running_state(True)
        
        # Check if local schedule is active
        if self.advanced_panel.scheduler_enabled_var.get():
            time_str = self.advanced_panel.schedule_time_var.get().strip()
            threading.Thread(target=self._run_scheduler_wait_loop, args=(time_str,), daemon=True, name="scheduler-wait-loop").start()
        else:
            # Spawn queue background execution worker thread
            threading.Thread(target=run_queue_executor, args=(self.app_state, self.ui_queue, self.cancel_event), daemon=True, name="queue-executor").start()

    def _run_scheduler_wait_loop(self, target_time_str: str) -> None:
        lang = self.app_state.current_lang
        try:
            parts = target_time_str.split(":")
            hour = int(parts[0])
            minute = int(parts[1])
        except Exception:
            self.ui_queue.put(("log", f"[Zamanlayıcı] Hata: Geçersiz zaman formatı '{target_time_str}'. Lütfen SS:DD formatında girin.\n"))
            self.ui_queue.put(("status", ("●", "#ef4444", "Hata: Geçersiz Zaman")))
            return

        self.ui_queue.put(("log", f"[Zamanlayıcı] İndirme zamanlandı: İndirmeler saat {target_time_str} olduğunda başlayacak.\n"))
        
        # Windows sleep prevention during countdown
        from core.downloader import prevent_sleep, allow_sleep
        prevent_sleep()
        
        try:
            while not self.cancel_event.is_set():
                now = datetime.datetime.now()
                if now.hour == hour and now.minute == minute:
                    self.ui_queue.put(("log", "[Zamanlayıcı] Hedef saate ulaşıldı! İndirmeler başlatılıyor...\n"))
                    self.cancel_event.clear()
                    self.app_state.current_item_index = 0
                    threading.Thread(target=run_queue_executor, args=(self.app_state, self.ui_queue, self.cancel_event), daemon=True, name="queue-executor").start()
                    break
                
                target_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if target_dt < now:
                    target_dt += datetime.timedelta(days=1)
                remaining = int((target_dt - now).total_seconds())
                
                h = remaining // 3600
                m = (remaining % 3600) // 60
                s = remaining % 60
                countdown_msg = f"{h:02d}:{m:02d}:{s:02d}"
                status_text = f"Zamanlandı: {target_time_str} (Kalan: {countdown_msg})"
                
                self.ui_queue.put(("status", ("⏰", "#4f46e5", status_text)))
                time.sleep(1.0)
        finally:
            allow_sleep()

    def _cancel_download(self):
        self.cancel_event.set()
        with self.app_state._lock:
            for task in self.app_state.queue_list:
                task.cancel_event.set()
        kill_all_active_subprocesses()
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
    # ================== METRIC DRAINING & LIFECYCLE ==================
    def _drain_ui_queue(self) -> None:
        try:
            self._drain_ui_queue_impl()
        except Exception as e:
            import logging
            logging.error(f"[UI Queue Drainer] Fatal error: {e}", exc_info=True)
        finally:
            self.after(50, self._drain_ui_queue)

    def _drain_ui_queue_impl(self) -> None:
        processed = 0
        log_batch = []
        needs_progress_update = False
        needs_active_file_update = False
        while processed < 100:
            try:
                kind, payload = self.ui_queue.get_nowait()
            except queue.Empty:
                break
            processed += 1

            if kind == "log":
                log_batch.append(str(payload))
            elif kind == "stats":
                stats = payload
                task_id = stats["task_id"]
                percent_val = float(stats["percent"])
                
                # Find and update task model
                for t in self.app_state.queue_list:
                    if t.id == task_id:
                        t.percent = percent_val
                        t.size = stats["size"]
                        t.speed = stats["speed"]
                        t.eta = stats["eta"]
                        break

                # Update the task progress dynamically in the card list without redrawing
                self.queue_panel.update_task_progress(
                    task_id=task_id,
                    percent=percent_val,
                    speed=stats["speed"],
                    eta=stats["eta"],
                    size=stats["size"]
                )

                needs_progress_update = True

            elif kind == "active_file":
                task_id, filename = payload
                for t in self.app_state.queue_list:
                    if t.id == task_id:
                        t.active_filename = filename
                        break
                needs_active_file_update = True
            elif kind == "percent_complete":
                pass # Handled by update_global_progress
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
                self._show_toast(TRANSLATIONS[self.app_state.current_lang]["lbl_toast_outdated_title"], TRANSLATIONS[self.app_state.current_lang]["lbl_toast_outdated_desc"])
            elif kind == "toast_success":
                from ui.components.toast import ActionableToast
                data = payload
                title_text = data.get("title", "Video")
                file_path = data.get("file_path", "")
                
                lang = self.app_state.current_lang
                desc_text = TRANSLATIONS[lang]["lbl_toast_success_desc"].format(title=title_text)
                
                if file_path and os.path.exists(file_path):
                    ActionableToast(
                        self,
                        title="İndirme Tamamlandı!" if lang == "tr" else ("¡Descarga Completada!" if lang == "es" else "Download Completed!"),
                        file_path=file_path
                    )
                else:
                    self._show_toast(TRANSLATIONS[lang]["lbl_toast_success_title"], desc_text)
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
                    self.progress_panel.show_completion_animation(success=False)
                else:
                    self.progress_panel.update_status("●", THEME_ACCENT_GREEN, TRANSLATIONS[self.app_state.current_lang]["lbl_status_completed"])
                    self.progress_panel.show_completion_animation(success=True)
                    self._show_toast(TRANSLATIONS[self.app_state.current_lang]["lbl_toast_all_title"], TRANSLATIONS[self.app_state.current_lang]["lbl_toast_all_desc"])

        # Coalesced UI updates — called at most once per drain cycle
        if needs_progress_update:
            self.progress_panel.update_global_progress(self.app_state.queue_list)

        if needs_active_file_update:
            active_tasks = [t for t in self.app_state.queue_list if t.status_code == TaskStatus.DOWNLOADING]
            if active_tasks:
                titles = ", ".join(t.title[:15] + "..." for t in active_tasks)
                self.progress_panel.active_file_var.set(f"Aktif İndirmeler: {titles}")

        if log_batch:
            self.progress_panel.append_log_batch(log_batch)

    def _show_toast(self, title: str, desc: str):
        from ui.components.toast import NotificationToast
        NotificationToast(self, title, desc)

    def _toggle_theme_mode(self):
        if self.app_state.current_theme == "Dark":
            self.app_state.current_theme = "Light"
            ctk.set_appearance_mode("Light")
            self.theme_btn.configure(text=TRANSLATIONS[self.app_state.current_lang]["theme_light"])
        else:
            self.app_state.current_theme = "Dark"
            ctk.set_appearance_mode("Dark")
            self.theme_btn.configure(text=TRANSLATIONS[self.app_state.current_lang]["theme_dark"])
        
        # Redraw standard tk.Canvas elements to reflect theme changes instantly
        if hasattr(self, "progress_panel"):
            self.progress_panel.draw_progress()
            self.progress_panel._redraw_sparkline()
        if hasattr(self, "preview_panel"):
            self.preview_panel.draw_sponsor_overlay()

    def _toggle_language(self, choice: str):
        LANG_MAP = {
            "türkçe": "tr",
            "english": "en",
            "español": "es",
            "tr": "tr",
            "en": "en",
            "es": "es"
        }
        self.app_state.current_lang = LANG_MAP.get(choice.lower(), "en")
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

        # Update compact mode state and button text translations
        self._apply_compact_mode()

    def _toggle_compact_mode(self):
        # Toggle preference
        self.app_state.preferences.compact_mode = not self.app_state.preferences.compact_mode
        # Save preference immediately
        from core.app_state import save_app_preferences
        save_app_preferences(self.app_state.preferences)
        # Apply change visually
        self._apply_compact_mode()

    def _apply_compact_mode(self):
        is_compact = self.app_state.preferences.compact_mode
        lang = self.app_state.current_lang

        if is_compact:
            self.advanced_panel.grid_remove()
            txt = TRANSLATIONS[lang].get("btn_compact_mode_expanded", "⚙️ Advanced")
        else:
            self.advanced_panel.grid(row=2, column=0, padx=4, pady=6, sticky="ew")
            txt = TRANSLATIONS[lang].get("btn_compact_mode_compact", "⚡ Compact")

        if hasattr(self, "btn_compact_mode"):
            self.btn_compact_mode.configure(text=txt)

    def _on_update_found(self, payload):
        # Schedule the UI configuration inside the safe main event loop
        self.after(0, lambda: self._show_update_badge(payload))

    def _show_update_badge(self, payload):
        self.active_update_payload = payload
        lang = self.app_state.current_lang
        
        if payload.action == "downgrade":
            btn_text = f"⚠️ Sürüm Düşür / Downgrade Core (v{payload.latest_version})" if lang == "tr" else f"⚠️ Downgrade Core / Sürüm Düşür (v{payload.latest_version})"
        else:
            btn_text = f"🚀 Motoru Güncelle / Update Core (v{payload.latest_version})" if lang == "tr" else f"🚀 Update Core / Motoru Güncelle (v{payload.latest_version})"
            
        self.btn_update_warning.configure(text=btn_text)
        self.btn_update_warning.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 16), sticky="ew")

    def perform_update(self):
        lang = self.app_state.current_lang
        payload = getattr(self, "active_update_payload", None)
        
        if not payload:
            return
            
        status_text = "Güncelleniyor... Lütfen bekleyin." if lang == "tr" else "Upgrading... Please wait."
        self.btn_update_warning.configure(text=status_text, state="disabled")
        
        import threading
        from core.updater import execute_update
        
        def _run():
            success, msg = execute_update(payload, str(self.scratch_dir))
            self.after(0, lambda: self._on_upgrade_complete(success, msg))
            
        threading.Thread(target=_run, daemon=True, name="self-updater").start()

    def _on_upgrade_complete(self, success: bool, message: str = ""):
        lang = self.app_state.current_lang
        if success:
            success_text = "Güncelleme Tamamlandı! Yeniden Başlatın." if lang == "tr" else "Upgrade Finished! Please Restart."
            fg_color = "#10b981"
        else:
            if "Güvenlik İhlali" in message or "Security Breach" in message:
                success_text = "Güvenlik Engeli: SHA-256 Eşleşmedi!" if lang == "tr" else "Security Block: Hash Mismatch!"
            else:
                success_text = "Güncelleme Başarısız!" if lang == "tr" else "Upgrade Failed!"
            fg_color = "#f43f5e"
            print(f"[Updater] Upgrade failed with message: {message}")
            
        self.btn_update_warning.configure(
            text=success_text,
            state="disabled",
            fg_color=fg_color
        )

    def _on_close(self):
        if self.app_state.is_executor_running:
            if not messagebox.askyesno(TRANSLATIONS[self.app_state.current_lang]["lbl_dialog_close_title"], TRANSLATIONS[self.app_state.current_lang]["lbl_dialog_close_desc"]):
                return
            self._cancel_download()
        
        # Absolute guarantee that no zombie ffmpeg threads survive
        try:
            kill_all_active_subprocesses()
        except Exception:
            pass

        try:
            shutdown_db()
        except Exception:
            pass
            
        try:
            shutil.rmtree(self.scratch_dir, ignore_errors=True)
        except Exception:
            pass

        self.destroy()
