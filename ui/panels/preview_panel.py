# ui/panels/preview_panel.py
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
from ui.theme import (
    THEME_BG, THEME_CARD_BG, THEME_CARD_BORDER, THEME_TEXT_PRIMARY,
    THEME_TEXT_SECONDARY, THEME_ACCENT_BLUE, THEME_ACCENT_INDIGO,
    THEME_ACCENT_RED, TRANSLATIONS
)
from core.app_state import AppState
from core.clip import format_seconds_to_mmss, validate_clip_range, parse_time_to_seconds
from core.profiles import EXPORT_PROFILES
from core.suggester import SmartFormatSuggester

from ui.components.clip_row import ClipRow


class PreviewPanel(ctk.CTkFrame):
    def __init__(self, parent, state: AppState, on_chapter_click_callback, on_create_channel_rule_callback=None, **kwargs):
        super().__init__(
            parent,
            fg_color=THEME_CARD_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            corner_radius=16,
            **kwargs
        )
        self.app_state = state
        self.on_chapter_click = on_chapter_click_callback
        self.on_create_channel_rule = on_create_channel_rule_callback
        
        self.current_channel_id = None
        self.current_channel_name = None
        
        # Clip State Variables
        self.clip_enabled_var = tk.BooleanVar(value=False)
        self.clip_rows = []
        
        self.grid_columnconfigure(1, weight=1)
        self._build_ui()

    def _build_ui(self):
        lang = self.app_state.current_lang

        # Loading visual overlay
        self.preview_loading_lbl = ctk.CTkLabel(
            self,
            text=TRANSLATIONS[lang]["lbl_preview_loading"],
            font=ctk.CTkFont(family="Segoe UI", size=13, slant="italic"),
            text_color=THEME_TEXT_SECONDARY,
        )
        self.preview_loading_lbl.grid(row=0, column=0, columnspan=2, padx=20, pady=24, sticky="ew")
        self.preview_loading_lbl.grid_remove()

        # Thumbnail display label
        self.thumb_label = ctk.CTkLabel(
            self,
            text="No Thumbnail",
            width=160,
            height=90,
            fg_color=THEME_BG,
            corner_radius=10
        )
        self.thumb_label.grid(row=0, column=0, padx=16, pady=16, sticky="w")

        # Metadata Details Frame
        self.meta_info = ctk.CTkFrame(self, fg_color="transparent")
        self.meta_info.grid(row=0, column=1, padx=(4, 16), pady=16, sticky="nsew")
        self.meta_info.grid_columnconfigure(0, weight=1)

        self.preview_title_lbl = ctk.CTkLabel(
            self.meta_info,
            text=TRANSLATIONS[lang]["lbl_preview_title"],
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=THEME_TEXT_PRIMARY,
            anchor="w",
            justify="left",
            wraplength=350,
        )
        self.preview_title_lbl.grid(row=0, column=0, sticky="w")

        self.preview_author_lbl = ctk.CTkLabel(
            self.meta_info,
            text=TRANSLATIONS[lang]["lbl_preview_author"],
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME_ACCENT_BLUE,
            anchor="w",
        )
        self.preview_author_lbl.grid(row=1, column=0, sticky="w", pady=(2, 0))

        self.preview_dur_lbl = ctk.CTkLabel(
            self.meta_info,
            text=TRANSLATIONS[lang]["lbl_preview_dur"],
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=THEME_TEXT_SECONDARY,
            anchor="w",
        )
        self.preview_dur_lbl.grid(row=2, column=0, sticky="w", pady=(2, 0))

        # Size Estimate Label
        self.preview_size_lbl = ctk.CTkLabel(
            self.meta_info,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=THEME_TEXT_SECONDARY,
            anchor="w",
        )
        self.preview_size_lbl.grid(row=3, column=0, sticky="w", pady=(2, 0))

        # Heuristic Suggestion Banner Frame (Row 4)
        self.preview_suggestion_frame = ctk.CTkFrame(self.meta_info, fg_color="transparent")
        self.preview_suggestion_frame.grid(row=4, column=0, sticky="w", pady=(4, 0))
        self.preview_suggestion_frame.grid_remove()

        self.lbl_suggestion = ctk.CTkLabel(
            self.preview_suggestion_frame,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=THEME_ACCENT_BLUE,
            anchor="w",
        )
        self.lbl_suggestion.pack(side="left", padx=(0, 6))

        self.btn_apply_suggestion = ctk.CTkButton(
            self.preview_suggestion_frame,
            text="Uygula" if lang == "tr" else ("Aplicar" if lang == "es" else "Apply"),
            width=50,
            height=20,
            corner_radius=6,
            fg_color=THEME_BG,
            text_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_CARD_BORDER,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            command=self._apply_suggestion
        )
        self.btn_apply_suggestion.pack(side="left")

        self.suggested_profile = None

        # Channel Auto-Rule Banner Frame (Row 5)
        self.preview_channel_rule_frame = ctk.CTkFrame(self.meta_info, fg_color="transparent")
        self.preview_channel_rule_frame.grid(row=5, column=0, sticky="w", pady=(4, 0))
        self.preview_channel_rule_frame.grid_remove()

        self.btn_channel_rule = ctk.CTkButton(
            self.preview_channel_rule_frame,
            text="",
            height=24,
            corner_radius=6,
            fg_color=THEME_BG,
            text_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_CARD_BORDER,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            command=self._on_channel_rule_clicked
        )
        self.btn_channel_rule.pack(side="left")

        # Chapters Section Frame (Scrollable horizontal chapter bar)
        self.chapters_frame = ctk.CTkScrollableFrame(
            self,
            orientation="horizontal",
            height=36,
            fg_color="transparent",
            scrollbar_button_color=THEME_CARD_BORDER
        )
        self.chapters_frame.grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 12), sticky="ew")
        self.chapters_frame.grid_remove()

        # Direct-in-Preview Clipping Frame (Relocated from advanced tab view)
        self.clip_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.clip_frame.grid(row=2, column=0, columnspan=2, padx=16, pady=(0, 16), sticky="ew")
        self.clip_frame.grid_columnconfigure(0, weight=1)

        # Toggle checkboxes sub-frame (Row 0)
        checkboxes_frame = ctk.CTkFrame(self.clip_frame, fg_color="transparent")
        checkboxes_frame.grid(row=0, column=0, pady=(0, 6), sticky="ew")
        checkboxes_frame.grid_columnconfigure((0, 1), weight=1)

        self.chk_clip_enable = ctk.CTkCheckBox(
            checkboxes_frame,
            text=TRANSLATIONS[lang]["lbl_clip_enable"],
            variable=self.clip_enabled_var,
            fg_color=THEME_ACCENT_INDIGO,
            text_color=THEME_TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._on_clip_toggled
        )
        self.chk_clip_enable.grid(row=0, column=0, padx=6, pady=4, sticky="w")

        # Added "Merge Clips into Single File" Checkbox
        self.merge_clips_var = tk.BooleanVar(value=False)
        self.chk_merge_clips = ctk.CTkCheckBox(
            checkboxes_frame,
            text="Klipleri Tek Dosyada Birleştir" if lang == "tr" else ("Unir clips en un solo archivo" if lang == "es" else "Merge Clips into Single File"),
            variable=self.merge_clips_var,
            fg_color=THEME_ACCENT_INDIGO,
            text_color=THEME_TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
        )
        self.chk_merge_clips.grid(row=0, column=1, padx=6, pady=4, sticky="w")

        # Scrollable container for Multi-Clip rows (Row 1)
        self.clips_scroll_frame = ctk.CTkScrollableFrame(
            self.clip_frame,
            height=220,
            fg_color="transparent",
            border_color=THEME_CARD_BORDER,
            border_width=1,
            corner_radius=12
        )
        self.clips_scroll_frame.grid(row=1, column=0, padx=6, pady=6, sticky="ew")
        self.clips_scroll_frame.grid_columnconfigure(0, weight=1)

        # Button container for clipping operations (Row 2)
        self.clip_buttons_frame = ctk.CTkFrame(self.clip_frame, fg_color="transparent")
        self.clip_buttons_frame.grid(row=2, column=0, padx=6, pady=4, sticky="ew")
        self.clip_buttons_frame.grid_columnconfigure((0, 1), weight=1)

        self.btn_add_clip = ctk.CTkButton(
            self.clip_buttons_frame,
            text="➕ Klip Ekle" if lang == "tr" else ("➕ Añadir Clip" if lang == "es" else "➕ Add Clip"),
            fg_color=THEME_BG,
            text_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_CARD_BORDER,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self.add_clip_row_default,
            height=30
        )
        self.btn_add_clip.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        self.btn_clean_sponsors = ctk.CTkButton(
            self.clip_buttons_frame,
            text="✂️ Sponsorları Temizle" if lang == "tr" else ("✂️ Quitar Sponsors" if lang == "es" else "✂️ Clean Sponsors"),
            fg_color=THEME_BG,
            text_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_CARD_BORDER,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            state="disabled",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self.clean_sponsors,
            height=30
        )
        self.btn_clean_sponsors.grid(row=0, column=1, padx=(4, 0), sticky="ew")

        self._on_clip_toggled() # Disable entry fields by default if checkbox off

    def update_channel_rule_button_text(self):
        if not hasattr(self, "btn_channel_rule"):
            return
        lang = self.app_state.current_lang
        from core.history import get_channel_rule
        has_rule = False
        if self.current_channel_id:
            rule = get_channel_rule(self.current_channel_id)
            if rule:
                has_rule = True
                
        if has_rule:
            txt = "✅ Kanal Kuralı Aktif (Düzenle)" if lang == "tr" else ("✅ Regla de Canal Activa (Editar)" if lang == "es" else "✅ Channel Rule Active (Edit)")
        else:
            txt = "📌 Bu Kanal İçin Kural Oluştur" if lang == "tr" else ("📌 Crear Regla Para Este Canal" if lang == "es" else "📌 Create Rule For This Channel")
        self.btn_channel_rule.configure(text=txt)

    def _on_channel_rule_clicked(self):
        if self.on_create_channel_rule and self.current_channel_id:
            self.on_create_channel_rule(self.current_channel_id, self.current_channel_name)
            self.update_channel_rule_button_text()

    def _on_clip_toggled(self):
        enabled = self.clip_enabled_var.get()
        if enabled:
            self.clips_scroll_frame.grid()
            self.clip_buttons_frame.grid()
            if not self.clip_rows:
                self.add_clip_row_default()
        else:
            self.clips_scroll_frame.grid_remove()
            self.clip_buttons_frame.grid_remove()

    def _bg_fetch_sponsor_segments(self, video_id):
        import threading
        from core.services import fetch_sponsor_segments
        
        def run():
            segments = fetch_sponsor_segments(video_id)
            if segments:
                self.after(0, self._on_sponsor_segments_loaded, segments)
                
        threading.Thread(target=run, daemon=True, name="sponsorblock-fetcher").start()

    def _on_sponsor_segments_loaded(self, segments):
        self.sponsor_segments = segments
        if hasattr(self, "btn_clean_sponsors"):
            self.btn_clean_sponsors.configure(state="normal")
        for row in self.clip_rows:
            if hasattr(row, "slider"):
                row.slider.sponsor_segments = segments
                row.slider.draw()
            if hasattr(row, "draw_sponsor_overlay"):
                row.draw_sponsor_overlay()

    def clean_sponsors(self):
        if not hasattr(self, "sponsor_segments") or not self.sponsor_segments:
            return
            
        duration = 0.0
        if self.app_state.current_video_info:
            duration = self.app_state.current_video_info.get("duration", 0.0)
        if duration <= 0:
            return
            
        # Inverted Sponsor Block Interval Merging with edge cases
        blocked = sorted([(s["start"], s["end"]) for s in self.sponsor_segments])
        merged = []
        for start, end in blocked:
            if merged and start <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append([start, end])
        
        # Invert merged blocks to find safe clips in [0, duration]
        safe_clips = []
        cursor = 0.0
        for blk_start, blk_end in merged:
            if cursor < blk_start - 0.5:  # Filter out short clips < 0.5 sec
                safe_clips.append((cursor, blk_start))
            cursor = blk_end
        if cursor < duration - 0.5:
            safe_clips.append((cursor, duration))
        
        # Fallback: if all segments are sponsored (safe_clips empty), provide full video
        if not safe_clips:
            safe_clips = [(0.0, duration)]
            
        # Clear current clip rows and enable clipping
        for row in list(self.clip_rows):
            row.destroy()
        self.clip_rows.clear()
        
        self.clip_enabled_var.set(True)
        self._on_clip_toggled()
        
        # Populate safe clips
        for start, end in safe_clips:
            self.add_clip_row(start, end)

    def add_clip_row(self, start_val, end_val, profile="Default (No Profile)"):
        duration = 0.0
        if self.app_state.current_video_info:
            duration = self.app_state.current_video_info.get("duration", 100.0)
            
        row = ClipRow(
            self.clips_scroll_frame,
            self,
            index=len(self.clip_rows),
            min_val=0.0,
            max_val=duration,
            start_val=start_val,
            end_val=end_val,
            on_delete=self._remove_clip_row
        )
        if hasattr(self, "sponsor_segments") and self.sponsor_segments:
            row.slider.sponsor_segments = self.sponsor_segments
            row.slider.draw()
            if hasattr(row, "draw_sponsor_overlay"):
                row.draw_sponsor_overlay()
        row.export_profile_var.set(profile)
        row.pack(fill="x", padx=4, pady=4)
        self.clip_rows.append(row)
        self.clips_scroll_frame.update_idletasks()

    def add_clip_row_default(self):
        duration = 0.0
        if self.app_state.current_video_info:
            duration = self.app_state.current_video_info.get("duration", 100.0)
        self.add_clip_row(0.0, duration)

    def _remove_clip_row(self, row):
        if row in self.clip_rows:
            self.clip_rows.remove(row)
            row.destroy()
        
        # Re-index remaining rows
        for idx, r in enumerate(self.clip_rows):
            r.index = idx

    def get_multi_clips(self) -> list[dict]:
        if not self.clip_enabled_var.get():
            return []
        clips = []
        for r in self.clip_rows:
            result = validate_clip_range(r.start_var.get(), r.end_var.get(), r.max_val)
            if isinstance(result, tuple):
                start, end = result
                clips.append({
                    "start": start,
                    "end": end,
                    "precise": r.precise_var.get(),
                    "profile": r.export_profile_var.get()
                })
        return clips

    def get_clip_settings(self) -> dict:
        if not self.clip_enabled_var.get() or not self.clip_rows:
            return {
                "clip_enabled": False,
                "clip_start": "00:00",
                "clip_end": "00:00",
                "clip_precise": False,
                "export_profile": "Default (No Profile)",
                "merge_clips": False
            }
        r = self.clip_rows[0]
        return {
            "clip_enabled": True,
            "clip_start": r.start_var.get(),
            "clip_end": r.end_var.get(),
            "clip_precise": r.precise_var.get(),
            "export_profile": r.export_profile_var.get(),
            "merge_clips": self.merge_clips_var.get()
        }

    def apply_clip_settings(self, d: dict):
        self.clip_enabled_var.set(d.get("clip_enabled", False))
        self.merge_clips_var.set(d.get("merge_clips", False))
        self._on_clip_toggled()
        if self.clip_rows:
            r = self.clip_rows[0]
            r.start_var.set(d.get("clip_start", "00:00"))
            r.end_var.set(d.get("clip_end", "01:00"))
            r.precise_var.set(d.get("clip_precise", False))
            r.export_profile_var.set(d.get("export_profile", "Default (No Profile)"))
            r._validate_entries()

    def _apply_suggestion(self):
        if not self.suggested_profile:
            return
        
        # Enable clipping
        self.clip_enabled_var.set(True)
        self._on_clip_toggled()
        
        # Ensure at least one row exists
        if not self.clip_rows:
            self.add_clip_row_default()
            
        # Apply suggested profile to all rows
        for row in self.clip_rows:
            row.export_profile_var.set(self.suggested_profile)
            row._validate_entries()
            
        # Hide the banner after successful application
        self.preview_suggestion_frame.grid_remove()

    def show_loading(self):
        self.grid()
        self.thumb_label.grid_remove()
        self.meta_info.grid_remove()
        self.chapters_frame.grid_remove()
        self.clip_frame.grid_remove()
        self.current_channel_id = None
        self.current_channel_name = None
        if hasattr(self, "preview_channel_rule_frame"):
            self.preview_channel_rule_frame.grid_remove()
        self.preview_loading_lbl.grid()

    def hide(self):
        self.current_channel_id = None
        self.current_channel_name = None
        if hasattr(self, "preview_channel_rule_frame"):
            self.preview_channel_rule_frame.grid_remove()
        self.grid_remove()

    def show_metadata(self, meta: dict, thumbnail_img: ImageTk.PhotoImage = None):
        self.grid()
        self.preview_loading_lbl.grid_remove()
        self.thumb_label.grid()
        self.meta_info.grid()
        self.clip_frame.grid()

        # Channel rule tracking
        self.current_channel_id = meta.get("channel_id")
        self.current_channel_name = meta.get("channel_name") or meta.get("uploader")
        if self.current_channel_id:
            self.preview_channel_rule_frame.grid()
            self.update_channel_rule_button_text()
        else:
            self.preview_channel_rule_frame.grid_remove()

        # Reset and trigger SponsorBlock fetching for YouTube videos
        self.sponsor_segments = []
        if hasattr(self, "btn_clean_sponsors"):
            self.btn_clean_sponsors.configure(state="disabled")
        video_id = meta.get("id")
        extractor = meta.get("extractor", "").lower()
        if video_id and "youtube" in extractor:
            self._bg_fetch_sponsor_segments(video_id)

        if thumbnail_img:
            self.thumb_label.configure(image=thumbnail_img, text="")
        else:
            self.thumb_label.configure(image="", text="No Image")

        # Set title, uploader, duration
        self.preview_title_lbl.configure(text=meta.get("title", "Unknown Title"))
        self.preview_author_lbl.configure(text=meta.get("uploader", "Unknown Channel"))
        
        duration_seconds = meta.get("duration", 0)
        duration_str = format_seconds_to_mmss(duration_seconds)
        self.preview_dur_lbl.configure(text=f"Duration: {duration_str}")

        # Clear existing clip rows
        for row in list(self.clip_rows):
            row.destroy()
        self.clip_rows.clear()

        # Auto-reset clipping variables to unchecked
        self.clip_enabled_var.set(False)
        self._on_clip_toggled()

        # Show Size Estimate
        filesize = meta.get("filesize") or meta.get("filesize_approx")
        if filesize:
            size_mb = filesize / (1024 * 1024)
            self.preview_size_lbl.configure(text=f"Est. Size: {size_mb:.1f} MB")
            self.preview_size_lbl.grid()
        else:
            self.preview_size_lbl.grid_remove()

        # Render Chapters (Feature 3.4)
        chapters = meta.get("chapters", [])
        if chapters:
            self.chapters_frame.grid()
            for child in self.chapters_frame.winfo_children():
                child.destroy()
            
            for idx, ch in enumerate(chapters):
                title = ch.get("title", f"Ch {idx+1}")
                start = ch.get("start_time", 0.0)
                end = ch.get("end_time", 0.0)
                
                ch_btn = ctk.CTkButton(
                    self.chapters_frame,
                    text=f"✂️ {title} ({format_seconds_to_mmss(start)})",
                    height=24,
                    corner_radius=6,
                    fg_color=THEME_BG,
                    text_color=THEME_TEXT_PRIMARY,
                    hover_color=THEME_CARD_BORDER,
                    border_color=THEME_CARD_BORDER,
                    border_width=1,
                    font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                    command=lambda s=start, e=end, t=title: self.on_chapter_click(s, e, t)
                )
                ch_btn.pack(side="left", padx=4)
        else:
            self.chapters_frame.grid_remove()

        # Heuristic Suggester Integration
        suggester = SmartFormatSuggester()
        suggested_key = suggester.analyze(meta)
        
        lang = self.app_state.current_lang
        if suggested_key == "mp4_vertical":
            prof = "YouTube Shorts (Max 60s, 9:16 Crop)" if meta.get("duration", 0) <= 60 else "Instagram Reels (Max 90s, 9:16 Crop)"
            suggestion_text = "💡 Öneri: Dikey Shorts/Reels video tespit edildi." if lang == "tr" else ("💡 Sugerencia: Video vertical Shorts/Reels detectado." if lang == "es" else "💡 Suggestion: Vertical Shorts/Reels video detected.")
            self.suggested_profile = prof
        elif suggested_key in ("mp3_music", "mp3_podcast"):
            prof = "Voice Note / Audiobook (Mono, Light M4A)"
            suggestion_text = "💡 Öneri: Müzik veya uzun konuşma tespit edildi." if lang == "tr" else ("💡 Sugerencia: Música o charla larga detectada." if lang == "es" else "💡 Suggestion: Music or long speech detected.")
            self.suggested_profile = prof
        else:
            self.suggested_profile = None
            
        if self.suggested_profile:
            self.lbl_suggestion.configure(text=suggestion_text)
            self.preview_suggestion_frame.grid()
        else:
            self.preview_suggestion_frame.grid_remove()

    def show_error(self):
        self.grid()
        self.thumb_label.grid_remove()
        self.meta_info.grid_remove()
        self.chapters_frame.grid_remove()
        self.clip_frame.grid_remove()
        self.current_channel_id = None
        self.current_channel_name = None
        if hasattr(self, "preview_channel_rule_frame"):
            self.preview_channel_rule_frame.grid_remove()
        self.preview_loading_lbl.configure(text=TRANSLATIONS[self.app_state.current_lang]["lbl_preview_err"])
        self.preview_loading_lbl.grid()

    def refresh_translations(self):
        lang = self.app_state.current_lang
        self.preview_loading_lbl.configure(text=TRANSLATIONS[lang]["lbl_preview_loading"])
        self.preview_title_lbl.configure(text=TRANSLATIONS[lang]["lbl_preview_title"])
        self.preview_author_lbl.configure(text=TRANSLATIONS[lang]["lbl_preview_author"])
        self.preview_dur_lbl.configure(text=TRANSLATIONS[lang]["lbl_preview_dur"])
        
        # Localize relocated clipping labels
        self.chk_clip_enable.configure(text=TRANSLATIONS[lang]["lbl_clip_enable"])
        self.btn_add_clip.configure(text="➕ Klip Ekle" if lang == "tr" else ("➕ Añadir Clip" if lang == "es" else "➕ Add Clip"))
        
        self.update_channel_rule_button_text()
        
        # Refresh all active rows
        for row in self.clip_rows:
            row._refresh_translations()

