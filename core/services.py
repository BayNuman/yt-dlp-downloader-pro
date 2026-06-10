# core/services.py
import os
import sys
import json
import hashlib
import urllib.request
from pathlib import Path
import yt_dlp
from PIL import Image

def fetch_video_metadata(url: str, cookies_file: str, browser_cookies: str, scratch_dir: Path, app_data_dir: Path) -> dict:
    """
    Extracts full metadata from a video URL using yt-dlp, and downloads/compresses its thumbnail.
    This contains pure business logic and has no dependency on Tkinter or other UI modules.
    """

    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
    }

    if 'list=' in url:
        ydl_opts['extract_flat'] = 'in_playlist'
    
    if cookies_file:
        ydl_opts['cookiefile'] = cookies_file
    elif browser_cookies and browser_cookies not in ("kapali", "disabled", "off", "closed", "none"):
        ydl_opts['cookiesfrombrowser'] = (browser_cookies,)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    if not info:
        raise ValueError("No info extracted")

    title = info.get("title", "Unknown Title")
    uploader = info.get("uploader", info.get("channel", "Unknown Channel"))
    duration_sec = info.get("duration", 0.0)

    thumbnail_url = info.get("thumbnail")
    compressed_thumb_path = None

    if thumbnail_url:
        try:
            url_hash = hashlib.md5(thumbnail_url.encode()).hexdigest()
            thumbs_dir = app_data_dir / "thumbnails"
            thumbs_dir.mkdir(parents=True, exist_ok=True)
            compressed_thumb_path = thumbs_dir / f"thumb_{url_hash}.webp"
            
            temp_raw_path = scratch_dir / f"temp_{url_hash}.jpg"
            
            req = urllib.request.Request(thumbnail_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                with open(temp_raw_path, 'wb') as out_file:
                    out_file.write(response.read())

            with Image.open(temp_raw_path) as pil_img:
                resized_webp = pil_img.resize((320, 180), Image.Resampling.LANCZOS)
                resized_webp.save(compressed_thumb_path, "webp", quality=75)
            
            try:
                os.remove(temp_raw_path)
            except Exception:
                pass
        except Exception as e:
            print(f"[Services] Thumbnail download/transcode failed: {e}")
            compressed_thumb_path = None

    ch_id = info.get("channel_id") or info.get("uploader_id")
    ch_name = info.get("channel") or info.get("uploader")
    if ch_id:
        info["channel_id"] = ch_id
    if ch_name:
        info["channel_name"] = ch_name

    return {
        "url": url,
        "title": title,
        "uploader": uploader,
        "duration": duration_sec,
        "thumbnail_path": str(compressed_thumb_path) if compressed_thumb_path else None,
        "chapters": info.get("chapters", []),
        "filesize": info.get("filesize"),
        "filesize_approx": info.get("filesize_approx"),
        "channel_id": ch_id,
        "channel_name": ch_name,
        "raw_info": info
    }

def fetch_sponsor_segments(video_id: str) -> list:
    """
    Fetches SponsorBlock segments for a given YouTube video ID from the Ajay API.
    Contains pure service logic and has no dependency on Tkinter / UI elements.
    """
    url = f"https://sponsor.ajay.app/api/skipSegments?videoID={video_id}"
    segments = []
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                for entry in data:
                    seg = entry.get("segment")
                    cat = entry.get("category", "sponsor")
                    if seg and len(seg) == 2:
                        segments.append({
                            "start": float(seg[0]),
                            "end": float(seg[1]),
                            "category": cat
                        })
    except Exception as e:
        print(f"[SponsorBlock Service] Fetch failed or no segments found: {e}")
    return segments
