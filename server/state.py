import threading
from dataclasses import dataclass, field
import asyncio
from core.controller import AppController
from server.ws.manager import ConnectionManager

@dataclass
class ServerState:
    controller: AppController
    ws_manager: ConnectionManager
    loop: asyncio.AbstractEventLoop
    startup_token: str
    cancel_event: threading.Event = field(default_factory=threading.Event)
