# core/command_builder.py
import sys
import shlex
from pathlib import Path
from core.clip import parse_time_to_seconds

VIDEO_PRESET_HEIGHT = {
    "Maksimum (Best)": "Best",
    "Ultra HD (2160p)": "2160",
    "QHD (1440p)": "1440",
    "Full HD (1080p)": "1080",
    "Dengeli (720p)": "720",
    "Hizli (480p)": "480",
    "Ekonomi (360p)": "360",
    "Ozel (Custom)": "CUSTOM",
}

AUDIO_PRESET_QUALITY = {
    "Best": "0",
    "Yuksek (320K)": "320K",
    "Dengeli (192K)": "192K",
    "Kucuk Boyut (128K)": "128K",
}

DEFAULT_OUTPUT_TEMPLATE = "%(title)s [%(id)s].%(ext)s"
YOUTUBE_FALLBACK_EXTRACTOR_ARGS = "youtube:player-client=tv"

def effective_video_height(item_config: dict) -> str:
    selected = VIDEO_PRESET_HEIGHT.get(item_config.get("video_profile"), "1080")
    if selected == "CUSTOM":
        return item_config.get("video_limit", "1080")
    return selected

def build_command(item: dict, output_dir: str) -> list[str]:
    out_dir = str(Path(output_dir).expanduser())
    output_template = item.get("output_template", "").strip() or DEFAULT_OUTPUT_TEMPLATE
    cmd: list[str] = [sys.executable, "-m", "yt_dlp", "--newline", "-P", out_dir, "-o", output_template]

    mode = item.get("mode", "Video")
    if mode == "Video":
        quality = effective_video_height(item)
        audio_codec = item.get("video_audio_codec", "AAC").strip().upper()
        if audio_codec.startswith("AAC"):
            preferred_audio_selector = "ba[acodec^=mp4a]"
            secondary_audio_selector = "ba[ext=m4a]"
        else:
            preferred_audio_selector = "ba[acodec*=opus]"
            secondary_audio_selector = "ba[ext=webm]"
            
        if quality == "Best":
            video_selector = "bv*"
            fallback_selector = "b"
        else:
            video_selector = f"bv*[height<=?{quality}]"
            fallback_selector = f"b[height<=?{quality}]"

        selector = (
            f"{video_selector}+{preferred_audio_selector}/"
            f"{video_selector}+{secondary_audio_selector}/"
            f"{video_selector}+ba/"
            f"{fallback_selector}"
        )
        cmd.extend(["-f", selector, "--merge-output-format", item.get("video_container", "mp4")])
    else:
        audio_quality = AUDIO_PRESET_QUALITY.get(item.get("audio_quality", "Best"), "0")
        cmd.extend(["-x", "--audio-format", item.get("audio_format", "mp3"), "--audio-quality", audio_quality])

    if not item.get("playlist"):
        cmd.append("--no-playlist")
    if item.get("metadata"):
        cmd.append("--add-metadata")
    if item.get("thumbnail_flag"):
        cmd.extend(["--write-thumbnail", "--convert-thumbnails", "jpg"])
        if mode == "Audio":
            cmd.append("--embed-thumbnail")
    if item.get("subs"):
        cmd.extend(["--write-subs", "--sub-langs", "all,-live_chat"])
    if item.get("auto_subs"):
        cmd.append("--write-auto-subs")
    if item.get("restrict_names"):
        cmd.append("--restrict-filenames")

    # Bug Fix 1: SponsorBlock queue snapshot persistence (read from item snapshot)
    if item.get("sponsorblock"):
        cmd.extend(["--sponsorblock-remove", "all"])

    playlist_items = item.get("playlist_items", "").strip()
    if playlist_items:
        cmd.extend(["--playlist-items", playlist_items.replace(" ", "")])

    max_downloads = item.get("max_downloads", "").strip()
    if max_downloads:
        cmd.extend(["--max-downloads", max_downloads])

    rate_limit = item.get("rate_limit", "").strip()
    if rate_limit:
        cmd.extend(["--limit-rate", rate_limit])

    if item.get("archive"):
        archive_file = str(Path(out_dir) / ".downloaded_archive.txt")
        cmd.extend(["--download-archive", archive_file])

    retries = item.get("retries", "").strip()
    if retries:
        cmd.extend(["--retries", retries])

    concurrent_fragments = item.get("concurrent_fragments", "").strip()
    if concurrent_fragments:
        cmd.extend(["--concurrent-fragments", concurrent_fragments])

    cookies_file = item.get("cookies", "").strip()
    if cookies_file:
        cmd.extend(["--cookies", cookies_file])
    else:
        browser_cookies = item.get("browser_cookies", "").strip().lower()
        # Bug Fix 4: Fix locale-specific hardcoded "Kapali" check
        if browser_cookies and browser_cookies not in ("kapali", "disabled", "off", "closed", "none"):
            cmd.extend(["--cookies-from-browser", browser_cookies])

    # Time Range Clip Integration (Strateji 1 & 2: Seek/Precision & Hybrid Pass 1)
    if item.get("clip_enabled"):
        clip_strategy = item.get("clip_strategy", "stream_seek")
        start_str = item.get("clip_start", "00:00").strip()
        end_str = item.get("clip_end", "00:00").strip()
        
        start = parse_time_to_seconds(start_str) or 0.0
        end = parse_time_to_seconds(end_str) or 0.0
        
        if clip_strategy == "hybrid":
            # Pass 1: Seek with 5s safety buffer
            buffer = 5.0
            buffered_start = max(0.0, start - buffer)
            buffered_end = end + buffer
            cmd.extend([
                "--download-sections", f"*{buffered_start}-{buffered_end}",
                "--force-keyframes-at-cuts"
            ])
        elif clip_strategy == "stream_seek" or clip_strategy == "precise_cut":
            cmd.extend([
                "--download-sections", f"*{start_str}-{end_str}",
                "--force-keyframes-at-cuts"
            ])
            if item.get("clip_precise") or clip_strategy == "precise_cut":
                cmd.extend([
                    "--postprocessor-args",
                    f"ffmpeg:-ss {start_str} -to {end_str} -avoid_negative_ts make_zero"
                ])

    extra_args = item.get("extra_args", "").strip()
    if extra_args:
        cmd.extend(shlex.split(extra_args, posix=False))

    cmd.append(item.get("url"))
    return cmd

def format_cmd_for_log(cmd: list[str]) -> str:
    safe_parts = []
    for part in cmd:
        if " " in part or "\t" in part:
            safe_parts.append(f'"{part}"')
        else:
            safe_parts.append(part)
    return " ".join(safe_parts)
