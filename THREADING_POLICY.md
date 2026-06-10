# Threading & Concurrency Policy

This document establishes the architecture and policy for concurrency, threading, and synchronization within the application. All future modules and modifications must comply with these guidelines.

---

## 1. Threading Architecture Hierarchy

The application utilizes three main concurrency primitives tailored for specific tasks:

1. **Long-Running / Core Tasks (Download Queue Execution)**:
   - Must use `ThreadPoolExecutor` (defined in `core/downloader.py`).
   - Limits resources based on `state.preferences.max_workers`.
   - Never spawn raw, unmanaged threads for multiple concurrent downloads.

2. **Sequential Background Services (Queue-driven workers)**:
   - **Waveform generation** (`waveform-worker`) and **database writes** (`db-writer`) use a single-threaded queue consumer pattern.
   - Tasks are put in a `queue.Queue` and consumed sequentially by a single daemon thread to eliminate thread pollution, database locks, and CPU bottlenecks.

3. **Short-Lived I/O Background Tasks (Metadata Fetching, API checks, updater)**:
   - Spawns simple daemon `threading.Thread` instances.
   - **Rule**: Every spawned raw thread must be given a descriptive `name` (e.g., `name="metadata-fetcher"`, `name="self-updater"`) for tracebility and debugging.
   - **Rule**: Eliminate double-threading (spawning a thread that only calls another async method). The caller (e.g. UI layer) should invoke the async method directly from the main thread instead of nesting thread creations.

---

## 2. Cancellation and Lifecycle Management

### 2.1 Thread Cancellation Checkpoints
Cancellation in the downloader is cooperative and propagates through thread-safe status checks:
- Tasks check `task.cancel_event.is_set()` before starting, during active command output parsing, and before post-processing.
- Child subprocesses (such as `yt-dlp` or `ffmpeg`) must be registered with the central subprocess register via `register_active_subprocess(proc)`.
- When cancellation is triggered, the subprocess is sent a termination signal, and the worker threads wait/cleanup safely without leaking zombie processes.

### 2.2 Main Window Close Lifecycle
On window close (`_on_close` in `ui/main_window.py`):
1. Check if the executor is active and prompt the user.
2. Trigger cancellation on all tasks.
3. Call `kill_all_active_subprocesses()` to immediately kill all running `yt-dlp` or `ffmpeg` child processes.
4. Call `shutdown_db()` to flush and close the writer thread.

---

## 3. Synchronization and Thread Safety

- **Shared State Guard**: All read/write operations on shared structures, particularly `AppState.queue_list`, must be wrapped in `with state._lock:` to ensure thread safety across GUI updates and background workers.
- **UI Interaction**: Background threads must never modify CustomTkinter widget properties directly. Communication from background threads to the UI thread must be routed through the thread-safe `self.ui_queue` or using `self.after(0, callback)`.
