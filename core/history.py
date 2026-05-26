# core/history.py
import sqlite3
import os
import platform
import time
import queue
import threading
from pathlib import Path
from typing import List, Dict, Any

def get_app_data_dir() -> Path:
    system = platform.system()
    if system == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".config"
    
    app_dir = base / "yt-dlp-downloader-pro"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir

def get_db_path() -> Path:
    return get_app_data_dir() / "history.db"

def connect_db() -> sqlite3.Connection:
    """Creates a database connection with high-performance concurrent WAL and busy timeouts."""
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path), timeout=30.0)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
    except Exception:
        pass
    return conn

_local = threading.local()

def get_read_connection() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = connect_db()
        _local.conn.row_factory = sqlite3.Row
    try:
        _local.conn.execute("SELECT 1")
    except Exception:
        _local.conn = connect_db()
        _local.conn.row_factory = sqlite3.Row
    return _local.conn

class DatabaseWriter:
    def __init__(self):
        self._queue: queue.Queue = queue.Queue()
        self._thread = threading.Thread(
            target=self._worker, daemon=True, name="db-writer"
        )
        self._thread.start()

    def _worker(self):
        # Dedicated database worker thread - sequential lock-free writes
        conn = connect_db()
        while True:
            try:
                item = self._queue.get(timeout=1.0)
                if item is None:  # Poison pill - exit
                    break
                fn, args, kwargs = item
                fn(conn, *args, **kwargs)
                conn.commit()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[DB Writer] SQL Write Error: {e}")
                try:
                    conn.rollback()
                except Exception:
                    pass
        try:
            conn.close()
        except Exception:
            pass

    def submit(self, fn, *args, **kwargs):
        """Dispatched from concurrent threads — non-blocking, asynchronous queue write"""
        self._queue.put((fn, args, kwargs))

    def shutdown(self):
        """Gracefully terminates the background SQLite worker thread"""
        self._queue.put(None)

# Global Singleton Database Writer Instance
_db_writer = DatabaseWriter()

def init_db():
    # Init db is run once synchronously at startup, before thread dispatchers
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS downloads (
            id TEXT PRIMARY KEY,
            title TEXT,
            url TEXT,
            format TEXT,
            file_path TEXT,
            status TEXT,
            downloaded_at INTEGER,
            file_size_bytes INTEGER,
            duration_seconds INTEGER
        )
    """)
    conn.commit()
    conn.close()

# --- DB Write Worker Callbacks ---

def _do_add_download_record(conn, item_id: str, title: str, url: str, format_desc: str, file_path: str, status: str, file_size: int, duration: int):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO downloads (id, title, url, format, file_path, status, downloaded_at, file_size_bytes, duration_seconds)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (item_id, title, url, format_desc, file_path, status, int(time.time()), file_size, duration))

def _do_update_download_status(conn, item_id: str, status: str, file_path: str = None, file_size: int = None, duration: int = None):
    cursor = conn.cursor()
    if file_path is not None or file_size is not None or duration is not None:
        updates = ["status = ?"]
        params = [status]
        if file_path is not None:
            updates.append("file_path = ?")
            params.append(file_path)
        if file_size is not None:
            updates.append("file_size_bytes = ?")
            params.append(file_size)
        if duration is not None:
            updates.append("duration_seconds = ?")
            params.append(duration)
        
        params.append(item_id)
        query = f"UPDATE downloads SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, tuple(params))
    else:
        cursor.execute("UPDATE downloads SET status = ? WHERE id = ?", (status, item_id))

def _do_clear_all_downloads(conn):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM downloads")

def _do_delete_download(conn, item_id: str):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM downloads WHERE id = ?", (item_id,))

# --- Exposed Non-Blocking API ---

def add_download_record(item_id: str, title: str, url: str, format_desc: str, file_path: str, status: str, file_size: int = 0, duration: int = 0):
    _db_writer.submit(_do_add_download_record, item_id, title, url, format_desc, file_path, status, file_size, duration)

def update_download_status(item_id: str, status: str, file_path: str = None, file_size: int = None, duration: int = None):
    _db_writer.submit(_do_update_download_status, item_id, status, file_path=file_path, file_size=file_size, duration=duration)

def clear_all_downloads():
    _db_writer.submit(_do_clear_all_downloads)

def delete_download(item_id: str):
    _db_writer.submit(_do_delete_download, item_id)

# --- Direct Read API (Safe concurrently with WAL mode) ---

def get_all_downloads() -> List[Dict[str, Any]]:
    db_path = get_db_path()
    if not db_path.exists():
        return []
    conn = get_read_connection()
    cursor = conn.cursor()
    downloads = []
    try:
        cursor.execute("SELECT * FROM downloads ORDER BY downloaded_at DESC")
        rows = cursor.fetchall()
        for row in rows:
            downloads.append(dict(row))
    except Exception as e:
        print(f"[!] SQLite Fetch Error: {e}")
    return downloads

