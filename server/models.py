from pydantic import BaseModel
from typing import Optional, Dict, List

class AppPreferencesModel(BaseModel):
    output_dir: str
    current_lang: str
    current_theme: str
    active_profile: str
    mode: str
    custom_settings: Dict
    spotify_client_id: str
    spotify_client_secret: str
    sponsorblock_enabled: bool
    browser_cookies: str
    speed_limit: Optional[str]
    metadata_flag: bool
    thumbnail_flag: bool
    subtitle_flag: bool
    auto_subtitle_flag: bool
    restrict_filenames: bool
    keep_video_flag: bool
    embed_chapters: bool
    concurrent_fragments: str
    output_template: str
    extra_args: str
    folder_org: str
    compact_mode: bool
    max_workers: int

class AppPreferencesPatchModel(BaseModel):
    output_dir: Optional[str] = None
    current_lang: Optional[str] = None
    current_theme: Optional[str] = None
    active_profile: Optional[str] = None
    mode: Optional[str] = None
    custom_settings: Optional[Dict] = None
    spotify_client_id: Optional[str] = None
    spotify_client_secret: Optional[str] = None
    sponsorblock_enabled: Optional[bool] = None
    browser_cookies: Optional[str] = None
    speed_limit: Optional[str] = None
    metadata_flag: Optional[bool] = None
    thumbnail_flag: Optional[bool] = None
    subtitle_flag: Optional[bool] = None
    auto_subtitle_flag: Optional[bool] = None
    restrict_filenames: Optional[bool] = None
    keep_video_flag: Optional[bool] = None
    embed_chapters: Optional[bool] = None
    concurrent_fragments: Optional[str] = None
    output_template: Optional[str] = None
    extra_args: Optional[str] = None
    folder_org: Optional[str] = None
    compact_mode: Optional[bool] = None
    max_workers: Optional[int] = None

class SpotifyTracksRequest(BaseModel):
    url: str

class MetadataRequest(BaseModel):
    url: str
    cookies_file: Optional[str] = ""
    browser_cookies: Optional[str] = "disabled"

class ClipRange(BaseModel):
    start: float
    end: float
    profile: Optional[str] = "Default (No Profile)"
    output_name: Optional[str] = ""
    clip_precise: Optional[bool] = False

class AddTaskRequest(BaseModel):
    url: str
    profile: Optional[str] = "best"
    clip_start: Optional[str] = "00:00"
    clip_end: Optional[str] = "00:00"
    clips: Optional[List[ClipRange]] = None
    preset_name: Optional[str] = None
    settings: Optional[Dict] = None

class DownloadTaskResponse(BaseModel):
    task_id: str
    url: str
    title: str
    duration: str
    preset: str
    status: str
    status_code: str
    mode: str
    video_profile: str
    audio_quality: str
    clip_enabled: bool
    clip_start: str
    clip_end: str
    percent: float
    speed: str
    eta: str
    size: str
    file_path: str
