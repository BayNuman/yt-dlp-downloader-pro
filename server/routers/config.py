import os
import shutil
import platform
import asyncio
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
import yt_dlp

from server.security import verify_token
from server.models import AppPreferencesModel, AppPreferencesPatchModel
from server.async_bridge import async_save_app_preferences
from core.profiles import EXPORT_PROFILES
from core.downloader import resolve_ffmpeg_path
from core.presets import load_presets, save_preset, delete_preset

router = APIRouter(
    prefix="/config",
    tags=["config"],
    dependencies=[Depends(verify_token)]
)

# --- Preferences REST Endpoints ---

@router.get("/preferences")
async def get_preferences(request: Request) -> Dict[str, Any]:
    """Retrieves current application preferences."""
    controller = request.app.state.server.controller
    return controller.state.preferences.to_dict()

@router.patch("/preferences")
async def patch_preferences(req: AppPreferencesPatchModel, request: Request) -> Dict[str, Any]:
    """Partially updates preferences and persists changes to settings.json."""
    controller = request.app.state.server.controller
    prefs = controller.state.preferences
    
    update_data = req.dict(exclude_unset=True)
    with controller.state._lock:
        for name, value in update_data.items():
            setattr(prefs, name, value)
            
    # Asynchronously save to settings file
    await async_save_app_preferences(prefs)
    return {"success": True, "preferences": prefs.to_dict()}


# --- Export Profiles REST Endpoints ---

@router.get("/profiles")
async def get_profiles() -> List[Dict[str, Any]]:
    """Retrieves all defined FFmpeg clip export profiles."""
    return [
        {
            "name": name,
            "ext": prof.ext,
            "max_duration": prof.max_duration
        }
        for name, prof in EXPORT_PROFILES.items()
    ]


# --- Presets REST Endpoints ---

@router.get("/presets")
async def get_all_presets() -> Dict[str, Any]:
    """Loads all saved preset configurations."""
    try:
        presets = await asyncio.to_thread(load_presets)
        return presets
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load presets: {str(e)}"
        )

@router.post("/presets/{name}")
async def create_preset(name: str, preset_data: Dict[str, Any]) -> Dict[str, Any]:
    """Saves or replaces a preset config under the specified name."""
    try:
        await asyncio.to_thread(save_preset, name, preset_data)
        return {"success": True, "detail": f"Preset '{name}' saved successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save preset: {str(e)}"
        )

@router.delete("/presets/{name}")
async def remove_preset(name: str) -> Dict[str, Any]:
    """Deletes the specified preset from disk."""
    try:
        await asyncio.to_thread(delete_preset, name)
        return {"success": True, "detail": f"Preset '{name}' deleted."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete preset: {str(e)}"
        )


# --- System Status REST Endpoint ---

@router.get("/system/status")
async def get_system_status(request: Request) -> Dict[str, Any]:
    """Exposes system diagnostic parameters, versions, and remaining disk space."""
    controller = request.app.state.server.controller
    output_dir = controller.state.preferences.output_dir
    
    # Calculate disk usage safely
    disk_total = 0
    disk_free = 0
    if output_dir and os.path.exists(output_dir):
        try:
            total, used, free = shutil.disk_usage(output_dir)
            disk_total = total
            disk_free = free
        except Exception:
            pass
            
    # Resolve ffmpeg executable
    try:
        ffmpeg_bin = await asyncio.to_thread(resolve_ffmpeg_path)
    except Exception:
        ffmpeg_bin = "ffmpeg (error resolving)"
        
    return {
        "app_version": "2.0.0",
        "yt_dlp_version": yt_dlp.version.__version__,
        "ffmpeg_path": ffmpeg_bin,
        "os_platform": platform.system(),
        "os_release": platform.release(),
        "disk_free_bytes": disk_free,
        "disk_total_bytes": disk_total
    }

@router.post("/select-directory")
async def select_directory():
    """Opens a native system folder dialog and returns the selected directory path."""
    import tkinter as tk
    from tkinter import filedialog
    
    def ask_dir():
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        root.attributes("-topmost", True)  # Make folder dialog topmost
        folder = filedialog.askdirectory(parent=root)
        root.destroy()
        return folder

    folder = await asyncio.to_thread(ask_dir)
    return {"directory": folder}
