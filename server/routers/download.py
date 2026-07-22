import threading
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Dict, Any

from server.security import verify_token
from server.ws.manager import WebSocketEventEmitter
from core.downloader import run_queue_executor

router = APIRouter(
    prefix="/download",
    tags=["download"],
    dependencies=[Depends(verify_token)]
)

@router.post("/start")
async def start_downloads(request: Request) -> Dict[str, Any]:
    """Starts processing all pending downloads in the queue concurrently using background workers."""
    server = request.app.state.server
    controller = server.controller
    
    # Verify not already running
    if controller.state.is_executor_running:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Download executor is already running."
        )
        
    # Clear the cancel event and trigger execution thread
    server.cancel_event.clear()
    emitter = WebSocketEventEmitter(server.ws_manager, server.loop)
    
    threading.Thread(
        target=run_queue_executor,
        args=(controller.state, emitter, server.cancel_event),
        daemon=True,
        name="api-queue-executor"
    ).start()
    
    return {"success": True, "detail": "Download queue execution started."}

@router.post("/cancel")
async def cancel_downloads(request: Request) -> Dict[str, Any]:
    """Signals all running downloads to stop and kills their subprocesses immediately."""
    server = request.app.state.server
    
    # Trigger cancellation flags on all worker processes
    server.cancel_event.set()
    server.controller.cancel_all_tasks()
    
    return {"success": True, "detail": "All downloads cancelled successfully."}
