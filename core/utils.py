# core/utils.py
"""
yt-dlp Downloader Pro - General Utility Functions
"""
import re

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
