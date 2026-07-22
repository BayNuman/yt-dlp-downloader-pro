from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Dict, Any

from server.models import AddTaskRequest, DownloadTaskResponse
from server.security import verify_token
from core.downloader import toggle_pause_task
from core.app_state import TaskStatus

router = APIRouter(
    prefix="/queue",
    tags=["queue"],
    dependencies=[Depends(verify_token)]
)

@router.get("", response_model=List[DownloadTaskResponse])
async def get_queue(request: Request):
    """Retrieves the list of all active/pending tasks in the download queue."""
    controller = request.app.state.server.controller
    with controller.state._lock:
        return [task.to_api_dict() for task in controller.state.queue_list]

@router.post("", status_code=status.HTTP_201_CREATED)
async def add_to_queue(req: AddTaskRequest, request: Request):
    """Adds new download tasks (or micro-clips) to the queue after validation."""
    controller = request.app.state.server.controller
    
    # 1. Duplicate check
    is_dup, title, fmt = controller.check_duplicate(req.url, req.settings or {})
    if is_dup:
        return {
            "success": False,
            "detail": f"Duplicate download detected: '{title}' ({fmt})",
            "added_count": 0
        }
        
    # 2. Extract micro clips list
    multi_clips = []
    if req.clips:
        multi_clips = [c.dict() for c in req.clips]
        
    # 3. Add to queue
    success, err_msg, added_count = controller.validate_and_add_tasks(
        url=req.url,
        item_cfg=req.settings or {},
        multi_clips=multi_clips,
        lang=controller.state.current_lang
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_msg
        )
        
    return {
        "success": True,
        "detail": f"Successfully added {added_count} task(s) to the queue.",
        "added_count": added_count
    }

@router.delete("/{task_id}")
async def remove_from_queue(task_id: str, request: Request):
    """Removes a task from the active queue, killing its process if downloading."""
    controller = request.app.state.server.controller
    removed = controller.remove_task(task_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found in the queue."
        )
    return {"success": True}

@router.post("/{task_id}/pause")
async def pause_task(task_id: str, request: Request):
    """Pauses a running download task at the OS subprocess level."""
    controller = request.app.state.server.controller
    target_task = None
    with controller.state._lock:
        for t in controller.state.queue_list:
            if t.id == task_id:
                target_task = t
                break
                
    if not target_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found in the queue."
        )
        
    if target_task.status_code != TaskStatus.DOWNLOADING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only active DOWNLOADING tasks can be paused."
        )
        
    if not getattr(target_task, "is_paused", False):
        toggle_pause_task(target_task)
        
    return {"success": True, "status": "paused"}

@router.post("/{task_id}/resume")
async def resume_task(task_id: str, request: Request):
    """Resumes a paused download task at the OS subprocess level."""
    controller = request.app.state.server.controller
    target_task = None
    with controller.state._lock:
        for t in controller.state.queue_list:
            if t.id == task_id:
                target_task = t
                break
                
    if not target_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found in the queue."
        )
        
    if target_task.status_code != TaskStatus.PAUSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PAUSED tasks can be resumed."
        )
        
    if getattr(target_task, "is_paused", False):
        toggle_pause_task(target_task)
        
    return {"success": True, "status": "downloading"}
