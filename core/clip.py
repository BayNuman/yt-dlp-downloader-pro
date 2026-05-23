# core/clip.py
import re
from typing import Tuple, Union, Optional

def parse_time_to_seconds(s: str) -> Optional[float]:
    s = s.strip()
    if not s:
        return None
    # Check format HH:MM:SS or MM:SS
    if ":" in s:
        parts = s.split(":")
        try:
            if len(parts) == 2:
                return int(parts[0]) * 60 + float(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        except ValueError:
            return None
    # Parse pure seconds string
    try:
        return float(s)
    except ValueError:
        return None

def format_seconds_to_mmss(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:05.2f}"
    return f"{m:02d}:{s:05.2f}"

def validate_clip_range(start_str: str, end_str: str, total_duration: float) -> Union[Tuple[float, float], str]:
    start = parse_time_to_seconds(start_str)
    end = parse_time_to_seconds(end_str)
    
    if start is None or end is None:
        return "Geçersiz zaman formatı. MM:SS veya saniye girin."
    if start < 0:
        return "Başlangıç negatif olamaz."
    if start >= end:
        return "Bitiş, başlangıçtan büyük olmalı."
    if total_duration > 0 and end > total_duration:
        end = total_duration  # Silent correction to end of video
    if (end - start) < 0.5:
        return "En az 0.5 saniyelik bir aralık seçin."
        
    return start, end

def decide_clip_strategy(info: dict, start: float, end: float) -> str:
    # Live stream - seek is problematic, must download and trim
    if info.get("is_live"):
        return "full_trim"
    
    # Check for HTTP/HTTPS seekable protocol in formats list
    formats = info.get("formats", [])
    has_seekable = any(
        f.get("protocol") in ("https", "http") or f.get("protocol") is None
        for f in formats
    )
    
    duration = info.get("duration", 0)
    clip_ratio = (end - start) / duration if duration else 1
    
    if has_seekable and clip_ratio < 0.15:
        # Less than 15% requested -> stream seek (Fastest)
        return "stream_seek"
    elif has_seekable and clip_ratio < 0.5:
        # Up to 50% -> hybrid: buffered seek + local c:copy trim
        return "hybrid"
    else:
        # Large part -> full download + local trim
        return "full_trim"
