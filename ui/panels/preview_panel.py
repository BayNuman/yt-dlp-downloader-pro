# ui/panels/preview_panel.py
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
from ui.theme import THEME_BG, THEME_CARD_BG, THEME_CARD_BORDER, THEME_TEXT_PRIMARY, THEME_TEXT_SECONDARY, THEME_ACCENT_BLUE, TRANSLATIONS
from core.app_state import AppState
from core.clip import format_seconds_to_mmss

class PreviewPanel(ctk.CTkFrame):
    def __init__(self, parent, state: AppState, on_chapter_click_callback, **kwargs):
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

    def show_loading(self):
        self.grid()
        self.thumb_label.grid_remove()
        self.meta_info.grid_remove()
        self.chapters_frame.grid_remove()
        self.preview_loading_lbl.grid()

    def hide(self):
        self.grid_remove()

    def show_metadata(self, meta: dict, thumbnail_img: ImageTk.PhotoImage = None):
        self.grid()
        self.preview_loading_lbl.grid_remove()
        self.thumb_label.grid()
        self.meta_info.grid()

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
            # Clear previous chapter buttons
            for child in self.chapters_frame.winfo_children():
                child.destroy()
            
            # Draw chapter tags
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

    def show_error(self):
        self.grid()
        self.thumb_label.grid_remove()
        self.meta_info.grid_remove()
        self.chapters_frame.grid_remove()
        self.preview_loading_lbl.configure(text=TRANSLATIONS[self.app_state.current_lang]["lbl_preview_err"])
        self.preview_loading_lbl.grid()

    def refresh_translations(self):
        lang = self.app_state.current_lang
        self.preview_loading_lbl.configure(text=TRANSLATIONS[lang]["lbl_preview_loading"])
        self.preview_title_lbl.configure(text=TRANSLATIONS[lang]["lbl_preview_title"])
        self.preview_author_lbl.configure(text=TRANSLATIONS[lang]["lbl_preview_author"])
        self.preview_dur_lbl.configure(text=TRANSLATIONS[lang]["lbl_preview_dur"])
