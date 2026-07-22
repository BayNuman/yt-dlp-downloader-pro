from dataclasses import dataclass
from typing import Any, Optional, Protocol
from enum import Enum

class EventKind(str, Enum):
    LOG = "log"
    STATS = "stats"
    ACTIVE_FILE = "active_file"
    PERCENT_COMPLETE = "percent_complete"
    STATUS = "status"
    QUEUE_SYNC = "queue_sync"
    METADATA_READY = "metadata_ready"
    METADATA_ERROR = "metadata_error"
    TOAST_OUTDATED = "toast_outdated"
    TOAST_SUCCESS = "toast_success"
    TOAST_CANCEL = "toast_cancel"
    TOAST_ERROR = "toast_error"
    QUEUE_DONE = "queue_done"

@dataclass
class AppEvent:
    kind: EventKind
    payload: Any = None
    task_id: Optional[str] = None

class EventEmitter(Protocol):
    """Abstract interface that core modules use to emit UI/progress events."""
    def emit(self, event: AppEvent) -> None:
        ...

class QueueEventEmitter:
    """Bridges AppEvent calls to Tkinter's traditional queue.Queue."""
    def __init__(self, ui_queue):
        self._queue = ui_queue

    def emit(self, event: AppEvent) -> None:
        try:
            # Traditional format: tuple of (kind_string, payload)
            self._queue.put_nowait((event.kind.value, event.payload))
        except Exception:
            pass  # Queue is full, drop event silently
