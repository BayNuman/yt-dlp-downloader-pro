# 🖥️ yt-dlp Downloader Pro — Desktop Codebase Architecture & Technical Digest

> **Version:** v2.0.4 (Production Grade)  
> **Repository:** [BayNuman/yt-dlp-downloader-pro](https://github.com/BayNuman/yt-dlp-downloader-pro)  
> **Tech Stack:** Rust Tauri v2 · React 18 · TypeScript · Vite · Tailwind CSS · FastAPI (Python 3.13) · PyInstaller · FFmpeg

---

## 1. 🏗️ High-Level System Architecture

The desktop application is built as a multi-tier hybrid architecture combining a high-performance **Rust Tauri** window shell, a glassmorphic **React/TypeScript** frontend, and an embedded **FastAPI (Python)** sidecar backend running locally on port `8765`.

```mermaid
graph TD
    User["👤 Desktop User"] --> UI["🖥️ React 18 + Vite Frontend"]
    
    subgraph Rust Tauri Process ("Tauri App Shell")
        UI <-->|Tauri IPC / Webview| TauriRust["Rust App Controller (lib.rs)"]
        TauriRust -->|Spawn & Lifecycle Management| SidecarExe["server-sidecar.exe"]
    end
    
    subgraph Embedded FastAPI Backend ("Python Sidecar - Port 8765")
        SidecarExe --> FASTAPI["FastAPI REST & WebSocket Server"]
        FASTAPI <-->|REST / API| UI
        FASTAPI <-->|WebSocket Realtime Stream| UI
        
        FASTAPI --> SpotifyResolver["🎵 Spotify Resolver (Web API + Embed Fallback)"]
        FASTAPI --> AppController["⚙️ AppController & Task Queue"]
        AppController --> DownloaderEngine["⬇️ Downloader Engine (ThreadPoolExecutor)"]
    end
    
    subgraph Execution & Processing
        DownloaderEngine -->|CLI Dispatch| PyInstallerCLI["server-sidecar.exe -m yt_dlp"]
        PyInstallerCLI --> YTDLP["yt-dlp Core Engine"]
        YTDLP --> FFMPEG["FFmpeg / FFprobe Processing"]
    end
```

---

## 2. 🎨 Frontend Architecture (`frontend/src/`)

Built with React 18, Vite, and Tailwind CSS, the user interface follows a modern glassmorphic theme design system with reactive state management and real-time WebSocket progress updates.

### Key Components:
- **`appStore.ts` (Zustand Global State Engine):**  
  Manages application preferences, active download queues, execution logs, toast notifications, and theme settings (`Forest`, `Makara Vintage Dark`, `Night Blue`).
- **`UrlPanel.tsx`:**  
  Handles link input, instant YouTube metadata inspection, and Spotify playlist URL resolution. Automatically triggers track listing modals for batch queue insertion.
- **`PreviewPanel.tsx` (Interactive Dual-Handle Slider):**  
  Interactive video trimmer overlaying video chapters and **SponsorBlock** ad segments on a bidirectional range timeline.
- **`QueuePanel.tsx` & `ProgressPanel.tsx`:**  
  Renders real-time download velocity (MB/s), active worker threads, progress bars, sparkline graphs, and diagnostic log output.
- **`useWebSocket.ts`:**  
  Subscribes to `ws://127.0.0.1:8765/ws` to receive live progress events, task completion triggers, and error messages from the backend.

---

## 3. ⚙️ Backend & Sidecar Architecture (`server/` & `core/`)

The backend operates as an isolated FastAPI sidecar process compiled into a standalone executable via PyInstaller.

### 🔌 API Routers (`server/routers/`):
- **`/api/config` (`config.py`):** System status inspection, directory selector via native Tkinter thread, and preference persistence.
- **`/api/metadata` (`metadata.py`):** Fast video metadata extraction and SponsorBlock segment fetching.
- **`/api/spotify` (`spotify.py`):**  
  **Dual-Strategy Spotify Engine:**
  1. *Primary:* Authenticates via official Spotify Web API (`Client Credentials Flow`).
  2. *Fallback:* If API returns `403 Forbidden` or credentials are missing, automatically parses public embed HTML (`open.spotify.com/embed/playlist/{id}`) using `__NEXT_DATA__` JSON extraction.
- **`/api/queue` (`queue.py`):** Multi-task batch enqueueing and execution control (`/start`, `/pause`, `/cancel`).

### 🛠️ Core Execution Engine (`core/`):
- **`downloader.py`:**  
  Thread-safe concurrent execution runner (`ThreadPoolExecutor` with configurable `max_workers`). Intercepts stdout logs, calculates ETA and download speed, and manages SQLite task history.
- **`command_builder.py`:**  
  Constructs optimized CLI arguments for `yt-dlp` and `FFmpeg` format conversions, metadata embedding, and directory organization.
- **`clip.py` (Interval Merging Algorithm):**  
  Implements **LeetCode 56 Greedy Interval Merging** to combine overlapping time segments and execute lossless FFmpeg concat joining.

---

## 4. 🔒 Resilience & Process Lifecycle Management

### 1. Stale Port Auto-Cleanup (`server/main.py`):
Before binding to port `8765`, the backend checks if the port is occupied. If a leftover process is detected, it automatically executes a process termination routine (`taskkill` on Windows / `fuser` on Linux) to ensure seamless startup.

### 2. Tauri Window Exit Handler (`frontend/src-tauri/src/lib.rs`):
Intercepts Tauri window destruction events (`RunEvent::ExitRequested` & `Exit`) and automatically terminates any orphan `server-sidecar.exe` processes.

### 3. PyInstaller Multiprocessing Router (`server_app.py`):
```python
if __name__ == "__main__":
    # 1. Enable PyInstaller Windows multiprocessing support
    multiprocessing.freeze_support()

    # 2. Route CLI execution calls (e.g. server-sidecar.exe -m yt_dlp ...)
    if "-m" in sys.argv:
        m_idx = sys.argv.index("-m")
        if m_idx + 1 < len(sys.argv) and sys.argv[m_idx + 1] == "yt_dlp":
            import yt_dlp
            sys.argv = [sys.argv[0]] + sys.argv[m_idx + 2:]
            sys.exit(yt_dlp.main())

    # 3. Prevent spawned worker forks from launching secondary FastAPI servers
    if any(arg.startswith("--multiprocessing-fork") for arg in sys.argv):
        sys.exit(0)

    # 4. Launch FastAPI web server
    uvicorn.run("server.main:app", host="127.0.0.1", port=8765, log_level="info", workers=1)
```

---

## 5. 📦 Packaging & Standalone Installer Pipelines

1. **PyInstaller Sidecar Compiler (`build_sidecar.py`):**  
   Bundles Python 3.13, FastAPI, uvicorn, yt-dlp, websockets, and dependencies into `dist/server-sidecar.exe` and copies it to `frontend/src-tauri/bin/server-sidecar-x86_64-pc-windows-msvc.exe`.
2. **Tauri Release Bundler (`npx @tauri-apps/cli build`):**  
   Compiles Rust binaries, packages static React frontend assets, embeds FFmpeg/FFprobe runtimes, and generates zero-dependency **NSIS Setup (`.exe`)** and **MSI (`.msi`)** installers.

---

## 💡 Summary of Differentiating Technical Features

1. **Zero-Dependency Installation:** Bundles Python runtime, FFmpeg, FFprobe, and sidecar backend in a single setup executable.
2. **Zero-Config Spotify Downloader:** Dual-mode resolver (API + Embed Scraper) enables parsing public Spotify playlists without mandatory developer credentials.
3. **Interactive Visual Trimming:** Dual-handle range slider with real-time SponsorBlock & chapter segment overlays.
4. **Resilient Process Management:** Automatic stale port clearing and PyInstaller multiprocessing fork routing prevent orphaned background processes.
