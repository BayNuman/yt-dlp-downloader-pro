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

