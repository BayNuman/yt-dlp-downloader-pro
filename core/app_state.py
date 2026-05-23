# core/app_state.py
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

@dataclass
class AppState:
    # Target download directories & settings
    output_dir: str = ""
    current_lang: str = "tr"  # Default language (tr, en, es)
    current_theme: str = "Dark"  # Default theme (Dark, Light)
    
    # Active inputs
    url: str = ""
    is_batch_mode: bool = False
    batch_urls: List[str] = field(default_factory=list)
    
    # Selected formats & preset choices
    active_profile: str = "best"  # best, 1080p, 720p, mp3, custom
    custom_settings: Dict = field(default_factory=dict)
    
    # Metadata caching
    current_video_info: Optional[Dict] = None  # Caches active metadata
    
    # Active download queues
    queue_list: List[Dict] = field(default_factory=list)
    
    # Shared settings (SponsorBlock, browser cookies, speed limits)
    sponsorblock_enabled: bool = False
    browser_cookies: str = "Kapali"  # Will map to BROWSER_COOKIE_SOURCES
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
    
    # Diagnostic logs
    terminal_logs: List[str] = field(default_factory=list)
    
    # Threading controls & active executor state
    is_executor_running: bool = False
    current_item_index: int = -1
    cancel_current_flag: bool = False
    
    # Outdated warning state
    saw_outdated_warning: bool = False
