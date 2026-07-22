import os
import base64
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from server.models import MetadataRequest
from server.security import verify_token
from core.services import fetch_video_metadata, fetch_sponsor_segments
from core.history import get_app_data_dir

router = APIRouter(
    prefix="/metadata",
    tags=["metadata"],
    dependencies=[Depends(verify_token)]
)

def get_base64_image(path: Optional[str]) -> Optional[str]:
    """Helper to convert local WebP thumbnail to a base64 data URL for frontend consumption."""
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            return f"data:image/webp;base64,{encoded}"
    except Exception:
        return None

@router.post("")
async def get_metadata(req: MetadataRequest) -> Dict[str, Any]:
    """Fetches video metadata from a URL and compiles the response (with base64 thumb)."""
    app_data_dir = get_app_data_dir()
    scratch_dir = Path.home() / ".yt-downloader-scratch"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Run blocking network/disk service in a separate thread to prevent event loop starvation
        meta = await asyncio.to_thread(
            fetch_video_metadata,
            req.url,
            req.cookies_file,
            req.browser_cookies,
            scratch_dir,
            app_data_dir
        )
        
        # Inject base64 image data for frontend loading
        meta["thumbnail_img"] = get_base64_image(meta.get("thumbnail_path"))
        return meta
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch metadata: {str(e)}"
        )

@router.get("/sponsorblock/{video_id}")
async def get_sponsorblock_segments(video_id: str) -> List[Dict[str, Any]]:
    """Retrieves SponsorBlock segments/skip marks for the specified YouTube video ID."""
    try:
        segments = await asyncio.to_thread(fetch_sponsor_segments, video_id)
        return segments
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch sponsor segments: {str(e)}"
        )

# Import asyncio within the module to use to_thread
import asyncio
