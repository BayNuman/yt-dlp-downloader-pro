# ui/components/clip_row.py
import tkinter as tk
import customtkinter as ctk
from ui.theme import (
    THEME_BG, THEME_CARD_BG, THEME_CARD_BORDER, THEME_TEXT_PRIMARY,
    THEME_TEXT_SECONDARY, THEME_ACCENT_BLUE, THEME_ACCENT_INDIGO,
    THEME_ACCENT_RED, TRANSLATIONS
)
from core.clip import format_seconds_to_mmss, validate_clip_range, parse_time_to_seconds
from core.profiles import EXPORT_PROFILES
from ui.components.range_slider import CTkRangeSlider

class ClipRow(ctk.CTkFrame):
    """
    A custom premium row nested inside the scrollable container.
    Represents a single clipping segment with its own start, end entries, profile optionmenu, precise cut checkbox, and dual-node range slider.
    """
    def __init__(self, parent, panel, index: int, min_val=0.0, max_val=100.0, start_val=0.0, end_val=100.0, on_delete=None, **kwargs):
        super().__init__(
            parent,
            fg_color=THEME_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            corner_radius=10,
            **kwargs
        )
        self.panel = panel
        self.index = index
        self.on_delete = on_delete
        self.min_val = min_val
        self.max_val = max_val

        self.start_var = ctk.StringVar(value=format_seconds_to_mmss(start_val))
        self.end_var = ctk.StringVar(value=format_seconds_to_mmss(end_val))
        self.export_profile_var = ctk.StringVar(value="Default (No Profile)")
        self.precise_var = tk.BooleanVar(value=False)

        self._build_ui(start_val, end_val)

    def _build_ui(self, start_val, end_val):
        lang = self.panel.app_state.current_lang
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(3, weight=1)

        # Row 0: Profile dropdown, Precise checkbox, and Delete Button
        r0_frame = ctk.CTkFrame(self, fg_color="transparent")
        r0_frame.grid(row=0, column=0, columnspan=4, padx=8, pady=(8, 4), sticky="ew")
        r0_frame.grid_columnconfigure(1, weight=1)

        self.lbl_profile = ctk.CTkLabel(
            r0_frame,
            text="Profil:" if lang == "tr" else ("Perfil:" if lang == "es" else "Profile:"),
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=THEME_TEXT_SECONDARY
        )
        self.lbl_profile.grid(row=0, column=0, padx=(0, 6), sticky="w")

        self.profile_menu = ctk.CTkOptionMenu(
            r0_frame,
            values=list(EXPORT_PROFILES.keys()),
            variable=self.export_profile_var,
            fg_color=THEME_CARD_BG,
            button_color=THEME_CARD_BG,
            button_hover_color=THEME_CARD_BORDER,
            text_color=THEME_TEXT_PRIMARY,
            dropdown_fg_color=THEME_CARD_BG,
            dropdown_hover_color=THEME_CARD_BORDER,
            dropdown_text_color=THEME_TEXT_PRIMARY,
            command=self._on_profile_selected,
            height=26,
            width=140
        )
        self.profile_menu.grid(row=0, column=1, sticky="w")

        self.chk_precise = ctk.CTkCheckBox(
            r0_frame,
            text=TRANSLATIONS[lang]["lbl_clip_precise"],
            variable=self.precise_var,
            fg_color=THEME_ACCENT_INDIGO,
            text_color=THEME_TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            width=100
        )
        self.chk_precise.grid(row=0, column=2, padx=12, sticky="w")

        # Delete Button (❌)
        btn_del = ctk.CTkButton(
            r0_frame,
            text="❌",
            width=28,
            height=26,
            fg_color="transparent",
            text_color=THEME_ACCENT_RED,
            hover_color=THEME_CARD_BORDER,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.on_delete(self) if self.on_delete else None
        )
        btn_del.grid(row=0, column=3, sticky="e")

        # Row 1: Start and End Entries
        self.lbl_start = ctk.CTkLabel(
            self,
            text="Start:" if lang == "en" else ("Başlangıç:" if lang == "tr" else "Inicio:"),
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=THEME_TEXT_PRIMARY
        )
        self.lbl_start.grid(row=1, column=0, padx=(8, 4), pady=4, sticky="w")

        self.start_entry = ctk.CTkEntry(
            self,
            textvariable=self.start_var,
            placeholder_text="00:00",
            height=26,
            fg_color=THEME_CARD_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            text_color=THEME_TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        self.start_entry.grid(row=1, column=1, padx=4, pady=4, sticky="ew")
        self.start_var.trace_add("write", self._validate_entries)

        self.lbl_end = ctk.CTkLabel(
            self,
            text="End:" if lang == "en" else ("Bitiş:" if lang == "tr" else "Fin:"),
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=THEME_TEXT_PRIMARY
        )
        self.lbl_end.grid(row=1, column=2, padx=(12, 4), pady=4, sticky="w")

        self.end_entry = ctk.CTkEntry(
            self,
            textvariable=self.end_var,
            placeholder_text="00:00",
            height=26,
            fg_color=THEME_CARD_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            text_color=THEME_TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        self.end_entry.grid(row=1, column=3, padx=(4, 8), pady=4, sticky="ew")
        self.end_var.trace_add("write", self._validate_entries)

        # Row 2: CTkRangeSlider
        self.slider = CTkRangeSlider(
            self,
            min_val=self.min_val,
            max_val=self.max_val,
            start_val=start_val,
            end_val=end_val,
            command=self._on_slider_moved,
            height=26
        )
        self.slider.grid(row=2, column=0, columnspan=4, padx=8, pady=(4, 0), sticky="ew")

        # Row 3: SponsorBlock Visual Canvas Overlay (Grid aligned, same width as slider)
        self.sponsor_overlay_canvas = ctk.CTkCanvas(
            self,
            height=8,
            bg="#121b2d" if ctk.get_appearance_mode() == "Dark" else "#ffffff",
            highlightthickness=0,
            borderwidth=0
        )
        self.sponsor_overlay_canvas.grid(row=3, column=0, columnspan=4, padx=12, pady=(2, 4), sticky="ew")
        self.sponsor_overlay_canvas.bind("<Configure>", lambda e: self.draw_sponsor_overlay())

        # Row 4: Validation Label
        self.validation_lbl = ctk.CTkLabel(
            self,
            text="",
            text_color=THEME_ACCENT_RED,
            font=ctk.CTkFont(family="Segoe UI", size=10)
        )
        self.validation_lbl.grid(row=4, column=0, columnspan=4, padx=8, pady=(2, 6), sticky="w")
        self._validate_entries()

    def _on_slider_moved(self, start, end):
        self.start_var.set(format_seconds_to_mmss(start))
        self.end_var.set(format_seconds_to_mmss(end))
        self._validate_entries()

    def _on_profile_selected(self, choice):
        self._validate_entries()

    def draw_sponsor_overlay(self):
        self.sponsor_overlay_canvas.delete("all")
        w = self.sponsor_overlay_canvas.winfo_width()
        h = self.sponsor_overlay_canvas.winfo_height()
        if w < 10 or h < 4:
            return
            
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_color = "#121b2d" if is_dark else "#ffffff"
        self.sponsor_overlay_canvas.configure(bg=bg_color)
        
        cy = h / 2
        
        # Base track
        self.sponsor_overlay_canvas.create_line(12, cy, w - 12, cy, fill="#22334f" if is_dark else "#e2e8f0", width=4, capstyle="round")
        
        if not hasattr(self.slider, "sponsor_segments") or not self.slider.sponsor_segments:
            return
            
        usable_width = w - 24
        div = (self.max_val - self.min_val) if (self.max_val - self.min_val) > 0 else 1.0
        
        category_colors = {
            "sponsor": "#f1c40f",
            "intro": "#3498db",
            "outro": "#e74c3c",
            "interaction": "#9b59b6",
            "selfpromo": "#e67e22",
            "preview": "#1abc9c",
            "music_offtopic": "#16a085",
            "filler": "#7f8c8d"
        }
        
        for seg in self.slider.sponsor_segments:
            seg_start = seg.get("start", 0.0)
            seg_end = seg.get("end", 0.0)
            cat = seg.get("category", "sponsor")
            color = category_colors.get(cat.lower(), "#f1c40f")
            
            x_seg_start = 12 + ((seg_start - self.min_val) / div) * usable_width
            x_seg_end = 12 + ((seg_end - self.min_val) / div) * usable_width
            
            x_seg_start = max(12.0, min(x_seg_start, float(w - 12)))
            x_seg_end = max(12.0, min(x_seg_end, float(w - 12)))
            
            if x_seg_end > x_seg_start:
                self.sponsor_overlay_canvas.create_line(x_seg_start, cy, x_seg_end, cy, fill=color, width=6, capstyle="butt")

    def _validate_entries(self, *args):
        try:
            start_sec = parse_time_to_seconds(self.start_var.get())
            end_sec = parse_time_to_seconds(self.end_var.get())
            if start_sec is not None and end_sec is not None and self.min_val <= start_sec <= self.max_val and self.min_val <= end_sec <= self.max_val:
                if abs(self.slider.value_start - start_sec) > 0.05 or abs(self.slider.value_end - end_sec) > 0.05:
                    self.slider.set_values(start_sec, end_sec)
        except Exception:
            pass

        profile_name = self.export_profile_var.get()
        profile = EXPORT_PROFILES.get(profile_name)

        result = validate_clip_range(
            self.start_var.get(),
            self.end_var.get(),
            self.max_val
        )
        if isinstance(result, str):
            self.validation_lbl.configure(text=result, text_color=THEME_ACCENT_RED)
            self.slider.set_warning(True)
        else:
            start, end = result
            diff = end - start
            if profile and profile.max_duration and diff > profile.max_duration:
                warning_text = f"⚠️ {profile.name} max duration is {profile.max_duration}s! Selected: {diff:.1f}s"
                self.validation_lbl.configure(text=warning_text, text_color=THEME_ACCENT_RED)
                self.slider.set_warning(True)
            else:
                self.slider.set_warning(False)
                self.validation_lbl.configure(
                    text=f"✓ Valid Clip Size: {format_seconds_to_mmss(diff)}",
                    text_color=THEME_TEXT_PRIMARY
                )

    def _refresh_translations(self):
        lang = self.panel.app_state.current_lang
        self.lbl_profile.configure(text="Profil:" if lang == "tr" else ("Perfil:" if lang == "es" else "Profile:"))
        self.chk_precise.configure(text=TRANSLATIONS[lang]["lbl_clip_precise"])
        self.lbl_start.configure(text="Start:" if lang == "en" else ("Başlangıç:" if lang == "tr" else "Inicio:"))
        self.lbl_end.configure(text="End:" if lang == "en" else ("Bitiş:" if lang == "tr" else "Fin:"))
