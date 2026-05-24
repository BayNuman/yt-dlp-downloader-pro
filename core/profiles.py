# core/profiles.py
from typing import List, Optional

class ExportProfile:
    def __init__(self, name: str, ext: str, max_duration: Optional[float] = None):
        self.name = name
        self.ext = ext
        self.max_duration = max_duration

    def get_ffmpeg_args(self, duration_sec: float) -> List[str]:
        # Default fallback: lossless stream copy
        return ["-c:v", "copy", "-c:a", "copy"]

class StandardProfile(ExportProfile):
    def __init__(self, name: str, ext: str):
        super().__init__(name, ext)

    def get_ffmpeg_args(self, duration_sec: float) -> List[str]:
        if self.ext == "mp3":
            return ["-vn", "-c:a", "libmp3lame", "-b:a", "192k"]
        return ["-c:v", "copy", "-c:a", "copy"]

class SizeBoundedProfile(ExportProfile):
    def __init__(self, name: str, target_mb: float):
        super().__init__(name, "mp4")
        self.target_mb = target_mb

    def get_ffmpeg_args(self, duration_sec: float) -> List[str]:
        d = max(0.5, duration_sec)
        # Target with 5% safety margin:
        target_kb = (self.target_mb * 0.95) * 8192
        total_bitrate = target_kb / d
        
        audio_bitrate = 96.0  # Light AAC audio
        video_bitrate = max(100.0, total_bitrate - audio_bitrate)
        
        return [
            "-c:v", "libx264",
            "-b:v", f"{int(video_bitrate)}k",
            "-c:a", "aac",
            "-b:a", f"{int(audio_bitrate)}k",
            "-preset", "veryfast"
        ]

class MemeGifProfile(ExportProfile):
    def __init__(self, name: str):
        super().__init__(name, "gif")

    def get_ffmpeg_args(self, duration_sec: float) -> List[str]:
        # Output as silent high-quality loop gif with split-palettegen-paletteuse filter pipeline
        return [
            "-an",
            "-vf", "fps=15,scale=480:-1:flags=lanczos[x];[x]split[y][z];[y]palettegen[p];[z][p]paletteuse",
            "-f", "gif"
        ]

class AudiobookProfile(ExportProfile):
    def __init__(self, name: str):
        super().__init__(name, "m4a")

    def get_ffmpeg_args(self, duration_sec: float) -> List[str]:
        # Mono channel, low bitrate voice note optimization
        return [
            "-vn",
            "-ac", "1",
            "-c:a", "aac",
            "-b:a", "48k"
        ]

class CenterCropProfile(ExportProfile):
    def __init__(self, name: str, max_duration: Optional[float] = None):
        super().__init__(name, "mp4", max_duration)

    def get_ffmpeg_args(self, duration_sec: float) -> List[str]:
        # Mathematical 16:9 to 9:16 vertical center crop with horizontal offset calculation
        return [
            "-vf", "crop=ih*(9/16):ih:(iw-ih*(9/16))/2:0",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-c:a", "copy"
        ]

EXPORT_PROFILES = {
    "Default (No Profile)": StandardProfile("Default", "mp4"),
    "Instagram Reels (Max 90s, 9:16 Crop)": CenterCropProfile("Instagram Reels", max_duration=90),
    "YouTube Shorts (Max 60s, 9:16 Crop)": CenterCropProfile("YouTube Shorts", max_duration=60),
    "Discord Share (Max 25MB)": SizeBoundedProfile("Discord Share", target_mb=25),
    "WhatsApp Share (Max 16MB)": SizeBoundedProfile("WhatsApp Share", target_mb=16),
    "Meme / GIF Creator (No Audio, 15fps)": MemeGifProfile("Meme / GIF"),
    "Voice Note / Audiobook (Mono, Light M4A)": AudiobookProfile("Audiobook")
}
