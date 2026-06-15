# yt-dlp Downloader Pro - Desktop Codebase Anthology

This document compiles the complete, production-ready desktop codebase of **yt-dlp Downloader Pro** into a single, beautifully structured reference file. It is optimized for engineering peer review, codebase auditing, and architecture inspection.

## 🏗️ Architectural Architecture & Design Patterns

The desktop side of the application is a high-fidelity desktop download manager built on **CustomTkinter** (UI) and **yt-dlp** + **FFmpeg** (Core Engine). It incorporates sophisticated patterns, modern aesthetics (glassmorphic styling, smooth micro-animations), and highly optimized algorithms:

1. **Greedy Interval Merging (LeetCode 56) in `core/clip.py`**:
   - When a user cuts multiple time-segments from a single video, downloading each segment individually is highly inefficient due to redundant network I/O.
   - The system utilizes a greedy merging algorithm (`optimize_clip_intervals`) with a configurable gap threshold (e.g., 30 seconds). It merges overlapping or closely situated time ranges into a minimal set of "Macro-Clips" which are downloaded in a single pass.
   - Post-download, the master file is sliced into individual "Micro-Clips" losslessly or re-encoded based on their custom export profiles, and optionally joined back together using the **FFmpeg Concat Demuxer** in `core/merger.py`.

2. **Polymorphic Export Profiles in `core/profiles.py`**:
   - Clipping segments can utilize targeted export profiles like *Instagram Reels*, *YouTube Shorts*, *Discord/WhatsApp size-bounded compression* (calculates target bitrates with safety margins), *Meme GIF Creator*, or *Audiobook Voice Optimization*.
   - Implemented via a clean object-oriented hierarchy (`ExportProfile` -> `StandardProfile`, `SizeBoundedProfile`, `CenterCropProfile`, etc.).

3. **Dynamic Path Reloader in `core/env.py`**:
   - Solves the problem of missing platform dependencies (like Node/Deno) installed while the app is running.
   - Dynamically parses the Windows registry and process environment variables to refresh the active `PATH` on the fly, allowing runtime discovery of Deno/Node without application restart.

4. **Polymorphic Profile Registry in `core/presets.py`**:
   - Empowers users to save, edit, and delete their own custom download presets (format, quality, concurrent fragments, metadata tags) stored as persistent JSON config templates.

5. **Heuristic Format Suggestion Engine in `core/suggester.py`**:
   - Analyzes raw metadata (dimensions, duration, category tags, title keywords) to predict the best format/preset (standard video, vertical video, music, or long speech/podcast) and prompts the user with actionable suggestions.

6. **SQLite Persistence Engine in `core/history.py`**:
   - Tracks persistent download records, file paths, and metadata in an SQLite local database, enabling re-downloads and native cross-platform folder exploration.

7. **Actionable Toast Notification System in `ui/components/toast.py` and `core/downloader.py`**:
   - A modern custom notification window that fades in, positions itself above the taskbar, and offers quick buttons to *Play*, *Show in Explorer*, or *Copy Path*.

## 📂 Codebase Table of Contents
- [app.py](#file-apppy)
- [core/env.py](#file-coreenvpy)
- [core/app_state.py](#file-coreapp_statepy)
- [core/clip.py](#file-coreclippy)
- [core/command_builder.py](#file-corecommand_builderpy)
- [core/merger.py](#file-coremergerpy)
- [core/suggester.py](#file-coresuggesterpy)
- [core/updater.py](#file-coreupdaterpy)
- [core/presets.py](#file-corepresetspy)
- [core/profiles.py](#file-coreprofilespy)
- [core/history.py](#file-corehistorypy)
- [core/downloader.py](#file-coredownloaderpy)
- [ui/theme.py](#file-uithemepy)
- [ui/components/toast.py](#file-uicomponentstoastpy)
- [ui/panels/url_panel.py](#file-uipanelsurl_panelpy)
- [ui/panels/preview_panel.py](#file-uipanelspreview_panelpy)
- [ui/panels/queue_panel.py](#file-uipanelsqueue_panelpy)
- [ui/panels/advanced_panel.py](#file-uipanelsadvanced_panelpy)
- [ui/panels/progress_panel.py](#file-uipanelsprogress_panelpy)
- [ui/main_window.py](#file-uimain_windowpy)

---

## <a name="file-apppy"></a> 📄 File: `app.py`
**Responsibility**: Entry point of the desktop application. Initializes state and boots the main window thread.

```python
# app.py
"""
yt-dlp Downloader Pro - Desktop Entry Point
A zero-config, premium glassmorphic media downloader powered by yt-dlp + ffmpeg.
"""

from core.env import refresh_path_env
# Refresh path environment variables on startup before importing anything else to pick up runtime updates like Deno
refresh_path_env()

import sys
if len(sys.argv) > 2 and sys.argv[1] == "-m" and sys.argv[2] == "yt_dlp":
    import yt_dlp
    sys.exit(yt_dlp.main(sys.argv[3:]))

from core.app_state import AppState
from ui.main_window import MainWindow

from core.logging_setup import setup_logging

def purge_scratch_directory():
    """
    Deterministik olarak önceki oturumlardan kalan tüm geçici 
    dosyaları başlangıç anında temizler.
    """
    import shutil
    from pathlib import Path
    scratch_dir = Path.home() / ".yt-downloader-scratch"
    
    if scratch_dir.exists():
        try:
            shutil.rmtree(scratch_dir, ignore_errors=True)
        except Exception as e:
            import logging
            logging.error(f"[Garbage Collection] I/O Error: {e}")
            
    # Temiz bir başlangıç için klasörü yeniden oluştur
    scratch_dir.mkdir(parents=True, exist_ok=True)

def main() -> None:
    # 0. Initialize central logging system
    setup_logging()
    
    # 1. Deterministik başlangıç çöp toplama (Garbage Collection)
    purge_scratch_directory()
    
    # 2. Initialize central application state configuration
    state = AppState()
    
    # 2. Boot up the main graphical window layout orchestrator
    app = MainWindow(state)
    
    # 3. Fire up the Tkinter main event thread loop
    app.mainloop()

if __name__ == "__main__":
    main()

```

---

## <a name="file-coreenvpy"></a> 📄 File: `core/env.py`
**Responsibility**: Dynamic PATH environment reloader. Pulls Windows registry changes in real time so runtime winget/deno installs work immediately.

```python
# core/env.py
import os
import sys

def refresh_path_env() -> None:
    """
    Dynamically loads the latest Windows PATH environment variables from the registry
    to pick up newly installed tools (like Deno or Node.js via winget) without requiring 
    a system or application restart.
    """
    if sys.platform != "win32":
        return

    try:
        import winreg
        paths = []
        
        # 1. Query Registry for User-level Environment PATH
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ) as key:
                val, _ = winreg.QueryValueEx(key, "Path")
                if val:
                    paths.extend(val.split(os.pathsep))
        except Exception:
            pass

        # 2. Query Registry for System-level (Machine) Environment PATH
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"System\CurrentControlSet\Control\Session Manager\Environment", 0, winreg.KEY_READ) as key:
                val, _ = winreg.QueryValueEx(key, "Path")
                if val:
                    paths.extend(val.split(os.pathsep))
        except Exception:
            pass

        # 3. Add explicit check for Winget Local Packages directory where Deno/Node.js is usually extracted
        winget_packages_dir = os.path.expandvars(r"%USERPROFILE%\AppData\Local\Microsoft\WinGet\Packages")
        if os.path.exists(winget_packages_dir):
            base_depth = winget_packages_dir.rstrip(os.path.sep).count(os.path.sep)
            for root, dirs, files in os.walk(winget_packages_dir):
                current_depth = root.rstrip(os.path.sep).count(os.path.sep) - base_depth
                if current_depth >= 3:
                    del dirs[:]  # Stop descending further
                if "deno.exe" in files or "node.exe" in files:
                    paths.append(root)

        # 4. Filter empty/duplicate paths and update the active process environment
        seen = set()
        cleaned_paths = []
        
        # Prepend the current path elements to avoid losing any dynamic paths added at runtime
        current_env_paths = os.environ.get("PATH", "").split(os.pathsep)
        for p in current_env_paths + paths:
            p_clean = os.path.expandvars(p.strip())
            if p_clean and p_clean not in seen:
                seen.add(p_clean)
                cleaned_paths.append(p_clean)
                
        os.environ["PATH"] = os.pathsep.join(cleaned_paths)
    except Exception as e:
        print(f"Error refreshing PATH: {e}")

```

---

## <a name="file-coreapp_statepy"></a> 📄 File: `core/app_state.py`
**Responsibility**: Centralized AppState data class which acts as a single source of truth for settings, active queues, log feeds, and cancellation tokens.

```python
# core/app_state.py
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

@dataclass
class DownloadTask:
    id: str
    url: str
    title: str
    duration: str
    preset: str
    status: str
    status_code: TaskStatus = TaskStatus.PENDING
    mode: str = "Video"  # "Video" or "Audio"

    # Profile & resolution configuration
    video_profile: str = "Full HD (1080p)"
    video_limit: str = "1080"
    video_container: str = "mp4"
    video_audio_codec: str = "AAC"
    audio_format: str = "mp3"
    audio_quality: str = "Dengeli (192K)"
    playlist: bool = True
    metadata: bool = True
    thumbnail_flag: bool = True
    subs: bool = False
    auto_subs: bool = False
    restrict_names: bool = False
    sponsorblock: bool = False
    playlist_items: str = ""
    max_downloads: str = ""
    rate_limit: str = ""
    archive: bool = True
    retries: str = ""
    concurrent_fragments: str = "3"
    cookies: str = ""
    browser_cookies: str = "disabled"
    youtube_403: bool = True
    output_template: str = ""
    extra_args: str = ""
    options_source: str = "Default"  # "Default" or "User_Explicit"
    folder_org: str = "None"  # "None", "Channel", "Year", "Format", "Channel_Year"
    thumbnail_path: Optional[str] = None

    # Clipping configurations
    clip_enabled: bool = False
    clip_start: str = "00:00"
    clip_end: str = "00:00"
    clip_precise: bool = False
    export_profile: str = "Default (No Profile)"
    merge_clips: bool = False
    clip_strategy: str = "stream_seek"
    macro_clips_data: Optional[List[dict]] = None
    video_info: Optional[dict] = None

    # Real-time task execution metrics
    percent: float = 0.0
    speed: str = "0.0 KB/s"
    eta: str = "--:--"
    size: str = "0.0 MB"
    active_filename: str = ""
    file_path: str = ""

    # Dynamic cancellation event for granular thread safety
    cancel_event: threading.Event = field(default_factory=threading.Event, compare=False, repr=False)

    # Internal dynamic variables
    _output_file: Optional[str] = None
    _temp_info_json: Optional[str] = None

def get_default_lang() -> str:
    import locale
    try:
        for get_func in (locale.getlocale, locale.getdefaultlocale):
            try:
                sys_lang = get_func()[0]
                if sys_lang:
                    lang_code = sys_lang.split("_")[0].lower()
                    if lang_code in ("tr", "es", "en"):
                        return lang_code
            except Exception:
                continue
    except Exception:
        pass
    return "en"

def load_app_preferences(prefs):
    from core.history import get_app_data_dir
    import json
    path = get_app_data_dir() / "settings.json"
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            prefs.output_dir = data.get("output_dir", prefs.output_dir)
            prefs.current_lang = data.get("current_lang", prefs.current_lang)
            prefs.current_theme = data.get("current_theme", prefs.current_theme)
            prefs.compact_mode = data.get("compact_mode", prefs.compact_mode)
        except Exception as e:
            print(f"[warning] Failed to load settings: {e}")

def save_app_preferences(prefs):
    from core.history import get_app_data_dir
    import json
    path = get_app_data_dir() / "settings.json"
    try:
        data = {
            "output_dir": prefs.output_dir,
            "current_lang": prefs.current_lang,
            "current_theme": prefs.current_theme,
            "compact_mode": getattr(prefs, "compact_mode", False)
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[warning] Failed to save settings: {e}")

@dataclass
class AppPreferences:
    # Target download directories & settings
    output_dir: str = ""
    current_lang: str = field(default_factory=get_default_lang)  # Auto-detected default language
    current_theme: str = "Dark"  # Default theme (Dark, Light)
    active_profile: str = "best"  # best, 1080p, 720p, mp3, custom
    custom_settings: Dict = field(default_factory=dict)

    # Shared settings (SponsorBlock, browser cookies, speed limits)
    sponsorblock_enabled: bool = False
    browser_cookies: str = "disabled"
    speed_limit: Optional[str] = None

    # Advanced panel configurations
    metadata_flag: bool = True
    thumbnail_flag: bool = True
    subtitle_flag: bool = False
    auto_subtitle_flag: bool = False
    restrict_filenames: bool = False
    keep_video_flag: bool = False
    embed_chapters: bool = False
    concurrent_fragments: str = "3"
    output_template: str = ""
    extra_args: str = ""
    folder_org: str = "None"  # "None", "Channel", "Year", "Format", "Channel_Year"
    compact_mode: bool = False

    # Multi-worker concurrency count
    max_workers: int = 3

@dataclass
class AppState:
    preferences: AppPreferences = field(default_factory=AppPreferences)

    # Active inputs
    url: str = ""
    is_batch_mode: bool = False
    batch_urls: List[str] = field(default_factory=list)

    # Metadata caching
    current_video_info: Optional[Dict] = None  # Caches active metadata
    current_thumbnail_path: Optional[str] = None

    # Strongly typed active download queue
    queue_list: List[DownloadTask] = field(default_factory=list)

    # Diagnostic logs
    terminal_logs: List[str] = field(default_factory=list)

    # Threading controls & active executor state
    is_executor_running: bool = False
    current_item_index: int = -1
    cancel_current_flag: bool = False

    # Outdated warning state
    saw_outdated_warning: bool = False

    def __post_init__(self):
        # Auto-initialize central logging system
        from core.logging_setup import setup_logging
        setup_logging()

        self._lock = threading.RLock()
        try:
            load_app_preferences(self.preferences)
        except Exception:
            pass

    def __getattr__(self, name):
        if name == "preferences":
            raise AttributeError("preferences not initialized")
        prefs = self.__dict__.get("preferences")
        if prefs and hasattr(prefs, name):
            return getattr(prefs, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name != "preferences":
            prefs = self.__dict__.get("preferences")
            if prefs and hasattr(prefs, name):
                setattr(prefs, name, value)
                return
        super().__setattr__(name, value)

```

---

## <a name="file-coreclippy"></a> 📄 File: `core/clip.py`
**Responsibility**: Advanced interval operations. Implements LeetCode 56 Greedy Interval Merging algorithm to bundle overlapping clips and reduce net requests.

```python
# core/clip.py
import re
from typing import Tuple, Union, Optional

def parse_time_to_seconds(s: str) -> Optional[float]:
    s = s.strip()
    if not s:
        return None
    is_negative = False
    if s.startswith("-"):
        is_negative = True
        s = s[1:].strip()
    # Check format HH:MM:SS or MM:SS
    val = None
    if ":" in s:
        parts = s.split(":")
        try:
            if len(parts) == 2:
                val = int(parts[0]) * 60 + float(parts[1])
            elif len(parts) == 3:
                val = int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        except ValueError:
            return None
    else:
        # Parse pure seconds string
        try:
            val = float(s)
        except ValueError:
            return None
    if val is not None:
        return -val if is_negative else val
    return None

def format_seconds_to_mmss(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:05.2f}"
    return f"{m:02d}:{s:05.2f}"

def validate_clip_range(start_str: str, end_str: str, total_duration: float) -> Union[Tuple[float, float], str]:
    start = parse_time_to_seconds(start_str)
    end = parse_time_to_seconds(end_str)
    
    if start is None or end is None:
        return "err_clip_format"
    if start < 0:
        return "err_clip_negative"
    if start >= end:
        return "err_clip_order"
    if total_duration > 0 and end > total_duration:
        end = total_duration  # Silent correction to end of video
    if (end - start) < 0.5:
        return "err_clip_min"
        
    return start, end

def decide_clip_strategy(info: dict, start: float, end: float) -> str:
    # Live stream - seek is problematic, must download and trim
    if info.get("is_live"):
        return "full_trim"
    
    # Check for HTTP/HTTPS seekable protocol in formats list
    formats = info.get("formats", [])
    has_seekable = any(
        f.get("protocol") in ("https", "http") or (f.get("url") and f.get("url").startswith(("http://", "https://")))
        for f in formats
    )
    
    duration = info.get("duration", 0)
    clip_ratio = (end - start) / duration if duration else 1
    
    if has_seekable and clip_ratio < 0.15:
        # Less than 15% requested -> stream seek (Fastest)
        return "stream_seek"
    elif has_seekable and clip_ratio < 0.5:
        # Up to 50% -> hybrid: buffered seek + local c:copy trim
        return "hybrid"
    else:
        # Large part -> full download + local trim
        return "full_trim"

from dataclasses import dataclass
from typing import List

@dataclass
class MicroClip:
    id: str
    start: float  # in seconds
    end: float
    export_profile: str
    output_name: str

@dataclass
class MacroClip:
    start: float
    end: float
    micro_clips: List[MicroClip]

def optimize_clip_intervals(clips: List[MicroClip], threshold_sec: float = 30.0) -> List[MacroClip]:
    """
    Greedy Interval Merging Algorithm (LeetCode 56) to combine overlapping or near
    clips to prevent redundant network I/O.
    """
    if not clips:
        return []

    # Sort clips chronologically by start time
    sorted_clips = sorted(clips, key=lambda c: c.start)
    
    macro_clips = []
    first_clip = sorted_clips[0]
    
    current_macro = MacroClip(
        start=first_clip.start,
        end=first_clip.end,
        micro_clips=[first_clip]
    )

    for i in range(1, len(sorted_clips)):
        next_clip = sorted_clips[i]
        
        # If next clip start is within threshold_sec of current macro's end, merge them!
        if next_clip.start <= current_macro.end + threshold_sec:
            current_macro.end = max(current_macro.end, next_clip.end)
            current_macro.micro_clips.append(next_clip)
        else:
            # Sizable gap: close current macro and start a new one
            macro_clips.append(current_macro)
            current_macro = MacroClip(
                start=next_clip.start,
                end=next_clip.end,
                micro_clips=[next_clip]
            )
            
    macro_clips.append(current_macro)
    return macro_clips

```

---

## <a name="file-corecommand_builderpy"></a> 📄 File: `core/command_builder.py`
**Responsibility**: Translates AppState options into dynamic, secure command arguments for the yt-dlp core, featuring loaded info-json injection to bypass double-fetching.

```python
# core/command_builder.py
import sys
import shlex
import os
import atexit
from pathlib import Path
from typing import Optional
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
    else:
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
        
    SAFE_ARG_PREFIXES = [
        "--sleep-", "--limit-", "--retries", "--socket-timeout", "--proxy",
        "--referer", "--user-agent", "--geo-", "--playlist-", "--yes-", "--no-",
        "--date", "--match-", "--reject-", "--min-", "--max-", "--flat-playlist",
        "--ignore-errors", "--verbose", "--quiet", "--force-", "--cookies",
        "--ffmpeg-", "--audio-", "--extract-audio", "--embed-", "--add-", "--write-",
        "--ignore-config", "--no-config", "--prefer-", "--http-", "--buffer-",
        "--resize-", "--remux-", "--recode-", "--postprocessor-", "--download-sections"
    ]
    SAFE_EXACT_ARGS = {
        "-i", "-v", "-q", "-h", "--help", "--version", "--force-keyframes-at-cuts"
    }
    
    sanitized_parts = []
    skip_next = False
    
    for i, part in enumerate(parts):
        if skip_next:
            skip_next = False
            continue
            
        part_clean = part.strip()
        if part_clean.startswith("-"):
            part_lower = part_clean.lower()
            is_safe = False
            for safe_exact in SAFE_EXACT_ARGS:
                if part_lower == safe_exact:
                    is_safe = True
                    break
            if not is_safe:
                for safe_prefix in SAFE_ARG_PREFIXES:
                    if part_lower.startswith(safe_prefix):
                        is_safe = True
                        break
            if not is_safe:
                print(f"[Security Protection] Blocked dangerous/unlisted parameter: {part}")
                if "=" not in part_clean and i + 1 < len(parts) and not parts[i + 1].strip().startswith("-"):
                    skip_next = True
                continue
                
        sanitized_parts.append(part)
        
    return sanitized_parts

def effective_video_height(item) -> Optional[int]:
    selected = VIDEO_PRESET_HEIGHT.get(safe_get(item, "video_profile"), "1080")
    if selected == "CUSTOM":
        val = safe_get(item, "video_limit", "1080")
    else:
        val = selected
        
    if val == "Best" or not val:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return 1080

def build_command(item, output_dir: str) -> list[str]:
    import tempfile
    import json
    
    out_dir = str(Path(output_dir).expanduser())
    folder_org = str(safe_get(item, "folder_org", "None")).strip()
    
    if folder_org and folder_org != "None":
        if folder_org == "Channel":
            output_template = "%(uploader).30s/%(title).70s [%(id)s].%(ext)s"
        elif folder_org == "Year":
            output_template = "%(upload_date>%Y)s/%(title).70s [%(id)s].%(ext)s"
        elif folder_org == "Format":
            output_template = "%(ext)s/%(title).70s [%(id)s].%(ext)s"
        elif folder_org == "Channel_Year":
            output_template = "%(uploader).30s/%(upload_date>%Y)s/%(title).70s [%(id)s].%(ext)s"
        else:
            output_template = DEFAULT_OUTPUT_TEMPLATE
    else:
        output_template = str(safe_get(item, "output_template", "")).strip() or DEFAULT_OUTPUT_TEMPLATE
        
    cmd: list[str] = [sys.executable, "-m", "yt_dlp", "--newline", "-P", out_dir, "-o", output_template]

    # If pre-fetched metadata exists (Multi-Clip Single-Fetch), inject it to avoid double-fetching network calls
    video_info = safe_get(item, "video_info")
    if video_info:
        try:
            # Create a temporary file inside our isolated scratch directory to write cached JSON metadata
            scratch_path = Path.home() / ".yt-downloader-scratch"
            scratch_path.mkdir(parents=True, exist_ok=True)
            
            temp_json = tempfile.NamedTemporaryFile(
                dir=str(scratch_path),
                mode="w",
                delete=False,
                suffix=".json",
                encoding="utf-8"
            )
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
            
        if quality is None:
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
    if safe_get(item, "restrict_names") or (folder_org and folder_org != "None"):
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
    else:
        cmd.extend(["--retries", "10"])

    # Protect against infinite TCP socket hangs on unstable/throttled connections
    cmd.extend(["--socket-timeout", "30"])

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

```

---

## <a name="file-coremergerpy"></a> 📄 File: `core/merger.py`
**Responsibility**: Concatenation engine utilizing the FFmpeg Concat Demuxer for lossless segment mergers.

```python
# core/merger.py
import subprocess
import os
import tempfile
from pathlib import Path

class LosslessMerger:
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path

    def merge_clips(self, clip_paths: list[str], output_path: str, cleanup: bool = False, register_proc_cb=None, unregister_proc_cb=None) -> bool:
        if len(clip_paths) < 2:
            print("[Merge Engine] At least 2 clips are required to perform merge.")
            return False

        working_dir = Path(output_path).parent.resolve()
        fd, list_file_path = tempfile.mkstemp(dir=str(working_dir), suffix=".txt", text=True)
        
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                for clip in clip_paths:
                    try:
                        # Calculate path relative to the working directory (output folder)
                        rel_path = os.path.relpath(clip, start=working_dir).replace('\\', '/')
                    except ValueError:
                        # Fallback to absolute path on cross-drive scenarios on Windows
                        rel_path = os.path.abspath(clip).replace('\\', '/')
                    # Safe quoting for ffmpeg concat demuxer format
                    rel_path = rel_path.replace("'", "\\'")
                    f.write(f"file '{rel_path}'\n")

            # Convert output path relative to working directory
            try:
                rel_output = os.path.relpath(output_path, start=working_dir).replace('\\', '/')
            except ValueError:
                rel_output = os.path.abspath(output_path).replace('\\', '/')
            
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", list_file_path,
                "-c", "copy",
                rel_output
            ]

            print(f"[Merge Engine] Starting demux concatenation of {len(clip_paths)} clips in {working_dir}...")
            
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                startupinfo=startupinfo,
                cwd=str(working_dir),
                shell=False
            )

            if register_proc_cb:
                register_proc_cb(process)

            try:
                stdout_data, stderr_data = process.communicate()
            finally:
                if unregister_proc_cb:
                    unregister_proc_cb(process)

            if process.returncode != 0:
                print(f"[Merge Engine] FFmpeg demux failed with returncode {process.returncode}:\n{stderr_data}")
                return False

            print(f"[Merge Engine] Finished successfully: {output_path}")

            if cleanup:
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    self._cleanup_clips(clip_paths)
                else:
                    print(f"[Merge Engine] Warning: Merged output file {output_path} is missing or empty. Skipping cleanup to prevent data loss.")
                    return False

            return True

        except Exception as e:
            print(f"[Merge Engine] Unexpected failure: {e}")
            return False

        finally:
            if os.path.exists(list_file_path):
                try:
                    os.remove(list_file_path)
                except Exception:
                    pass

    def _cleanup_clips(self, clip_paths: list[str]):
        for clip in clip_paths:
            try:
                if os.path.exists(clip):
                    os.remove(clip)
            except Exception as e:
                print(f"[Merge Engine] Cleanup failed for {clip}: {e}")

```

---

## <a name="file-coresuggesterpy"></a> 📄 File: `core/suggester.py`
**Responsibility**: Heuristic decision engine that profiles videos by height, duration, and tags to suggest vertical crop, standard MP4, or podcast MP3.

```python
# core/suggester.py

class SmartFormatSuggester:
    """Heuristic Scoring Engine analyzing video metadata to predict the optimal download format."""
    
    def __init__(self):
        # Base scores for fallback categories
        self.base_scores = {
            "mp4_standard": 10,  # Base fallback level
            "mp4_vertical": 0,
            "mp3_music": 0,
            "mp3_podcast": 0
        }

        # Sets for O(1) membership queries
        self.music_keywords = {"music", "song", "official", "audio", "lyric", "album", "cover", "clip", "müzik", "şarkı", "klip"}
        self.podcast_keywords = {"podcast", "interview", "röportaj", "talk", "episode", "full length", "söyleşi", "sohbet", "ders", "lecture"}

    def analyze(self, info_dict: dict) -> str:
        """
        Analyzes metadata and outputs the highest-scoring format key.
        Keys: 'mp4_standard', 'mp4_vertical', 'mp3_music', 'mp3_podcast'
        """
        scores = self.base_scores.copy()

        # Gather data safely with defaults to avoid KeyErrors
        duration = info_dict.get("duration", 0.0) or 0.0
        width = info_dict.get("width", 1) or 1
        height = info_dict.get("height", 1) or 1
        
        title = str(info_dict.get("title", "")).lower()
        
        # Safe categories pulling
        categories = info_dict.get("categories") or []
        categories = [str(c).lower() for c in categories]
        
        # Safe tags pulling
        tags = info_dict.get("tags") or []
        tags = [str(t).lower() for t in tags]

        # Consolidate all metadata terms to analyze intersections
        text_pool = set(title.split() + categories + tags)

        # ----------------- HEURISTIC RULES -----------------
        
        # Rule 1: Aspect Ratio and Duration (Shorts/Reels detection)
        if height > width and duration < 180:
            scores["mp4_vertical"] += 60
        elif height > width:
            scores["mp4_vertical"] += 25

        # Rule 2: Official Categorizations
        if "music" in categories:
            scores["mp3_music"] += 45
        if "education" in categories or "science & technology" in categories or "news & politics" in categories:
            scores["mp3_podcast"] += 20

        # Rule 3: Title & Tags Text Intersection Queries
        music_hits = len(self.music_keywords.intersection(text_pool))
        scores["mp3_music"] += (music_hits * 15)

        podcast_hits = len(self.podcast_keywords.intersection(text_pool))
        scores["mp3_podcast"] += (podcast_hits * 20)

        # Rule 4: Duration Behavior Analysis
        # Over 45 minutes -> highly likely a podcast, tutorial, or background lecture
        if duration > 2700:
            scores["mp3_podcast"] += 35
            scores["mp4_standard"] -= 15  # Discourage large video downloads

        # Result selection
        best_format = max(scores, key=scores.get)
        return best_format

```

---

## <a name="file-coreupdaterpy"></a> 📄 File: `core/updater.py`
**Responsibility**: Background checker that queries PyPI to alert users if their yt-dlp modules are older than 90 days.

```python
# core/updater.py
import urllib.request
import urllib.error
import json
import threading
import hashlib
from dataclasses import dataclass
import yt_dlp

# Pinned stable release hashes to protect against supply chain compromise (Offline Trusted Roots)
KNOWN_VERSIONS = {
    "2026.06.09": "c76f5713437df4c8996fb92427ae41e4649b934ca495991b7852b855e3a51fef", # Example hash for release
}

@dataclass
class UpdatePayload:
    """Strongly-typed data container representing an update check result."""
    current_version: str
    latest_version: str
    download_url: str = None
    sha256: str = None
    action: str = "upgrade"  # "upgrade" or "downgrade"
    is_fallback: bool = False

def verify_hash_against_pypi(version: str, sha256_val: str) -> bool:
    """Queries the official PyPI JSON API for the specific version and verifies if the hash is registered."""
    pypi_version_url = f"https://pypi.org/pypi/yt-dlp/{version}/json"
    try:
        req = urllib.request.Request(pypi_version_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=4.0) as response:
            data = json.loads(response.read().decode('utf-8'))
            urls = data.get("urls", [])
            for url_entry in urls:
                digests = url_entry.get("digests", {})
                pypi_sha256 = digests.get("sha256", "")
                if pypi_sha256 and pypi_sha256.lower() == sha256_val.lower():
                    print(f"[Updater] Hash {sha256_val} verified against official PyPI release.")
                    return True
    except Exception as e:
        print(f"[Updater] Failed to verify hash against PyPI: {e}")
    return False

def calculate_sha256(file_path: str) -> str:
    """Computes the SHA-256 checksum of a local file in memory-efficient chunks."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"[Updater] Failed to compute file hash: {e}")
        return ""

class UpdateChecker:
    """Schedules background update checks, routing query streams through a two-tiered fallback pipeline."""
    
    def __init__(self, ui_callback):
        """
        ui_callback: Function to invoke inside UI thread when an update/rollback action is detected.
                     Prototype: callback(payload: UpdatePayload)
        """
        self.ui_callback = ui_callback
        self.bff_url = "https://api.baynuman.com/v1/update/desktop"
        self.pypi_url = "https://pypi.org/pypi/yt-dlp/json"

    def check_in_background(self):
        """Spawns a background daemon thread to perform update queries without locking the GUI thread."""
        thread = threading.Thread(target=self._network_task, daemon=True, name="update-checker")
        thread.start()

    def _network_task(self):
        current_version = yt_dlp.version.__version__
        
        # --- TIER 1: Unified Update Broker BFF ---
        try:
            print("[Updater] Tier 1: Querying custom Update Broker BFF...")
            req = urllib.request.Request(self.bff_url, headers={'User-Agent': 'yt-dlp-Pro-Desktop'})
            with urllib.request.urlopen(req, timeout=3.0) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                latest_version = data.get("validated_version", "")
                download_url = data.get("download_url", None)
                expected_sha256 = data.get("sha256", None)
                action = data.get("action", "upgrade")
                
                if latest_version and latest_version != current_version:
                    # Deterministic update/rollback detected!
                    payload = UpdatePayload(
                        current_version=current_version,
                        latest_version=latest_version,
                        download_url=download_url,
                        sha256=expected_sha256,
                        action=action,
                        is_fallback=False
                    )
                    self.ui_callback(payload)
                    return  # Early exit on successful Tier 1 resolution!

        except Exception as e:
            # Catch all DNS resolution, timeout, and response parse errors silently
            print(f"[Updater] Tier 1 failed or timed out: {e}. Transitioning to Tier 2 (Plan B Fallback)...")
            
        # --- TIER 2: Plan B Official PyPI Fallback ---
        try:
            req = urllib.request.Request(self.pypi_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3.0) as response:
                data = json.loads(response.read().decode('utf-8'))
                latest_version = data["info"]["version"]
                
            try:
                current_tuple = tuple(int(x) for x in current_version.split('.') if x.isdigit())
                latest_tuple = tuple(int(x) for x in latest_version.split('.') if x.isdigit())
            except Exception:
                return

            if latest_tuple > current_tuple:
                # Official upgrade found!
                payload = UpdatePayload(
                    current_version=current_version,
                    latest_version=latest_version,
                    download_url=None, # Falls back to standard pip install
                    sha256=None,
                    action="upgrade",
                    is_fallback=True
                )
                self.ui_callback(payload)

        except Exception as fallback_err:
            print(f"[Updater] Tier 2 fallback query failed: {fallback_err}. Update check aborted.")
            pass

def execute_update(payload: UpdatePayload, scratch_dir: str) -> tuple[bool, str]:
    """
    Executes the update/downgrade process in a background-safe service layer.
    Verifies cryptographic hashes (SHA-256) of downloaded update package.
    Returns: (success_bool, message_str)
    """
    import sys
    import os
    import subprocess
    import urllib.request
    
    if getattr(sys, "frozen", False):
        # Standalone portable EXE build doesn't support pip upgrades
        return False, "Self-updates are not supported in the standalone portable version. Please download the latest version from GitHub!"

    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW

    # If we don't have a download URL (Plan B Fallback / PyPI), do standard pip upgrade
    if payload.is_fallback or not payload.download_url:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-U", "yt-dlp"],
                capture_output=True,
                creationflags=creationflags,
                shell=False
            )
            success = (result.returncode == 0)
            msg = "Fallback pip upgrade finished." if success else result.stderr.decode("utf-8", errors="replace")
            return success, msg
        except Exception as e:
            return False, str(e)

    # Tier 1 Custom Update Broker Flow
    try:
        # 1. Download target archive
        temp_filename = f"yt_dlp_update_{payload.latest_version}.tar.gz"
        temp_path = os.path.join(scratch_dir, temp_filename)
        
        print(f"[Updater] Downloading verified update package: {payload.download_url} -> {temp_path}")
        req = urllib.request.Request(payload.download_url, headers={'User-Agent': 'yt-dlp-Pro-Desktop'})
        with urllib.request.urlopen(req, timeout=10.0) as response, open(temp_path, "wb") as out_file:
            out_file.write(response.read())
            
        # 2. Cryptographic Integrity Verification (Supply Chain Protection)
        if payload.sha256:
            computed_hash = calculate_sha256(temp_path)
            print(f"[Updater] Verifying SHA-256 Checksum... Expected: {payload.sha256}, Computed: {computed_hash}")
            
            if computed_hash.lower() != payload.sha256.lower():
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
                return False, "Güvenlik İhlali: SHA-256 Bütünlük Doğrulaması Başarısız! (Security Breach: Checksum Mismatch)"
                
            # Verify update source authenticity (local pin or PyPI registration)
            is_trusted = False
            latest_ver = payload.latest_version
            if latest_ver in KNOWN_VERSIONS:
                if KNOWN_VERSIONS[latest_ver].lower() == payload.sha256.lower():
                    is_trusted = True
                    print(f"[Updater] Version {latest_ver} verified locally via KNOWN_VERSIONS.")
            else:
                if verify_hash_against_pypi(latest_ver, payload.sha256):
                    is_trusted = True
                    
            if not is_trusted:
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
                return False, "Güvenlik İhlali: Sürüm imza/özeti güvenilmeyen bir kaynaktan geliyor! (Security Breach: Untrusted Update Package)"
        
        # 3. Secure Installation
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--no-deps", temp_path],
            capture_output=True,
            creationflags=creationflags,
            shell=False
        )
        success = (result.returncode == 0)
        msg = result.stderr.decode("utf-8", errors="replace") if not success else "Success"
        
        # Cleanup downloaded archive
        try:
            os.remove(temp_path)
        except Exception:
            pass
            
        return success, msg

    except Exception as e:
        return False, str(e)

```

---

## <a name="file-corepresetspy"></a> 📄 File: `core/presets.py`
**Responsibility**: Manages loading and saving of user-customized JSON presets.

```python
# core/presets.py
import json
from pathlib import Path
from core.history import get_app_data_dir

def get_presets_file_path() -> Path:
    return get_app_data_dir() / "presets.json"

def get_default_presets() -> dict:
    return {
        "Podcast MP3": {
            "mode": "Audio",
            "audio_format": "mp3",
            "audio_quality": "Yuksek (320K)",
            "metadata_flag": True,
            "thumbnail_flag": True,
            "restrict_filenames": False
        },
        "4K Arşiv": {
            "mode": "Video",
            "video_profile": "Ultra HD (2160p)",
            "video_format": "mp4",
            "metadata_flag": True,
            "concurrent_fragments": "4"
        },
        "Twitter Klip": {
            "mode": "Video",
            "video_profile": "Dengeli (720p)",
            "video_format": "mp4",
            "restrict_filenames": True,
            "concurrent_fragments": "3"
        }
    }

_presets_cache = None

def load_presets(force_reload: bool = False) -> dict:
    global _presets_cache
    if _presets_cache is not None and not force_reload:
        return _presets_cache
        
    path = get_presets_file_path()
    if not path.exists():
        # Write default presets first time
        defaults = get_default_presets()
        save_all_presets(defaults)
        _presets_cache = defaults
        return defaults
    try:
        with open(path, "r", encoding="utf-8") as f:
            _presets_cache = json.load(f)
            return _presets_cache
    except Exception as e:
        print(f"[!] Error loading presets: {e}")
        return get_default_presets()

def save_all_presets(presets: dict):
    global _presets_cache
    _presets_cache = presets
    path = get_presets_file_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(presets, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[!] Error saving presets: {e}")

def save_preset(name: str, preset_dict: dict):
    presets = load_presets()
    presets[name] = preset_dict
    save_all_presets(presets)

def delete_preset(name: str):
    presets = load_presets()
    if name in presets:
        del presets[name]
        save_all_presets(presets)


```

---

## <a name="file-coreprofilespy"></a> 📄 File: `core/profiles.py`
**Responsibility**: Polymorphic export profile definitions (Shorts, Reels, Discord, WhatsApp) generating appropriate re-encoding ffmpeg parameters.

```python
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

```

---

## <a name="file-corehistorypy"></a> 📄 File: `core/history.py`
**Responsibility**: SQLite connection and schema manager representing local history database tables.

```python
# core/history.py
import sqlite3
import os
import platform
import time
import queue
import threading
from pathlib import Path
from typing import List, Dict, Any

def get_app_data_dir() -> Path:
    system = platform.system()
    if system == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".config"
    
    app_dir = base / "yt-dlp-downloader-pro"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir

def get_db_path() -> Path:
    return get_app_data_dir() / "history.db"

def connect_db() -> sqlite3.Connection:
    """Creates a database connection with high-performance concurrent WAL and busy timeouts."""
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path), timeout=30.0)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
    except Exception:
        pass
    return conn

_local = threading.local()

def get_read_connection() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = connect_db()
        _local.conn.row_factory = sqlite3.Row
    try:
        _local.conn.execute("SELECT 1")
    except Exception:
        _local.conn = connect_db()
        _local.conn.row_factory = sqlite3.Row
    return _local.conn

class DatabaseWriter:
    def __init__(self):
        self._queue: queue.Queue = queue.Queue()
        self._thread = threading.Thread(
            target=self._worker, daemon=True, name="db-writer"
        )
        self._thread.start()

    def _worker(self):
        # Dedicated database worker thread - sequential lock-free writes
        conn = connect_db()
        while True:
            try:
                item = self._queue.get(timeout=1.0)
                if item is None:  # Poison pill - exit
                    self._queue.task_done()
                    break
                
                try:
                    fn, args, kwargs = item
                    fn(conn, *args, **kwargs)
                    conn.commit()
                except Exception as e:
                    print(f"[DB Writer] SQL Write Error: {e}")
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                finally:
                    self._queue.task_done()
            except queue.Empty:
                continue
        try:
            conn.close()
        except Exception:
            pass

    def submit(self, fn, *args, **kwargs):
        """Dispatched from concurrent threads — non-blocking, asynchronous queue write"""
        self._queue.put((fn, args, kwargs))

    def shutdown(self):
        """Gracefully terminates the background SQLite worker thread after draining all writes"""
        try:
            self._queue.join()
        except Exception:
            pass
        self._queue.put(None)
        try:
            self._thread.join(timeout=3.0)
        except Exception:
            pass

# Global Singleton Database Writer Instance
_db_writer = DatabaseWriter()

def shutdown_db() -> None:
    """Gracefully terminates the background SQLite worker thread."""
    _db_writer.shutdown()

def init_db():
    # Init db is run once synchronously at startup, before thread dispatchers
    conn = connect_db()
    cursor = conn.cursor()
    
    # Enable WAL mode and check current version
    cursor.execute("PRAGMA user_version")
    current_version = cursor.fetchone()[0]
    
    TARGET_VERSION = 3
    
    if current_version < 1:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id TEXT PRIMARY KEY,
                title TEXT,
                url TEXT,
                format TEXT,
                file_path TEXT,
                status TEXT,
                downloaded_at INTEGER,
                file_size_bytes INTEGER,
                duration_seconds INTEGER
            )
        """)
        
    if current_version < 2:
        try:
            cursor.execute("ALTER TABLE downloads ADD COLUMN thumbnail_path TEXT")
        except sqlite3.OperationalError:
            # Column might already exist from older manual runs
            pass
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_downloads_url_format ON downloads (url, format)
        """)
        
    if current_version < 3:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS channel_rules (
                channel_id TEXT PRIMARY KEY,
                channel_name TEXT,
                settings_json TEXT,
                created_at INTEGER,
                updated_at INTEGER
            )
        """)
        
    if current_version < TARGET_VERSION:
        cursor.execute(f"PRAGMA user_version = {TARGET_VERSION}")
        
    conn.commit()
    conn.close()

# --- DB Write Worker Callbacks ---

def _do_add_download_record(conn, item_id: str, title: str, url: str, format_desc: str, file_path: str, status: str, file_size: int, duration: int, thumbnail_path: str = None):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO downloads (id, title, url, format, file_path, status, downloaded_at, file_size_bytes, duration_seconds, thumbnail_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (item_id, title, url, format_desc, file_path, status, int(time.time()), file_size, duration, thumbnail_path))

def _do_update_download_status(conn, item_id: str, status: str, file_path: str = None, file_size: int = None, duration: int = None, thumbnail_path: str = None):
    cursor = conn.cursor()
    if file_path is not None or file_size is not None or duration is not None or thumbnail_path is not None:
        updates = ["status = ?"]
        params = [status]
        if file_path is not None:
            updates.append("file_path = ?")
            params.append(file_path)
        if file_size is not None:
            updates.append("file_size_bytes = ?")
            params.append(file_size)
        if duration is not None:
            updates.append("duration_seconds = ?")
            params.append(duration)
        if thumbnail_path is not None:
            updates.append("thumbnail_path = ?")
            params.append(thumbnail_path)
        
        params.append(item_id)
        query = f"UPDATE downloads SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, tuple(params))
    else:
        cursor.execute("UPDATE downloads SET status = ? WHERE id = ?", (status, item_id))

def _do_clear_all_downloads(conn):
    cursor = conn.cursor()
    # Physical file cleanup to prevent orphaned WebP cache files
    try:
        cursor.execute("SELECT thumbnail_path FROM downloads")
        for row in cursor.fetchall():
            if row and row[0]:
                t_path = row[0]
                if os.path.exists(t_path):
                    try:
                        os.remove(t_path)
                    except Exception:
                        pass
    except Exception:
        pass
    cursor.execute("DELETE FROM downloads")

def _do_delete_download(conn, item_id: str):
    cursor = conn.cursor()
    # Physical file cleanup to prevent orphaned WebP cache files
    try:
        cursor.execute("SELECT thumbnail_path FROM downloads WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        if row and row[0]:
            t_path = row[0]
            if os.path.exists(t_path):
                try:
                    os.remove(t_path)
                except Exception:
                    pass
    except Exception:
        pass
    cursor.execute("DELETE FROM downloads WHERE id = ?", (item_id,))

# --- Exposed Non-Blocking API ---

def add_download_record(item_id: str, title: str, url: str, format_desc: str, file_path: str, status: str, file_size: int = 0, duration: int = 0, thumbnail_path: str = None):
    _db_writer.submit(_do_add_download_record, item_id, title, url, format_desc, file_path, status, file_size, duration, thumbnail_path=thumbnail_path)

def update_download_status(item_id: str, status: str, file_path: str = None, file_size: int = None, duration: int = None, thumbnail_path: str = None):
    _db_writer.submit(_do_update_download_status, item_id, status, file_path=file_path, file_size=file_size, duration=duration, thumbnail_path=thumbnail_path)

def clear_all_downloads():
    _db_writer.submit(_do_clear_all_downloads)

def delete_download(item_id: str):
    _db_writer.submit(_do_delete_download, item_id)

# --- Direct Read API (Safe concurrently with WAL mode) ---

def find_completed_download_in_db(video_id: str, url: str, format_desc: str) -> Dict[str, Any]:
    """
    Looks up a completed download in the database by exact URL, or URL matching video_id, and format.
    Returns a dictionary of the record if found, else None.
    """
    db_path = get_db_path()
    if not db_path.exists():
        return None
    conn = get_read_connection()
    cursor = conn.cursor()
    try:
        url_like = f"%{video_id}%" if video_id else "NOT_FOUND"
        cursor.execute(
            "SELECT * FROM downloads WHERE (url = ? OR url LIKE ?) AND format = ? LIMIT 1",
            (url, url_like, format_desc)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
    except Exception as e:
        print(f"[!] SQLite Search Error: {e}")
    return None

def get_all_downloads() -> List[Dict[str, Any]]:
    db_path = get_db_path()
    if not db_path.exists():
        return []
    conn = get_read_connection()
    cursor = conn.cursor()
    downloads = []
    try:
        cursor.execute("SELECT * FROM downloads ORDER BY downloaded_at DESC")
        rows = cursor.fetchall()
        for row in rows:
            downloads.append(dict(row))
    except Exception as e:
        print(f"[!] SQLite Fetch Error: {e}")
    return downloads


# ========== Channel Auto-Rules (Schemaless JSON Patch Storage) ==========

import json

def _do_save_channel_rule(conn, channel_id: str, channel_name: str, settings_json: str):
    cursor = conn.cursor()
    now = int(time.time())
    cursor.execute("""
        INSERT OR REPLACE INTO channel_rules (channel_id, channel_name, settings_json, created_at, updated_at)
        VALUES (?, ?, ?, COALESCE((SELECT created_at FROM channel_rules WHERE channel_id = ?), ?), ?)
    """, (channel_id, channel_name, settings_json, channel_id, now, now))

def _do_delete_channel_rule(conn, channel_id: str):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM channel_rules WHERE channel_id = ?", (channel_id,))

def save_channel_rule(channel_id: str, channel_name: str, settings_dict: dict):
    """Non-blocking async write — enqueues channel rule save to DB writer thread."""
    settings_json = json.dumps(settings_dict, ensure_ascii=False)
    _db_writer.submit(_do_save_channel_rule, channel_id, channel_name, settings_json)

def delete_channel_rule(channel_id: str):
    """Non-blocking async write — enqueues channel rule deletion to DB writer thread."""
    _db_writer.submit(_do_delete_channel_rule, channel_id)

def get_channel_rule(channel_id: str) -> dict:
    """Direct WAL-safe read — returns {channel_id, channel_name, settings_dict} or None."""
    db_path = get_db_path()
    if not db_path.exists() or not channel_id:
        return None
    conn = get_read_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM channel_rules WHERE channel_id = ? LIMIT 1", (channel_id,))
        row = cursor.fetchone()
        if row:
            record = dict(row)
            try:
                record["settings_dict"] = json.loads(record.get("settings_json", "{}"))
            except Exception:
                record["settings_dict"] = {}
            return record
    except Exception as e:
        print(f"[!] Channel Rule Read Error: {e}")
    return None

def get_all_channel_rules() -> List[Dict[str, Any]]:
    """Direct WAL-safe read — returns all channel rules sorted by most recently updated."""
    db_path = get_db_path()
    if not db_path.exists():
        return []
    conn = get_read_connection()
    cursor = conn.cursor()
    rules = []
    try:
        cursor.execute("SELECT * FROM channel_rules ORDER BY updated_at DESC")
        for row in cursor.fetchall():
            record = dict(row)
            try:
                record["settings_dict"] = json.loads(record.get("settings_json", "{}"))
            except Exception:
                record["settings_dict"] = {}
            rules.append(record)
    except Exception as e:
        print(f"[!] Channel Rules Fetch Error: {e}")
    return rules

```

---

## <a name="file-coredownloaderpy"></a> 📄 File: `core/downloader.py`
**Responsibility**: Background thread executor queue. Drives subprocess streaming pipelines, captures standard output, handles 403 fallbacks, and executes re-encoding profiles.

```python
# core/downloader.py
import os
import re
import sys
import time
import shlex
import subprocess
import ctypes
import threading
import queue
import logging
import signal
from typing import NamedTuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, wait

class CommandResult(NamedTuple):
    returncode: int
    saw_http_403: bool
    saw_outdated: bool

# Windows Sleep prevention constants
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001

def prevent_sleep():
    if os.name == 'nt':
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
        except Exception as e:
            logging.error(f"[Sleep Prevention] Failed to prevent sleep: {e}")

def allow_sleep():
    if os.name == 'nt':
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
        except Exception as e:
            logging.error(f"[Sleep Prevention] Failed to restore sleep state: {e}")

def get_subprocess_encoding() -> str:
    import locale
    if os.name == 'nt':
        try:
            return locale.getpreferredencoding(False) or "utf-8"
        except Exception:
            return "utf-8"
    return "utf-8"

def safe_put_ui(ui_queue, item):
    try:
        # Bloklanmaya veya timeout'a kesinlikle izin yok
        ui_queue.put_nowait(item)
    except queue.Full:
        # Load Shedding: UI yetişemiyorsa paketi düşür (drop).
        # Progress stat'ları veya terminal logları anlıktır, bir sonraki tick'te yenisi gelir.
        # Worker thread asla UI'ı beklememeli.
        pass

# Thread-safe subprocess tracking to prevent Zombie Processes
active_subprocess_lock = threading.Lock()
active_subprocesses = set()

def register_active_subprocess(proc):
    with active_subprocess_lock:
        active_subprocesses.add(proc)

def unregister_active_subprocess(proc):
    with active_subprocess_lock:
        active_subprocesses.discard(proc)

def resume_subprocess(proc):
    try:
        if os.name == 'nt':
            import ctypes
            ctypes.windll.ntdll.NtResumeProcess(proc._handle)
        else:
            import signal
            os.kill(proc.pid, signal.SIGCONT)
    except Exception:
        pass

def kill_all_active_subprocesses():
    with active_subprocess_lock:
        for proc in list(active_subprocesses):
            try:
                # Safe resume first to ensure it processes termination signals on POSIX/Windows
                resume_subprocess(proc)
                proc.terminate()
                proc.wait(timeout=1)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        active_subprocesses.clear()

from core.waveform import enqueue_waveform_generation
from core.utils import clean_empty_directories, extract_video_id

def _on_waveform_done(task_id, png_path, ui_queue):
    update_download_status(task_id, "COMPLETED", thumbnail_path=png_path)
    safe_put_ui(ui_queue, ("queue_sync", None))

# Core state & DB models
from core.app_state import AppState, DownloadTask, TaskStatus
from core.command_builder import build_command, format_cmd_for_log, YOUTUBE_FALLBACK_EXTRACTOR_ARGS
from core.history import add_download_record, update_download_status
from core.clip import parse_time_to_seconds

def resolve_ffmpeg_path() -> str:
    """Finds the ffmpeg binary, checking bundled paths or standard locations."""
    # 1. Check PyInstaller temp directory (if bundled inside the EXE)
    try:
        base_path = sys._MEIPASS
        bundled = os.path.join(base_path, "ffmpeg.exe" if os.name == "nt" else "ffmpeg")
        if os.path.exists(bundled):
            return bundled
    except Exception:
        pass

    # 2. Check directly next to the running executable (for installed Windows setups)
    try:
        app_dir = os.path.dirname(sys.executable)
        adjacent = os.path.join(app_dir, "ffmpeg.exe" if os.name == "nt" else "ffmpeg")
        if os.path.exists(adjacent):
            return adjacent
    except Exception:
        pass

    # 3. Check local bin directory (for development)
    local_bin = Path(".") / "bin" / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    if local_bin.exists():
        return str(local_bin.resolve())

    # 4. Fallback to system PATH
    return "ffmpeg"

def append_options_before_urls(cmd: list[str], urls: list[str], options: list[str]) -> list[str]:
    if not urls:
        return cmd + options
    option_area = cmd[:-len(urls)]
    url_area = cmd[-len(urls):]
    return option_area + options + url_area

def run_command_stream(cmd: list[str], task: DownloadTask, state: AppState, ui_queue, cancel_event) -> CommandResult:
    progress_re = re.compile(
        r"\[download\]\s+(\d{1,3}(?:\.\d+)?)%\s+of\s+(~?\d+(?:\.\d+)?\w+)\s+at\s+(\d+(?:\.\d+)?\w+/s|Unknown speed)\s+ETA\s+(\d{2}:\d{2}|\w+)"
    )
    dest_re = re.compile(r"\[download\]\s+Destination:\s+(.+)")
    already_re = re.compile(r"\[download\]\s+(.+)\s+has already been downloaded")
    merge_re = re.compile(r"\[Merger\]\s+Merging\s+formats\s+into\s+\"(.+?)\"")
    post_re = re.compile(r"\[(ExtractAudio|RecodeVideo|Metadata)\]\s+(?:Destination:\s+|\w+\s+to\s+\")(.+?)\"?$")

    saw_http_403 = False
    saw_outdated_warning = False

    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding=get_subprocess_encoding(),
        errors="replace",
        bufsize=1,
        startupinfo=startupinfo,
        shell=False,
    )
    assert process.stdout is not None
    task._process = process

    try:
        register_active_subprocess(process)
        for line in process.stdout:
            # Prefix UI logs with task title for concurrent visibility
            safe_put_ui(ui_queue, ("log", f"[{task.title[:18]}...] {line}"))

            if cancel_event.is_set() or task.cancel_event.is_set():
                process.terminate()
                break

            match = progress_re.search(line)
            if match:
                value = max(0.0, min(100.0, float(match.group(1))))
                size_str = match.group(2)
                speed_str = match.group(3)
                eta_str = match.group(4)

                stats_payload = {
                    "task_id": task.id,
                    "percent": value,
                    "size": size_str,
                    "speed": speed_str,
                    "eta": eta_str,
                }
                safe_put_ui(ui_queue, ("stats", stats_payload))

            dest_match = dest_re.search(line)
            if dest_match:
                full_path = dest_match.group(1).strip()
                filename = Path(full_path).name
                safe_put_ui(ui_queue, ("active_file", (task.id, filename)))
                task._output_file = full_path

            already_match = already_re.search(line)
            if already_match:
                full_path = already_match.group(1).strip()
                filename = Path(full_path).name
                safe_put_ui(ui_queue, ("active_file", (task.id, filename)))
                task._output_file = full_path

            merge_match = merge_re.search(line)
            if merge_match:
                full_path = merge_match.group(1).strip()
                filename = Path(full_path).name
                safe_put_ui(ui_queue, ("active_file", (task.id, filename)))
                task._output_file = full_path

            post_match = post_re.search(line)
            if post_match:
                full_path = post_match.group(2).strip()
                filename = Path(full_path).name
                safe_put_ui(ui_queue, ("active_file", (task.id, filename)))
                task._output_file = full_path

            if "HTTP Error 403: Forbidden" in line:
                saw_http_403 = True
            if "version" in line and "older than 90 days" in line:
                saw_outdated_warning = True

        return CommandResult(
            returncode=process.wait(),
            saw_http_403=saw_http_403,
            saw_outdated=saw_outdated_warning
        )
    finally:
        unregister_active_subprocess(process)

def wait_process_with_timeout(proc, timeout=120) -> int:
    try:
        return proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()  # sweep zombie process
        raise RuntimeError(f"Process timed out after {timeout} seconds")

# clean_empty_directories is now imported from core.utils

def _handle_cancel(task, lang, ui_queue, base_dir=None):
    task.status_code = TaskStatus.CANCELLED
    task.status = "Cancelled"
    update_download_status(task.id, "CANCELLED")
    if base_dir and getattr(task, "_output_file", None):
        clean_empty_directories(task._output_file, base_dir)
    safe_put_ui(ui_queue, ("toast_cancel", task.title))
    safe_put_ui(ui_queue, ("queue_sync", None))

def _set_downloading_status(task, lang, ui_queue):
    task.status_code = TaskStatus.DOWNLOADING
    task.status = "Downloading"
    safe_put_ui(ui_queue, ("queue_sync", None))

def _log_start(task, cmd, ui_queue):
    safe_put_ui(ui_queue, ("active_file", (task.id, task.title)))
    safe_put_ui(ui_queue, ("log", f"\n[queue] Download Started: {task.title}\n"))
    safe_put_ui(ui_queue, ("log", f"$ {format_cmd_for_log(cmd)}\n"))
    add_download_record(
        item_id=task.id,
        title=task.title,
        url=task.url,
        format_desc=f"{task.mode} ({task.video_profile if task.mode == 'Video' else task.audio_quality})",
        file_path="",
        status="DOWNLOADING",
        file_size=0,
        duration=int(parse_time_to_seconds(task.duration) or 0),
        thumbnail_path=getattr(task, "thumbnail_path", None)
    )

def _cleanup_temp_json(task):
    temp_json_file = getattr(task, "_temp_info_json", None)
    if temp_json_file and os.path.exists(temp_json_file):
        try:
            os.remove(temp_json_file)
        except Exception:
            pass

def _apply_clip_profile(task, ffmpeg_bin: str, input_path: Path, output_path: Path, 
                        start_offset: float, end_offset: float, profile, 
                        precise_override: bool = False, timeout: int = 600) -> bool:
    """
    Helper function to apply seeking, re-encoding, and profiles to a clip segment via FFmpeg.
    """
    duration_sec = end_offset - start_offset
    ffmpeg_cmd = [ffmpeg_bin, "-y", "-ss", str(start_offset), "-to", str(end_offset), "-i", str(input_path)]

    if profile and profile.name != "Default":
        ffmpeg_cmd.extend(profile.get_ffmpeg_args(duration_sec))
    else:
        # Smart Transcoding: Re-encode video+audio if Precise Cut is enabled
        if precise_override:
            if getattr(task, "mode", "Video") == "Audio":
                aud_fmt = getattr(task, "audio_format", "mp3")
                if aud_fmt == "mp3":
                    ffmpeg_cmd.extend(["-c:a", "libmp3lame", "-b:a", "192k"])
                elif aud_fmt in ("m4a", "aac"):
                    ffmpeg_cmd.extend(["-c:a", "aac", "-b:a", "192k"])
                else:
                    ffmpeg_cmd.extend(["-c:a", "copy"])
            else:
                ffmpeg_cmd.extend(["-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-c:a", "aac", "-b:a", "192k"])
        else:
            ffmpeg_cmd.extend(["-c:v", "copy", "-c:a", "copy"])

    ffmpeg_cmd.append(str(output_path))

    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    proc = None
    try:
        proc = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            startupinfo=startupinfo,
            shell=False,
        )
        register_active_subprocess(proc)
        wait_process_with_timeout(proc, timeout=timeout)
    finally:
        if proc:
            unregister_active_subprocess(proc)

    return proc is not None and proc.returncode == 0 and output_path.exists()

def _process_macro_clips(task, output_file, lang, ui_queue, cancel_event) -> str:
    safe_put_ui(ui_queue, ("log", f"[{task.title}] Slicing LeetCode 56 Multi-Clips...\n"))
    ffmpeg_bin = resolve_ffmpeg_path()
    input_path = Path(output_file)
    macro_start = parse_time_to_seconds(task.clip_start) or 0.0
    macro_clips = task.macro_clips_data
    from core.profiles import EXPORT_PROFILES

    micro_paths = []
    for idx_m, micro in enumerate(macro_clips):
        if cancel_event.is_set() or task.cancel_event.is_set():
            break
        micro_start = micro["start"]
        micro_end = micro["end"]
        micro_profile_name = micro.get("profile", "Default (No Profile)")
        micro_profile = EXPORT_PROFILES.get(micro_profile_name)

        rel_start = max(0.0, micro_start - macro_start)
        rel_end = max(0.0, micro_end - macro_start)
        duration_sec = rel_end - rel_start

        target_ext = micro_profile.ext if (micro_profile and micro_profile.name != "Default") else input_path.suffix.lstrip(".")
        suffix = micro.get("output_suffix", f"_clip{idx_m+1}")
        micro_output_path = input_path.parent / f"{input_path.stem}{suffix}.{target_ext}"

        safe_put_ui(ui_queue, ("log", f"[{task.title}] Slicing segment {idx_m+1}/{len(macro_clips)}: {micro_output_path.name}\n"))

        success = _apply_clip_profile(
            task=task,
            ffmpeg_bin=ffmpeg_bin,
            input_path=input_path,
            output_path=micro_output_path,
            start_offset=rel_start,
            end_offset=rel_end,
            profile=micro_profile,
            precise_override=micro.get("clip_precise") or getattr(task, "clip_precise", False),
            timeout=300
        )

        if success:
            micro_paths.append(str(micro_output_path))
            add_download_record(
                item_id=f"{task.id}_clip{idx_m+1}",
                title=f"{task.title} (Clip {idx_m+1})",
                url=task.url,
                format_desc=f"{task.mode} ({micro_profile_name})",
                file_path=str(micro_output_path),
                status="COMPLETED",
                file_size=os.path.getsize(micro_output_path),
                duration=int(duration_sec),
                thumbnail_path=getattr(task, "thumbnail_path", None)
            )

    if cancel_event.is_set() or task.cancel_event.is_set():
        return output_file

    try:
        os.remove(input_path)
    except Exception:
        pass
    ret_file = str(input_path.parent / f"{input_path.stem}_clips_generated")

    if task.merge_clips and len(micro_paths) > 1 and macro_clips:
        merged_ext = EXPORT_PROFILES[macro_clips[0].get("profile", "Default (No Profile)")].ext if EXPORT_PROFILES.get(macro_clips[0].get("profile")) else input_path.suffix.lstrip(".")
        merged_output_path = input_path.parent / f"{input_path.stem}_merged.{merged_ext}"

        # Homogeneity Check: Verify all clips have the exact same export profile
        profiles_used = {mc.get("profile", "Default (No Profile)") for mc in macro_clips}
        is_homogeneous = len(profiles_used) == 1

        if is_homogeneous:
            safe_put_ui(ui_queue, ("log", f"[{task.title}] Profiller eşleşti. Concat Demuxer ile kayıpsız birleştiriliyor...\n"))
            from core.merger import LosslessMerger
            merger = LosslessMerger(ffmpeg_bin)
            success = merger.merge_clips(
                micro_paths,
                str(merged_output_path),
                cleanup=True,
                register_proc_cb=register_active_subprocess,
                unregister_proc_cb=unregister_active_subprocess
            )
        else:
            safe_put_ui(ui_queue, ("log", f"[{task.title}] Heterojen profiller tespit edildi. Filtreleme ile yeniden kodlanıyor (Transcode Merge)...\n"))
            transcode_cmd = [ffmpeg_bin, "-y"]
            for mp in micro_paths:
                transcode_cmd.extend(["-i", mp])
            
            n = len(micro_paths)
            if task.mode == "audio":
                filter_str = "".join([f"[{i}:a]" for i in range(n)]) + f"concat=n={n}:v=0:a=1[a]"
                transcode_cmd.extend([
                    "-filter_complex", filter_str,
                    "-map", "[a]",
                    "-c:a", "aac", "-b:a", "192k",
                    str(merged_output_path)
                ])
            else:
                filter_str = "".join([f"[{i}:v][{i}:a]" for i in range(n)]) + f"concat=n={n}:v=1:a=1[v][a]"
                transcode_cmd.extend([
                    "-filter_complex", filter_str,
                    "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                    "-c:a", "aac", "-b:a", "192k",
                    str(merged_output_path)
                ])

            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            process = subprocess.Popen(
                transcode_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                startupinfo=startupinfo,
                text=True,
                encoding=get_subprocess_encoding(),
                errors="replace"
            )
            
            register_active_subprocess(process)
            try:
                stdout_data, _ = process.communicate()
            finally:
                unregister_active_subprocess(process)
                
            success = merged_output_path.exists() and process.returncode == 0
            
            if success:
                for mp in micro_paths:
                    try:
                        os.remove(mp)
                    except:
                        pass

        if success and merged_output_path.exists():
            ret_file = str(merged_output_path)
            add_download_record(
                item_id=f"{task.id}_merged",
                title=f"{task.title} (Merged)",
                url=task.url,
                format_desc=f"{task.mode} (Merged Clips)",
                file_path=str(merged_output_path),
                status="COMPLETED",
                file_size=os.path.getsize(merged_output_path),
                duration=int(sum(mc["end"] - mc["start"] for mc in macro_clips)),
                thumbnail_path=getattr(task, "thumbnail_path", None)
            )
    return ret_file

def _process_single_clip(task, output_file, lang, ui_queue, cancel_event) -> str:
    safe_put_ui(ui_queue, ("log", f"[{task.title}] Postprocessing clip media...\n"))
    ffmpeg_bin = resolve_ffmpeg_path()
    input_path = Path(output_file)
    from core.profiles import EXPORT_PROFILES
    profile = EXPORT_PROFILES.get(task.export_profile)

    target_ext = profile.ext if (profile and profile.name != "Default") else input_path.suffix.lstrip(".")
    final_path = input_path.parent / f"processed_{input_path.stem}.{target_ext}"

    start = parse_time_to_seconds(task.clip_start) or 0.0
    end = parse_time_to_seconds(task.clip_end) or 0.0
    duration_sec = (end - start) if task.clip_enabled else (parse_time_to_seconds(task.duration) or 10.0)

    if task.clip_enabled and task.clip_strategy in ("hybrid", "full_trim"):
        if task.clip_strategy == "hybrid":
            buffered_start = max(0.0, start - 5.0)
            rel_start = start - buffered_start
            rel_end = end - buffered_start
        else:
            rel_start = start
            rel_end = end
    else:
        rel_start = 0.0
        rel_end = duration_sec

    success = _apply_clip_profile(
        task=task,
        ffmpeg_bin=ffmpeg_bin,
        input_path=input_path,
        output_path=final_path,
        start_offset=rel_start,
        end_offset=rel_end,
        profile=profile,
        precise_override=getattr(task, "clip_precise", False),
        timeout=600
    )

    if success:
        try:
            os.remove(input_path)
            clean_output_path = input_path.with_suffix(f".{target_ext}")
            if final_path != clean_output_path:
                if os.path.exists(clean_output_path):
                    os.remove(clean_output_path)
                os.rename(final_path, clean_output_path)
            return str(clean_output_path)
        except Exception:
            pass
    return output_file

def resolve_actual_file_path(output_file: str, url: str) -> str:
    if not output_file:
        return ""
    if os.path.exists(output_file):
        return output_file
        
    # If file doesn't exist directly (e.g., due to Windows CP1254 character set conversions or unicode replacement slashes like ⧸),
    # let's find a file in the same directory that has the exact video ID in its name.
    # To prevent collisions in concurrent downloads (e.g. video and audio of the same ID), we normalize names for comparison.
    try:
        path = Path(output_file)
        parent = path.parent
        if not parent.exists():
            return output_file
            
        # Extract video ID from URL
        video_id = extract_video_id(url)
        if not video_id:
            return output_file
            
        # Helper to normalize string names (keep alphanumeric only)
        expected_norm_no_ext = re.sub(r'[^a-zA-Z0-9]', '', path.stem).lower()
        
        # 1. First Pass: Exact extension match + normalized stem match
        for child in parent.iterdir():
            if child.is_file() and video_id in child.name:
                if child.suffix.lower() == path.suffix.lower():
                    child_norm_no_ext = re.sub(r'[^a-zA-Z0-9]', '', child.stem).lower()
                    if child_norm_no_ext == expected_norm_no_ext:
                        return str(child)
                        
        # 2. Second Pass: Allow different media extension + normalized stem match (e.g. merged to .mkv instead of .mp4)
        MEDIA_SUFFIXES = {".mp4", ".mkv", ".webm", ".mp3", ".m4a", ".aac"}
        for child in parent.iterdir():
            if child.is_file() and video_id in child.name:
                if child.suffix.lower() in MEDIA_SUFFIXES:
                    child_norm_no_ext = re.sub(r'[^a-zA-Z0-9]', '', child.stem).lower()
                    if child_norm_no_ext == expected_norm_no_ext:
                        return str(child)
                        
        # 3. Third Pass: Legacy Fallback in case name was severely truncated
        for child in parent.iterdir():
            if child.is_file() and video_id in child.name:
                if child.suffix.lower() == path.suffix.lower():
                    return str(child)
                    
        for child in parent.iterdir():
            if child.is_file() and video_id in child.name:
                if child.suffix.lower() in MEDIA_SUFFIXES:
                    return str(child)
    except Exception:
        pass
        
    return output_file

def _set_completed_status(task, output_file, lang, ui_queue):
    task.status_code = TaskStatus.COMPLETED
    task.status = "Completed"
    file_size = os.path.getsize(output_file) if output_file and os.path.exists(output_file) else 0
    task.file_path = output_file or ""
    task.percent = 100.0
    
    thumb_path = getattr(task, "thumbnail_path", None)
    if getattr(task, "mode", "Video") == "Audio" and output_file and os.path.exists(output_file):
        # Enqueue waveform generation in a single-threaded queue to prevent CPU boğulma
        def cb(png):
            _on_waveform_done(task.id, png, ui_queue)
        enqueue_waveform_generation(task, output_file, cb)
        
    update_download_status(task.id, "COMPLETED", file_path=output_file or "", file_size=file_size, thumbnail_path=thumb_path)
    safe_put_ui(ui_queue, ("percent_complete", 1.0))
    safe_put_ui(ui_queue, ("toast_success", {"title": task.title, "file_path": output_file or ""}))

def _set_failed_status(task, code, lang, ui_queue, base_dir=None):
    task.status_code = TaskStatus.FAILED
    task.status = "Failed"
    update_download_status(task.id, "FAILED")
    if base_dir and getattr(task, "_output_file", None):
        clean_empty_directories(task._output_file, base_dir)
    safe_put_ui(ui_queue, ("toast_error", {"code": code, "title": task.title}))

def _handle_exception(task, e, lang, ui_queue, base_dir=None):
    task.status_code = TaskStatus.FAILED
    task.status = "Failed"
    update_download_status(task.id, "FAILED")
    if base_dir and getattr(task, "_output_file", None):
        clean_empty_directories(task._output_file, base_dir)
    safe_put_ui(ui_queue, ("log", f"[{task.title}] post-processing error: {e}\n"))

def download_single_task(task: DownloadTask, state: AppState, ui_queue, cancel_event) -> None:
    lang = state.current_lang
    if cancel_event.is_set() or task.cancel_event.is_set():
        _handle_cancel(task, lang, ui_queue, state.output_dir)
        return

    _set_downloading_status(task, lang, ui_queue)
    cmd = build_command(task, state.output_dir)
    _log_start(task, cmd, ui_queue)

    try:
        result = run_command_stream(cmd, task, state, ui_queue, cancel_event)
        _cleanup_temp_json(task)

        if result.saw_outdated:
            state.saw_outdated_warning = True
            safe_put_ui(ui_queue, ("toast_outdated", None))

        if cancel_event.is_set() or task.cancel_event.is_set():
            _handle_cancel(task, lang, ui_queue, state.output_dir)
            return

        if result.returncode != 0:
            should_retry = (
                result.saw_http_403
                and task.youtube_403
                and YOUTUBE_FALLBACK_EXTRACTOR_ARGS not in " ".join(cmd)
            )
            if should_retry:
                safe_put_ui(ui_queue, ("log", f"[{task.title}] YouTube 403 Forbidden, triggering TV Client fallback...\n"))
                retry_cmd = append_options_before_urls(cmd, [task.url], ["--extractor-args", YOUTUBE_FALLBACK_EXTRACTOR_ARGS])
                result = run_command_stream(retry_cmd, task, state, ui_queue, cancel_event)

        if result.returncode == 0:
            output_file = task._output_file
            
            # Resolve actual physical path (fixes Windows double-spaces and Unicode slashes ⧸ cp1254 mismatches)
            output_file = resolve_actual_file_path(output_file, task.url)
            
            if output_file and os.path.exists(output_file):
                if task.macro_clips_data:
                    output_file = _process_macro_clips(task, output_file, lang, ui_queue, cancel_event)
                elif (task.clip_enabled or task.export_profile != "Default (No Profile)"):
                    output_file = _process_single_clip(task, output_file, lang, ui_queue, cancel_event)

            if cancel_event.is_set() or task.cancel_event.is_set():
                _handle_cancel(task, lang, ui_queue, state.output_dir)
                return

            _set_completed_status(task, output_file, lang, ui_queue)
        else:
            _set_failed_status(task, result.returncode, lang, ui_queue, state.output_dir)

    except Exception as e:
        _handle_exception(task, e, lang, ui_queue, state.output_dir)
    finally:
        _cleanup_temp_json(task)
        safe_put_ui(ui_queue, ("queue_sync", None))

def run_queue_executor(state: AppState, ui_queue, cancel_event) -> None:
    """Processes pending items in parallel utilizing ThreadPoolExecutor based on max_workers."""
    lang = state.current_lang
    state.is_executor_running = True
    
    # Query pending tasks
    with state._lock:
        tasks_to_run = [
            task for task in state.queue_list
            if task.status_code == TaskStatus.PENDING
        ]
    
    if not tasks_to_run:
        state.is_executor_running = False
        safe_put_ui(ui_queue, ("queue_done", None))
        return

    prevent_sleep()
    try:
        status_message = "İşleniyor" if lang == "tr" else ("Procesando" if lang == "es" else "Processing")
        safe_put_ui(ui_queue, ("status", ("●", "#4f46e5", f"{status_message} (Concurrently)")))

        max_workers = state.preferences.max_workers
        safe_put_ui(ui_queue, ("log", f"[executor] Initiating parallel downloads (max_workers={max_workers}) for {len(tasks_to_run)} tasks...\n"))

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(download_single_task, task, state, ui_queue, task.cancel_event): task
                for task in tasks_to_run
            }
            wait(futures)
    finally:
        allow_sleep()
        state.is_executor_running = False
        safe_put_ui(ui_queue, ("queue_done", None))

def toggle_pause_task(task):
    """
    Toggles the pause/resume state of a download task.
    Note: This suspends/resumes the external child process (the yt-dlp executable subprocess)
    at the OS level (using NtSuspendProcess on Windows and SIGSTOP on Unix). It does NOT
    suspend python worker threads inside our process, avoiding TCP socket corruptions or thread deadlocks.
    """
    if not hasattr(task, "is_paused"):
        task.is_paused = False
    task.is_paused = not task.is_paused
    
    # Update status code and status text
    if task.is_paused:
        task.status = "Paused"
        task.status_code = TaskStatus.PAUSED
    else:
        task.status = "Downloading"
        task.status_code = TaskStatus.DOWNLOADING
        
    proc = getattr(task, "_process", None)
    if proc:
        if os.name == 'nt':
            try:
                if task.is_paused:
                    ctypes.windll.ntdll.NtSuspendProcess(proc._handle)
                else:
                    ctypes.windll.ntdll.NtResumeProcess(proc._handle)
            except Exception as e:
                logging.error(f"[!] WinAPI Suspend/Resume error: {e}")
        else:
            try:
                if task.is_paused:
                    os.kill(proc.pid, signal.SIGSTOP)
                else:
                    os.kill(proc.pid, signal.SIGCONT)
            except Exception as e:
                logging.error(f"[!] POSIX Suspend/Resume error: {e}")

```

---

## <a name="file-uithemepy"></a> 📄 File: `ui/theme.py`
**Responsibility**: Central theme configuration, palette constants (glassmorphic dark/light HSL palettes), and full localization dictionary (EN, TR, ES).

```python
# ui/theme.py
import customtkinter as ctk

# Premium Glassmorphic Theme Palette Colors (Light, Dark)
THEME_BG = ("#f1f5f9", "#090d16")                 # Soft Slate-Blue / Deep Space Obsidian
THEME_CARD_BG = ("#ffffff", "#121b2d")             # Translucent white glass / Deep Slate card glass
THEME_CARD_BORDER = ("#cbd5e1", "#22334f")         # Soft borders / Glass glow border
THEME_TEXT_PRIMARY = ("#0f172a", "#f8fafc")        # Title / strong text
THEME_TEXT_SECONDARY = ("#475569", "#94a3b8")      # Muted body text
THEME_ACCENT_BLUE = ("#2563eb", "#00d2ff")         # Accent cyan/blue
THEME_ACCENT_INDIGO = ("#4f46e5", "#6366f1")       # Violet-Indigo main
THEME_ACCENT_GREEN = ("#16a34a", "#10b981")        # Success states
THEME_ACCENT_RED = ("#dc2626", "#f43f5e")          # Error/Cancel states
THEME_CARD_SUBTITLE = ("#64748b", "#38bdf8")

from ui.i18n import TRANSLATIONS


```

---

## <a name="file-uicomponentstoastpy"></a> 📄 File: `ui/components/toast.py`
**Responsibility**: Actionable toast dialog that slides into view when a download finishes, offering Explorer exploration and media playing options.

```python
# ui/components/toast.py
import os
import sys
import subprocess
import customtkinter as ctk
import tkinter as tk
from pathlib import Path
from ui.theme import (
    THEME_BG, THEME_CARD_BG, THEME_CARD_BORDER, THEME_TEXT_PRIMARY,
    THEME_TEXT_SECONDARY, THEME_ACCENT_BLUE, THEME_ACCENT_INDIGO,
    THEME_ACCENT_RED
)


class BaseToast(ctk.CTkToplevel):
    """Base class for all toast notifications.
    Encapsulates shared window setup, positioning, fade-in/out animation,
    and auto-dismiss lifecycle so subclasses only implement _build_body().
    """
    def __init__(self, master, border_color=THEME_ACCENT_BLUE, duration_ms: int = 5000, **kwargs):
        super().__init__(master, **kwargs)

        self.duration_ms = duration_ms

        # Hide default OS window borders & decorations
        self.overrideredirect(True)
        # Keep on top of all windows
        self.attributes("-topmost", True)

        # Frosted glass card border container
        self.frame = ctk.CTkFrame(
            self,
            fg_color=THEME_CARD_BG,
            border_width=2,
            border_color=border_color,
            corner_radius=12
        )
        self.frame.pack(fill="both", expand=True)

        # Build the specific body content (subclass hook)
        self._build_body()

        # Geo Positioning & Fade Animation
        self.attributes("-alpha", 0.0)
        self.update_idletasks()  # Force geometry calculations to avoid 1x1 top-left bug
        self._position_toast()

        # Fade-in and bootstrap lifecycle
        self._fade_in()
        self.timer_id = self.after(self.duration_ms, self._fade_out)

    def _build_body(self):
        """Override in subclasses to build the toast's content inside self.frame."""
        raise NotImplementedError

    def _build_header(self, title: str):
        """Shared header row with title and close button."""
        header_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=12, pady=(12, 4))
        header_frame.grid_columnconfigure(0, weight=1)

        lbl_title = ctk.CTkLabel(
            header_frame,
            text=title,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=THEME_TEXT_PRIMARY
        )
        lbl_title.grid(row=0, column=0, sticky="w")

        btn_close = ctk.CTkButton(
            header_frame,
            text="✕",
            width=20,
            height=20,
            fg_color="transparent",
            text_color=THEME_TEXT_SECONDARY,
            hover_color=THEME_ACCENT_RED,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            command=self._fade_out
        )
        btn_close.grid(row=0, column=1, sticky="e")

    def _position_toast(self):
        req_width = self.winfo_reqwidth()
        req_height = self.winfo_reqheight()

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Margins to protect Taskbar overlaps
        margin_x = 24
        margin_y = 72

        x = screen_width - req_width - margin_x
        y = screen_height - req_height - margin_y

        self.geometry(f"{req_width}x{req_height}+{x}+{y}")

    def _fade_in(self):
        alpha = self.attributes("-alpha")
        if alpha < 1.0:
            alpha += 0.1
            self.attributes("-alpha", min(alpha, 1.0))
            self.after(20, self._fade_in)

    def _fade_out(self):
        if hasattr(self, 'timer_id') and self.timer_id:
            try:
                self.after_cancel(self.timer_id)
            except Exception:
                pass
            self.timer_id = None

        alpha = self.attributes("-alpha")
        if alpha > 0.0:
            alpha -= 0.1
            self.attributes("-alpha", max(alpha, 0.0))
            self.after(20, self._fade_out)
        else:
            self.destroy()


class ActionableToast(BaseToast):
    def __init__(self, master, title: str, file_path: str, duration_ms: int = 7000, **kwargs):
        self.file_path = str(Path(file_path).resolve())
        self._title = title
        super().__init__(master, border_color=THEME_ACCENT_BLUE, duration_ms=duration_ms, **kwargs)

    def _build_body(self):
        # Header Row: Title & Close Button
        self._build_header(self._title)

        # Filename Row
        file_name = os.path.basename(self.file_path)
        display_name = file_name if len(file_name) < 38 else file_name[:35] + "..."
        lbl_file = ctk.CTkLabel(
            self.frame,
            text=display_name,
            font=ctk.CTkFont(family="Segoe UI", size=11, slant="italic"),
            text_color=THEME_TEXT_SECONDARY,
            anchor="w",
            justify="left"
        )
        lbl_file.pack(fill="x", padx=12, pady=(0, 10))

        # Bottom Action Bar (3 column grid)
        btn_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=(0, 14))
        btn_frame.grid_columnconfigure((0, 1, 2), weight=1)

        btn_play = ctk.CTkButton(
            btn_frame,
            text="▶ Oynat" if ctk.get_appearance_mode() == "Dark" else "▶ Play",
            width=76,
            height=26,
            fg_color=THEME_ACCENT_INDIGO,
            text_color="#ffffff",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            command=self._action_play
        )
        btn_play.grid(row=0, column=0, padx=2)

        btn_folder = ctk.CTkButton(
            btn_frame,
            text="📂 Göster" if ctk.get_appearance_mode() == "Dark" else "📂 Show",
            width=76,
            height=26,
            fg_color=THEME_BG,
            text_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_CARD_BORDER,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            command=self._action_show_folder
        )
        btn_folder.grid(row=0, column=1, padx=2)

        btn_copy = ctk.CTkButton(
            btn_frame,
            text="📋 Kopyala" if ctk.get_appearance_mode() == "Dark" else "📋 Copy Path",
            width=88,
            height=26,
            fg_color="transparent",
            text_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_CARD_BORDER,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            command=self._action_copy_path
        )
        btn_copy.grid(row=0, column=2, padx=2)

    def _action_play(self):
        try:
            if sys.platform == "win32":
                os.startfile(self.file_path)
            elif sys.platform == "darwin":
                subprocess.call(["open", self.file_path])
            else:
                subprocess.call(["xdg-open", self.file_path])
            self._fade_out()
        except Exception as e:
            print(f"[Toast] Playback error: {e}")

    def _action_show_folder(self):
        try:
            if sys.platform == "win32":
                # Launch Windows Explorer and highlight the file
                subprocess.Popen(rf'explorer /select,"{self.file_path}"')
            elif sys.platform == "darwin":
                subprocess.call(["open", "-R", self.file_path])
            else:
                folder = os.path.dirname(self.file_path)
                subprocess.call(["xdg-open", folder])
            self._fade_out()
        except Exception as e:
            print(f"[Toast] Explorer open error: {e}")

    def _action_copy_path(self):
        self.clipboard_clear()
        self.clipboard_append(self.file_path)
        self.update()
        self._fade_out()


class NotificationToast(BaseToast):
    def __init__(self, master, title: str, desc: str, duration_ms: int = 5000, color=THEME_ACCENT_BLUE, **kwargs):
        self._title = title
        self._desc = desc
        super().__init__(master, border_color=color, duration_ms=duration_ms, **kwargs)

    def _build_body(self):
        self._build_header(self._title)

        lbl_desc = ctk.CTkLabel(
            self.frame,
            text=self._desc,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=THEME_TEXT_SECONDARY,
            anchor="w",
            justify="left",
            wraplength=260
        )
        lbl_desc.pack(fill="x", padx=12, pady=(0, 14))

```

---

## <a name="file-uipanelsurl_panelpy"></a> 📄 File: `ui/panels/url_panel.py`
**Responsibility**: Frame for URL input, batch pasting, and directory browsing, featuring drag-and-drop registration.

```python
# ui/panels/url_panel.py
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
import customtkinter as ctk
from ui.theme import THEME_BG, THEME_CARD_BORDER, THEME_TEXT_PRIMARY, THEME_TEXT_SECONDARY, TRANSLATIONS
from core.app_state import AppState

class UrlPanel(ctk.CTkFrame):
    def __init__(self, parent, state: AppState, on_url_changed_callback, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.app_state = state
        self.on_url_changed = on_url_changed_callback
        
        self.grid_columnconfigure(0, weight=1)
        self._build_ui()

    def _build_ui(self):
        lang = self.app_state.current_lang
        
        # Header Row: Label & Paste Button & Switch
        header_row = ctk.CTkFrame(self, fg_color="transparent")
        header_row.grid(row=0, column=0, pady=(16, 8), sticky="ew")
        header_row.grid_columnconfigure(0, weight=1)
        header_row.grid_columnconfigure(1, weight=0)
        header_row.grid_columnconfigure(2, weight=0)

        self.url_label = ctk.CTkLabel(
            header_row,
            text=TRANSLATIONS[lang]["url_label"],
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=THEME_TEXT_PRIMARY,
        )
        self.url_label.grid(row=0, column=0, sticky="w")

        self.paste_btn = ctk.CTkButton(
            header_row,
            text=TRANSLATIONS[lang]["paste_btn"],
            width=150,
            height=30,
            corner_radius=10,
            fg_color=THEME_BG,
            text_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_CARD_BORDER,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._paste_from_clipboard,
        )
        self.paste_btn.grid(row=0, column=1, padx=(0, 16), sticky="e")

        self.batch_mode_var = ctk.BooleanVar(value=self.app_state.is_batch_mode)
        self.batch_mode_switch = ctk.CTkSwitch(
            header_row,
            text=TRANSLATIONS[lang]["batch_switch"],
            variable=self.batch_mode_var,
            onvalue=True,
            offvalue=False,
            command=self._toggle_batch_mode,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME_TEXT_SECONDARY,
            progress_color="#4f46e5",
            button_color="#6366f1",
            button_hover_color="#4f46e5",
        )
        self.batch_mode_switch.grid(row=0, column=2, sticky="e")

        # URL Inputs Frame
        self.url_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.url_frame.grid(row=1, column=0, pady=(0, 10), sticky="ew")
        self.url_frame.grid_columnconfigure(0, weight=1)

        # Single-line URL Input
        self.url_entry = ctk.CTkEntry(
            self.url_frame,
            placeholder_text=TRANSLATIONS[lang]["url_placeholder"],
            height=38,
            corner_radius=10,
            fg_color=THEME_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            text_color=THEME_TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self.url_entry.grid(row=0, column=0, sticky="ew")
        self.url_entry.insert(0, self.app_state.url)
        self.url_entry.bind("<KeyRelease>", self._on_url_keyrelease)

        # Multi-line URL Input (hidden by default)
        self.url_textbox = ctk.CTkTextbox(
            self.url_frame,
            height=86,
            corner_radius=10,
            fg_color=THEME_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            text_color=THEME_TEXT_PRIMARY,
            font=ctk.CTkFont(family="Consolas", size=12),
        )
        self.url_textbox.grid(row=0, column=0, sticky="ew")
        self.url_textbox.grid_remove()
        self.url_textbox.bind("<KeyRelease>", lambda event: self._on_textbox_change())

        # Output Folder Section
        self.save_folder_lbl = ctk.CTkLabel(
            self,
            text=TRANSLATIONS[lang]["save_folder_label"],
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=THEME_TEXT_PRIMARY,
        )
        self.save_folder_lbl.grid(row=2, column=0, pady=(8, 4), sticky="w")

        folder_row = ctk.CTkFrame(self, fg_color="transparent")
        folder_row.grid(row=3, column=0, pady=(0, 16), sticky="ew")
        folder_row.grid_columnconfigure(0, weight=1)
        folder_row.grid_columnconfigure(1, weight=0)

        # Output Entry
        self.output_entry = ctk.CTkEntry(
            folder_row,
            placeholder_text="Output Directory...",
            height=38,
            corner_radius=10,
            fg_color=THEME_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            text_color=THEME_TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self.output_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.output_entry.insert(0, self.app_state.output_dir)
        self.output_entry.bind("<KeyRelease>", self._on_output_dir_keyrelease)

        self.browse_btn = ctk.CTkButton(
            folder_row,
            text=TRANSLATIONS[lang]["browse_btn"],
            width=130,
            height=38,
            corner_radius=10,
            fg_color=THEME_BG,
            text_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_CARD_BORDER,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self._pick_output_dir,
        )
        self.browse_btn.grid(row=0, column=1, sticky="e")

        # Setup Drag and Drop
        self._setup_dnd()

    def _setup_dnd(self):
        # Feature 3.5: Drag and Drop URL Support using TkinterDnD (if available)
        try:
            from tkinterdnd2 import DND_TEXT
            self.url_entry.drop_target_register(DND_TEXT)
            self.url_entry.dnd_bind("<<Drop>>", self._on_url_drop)
            self.url_textbox.drop_target_register(DND_TEXT)
            self.url_textbox.dnd_bind("<<Drop>>", self._on_url_drop)
        except ImportError:
            pass # Silent fail if tkinterdnd2 is not installed

    def _on_url_drop(self, event):
        url_data = event.data.strip()
        # Clean brackets if dropped from some browsers
        if url_data.startswith("{") and url_data.endswith("}"):
            url_data = url_data[1:-1]
        
        if self.batch_mode_var.get():
            self.url_textbox.insert("insert", f"{url_data}\n")
            self._on_textbox_change()
        else:
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, url_data)
            self.app_state.url = url_data
            self.on_url_changed()

    def _paste_from_clipboard(self):
        try:
            clipboard = self.clipboard_get().strip()
            if clipboard:
                if self.batch_mode_var.get():
                    self.url_textbox.insert("insert", f"{clipboard}\n")
                    self._on_textbox_change()
                else:
                    self.url_entry.delete(0, "end")
                    self.url_entry.insert(0, clipboard)
                    self.app_state.url = clipboard
                    self.on_url_changed()
        except Exception:
            pass

    def _toggle_batch_mode(self):
        is_batch = self.batch_mode_var.get()
        self.app_state.is_batch_mode = is_batch
        if is_batch:
            self.url_entry.grid_remove()
            self.url_textbox.grid(row=0, column=0, sticky="ew")
            self.url_textbox.delete("1.0", "end")
            self.url_textbox.insert("1.0", self.url_entry.get())
            self._on_textbox_change()
        else:
            self.url_textbox.grid_remove()
            self.url_entry.grid(row=0, column=0, sticky="ew")
            lines = self.url_textbox.get("1.0", "end-1c").splitlines()
            first_line = lines[0] if (lines and lines[0].strip()) else ""
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, first_line)
            self.app_state.url = first_line
            self.app_state.batch_urls = [l.strip() for l in lines if l.strip()]
            self.on_url_changed()

    def _on_url_keyrelease(self, event):
        self.app_state.url = self.url_entry.get().strip()
        self.on_url_changed()

    def _on_textbox_change(self):
        lines = self.url_textbox.get("1.0", "end-1c").splitlines()
        self.app_state.batch_urls = [l.strip() for l in lines if l.strip()]
        if self.app_state.batch_urls:
            self.app_state.url = self.app_state.batch_urls[0]
        else:
            self.app_state.url = ""
        self.on_url_changed()

    def _on_output_dir_keyrelease(self, event):
        self.app_state.output_dir = self.output_entry.get().strip()

    def _pick_output_dir(self):
        chosen = filedialog.askdirectory(initialdir=self.app_state.output_dir)
        if chosen:
            self.app_state.output_dir = chosen
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, chosen)

    def set_url(self, val: str):
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, val)
        self.app_state.url = val
        if self.batch_mode_var.get():
            self.url_textbox.delete("1.0", "end")
            self.url_textbox.insert("1.0", val)
            self._on_textbox_change()
        else:
            self.on_url_changed()

    def refresh_translations(self):
        lang = self.app_state.current_lang
        self.url_label.configure(text=TRANSLATIONS[lang]["url_label"])
        self.paste_btn.configure(text=TRANSLATIONS[lang]["paste_btn"])
        self.batch_mode_switch.configure(text=TRANSLATIONS[lang]["batch_switch"])
        self.url_entry.configure(placeholder_text=TRANSLATIONS[lang]["url_placeholder"])
        self.save_folder_lbl.configure(text=TRANSLATIONS[lang]["save_folder_label"])
        self.browse_btn.configure(text=TRANSLATIONS[lang]["browse_btn"])

```

---

## <a name="file-uipanelspreview_panelpy"></a> 📄 File: `ui/panels/preview_panel.py`
**Responsibility**: Fidelity video metadata card, chapter markers bar, custom CTkRangeSlider, and multi-clip list.

```python
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
        
        self.current_video_id = video_id
        
        def run():
            segments = fetch_sponsor_segments(video_id)
            if segments and getattr(self, "current_video_id", None) == video_id:
                self.after(0, self._on_sponsor_segments_loaded, segments, video_id)
                
        threading.Thread(target=run, daemon=True, name="sponsorblock-fetcher").start()

    def _on_sponsor_segments_loaded(self, segments, video_id):
        if getattr(self, "current_video_id", None) != video_id:
            return
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
        self.current_video_id = video_id
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


```

---

## <a name="file-uipanelsqueue_panelpy"></a> 📄 File: `ui/panels/queue_panel.py`
**Responsibility**: Responsive segment button tab switcher that toggles active queues and persistent history, providing native re-download and file path lookup triggers.

```python
# ui/panels/queue_panel.py
import tkinter as tk
from tkinter import messagebox
import os
import platform
import subprocess
from pathlib import Path
import time
import customtkinter as ctk
from ui.theme import (
    THEME_BG, THEME_CARD_BG, THEME_CARD_BORDER, THEME_TEXT_PRIMARY,
    THEME_TEXT_SECONDARY, THEME_ACCENT_BLUE, THEME_ACCENT_INDIGO,
    THEME_ACCENT_GREEN, THEME_ACCENT_RED, THEME_CARD_SUBTITLE, TRANSLATIONS
)
from core.app_state import AppState, TaskStatus
from core.history import get_all_downloads, clear_all_downloads, delete_download

class QueuePanel(ctk.CTkFrame):
    def __init__(self, parent, state: AppState, on_remove_item_callback, on_redownload_callback, on_cancel_task_callback=None, **kwargs):
        super().__init__(
            parent,
            fg_color=THEME_CARD_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            corner_radius=16,
            **kwargs
        )
        self.app_state = state
        self.on_remove_item = on_remove_item_callback
        self.on_redownload = on_redownload_callback
        self.on_cancel_task = on_cancel_task_callback

        # Dynamic trackers to allow high-performance in-memory progress updates
        self.card_status_labels = {}
        self.card_dot_labels = {}
        # Smart diffing: track current card composition to avoid unnecessary rebuilds
        self._active_card_ids = []
        self._active_tab_snapshot = None
        
        # Asynchronous thumbnail caching and worker pool to prevent scroll jank!
        self.image_cache = {}
        from concurrent.futures import ThreadPoolExecutor
        self.image_loader_pool = ThreadPoolExecutor(max_workers=4)
        
        self.grid_columnconfigure(0, weight=1)
        self._build_ui()

    def destroy(self):
        try:
            self.image_loader_pool.shutdown(wait=False)
        except Exception:
            pass
        super().destroy()

    def _async_load_thumbnail(self, thumb_path: str, label_widget):
        if not thumb_path or not os.path.exists(thumb_path):
            return
            
        def load_thread():
            try:
                from PIL import Image
                with Image.open(thumb_path) as pil_img:
                    img_width = pil_img.width
                    img_height = pil_img.height
                    aspect = img_width / img_height if img_height > 0 else 1.0

                    if aspect > 2.5:  # Waveform (320x60 = 5.3:1)
                        target_w, target_h = 80, 15
                    else:  # Normal thumbnail (16:9 = 1.78:1)
                        target_w, target_h = 80, 45

                    # Support Pillow versions with Resampling or legacy ANTIALIAS fallback
                    resample_filter = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.ANTIALIAS
                    resized = pil_img.resize((target_w, target_h), resample_filter).copy()
                    size = (target_w, target_h)
                self.after(0, self._set_loaded_image, thumb_path, resized, label_widget, size)
            except Exception as e:
                print(f"[!] Async thumbnail load error: {e}")
                
        self.image_loader_pool.submit(load_thread)

    def _set_loaded_image(self, thumb_path: str, pil_img, label_widget, size=(80, 45)):
        try:
            # Create CTkImage inside main thread to be fully thread-safe
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
            self.image_cache[thumb_path] = ctk_img
            if label_widget.winfo_exists():
                label_widget.configure(image=ctk_img, text="")
        except Exception:
            pass

    def _build_ui(self):
        lang = self.app_state.current_lang

        # Segmented Control Tab Switcher
        self.tab_selector_var = ctk.StringVar(value="active")
        self.tab_selector = ctk.CTkSegmentedButton(
            self,
            values=["Active Queue 📋", "History 📁"], # Will translate dynamically
            variable=self.tab_selector_var,
            selected_color=THEME_ACCENT_INDIGO,
            unselected_color=THEME_BG,
            unselected_hover_color=THEME_CARD_BORDER,
            text_color=THEME_TEXT_PRIMARY,
            command=self._on_tab_changed,
            height=34,
            corner_radius=10
        )
        self.tab_selector.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")

        # Scrollable Frame for listing items
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            height=180,
            fg_color="transparent",
            scrollbar_button_color=THEME_CARD_BORDER
        )
        self.scroll_frame.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        # Clear History button (only shown on History tab)
        self.btn_clear_history = ctk.CTkButton(
            self,
            text="🧹 Clear History",
            height=28,
            corner_radius=8,
            fg_color=THEME_BG,
            text_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_ACCENT_RED,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._clear_history_db
        )
        # Hidden by default

        self.update_list()

    def _on_tab_changed(self, choice):
        # Determine tab kind based on deterministic language-agnostic index
        values = self.tab_selector.cget("values")
        try:
            idx = values.index(choice)
        except ValueError:
            idx = 0
            
        if idx == 1:
            self.tab_selector_var.set("history")
            self.btn_clear_history.grid(row=2, column=0, padx=16, pady=(0, 16), sticky="e")
        else:
            self.tab_selector_var.set("active")
            self.btn_clear_history.grid_forget()
            
        self.update_list()

    def _clear_history_db(self):
        lang = self.app_state.current_lang
        title = TRANSLATIONS[lang].get("lbl_dialog_close_title", "Exit")
        msg = TRANSLATIONS[lang].get("msg_confirm_clear_history", "Are you sure you want to clear all history?")
        confirm = messagebox.askyesno(title, msg)
        if confirm:
            clear_all_downloads()
            self.update_list()

    def update_task_progress(self, task_id: str, percent: float, speed: str, eta: str, size: str):
        """High-performance direct in-memory widget text configuration."""
        if task_id in self.card_status_labels:
            lbl = self.card_status_labels[task_id]
            if lbl.winfo_exists():
                try:
                    lang = self.app_state.current_lang
                    active_str = TRANSLATIONS[lang].get("lbl_task_downloading", "Downloading")
                    lbl.configure(text=f"{active_str} ({percent:.1f}% - {speed})")
                except Exception:
                    pass

            # Update dot color to active indigo dynamically
            if task_id in self.card_dot_labels:
                dot = self.card_dot_labels[task_id]
                if dot.winfo_exists():
                    try:
                        dot.configure(text_color=THEME_ACCENT_INDIGO)
                    except Exception:
                        pass

    def _get_translated_status(self, item, lang: str) -> str:
        """Return localized status string using lbl_task_ keys from TRANSLATIONS."""
        key = f"lbl_task_{item.status_code.value}"
        return TRANSLATIONS[lang].get(key, item.status)

    def update_list(self):
        tab = self.tab_selector_var.get()
        lang = self.app_state.current_lang

        if tab == "active":
            # Smart diffing: compute current card IDs and status codes to avoid unnecessary rebuilds
            current_states = [(item.id, item.status_code) for item in self.app_state.queue_list]
            if current_states == self._active_card_ids and self._active_tab_snapshot == "active":
                # Composition unchanged — only update text content of existing cards
                for item in self.app_state.queue_list:
                    status_text = self._get_translated_status(item, lang)
                    dot_color = self._dot_color_for_status(item.status_code)
                    if item.status_code == TaskStatus.DOWNLOADING:
                        dl_str = TRANSLATIONS[lang].get("lbl_task_downloading", "Downloading")
                        status_text = f"{dl_str} ({item.percent:.1f}% - {item.speed})"
                    elif item.status_code == TaskStatus.PAUSED:
                        status_text = TRANSLATIONS[lang].get("lbl_task_paused", "Paused")
                    if item.id in self.card_status_labels:
                        lbl = self.card_status_labels[item.id]
                        if lbl.winfo_exists():
                            try:
                                lbl.configure(text=status_text)
                            except Exception:
                                pass
                    if item.id in self.card_dot_labels:
                        dot = self.card_dot_labels[item.id]
                        if dot.winfo_exists():
                            try:
                                dot.configure(text_color=dot_color)
                            except Exception:
                                pass
                return

            # Composition changed — full rebuild required
            for child in self.scroll_frame.winfo_children():
                child.destroy()
            self.card_status_labels.clear()
            self.card_dot_labels.clear()
            self._active_card_ids = current_states
            self._active_tab_snapshot = "active"

            # RENDER ACTIVE QUEUE
            if not self.app_state.queue_list:
                placeholder = ctk.CTkLabel(
                    self.scroll_frame,
                    text=TRANSLATIONS[lang]["lbl_queue_item_placeholder"],
                    font=ctk.CTkFont(family="Segoe UI", size=12, slant="italic"),
                    text_color=THEME_TEXT_SECONDARY,
                )
                placeholder.grid(row=0, column=0, pady=40, sticky="ew")
                return

            for idx, item in enumerate(self.app_state.queue_list):
                card = ctk.CTkFrame(
                    self.scroll_frame,
                    fg_color=THEME_CARD_BG,
                    border_color=THEME_CARD_BORDER,
                    border_width=1,
                    corner_radius=10
                )
                card.grid(row=idx, column=0, padx=6, pady=4, sticky="ew")
                card.grid_columnconfigure(1, weight=1)
                card.grid_columnconfigure((0, 2, 3, 4), weight=0)

                # Dot indicator color
                dot_color = self._dot_color_for_status(item.status_code)

                dot_lbl = ctk.CTkLabel(card, text="●", text_color=dot_color, font=ctk.CTkFont(size=14))
                dot_lbl.grid(row=0, column=0, padx=(12, 6))
                self.card_dot_labels[item.id] = dot_lbl

                # Text Title
                title_text = item.title
                if len(title_text) > 40:
                    title_text = title_text[:37] + "..."
                title_lbl = ctk.CTkLabel(card, text=title_text, font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=THEME_TEXT_PRIMARY, anchor="w")
                title_lbl.grid(row=0, column=1, padx=6, pady=8, sticky="w")

                # Format preset label badge
                preset_name = str(item.preset).upper()
                badge_lbl = ctk.CTkLabel(card, text=f"[{preset_name}]", text_color=THEME_CARD_SUBTITLE, font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"))
                badge_lbl.grid(row=0, column=2, padx=10)

                # Status label (using translations)
                display_status = self._get_translated_status(item, lang)
                if item.status_code == TaskStatus.DOWNLOADING:
                    dl_str = TRANSLATIONS[lang].get("lbl_task_downloading", "Downloading")
                    display_status = f"{dl_str} ({item.percent:.1f}% - {item.speed})"
                elif item.status_code == TaskStatus.PAUSED:
                    display_status = TRANSLATIONS[lang].get("lbl_task_paused", "Paused")

                status_lbl = ctk.CTkLabel(card, text=display_status, font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=THEME_TEXT_SECONDARY)
                status_lbl.grid(row=0, column=3, padx=10)
                self.card_status_labels[item.id] = status_lbl

                # Remove or Cancel Button based on active downloading state
                is_active = item.status_code == TaskStatus.DOWNLOADING
                if is_active and self.on_cancel_task:
                    btn_text = TRANSLATIONS[lang]["btn_cancel"]
                    btn_color = THEME_BG
                    hover_color = THEME_ACCENT_RED
                    text_color = THEME_ACCENT_RED
                    cmd = lambda t_id=item.id: self.on_cancel_task(t_id)
                else:
                    btn_text = TRANSLATIONS[lang]["lbl_queue_remove"]
                    btn_color = THEME_BG
                    hover_color = THEME_ACCENT_RED
                    text_color = THEME_TEXT_PRIMARY
                    cmd = lambda i=idx: self.on_remove_item(i)

                rem_btn = ctk.CTkButton(
                    card,
                    text=btn_text,
                    width=75 if is_active else 60,
                    height=26,
                    fg_color=btn_color,
                    hover_color=hover_color,
                    text_color=text_color,
                    border_color=THEME_CARD_BORDER,
                    border_width=1,
                    corner_radius=6,
                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                    command=cmd
                )
                rem_btn.grid(row=0, column=4, padx=(6, 12))

        else:
            # History tab — always reset diffing state
            self._active_card_ids = []
            self._active_tab_snapshot = "history"
            for child in self.scroll_frame.winfo_children():
                child.destroy()

            # RENDER PERSISTENT HISTORY FROM SQLITE
            downloads = get_all_downloads()
            if not downloads:
                placeholder = ctk.CTkLabel(
                    self.scroll_frame,
                    text="İndirme geçmişi bulunamadı." if lang == "tr" else "No download history found.",
                    font=ctk.CTkFont(family="Segoe UI", size=12, slant="italic"),
                    text_color=THEME_TEXT_SECONDARY,
                )
                placeholder.grid(row=0, column=0, pady=40, sticky="ew")
                return

            for idx, item in enumerate(downloads):
                card = ctk.CTkFrame(
                    self.scroll_frame,
                    fg_color=THEME_CARD_BG,
                    border_color=THEME_CARD_BORDER,
                    border_width=1,
                    corner_radius=10
                )
                card.grid(row=idx, column=0, padx=6, pady=4, sticky="ew")
                card.grid_columnconfigure(2, weight=1)
                card.grid_columnconfigure((0, 1, 3, 4, 5, 6), weight=0)

                # Status Dot Indicator
                dot_color = THEME_TEXT_SECONDARY
                status_str = item.get("status", "COMPLETED")
                if status_str == "COMPLETED":
                    dot_color = THEME_ACCENT_GREEN
                elif status_str == "DOWNLOADING":
                    dot_color = THEME_ACCENT_INDIGO
                elif status_str in ("PAUSED", "Paused"):
                    dot_color = "#d97706"
                elif status_str in ("CANCELLED", "FAILED"):
                    dot_color = THEME_ACCENT_RED
                else:
                    dot_color = THEME_ACCENT_BLUE

                ctk.CTkLabel(card, text="●", text_color=dot_color, font=ctk.CTkFont(size=14)).grid(row=0, column=0, padx=(12, 4))

                # Thumbnail Column 1 (Async Cache Loaded)
                thumb_path = item.get("thumbnail_path")
                thumb_lbl = ctk.CTkLabel(card, text="🎬", width=80, height=45, fg_color=THEME_BG, corner_radius=6)
                thumb_lbl.grid(row=0, column=1, padx=6, pady=4)
                
                if thumb_path:
                    if thumb_path in self.image_cache:
                        thumb_lbl.configure(image=self.image_cache[thumb_path], text="")
                    else:
                        self._async_load_thumbnail(thumb_path, thumb_lbl)

                # Text Title on Column 2
                title_text = item.get("title", "Unknown Video")
                if len(title_text) > 40:
                    title_text = title_text[:37] + "..."
                title_lbl = ctk.CTkLabel(card, text=title_text, font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=THEME_TEXT_PRIMARY, anchor="w")
                title_lbl.grid(row=0, column=2, padx=6, pady=8, sticky="w")

                # Format details on Column 3
                format_lbl = ctk.CTkLabel(card, text=item.get("format", "Video"), text_color=THEME_CARD_SUBTITLE, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"))
                format_lbl.grid(row=0, column=3, padx=10)

                # Date of download on Column 4
                timestamp = item.get("downloaded_at", 0)
                time_struct = time.localtime(timestamp)
                date_str = time.strftime("%d/%m/%Y %H:%M", time_struct)
                date_lbl = ctk.CTkLabel(card, text=date_str, font=ctk.CTkFont(family="Segoe UI", size=10), text_color=THEME_TEXT_SECONDARY)
                date_lbl.grid(row=0, column=4, padx=10)

                # 1. Premium "Re-download" Button on Column 5
                redl_btn = ctk.CTkButton(
                    card,
                    text=TRANSLATIONS[lang]["btn_redownload"],
                    width=90,
                    height=26,
                    fg_color=THEME_BG,
                    hover_color=THEME_ACCENT_BLUE,
                    text_color=THEME_TEXT_PRIMARY,
                    border_color=THEME_CARD_BORDER,
                    border_width=1,
                    corner_radius=6,
                    font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                    command=lambda u=item.get("url"), f=item.get("format"): self.on_redownload(u, f)
                )
                redl_btn.grid(row=0, column=5, padx=4)

                # 2. Premium "Open Folder" Button (only active if file path exists) on Column 6
                file_path = item.get("file_path", "")
                folder_exists = file_path and os.path.exists(Path(file_path).parent)
                folder_state = "normal" if folder_exists else "disabled"
                
                folder_btn = ctk.CTkButton(
                    card,
                    text=TRANSLATIONS[lang]["btn_open_folder"],
                    width=80,
                    height=26,
                    state=folder_state,
                    fg_color=THEME_BG,
                    hover_color=THEME_CARD_BORDER,
                    text_color=THEME_TEXT_PRIMARY,
                    border_color=THEME_CARD_BORDER,
                    border_width=1,
                    corner_radius=6,
                    font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                    command=lambda p=file_path: self._open_native_folder(p)
                )
                folder_btn.grid(row=0, column=6, padx=(4, 12))

    @staticmethod
    def _dot_color_for_status(status_code: TaskStatus) -> str:
        """Map TaskStatus enum to dot indicator color."""
        if status_code == TaskStatus.PENDING:
            return THEME_ACCENT_BLUE
        elif status_code == TaskStatus.DOWNLOADING:
            return THEME_ACCENT_INDIGO
        elif status_code == TaskStatus.COMPLETED:
            return THEME_ACCENT_GREEN
        elif status_code in (TaskStatus.FAILED, TaskStatus.CANCELLED):
            return THEME_ACCENT_RED
        return THEME_TEXT_SECONDARY

    def _open_native_folder(self, file_path_str: str):
        # Bug Fix 3: Cross-platform native folder opening (instead of os.startfile)
        if not file_path_str:
            return
        
        path = Path(file_path_str).parent
        if not path.exists():
            return
            
        system = platform.system()
        if system == "Windows":
            os.startfile(str(path))
        elif system == "Darwin":
            subprocess.run(["open", str(path)])
        else:
            subprocess.run(["xdg-open", str(path)])

    def refresh_translations(self):
        lang = self.app_state.current_lang
        
        # Re-build Segmented button values to update translations
        active_tab_txt = TRANSLATIONS[lang]["tab_active"]
        history_tab_txt = TRANSLATIONS[lang]["tab_history"]
        
        curr_selection = self.tab_selector_var.get()
        self.tab_selector.configure(values=[active_tab_txt, history_tab_txt])
        
        if curr_selection == "history":
            self.tab_selector_var.set(history_tab_txt)
        else:
            self.tab_selector_var.set(active_tab_txt)
            
        self.btn_clear_history.configure(
            text="🧹 " + ("Geçmişi Temizle" if lang == "tr" else ("Clear History" if lang == "en" else "Limpiar Historial"))
        )
        
        self.update_list()

```

---

## <a name="file-uipanelsadvanced_panelpy"></a> 📄 File: `ui/panels/advanced_panel.py`
**Responsibility**: Contains the CTkTabView containing advanced download options: codecs, browser cookie extractors, retry limits, and custom preset builders.

```python
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
        
        # User explicit setting tracking
        self.user_explicit = False
        self._applying_programmatic = False
        
        self.grid_columnconfigure(0, weight=1)
        self._build_ui()
        self._load_presets_dropdown()
        self._setup_change_traces()

    def _setup_change_traces(self):
        vars_to_trace = [
            self.mode_var,
            self.video_profile_var,
            self.custom_video_height_var,
            self.video_container_var,
            self.audio_format_var,
            self.audio_quality_var,
            self.video_audio_codec_var,
            self.playlist_var,
            self.metadata_var,
            self.thumbnail_var,
            self.subs_var,
            self.auto_subs_var,
            self.restrict_names_var,
            self.download_archive_var,
            self.retries_var,
            self.concurrent_fragments_var,
            self.cookies_var,
            self.browser_cookies_var,
            self.youtube_403_fallback_var,
            self.max_workers_var,
            self.scheduler_enabled_var,
            self.schedule_time_var,
            self.playlist_items_var,
            self.max_downloads_var,
            self.rate_limit_var,
            self.sponsorblock_var,
            self.folder_org_var
        ]
        for var in vars_to_trace:
            var.trace_add("write", self._on_var_changed)

    def _on_var_changed(self, *args):
        if not self._applying_programmatic:
            self.user_explicit = True

    def reset_user_explicit(self):
        self.user_explicit = False

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
        self.tab_schedule = self.tabview.add(TRANSLATIONS[lang]["tab_scheduling"])

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
            values=["AAC", "OPUS (Open)"],
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

        self.lbl_concurrent_frag = ctk.CTkLabel(l1, text="Eşzamanlı Parça" if lang == "tr" else ("Fragmentos Conc." if lang == "es" else "Concurrent Frags"), text_color=THEME_TEXT_PRIMARY)
        self.lbl_concurrent_frag.grid(row=3, column=0, sticky="w", padx=6, pady=6)
        
        self.concurrent_fragments_var = ctk.StringVar(value="3")
        self.concurrent_fragments_entry = ctk.CTkEntry(l1, textvariable=self.concurrent_fragments_var, placeholder_text="Ex: 3", height=30, fg_color=THEME_BG, border_color=THEME_CARD_BORDER, border_width=1, text_color=THEME_TEXT_PRIMARY)
        self.concurrent_fragments_entry.grid(row=3, column=1, sticky="ew", padx=6, pady=6)

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

        # Max Concurrent Downloads Option Menu (1, 2, 3, 4, 5 parallel tasks)
        self.lbl_max_workers = ctk.CTkLabel(l2, text="Maks. Eşzamanlı İndirme:" if lang == "tr" else ("Descargas Simultáneas:" if lang == "es" else "Max Parallel Downloads:"), text_color=THEME_TEXT_PRIMARY)
        self.lbl_max_workers.grid(row=3, column=0, sticky="w", padx=6, pady=6)
        
        self.max_workers_var = ctk.StringVar(value=str(self.app_state.preferences.max_workers))
        self.max_workers_menu = ctk.CTkOptionMenu(
            l2,
            values=["1", "2", "3", "4", "5"],
            variable=self.max_workers_var,
            fg_color=THEME_BG,
            button_color=THEME_BG,
            button_hover_color=THEME_CARD_BORDER,
            text_color=THEME_TEXT_PRIMARY,
            dropdown_fg_color=THEME_CARD_BG,
            dropdown_hover_color=THEME_CARD_BORDER,
            dropdown_text_color=THEME_TEXT_PRIMARY,
            height=30,
            command=self._on_max_workers_changed
        )
        self.max_workers_menu.grid(row=3, column=1, sticky="ew", padx=6, pady=6)

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

        # Smart Folder Organization UI
        self.lbl_folder_org = ctk.CTkLabel(f1, text=TRANSLATIONS[lang]["lbl_folder_org"], text_color=THEME_TEXT_PRIMARY)
        self.lbl_folder_org.grid(row=4, column=0, sticky="w", padx=6, pady=(10, 2))
        
        self.folder_org_var = ctk.StringVar(value="None")
        
        self.folder_org_menu = ctk.CTkOptionMenu(
            f1,
            values=[],
            variable=self.folder_org_var,
            fg_color=THEME_BG,
            button_color=THEME_BG,
            button_hover_color=THEME_CARD_BORDER,
            text_color=THEME_TEXT_PRIMARY,
            dropdown_fg_color=THEME_CARD_BG,
            dropdown_hover_color=THEME_CARD_BORDER,
            dropdown_text_color=THEME_TEXT_PRIMARY,
            height=30,
            command=self._on_folder_org_menu_changed
        )
        self.folder_org_menu.grid(row=5, column=0, sticky="ew", padx=6, pady=2)
        self._update_folder_org_dropdown()

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

        # ==================== TAB 4: SCHEDULER & ZAMANLAYICI ====================
        self.tab_schedule.grid_columnconfigure(0, weight=1)
        
        s_frame = ctk.CTkFrame(self.tab_schedule, fg_color="transparent")
        s_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        s_frame.grid_columnconfigure(1, weight=1)

        # 1. Schedule Enabled switch
        self.scheduler_enabled_var = tk.BooleanVar(value=False)
        self.chk_schedule = ctk.CTkCheckBox(
            s_frame,
            text=TRANSLATIONS[lang]["lbl_schedule_enable"],
            variable=self.scheduler_enabled_var,
            fg_color=THEME_ACCENT_INDIGO,
            text_color=THEME_TEXT_PRIMARY,
            command=self._on_schedule_changed
        )
        self.chk_schedule.grid(row=0, column=0, columnspan=2, padx=6, pady=8, sticky="w")

        # 2. Schedule Time Label & Input
        self.lbl_schedule_time = ctk.CTkLabel(s_frame, text=TRANSLATIONS[lang]["lbl_schedule_time"], text_color=THEME_TEXT_PRIMARY)
        self.lbl_schedule_time.grid(row=1, column=0, sticky="w", padx=6, pady=8)
        
        self.schedule_time_var = ctk.StringVar(value="03:00")
        self.schedule_time_entry = ctk.CTkEntry(
            s_frame,
            textvariable=self.schedule_time_var,
            placeholder_text="03:00",
            height=30,
            fg_color=THEME_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            text_color=THEME_TEXT_PRIMARY
        )
        self.schedule_time_entry.grid(row=1, column=1, sticky="w", padx=6, pady=8, ipadx=20)
        self.schedule_time_entry.configure(state="disabled")

        # Description Label
        self.lbl_schedule_desc = ctk.CTkLabel(
            s_frame,
            text=TRANSLATIONS[lang]["lbl_schedule_desc"],
            text_color=THEME_TEXT_SECONDARY,
            font=ctk.CTkFont(family="Segoe UI", size=11, slant="italic")
        )
        self.lbl_schedule_desc.grid(row=2, column=0, columnspan=2, padx=6, pady=8, sticky="w")



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

    def _update_folder_org_dropdown(self):
        lang = self.app_state.current_lang
        val_map = {
            "None": TRANSLATIONS[lang]["folder_org_none"],
            "Channel": TRANSLATIONS[lang]["folder_org_channel"],
            "Year": TRANSLATIONS[lang]["folder_org_year"],
            "Format": TRANSLATIONS[lang]["folder_org_format"],
            "Channel_Year": TRANSLATIONS[lang]["folder_org_channel_year"],
        }
        curr_logical = self.get_folder_org_logical()
        translated_vals = list(val_map.values())
        self.folder_org_menu.configure(values=translated_vals)
        t_val = val_map.get(curr_logical, translated_vals[0])
        self.folder_org_var.set(t_val)

    def get_folder_org_logical(self) -> str:
        choice = self.folder_org_var.get()
        # Find choice in TRANSLATIONS across all lang codes to map logically
        for lang in TRANSLATIONS:
            val_map = {
                "None": TRANSLATIONS[lang]["folder_org_none"],
                "Channel": TRANSLATIONS[lang]["folder_org_channel"],
                "Year": TRANSLATIONS[lang]["folder_org_year"],
                "Format": TRANSLATIONS[lang]["folder_org_format"],
                "Channel_Year": TRANSLATIONS[lang]["folder_org_channel_year"],
            }
            inverse_map = {v: k for k, v in val_map.items()}
            if choice in inverse_map:
                return inverse_map[choice]
        return "None"

    def _on_folder_org_menu_changed(self, choice):
        self.user_explicit = True

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

    def _on_max_workers_changed(self, choice):
        try:
            self.app_state.preferences.max_workers = int(choice)
        except Exception:
            pass

    def _on_schedule_changed(self):
        if self.scheduler_enabled_var.get():
            self.schedule_time_entry.configure(state="normal")
        else:
            self.schedule_time_entry.configure(state="disabled")

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
        
        self._applying_programmatic = True
        try:
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
            
            self.concurrent_fragments_var.set(p.get("concurrent_fragments", "3"))
            self.playlist_items_var.set(p.get("playlist_items", ""))
            self.max_downloads_var.set(p.get("max_downloads", ""))
            self.rate_limit_var.set(p.get("rate_limit", ""))

            # Smart Folder
            logical_folder = p.get("folder_org", "None")
            lang = self.app_state.current_lang
            val_map = {
                "None": TRANSLATIONS[lang]["folder_org_none"],
                "Channel": TRANSLATIONS[lang]["folder_org_channel"],
                "Year": TRANSLATIONS[lang]["folder_org_year"],
                "Format": TRANSLATIONS[lang]["folder_org_format"],
                "Channel_Year": TRANSLATIONS[lang]["folder_org_channel_year"],
            }
            t_val = val_map.get(logical_folder, val_map["None"])
            self.folder_org_var.set(t_val)

            if self.on_preset_loaded:
                self.on_preset_loaded()
        finally:
            self._applying_programmatic = False
        self.user_explicit = True

    def _prompt_save_preset(self):
        lang = self.app_state.current_lang
        prompt_txt = TRANSLATIONS[lang].get("msg_prompt_preset_name", "Enter new preset profile name:")
        prompt_title = TRANSLATIONS[lang].get("msg_save_preset_title", "Save Preset Profile")
        dialog = ctk.CTkInputDialog(
            text=prompt_txt,
            title=prompt_title
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
                "rate_limit": self.rate_limit_var.get(),
                "concurrent_fragments": self.concurrent_fragments_var.get(),
                "folder_org": self.get_folder_org_logical()
            }
            save_preset(name, preset_dict)
            self._load_presets_dropdown()
            self.presets_dropdown_var.set(name)
            title = TRANSLATIONS[lang].get("msg_success_title", "Success")
            msg = TRANSLATIONS[lang].get("msg_preset_saved", "'{}' preset profile successfully saved.").format(name)
            messagebox.showinfo(title, msg)

    def _delete_selected_preset(self):
        name = self.presets_dropdown_var.get()
        if not name:
            return
        lang = self.app_state.current_lang
        title = TRANSLATIONS[lang].get("msg_confirm_delete_title", "Are you sure?")
        msg = TRANSLATIONS[lang].get("msg_confirm_delete", "Are you sure you want to delete '{}' template?").format(name)
        if messagebox.askyesno(title, msg):
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
            "concurrent_fragments": self.concurrent_fragments_var.get(),
            "cookies": self.cookies_var.get(),
            "browser_cookies": self.browser_cookies_var.get(),
            "youtube_403": self.youtube_403_fallback_var.get(),
            "max_workers": int(self.max_workers_var.get()),
            "scheduler_enabled": self.scheduler_enabled_var.get(),
            "scheduler_time": self.schedule_time_var.get(),
            "options_source": "User_Explicit" if self.user_explicit else "Default",
            "folder_org": self.get_folder_org_logical()
        }

    def apply_settings_dict(self, d: dict):
        self._applying_programmatic = True
        try:
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
            self.concurrent_fragments_var.set(d.get("concurrent_fragments", "3"))
            self.download_archive_var.set(d.get("archive", True))
            self.retries_var.set(d.get("retries", ""))
            self.cookies_var.set(d.get("cookies", ""))
            self.browser_cookies_var.set(d.get("browser_cookies", "Kapali"))
            self.youtube_403_fallback_var.set(d.get("youtube_403", True))
            self.max_workers_var.set(str(d.get("max_workers", 3)))
            self.app_state.preferences.max_workers = int(self.max_workers_var.get())
            self.scheduler_enabled_var.set(d.get("scheduler_enabled", False))
            self._on_schedule_changed()
            self.schedule_time_var.set(d.get("scheduler_time", "03:00"))
            
            opt_src = d.get("options_source", "Default")
            self.user_explicit = (opt_src == "User_Explicit")

            # Smart Folder Restore
            logical_folder = d.get("folder_org", "None")
            lang = self.app_state.current_lang
            val_map = {
                "None": TRANSLATIONS[lang]["folder_org_none"],
                "Channel": TRANSLATIONS[lang]["folder_org_channel"],
                "Year": TRANSLATIONS[lang]["folder_org_year"],
                "Format": TRANSLATIONS[lang]["folder_org_format"],
                "Channel_Year": TRANSLATIONS[lang]["folder_org_channel_year"],
            }
            t_val = val_map.get(logical_folder, val_map["None"])
            self.folder_org_var.set(t_val)
        finally:
            self._applying_programmatic = False

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
        self.lbl_max_workers.configure(text="Maks. Eşzamanlı İndirme:" if lang == "tr" else ("Descargas Simultáneas:" if lang == "es" else "Max Parallel Downloads:"))

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

        # Translate Smart Folder UI
        self.lbl_folder_org.configure(text=TRANSLATIONS[lang]["lbl_folder_org"])
        self._update_folder_org_dropdown()

```

---

## <a name="file-uipanelsprogress_panelpy"></a> 📄 File: `ui/panels/progress_panel.py`
**Responsibility**: Renders progress bars, speed/ETA/size widgets, terminal logs frame, and execution controllers.

```python
# ui/panels/progress_panel.py
import tkinter as tk
import customtkinter as ctk
from ui.theme import (
    THEME_BG, THEME_CARD_BG, THEME_CARD_BORDER, THEME_TEXT_PRIMARY,
    THEME_TEXT_SECONDARY, THEME_ACCENT_BLUE, THEME_ACCENT_INDIGO,
    THEME_ACCENT_GREEN, THEME_ACCENT_RED, TRANSLATIONS
)
from core.app_state import AppState, TaskStatus
from core.utils import parse_speed_to_mbps

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

        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_card_col = THEME_CARD_BG[1] if is_dark else THEME_CARD_BG[0]
        self.progress_canvas = tk.Canvas(
            progress_container,
            height=12,
            bg=bg_card_col,
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
        bg_col = THEME_BG[1] if is_dark else THEME_BG[0]
        self.graph_canvas = tk.Canvas(self, height=50, bg=bg_col, highlightthickness=0, bd=0)
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
        bg_card_col = THEME_CARD_BG[1] if is_dark else THEME_CARD_BG[0]
        self.progress_canvas.configure(bg=bg_card_col)
        
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
        raw_mbps = parse_speed_to_mbps(speed_str)
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

```

---

## <a name="file-uimain_windowpy"></a> 📄 File: `ui/main_window.py`
**Responsibility**: Central Tkinter layout orchestrator and thread dispatcher. Drains worker threads, handles window bindings, and prompts for system dependencies (Deno via winget).

```python
# ui/main_window.py
import os
import sys
import queue
import re
import shutil
import threading
import urllib.request
import hashlib
import platform
import uuid
import subprocess
import datetime
import time
from pathlib import Path
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image, ImageTk

# Core imports
from core.app_state import AppState, TaskStatus, save_app_preferences
from core.downloader import run_queue_executor, resolve_ffmpeg_path, kill_all_active_subprocesses
from core.history import init_db, add_download_record, get_all_downloads, shutdown_db, get_channel_rule
from core.clip import decide_clip_strategy, parse_time_to_seconds, format_seconds_to_mmss
from core.controller import AppController

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
        self.ui_queue = queue.Queue(maxsize=500)
        self.cancel_event = threading.Event()
        self._queue_lock = threading.RLock()
        self.last_fetched_url = ""
        self.controller = AppController(state)
        
        # Setup paths
        self.app_state.output_dir = str(Path.home() / "Downloads" / "yt-downloads")
        self.scratch_dir = Path.home() / ".yt-downloader-scratch"
        self.scratch_dir.mkdir(parents=True, exist_ok=True)
        
        # Init SQLite History database
        init_db()

        # Premium Glassmorphic Configuration
        self.title("yt-dlp Downloader Pro")
        self.geometry("1100x820")
        self.resizable(True, True)
        self.minsize(1000, 750)
        
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
 
        # Main Container Frame (instead of scrollable frame)
        self.main_container = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(0, weight=0) # Header Card
        self.main_container.grid_rowconfigure(1, weight=1) # Columns row
 
        # Side-by-side Columns
        self.left_column = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.left_column.grid(row=1, column=0, padx=(0, 6), pady=(6, 0), sticky="nsew")
        self.left_column.grid_columnconfigure(0, weight=1)
        self.left_column.grid_rowconfigure(0, weight=0) # URL Panel
        self.left_column.grid_rowconfigure(1, weight=1) # Preview Panel
        self.left_column.grid_rowconfigure(2, weight=0) # Advanced Panel

        self.right_column = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.right_column.grid(row=1, column=1, padx=(6, 0), pady=(6, 0), sticky="nsew")
        self.right_column.grid_columnconfigure(0, weight=1)
        self.right_column.grid_rowconfigure(0, weight=1) # Queue Panel
        self.right_column.grid_rowconfigure(1, weight=0) # Progress Panel

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
        if platform.system() != "Windows":
            return

        def bg_check():
            import shutil
            if shutil.which('deno') or shutil.which('node'):
                return
            
            self.after(0, self._show_deno_prompt)

        threading.Thread(target=bg_check, daemon=True, name="deno-env-checker").start()

    def _show_deno_prompt(self) -> None:
        import shutil
        from core.env import refresh_path_env
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
                    
            threading.Thread(target=installer_thread, daemon=True, name="deno-installer").start()

    def _build_header_card(self):
        lang = self.app_state.current_lang
        
        # Header frosted glass card
        header_card = ctk.CTkFrame(
            self.main_container,
            fg_color=THEME_CARD_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            corner_radius=16
        )
        header_card.grid(row=0, column=0, columnspan=2, padx=4, pady=6, sticky="ew")
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

        self.btn_compact_mode = ctk.CTkButton(
            config_frame,
            text="",
            width=110,
            height=30,
            corner_radius=8,
            fg_color=THEME_BG,
            text_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_CARD_BORDER,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._toggle_compact_mode,
        )
        self.btn_compact_mode.grid(row=0, column=2, padx=4, pady=4, sticky="e")

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
        self.url_panel = UrlPanel(self.left_column, self.app_state, self._trigger_metadata_fetch)
        self.url_panel.grid(row=0, column=0, padx=4, pady=6, sticky="ew")

        # 2. Preview Panel (Metadata Viewer)
        self.preview_panel = PreviewPanel(self.left_column, self.app_state, self._on_chapter_clicked, self._on_create_channel_rule)
        self.preview_panel.grid(row=1, column=0, padx=4, pady=6, sticky="nsew")
        self.preview_panel.hide()

        # 3. Advanced Panel (Gelişmiş Ayarlar)
        self.advanced_panel = AdvancedPanel(self.left_column, self.app_state, self._on_preset_applied)
        self.advanced_panel.grid(row=2, column=0, padx=4, pady=6, sticky="ew")

        # 4. Queue Panel (Kuyruk listesi & Geçmiş)
        self.queue_panel = QueuePanel(self.right_column, self.app_state, self._remove_from_queue, self._redownload_historic_item, self._cancel_single_task)
        self.queue_panel.grid(row=0, column=0, padx=4, pady=6, sticky="nsew")

        # 5. Progress Dashboard Panel (İndirme İlerleme Paneli)
        self.progress_panel = ProgressPanel(self.right_column, self.app_state, self._start_download, self._cancel_download, self._open_output_dir)
        self.progress_panel.grid(row=1, column=0, padx=4, pady=6, sticky="ew")

        # Bind close handler
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Initialize context-aware cross-platform keyboard shortcuts
        self._setup_shortcuts()

        # Apply initial compact mode layout state
        self._apply_compact_mode()

    def _setup_shortcuts(self):
        import sys
        from core.app_state import TaskStatus
        modifier = "Command" if sys.platform == "darwin" else "Control"
        
        # 1. Paste & Fetch: Ctrl+V or Cmd+V
        self.bind_all(f"<{modifier}-v>", self._handle_shortcut_paste)
        # 2. Start Download: Ctrl+Enter or Cmd+Return
        self.bind_all(f"<{modifier}-Return>", self._handle_shortcut_start_download)
        # 3. Pause/Resume active download task: Space
        self.bind_all("<space>", self._handle_shortcut_space)
        # 4. Cancel active queue download: Escape
        self.bind_all("<Escape>", self._handle_shortcut_escape)

    def _handle_shortcut_paste(self, event):
        focused = self.focus_get()
        # If user is in an entry or text field, bypass global hook
        if isinstance(focused, (ctk.CTkEntry, ctk.CTkTextbox)) or (focused and "entry" in str(focused).lower()) or (focused and "text" in str(focused).lower()):
            return
        try:
            clipboard_text = self.clipboard_get()
            if clipboard_text and clipboard_text.strip().startswith(("http://", "https://")):
                self.url_panel.set_url(clipboard_text.strip())
                self._trigger_metadata_fetch()
                return "break"
        except Exception:
            pass

    def _handle_shortcut_start_download(self, event):
        focused = self.focus_get()
        if isinstance(focused, ctk.CTkTextbox) or (focused and "text" in str(focused).lower()):
            return
        url = self.app_state.url.strip()
        if url.startswith(("http://", "https://")) or self.app_state.queue_list:
            self._start_download()
            return "break"

    def _handle_shortcut_space(self, event):
        from core.app_state import TaskStatus
        focused = self.focus_get()
        if isinstance(focused, (ctk.CTkEntry, ctk.CTkTextbox)) or (focused and "entry" in str(focused).lower()) or (focused and "text" in str(focused).lower()):
            return
            
        # Space pauses/resumes active download
        active_task = None
        for task in self.app_state.queue_list:
            if task.status_code == TaskStatus.DOWNLOADING or getattr(task, "is_paused", False):
                active_task = task
                break
        if active_task:
            from core.downloader import toggle_pause_task
            toggle_pause_task(active_task)
            self.queue_panel.update_list()
            return "break"

    def _handle_shortcut_escape(self, event):
        focused = self.focus_get()
        if isinstance(focused, (ctk.CTkEntry, ctk.CTkTextbox)) or (focused and "entry" in str(focused).lower()) or (focused and "text" in str(focused).lower()):
            return
        if self.app_state.is_executor_running:
            self._cancel_download()
            return "break"

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
        
        # Reset the manual override track on new preview
        self.advanced_panel.reset_user_explicit()

        # Call async metadata fetch (controller handles background thread execution)
        self._run_metadata_fetch(url)

    def _on_create_channel_rule(self, channel_id: str, channel_name: str):
        settings_dict = self.advanced_panel.get_settings_dict()
        # Keep clean patch: remove output_dir and transient fields
        keys_to_remove = ["cookies", "scheduler_time", "scheduler_enabled", "options_source"]
        for k in keys_to_remove:
            if k in settings_dict:
                del settings_dict[k]
                
        from core.history import save_channel_rule
        save_channel_rule(channel_id, channel_name, settings_dict)
        
        lang = self.app_state.current_lang
        msg = f"Kanal kuralı kaydedildi: {channel_name}" if lang == "tr" else (f"Regla de canal guardada: {channel_name}" if lang == "es" else f"Channel rule saved: {channel_name}")
        self.progress_panel.append_log_batch([f"[Kanal Kuralı] {msg}\n"])
        messagebox.showinfo("Başarılı" if lang == "tr" else ("Éxito" if lang == "es" else "Success"), msg)

    def _run_metadata_fetch(self, url: str) -> None:
        settings = self.advanced_panel.get_settings_dict()
        cookies_file = settings.get("cookies", "").strip()
        browser_cookies = settings.get("browser_cookies", "").strip().lower()

        def on_success(metadata):
            local_thumb_img = None
            thumb_path = metadata.get("thumbnail_path")
            if thumb_path:
                try:
                    with Image.open(thumb_path) as pil_img:
                        resized_ui = pil_img.resize((160, 90), Image.Resampling.LANCZOS).copy()
                    local_thumb_img = ctk.CTkImage(light_image=resized_ui, dark_image=resized_ui, size=(160, 90))
                except Exception as e:
                    print(f"Error loading thumbnail in UI: {e}")

            fetched_metadata = {
                "url": url,
                "title": metadata["title"],
                "uploader": metadata["uploader"],
                "duration": metadata["duration"],
                "thumbnail_img": local_thumb_img,
                "chapters": metadata["chapters"],
                "filesize": metadata["filesize"],
                "filesize_approx": metadata["filesize_approx"],
                "channel_id": metadata["channel_id"],
                "channel_name": metadata["channel_name"]
            }
            self.ui_queue.put(("metadata_ready", fetched_metadata))

        def on_error(err_str):
            print(f"[!] Metadata fetch failed: {err_str}")
            self.ui_queue.put(("metadata_error", err_str))

        from core.history import get_app_data_dir
        self.controller.run_metadata_fetch(
            url=url,
            cookies_file=cookies_file,
            browser_cookies=browser_cookies,
            scratch_dir=self.scratch_dir,
            app_data_dir=get_app_data_dir(),
            on_success_callback=on_success,
            on_error_callback=on_error
        )

    def _on_chapter_clicked(self, start_seconds: float, end_seconds: float, chapter_title: str):
        # Feature 3.4 Chapters auto-clipping selection integration directly inside PreviewPanel
        self.preview_panel.clip_enabled_var.set(True)
        self.preview_panel._on_clip_toggled()
        self.preview_panel.add_clip_row(start_seconds, end_seconds)

    def _on_preset_applied(self):
        # Refresh current profile preview hint
        pass

    # extract_video_id is unused in MainWindow and now imported from core.utils where needed

    def _add_to_queue(self) -> None:
        # Synchronize app_state.url with the UI before queueing to avoid empty/stale values
        if self.url_panel.batch_mode_var.get():
            lines = self.url_panel.url_textbox.get("1.0", "end-1c").splitlines()
            self.app_state.batch_urls = [l.strip() for l in lines if l.strip()]
            self.app_state.url = self.app_state.batch_urls[0] if self.app_state.batch_urls else ""
        else:
            self.app_state.url = self.url_panel.url_entry.get().strip()

        url = self.app_state.url.strip()
        if not url:
            messagebox.showwarning(TRANSLATIONS[self.app_state.current_lang]["lbl_dialog_warning_title"], TRANSLATIONS[self.app_state.current_lang]["lbl_dialog_warning_url"])
            return

        lang = self.app_state.current_lang
        item_cfg = self.advanced_panel.get_settings_dict()

        # 1. Check for duplicates using Controller
        is_duplicate, dup_title, dup_format = self.controller.check_duplicate(url, item_cfg)
        if is_duplicate:
            title_msg = TRANSLATIONS[lang]["lbl_duplicate_title"]
            body_template = TRANSLATIONS[lang]["lbl_duplicate_body"]
            body_msg = body_template.replace("{title}", dup_title).replace("{format}", dup_format)
            confirm = messagebox.askyesno(title_msg, body_msg)
            if not confirm:
                return

        # 2. Merge clipping parameters directly from PreviewPanel if not in batch mode
        if not self.app_state.is_batch_mode:
            item_cfg.update(self.preview_panel.get_clip_settings())
        else:
            item_cfg.update({
                "clip_enabled": False,
                "clip_start": "00:00",
                "clip_end": "00:00",
                "clip_precise": False,
                "export_profile": "Default (No Profile)"
            })

        # 3. Prepare multi-clip selections
        if item_cfg.get("clip_enabled") and not self.app_state.is_batch_mode:
            multi_clips = self.preview_panel.get_multi_clips()
        else:
            multi_clips = []

        # Ensure current thumbnail path is passed to task config
        item_cfg["thumbnail_path"] = getattr(self.app_state, "current_thumbnail_path", None)

        # 4. Delegate task creation and state append to Controller
        success, error, added_count = self.controller.validate_and_add_tasks(url, item_cfg, multi_clips, lang)
        
        if success:
            if self.app_state.is_batch_mode:
                self.url_panel.set_url("")
                self.progress_panel.update_status("●", THEME_ACCENT_BLUE, TRANSLATIONS[self.app_state.current_lang]["lbl_status_added"].format(count=added_count))
            else:
                self.url_panel.set_url("")
                self.preview_panel.hide()
                self.progress_panel.update_status("●", THEME_ACCENT_BLUE, TRANSLATIONS[self.app_state.current_lang]["lbl_status_ready"])
            
            # Post updates to progress panel if automated rules were applied
            if item_cfg.get("options_source") == "Default" and self.app_state.current_video_info and not self.app_state.is_batch_mode:
                ch_id = self.app_state.current_video_info.get("channel_id")
                if ch_id:
                    rule = get_channel_rule(ch_id)
                    if rule and rule.get("settings_dict"):
                        ch_name = rule.get("channel_name") or ch_id
                        msg = f"[Kanal Kuralı] {ch_name} için otomatik kural uygulandı.\n"
                        self.progress_panel.append_log_batch([msg])
        else:
            messagebox.showwarning(TRANSLATIONS[self.app_state.current_lang]["lbl_dialog_warning_title"], error)

        self.queue_panel.update_list()

    def _remove_from_queue(self, idx: int):
        with self.app_state._lock:
            if idx >= 0 and idx < len(self.app_state.queue_list):
                item = self.app_state.queue_list[idx]
                # Don't delete active downloading item
                if item.status_code == TaskStatus.DOWNLOADING:
                    return
                del self.app_state.queue_list[idx]
        self.queue_panel.update_list()

    def _cancel_single_task(self, task_id: str):
        with self.app_state._lock:
            for task in self.app_state.queue_list:
                if task.id == task_id:
                    task.cancel_event.set()
                    proc = getattr(task, "_process", None)
                    if proc:
                        try:
                            if getattr(task, "is_paused", False):
                                if os.name == 'nt':
                                    import ctypes
                                    ctypes.windll.ntdll.NtResumeProcess(proc._handle)
                                else:
                                    import signal
                                    os.kill(proc.pid, signal.SIGCONT)
                                task.is_paused = False
                            proc.terminate()
                        except Exception:
                            pass
                    lang = self.app_state.current_lang
                    task.status = "İptal Ediliyor" if lang == "tr" else ("Cancelando" if lang == "es" else "Cancelling")
                    task.status_code = TaskStatus.CANCELLED
                    self.queue_panel.update_list()
                    break

    def _redownload_historic_item(self, url: str, format_desc: str):
        # Feature 3.2: Re-download callback
        self.url_panel.set_url(url)
        self.app_state.url = url
        # Toggle mode based on history format description via Controller
        mode = self.controller.get_mode_from_format(format_desc)
        self.advanced_panel.mode_var.set(mode)
        self.advanced_panel._on_mode_changed(mode)
        
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

        # Synchronize app_state.url with the UI before starting to avoid empty/stale values
        if self.url_panel.batch_mode_var.get():
            lines = self.url_panel.url_textbox.get("1.0", "end-1c").splitlines()
            self.app_state.batch_urls = [l.strip() for l in lines if l.strip()]
            self.app_state.url = self.app_state.batch_urls[0] if self.app_state.batch_urls else ""
        else:
            self.app_state.url = self.url_panel.url_entry.get().strip()

        # Auto queue URL input if queue list empty
        if not self.app_state.queue_list:
            url = self.app_state.url.strip()
            if url:
                self._add_to_queue()
                if not self.app_state.queue_list:
                    return
            else:
                messagebox.showwarning(TRANSLATIONS[self.app_state.current_lang]["lbl_dialog_warning_title"], TRANSLATIONS[self.app_state.current_lang]["lbl_dialog_warning_url"])
                return

        self.cancel_event.clear()
        self.app_state.current_item_index = 0
        self.progress_panel.set_running_state(True)
        
        # Check if local schedule is active
        if self.advanced_panel.scheduler_enabled_var.get():
            time_str = self.advanced_panel.schedule_time_var.get().strip()
            threading.Thread(target=self._run_scheduler_wait_loop, args=(time_str,), daemon=True, name="scheduler-wait-loop").start()
        else:
            # Spawn queue background execution worker thread
            threading.Thread(target=run_queue_executor, args=(self.app_state, self.ui_queue, self.cancel_event), daemon=True, name="queue-executor").start()

    def _run_scheduler_wait_loop(self, target_time_str: str) -> None:
        lang = self.app_state.current_lang
        try:
            parts = target_time_str.split(":")
            hour = int(parts[0])
            minute = int(parts[1])
        except Exception:
            self.ui_queue.put(("log", f"[Zamanlayıcı] Hata: Geçersiz zaman formatı '{target_time_str}'. Lütfen SS:DD formatında girin.\n"))
            self.ui_queue.put(("status", ("●", "#ef4444", "Hata: Geçersiz Zaman")))
            return

        self.ui_queue.put(("log", f"[Zamanlayıcı] İndirme zamanlandı: İndirmeler saat {target_time_str} olduğunda başlayacak.\n"))
        
        # Windows sleep prevention during countdown
        from core.downloader import prevent_sleep, allow_sleep
        prevent_sleep()
        
        try:
            while not self.cancel_event.is_set():
                now = datetime.datetime.now()
                if now.hour == hour and now.minute == minute:
                    self.ui_queue.put(("log", "[Zamanlayıcı] Hedef saate ulaşıldı! İndirmeler başlatılıyor...\n"))
                    self.cancel_event.clear()
                    self.app_state.current_item_index = 0
                    threading.Thread(target=run_queue_executor, args=(self.app_state, self.ui_queue, self.cancel_event), daemon=True, name="queue-executor").start()
                    break
                
                target_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if target_dt < now:
                    target_dt += datetime.timedelta(days=1)
                remaining = int((target_dt - now).total_seconds())
                
                h = remaining // 3600
                m = (remaining % 3600) // 60
                s = remaining % 60
                countdown_msg = f"{h:02d}:{m:02d}:{s:02d}"
                status_text = f"Zamanlandı: {target_time_str} (Kalan: {countdown_msg})"
                
                self.ui_queue.put(("status", ("⏰", "#4f46e5", status_text)))
                time.sleep(1.0)
        finally:
            allow_sleep()

    def _cancel_download(self):
        self.cancel_event.set()
        with self.app_state._lock:
            for task in self.app_state.queue_list:
                task.cancel_event.set()
        kill_all_active_subprocesses()
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
    # ================== METRIC DRAINING & LIFECYCLE ==================
    def _drain_ui_queue(self) -> None:
        try:
            self._drain_ui_queue_impl()
        except Exception as e:
            import logging
            logging.error(f"[UI Queue Drainer] Fatal error: {e}", exc_info=True)
        finally:
            self.after(50, self._drain_ui_queue)

    def _drain_ui_queue_impl(self) -> None:
        processed = 0
        log_batch = []
        needs_progress_update = False
        needs_active_file_update = False
        while processed < 100:
            try:
                kind, payload = self.ui_queue.get_nowait()
            except queue.Empty:
                break
            processed += 1

            if kind == "log":
                log_batch.append(str(payload))
            elif kind == "stats":
                stats = payload
                task_id = stats["task_id"]
                percent_val = float(stats["percent"])
                
                # Find and update task model
                for t in self.app_state.queue_list:
                    if t.id == task_id:
                        t.percent = percent_val
                        t.size = stats["size"]
                        t.speed = stats["speed"]
                        t.eta = stats["eta"]
                        break

                # Update the task progress dynamically in the card list without redrawing
                self.queue_panel.update_task_progress(
                    task_id=task_id,
                    percent=percent_val,
                    speed=stats["speed"],
                    eta=stats["eta"],
                    size=stats["size"]
                )

                needs_progress_update = True

            elif kind == "active_file":
                task_id, filename = payload
                for t in self.app_state.queue_list:
                    if t.id == task_id:
                        t.active_filename = filename
                        break
                needs_active_file_update = True
            elif kind == "percent_complete":
                pass # Handled by update_global_progress
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
                    self.progress_panel.show_completion_animation(success=False)
                else:
                    self.progress_panel.update_status("●", THEME_ACCENT_GREEN, TRANSLATIONS[self.app_state.current_lang]["lbl_status_completed"])
                    self.progress_panel.show_completion_animation(success=True)
                    self._show_toast(TRANSLATIONS[self.app_state.current_lang]["lbl_toast_all_title"], TRANSLATIONS[self.app_state.current_lang]["lbl_toast_all_desc"])

        # Coalesced UI updates — called at most once per drain cycle
        if needs_progress_update:
            self.progress_panel.update_global_progress(self.app_state.queue_list)

        if needs_active_file_update:
            active_tasks = [t for t in self.app_state.queue_list if t.status_code == TaskStatus.DOWNLOADING]
            if active_tasks:
                titles = ", ".join(t.title[:15] + "..." for t in active_tasks)
                self.progress_panel.active_file_var.set(f"Aktif İndirmeler: {titles}")

        if log_batch:
            self.progress_panel.append_log_batch(log_batch)

    def _show_toast(self, title: str, desc: str):
        from ui.components.toast import NotificationToast
        NotificationToast(self, title, desc)

    def _toggle_theme_mode(self):
        if self.app_state.current_theme == "Dark":
            self.app_state.current_theme = "Light"
            ctk.set_appearance_mode("Light")
            self.theme_btn.configure(text=TRANSLATIONS[self.app_state.current_lang]["theme_light"])
        else:
            self.app_state.current_theme = "Dark"
            ctk.set_appearance_mode("Dark")
            self.theme_btn.configure(text=TRANSLATIONS[self.app_state.current_lang]["theme_dark"])
        
        # Redraw standard tk.Canvas elements to reflect theme changes instantly
        if hasattr(self, "progress_panel"):
            self.progress_panel.draw_progress()
            self.progress_panel._redraw_sparkline()
        if hasattr(self, "preview_panel"):
            self.preview_panel.draw_sponsor_overlay()

    def _toggle_language(self, choice: str):
        LANG_MAP = {
            "türkçe": "tr",
            "english": "en",
            "español": "es",
            "tr": "tr",
            "en": "en",
            "es": "es"
        }
        self.app_state.current_lang = LANG_MAP.get(choice.lower(), "en")
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

        # Update compact mode state and button text translations
        self._apply_compact_mode()

    def _toggle_compact_mode(self):
        # Toggle preference
        self.app_state.preferences.compact_mode = not self.app_state.preferences.compact_mode
        # Save preference immediately
        from core.app_state import save_app_preferences
        save_app_preferences(self.app_state.preferences)
        # Apply change visually
        self._apply_compact_mode()

    def _apply_compact_mode(self):
        is_compact = self.app_state.preferences.compact_mode
        lang = self.app_state.current_lang

        if is_compact:
            self.advanced_panel.grid_remove()
            txt = TRANSLATIONS[lang].get("btn_compact_mode_expanded", "⚙️ Advanced")
        else:
            self.advanced_panel.grid(row=2, column=0, padx=4, pady=6, sticky="ew")
            txt = TRANSLATIONS[lang].get("btn_compact_mode_compact", "⚡ Compact")

        if hasattr(self, "btn_compact_mode"):
            self.btn_compact_mode.configure(text=txt)

    def _on_update_found(self, payload):
        # Schedule the UI configuration inside the safe main event loop
        self.after(0, lambda: self._show_update_badge(payload))

    def _show_update_badge(self, payload):
        self.active_update_payload = payload
        lang = self.app_state.current_lang
        
        if payload.action == "downgrade":
            btn_text = f"⚠️ Sürüm Düşür / Downgrade Core (v{payload.latest_version})" if lang == "tr" else f"⚠️ Downgrade Core / Sürüm Düşür (v{payload.latest_version})"
        else:
            btn_text = f"🚀 Motoru Güncelle / Update Core (v{payload.latest_version})" if lang == "tr" else f"🚀 Update Core / Motoru Güncelle (v{payload.latest_version})"
            
        self.btn_update_warning.configure(text=btn_text)
        self.btn_update_warning.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 16), sticky="ew")

    def perform_update(self):
        lang = self.app_state.current_lang
        payload = getattr(self, "active_update_payload", None)
        
        if not payload:
            return
            
        status_text = "Güncelleniyor... Lütfen bekleyin." if lang == "tr" else "Upgrading... Please wait."
        self.btn_update_warning.configure(text=status_text, state="disabled")
        
        import threading
        from core.updater import execute_update
        
        def _run():
            success, msg = execute_update(payload, str(self.scratch_dir))
            self.after(0, lambda: self._on_upgrade_complete(success, msg))
            
        threading.Thread(target=_run, daemon=True, name="self-updater").start()

    def _on_upgrade_complete(self, success: bool, message: str = ""):
        lang = self.app_state.current_lang
        if success:
            success_text = "Güncelleme Tamamlandı! Yeniden Başlatın." if lang == "tr" else "Upgrade Finished! Please Restart."
            fg_color = "#10b981"
        else:
            if "Güvenlik İhlali" in message or "Security Breach" in message:
                success_text = "Güvenlik Engeli: SHA-256 Eşleşmedi!" if lang == "tr" else "Security Block: Hash Mismatch!"
            else:
                success_text = "Güncelleme Başarısız!" if lang == "tr" else "Upgrade Failed!"
            fg_color = "#f43f5e"
            print(f"[Updater] Upgrade failed with message: {message}")
            
        self.btn_update_warning.configure(
            text=success_text,
            state="disabled",
            fg_color=fg_color
        )

    def _on_close(self):
        if self.app_state.is_executor_running:
            if not messagebox.askyesno(TRANSLATIONS[self.app_state.current_lang]["lbl_dialog_close_title"], TRANSLATIONS[self.app_state.current_lang]["lbl_dialog_close_desc"]):
                return
            self._cancel_download()
        
        # Absolute guarantee that no zombie ffmpeg threads survive
        try:
            kill_all_active_subprocesses()
        except Exception:
            pass

        try:
            shutdown_db()
        except Exception:
            pass
            
        try:
            shutil.rmtree(self.scratch_dir, ignore_errors=True)
        except Exception:
            pass

        self.destroy()

```

---
