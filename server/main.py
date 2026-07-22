import os
import sys
import socket
import secrets
import asyncio
import logging
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from core.app_state import AppState
from core.controller import AppController
from server.ws.manager import ConnectionManager, WebSocketEventEmitter
from server.state import ServerState

PORT = 8765

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Check if port is bound on localhost
        return s.connect_ex(('127.0.0.1', port)) == 0

# Global server state reference
server_state: ServerState = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global server_state
    
    # 1. Port conflict check
    if is_port_in_use(PORT):
        logging.critical(f"[-] Port {PORT} is already in use. Aborting startup.")
        sys.exit(1)
        
    # 2. Initialize Core Layer
    app_state = AppState()
    controller = AppController(app_state)
    ws_manager = ConnectionManager()
    loop = asyncio.get_running_loop()
    
    # 3. Generate secure startup token
    startup_token = secrets.token_urlsafe(32)
    
    # 4. Create server state
    server_state = ServerState(
        controller=controller,
        ws_manager=ws_manager,
        loop=loop,
        startup_token=startup_token
    )
    app.state.server = server_state
    
    # 5. Bind AppController callbacks to WebSocket broadcasts
    emitter = WebSocketEventEmitter(ws_manager, loop)
    
    def on_task_added(task):
        asyncio.run_coroutine_threadsafe(
            ws_manager.broadcast({
                "type": "task_added",
                "task": task.to_api_dict()
            }),
            loop
        )

    def on_task_removed(task_id):
        asyncio.run_coroutine_threadsafe(
            ws_manager.broadcast({
                "type": "task_removed",
                "task_id": task_id
            }),
            loop
        )
        
    def on_metadata_ready(metadata):
        asyncio.run_coroutine_threadsafe(
            ws_manager.broadcast({
                "type": "metadata_ready",
                "payload": metadata
            }),
            loop
        )

    def on_metadata_error(err_str):
        asyncio.run_coroutine_threadsafe(
            ws_manager.broadcast({
                "type": "metadata_error",
                "payload": err_str
            }),
            loop
        )

    controller.on_task_added = on_task_added
    controller.on_task_removed = on_task_removed
    controller.on_metadata_ready = on_metadata_ready
    controller.on_metadata_error = on_metadata_error
    
    # Print the token to stdout so Tauri sidecar can intercept it
    print(f"BAYNUMAN_TOKEN:{startup_token}", flush=True)
    
    yield
    
    # 6. Graceful Shutdown: Cancel all running tasks
    logging.info("[*] Shutting down. Cancelling active downloads...")
    controller.cancel_all_tasks()

app = FastAPI(
    title="baynuman API",
    description="Backend API for the baynuman desktop application",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration supporting development and Tauri origins
origins = [
    "null",
    "http://localhost:5173",
    "http://tauri.localhost",
    "https://tauri.localhost"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "2.0.0"}

@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    from server.security import verify_ws_token
    verified = await verify_ws_token(websocket, token)
    if verified is None:
        return
        
    ws_manager = app.state.server.ws_manager
    await ws_manager.connect(websocket)
    try:
        while True:
            # Maintain active heartbeat listen
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

from server.routers.metadata import router as metadata_router
from server.routers.queue import router as queue_router
from server.routers.download import router as download_router
from server.routers.history import router as history_router
from server.routers.config import router as config_router
from server.routers.spotify import router as spotify_router

app.include_router(metadata_router, prefix="/api")
app.include_router(queue_router, prefix="/api")
app.include_router(download_router, prefix="/api")
app.include_router(history_router, prefix="/api")
app.include_router(config_router, prefix="/api")
app.include_router(spotify_router, prefix="/api")

