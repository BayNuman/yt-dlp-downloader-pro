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
"""

from core.env import refresh_path_env
# Refresh path environment variables on startup before importing anything else to pick up runtime updates like Deno

import sys
    import yt_dlp

from core.app_state import AppState
from ui.main_window import MainWindow

from core.logging_setup import setup_logging

def purge_scratch_directory():
    """
    """
    import shutil
    from pathlib import Path
    
            import logging
            
    # Temiz bir başlangıç için klasörü yeniden oluştur

def main() -> None:
    # 0. Initialize central logging system
    
    # 1. Deterministik başlangıç çöp toplama (Garbage Collection)
    
    # 2. Initialize central application state configuration
    
    # 2. Boot up the main graphical window layout orchestrator
    
    # 3. Fire up the Tkinter main event thread loop


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
    """

        import winreg
        
        # 1. Query Registry for User-level Environment PATH

        # 2. Query Registry for System-level (Machine) Environment PATH

        # 3. Add explicit check for Winget Local Packages directory where Deno/Node.js is usually extracted

        # 4. Filter empty/duplicate paths and update the active process environment
        
        # Prepend the current path elements to avoid losing any dynamic paths added at runtime
                

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

@dataclass
class DownloadTask:

    # Profile & resolution configuration

    # Clipping configurations

    # Real-time task execution metrics

    # Dynamic cancellation event for granular thread safety

    # Internal dynamic variables

def get_default_lang() -> str:
    import locale

def load_app_preferences(prefs):
    from core.history import get_app_data_dir
    import json

def save_app_preferences(prefs):
    from core.history import get_app_data_dir
    import json

@dataclass
class AppPreferences:
    # Target download directories & settings

    # Shared settings (SponsorBlock, browser cookies, speed limits)

    # Advanced panel configurations

    # Multi-worker concurrency count

@dataclass
class AppState:

    # Active inputs

    # Metadata caching

    # Strongly typed active download queue

    # Diagnostic logs

    # Threading controls & active executor state

    # Outdated warning state

    def __post_init__(self):
        # Auto-initialize central logging system
        from core.logging_setup import setup_logging


    def __getattr__(self, name):

    def __setattr__(self, name, value):

```

---

## <a name="file-coreclippy"></a> 📄 File: `core/clip.py`
**Responsibility**: Advanced interval operations. Implements LeetCode 56 Greedy Interval Merging algorithm to bundle overlapping clips and reduce net requests.

```python
# core/clip.py
import re
from typing import Tuple, Union, Optional

def parse_time_to_seconds(s: str) -> Optional[float]:
    # Check format HH:MM:SS or MM:SS
    val = None
                val = int(parts[0]) * 60 + float(parts[1])
                val = int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        # Parse pure seconds string
            val = float(s)

def format_seconds_to_mmss(seconds: float) -> str:

def validate_clip_range(start_str: str, end_str: str, total_duration: float) -> Union[Tuple[float, float], str]:
    
        

def decide_clip_strategy(info: dict, start: float, end: float) -> str:
    # Live stream - seek is problematic, must download and trim
    
    # Check for HTTP/HTTPS seekable protocol in formats list
    
    
        # Less than 15% requested -> stream seek (Fastest)
        # Up to 50% -> hybrid: buffered seek + local c:copy trim
        # Large part -> full download + local trim

from dataclasses import dataclass
from typing import List

@dataclass
class MicroClip:

@dataclass
class MacroClip:

def optimize_clip_intervals(clips: List[MicroClip], threshold_sec: float = 30.0) -> List[MacroClip]:
    """
    """

    # Sort clips chronologically by start time
    
    

        
        # If next clip start is within threshold_sec of current macro's end, merge them!
            # Sizable gap: close current macro and start a new one
            

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


def _cleanup_temp_files():





def safe_get(obj, key, default=None):
        val = obj.get(key, default)
        val = getattr(obj, key, default)

def safe_set(obj, key, value):

def sanitize_extra_args(extra_args_str: str) -> list[str]:
    
        
    
    
            
                
        

def effective_video_height(item) -> Optional[int]:
        val = safe_get(item, "video_limit", "1080")
        val = selected
        

def build_command(item, output_dir: str) -> list[str]:
    import tempfile
    import json
    
    
        

    # If pre-fetched metadata exists (Multi-Clip Single-Fetch), inject it to avoid double-fetching network calls
            # Create a temporary file inside our isolated scratch directory to write cached JSON metadata
            
            # Cache the temp path so downloader can clean it up

            







        from core.history import get_app_data_dir


    # Protect against infinite TCP socket hangs on unstable/throttled connections



        # DESIGN NOTE (full_trim): Under "full_trim", we intentionally do NOT inject yt-dlp section downloads.
        # This is an intentional design contract: the whole file is downloaded first, then trimmed in downloader.py
        # post-processing using FFmpeg to guarantee frame accuracy and codec stability.
        
        



def format_cmd_for_log(cmd: list[str]) -> str:

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

    def merge_clips(self, clip_paths: list[str], output_path: str, cleanup: bool = False, register_proc_cb=None, unregister_proc_cb=None) -> bool:

        
                        # Calculate path relative to the working directory (output folder)
                        # Fallback to absolute path on cross-drive scenarios on Windows
                    # Safe quoting for ffmpeg concat demuxer format

            # Convert output path relative to working directory
            

            










    def _cleanup_clips(self, clip_paths: list[str]):

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

        # Sets for O(1) membership queries

    def analyze(self, info_dict: dict) -> str:
        """
        """

        # Gather data safely with defaults to avoid KeyErrors
        
        
        # Safe categories pulling
        
        # Safe tags pulling

        # Consolidate all metadata terms to analyze intersections

        # ----------------- HEURISTIC RULES -----------------
        
        # Rule 1: Aspect Ratio and Duration (Shorts/Reels detection)

        # Rule 2: Official Categorizations

        # Rule 3: Title & Tags Text Intersection Queries


        # Rule 4: Duration Behavior Analysis
        # Over 45 minutes -> highly likely a podcast, tutorial, or background lecture

        # Result selection

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

@dataclass
class UpdatePayload:
    """Strongly-typed data container representing an update check result."""

def verify_hash_against_pypi(version: str, sha256_val: str) -> bool:
    """Queries the official PyPI JSON API for the specific version and verifies if the hash is registered."""

def calculate_sha256(file_path: str) -> str:
    """Computes the SHA-256 checksum of a local file in memory-efficient chunks."""

class UpdateChecker:
    """Schedules background update checks, routing query streams through a two-tiered fallback pipeline."""
    
    def __init__(self, ui_callback):
        """
        """

    def check_in_background(self):
        """Spawns a background daemon thread to perform update queries without locking the GUI thread."""

    def _network_task(self):
        
        # --- TIER 1: Unified Update Broker BFF ---
                
                
                    # Deterministic update/rollback detected!

            # Catch all DNS resolution, timeout, and response parse errors silently
            
        # --- TIER 2: Plan B Official PyPI Fallback ---
                

                # Official upgrade found!


def execute_update(payload: UpdatePayload, scratch_dir: str) -> tuple[bool, str]:
    """
    """
    import sys
    import os
    import subprocess
    import urllib.request
    
        # Standalone portable EXE build doesn't support pip upgrades


    # If we don't have a download URL (Plan B Fallback / PyPI), do standard pip upgrade

    # Tier 1 Custom Update Broker Flow
        # 1. Download target archive
        
            
        # 2. Cryptographic Integrity Verification (Supply Chain Protection)
            
                
            # Verify update source authenticity (local pin or PyPI registration)
                    
        
        # 3. Secure Installation
        
        # Cleanup downloaded archive
            


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

def get_default_presets() -> dict:


def load_presets(force_reload: bool = False) -> dict:
        
        # Write default presets first time

def save_all_presets(presets: dict):

def save_preset(name: str, preset_dict: dict):

def delete_preset(name: str):


```

---

## <a name="file-coreprofilespy"></a> 📄 File: `core/profiles.py`
**Responsibility**: Polymorphic export profile definitions (Shorts, Reels, Discord, WhatsApp) generating appropriate re-encoding ffmpeg parameters.

```python
# core/profiles.py
from typing import List, Optional

class ExportProfile:
    def __init__(self, name: str, ext: str, max_duration: Optional[float] = None):

    def get_ffmpeg_args(self, duration_sec: float) -> List[str]:
        # Default fallback: lossless stream copy

class StandardProfile(ExportProfile):
    def __init__(self, name: str, ext: str):

    def get_ffmpeg_args(self, duration_sec: float) -> List[str]:

class SizeBoundedProfile(ExportProfile):
    def __init__(self, name: str, target_mb: float):

    def get_ffmpeg_args(self, duration_sec: float) -> List[str]:
        # Target with 5% safety margin:
        
        

class MemeGifProfile(ExportProfile):
    def __init__(self, name: str):

    def get_ffmpeg_args(self, duration_sec: float) -> List[str]:
        # Output as silent high-quality loop gif with split-palettegen-paletteuse filter pipeline

class AudiobookProfile(ExportProfile):
    def __init__(self, name: str):

    def get_ffmpeg_args(self, duration_sec: float) -> List[str]:
        # Mono channel, low bitrate voice note optimization

class CenterCropProfile(ExportProfile):
    def __init__(self, name: str, max_duration: Optional[float] = None):

    def get_ffmpeg_args(self, duration_sec: float) -> List[str]:
        # Mathematical 16:9 to 9:16 vertical center crop with horizontal offset calculation


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
    

def get_db_path() -> Path:

def connect_db() -> sqlite3.Connection:
    """Creates a database connection with high-performance concurrent WAL and busy timeouts."""


def get_read_connection() -> sqlite3.Connection:

class DatabaseWriter:
    def __init__(self):

    def _worker(self):
        # Dedicated database worker thread - sequential lock-free writes
                

    def submit(self, fn, *args, **kwargs):
        """Dispatched from concurrent threads — non-blocking, asynchronous queue write"""

    def shutdown(self):
        """Gracefully terminates the background SQLite worker thread after draining all writes"""

# Global Singleton Database Writer Instance

def shutdown_db() -> None:
    """Gracefully terminates the background SQLite worker thread."""

def init_db():
    # Init db is run once synchronously at startup, before thread dispatchers
    
    # Enable WAL mode and check current version
    
    
        """)
        
            # Column might already exist from older manual runs
        """)
        
        """)
        
        

# --- DB Write Worker Callbacks ---

def _do_add_download_record(conn, item_id: str, title: str, url: str, format_desc: str, file_path: str, status: str, file_size: int, duration: int, thumbnail_path: str = None):
    """, (item_id, title, url, format_desc, file_path, status, int(time.time()), file_size, duration, thumbnail_path))

def _do_update_download_status(conn, item_id: str, status: str, file_path: str = None, file_size: int = None, duration: int = None, thumbnail_path: str = None):
        

def _do_clear_all_downloads(conn):
    # Physical file cleanup to prevent orphaned WebP cache files

def _do_delete_download(conn, item_id: str):
    # Physical file cleanup to prevent orphaned WebP cache files

# --- Exposed Non-Blocking API ---

def add_download_record(item_id: str, title: str, url: str, format_desc: str, file_path: str, status: str, file_size: int = 0, duration: int = 0, thumbnail_path: str = None):

def update_download_status(item_id: str, status: str, file_path: str = None, file_size: int = None, duration: int = None, thumbnail_path: str = None):

def clear_all_downloads():

def delete_download(item_id: str):

# --- Direct Read API (Safe concurrently with WAL mode) ---

def find_completed_download_in_db(video_id: str, url: str, format_desc: str) -> Dict[str, Any]:
    """
    """

def get_all_downloads() -> List[Dict[str, Any]]:


# ========== Channel Auto-Rules (Schemaless JSON Patch Storage) ==========

import json

def _do_save_channel_rule(conn, channel_id: str, channel_name: str, settings_json: str):
    """, (channel_id, channel_name, settings_json, channel_id, now, now))

def _do_delete_channel_rule(conn, channel_id: str):

def save_channel_rule(channel_id: str, channel_name: str, settings_dict: dict):
    """Non-blocking async write — enqueues channel rule save to DB writer thread."""

def delete_channel_rule(channel_id: str):
    """Non-blocking async write — enqueues channel rule deletion to DB writer thread."""

def get_channel_rule(channel_id: str) -> dict:
    """Direct WAL-safe read — returns {channel_id, channel_name, settings_dict} or None."""

def get_all_channel_rules() -> List[Dict[str, Any]]:
    """Direct WAL-safe read — returns all channel rules sorted by most recently updated."""

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

# Windows Sleep prevention constants

def prevent_sleep():

def allow_sleep():

def get_subprocess_encoding() -> str:
    import locale

def safe_put_ui(ui_queue, item):
        # Bloklanmaya veya timeout'a kesinlikle izin yok
        # Load Shedding: UI yetişemiyorsa paketi düşür (drop).
        # Progress stat'ları veya terminal logları anlıktır, bir sonraki tick'te yenisi gelir.
        # Worker thread asla UI'ı beklememeli.

# Thread-safe subprocess tracking to prevent Zombie Processes

def register_active_subprocess(proc):

def unregister_active_subprocess(proc):

def resume_subprocess(proc):
            import ctypes
            import signal

def kill_all_active_subprocesses():
                # Safe resume first to ensure it processes termination signals on POSIX/Windows

from core.waveform import enqueue_waveform_generation
from core.utils import clean_empty_directories, extract_video_id

def _on_waveform_done(task_id, png_path, ui_queue):

# Core state & DB models
from core.app_state import AppState, DownloadTask, TaskStatus
from core.command_builder import build_command, format_cmd_for_log, YOUTUBE_FALLBACK_EXTRACTOR_ARGS
from core.history import add_download_record, update_download_status
from core.clip import parse_time_to_seconds

def resolve_ffmpeg_path() -> str:
    """Finds the ffmpeg binary, checking bundled paths or standard locations."""
    # 1. Check PyInstaller temp directory (if bundled inside the EXE)

    # 2. Check directly next to the running executable (for installed Windows setups)

    # 3. Check local bin directory (for development)

    # 4. Fallback to system PATH

def append_options_before_urls(cmd: list[str], urls: list[str], options: list[str]) -> list[str]:

def run_command_stream(cmd: list[str], task: DownloadTask, state: AppState, ui_queue, cancel_event) -> CommandResult:




            # Prefix UI logs with task title for concurrent visibility










def wait_process_with_timeout(proc, timeout=120) -> int:

# clean_empty_directories is now imported from core.utils

def _handle_cancel(task, lang, ui_queue, base_dir=None):

def _set_downloading_status(task, lang, ui_queue):

def _log_start(task, cmd, ui_queue):

def _cleanup_temp_json(task):

def _apply_clip_profile(task, ffmpeg_bin: str, input_path: Path, output_path: Path, 
    """
    """

        # Smart Transcoding: Re-encode video+audio if Precise Cut is enabled





def _process_macro_clips(task, output_file, lang, ui_queue, cancel_event) -> str:
    from core.profiles import EXPORT_PROFILES










        # Homogeneity Check: Verify all clips have the exact same export profile

            from core.merger import LosslessMerger
            


            
                
            


def _process_single_clip(task, output_file, lang, ui_queue, cancel_event) -> str:
    from core.profiles import EXPORT_PROFILES






def resolve_actual_file_path(output_file: str, url: str) -> str:
        
    # If file doesn't exist directly (e.g., due to Windows CP1254 character set conversions or unicode replacement slashes like ⧸),
    # let's find a file in the same directory that has the exact video ID in its name.
    # To prevent collisions in concurrent downloads (e.g. video and audio of the same ID), we normalize names for comparison.
            
        # Extract video ID from URL
            
        # Helper to normalize string names (keep alphanumeric only)
        
        # 1. First Pass: Exact extension match + normalized stem match
                        
        # 2. Second Pass: Allow different media extension + normalized stem match (e.g. merged to .mkv instead of .mp4)
                        
        # 3. Third Pass: Legacy Fallback in case name was severely truncated
                    
        

def _set_completed_status(task, output_file, lang, ui_queue):
    
        # Enqueue waveform generation in a single-threaded queue to prevent CPU boğulma
        def cb(png):
        

def _set_failed_status(task, code, lang, ui_queue, base_dir=None):

def _handle_exception(task, e, lang, ui_queue, base_dir=None):

def download_single_task(task: DownloadTask, state: AppState, ui_queue, cancel_event) -> None:






            
            # Resolve actual physical path (fixes Windows double-spaces and Unicode slashes ⧸ cp1254 mismatches)
            




def run_queue_executor(state: AppState, ui_queue, cancel_event) -> None:
    """Processes pending items in parallel utilizing ThreadPoolExecutor based on max_workers."""
    
    # Query pending tasks
    




def toggle_pause_task(task):
    """
    """
    
    # Update status code and status text
        

```

---

## <a name="file-uithemepy"></a> 📄 File: `ui/theme.py`
**Responsibility**: Central theme configuration, palette constants (glassmorphic dark/light HSL palettes), and full localization dictionary (EN, TR, ES).

```python
# ui/theme.py
import customtkinter as ctk

# Premium Glassmorphic Theme Palette Colors (Light, Dark)

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


class BaseToast(ctk.CTkToplevel):
    """Base class for all toast notifications.
    """
    def __init__(self, master, border_color=THEME_ACCENT_BLUE, duration_ms: int = 5000, **kwargs):


        # Hide default OS window borders & decorations
        # Keep on top of all windows

        # Frosted glass card border container

        # Build the specific body content (subclass hook)

        # Geo Positioning & Fade Animation

        # Fade-in and bootstrap lifecycle

    def _build_body(self):
        """Override in subclasses to build the toast's content inside self.frame."""

    def _build_header(self, title: str):
        """Shared header row with title and close button."""



    def _position_toast(self):


        # Margins to protect Taskbar overlaps



    def _fade_in(self):

    def _fade_out(self):



class ActionableToast(BaseToast):
    def __init__(self, master, title: str, file_path: str, duration_ms: int = 7000, **kwargs):

    def _build_body(self):
        # Header Row: Title & Close Button

        # Filename Row

        # Bottom Action Bar (3 column grid)




    def _action_play(self):

    def _action_show_folder(self):
                # Launch Windows Explorer and highlight the file

    def _action_copy_path(self):


class NotificationToast(BaseToast):
    def __init__(self, master, title: str, desc: str, duration_ms: int = 5000, color=THEME_ACCENT_BLUE, **kwargs):

    def _build_body(self):


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
        

    def _build_ui(self):
        
        # Header Row: Label & Paste Button & Switch




        # URL Inputs Frame

        # Single-line URL Input

        # Multi-line URL Input (hidden by default)

        # Output Folder Section


        # Output Entry


        # Setup Drag and Drop

    def _setup_dnd(self):
        # Feature 3.5: Drag and Drop URL Support using TkinterDnD (if available)
            from tkinterdnd2 import DND_TEXT

    def _on_url_drop(self, event):
        # Clean brackets if dropped from some browsers
        

    def _paste_from_clipboard(self):

    def _toggle_batch_mode(self):

    def _on_url_keyrelease(self, event):

    def _on_textbox_change(self):

    def _on_output_dir_keyrelease(self, event):

    def _pick_output_dir(self):

    def set_url(self, val: str):

    def refresh_translations(self):

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
from core.app_state import AppState
from core.clip import format_seconds_to_mmss, validate_clip_range, parse_time_to_seconds
from core.profiles import EXPORT_PROFILES
from core.suggester import SmartFormatSuggester

from ui.components.clip_row import ClipRow


class PreviewPanel(ctk.CTkFrame):
    def __init__(self, parent, state: AppState, on_chapter_click_callback, on_create_channel_rule_callback=None, **kwargs):
        
        
        # Clip State Variables
        

    def _build_ui(self):

        # Loading visual overlay

        # Thumbnail display label

        # Metadata Details Frame




        # Size Estimate Label

        # Heuristic Suggestion Banner Frame (Row 4)




        # Channel Auto-Rule Banner Frame (Row 5)


        # Chapters Section Frame (Scrollable horizontal chapter bar)

        # Direct-in-Preview Clipping Frame (Relocated from advanced tab view)

        # Toggle checkboxes sub-frame (Row 0)


        # Added "Merge Clips into Single File" Checkbox

        # Scrollable container for Multi-Clip rows (Row 1)

        # Button container for clipping operations (Row 2)




    def update_channel_rule_button_text(self):
        from core.history import get_channel_rule
                

    def _on_channel_rule_clicked(self):

    def _on_clip_toggled(self):

    def _bg_fetch_sponsor_segments(self, video_id):
        import threading
        from core.services import fetch_sponsor_segments
        
        
        def run():
                

    def _on_sponsor_segments_loaded(self, segments, video_id):

    def clean_sponsors(self):
            
            
        # Inverted Sponsor Block Interval Merging with edge cases
        
        # Invert merged blocks to find safe clips in [0, duration]
        
        # Fallback: if all segments are sponsored (safe_clips empty), provide full video
            
        # Clear current clip rows and enable clipping
        
        
        # Populate safe clips

    def add_clip_row(self, start_val, end_val, profile="Default (No Profile)"):
            

    def add_clip_row_default(self):

    def _remove_clip_row(self, row):
        
        # Re-index remaining rows

    def get_multi_clips(self) -> list[dict]:

    def get_clip_settings(self) -> dict:

    def apply_clip_settings(self, d: dict):

    def _apply_suggestion(self):
        
        # Enable clipping
        
        # Ensure at least one row exists
            
        # Apply suggested profile to all rows
            
        # Hide the banner after successful application

    def show_loading(self):

    def hide(self):

    def show_metadata(self, meta: dict, thumbnail_img: ImageTk.PhotoImage = None):

        # Channel rule tracking

        # Reset and trigger SponsorBlock fetching for YouTube videos


        # Set title, uploader, duration
        

        # Clear existing clip rows

        # Auto-reset clipping variables to unchecked

        # Show Size Estimate

        # Render Chapters (Feature 3.4)
            
                

        # Heuristic Suggester Integration
        
            

    def show_error(self):

    def refresh_translations(self):
        
        # Localize relocated clipping labels
        
        
        # Refresh all active rows


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
from core.app_state import AppState, TaskStatus
from core.history import get_all_downloads, clear_all_downloads, delete_download

class QueuePanel(ctk.CTkFrame):
    def __init__(self, parent, state: AppState, on_remove_item_callback, on_redownload_callback, on_cancel_task_callback=None, **kwargs):

        # Dynamic trackers to allow high-performance in-memory progress updates
        # Smart diffing: track current card composition to avoid unnecessary rebuilds
        
        # Asynchronous thumbnail caching and worker pool to prevent scroll jank!
        from concurrent.futures import ThreadPoolExecutor
        

    def destroy(self):

    def _async_load_thumbnail(self, thumb_path: str, label_widget):
            
        def load_thread():
                from PIL import Image


                    # Support Pillow versions with Resampling or legacy ANTIALIAS fallback
                

    def _set_loaded_image(self, thumb_path: str, pil_img, label_widget, size=(80, 45)):
            # Create CTkImage inside main thread to be fully thread-safe

    def _build_ui(self):

        # Segmented Control Tab Switcher

        # Scrollable Frame for listing items

        # Clear History button (only shown on History tab)
        # Hidden by default


    def _on_tab_changed(self, choice):
        # Determine tab kind based on deterministic language-agnostic index
            
            

    def _clear_history_db(self):

    def update_task_progress(self, task_id: str, percent: float, speed: str, eta: str, size: str):
        """High-performance direct in-memory widget text configuration."""

            # Update dot color to active indigo dynamically

    def _get_translated_status(self, item, lang: str) -> str:
        """Return localized status string using lbl_task_ keys from TRANSLATIONS."""

    def update_list(self):

            # Smart diffing: compute current card IDs and status codes to avoid unnecessary rebuilds
                # Composition unchanged — only update text content of existing cards

            # Composition changed — full rebuild required

            # RENDER ACTIVE QUEUE


                # Dot indicator color


                # Text Title

                # Format preset label badge

                # Status label (using translations)


                # Remove or Cancel Button based on active downloading state


            # History tab — always reset diffing state

            # RENDER PERSISTENT HISTORY FROM SQLITE


                # Status Dot Indicator


                # Thumbnail Column 1 (Async Cache Loaded)
                

                # Text Title on Column 2

                # Format details on Column 3

                # Date of download on Column 4

                # 1. Premium "Re-download" Button on Column 5

                # 2. Premium "Open Folder" Button (only active if file path exists) on Column 6
                

    @staticmethod
    def _dot_color_for_status(status_code: TaskStatus) -> str:
        """Map TaskStatus enum to dot indicator color."""

    def _open_native_folder(self, file_path_str: str):
        # Bug Fix 3: Cross-platform native folder opening (instead of os.startfile)
        
            

    def refresh_translations(self):
        
        # Re-build Segmented button values to update translations
        
        
            
        

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
from core.app_state import AppState
from core.presets import load_presets, save_preset, delete_preset
from core.clip import validate_clip_range, format_seconds_to_mmss

class AdvancedPanel(ctk.CTkFrame):
    def __init__(self, parent, state: AppState, on_preset_load_callback=None, **kwargs):
        
        # User explicit setting tracking
        

    def _setup_change_traces(self):

    def _on_var_changed(self, *args):

    def reset_user_explicit(self):

    def _build_ui(self):

        # Tabview Integration


        # ==================== TAB 1: RESOLUTION & CODECS ====================


        

        

        


        

        

        



        # ==================== TAB 2: LIMITS & COOKIES ====================


        

        

        

        


        
        
        

        

        

        # Max Concurrent Downloads Option Menu (1, 2, 3, 4, 5 parallel tasks)
        

        # ==================== TAB 3: FLAGS & CHECKBOXES ====================

        


        
        

        # Smart Folder Organization UI
        
        

        


        
        
        
        
        

        # ==================== TAB 4: SCHEDULER & ZAMANLAYICI ====================
        

        # 1. Schedule Enabled switch

        # 2. Schedule Time Label & Input
        

        # Description Label



        # ==================== PRESETS DRAWER (FEATURE 3.3) ====================



        # Save Preset Button

        # Delete Preset Button

    def _update_folder_org_dropdown(self):

    def get_folder_org_logical(self) -> str:
        # Find choice in TRANSLATIONS across all lang codes to map logically

    def _on_folder_org_menu_changed(self, choice):

    def _on_mode_changed(self, choice):
            
            

    def _on_video_profile_changed(self, choice):

    def _on_max_workers_changed(self, choice):

    def _on_schedule_changed(self):

    def _pick_cookies_file(self):

    # ================= PRESET IMPLEMENTATIONS (FEATURE 3.3) =================
    def _load_presets_dropdown(self):

    def _load_selected_preset(self, name):
        
            
            # Apply mode

            # Audio settings

            # Video settings

            # Add-ons
            

            # Smart Folder


    def _prompt_save_preset(self):

    def _delete_selected_preset(self):

    # Pull UI state values directly into dict
    def get_settings_dict(self) -> dict:

    def apply_settings_dict(self, d: dict):
            

            # Smart Folder Restore

    def refresh_translations(self):
        
        






        # Translate Smart Folder UI

```

---

## <a name="file-uipanelsprogress_panelpy"></a> 📄 File: `ui/panels/progress_panel.py`
**Responsibility**: Renders progress bars, speed/ETA/size widgets, terminal logs frame, and execution controllers.

```python
# ui/panels/progress_panel.py
import tkinter as tk
import customtkinter as ctk
from ui.theme import (
from core.app_state import AppState, TaskStatus
from core.utils import parse_speed_to_mbps

class ProgressPanel(ctk.CTkFrame):
    def __init__(self, parent, state: AppState, on_start_callback, on_cancel_callback, on_open_folder_callback, **kwargs):
        
        # 60-point circular buffer + EMA Low-pass filter for visual trend smoothness
        

    def _build_ui(self):

        # Button Grid Frame

        # 1. Start Button (Huge primary action)

        # 2. Cancel Button (Secondary destructive)

        # 3. Clean Outline actions (neutral buttons)



        # ProgressBar Container



        # Status text row



        # Active File Display

        # Metrics Dashboard Grid


        # Live Speed Sparkline Graph (Row 5 - created once with O(1)coords updates)
        
        # Grid lines (draw reference lines once)

        # Graph lines and fill (created once)
        
        # Bind canvas resize to redraw

        # Terminal / System logs toggles (Row 6)

        # Scrollable Logs Text Box (Row 7)

    def _build_dashboard_stat(self, col: int, label_text: str, value_text: str, attr_suffix: str):




    def _toggle_logs_section(self):

    def _clear_logs_textbox(self):

    def append_log(self, text: str):

    def append_log_batch(self, lines: list[str]):

    def draw_progress(self):
        
        
        
        
        # Resolve accent indigo / override color
            
        # Background pill track
        
            val = max(0.0, min(1.0, self.current_progress_value))
            # High-tech segment rendering
            
            # Diverse premium colors for visual segment differentiation
            
                val = max(0.0, min(1.0, self.segment_progress_values[i]))
                
                # Draw hollow background for the segment if empty
                    
                    # Round edges for start and end segments
                        

    def set_progress(self, percent: float):

    def set_segmented_progress(self, segments: list[float]):

    def show_completion_animation(self, success=True):
        

    def update_global_progress(self, queue_list: list):
            
        
        # Calculate unified stats concurrently
            # Collect active stats to show combined values
                    
        
        # Dynamic check if concurrent fragments is active

        # Set aggregated metrics
        

    def update_status(self, dot: str, color: str, message: str):

    def set_stats(self, speed: str, eta: str, size: str):

    def set_running_state(self, running: bool):

    def push_speed(self, speed_str: str):
        # EMA Low-pass filter (α = 0.2, 1-α = 0.8) to keep transitions smooth
        

    def reset_sparkline(self):

    def _redraw_sparkline(self):
        """O(1) coordinate update on single canvas elements — completely leaks-free."""
            
        
        
        # Position reference grid lines
            
        # Re-align circular buffer sequentially from write index
        
            

    def refresh_translations(self):
        
        

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
from ui.panels.url_panel import UrlPanel
from ui.panels.preview_panel import PreviewPanel
from ui.panels.advanced_panel import AdvancedPanel
from ui.panels.queue_panel import QueuePanel
from ui.panels.progress_panel import ProgressPanel

class MainWindow(ctk.CTk):
    def __init__(self, state: AppState):
        
        # Setup paths
        
        # Init SQLite History database

        # Premium Glassmorphic Configuration
        
        # Load and set the high-fidelity window icon dynamically at runtime
            
                from PIL import ImageTk
        
 
        # Setup layout configurations
 
        # Main Container Frame (instead of scrollable frame)
 
        # Side-by-side Columns


        
        # Start PyPI update checker silently in background
        from core.updater import UpdateChecker

        # Start the async UI metric queue draining loop

        # Check and prompt to install JS runtime Deno dynamically after a 2-second UI load buffer

    def _check_and_prompt_deno(self) -> None:

        def bg_check():
            import shutil
            


    def _show_deno_prompt(self) -> None:
        import shutil
        from core.env import refresh_path_env
        
            def installer_thread():
                    import subprocess
                    
                    # Execute Winget install
                    
                    # Refresh PATH
                    
                    

    def _build_header_card(self):
        
        # Header frosted glass card




        # Theme & Language Panel (Right Aligned)




        # Hidden update warning button

    def _build_panels(self):
        # 1. URL Panel (Inputs)

        # 2. Preview Panel (Metadata Viewer)

        # 3. Advanced Panel (Gelişmiş Ayarlar)

        # 4. Queue Panel (Kuyruk listesi & Geçmiş)

        # 5. Progress Dashboard Panel (İndirme İlerleme Paneli)

        # Bind close handler

        # Initialize context-aware cross-platform keyboard shortcuts

        # Apply initial compact mode layout state

    def _setup_shortcuts(self):
        import sys
        from core.app_state import TaskStatus
        
        # 1. Paste & Fetch: Ctrl+V or Cmd+V
        # 2. Start Download: Ctrl+Enter or Cmd+Return
        # 3. Pause/Resume active download task: Space
        # 4. Cancel active queue download: Escape

    def _handle_shortcut_paste(self, event):
        # If user is in an entry or text field, bypass global hook

    def _handle_shortcut_start_download(self, event):

    def _handle_shortcut_space(self, event):
        from core.app_state import TaskStatus
            
        # Space pauses/resumes active download
            from core.downloader import toggle_pause_task

    def _handle_shortcut_escape(self, event):

    # ================== METADATA FETCH IMPLEMENTATIONS ==================
    def _trigger_metadata_fetch(self) -> None:



        
        # Reset the manual override track on new preview

        # Call async metadata fetch (controller handles background thread execution)

    def _on_create_channel_rule(self, channel_id: str, channel_name: str):
        # Keep clean patch: remove output_dir and transient fields
                
        from core.history import save_channel_rule
        

    def _run_metadata_fetch(self, url: str) -> None:

        def on_success(metadata):


        def on_error(err_str):

        from core.history import get_app_data_dir

    def _on_chapter_clicked(self, start_seconds: float, end_seconds: float, chapter_title: str):
        # Feature 3.4 Chapters auto-clipping selection integration directly inside PreviewPanel

    def _on_preset_applied(self):
        # Refresh current profile preview hint

    # extract_video_id is unused in MainWindow and now imported from core.utils where needed

    def _add_to_queue(self) -> None:
        # Synchronize app_state.url with the UI before queueing to avoid empty/stale values



        # 1. Check for duplicates using Controller

        # 2. Merge clipping parameters directly from PreviewPanel if not in batch mode

        # 3. Prepare multi-clip selections

        # Ensure current thumbnail path is passed to task config

        # 4. Delegate task creation and state append to Controller
        
            
            # Post updates to progress panel if automated rules were applied


    def _remove_from_queue(self, idx: int):
                # Don't delete active downloading item

    def _cancel_single_task(self, task_id: str):
                                    import ctypes
                                    import signal

    def _redownload_historic_item(self, url: str, format_desc: str):
        # Feature 3.2: Re-download callback
        # Toggle mode based on history format description via Controller
        
        # Trigger queue panel tab view switch back to Active Queue
        
        # Auto-trigger preview metadata fetch

    # ================== RUN EXECUTION ACTIONS ==================
    def _start_download(self) -> None:

        # Synchronize app_state.url with the UI before starting to avoid empty/stale values

        # Auto queue URL input if queue list empty

        
        # Check if local schedule is active
            # Spawn queue background execution worker thread

    def _run_scheduler_wait_loop(self, target_time_str: str) -> None:

        
        # Windows sleep prevention during countdown
        from core.downloader import prevent_sleep, allow_sleep
        
                
                
                

    def _cancel_download(self):

    def _open_output_dir(self):
        # Bug Fix 3: Cross-platform output directory opening (Windows, macOS, Linux)
        

    # ================== METRIC DRAINING & LIFECYCLE ==================
    # ================== METRIC DRAINING & LIFECYCLE ==================
    def _drain_ui_queue(self) -> None:
            import logging

    def _drain_ui_queue_impl(self) -> None:

                
                # Find and update task model

                # Update the task progress dynamically in the card list without redrawing


                from ui.components.toast import ActionableToast
                
                
                

        # Coalesced UI updates — called at most once per drain cycle



    def _show_toast(self, title: str, desc: str):
        from ui.components.toast import NotificationToast

    def _toggle_theme_mode(self):
        
        # Redraw standard tk.Canvas elements to reflect theme changes instantly

    def _toggle_language(self, choice: str):
        
        # Update Header Card labels

        # Refresh all sub-panels' translations dynamically

        # Update compact mode state and button text translations

    def _toggle_compact_mode(self):
        # Toggle preference
        # Save preference immediately
        from core.app_state import save_app_preferences
        # Apply change visually

    def _apply_compact_mode(self):



    def _on_update_found(self, payload):
        # Schedule the UI configuration inside the safe main event loop

    def _show_update_badge(self, payload):
        
            

    def perform_update(self):
        
            
        
        import threading
        from core.updater import execute_update
        
        def _run():
            

    def _on_upgrade_complete(self, success: bool, message: str = ""):
            

    def _on_close(self):
        
        # Absolute guarantee that no zombie ffmpeg threads survive

            


```

---