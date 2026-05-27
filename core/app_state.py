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
        self._lock = threading.RLock()
        try:
            load_app_preferences(self.preferences)
        except Exception:
            pass

    _PREFERENCE_FIELDS = {
        "output_dir", "current_lang", "current_theme", "active_profile",
        "custom_settings", "sponsorblock_enabled", "browser_cookies", "speed_limit",
        "metadata_flag", "thumbnail_flag", "subtitle_flag", "auto_subtitle_flag",
        "restrict_filenames", "keep_video_flag", "embed_chapters", "concurrent_fragments",
        "output_template", "extra_args", "folder_org", "compact_mode", "max_workers"
    }

    # Dynamic Delegation Pattern for Property Proxies
    def __getattr__(self, name):
        if name in AppState._PREFERENCE_FIELDS:
            return getattr(self.preferences, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name in AppState._PREFERENCE_FIELDS:
            setattr(self.preferences, name, value)
        else:
            object.__setattr__(self, name, value)
