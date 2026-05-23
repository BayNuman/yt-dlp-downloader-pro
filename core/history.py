# core/history.py
import sqlite3
import os
import platform
import time
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

def init_db():
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
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

def add_download_record(item_id: str, title: str, url: str, format_desc: str, file_path: str, status: str, file_size: int = 0, duration: int = 0):
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO downloads (id, title, url, format, file_path, status, downloaded_at, file_size_bytes, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (item_id, title, url, format_desc, file_path, status, int(time.time()), file_size, duration))
        conn.commit()
    except Exception as e:
        print(f"[!] SQLite Error: {e}")
    finally:
        conn.close()

def update_download_status(item_id: str, status: str, file_path: str = None, file_size: int = None, duration: int = None):
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    try:
        if file_path is not None or file_size is not None or duration is not None:
            # Build dynamic update
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
        conn.commit()
    except Exception as e:
        print(f"[!] SQLite Update Error: {e}")
    finally:
        conn.close()

def get_all_downloads() -> List[Dict[str, Any]]:
    db_path = get_db_path()
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    downloads = []
    try:
        cursor.execute("SELECT * FROM downloads ORDER BY downloaded_at DESC")
        rows = cursor.fetchall()
        for row in rows:
            downloads.append(dict(row))
    except Exception as e:
        print(f"[!] SQLite Fetch Error: {e}")
    finally:
        conn.close()
    return downloads

def clear_all_downloads():
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM downloads")
        conn.commit()
    except Exception as e:
        print(f"[!] SQLite Clear Error: {e}")
    finally:
        conn.close()

def delete_download(item_id: str):
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM downloads WHERE id = ?", (item_id,))
        conn.commit()
    except Exception as e:
        print(f"[!] SQLite Delete Error: {e}")
    finally:
        conn.close()
