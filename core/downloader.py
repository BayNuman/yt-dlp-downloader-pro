# core/downloader.py
import os
import re
import sys
import time
import shlex
import subprocess
import ctypes
import threading
import queue
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, wait

# Windows Sleep prevention constants
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001

def prevent_sleep():
    if os.name == 'nt':
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
        except Exception as e:
            print(f"[Sleep Prevention] Failed to prevent sleep: {e}")

def allow_sleep():
    if os.name == 'nt':
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
        except Exception as e:
            print(f"[Sleep Prevention] Failed to restore sleep state: {e}")

def safe_put_ui(ui_queue, item):
    try:
        ui_queue.put_nowait(item)
    except queue.Full:
        if item[0] == "log":
            pass  # Shed verbose logs under heavy load
        else:
            try:
                ui_queue.put(item, timeout=0.1)
            except Exception:
                pass

# Thread-safe subprocess tracking to prevent Zombie Processes
active_subprocess_lock = threading.Lock()
active_subprocesses = set()

def register_active_subprocess(proc):
    with active_subprocess_lock:
        active_subprocesses.add(proc)

def unregister_active_subprocess(proc):
    with active_subprocess_lock:
        active_subprocesses.discard(proc)

def kill_all_active_subprocesses():
    with active_subprocess_lock:
        for proc in list(active_subprocesses):
            try:
                proc.terminate()
                proc.wait(timeout=1)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        active_subprocesses.clear()

# Low-pass Downsampled Waveform Generation
def generate_audio_waveform(task, input_file_path: str) -> str:
    """
    Generates a 320x60 static waveform image for audio files under app_data_dir / waveforms / waveform_{id}.png.
    Utilizes Downsampling (aresample=1000) for extremely fast O(1) performance (1.5s vs 45s).
    """
    try:
        from core.history import get_app_data_dir
        if not input_file_path or not os.path.exists(input_file_path):
            return None
        waveforms_dir = get_app_data_dir() / "waveforms"
        waveforms_dir.mkdir(parents=True, exist_ok=True)
        output_png = waveforms_dir / f"waveform_{task.id}.png"
        ffmpeg_bin = resolve_ffmpeg_path()
        cmd = [
            ffmpeg_bin, "-y",
            "-i", input_file_path,
            "-filter_complex", "aresample=1000,showwavespic=s=320x60:colors=#6366f1",
            "-frames:v", "1",
            str(output_png)
        ]
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        proc = None
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                startupinfo=startupinfo,
                shell=False
            )
            register_active_subprocess(proc)
            proc.wait(timeout=10)
        finally:
            if proc:
                unregister_active_subprocess(proc)
        if output_png.exists():
            return str(output_png)
    except Exception as e:
        print(f"[warning] Waveform generation failed: {e}")
    return None

# Single-Threaded Background Waveform Generation Queue
waveform_queue = queue.Queue()

def _waveform_worker():
    while True:
        task, file_path, callback = waveform_queue.get()
        try:
            png_path = generate_audio_waveform(task, file_path)
            if png_path:
                callback(png_path)
        except Exception as e:
            print(f"[warning] Waveform worker error: {e}")
        finally:
            waveform_queue.task_done()

threading.Thread(target=_waveform_worker, daemon=True).start()

def enqueue_waveform_generation(task, file_path, callback):
    waveform_queue.put((task, file_path, callback))

def _on_waveform_done(task_id, png_path, ui_queue):
    update_download_status(task_id, "COMPLETED", thumbnail_path=png_path)
    safe_put_ui(ui_queue, ("queue_sync", None))

# Core state & DB models
from core.app_state import AppState, DownloadTask, TaskStatus
from core.command_builder import build_command, format_cmd_for_log, YOUTUBE_FALLBACK_EXTRACTOR_ARGS
from core.history import add_download_record, update_download_status
from core.clip import parse_time_to_seconds
from core.env import refresh_path_env

def resolve_ffmpeg_path() -> str:
    """Finds the ffmpeg binary, checking bundled paths or standard locations."""
    # 1. Check PyInstaller temp directory (if bundled inside the EXE)
    try:
        base_path = sys._MEIPASS
        bundled = os.path.join(base_path, "ffmpeg.exe" if os.name == "nt" else "ffmpeg")
        if os.path.exists(bundled):
            return bundled
    except Exception:
        pass

    # 2. Check directly next to the running executable (for installed Windows setups)
    try:
        app_dir = os.path.dirname(sys.executable)
        adjacent = os.path.join(app_dir, "ffmpeg.exe" if os.name == "nt" else "ffmpeg")
        if os.path.exists(adjacent):
            return adjacent
    except Exception:
        pass

    # 3. Check local bin directory (for development)
    local_bin = Path(".") / "bin" / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    if local_bin.exists():
        return str(local_bin.resolve())

    # 4. Fallback to system PATH
    return "ffmpeg"

def append_options_before_urls(cmd: list[str], urls: list[str], options: list[str]) -> list[str]:
    if not urls:
        return cmd + options
    option_area = cmd[:-len(urls)]
    url_area = cmd[-len(urls):]
    return option_area + options + url_area

def run_command_stream(cmd: list[str], task: DownloadTask, state: AppState, ui_queue, cancel_event) -> tuple[int, bool, bool]:
    progress_re = re.compile(
        r"\[download\]\s+(\d{1,3}(?:\.\d+)?)%\s+of\s+(~?\d+(?:\.\d+)?\w+)\s+at\s+(\d+(?:\.\d+)?\w+/s|Unknown speed)\s+ETA\s+(\d{2}:\d{2}|\w+)"
    )
    dest_re = re.compile(r"\[download\]\s+Destination:\s+(.+)")
    already_re = re.compile(r"\[download\]\s+(.+)\s+has already been downloaded")

    saw_http_403 = False
    saw_outdated_warning = False

    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        startupinfo=startupinfo,
        shell=False,
    )
    assert process.stdout is not None
    task._process = process

    try:
        register_active_subprocess(process)
        for line in process.stdout:
            if getattr(task, "is_paused", False):
                while getattr(task, "is_paused", False) and not (cancel_event.is_set() or task.cancel_event.is_set()):
                    time.sleep(0.2)

            # Prefix UI logs with task title for concurrent visibility
            safe_put_ui(ui_queue, ("log", f"[{task.title[:18]}...] {line}"))

            if cancel_event.is_set() or task.cancel_event.is_set():
                process.terminate()
                break

            match = progress_re.search(line)
            if match:
                value = max(0.0, min(100.0, float(match.group(1))))
                size_str = match.group(2)
                speed_str = match.group(3)
                eta_str = match.group(4)

                stats_payload = {
                    "task_id": task.id,
                    "percent": value,
                    "size": size_str,
                    "speed": speed_str,
                    "eta": eta_str,
                }
                safe_put_ui(ui_queue, ("stats", stats_payload))

            dest_match = dest_re.search(line)
            if dest_match:
                full_path = dest_match.group(1).strip()
                filename = Path(full_path).name
                safe_put_ui(ui_queue, ("active_file", (task.id, filename)))
                task._output_file = full_path

            already_match = already_re.search(line)
            if already_match:
                full_path = already_match.group(1).strip()
                filename = Path(full_path).name
                safe_put_ui(ui_queue, ("active_file", (task.id, filename)))
                task._output_file = full_path

            if "HTTP Error 403: Forbidden" in line:
                saw_http_403 = True
            if "version" in line and "older than 90 days" in line:
                saw_outdated_warning = True

        return process.wait(), saw_http_403, saw_outdated_warning
    finally:
        unregister_active_subprocess(process)

def wait_process_with_timeout(proc, timeout=120) -> int:
    try:
        return proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()  # sweep zombie process
        raise RuntimeError(f"Process timed out after {timeout} seconds")

def clean_empty_directories(path_str: str, base_dir_str: str):
    """
    Recursively deletes empty parent directories up to base_dir_str.
    Does not delete base_dir_str itself.
    """
    try:
        if not path_str or not base_dir_str:
            return
        
        path = Path(path_str).resolve()
        base_dir = Path(base_dir_str).resolve()
        
        # If path is a file, take its parent folder
        if path.is_file():
            folder = path.parent
        else:
            folder = path
            
        # Traverse upwards from folder to base_dir (exclusive of base_dir)
        while folder != base_dir and base_dir in folder.parents:
            # Check if directory exists and is empty
            if folder.exists() and folder.is_dir():
                # Check if empty (no files or folders inside)
                if not any(folder.iterdir()):
                    try:
                        folder.rmdir()
                    except Exception as e:
                        print(f"[Cleanup Hook] Failed to remove folder {folder}: {e}")
                        break # stop if we cannot delete
                else:
                    # Folder is not empty, so we cannot delete it, and parents won't be empty either
                    break
            else:
                break
            # Go up one level
            folder = folder.parent
    except Exception as e:
        print(f"[Cleanup Hook] Error in clean_empty_directories: {e}")

def _handle_cancel(task, lang, ui_queue, base_dir=None):
    task.status_code = TaskStatus.CANCELLED
    task.status = "Cancelled"
    update_download_status(task.id, "CANCELLED")
    if base_dir and getattr(task, "_output_file", None):
        clean_empty_directories(task._output_file, base_dir)
    safe_put_ui(ui_queue, ("toast_cancel", task.title))
    safe_put_ui(ui_queue, ("queue_sync", None))

def _set_downloading_status(task, lang, ui_queue):
    task.status_code = TaskStatus.DOWNLOADING
    task.status = "Downloading"
    safe_put_ui(ui_queue, ("queue_sync", None))

def _log_start(task, cmd, ui_queue):
    safe_put_ui(ui_queue, ("active_file", (task.id, task.title)))
    safe_put_ui(ui_queue, ("log", f"\n[queue] Download Started: {task.title}\n"))
    safe_put_ui(ui_queue, ("log", f"$ {format_cmd_for_log(cmd)}\n"))
    add_download_record(
        item_id=task.id,
        title=task.title,
        url=task.url,
        format_desc=f"{task.mode} ({task.video_profile if task.mode == 'Video' else task.audio_quality})",
        file_path="",
        status="DOWNLOADING",
        file_size=0,
        duration=int(parse_time_to_seconds(task.duration) or 0),
        thumbnail_path=getattr(task, "thumbnail_path", None)
    )

def _cleanup_temp_json(task):
    temp_json_file = getattr(task, "_temp_info_json", None)
    if temp_json_file and os.path.exists(temp_json_file):
        try:
            os.remove(temp_json_file)
        except Exception:
            pass

def _process_macro_clips(task, output_file, lang, ui_queue, cancel_event) -> str:
    safe_put_ui(ui_queue, ("log", f"[{task.title}] Slicing LeetCode 56 Multi-Clips...\n"))
    ffmpeg_bin = resolve_ffmpeg_path()
    input_path = Path(output_file)
    macro_start = parse_time_to_seconds(task.clip_start) or 0.0
    macro_clips = task.macro_clips_data
    from core.profiles import EXPORT_PROFILES

    micro_paths = []
    for idx_m, micro in enumerate(macro_clips):
        if cancel_event.is_set() or task.cancel_event.is_set():
            break
        micro_start = micro["start"]
        micro_end = micro["end"]
        micro_profile_name = micro.get("profile", "Default (No Profile)")
        micro_profile = EXPORT_PROFILES.get(micro_profile_name)

        rel_start = max(0.0, micro_start - macro_start)
        rel_end = max(0.0, micro_end - macro_start)
        duration_sec = rel_end - rel_start

        target_ext = micro_profile.ext if (micro_profile and micro_profile.name != "Default") else input_path.suffix.lstrip(".")
        suffix = micro.get("output_suffix", f"_clip{idx_m+1}")
        micro_output_path = input_path.parent / f"{input_path.stem}{suffix}.{target_ext}"

        ffmpeg_cmd = [ffmpeg_bin, "-y", "-ss", str(rel_start), "-to", str(rel_end), "-i", str(input_path)]

        if micro_profile and micro_profile.name != "Default":
            ffmpeg_cmd.extend(micro_profile.get_ffmpeg_args(duration_sec))
        else:
            # Smart Transcoding: Re-encode video+audio if Precise Cut is enabled
            if micro.get("clip_precise") or getattr(task, "clip_precise", False):
                if getattr(task, "mode", "Video") == "Audio":
                    aud_fmt = getattr(task, "audio_format", "mp3")
                    if aud_fmt == "mp3":
                        ffmpeg_cmd.extend(["-c:a", "libmp3lame", "-b:a", "192k"])
                    elif aud_fmt in ("m4a", "aac"):
                        ffmpeg_cmd.extend(["-c:a", "aac", "-b:a", "192k"])
                    else:
                        ffmpeg_cmd.extend(["-c:a", "copy"])
                else:
                    ffmpeg_cmd.extend(["-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-c:a", "aac", "-b:a", "192k"])
            else:
                ffmpeg_cmd.extend(["-c:v", "copy", "-c:a", "copy"])

        ffmpeg_cmd.append(str(micro_output_path))

        safe_put_ui(ui_queue, ("log", f"[{task.title}] Slicing segment {idx_m+1}/{len(macro_clips)}: {micro_output_path.name}\n"))

        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        proc = None
        try:
            proc = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                startupinfo=startupinfo,
                shell=False,
            )
            register_active_subprocess(proc)
            wait_process_with_timeout(proc, timeout=300)
        finally:
            if proc:
                unregister_active_subprocess(proc)

        if micro_output_path.exists():
            micro_paths.append(str(micro_output_path))
            add_download_record(
                item_id=f"{task.id}_clip{idx_m+1}",
                title=f"{task.title} (Clip {idx_m+1})",
                url=task.url,
                format_desc=f"{task.mode} ({micro_profile_name})",
                file_path=str(micro_output_path),
                status="COMPLETED",
                file_size=os.path.getsize(micro_output_path),
                duration=int(duration_sec),
                thumbnail_path=getattr(task, "thumbnail_path", None)
            )

    if cancel_event.is_set() or task.cancel_event.is_set():
        return output_file

    try:
        os.remove(input_path)
    except Exception:
        pass
    ret_file = str(input_path.parent / f"{input_path.stem}_clips_generated")

    if task.merge_clips and len(micro_paths) > 1 and macro_clips:
        safe_put_ui(ui_queue, ("log", f"[{task.title}] Losslessly merging fanned out segments via Concat Demuxer...\n"))
        from core.merger import LosslessMerger
        merger = LosslessMerger(ffmpeg_bin)

        merged_ext = EXPORT_PROFILES[macro_clips[0].get("profile", "Default (No Profile)")].ext if EXPORT_PROFILES.get(macro_clips[0].get("profile")) else input_path.suffix.lstrip(".")
        merged_output_path = input_path.parent / f"{input_path.stem}_merged.{merged_ext}"

        success = merger.merge_clips(micro_paths, str(merged_output_path), cleanup=True)
        if success and merged_output_path.exists():
            ret_file = str(merged_output_path)
            add_download_record(
                item_id=f"{task.id}_merged",
                title=f"{task.title} (Merged)",
                url=task.url,
                format_desc=f"{task.mode} (Merged Clips)",
                file_path=str(merged_output_path),
                status="COMPLETED",
                file_size=os.path.getsize(merged_output_path),
                duration=int(sum(mc["end"] - mc["start"] for mc in macro_clips)),
                thumbnail_path=getattr(task, "thumbnail_path", None)
            )
    return ret_file

def _process_single_clip(task, output_file, lang, ui_queue, cancel_event) -> str:
    safe_put_ui(ui_queue, ("log", f"[{task.title}] Postprocessing clip media...\n"))
    ffmpeg_bin = resolve_ffmpeg_path()
    input_path = Path(output_file)
    from core.profiles import EXPORT_PROFILES
    profile = EXPORT_PROFILES.get(task.export_profile)

    target_ext = profile.ext if (profile and profile.name != "Default") else input_path.suffix.lstrip(".")
    final_path = input_path.parent / f"processed_{input_path.stem}.{target_ext}"

    start = parse_time_to_seconds(task.clip_start) or 0.0
    end = parse_time_to_seconds(task.clip_end) or 0.0
    duration_sec = (end - start) if task.clip_enabled else (parse_time_to_seconds(task.duration) or 10.0)

    ffmpeg_cmd = [ffmpeg_bin, "-y"]
    if task.clip_enabled and task.clip_strategy in ("hybrid", "full_trim"):
        if task.clip_strategy == "hybrid":
            buffered_start = max(0.0, start - 5.0)
            offset_start = start - buffered_start
            offset_end = end - buffered_start
            ffmpeg_cmd.extend(["-ss", str(offset_start), "-to", str(offset_end)])
        else:
            ffmpeg_cmd.extend(["-ss", str(start), "-to", str(end)])

    ffmpeg_cmd.extend(["-i", str(input_path)])

    if profile and profile.name != "Default":
        ffmpeg_cmd.extend(profile.get_ffmpeg_args(duration_sec))
    else:
        # Smart Transcoding: Re-encode video+audio if Precise Cut is enabled
        if getattr(task, "clip_precise", False):
            if getattr(task, "mode", "Video") == "Audio":
                aud_fmt = getattr(task, "audio_format", "mp3")
                if aud_fmt == "mp3":
                    ffmpeg_cmd.extend(["-c:a", "libmp3lame", "-b:a", "192k"])
                elif aud_fmt in ("m4a", "aac"):
                    ffmpeg_cmd.extend(["-c:a", "aac", "-b:a", "192k"])
                else:
                    ffmpeg_cmd.extend(["-c:a", "copy"])
            else:
                ffmpeg_cmd.extend(["-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-c:a", "aac", "-b:a", "192k"])
        else:
            ffmpeg_cmd.extend(["-c:v", "copy", "-c:a", "copy"])

    ffmpeg_cmd.append(str(final_path))

    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    proc = None
    try:
        proc = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            startupinfo=startupinfo,
            shell=False,
        )
        register_active_subprocess(proc)
        wait_process_with_timeout(proc, timeout=600)
    finally:
        if proc:
            unregister_active_subprocess(proc)

    if proc.returncode == 0 and final_path.exists():
        try:
            os.remove(input_path)
            clean_output_path = input_path.with_suffix(f".{target_ext}")
            if final_path != clean_output_path:
                if os.path.exists(clean_output_path):
                    os.remove(clean_output_path)
                os.rename(final_path, clean_output_path)
            return str(clean_output_path)
        except Exception:
            pass
    return output_file

def _set_completed_status(task, output_file, lang, ui_queue):
    task.status_code = TaskStatus.COMPLETED
    task.status = "Completed"
    file_size = os.path.getsize(output_file) if output_file and os.path.exists(output_file) else 0
    task.file_path = output_file or ""
    task.percent = 100.0
    
    thumb_path = getattr(task, "thumbnail_path", None)
    if getattr(task, "mode", "Video") == "Audio" and output_file and os.path.exists(output_file):
        # Enqueue waveform generation in a single-threaded queue to prevent CPU boğulma
        def cb(png):
            _on_waveform_done(task.id, png, ui_queue)
        enqueue_waveform_generation(task, output_file, cb)
        
    update_download_status(task.id, "COMPLETED", file_path=output_file or "", file_size=file_size, thumbnail_path=thumb_path)
    safe_put_ui(ui_queue, ("percent_complete", 1.0))
    safe_put_ui(ui_queue, ("toast_success", {"title": task.title, "file_path": output_file or ""}))

def _set_failed_status(task, code, lang, ui_queue, base_dir=None):
    task.status_code = TaskStatus.FAILED
    task.status = "Failed"
    update_download_status(task.id, "FAILED")
    if base_dir and getattr(task, "_output_file", None):
        clean_empty_directories(task._output_file, base_dir)
    safe_put_ui(ui_queue, ("toast_error", {"code": code, "title": task.title}))

def _handle_exception(task, e, lang, ui_queue, base_dir=None):
    task.status_code = TaskStatus.FAILED
    task.status = "Failed"
    update_download_status(task.id, "FAILED")
    if base_dir and getattr(task, "_output_file", None):
        clean_empty_directories(task._output_file, base_dir)
    safe_put_ui(ui_queue, ("log", f"[{task.title}] post-processing error: {e}\n"))

def download_single_task(task: DownloadTask, state: AppState, ui_queue, cancel_event) -> None:
    lang = state.current_lang
    if cancel_event.is_set() or task.cancel_event.is_set():
        _handle_cancel(task, lang, ui_queue, state.output_dir)
        return

    _set_downloading_status(task, lang, ui_queue)
    cmd = build_command(task, state.output_dir)
    _log_start(task, cmd, ui_queue)

    try:
        code, saw_http_403, saw_outdated = run_command_stream(cmd, task, state, ui_queue, cancel_event)
        _cleanup_temp_json(task)

        if saw_outdated:
            state.saw_outdated_warning = True
            safe_put_ui(ui_queue, ("toast_outdated", None))

        if cancel_event.is_set() or task.cancel_event.is_set():
            _handle_cancel(task, lang, ui_queue, state.output_dir)
            return

        if code != 0:
            should_retry = (
                saw_http_403
                and task.youtube_403
                and YOUTUBE_FALLBACK_EXTRACTOR_ARGS not in " ".join(cmd)
            )
            if should_retry:
                safe_put_ui(ui_queue, ("log", f"[{task.title}] YouTube 403 Forbidden, triggering TV Client fallback...\n"))
                retry_cmd = append_options_before_urls(cmd, [task.url], ["--extractor-args", YOUTUBE_FALLBACK_EXTRACTOR_ARGS])
                code, saw_http_403, saw_outdated = run_command_stream(retry_cmd, task, state, ui_queue, cancel_event)

        if code == 0:
            output_file = task._output_file
            if output_file and os.path.exists(output_file):
                if task.macro_clips_data:
                    output_file = _process_macro_clips(task, output_file, lang, ui_queue, cancel_event)
                elif (task.clip_enabled or task.export_profile != "Default (No Profile)"):
                    output_file = _process_single_clip(task, output_file, lang, ui_queue, cancel_event)

            if cancel_event.is_set() or task.cancel_event.is_set():
                _handle_cancel(task, lang, ui_queue, state.output_dir)
                return

            _set_completed_status(task, output_file, lang, ui_queue)
        else:
            _set_failed_status(task, code, lang, ui_queue, state.output_dir)

    except Exception as e:
        _handle_exception(task, e, lang, ui_queue, state.output_dir)
    finally:
        _cleanup_temp_json(task)
        safe_put_ui(ui_queue, ("queue_sync", None))

def run_queue_executor(state: AppState, ui_queue, cancel_event) -> None:
    """Processes pending items in parallel utilizing ThreadPoolExecutor based on max_workers."""
    lang = state.current_lang
    state.is_executor_running = True
    refresh_path_env()
    
    # Query pending tasks
    with state._lock:
        tasks_to_run = [
            task for task in state.queue_list
            if task.status_code == TaskStatus.PENDING
        ]
    
    if not tasks_to_run:
        state.is_executor_running = False
        safe_put_ui(ui_queue, ("queue_done", None))
        return

    prevent_sleep()
    try:
        status_message = "İşleniyor" if lang == "tr" else ("Procesando" if lang == "es" else "Processing")
        safe_put_ui(ui_queue, ("status", ("●", "#4f46e5", f"{status_message} (Concurrently)")))

        max_workers = state.preferences.max_workers
        safe_put_ui(ui_queue, ("log", f"[executor] Initiating parallel downloads (max_workers={max_workers}) for {len(tasks_to_run)} tasks...\n"))

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(download_single_task, task, state, ui_queue, task.cancel_event): task
                for task in tasks_to_run
            }
            wait(futures)
    finally:
        allow_sleep()
        state.is_executor_running = False
        safe_put_ui(ui_queue, ("queue_done", None))

def toggle_pause_task(task):
    if not hasattr(task, "is_paused"):
        task.is_paused = False
    task.is_paused = not task.is_paused
    
    # Update status code and status text
    if task.is_paused:
        task.status = "Paused"
        task.status_code = TaskStatus.PAUSED
    else:
        task.status = "Downloading"
        task.status_code = TaskStatus.DOWNLOADING
        
    proc = getattr(task, "_process", None)
    if proc:
        import os
        if os.name == 'nt':
            import ctypes
            try:
                if task.is_paused:
                    ctypes.windll.ntdll.NtSuspendProcess(proc._handle)
                else:
                    ctypes.windll.ntdll.NtResumeProcess(proc._handle)
            except Exception as e:
                print(f"[!] WinAPI Suspend/Resume error: {e}")
        else:
            import signal
            try:
                if task.is_paused:
                    os.kill(proc.pid, signal.SIGSTOP)
                else:
                    os.kill(proc.pid, signal.SIGCONT)
            except Exception as e:
                print(f"[!] POSIX Suspend/Resume error: {e}")
