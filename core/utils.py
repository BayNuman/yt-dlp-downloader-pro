# core/utils.py
"""
yt-dlp Downloader Pro - General Utility Functions
"""
import re
import os
from pathlib import Path

def parse_speed_to_mbps(speed_str: str) -> float:
    """
    Parses a speed string (e.g. '15.3MiB/s', '200B/s') into a float representing speed in Mbps.
    """
    if not speed_str:
        return 0.0
    # Parse value and unit (e.g. 15.3MiB/s, 200B/s)
    match = re.search(r"([\d\.]+)\s*([a-zA-Z/]+)", speed_str)
    if not match:
        return 0.0
    val = float(match.group(1))
    unit = match.group(2).lower()
    
    if "g" in unit:
        return val * 1024.0
    elif "m" in unit:
        return val
    elif "k" in unit:
        return val / 1024.0
    elif "b" in unit:
        return val / (1024.0 * 1024.0)
    return val

def clean_empty_directories(path_str: str, base_dir_str: str):
    """
    Recursively deletes empty parent directories up to base_dir_str.
    Does not delete base_dir_str itself.
    """
    try:
        if not path_str or not base_dir_str:
            return
        
        path = Path(path_str).resolve()
        base_dir = Path(base_dir_str).resolve()
        
        # If path is a file, take its parent folder
        if path.is_file():
            folder = path.parent
        else:
            folder = path
            
        # Traverse upwards from folder to base_dir (exclusive of base_dir)
        while folder != base_dir and base_dir in folder.parents:
            # Check if directory exists and is empty
            if folder.exists() and folder.is_dir():
                # Check if empty (no files or folders inside)
                if not any(folder.iterdir()):
                    try:
                        folder.rmdir()
                    except Exception as e:
                        print(f"[Cleanup Hook] Failed to remove folder {folder}: {e}")
                        break # stop if we cannot delete
                else:
                    # Folder is not empty, so we cannot delete it, and parents won't be empty either
                    break
            else:
                break
            # Go up one level
            folder = folder.parent
    except Exception as e:
        print(f"[Cleanup Hook] Error in clean_empty_directories: {e}")

def extract_video_id(url: str) -> str:
    """
    Extracts the 11-character YouTube video ID from a URL.
    """
    if not url:
        return ""
    patterns = [
        r"(?:v=|\/v\/|embed\/|shorts\/|youtu\.be\/|\/embed\/|\/shorts\/)([a-zA-Z0-9_-]{11})",
        r"(?:\/shorts\/|youtu\.be\/|v\/|embed\/)([a-zA-Z0-9_-]{11})"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ""
