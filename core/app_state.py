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

    # Dynamic Delegation Pattern for Property Proxies
    def __getattr__(self, name):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError
        if hasattr(self, "preferences"):
            pref = object.__getattribute__(self, "preferences")
            if hasattr(pref, name):
                return getattr(pref, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name != "preferences" and hasattr(self, "preferences"):
            pref = object.__getattribute__(self, "preferences")
            if hasattr(pref, name):
                setattr(pref, name, value)
                return
        object.__setattr__(self, name, value)
