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
from core.clip import decide_clip_strategy, parse_time_to_seconds, format_seconds_to_mmss

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
        self.geometry("680x880")
        self.resizable(True, True)
        self.minsize(680, 850)
        
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
        
        # Start PyPI update checker silently in background
        from core.updater import UpdateChecker
        self.updater = UpdateChecker(ui_callback=self._on_update_found)
        self.updater.check_in_background()

        # Start the async UI metric queue draining loop
        self._drain_ui_queue()

        # Check and prompt to install JS runtime Deno dynamically after a 2-second UI load buffer
        self.after(2000, self._check_and_prompt_deno)

    def _check_and_prompt_deno(self) -> None:
        import shutil
        from core.env import refresh_path_env
        
        refresh_path_env()
        if shutil.which('deno') or shutil.which('node'):
            return  # Already installed!
            
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
        
        from tkinter import messagebox
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
                    
            threading.Thread(target=installer_thread, daemon=True).start()

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
            # 1. Dynamically refresh PATH to pick up newly installed runtimes like Deno without rebooting
            from core.env import refresh_path_env
            refresh_path_env()

            import yt_dlp
            
            # 2. Extract current cookie settings from AdvancedPanel to support private or throttled videos
            settings = self.advanced_panel.get_settings_dict()
            cookies_file = settings.get("cookies", "").strip()
            browser_cookies = settings.get("browser_cookies", "").strip().lower()

            # We skip downloading, but extract full details (including chapters and formats)
            ydl_opts = {
                'skip_download': True,
                'quiet': True,
                'no_warnings': True,
            }
            
            if cookies_file:
                ydl_opts['cookiefile'] = cookies_file
            elif browser_cookies and browser_cookies not in ("kapali", "disabled", "off", "closed", "none"):
                ydl_opts['cookiesfrombrowser'] = (browser_cookies,)

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
        # Feature 3.4 Chapters auto-clipping selection integration directly inside PreviewPanel
        self.preview_panel.clip_enabled_var.set(True)
        self.preview_panel._on_clip_toggled()
        self.preview_panel.add_clip_row(start_seconds, end_seconds)

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
        
        # Merge clipping parameters directly from PreviewPanel if not in batch mode
        if not self.app_state.is_batch_mode:
            item_cfg.update(self.preview_panel.get_clip_settings())
        else:
            # Batch mode does not support active single-video clipping parameters
            item_cfg.update({
                "clip_enabled": False,
                "clip_start": "00:00",
                "clip_end": "00:00",
                "clip_precise": False,
                "export_profile": "Default (No Profile)"
            })
            
        # If clipping is enabled, check for export profiles duration boundaries
        if item_cfg.get("clip_enabled") and not self.app_state.is_batch_mode:
            from core.profiles import EXPORT_PROFILES
            
            multi_clips = self.preview_panel.get_multi_clips()
            for mc_cfg in multi_clips:
                profile_name = mc_cfg.get("profile", "Default (No Profile)")
                profile = EXPORT_PROFILES.get(profile_name)
                diff = mc_cfg["end"] - mc_cfg["start"]
                
                if profile and profile.max_duration and diff > profile.max_duration:
                    error_msg = (
                        f"Seçilen kırpma süresi ({diff:.1f}s), '{profile.name}' profilinin "
                        f"maksimum sınırını ({profile.max_duration}s) aşıyor! Lütfen süreyi kısaltın."
                        if lang == "tr"
                        else (
                            f"El tiempo seleccionado ({diff:.1f}s) supera el límite máximo "
                            f"del perfil '{profile.name}' ({profile.max_duration}s). Por favor acórtelo."
                            if lang == "es"
                            else f"Selected clip duration ({diff:.1f}s) exceeds '{profile.name}' "
                                 f"profile maximum limit ({profile.max_duration}s)! Please shorten the clip."
                        )
                    )
                    messagebox.showwarning(TRANSLATIONS[self.app_state.current_lang]["lbl_dialog_warning_title"], error_msg)
                    return
        
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
            title_base = self.app_state.current_video_info.get("title", "Video Title") if self.app_state.current_video_info else "Downloading video"
            duration_total = self.app_state.current_video_info.get("duration", 0) if self.app_state.current_video_info else 0
            duration = format_seconds_to_mmss(duration_total)
            
            # Check if Multi-Clip is active
            multi_clips = self.preview_panel.get_multi_clips()
            if multi_clips:
                from core.clip import MicroClip, optimize_clip_intervals
                micro_list = []
                for i, c in enumerate(multi_clips):
                    micro_list.append(MicroClip(
                        id=f"clip_{i+1}",
                        start=c["start"],
                        end=c["end"],
                        export_profile=c["profile"],
                        output_name=f"_clip{i+1}"
                    ))
                
                # LeetCode 56 Greedy Merging (threshold of 30s)
                macro_list = optimize_clip_intervals(micro_list, threshold_sec=30.0)
                
                added_count = 0
                for idx_macro, macro in enumerate(macro_list):
                    item_id = hashlib.md5(f"{url}_{idx_macro}_{macro.start}_{macro.end}".encode()).hexdigest()
                    macro_start_str = format_seconds_to_mmss(macro.start)
                    macro_end_str = format_seconds_to_mmss(macro.end)
                    
                    macro_item = {
                        "id": item_id,
                        "url": url,
                        "preset": item_cfg.get("video_profile", "Custom"),
                        "status": "Bekliyor" if lang == "tr" else ("Esperando" if lang == "es" else "Waiting"),
                        "video_info": self.app_state.current_video_info,  # Inject cached video_info for --load-info-json
                        "merge_clips": self.preview_panel.merge_clips_var.get()
                    }
                    macro_item.update(item_cfg)
                    
                    if len(macro.micro_clips) > 1:
                        macro_item.update({
                            "title": f"{title_base} [Macro Clip {idx_macro+1}]",
                            "duration": format_seconds_to_mmss(macro.end - macro.start),
                            "clip_enabled": True,
                            "clip_start": macro_start_str,
                            "clip_end": macro_end_str,
                            "clip_strategy": decide_clip_strategy(self.app_state.current_video_info, macro.start, macro.end),
                            "macro_clips_data": [
                                {
                                    "start": mc.start,
                                    "end": mc.end,
                                    "profile": mc.export_profile,
                                    "output_suffix": mc.output_name
                                }
                                for mc in macro.micro_clips
                            ]
                        })
                    else:
                        mc = macro.micro_clips[0]
                        macro_item.update({
                            "title": f"{title_base} (Clip {mc.id})",
                            "duration": format_seconds_to_mmss(mc.end - mc.start),
                            "clip_enabled": True,
                            "clip_start": format_seconds_to_mmss(mc.start),
                            "clip_end": format_seconds_to_mmss(mc.end),
                            "clip_strategy": decide_clip_strategy(self.app_state.current_video_info, mc.start, mc.end),
                            "export_profile": mc.export_profile,
                        })
                    
                    self.app_state.queue_list.append(macro_item)
                    added_count += 1
                
                self.url_panel.set_url("")
                self.preview_panel.hide()
                self.progress_panel.update_status("●", THEME_ACCENT_BLUE, TRANSLATIONS[self.app_state.current_lang]["lbl_status_added"].format(count=added_count))
            else:
                # Normal single item or clipping off
                item_id = hashlib.md5(url.encode()).hexdigest()
                item = {
                    "id": item_id,
                    "url": url,
                    "title": title_base,
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

    def _on_update_found(self, current, latest):
        # Schedule the UI configuration inside the safe main event loop
        self.after(0, lambda: self._show_update_badge(current, latest))

    def _show_update_badge(self, current, latest):
        lang = self.app_state.current_lang
        btn_text = f"🚀 Motoru Güncelle / Update Core (v{latest})" if lang == "tr" else f"🚀 Update Core / Motoru Güncelle (v{latest})"
        self.btn_update_warning.configure(text=btn_text)
        self.btn_update_warning.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 16), sticky="ew")

    def perform_update(self):
        lang = self.app_state.current_lang
        status_text = "Güncelleniyor... Lütfen bekleyin." if lang == "tr" else "Upgrading... Please wait."
        self.btn_update_warning.configure(text=status_text, state="disabled")
        
        import subprocess
        import sys
        
        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NO_WINDOW
            
        # Launch ghost upgrade subprocess without flashing black command windows
        subprocess.Popen(
            [sys.executable, "-m", "pip", "install", "-U", "yt-dlp"],
            creationflags=creationflags
        )
        
        # Schedule visual callback in 6 seconds
        self.after(6000, self._on_upgrade_complete)

    def _on_upgrade_complete(self):
        lang = self.app_state.current_lang
        success_text = "Güncelleme Tamamlandı! Yeniden Başlatın." if lang == "tr" else "Upgrade Finished! Please Restart."
        self.btn_update_warning.configure(
            text=success_text,
            state="disabled",
            fg_color="#10b981"
        )

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
