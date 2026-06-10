# ui/components/range_slider.py
import customtkinter as ctk

class CTkRangeSlider(ctk.CTkCanvas):
    """
    A custom double-node (range selection) slider designed to fit glassmorphic CustomTkinter aesthetics.
    Draws a single horizontal line with two active circular handle nodes that represent Start and End range boundaries.
    """
    def __init__(self, parent, min_val=0.0, max_val=100.0, start_val=0.0, end_val=100.0, command=None, **kwargs):
        super().__init__(parent, highlightthickness=0, borderwidth=0, **kwargs)
        self.min_val = min_val
        self.max_val = max_val
        self.value_start = start_val
        self.value_end = end_val
        self.command = command
        self.state = "normal"
        self.is_warning = False  # Warning state trigger for limits violations
        self.pad = 12
        self.active_handle = None
        self.sponsor_segments = []  # Premium SponsorBlock timeline segments

        self.bind("<Button-1>", self._on_click)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Configure>", lambda e: self.draw())

    def _get_colors(self):
        is_dark = ctk.get_appearance_mode() == "Dark"
        if self.state == "disabled":
            track_bg = "#1b2336" if is_dark else "#cbd5e1"
            track_fg = "#2e3b52" if is_dark else "#94a3b8"
            handle_bg = "#475569" if is_dark else "#cbd5e1"
            handle_inner = "#2e3b52" if is_dark else "#94a3b8"
        elif self.is_warning:
            track_bg = "#3d1e25" if is_dark else "#fee2e2"
            track_fg = "#f43f5e" if is_dark else "#dc2626"
            handle_bg = "#f43f5e" if is_dark else "#dc2626"
            handle_inner = "#ffffff"
        else:
            track_bg = "#22334f" if is_dark else "#e2e8f0"
            track_fg = "#6366f1" if is_dark else "#4f46e5"
            handle_bg = "#00d2ff" if is_dark else "#2563eb"
            handle_inner = "#ffffff"
        return track_bg, track_fg, handle_bg, handle_inner

    def draw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 10 or h < 10:
            return

        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_color = "#121b2d" if is_dark else "#ffffff"
        self.configure(bg=bg_color)

        cy = h / 2
        track_bg, track_fg, handle_bg, handle_inner = self._get_colors()

        # Draw background track
        self.create_line(self.pad, cy, w - self.pad, cy, fill=track_bg, width=6, capstyle="round")

        usable_width = w - 2 * self.pad
        div = (self.max_val - self.min_val) if (self.max_val - self.min_val) > 0 else 1.0

        # Draw active highlighted region
        x_start = self.pad + ((self.value_start - self.min_val) / div) * usable_width
        x_end = self.pad + ((self.value_end - self.min_val) / div) * usable_width

        self.create_line(x_start, cy, x_end, cy, fill=track_fg, width=6, capstyle="round")

        # Draw Start handle
        r = 8
        self.create_oval(x_start - r, cy - r, x_start + r, cy + r, fill=handle_bg, outline="")
        self.create_oval(x_start - r/2, cy - r/2, x_start + r/2, cy + r/2, fill=handle_inner, outline="")

        # Draw End handle
        self.create_oval(x_end - r, cy - r, x_end + r, cy + r, fill=handle_bg, outline="")
        self.create_oval(x_end - r/2, cy - r/2, x_end + r/2, cy + r/2, fill=handle_inner, outline="")

    def set_values(self, start, end):
        self.value_start = max(self.min_val, min(start, self.max_val))
        self.value_end = max(self.min_val, min(end, self.max_val))
        if self.value_start > self.value_end:
            self.value_start, self.value_end = self.value_end, self.value_start
        self.draw()

    def set_warning(self, val: bool):
        if self.is_warning != val:
            self.is_warning = val
            self.draw()

    def configure(self, **kwargs):
        if "state" in kwargs:
            self.state = kwargs["state"]
            self.draw()
            del kwargs["state"]
        super().configure(**kwargs)

    def _on_click(self, event):
        if self.state == "disabled":
            return
        w = self.winfo_width()
        usable_width = w - 2 * self.pad
        div = (self.max_val - self.min_val) if (self.max_val - self.min_val) > 0 else 1.0

        x_start = self.pad + ((self.value_start - self.min_val) / div) * usable_width
        x_end = self.pad + ((self.value_end - self.min_val) / div) * usable_width

        dist_start = abs(event.x - x_start)
        dist_end = abs(event.x - x_end)

        if dist_start < dist_end:
            self.active_handle = "start"
        else:
            self.active_handle = "end"

        self._on_drag(event)

    def _on_drag(self, event):
        if self.state == "disabled" or not self.active_handle:
            return
        w = self.winfo_width()
        usable_width = w - 2 * self.pad
        if usable_width <= 0:
            return

        ratio = (event.x - self.pad) / usable_width
        ratio = max(0.0, min(ratio, 1.0))
        val = self.min_val + ratio * (self.max_val - self.min_val)

        buffer = 0.5  # Prevents crossover handles
        if self.active_handle == "start":
            self.value_start = min(val, self.value_end - buffer)
        else:
            self.value_end = max(val, self.value_start + buffer)

        self.draw()
        if self.command:
            self.command(self.value_start, self.value_end)

    def _on_release(self, event):
        self.active_handle = None
