# ui/panels/advanced_panel.py
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from ui.theme import (
    THEME_BG, THEME_CARD_BG, THEME_CARD_BORDER, THEME_TEXT_PRIMARY,
    THEME_TEXT_SECONDARY, THEME_ACCENT_BLUE, THEME_ACCENT_INDIGO,
    THEME_ACCENT_RED, TRANSLATIONS
)
from core.app_state import AppState
from core.presets import load_presets, save_preset, delete_preset
from core.clip import validate_clip_range, format_seconds_to_mmss

class AdvancedPanel(ctk.CTkFrame):
    def __init__(self, parent, state: AppState, on_preset_load_callback=None, **kwargs):
        super().__init__(
            parent,
            fg_color=THEME_CARD_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            corner_radius=16,
            **kwargs
        )
        self.app_state = state
        self.on_preset_loaded = on_preset_load_callback
        
        self.grid_columnconfigure(0, weight=1)
        self._build_ui()
        self._load_presets_dropdown()

    def _build_ui(self):
        lang = self.app_state.current_lang

        # Tabview Integration
        self.tabview = ctk.CTkTabview(
            self,
            height=280,
            corner_radius=12,
            fg_color=THEME_CARD_BG,
            segmented_button_selected_color=THEME_ACCENT_INDIGO,
            segmented_button_selected_hover_color=THEME_ACCENT_BLUE,
            segmented_button_unselected_color=THEME_BG,
            segmented_button_unselected_hover_color=THEME_CARD_BORDER,
            text_color=THEME_TEXT_PRIMARY,
        )
        self.tabview.grid(row=0, column=0, padx=16, pady=12, sticky="nsew")

        self.tab_codec = self.tabview.add(TRANSLATIONS[lang]["tab_codecs"])
        self.tab_limits = self.tabview.add(TRANSLATIONS[lang]["tab_limits"])
        self.tab_flags = self.tabview.add(TRANSLATIONS[lang]["tab_flags"])

        # ==================== TAB 1: RESOLUTION & CODECS ====================
        self.tab_codec.grid_columnconfigure((0, 1), weight=1)

        c1 = ctk.CTkFrame(self.tab_codec, fg_color="transparent")
        c1.grid(row=0, column=0, padx=10, pady=8, sticky="nsew")
        c1.grid_columnconfigure(1, weight=1)

        self.lbl_mode = ctk.CTkLabel(c1, text=TRANSLATIONS[lang]["lbl_mode"], text_color=THEME_TEXT_PRIMARY)
        self.lbl_mode.grid(row=0, column=0, sticky="w", padx=6, pady=6)
        
        self.mode_var = ctk.StringVar(value=self.app_state.active_profile if self.app_state.active_profile == "Audio" else "Video")
        self.mode_switch = ctk.CTkSegmentedButton(
            c1,
            values=["Video", "Audio"],
            variable=self.mode_var,
            selected_color=THEME_ACCENT_INDIGO,
            unselected_color=THEME_BG,
            unselected_hover_color=THEME_CARD_BORDER,
            text_color=THEME_TEXT_PRIMARY,
            command=self._on_mode_changed,
        )
        self.mode_switch.grid(row=0, column=1, sticky="ew", padx=6, pady=6)

        self.lbl_profile = ctk.CTkLabel(c1, text=TRANSLATIONS[lang]["lbl_profile"], text_color=THEME_TEXT_PRIMARY)
        self.lbl_profile.grid(row=1, column=0, sticky="w", padx=6, pady=6)
        
        self.video_profile_var = ctk.StringVar(value="Full HD (1080p)")
        self.video_profile_menu = ctk.CTkOptionMenu(
            c1,
            values=["Maksimum (Best)", "Ultra HD (2160p)", "QHD (1440p)", "Full HD (1080p)", "Dengeli (720p)", "Hizli (480p)", "Ekonomi (360p)", "Ozel (Custom)"],
            variable=self.video_profile_var,
            fg_color=THEME_BG,
            button_color=THEME_BG,
            button_hover_color=THEME_CARD_BORDER,
            text_color=THEME_TEXT_PRIMARY,
            dropdown_fg_color=THEME_CARD_BG,
            dropdown_hover_color=THEME_CARD_BORDER,
            dropdown_text_color=THEME_TEXT_PRIMARY,
            command=self._on_video_profile_changed,
        )
        self.video_profile_menu.grid(row=1, column=1, sticky="ew", padx=6, pady=6)

        self.lbl_max_res = ctk.CTkLabel(c1, text=TRANSLATIONS[lang]["lbl_max_res"], text_color=THEME_TEXT_PRIMARY)
        self.lbl_max_res.grid(row=2, column=0, sticky="w", padx=6, pady=6)
        
        self.custom_video_height_var = ctk.StringVar(value="1080")
        self.video_limit_menu = ctk.CTkOptionMenu(
            c1,
            values=["2160", "1440", "1080", "720", "480", "360"],
            variable=self.custom_video_height_var,
            fg_color=THEME_BG,
            button_color=THEME_BG,
            button_hover_color=THEME_CARD_BORDER,
            text_color=THEME_TEXT_PRIMARY,
            dropdown_fg_color=THEME_CARD_BG,
            dropdown_hover_color=THEME_CARD_BORDER,
            dropdown_text_color=THEME_TEXT_PRIMARY,
        )
        self.video_limit_menu.grid(row=2, column=1, sticky="ew", padx=6, pady=6)

        c2 = ctk.CTkFrame(self.tab_codec, fg_color="transparent")
        c2.grid(row=0, column=1, padx=10, pady=8, sticky="nsew")
        c2.grid_columnconfigure(1, weight=1)

        self.lbl_format = ctk.CTkLabel(c2, text=TRANSLATIONS[lang]["lbl_format"], text_color=THEME_TEXT_PRIMARY)
        self.lbl_format.grid(row=0, column=0, sticky="w", padx=6, pady=6)
        
        self.video_container_var = ctk.StringVar(value="mp4")
        self.video_container_menu = ctk.CTkOptionMenu(
            c2,
            values=["mp4", "mkv", "webm"],
            variable=self.video_container_var,
            fg_color=THEME_BG,
            button_color=THEME_BG,
            button_hover_color=THEME_CARD_BORDER,
            text_color=THEME_TEXT_PRIMARY,
            dropdown_fg_color=THEME_CARD_BG,
            dropdown_hover_color=THEME_CARD_BORDER,
            dropdown_text_color=THEME_TEXT_PRIMARY,
        )
        self.video_container_menu.grid(row=0, column=1, sticky="ew", padx=6, pady=6)

        self.lbl_audio_ext = ctk.CTkLabel(c2, text=TRANSLATIONS[lang]["lbl_audio_ext"], text_color=THEME_TEXT_PRIMARY)
        self.lbl_audio_ext.grid(row=1, column=0, sticky="w", padx=6, pady=6)
        
        self.audio_format_var = ctk.StringVar(value="mp3")
        self.audio_format_menu = ctk.CTkOptionMenu(
            c2,
            values=["mp3", "aac", "opus", "m4a", "wav", "flac"],
            variable=self.audio_format_var,
            fg_color=THEME_BG,
            button_color=THEME_BG,
            button_hover_color=THEME_CARD_BORDER,
            text_color=THEME_TEXT_PRIMARY,
            dropdown_fg_color=THEME_CARD_BG,
            dropdown_hover_color=THEME_CARD_BORDER,
            dropdown_text_color=THEME_TEXT_PRIMARY,
        )
        self.audio_format_menu.grid(row=1, column=1, sticky="ew", padx=6, pady=6)

        self.lbl_audio_qual = ctk.CTkLabel(c2, text=TRANSLATIONS[lang]["lbl_audio_qual"], text_color=THEME_TEXT_PRIMARY)
        self.lbl_audio_qual.grid(row=2, column=0, sticky="w", padx=6, pady=6)
        
        self.audio_quality_var = ctk.StringVar(value="Dengeli (192K)")
        self.audio_quality_menu = ctk.CTkOptionMenu(
            c2,
            values=["Best", "Yuksek (320K)", "Dengeli (192K)", "Kucuk Boyut (128K)"],
            variable=self.audio_quality_var,
            fg_color=THEME_BG,
            button_color=THEME_BG,
            button_hover_color=THEME_CARD_BORDER,
            text_color=THEME_TEXT_PRIMARY,
            dropdown_fg_color=THEME_CARD_BG,
            dropdown_hover_color=THEME_CARD_BORDER,
            dropdown_text_color=THEME_TEXT_PRIMARY,
        )
        self.audio_quality_menu.grid(row=2, column=1, sticky="ew", padx=6, pady=6)

        self.video_audio_codec_lbl = ctk.CTkLabel(c2, text=TRANSLATIONS[lang]["lbl_audio_codec"], text_color=THEME_TEXT_PRIMARY)
        self.video_audio_codec_lbl.grid(row=3, column=0, sticky="w", padx=6, pady=6)

        self.video_audio_codec_var = ctk.StringVar(value="AAC")
        self.video_audio_codec_menu = ctk.CTkOptionMenu(
            c2,
            values=["AAC", "OPUS (OPEC)"],
            variable=self.video_audio_codec_var,
            fg_color=THEME_BG,
            button_color=THEME_BG,
            button_hover_color=THEME_CARD_BORDER,
            text_color=THEME_TEXT_PRIMARY,
            dropdown_fg_color=THEME_CARD_BG,
            dropdown_hover_color=THEME_CARD_BORDER,
            dropdown_text_color=THEME_TEXT_PRIMARY,
        )
        self.video_audio_codec_menu.grid(row=3, column=1, sticky="ew", padx=6, pady=6)

        # ==================== TAB 2: LIMITS & COOKIES ====================
        self.tab_limits.grid_columnconfigure((0, 1), weight=1)

        l1 = ctk.CTkFrame(self.tab_limits, fg_color="transparent")
        l1.grid(row=0, column=0, padx=10, pady=8, sticky="nsew")
        l1.grid_columnconfigure(1, weight=1)

        self.lbl_playlist_range = ctk.CTkLabel(l1, text=TRANSLATIONS[lang]["lbl_playlist_range"], text_color=THEME_TEXT_PRIMARY)
        self.lbl_playlist_range.grid(row=0, column=0, sticky="w", padx=6, pady=6)
        
        self.playlist_items_var = ctk.StringVar(value="")
        self.playlist_items_entry = ctk.CTkEntry(l1, textvariable=self.playlist_items_var, placeholder_text="Ex: 1-10, 15", height=30, fg_color=THEME_BG, border_color=THEME_CARD_BORDER, border_width=1, text_color=THEME_TEXT_PRIMARY)
        self.playlist_items_entry.grid(row=0, column=1, sticky="ew", padx=6, pady=6)

        self.lbl_max_dl = ctk.CTkLabel(l1, text=TRANSLATIONS[lang]["lbl_max_dl"], text_color=THEME_TEXT_PRIMARY)
        self.lbl_max_dl.grid(row=1, column=0, sticky="w", padx=6, pady=6)
        
        self.max_downloads_var = ctk.StringVar(value="")
        self.max_downloads_entry = ctk.CTkEntry(l1, textvariable=self.max_downloads_var, placeholder_text="Ex: 5", height=30, fg_color=THEME_BG, border_color=THEME_CARD_BORDER, border_width=1, text_color=THEME_TEXT_PRIMARY)
        self.max_downloads_entry.grid(row=1, column=1, sticky="ew", padx=6, pady=6)

        self.lbl_speed_limit = ctk.CTkLabel(l1, text=TRANSLATIONS[lang]["lbl_speed_limit"], text_color=THEME_TEXT_PRIMARY)
        self.lbl_speed_limit.grid(row=2, column=0, sticky="w", padx=6, pady=6)
        
        self.rate_limit_var = ctk.StringVar(value="")
        self.rate_limit_entry = ctk.CTkEntry(l1, textvariable=self.rate_limit_var, placeholder_text="Ex: 2M or 500K", height=30, fg_color=THEME_BG, border_color=THEME_CARD_BORDER, border_width=1, text_color=THEME_TEXT_PRIMARY)
        self.rate_limit_entry.grid(row=2, column=1, sticky="ew", padx=6, pady=6)

        l2 = ctk.CTkFrame(self.tab_limits, fg_color="transparent")
        l2.grid(row=0, column=1, padx=10, pady=8, sticky="nsew")
        l2.grid_columnconfigure(1, weight=1)

        self.lbl_cookie_file = ctk.CTkLabel(l2, text=TRANSLATIONS[lang]["lbl_cookie_file"], text_color=THEME_TEXT_PRIMARY)
        self.lbl_cookie_file.grid(row=0, column=0, sticky="w", padx=6, pady=6)
        
        cookies_row = ctk.CTkFrame(l2, fg_color="transparent")
        cookies_row.grid(row=0, column=1, sticky="ew", padx=6, pady=6)
        cookies_row.grid_columnconfigure(0, weight=1)
        
        self.cookies_var = ctk.StringVar(value="")
        self.cookies_entry = ctk.CTkEntry(cookies_row, textvariable=self.cookies_var, placeholder_text="Select path...", height=30, fg_color=THEME_BG, border_color=THEME_CARD_BORDER, border_width=1, text_color=THEME_TEXT_PRIMARY)
        self.cookies_entry.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        
        ctk.CTkButton(
            cookies_row,
            text="Sec" if lang == "tr" else "Select",
            width=50,
            height=30,
            fg_color=THEME_BG,
            text_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_CARD_BORDER,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            command=self._pick_cookies_file
        ).grid(row=0, column=1)

        self.lbl_browser_cookie = ctk.CTkLabel(l2, text=TRANSLATIONS[lang]["lbl_browser_cookie"], text_color=THEME_TEXT_PRIMARY)
        self.lbl_browser_cookie.grid(row=1, column=0, sticky="w", padx=6, pady=6)
        
        self.browser_cookies_var = ctk.StringVar(value="Kapali")
        self.browser_cookies_menu = ctk.CTkOptionMenu(
            l2,
            values=["Kapali", "chrome", "edge", "firefox", "brave", "opera", "vivaldi"],
            variable=self.browser_cookies_var,
            fg_color=THEME_BG,
            button_color=THEME_BG,
            button_hover_color=THEME_CARD_BORDER,
            text_color=THEME_TEXT_PRIMARY,
            dropdown_fg_color=THEME_CARD_BG,
            dropdown_hover_color=THEME_CARD_BORDER,
            dropdown_text_color=THEME_TEXT_PRIMARY,
            height=30
        )
        self.browser_cookies_menu.grid(row=1, column=1, sticky="ew", padx=6, pady=6)

        self.lbl_retry = ctk.CTkLabel(l2, text=TRANSLATIONS[lang]["lbl_retry"], text_color=THEME_TEXT_PRIMARY)
        self.lbl_retry.grid(row=2, column=0, sticky="w", padx=6, pady=6)
        
        self.retries_var = ctk.StringVar(value="")
        self.retries_entry = ctk.CTkEntry(l2, textvariable=self.retries_var, placeholder_text="Ex: 10", height=30, fg_color=THEME_BG, border_color=THEME_CARD_BORDER, border_width=1, text_color=THEME_TEXT_PRIMARY)
        self.retries_entry.grid(row=2, column=1, sticky="ew", padx=6, pady=6)

        # ==================== TAB 3: FLAGS & CHECKBOXES ====================
        self.tab_flags.grid_columnconfigure((0, 1), weight=1)

        f1 = ctk.CTkFrame(self.tab_flags, fg_color="transparent")
        f1.grid(row=0, column=0, padx=10, pady=4, sticky="nsew")
        
        self.lbl_header_addons = ctk.CTkLabel(f1, text=TRANSLATIONS[lang]["lbl_header_addons"], font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=THEME_ACCENT_BLUE)
        self.lbl_header_addons.grid(row=0, column=0, sticky="w", padx=6, pady=2)

        self.thumbnail_var = tk.BooleanVar(value=self.app_state.thumbnail_flag)
        self.subs_var = tk.BooleanVar(value=self.app_state.subtitle_flag)
        self.auto_subs_var = tk.BooleanVar(value=self.app_state.auto_subtitle_flag)

        self.chk_thumb = ctk.CTkCheckBox(f1, text=TRANSLATIONS[lang]["chk_thumb"], variable=self.thumbnail_var, fg_color=THEME_ACCENT_INDIGO, text_color=THEME_TEXT_PRIMARY)
        self.chk_thumb.grid(row=1, column=0, padx=6, pady=4, sticky="w")
        
        self.chk_subs = ctk.CTkCheckBox(f1, text=TRANSLATIONS[lang]["chk_subs"], variable=self.subs_var, fg_color=THEME_ACCENT_INDIGO, text_color=THEME_TEXT_PRIMARY)
        self.chk_subs.grid(row=2, column=0, padx=6, pady=4, sticky="w")
        
        self.auto_subs_check = ctk.CTkCheckBox(f1, text=TRANSLATIONS[lang]["chk_auto_subs"], variable=self.auto_subs_var, fg_color=THEME_ACCENT_INDIGO, text_color=THEME_TEXT_PRIMARY)
        self.auto_subs_check.grid(row=3, column=0, padx=18, pady=4, sticky="w")

        f2 = ctk.CTkFrame(self.tab_flags, fg_color="transparent")
        f2.grid(row=0, column=1, padx=10, pady=4, sticky="nsew")
        
        self.lbl_header_behavior = ctk.CTkLabel(f2, text=TRANSLATIONS[lang]["lbl_header_behavior"], font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=THEME_ACCENT_BLUE)
        self.lbl_header_behavior.grid(row=0, column=0, sticky="w", padx=6, pady=2)

        self.playlist_var = tk.BooleanVar(value=True)
        self.metadata_var = tk.BooleanVar(value=self.app_state.metadata_flag)
        self.restrict_names_var = tk.BooleanVar(value=self.app_state.restrict_filenames)
        self.download_archive_var = tk.BooleanVar(value=True)
        self.youtube_403_fallback_var = tk.BooleanVar(value=True)
        self.sponsorblock_var = tk.BooleanVar(value=self.app_state.sponsorblock_enabled)

        self.chk_playlist = ctk.CTkCheckBox(f2, text=TRANSLATIONS[lang]["chk_playlist"], variable=self.playlist_var, fg_color=THEME_ACCENT_INDIGO, text_color=THEME_TEXT_PRIMARY)
        self.chk_playlist.grid(row=1, column=0, padx=6, pady=2, sticky="w")
        
        self.chk_metadata = ctk.CTkCheckBox(f2, text=TRANSLATIONS[lang]["chk_metadata"], variable=self.metadata_var, fg_color=THEME_ACCENT_INDIGO, text_color=THEME_TEXT_PRIMARY)
        self.chk_metadata.grid(row=2, column=0, padx=6, pady=2, sticky="w")
        
        self.chk_restrict_names = ctk.CTkCheckBox(f2, text=TRANSLATIONS[lang]["chk_restrict_names"], variable=self.restrict_names_var, fg_color=THEME_ACCENT_INDIGO, text_color=THEME_TEXT_PRIMARY)
        self.chk_restrict_names.grid(row=3, column=0, padx=6, pady=2, sticky="w")
        
        self.chk_archive = ctk.CTkCheckBox(f2, text=TRANSLATIONS[lang]["chk_archive"], variable=self.download_archive_var, fg_color=THEME_ACCENT_INDIGO, text_color=THEME_TEXT_PRIMARY)
        self.chk_archive.grid(row=4, column=0, padx=6, pady=2, sticky="w")
        
        self.chk_youtube_403 = ctk.CTkCheckBox(f2, text=TRANSLATIONS[lang]["chk_youtube_403"], variable=self.youtube_403_fallback_var, fg_color=THEME_ACCENT_INDIGO, text_color=THEME_TEXT_PRIMARY)
        self.chk_youtube_403.grid(row=5, column=0, padx=6, pady=2, sticky="w")
        
        self.chk_sponsorblock = ctk.CTkCheckBox(f2, text=TRANSLATIONS[lang]["chk_sponsorblock"], variable=self.sponsorblock_var, fg_color=THEME_ACCENT_INDIGO, text_color=THEME_TEXT_PRIMARY)
        self.chk_sponsorblock.grid(row=6, column=0, padx=6, pady=2, sticky="w")



        # ==================== PRESETS DRAWER (FEATURE 3.3) ====================
        presets_card = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        presets_card.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="ew")
        presets_card.grid_columnconfigure(1, weight=1)

        self.lbl_presets = ctk.CTkLabel(
            presets_card,
            text=TRANSLATIONS[lang]["lbl_preset_action"],
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME_TEXT_SECONDARY
        )
        self.lbl_presets.grid(row=0, column=0, padx=6, pady=6, sticky="w")

        self.presets_dropdown_var = ctk.StringVar(value="Podcast MP3")
        self.presets_dropdown = ctk.CTkOptionMenu(
            presets_card,
            values=[],
            variable=self.presets_dropdown_var,
            fg_color=THEME_BG,
            button_color=THEME_BG,
            button_hover_color=THEME_CARD_BORDER,
            text_color=THEME_TEXT_PRIMARY,
            dropdown_fg_color=THEME_CARD_BG,
            dropdown_hover_color=THEME_CARD_BORDER,
            dropdown_text_color=THEME_TEXT_PRIMARY,
            command=self._load_selected_preset
        )
        self.presets_dropdown.grid(row=0, column=1, padx=6, pady=6, sticky="ew")

        # Save Preset Button
        self.btn_save_preset = ctk.CTkButton(
            presets_card,
            text=TRANSLATIONS[lang]["btn_save_preset"],
            width=110,
            height=30,
            corner_radius=8,
            fg_color=THEME_BG,
            text_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_CARD_BORDER,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._prompt_save_preset
        )
        self.btn_save_preset.grid(row=0, column=2, padx=6, pady=6, sticky="e")

        # Delete Preset Button
        self.btn_delete_preset = ctk.CTkButton(
            presets_card,
            text=TRANSLATIONS[lang]["btn_delete_preset"],
            width=80,
            height=30,
            corner_radius=8,
            fg_color=THEME_BG,
            text_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_CARD_BORDER,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._delete_selected_preset
        )
        self.btn_delete_preset.grid(row=0, column=3, padx=6, pady=6, sticky="e")

    def _on_mode_changed(self, choice):
        self.app_state.active_profile = "custom"
        if choice == "Audio":
            self.video_profile_menu.configure(state="disabled")
            self.video_limit_menu.configure(state="disabled")
            self.video_container_menu.configure(state="disabled")
            self.video_audio_codec_menu.configure(state="disabled")
            self.video_audio_codec_lbl.configure(text_color=THEME_TEXT_SECONDARY)
            
            self.audio_format_menu.configure(state="normal")
            self.audio_quality_menu.configure(state="normal")
        else:
            self.video_profile_menu.configure(state="normal")
            self.video_limit_menu.configure(state="normal")
            self.video_container_menu.configure(state="normal")
            self.video_audio_codec_menu.configure(state="normal")
            self.video_audio_codec_lbl.configure(text_color=THEME_TEXT_PRIMARY)
            
            self.audio_format_menu.configure(state="disabled")
            self.audio_quality_menu.configure(state="disabled")

    def _on_video_profile_changed(self, choice):
        self.app_state.active_profile = "custom"
        if choice == "Ozel (Custom)":
            self.video_limit_menu.configure(state="normal")
        else:
            self.video_limit_menu.configure(state="disabled")



    def _pick_cookies_file(self):
        chosen = filedialog.askopenfilename(
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if chosen:
            self.cookies_var.set(chosen)

    # ================= PRESET IMPLEMENTATIONS (FEATURE 3.3) =================
    def _load_presets_dropdown(self):
        presets = load_presets()
        keys = list(presets.keys())
        self.presets_dropdown.configure(values=keys)
        if keys:
            self.presets_dropdown_var.set(keys[0])

    def _load_selected_preset(self, name):
        presets = load_presets()
        if name not in presets:
            return
        
        p = presets[name]
        
        # Apply mode
        mode = p.get("mode", "Video")
        self.mode_var.set(mode)
        self._on_mode_changed(mode)

        # Audio settings
        self.audio_format_var.set(p.get("audio_format", "mp3"))
        self.audio_quality_var.set(p.get("audio_quality", "Dengeli (192K)"))

        # Video settings
        self.video_profile_var.set(p.get("video_profile", "Full HD (1080p)"))
        self._on_video_profile_changed(self.video_profile_var.get())
        self.video_container_var.set(p.get("video_container", "mp4"))
        self.video_audio_codec_var.set(p.get("video_audio_codec", "AAC"))

        # Add-ons
        self.thumbnail_var.set(p.get("thumbnail_flag", True))
        self.metadata_var.set(p.get("metadata_flag", True))
        self.restrict_names_var.set(p.get("restrict_filenames", False))
        
        concurrent = p.get("concurrent_fragments", "3")
        self.playlist_items_var.set(p.get("playlist_items", ""))
        self.max_downloads_var.set(p.get("max_downloads", ""))
        self.rate_limit_var.set(p.get("rate_limit", ""))

        if self.on_preset_loaded:
            self.on_preset_loaded()

    def _prompt_save_preset(self):
        dialog = ctk.CTkInputDialog(
            text="Yeni Profil İsmi Girin / Enter Preset Name:",
            title="Save Preset Profile"
        )
        name = dialog.get_input()
        if name and name.strip():
            name = name.strip()
            preset_dict = {
                "mode": self.mode_var.get(),
                "audio_format": self.audio_format_var.get(),
                "audio_quality": self.audio_quality_var.get(),
                "video_profile": self.video_profile_var.get(),
                "video_container": self.video_container_var.get(),
                "video_audio_codec": self.video_audio_codec_var.get(),
                "thumbnail_flag": self.thumbnail_var.get(),
                "metadata_flag": self.metadata_var.get(),
                "restrict_filenames": self.restrict_names_var.get(),
                "playlist_items": self.playlist_items_var.get(),
                "max_downloads": self.max_downloads_var.get(),
                "rate_limit": self.rate_limit_var.get()
            }
            save_preset(name, preset_dict)
            self._load_presets_dropdown()
            self.presets_dropdown_var.set(name)
            messagebox.showinfo("Başarılı", f"'{name}' profil şablonu başarıyla kaydedildi.")

    def _delete_selected_preset(self):
        name = self.presets_dropdown_var.get()
        if not name:
            return
        if messagebox.askyesno("Emin misiniz?", f"'{name}' şablonunu silmek istediğinize emin misiniz?"):
            delete_preset(name)
            self._load_presets_dropdown()

    # Pull UI state values directly into dict
    def get_settings_dict(self) -> dict:
        return {
            "mode": self.mode_var.get(),
            "video_profile": self.video_profile_var.get(),
            "video_limit": self.custom_video_height_var.get(),
            "video_container": self.video_container_var.get(),
            "audio_format": self.audio_format_var.get(),
            "audio_quality": self.audio_quality_var.get(),
            "video_audio_codec": self.video_audio_codec_var.get(),
            "playlist": self.playlist_var.get(),
            "metadata": self.metadata_var.get(),
            "thumbnail_flag": self.thumbnail_var.get(),
            "subs": self.subs_var.get(),
            "auto_subs": self.auto_subs_var.get(),
            "restrict_names": self.restrict_names_var.get(),
            "sponsorblock": self.sponsorblock_var.get(),
            "playlist_items": self.playlist_items_var.get(),
            "max_downloads": self.max_downloads_var.get(),
            "rate_limit": self.rate_limit_var.get(),
            "archive": self.download_archive_var.get(),
            "retries": self.retries_var.get(),
            "concurrent_fragments": "3",
            "cookies": self.cookies_var.get(),
            "browser_cookies": self.browser_cookies_var.get(),
            "youtube_403": self.youtube_403_fallback_var.get()
        }

    def apply_settings_dict(self, d: dict):
        self.mode_var.set(d.get("mode", "Video"))
        self._on_mode_changed(self.mode_var.get())
        self.video_profile_var.set(d.get("video_profile", "Full HD (1080p)"))
        self._on_video_profile_changed(self.video_profile_var.get())
        self.custom_video_height_var.set(d.get("video_limit", "1080"))
        self.video_container_var.set(d.get("video_container", "mp4"))
        self.audio_format_var.set(d.get("audio_format", "mp3"))
        self.audio_quality_var.set(d.get("audio_quality", "Dengeli (192K)"))
        self.video_audio_codec_var.set(d.get("video_audio_codec", "AAC"))
        self.playlist_var.set(d.get("playlist", True))
        self.metadata_var.set(d.get("metadata", True))
        self.thumbnail_var.set(d.get("thumbnail_flag", True))
        self.subs_var.set(d.get("subs", False))
        self.auto_subs_var.set(d.get("auto_subs", False))
        self.restrict_names_var.set(d.get("restrict_names", False))
        self.sponsorblock_var.set(d.get("sponsorblock", False))
        self.playlist_items_var.set(d.get("playlist_items", ""))
        self.max_downloads_var.set(d.get("max_downloads", ""))
        self.rate_limit_var.set(d.get("rate_limit", ""))
        self.download_archive_var.set(d.get("archive", True))
        self.retries_var.set(d.get("retries", ""))
        self.cookies_var.set(d.get("cookies", ""))
        self.browser_cookies_var.set(d.get("browser_cookies", "Kapali"))
        self.youtube_403_fallback_var.set(d.get("youtube_403", True))

    def refresh_translations(self):
        lang = self.app_state.current_lang
        
        self.tabview.rename(TRANSLATIONS[lang]["tab_codecs"], TRANSLATIONS[lang]["tab_codecs"]) #CTk TabView has no clean rename, we will reconstruct tab texts dynamically in main_window.
        self.lbl_mode.configure(text=TRANSLATIONS[lang]["lbl_mode"])
        self.lbl_profile.configure(text=TRANSLATIONS[lang]["lbl_profile"])
        self.lbl_max_res.configure(text=TRANSLATIONS[lang]["lbl_max_res"])
        self.lbl_format.configure(text=TRANSLATIONS[lang]["lbl_format"])
        self.lbl_audio_ext.configure(text=TRANSLATIONS[lang]["lbl_audio_ext"])
        self.lbl_audio_qual.configure(text=TRANSLATIONS[lang]["lbl_audio_qual"])
        self.video_audio_codec_lbl.configure(text=TRANSLATIONS[lang]["lbl_audio_codec"])
        
        self.lbl_playlist_range.configure(text=TRANSLATIONS[lang]["lbl_playlist_range"])
        self.lbl_max_dl.configure(text=TRANSLATIONS[lang]["lbl_max_dl"])
        self.lbl_speed_limit.configure(text=TRANSLATIONS[lang]["lbl_speed_limit"])
        self.lbl_cookie_file.configure(text=TRANSLATIONS[lang]["lbl_cookie_file"])
        self.lbl_browser_cookie.configure(text=TRANSLATIONS[lang]["lbl_browser_cookie"])
        self.lbl_retry.configure(text=TRANSLATIONS[lang]["lbl_retry"])

        self.lbl_header_addons.configure(text=TRANSLATIONS[lang]["lbl_header_addons"])
        self.chk_thumb.configure(text=TRANSLATIONS[lang]["chk_thumb"])
        self.chk_subs.configure(text=TRANSLATIONS[lang]["chk_subs"])
        self.auto_subs_check.configure(text=TRANSLATIONS[lang]["chk_auto_subs"])

        self.lbl_header_behavior.configure(text=TRANSLATIONS[lang]["lbl_header_behavior"])
        self.chk_playlist.configure(text=TRANSLATIONS[lang]["chk_playlist"])
        self.chk_metadata.configure(text=TRANSLATIONS[lang]["chk_metadata"])
        self.chk_restrict_names.configure(text=TRANSLATIONS[lang]["chk_restrict_names"])
        self.chk_archive.configure(text=TRANSLATIONS[lang]["chk_archive"])
        self.chk_youtube_403.configure(text=TRANSLATIONS[lang]["chk_youtube_403"])
        self.chk_sponsorblock.configure(text=TRANSLATIONS[lang]["chk_sponsorblock"])



        self.lbl_presets.configure(text=TRANSLATIONS[lang]["lbl_preset_action"])
        self.btn_save_preset.configure(text=TRANSLATIONS[lang]["btn_save_preset"])
        self.btn_delete_preset.configure(text=TRANSLATIONS[lang]["btn_delete_preset"])
