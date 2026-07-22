import asyncio
from typing import Any, Dict, List, Optional
from core.history import (
    add_download_record,
    update_download_status,
    clear_all_downloads,
    delete_download,
    find_completed_download_in_db,
    get_all_downloads,
    save_channel_rule,
    delete_channel_rule,
    get_channel_rule,
    get_all_channel_rules
)
from core.app_state import load_app_preferences, save_app_preferences, AppPreferences

# --- Preferences I/O Wrappers ---
async def async_load_app_preferences(prefs: AppPreferences) -> None:
    """Asynchronously loads app preferences from the configuration file."""
    await asyncio.to_thread(load_app_preferences, prefs)

async def async_save_app_preferences(prefs: AppPreferences) -> None:
    """Asynchronously saves app preferences to the configuration file."""
    await asyncio.to_thread(save_app_preferences, prefs)

# --- SQLite Writes (Non-blocking queue submission in core, but wrapped for async loop friendliness) ---
async def async_add_download_record(
    item_id: str,
    title: str,
    url: str,
    format_desc: str,
    file_path: str,
    status: str,
    file_size: int = 0,
    duration: int = 0,
    thumbnail_path: Optional[str] = None
) -> None:
    await asyncio.to_thread(
        add_download_record,
        item_id,
        title,
        url,
        format_desc,
        file_path,
        status,
        file_size,
        duration,
        thumbnail_path=thumbnail_path
    )

async def async_update_download_status(
    item_id: str,
    status: str,
    file_path: Optional[str] = None,
    file_size: Optional[int] = None,
    duration: Optional[int] = None,
    thumbnail_path: Optional[str] = None
) -> None:
    await asyncio.to_thread(
        update_download_status,
        item_id,
        status,
        file_path=file_path,
        file_size=file_size,
        duration=duration,
        thumbnail_path=thumbnail_path
    )

async def async_clear_all_downloads() -> None:
    await asyncio.to_thread(clear_all_downloads)

async def async_delete_download(item_id: str) -> None:
    await asyncio.to_thread(delete_download, item_id)

async def async_save_channel_rule(channel_id: str, channel_name: str, settings_dict: dict) -> None:
    await asyncio.to_thread(save_channel_rule, channel_id, channel_name, settings_dict)

async def async_delete_channel_rule(channel_id: str) -> None:
    await asyncio.to_thread(delete_channel_rule, channel_id)

# --- SQLite Reads (Blocking file I/O operations, wrapped to prevent event loop starvation) ---
async def async_find_completed_download_in_db(video_id: str, url: str, format_desc: str) -> Optional[Dict[str, Any]]:
    return await asyncio.to_thread(find_completed_download_in_db, video_id, url, format_desc)

async def async_get_all_downloads() -> List[Dict[str, Any]]:
    return await asyncio.to_thread(get_all_downloads)

async def async_get_channel_rule(channel_id: str) -> Optional[Dict[str, Any]]:
    return await asyncio.to_thread(get_channel_rule, channel_id)

async def async_get_all_channel_rules() -> List[Dict[str, Any]]:
    return await asyncio.to_thread(get_all_channel_rules)
