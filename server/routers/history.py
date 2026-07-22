from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional

from server.security import verify_token
from server.async_bridge import async_get_all_downloads, async_delete_download, async_clear_all_downloads

router = APIRouter(
    prefix="/history",
    tags=["history"],
    dependencies=[Depends(verify_token)]
)

@router.get("")
async def get_history(limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
    """Retrieves all downloads from the SQLite history database (supports pagination)."""
    try:
        records = await async_get_all_downloads()
        if limit is not None:
            return records[offset : offset + limit]
        return records[offset:]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch history: {str(e)}"
        )

@router.delete("/{record_id}")
async def delete_history_item(record_id: str) -> Dict[str, Any]:
    """Deletes a specific download history record and cleans up cached thumbnails."""
    try:
        await async_delete_download(record_id)
        return {"success": True, "detail": f"Record '{record_id}' deleted."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete history record: {str(e)}"
        )

@router.post("/clear")
async def clear_history() -> Dict[str, Any]:
    """Clears all download history records and removes associated thumbnail files."""
    try:
        await async_clear_all_downloads()
        return {"success": True, "detail": "All download history cleared."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear history: {str(e)}"
        )
