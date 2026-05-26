# core/command_builder.py
import sys
import shlex
import os
import atexit
from pathlib import Path
from core.clip import parse_time_to_seconds

_created_temp_files = []

def _cleanup_temp_files():
    for path in _created_temp_files:
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

atexit.register(_cleanup_temp_files)

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

def safe_get(obj, key, default=None):
    if isinstance(obj, dict):
        val = obj.get(key, default)
        return default if val is None else val
    val = getattr(obj, key, default)
    return default if val is None else val

def safe_set(obj, key, value):
    if isinstance(obj, dict):
        obj[key] = value
    else:
        setattr(obj, key, value)

def sanitize_extra_args(extra_args_str: str) -> list[str]:
    if not extra_args_str.strip():
        return []
    
    try:
        parts = shlex.split(extra_args_str, posix=False)
    except Exception:
        parts = extra_args_str.split()
        
    blacklist = {
        "--exec", "--exec-before-download", "--exec-cmd", "-e",
        "--downloader", "--external-downloader",
        "--downloader-args", "--external-downloader-args"
    }
    
    sanitized_parts = []
    skip_next = False
    
    for i, part in enumerate(parts):
        if skip_next:
            skip_next = False
            continue
            
        part_clean = part.strip()
        part_lower = part_clean.lower()
        
        is_blocked = False
        for blocked_arg in blacklist:
            if part_lower == blocked_arg:
                is_blocked = True
                break
            if part_lower.startswith(blocked_arg + "="):
                is_blocked = True
                break
                
        if is_blocked:
            print(f"[Security Protection] Blocked dangerous parameter: {part}")
            if "=" not in part_clean and i + 1 < len(parts):
                skip_next = True
            continue
            
        sanitized_parts.append(part)
        
    return sanitized_parts

def effective_video_height(item) -> str:
    selected = VIDEO_PRESET_HEIGHT.get(safe_get(item, "video_profile"), "1080")
    if selected == "CUSTOM":
        return safe_get(item, "video_limit", "1080")
    return selected

def build_command(item, output_dir: str) -> list[str]:
    import tempfile
    import json
    
    out_dir = str(Path(output_dir).expanduser())
    output_template = str(safe_get(item, "output_template", "")).strip() or DEFAULT_OUTPUT_TEMPLATE
    cmd: list[str] = [sys.executable, "-m", "yt_dlp", "--newline", "-P", out_dir, "-o", output_template]

    # If pre-fetched metadata exists (Multi-Clip Single-Fetch), inject it to avoid double-fetching network calls
    video_info = safe_get(item, "video_info")
    if video_info:
        try:
            # Create a temporary file to write cached JSON metadata
            temp_json = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json", encoding="utf-8")
            json.dump(video_info, temp_json, ensure_ascii=False)
            temp_json.close()
            # Cache the temp path so downloader can clean it up
            safe_set(item, "_temp_info_json", temp_json.name)
            cmd.extend(["--load-info-json", temp_json.name])
        except Exception as e:
            print(f"[warning] Failed to write --load-info-json temp file: {e}")

    mode = safe_get(item, "mode", "Video")
    if mode == "Video":
        quality = effective_video_height(item)
        audio_codec = str(safe_get(item, "video_audio_codec", "AAC")).strip().upper()
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
        cmd.extend(["-f", selector, "--merge-output-format", safe_get(item, "video_container", "mp4")])
    else:
        audio_quality = AUDIO_PRESET_QUALITY.get(safe_get(item, "audio_quality", "Best"), "0")
        cmd.extend(["-x", "--audio-format", safe_get(item, "audio_format", "mp3"), "--audio-quality", audio_quality])

    if not safe_get(item, "playlist"):
        cmd.append("--no-playlist")
    if safe_get(item, "metadata"):
        cmd.append("--add-metadata")
    if safe_get(item, "thumbnail_flag"):
        cmd.extend(["--write-thumbnail", "--convert-thumbnails", "jpg"])
        if mode == "Audio":
            cmd.append("--embed-thumbnail")
    if safe_get(item, "subs"):
        cmd.extend(["--write-subs", "--sub-langs", "all,-live_chat"])
    if safe_get(item, "auto_subs"):
        cmd.append("--write-auto-subs")
    if safe_get(item, "restrict_names"):
        cmd.append("--restrict-filenames")

    if safe_get(item, "sponsorblock"):
        cmd.extend(["--sponsorblock-remove", "all"])

    playlist_items = str(safe_get(item, "playlist_items", "")).strip()
    if playlist_items:
        cmd.extend(["--playlist-items", playlist_items.replace(" ", "")])

    max_downloads = str(safe_get(item, "max_downloads", "")).strip()
    if max_downloads:
        cmd.extend(["--max-downloads", max_downloads])

    rate_limit = str(safe_get(item, "rate_limit", "")).strip()
    if rate_limit:
        cmd.extend(["--limit-rate", rate_limit])

    if safe_get(item, "archive"):
        from core.history import get_app_data_dir
        archive_file = str(get_app_data_dir() / "download_archive.txt")
        cmd.extend(["--download-archive", archive_file])

    retries = str(safe_get(item, "retries", "")).strip()
    if retries:
        cmd.extend(["--retries", retries])

    concurrent_fragments = str(safe_get(item, "concurrent_fragments", "")).strip()
    if concurrent_fragments:
        cmd.extend(["--concurrent-fragments", concurrent_fragments])

    cookies_file = str(safe_get(item, "cookies", "")).strip()
    if cookies_file:
        cmd.extend(["--cookies", cookies_file])
    else:
        browser_cookies = str(safe_get(item, "browser_cookies", "")).strip().lower()
        if browser_cookies and browser_cookies not in ("kapali", "disabled", "off", "closed", "none"):
            cmd.extend(["--cookies-from-browser", browser_cookies])

    if safe_get(item, "clip_enabled"):
        clip_strategy = safe_get(item, "clip_strategy", "stream_seek")
        # DESIGN NOTE (full_trim): Under "full_trim", we intentionally do NOT inject yt-dlp section downloads.
        # This is an intentional design contract: the whole file is downloaded first, then trimmed in downloader.py
        # post-processing using FFmpeg to guarantee frame accuracy and codec stability.
        start_str = str(safe_get(item, "clip_start", "00:00")).strip()
        end_str = str(safe_get(item, "clip_end", "00:00")).strip()
        
        start = parse_time_to_seconds(start_str) or 0.0
        end = parse_time_to_seconds(end_str) or 0.0
        
        if clip_strategy == "hybrid":
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
            if safe_get(item, "clip_precise") or clip_strategy == "precise_cut":
                cmd.extend([
                    "--postprocessor-args",
                    f"ffmpeg:-ss {start_str} -to {end_str} -avoid_negative_ts make_zero"
                ])

    extra_args = str(safe_get(item, "extra_args", "")).strip()
    if extra_args:
        cmd.extend(sanitize_extra_args(extra_args))

    cmd.append(safe_get(item, "url"))
    return cmd

def format_cmd_for_log(cmd: list[str]) -> str:
    safe_parts = []
    for part in cmd:
        if " " in part or "\t" in part:
            safe_parts.append(f'"{part}"')
        else:
            safe_parts.append(part)
    return " ".join(safe_parts)
