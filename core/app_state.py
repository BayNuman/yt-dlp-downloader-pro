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

@dataclass
class AppPreferences:
    # Target download directories & settings
    output_dir: str = ""
    current_lang: str = "tr"  # Default language (tr, en, es)
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

    # Backward-compatible Property Proxies for UI and Command Builder compatibility
    @property
    def output_dir(self) -> str:
        return self.preferences.output_dir
    @output_dir.setter
    def output_dir(self, val: str):
        self.preferences.output_dir = val

    @property
    def current_lang(self) -> str:
        return self.preferences.current_lang
    @current_lang.setter
    def current_lang(self, val: str):
        self.preferences.current_lang = val

    @property
    def current_theme(self) -> str:
        return self.preferences.current_theme
    @current_theme.setter
    def current_theme(self, val: str):
        self.preferences.current_theme = val

    @property
    def active_profile(self) -> str:
        return self.preferences.active_profile
    @active_profile.setter
    def active_profile(self, val: str):
        self.preferences.active_profile = val

    @property
    def custom_settings(self) -> Dict:
        return self.preferences.custom_settings
    @custom_settings.setter
    def custom_settings(self, val: Dict):
        self.preferences.custom_settings = val

    @property
    def sponsorblock_enabled(self) -> bool:
        return self.preferences.sponsorblock_enabled
    @sponsorblock_enabled.setter
    def sponsorblock_enabled(self, val: bool):
        self.preferences.sponsorblock_enabled = val

    @property
    def browser_cookies(self) -> str:
        return self.preferences.browser_cookies
    @browser_cookies.setter
    def browser_cookies(self, val: str):
        self.preferences.browser_cookies = val

    @property
    def speed_limit(self) -> Optional[str]:
        return self.preferences.speed_limit
    @speed_limit.setter
    def speed_limit(self, val: Optional[str]):
        self.preferences.speed_limit = val

    @property
    def metadata_flag(self) -> bool:
        return self.preferences.metadata_flag
    @metadata_flag.setter
    def metadata_flag(self, val: bool):
        self.preferences.metadata_flag = val

    @property
    def thumbnail_flag(self) -> bool:
        return self.preferences.thumbnail_flag
    @thumbnail_flag.setter
    def thumbnail_flag(self, val: bool):
        self.preferences.thumbnail_flag = val

    @property
    def subtitle_flag(self) -> bool:
        return self.preferences.subtitle_flag
    @subtitle_flag.setter
    def subtitle_flag(self, val: bool):
        self.preferences.subtitle_flag = val

    @property
    def auto_subtitle_flag(self) -> bool:
        return self.preferences.auto_subtitle_flag
    @auto_subtitle_flag.setter
    def auto_subtitle_flag(self, val: bool):
        self.preferences.auto_subtitle_flag = val

    @property
    def restrict_filenames(self) -> bool:
        return self.preferences.restrict_filenames
    @restrict_filenames.setter
    def restrict_filenames(self, val: bool):
        self.preferences.restrict_filenames = val

    @property
    def keep_video_flag(self) -> bool:
        return self.preferences.keep_video_flag
    @keep_video_flag.setter
    def keep_video_flag(self, val: bool):
        self.preferences.keep_video_flag = val

    @property
    def embed_chapters(self) -> bool:
        return self.preferences.embed_chapters
    @embed_chapters.setter
    def embed_chapters(self, val: bool):
        self.preferences.embed_chapters = val

    @property
    def concurrent_fragments(self) -> str:
        return self.preferences.concurrent_fragments
    @concurrent_fragments.setter
    def concurrent_fragments(self, val: str):
        self.preferences.concurrent_fragments = val

    @property
    def output_template(self) -> str:
        return self.preferences.output_template
    @output_template.setter
    def output_template(self, val: str):
        self.preferences.output_template = val

    @property
    def extra_args(self) -> str:
        return self.preferences.extra_args
    @extra_args.setter
    def extra_args(self, val: str):
        self.preferences.extra_args = val
