# ui/panels/progress_panel.py
import tkinter as tk
import customtkinter as ctk
from ui.theme import (
    THEME_BG, THEME_CARD_BG, THEME_CARD_BORDER, THEME_TEXT_PRIMARY,
    THEME_TEXT_SECONDARY, THEME_ACCENT_BLUE, THEME_ACCENT_INDIGO,
    THEME_ACCENT_GREEN, THEME_ACCENT_RED, TRANSLATIONS
)
from core.app_state import AppState, TaskStatus

class ProgressPanel(ctk.CTkFrame):
    def __init__(self, parent, state: AppState, on_start_callback, on_cancel_callback, on_open_folder_callback, **kwargs):
        super().__init__(
            parent,
            fg_color=THEME_CARD_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            corner_radius=16,
            **kwargs
        )
        self.app_state = state
        self.on_start = on_start_callback
        self.on_cancel = on_cancel_callback
        self.on_open_folder = on_open_folder_callback
        
        # 60-point circular buffer + EMA Low-pass filter for visual trend smoothness
        self.speed_history = [0.0] * 60
        self.speed_write_idx = 0
        self.ema_smoothed = 0.0
        
        self.grid_columnconfigure(0, weight=1)
        self._build_ui()

    def _build_ui(self):
        lang = self.app_state.current_lang

        # Button Grid Frame
        btn_grid = ctk.CTkFrame(self, fg_color="transparent")
        btn_grid.grid(row=0, column=0, padx=20, pady=(16, 12), sticky="ew")
        btn_grid.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # 1. Start Button (Huge primary action)
        self.start_btn = ctk.CTkButton(
            btn_grid,
            text=TRANSLATIONS[lang]["btn_start"],
            height=44,
            corner_radius=10,
            fg_color=THEME_ACCENT_INDIGO,
            text_color="#ffffff",
            hover_color=THEME_ACCENT_BLUE,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            command=self.on_start,
        )
        self.start_btn.grid(row=0, column=0, columnspan=2, padx=6, pady=2, sticky="ew")

        # 2. Cancel Button (Secondary destructive)
        self.cancel_btn = ctk.CTkButton(
            btn_grid,
            text=TRANSLATIONS[lang]["btn_cancel"],
            height=44,
            corner_radius=10,
            fg_color="transparent",
            text_color=THEME_ACCENT_RED,
            hover_color=("#fee2e2", "#271c24"),
            border_color=THEME_ACCENT_RED,
            border_width=1.5,
            state="disabled",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self.on_cancel,
        )
        self.cancel_btn.grid(row=0, column=2, padx=6, pady=2, sticky="ew")

        # 3. Clean Outline actions (neutral buttons)
        neutral_frame = ctk.CTkFrame(btn_grid, fg_color="transparent")
        neutral_frame.grid(row=0, column=3, padx=6, pady=2, sticky="ew")
        neutral_frame.grid_columnconfigure((0, 1), weight=1)

        self.clear_btn = ctk.CTkButton(
            neutral_frame,
            text=TRANSLATIONS[lang]["btn_clear"],
            height=44,
            corner_radius=10,
            fg_color=THEME_BG,
            text_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_CARD_BORDER,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self._clear_logs_textbox,
        )
        self.clear_btn.grid(row=0, column=0, padx=3, sticky="ew")

        self.open_folder_btn = ctk.CTkButton(
            neutral_frame,
            text=TRANSLATIONS[lang]["btn_open_folder"],
            height=44,
            corner_radius=10,
            fg_color=THEME_BG,
            text_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_CARD_BORDER,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self.on_open_folder,
        )
        self.open_folder_btn.grid(row=0, column=1, padx=3, sticky="ew")

        # ProgressBar Container
        progress_container = ctk.CTkFrame(self, fg_color="transparent")
        progress_container.grid(row=1, column=0, padx=20, pady=(6, 12), sticky="ew")
        progress_container.grid_columnconfigure(0, weight=1)
        progress_container.grid_columnconfigure(1, weight=0)

        self.progress_canvas = tk.Canvas(
            progress_container,
            height=12,
            bg=THEME_CARD_BG,
            highlightthickness=0,
            bd=0
        )
        self.progress_canvas.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.current_progress_value = 0.0
        self.segment_progress_values = [0.0] * 4
        self.is_segmented = False
        self.progress_color_override = None
        self.progress_canvas.bind("<Configure>", lambda e: self.draw_progress())

        self.percent_stat_var = ctk.StringVar(value="0%")
        self.percent_label = ctk.CTkLabel(
            progress_container,
            textvariable=self.percent_stat_var,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=THEME_ACCENT_INDIGO,
        )
        self.percent_label.grid(row=0, column=1, sticky="e")

        # Status text row
        status_row = ctk.CTkFrame(self, fg_color="transparent")
        status_row.grid(row=2, column=0, padx=20, pady=(0, 16), sticky="ew")
        status_row.grid_columnconfigure(1, weight=1)

        self.status_dot = ctk.CTkLabel(
            status_row,
            text="●",
            font=ctk.CTkFont(size=16),
            text_color=THEME_ACCENT_GREEN,
        )
        self.status_dot.grid(row=0, column=0, padx=(0, 6))

        self.status_var = ctk.StringVar(value=TRANSLATIONS[lang]["lbl_status_ready"])
        self.status_label = ctk.CTkLabel(
            status_row,
            textvariable=self.status_var,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME_TEXT_SECONDARY,
        )
        self.status_label.grid(row=0, column=1, sticky="w")

        # Active File Display
        self.active_file_var = ctk.StringVar(value=TRANSLATIONS[lang]["lbl_active_dl"])
        self.active_file_label = ctk.CTkLabel(
            self,
            textvariable=self.active_file_var,
            font=ctk.CTkFont(family="Segoe UI", size=11, slant="italic"),
            text_color=THEME_TEXT_SECONDARY,
            anchor="w",
            wraplength=550,
        )
        self.active_file_label.grid(row=3, column=0, padx=20, pady=(0, 12), sticky="ew")

        # Metrics Dashboard Grid
        self.dashboard_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.dashboard_frame.grid(row=4, column=0, padx=20, pady=(0, 16), sticky="ew")
        self.dashboard_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self._build_dashboard_stat(0, TRANSLATIONS[lang]["lbl_speed"], "0.0 MB/s", "_speed")
        self._build_dashboard_stat(1, TRANSLATIONS[lang]["lbl_eta"], "00:00:00", "_eta")
        self._build_dashboard_stat(2, TRANSLATIONS[lang]["lbl_size"], "0.0 MB", "_size")

        # Live Speed Sparkline Graph (Row 5 - created once with O(1)coords updates)
        self.graph_canvas = tk.Canvas(self, height=50, bg=THEME_BG, highlightthickness=0, bd=0)
        self.graph_canvas.grid(row=5, column=0, padx=20, pady=(0, 12), sticky="ew")
        
        # Grid lines (draw reference lines once)
        self.grid_lines = []
        for i in range(3):
            gl = self.graph_canvas.create_line(0, 0, 0, 0, fill="#2b3c5d", width=1, dash=(2, 4))
            self.grid_lines.append(gl)

        # Graph lines and fill (created once)
        self.graph_fill = self.graph_canvas.create_polygon(0, 0, 0, 0, fill="#6366f1", outline="")
        self.graph_line = self.graph_canvas.create_line(0, 0, 0, 0, fill="#6366f1", width=2, smooth=True)
        
        # Bind canvas resize to redraw
        self.graph_canvas.bind("<Configure>", lambda e: self._redraw_sparkline())

        # Terminal / System logs toggles (Row 6)
        self.logs_visible_var = ctk.BooleanVar(value=False)
        self.logs_switch = ctk.CTkSwitch(
            self,
            text=TRANSLATIONS[lang]["lbl_logs_toggle"],
            variable=self.logs_visible_var,
            progress_color=THEME_ACCENT_INDIGO,
            text_color=THEME_TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self._toggle_logs_section
        )
        self.logs_switch.grid(row=6, column=0, padx=20, pady=(0, 12), sticky="w")

        # Scrollable Logs Text Box (Row 7)
        self.log_textbox = ctk.CTkTextbox(
            self,
            height=130,
            corner_radius=10,
            fg_color=THEME_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            text_color=THEME_TEXT_SECONDARY,
            font=ctk.CTkFont(family="Consolas", size=10),
            state="normal"
        )
        self.log_textbox.grid(row=7, column=0, padx=20, pady=(0, 16), sticky="ew")
        self.log_textbox.grid_remove()

    def _build_dashboard_stat(self, col: int, label_text: str, value_text: str, attr_suffix: str):
        box = ctk.CTkFrame(self.dashboard_frame, fg_color=THEME_BG, corner_radius=10, border_color=THEME_CARD_BORDER, border_width=1)
        box.grid(row=0, column=col, padx=4, pady=4, sticky="ew")
        box.grid_columnconfigure(0, weight=1)

        lbl = ctk.CTkLabel(box, text=label_text, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color=THEME_TEXT_SECONDARY)
        lbl.grid(row=0, column=0, pady=(6, 2))

        val_var = ctk.StringVar(value=value_text)
        setattr(self, f"stat{attr_suffix}_var", val_var)
        setattr(self, f"stat{attr_suffix}_lbl", lbl)

        val_lbl = ctk.CTkLabel(box, textvariable=val_var, font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), text_color=THEME_ACCENT_INDIGO)
        val_lbl.grid(row=1, column=0, pady=(2, 6))

    def _toggle_logs_section(self):
        if self.logs_visible_var.get():
            self.log_textbox.grid()
        else:
            self.log_textbox.grid_remove()

    def _clear_logs_textbox(self):
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.app_state.terminal_logs.clear()

    def append_log(self, text: str):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", text)
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")
        self.app_state.terminal_logs.append(text)

    def append_log_batch(self, lines: list[str]):
        if not lines:
            return
        self.log_textbox.configure(state="normal")
        combined_text = "".join(lines)
        self.log_textbox.insert("end", combined_text)
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")
        self.app_state.terminal_logs.extend(lines)

    def draw_progress(self):
        w = self.progress_canvas.winfo_width()
        h = self.progress_canvas.winfo_height()
        if w < 10 or h < 2:
            return
        
        self.progress_canvas.delete("all")
        
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_col = THEME_BG[1] if is_dark else THEME_BG[0]
        
        # Resolve accent indigo / override color
        if self.progress_color_override:
            act_col = self.progress_color_override
        else:
            act_col = THEME_ACCENT_INDIGO[1] if is_dark else THEME_ACCENT_INDIGO[0]
            
        r = h / 2
        # Background pill track
        self.progress_canvas.create_oval(0, 0, h, h, fill=bg_col, outline="")
        self.progress_canvas.create_oval(w - h, 0, w, h, fill=bg_col, outline="")
        self.progress_canvas.create_rectangle(r, 0, w - r, h, fill=bg_col, outline="")
        
        if not self.is_segmented:
            val = max(0.0, min(1.0, self.current_progress_value))
            if val > 0.0:
                bar_w = val * w
                if bar_w >= h:
                    self.progress_canvas.create_oval(0, 0, h, h, fill=act_col, outline="")
                    self.progress_canvas.create_oval(bar_w - h, 0, bar_w, h, fill=act_col, outline="")
                    self.progress_canvas.create_rectangle(r, 0, bar_w - r, h, fill=act_col, outline="")
                else:
                    self.progress_canvas.create_oval(0, 0, bar_w, h, fill=act_col, outline="")
        else:
            # High-tech segment rendering
            n = len(self.segment_progress_values)
            gap = 4.0
            seg_w = (w - (n - 1) * gap) / n
            
            # Diverse premium colors for visual segment differentiation
            blue_col = THEME_ACCENT_BLUE[1] if is_dark else THEME_ACCENT_BLUE[0]
            seg_colors = [act_col, blue_col, "#8b5cf6", "#ec4899"] if not self.progress_color_override else [act_col] * n
            
            for i in range(n):
                val = max(0.0, min(1.0, self.segment_progress_values[i]))
                seg_x0 = i * (seg_w + gap)
                
                # Draw hollow background for the segment if empty
                if val <= 0.0:
                    self.progress_canvas.create_rectangle(seg_x0, 0, seg_x0 + seg_w, h, fill=bg_col, outline="")
                else:
                    seg_x1 = seg_x0 + seg_w * val
                    color = seg_colors[i % len(seg_colors)]
                    
                    # Round edges for start and end segments
                    if i == 0 and val >= 1.0:
                        self.progress_canvas.create_oval(seg_x0, 0, seg_x0 + h, h, fill=color, outline="")
                    if i == n - 1 and val >= 1.0:
                        self.progress_canvas.create_oval(seg_x0 + seg_w - h, 0, seg_x0 + seg_w, h, fill=color, outline="")
                        
                    self.progress_canvas.create_rectangle(seg_x0, 0, seg_x1, h, fill=color, outline="")

    def set_progress(self, percent: float):
        self.current_progress_value = percent
        self.is_segmented = False
        self.percent_stat_var.set(f"{int(percent * 100)}%")
        self.draw_progress()

    def set_segmented_progress(self, segments: list[float]):
        self.segment_progress_values = segments
        self.is_segmented = True
        avg = sum(segments) / len(segments)
        self.current_progress_value = avg
        self.percent_stat_var.set(f"{int(avg * 100)}%")
        self.draw_progress()

    def show_completion_animation(self, success=True):
        is_dark = ctk.get_appearance_mode() == "Dark"
        green_col = THEME_ACCENT_GREEN[1] if is_dark else THEME_ACCENT_GREEN[0]
        red_col = THEME_ACCENT_RED[1] if is_dark else THEME_ACCENT_RED[0]
        
        if success:
            self.progress_color_override = green_col
            self.percent_stat_var.set("✓ 100%")
            self.percent_label.configure(text_color=green_col)
        else:
            self.progress_color_override = red_col
            self.percent_label.configure(text_color=red_col)
        self.draw_progress()

    def update_global_progress(self, queue_list: list):
        if not queue_list:
            self.current_progress_value = 0.0
            self.is_segmented = False
            self.percent_stat_var.set("0%")
            self.draw_progress()
            self.set_stats("0.0 KB/s", "--:--", "0.0 MB")
            return
            
        total_percent = 0.0
        active_speeds = []
        active_etas = []
        total_sizes = []
        
        # Calculate unified stats concurrently
        for task in queue_list:
            total_percent += task.percent
            # Collect active stats to show combined values
            if task.status_code == TaskStatus.DOWNLOADING:
                if task.speed and "0.0" not in task.speed and "Unknown" not in task.speed:
                    active_speeds.append(task.speed)
                if task.eta and "--" not in task.eta:
                    active_etas.append(task.eta)
                if task.size and "0.0" not in task.size:
                    total_sizes.append(task.size)
                    
        avg_percent = total_percent / len(queue_list)
        p_val = avg_percent / 100.0
        
        # Dynamic check if concurrent fragments is active
        cf = getattr(self.app_state.preferences, "concurrent_fragments", 1)
        if cf > 1:
            segs = []
            for i in range(cf):
                seg_val = max(0.0, min(1.0, (p_val - i * (1.0 / cf)) / (1.0 / cf)))
                segs.append(seg_val)
            self.set_segmented_progress(segs)
        else:
            self.set_progress(p_val)

        # Set aggregated metrics
        combined_speed = active_speeds[0] if active_speeds else "0.0 KB/s"
        combined_eta = active_etas[0] if active_etas else "--:--"
        combined_size = total_sizes[0] if total_sizes else "0.0 MB"
        
        self.set_stats(combined_speed, combined_eta, combined_size)

    def update_status(self, dot: str, color: str, message: str):
        self.status_dot.configure(text=dot, text_color=color)
        self.status_var.set(message)

    def set_stats(self, speed: str, eta: str, size: str):
        self.stat_speed_var.set(speed)
        self.stat_eta_var.set(eta)
        self.stat_size_var.set(size)
        self.push_speed(speed)

    def set_running_state(self, running: bool):
        if running:
            self.start_btn.configure(state="disabled")
            self.cancel_btn.configure(state="normal")
            self.progress_color_override = None
            is_dark = ctk.get_appearance_mode() == "Dark"
            indigo_col = THEME_ACCENT_INDIGO[1] if is_dark else THEME_ACCENT_INDIGO[0]
            self.percent_label.configure(text_color=indigo_col)
        else:
            self.start_btn.configure(state="normal")
            self.cancel_btn.configure(state="disabled")
            self.reset_sparkline()

    def push_speed(self, speed_str: str):
        raw_mbps = self._parse_speed_to_mbps(speed_str)
        # EMA Low-pass filter (α = 0.2, 1-α = 0.8) to keep transitions smooth
        self.ema_smoothed = (raw_mbps * 0.2) + (self.ema_smoothed * 0.8)
        
        self.speed_history[self.speed_write_idx] = self.ema_smoothed
        self.speed_write_idx = (self.speed_write_idx + 1) % 60
        self._redraw_sparkline()

    def reset_sparkline(self):
        self.speed_history = [0.0] * 60
        self.speed_write_idx = 0
        self.ema_smoothed = 0.0
        self._redraw_sparkline()

    def _parse_speed_to_mbps(self, speed_str: str) -> float:
        if not speed_str:
            return 0.0
        import re
        # Parse value and unit (e.g. 15.3MiB/s, 200B/s)
        match = re.search(r"([\d\.]+)\s*([a-zA-Z/]+)", speed_str)
        if not match:
            return 0.0
        val = float(match.group(1))
        unit = match.group(2).lower()
        
        if "g" in unit:
            return val * 1024.0
        elif "m" in unit:
            return val
        elif "k" in unit:
            return val / 1024.0
        elif "b" in unit:
            return val / (1024.0 * 1024.0)
        return val

    def _redraw_sparkline(self):
        """O(1) coordinate update on single canvas elements — completely leaks-free."""
        if not hasattr(self, "graph_canvas"):
            return
        w = self.graph_canvas.winfo_width()
        h = self.graph_canvas.winfo_height()
        if w < 10 or h < 10:
            return
            
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_col = "#121b2d" if is_dark else "#f1f5f9"
        fill_col = "#1e2c4a" if is_dark else "#cbd5e1"
        line_col = "#6366f1" if is_dark else "#4f46e5"
        grid_col = "#2b3c5d" if is_dark else "#cbd5e1"
        
        self.graph_canvas.configure(bg=bg_col)
        self.graph_canvas.itemconfigure(self.graph_line, fill=line_col)
        self.graph_canvas.itemconfigure(self.graph_fill, fill=fill_col)
        
        # Position reference grid lines
        for i, gl in enumerate(self.grid_lines):
            self.graph_canvas.itemconfigure(gl, fill=grid_col)
            y = h * (1.0 - (i + 1) / 4.0)
            self.graph_canvas.coords(gl, 0, y, w, y)
            
        # Re-align circular buffer sequentially from write index
        ordered = self.speed_history[self.speed_write_idx:] + self.speed_history[:self.speed_write_idx]
        max_val = max(max(ordered), 0.01)
        
        points = []
        for i, val in enumerate(ordered):
            x = (i / 59) * w
            y = h - (val / max_val) * (h - 4)
            points.extend([x, y])
            
        self.graph_canvas.coords(self.graph_line, *points)
        fill_points = [0, h] + points + [w, h]
        self.graph_canvas.coords(self.graph_fill, *fill_points)

    def refresh_translations(self):
        lang = self.app_state.current_lang
        self.start_btn.configure(text=TRANSLATIONS[lang]["btn_start"])
        self.cancel_btn.configure(text=TRANSLATIONS[lang]["btn_cancel"])
        self.clear_btn.configure(text=TRANSLATIONS[lang]["btn_clear"])
        self.open_folder_btn.configure(text=TRANSLATIONS[lang]["btn_open_folder"])
        
        self.status_var.set(TRANSLATIONS[lang]["lbl_status_ready"])
        self.active_file_var.set(TRANSLATIONS[lang]["lbl_active_dl"])
        self.logs_switch.configure(text=TRANSLATIONS[lang]["lbl_logs_toggle"])
        
        self.stat_speed_lbl.configure(text=TRANSLATIONS[lang]["lbl_speed"])
        self.stat_eta_lbl.configure(text=TRANSLATIONS[lang]["lbl_eta"])
        self.stat_size_lbl.configure(text=TRANSLATIONS[lang]["lbl_size"])
