from fastapi import Request, HTTPException, status, WebSocket, Query
from typing import Optional
import logging

async def verify_token(request: Request) -> None:
    """FastAPI dependency to verify HTTP requests using the secure startup token header."""
    token = request.headers.get("X-Baynuman-Token")
    expected_token = request.app.state.server.startup_token
    
    if not token or token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing startup token."
        )

async def verify_ws_token(websocket: WebSocket, token: str = Query(None)) -> Optional[str]:
    """FastAPI WebSocket dependency to verify query parameter token authentication."""
    expected_token = websocket.app.state.server.startup_token
    
    if not token or token != expected_token:
        # 1008 policy violation signals auth failure
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
        
    return token
