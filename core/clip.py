# core/clip.py
import re
from typing import Tuple, Union, Optional

def parse_time_to_seconds(s: str) -> Optional[float]:
    s = s.strip()
    if not s:
        return None
    is_negative = False
    if s.startswith("-"):
        is_negative = True
        s = s[1:].strip()
    # Check format HH:MM:SS or MM:SS
    val = None
    if ":" in s:
        parts = s.split(":")
        try:
            if len(parts) == 2:
                val = int(parts[0]) * 60 + float(parts[1])
            elif len(parts) == 3:
                val = int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        except ValueError:
            return None
    else:
        # Parse pure seconds string
        try:
            val = float(s)
        except ValueError:
            return None
    if val is not None:
        return -val if is_negative else val
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
        return "err_clip_format"
    if start < 0:
        return "err_clip_negative"
    if start >= end:
        return "err_clip_order"
    if total_duration > 0 and end > total_duration:
        end = total_duration  # Silent correction to end of video
    if (end - start) < 0.5:
        return "err_clip_min"
        
    return start, end

def decide_clip_strategy(info: dict, start: float, end: float) -> str:
    # Live stream - seek is problematic, must download and trim
    if info.get("is_live"):
        return "full_trim"
    
    # Check for HTTP/HTTPS seekable protocol in formats list
    formats = info.get("formats", [])
    has_seekable = any(
        f.get("protocol") in ("https", "http") or (f.get("url") and f.get("url").startswith(("http://", "https://")))
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

from dataclasses import dataclass
from typing import List

@dataclass
class MicroClip:
    id: str
    start: float  # in seconds
    end: float
    export_profile: str
    output_name: str

@dataclass
class MacroClip:
    start: float
    end: float
    micro_clips: List[MicroClip]

def optimize_clip_intervals(clips: List[MicroClip], threshold_sec: float = 30.0) -> List[MacroClip]:
    """
    Greedy Interval Merging Algorithm (LeetCode 56) to combine overlapping or near
    clips to prevent redundant network I/O.
    """
    if not clips:
        return []

    # Sort clips chronologically by start time
    sorted_clips = sorted(clips, key=lambda c: c.start)
    
    macro_clips = []
    first_clip = sorted_clips[0]
    
    current_macro = MacroClip(
        start=first_clip.start,
        end=first_clip.end,
        micro_clips=[first_clip]
    )

    for i in range(1, len(sorted_clips)):
        next_clip = sorted_clips[i]
        
        # If next clip start is within threshold_sec of current macro's end, merge them!
        if next_clip.start <= current_macro.end + threshold_sec:
            current_macro.end = max(current_macro.end, next_clip.end)
            current_macro.micro_clips.append(next_clip)
        else:
            # Sizable gap: close current macro and start a new one
            macro_clips.append(current_macro)
            current_macro = MacroClip(
                start=next_clip.start,
                end=next_clip.end,
                micro_clips=[next_clip]
            )
            
    macro_clips.append(current_macro)
    return macro_clips
