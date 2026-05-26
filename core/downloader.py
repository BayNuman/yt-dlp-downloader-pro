# core/downloader.py
import os
import re
import sys
import shlex
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, wait

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

    for line in process.stdout:
        # Prefix UI logs with task title for concurrent visibility
        ui_queue.put(("log", f"[{task.title[:18]}...] {line}"))

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
            ui_queue.put(("stats", stats_payload))

        dest_match = dest_re.search(line)
        if dest_match:
            full_path = dest_match.group(1).strip()
            filename = Path(full_path).name
            ui_queue.put(("active_file", (task.id, filename)))
            task._output_file = full_path

        if "HTTP Error 403: Forbidden" in line:
            saw_http_403 = True
        if "version" in line and "older than 90 days" in line:
            saw_outdated_warning = True

    return process.wait(), saw_http_403, saw_outdated_warning

def wait_process_with_timeout(proc, timeout=120) -> int:
    try:
        return proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()  # sweep zombie process
        raise RuntimeError(f"Process timed out after {timeout} seconds")

def _handle_cancel(task, lang, ui_queue):
    task.status_code = TaskStatus.CANCELLED
    task.status = "Cancelled"
    update_download_status(task.id, "CANCELLED")
    ui_queue.put(("toast_cancel", task.title))
    ui_queue.put(("queue_sync", None))

def _set_downloading_status(task, lang, ui_queue):
    task.status_code = TaskStatus.DOWNLOADING
    task.status = "Downloading"
    ui_queue.put(("queue_sync", None))

def _log_start(task, cmd, ui_queue):
    ui_queue.put(("active_file", (task.id, task.title)))
    ui_queue.put(("log", f"\n[queue] Download Started: {task.title}\n"))
    ui_queue.put(("log", f"$ {format_cmd_for_log(cmd)}\n"))
    add_download_record(
        item_id=task.id,
        title=task.title,
        url=task.url,
        format_desc=f"{task.mode} ({task.video_profile if task.mode == 'Video' else task.audio_quality})",
        file_path="",
        status="DOWNLOADING",
        file_size=0,
        duration=int(parse_time_to_seconds(task.duration) or 0)
    )

def _cleanup_temp_json(task):
    temp_json_file = getattr(task, "_temp_info_json", None)
    if temp_json_file and os.path.exists(temp_json_file):
        try:
            os.remove(temp_json_file)
        except Exception:
            pass

def _process_macro_clips(task, output_file, lang, ui_queue, cancel_event) -> str:
    ui_queue.put(("log", f"[{task.title}] Slicing LeetCode 56 Multi-Clips...\n"))
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
            ffmpeg_cmd.extend(["-c:v", "copy", "-c:a", "copy"])

        ffmpeg_cmd.append(str(micro_output_path))

        ui_queue.put(("log", f"[{task.title}] Slicing segment {idx_m+1}/{len(macro_clips)}: {micro_output_path.name}\n"))

        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

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
        wait_process_with_timeout(proc, timeout=300)

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
                duration=int(duration_sec)
            )

    if cancel_event.is_set() or task.cancel_event.is_set():
        return output_file

    try:
        os.remove(input_path)
    except Exception:
        pass
    ret_file = str(input_path.parent / f"{input_path.stem}_clips_generated")

    if task.merge_clips and len(micro_paths) > 1:
        ui_queue.put(("log", f"[{task.title}] Losslessly merging fanned out segments via Concat Demuxer...\n"))
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
                duration=int(sum(mc["end"] - mc["start"] for mc in macro_clips))
            )
    return ret_file

def _process_single_clip(task, output_file, lang, ui_queue, cancel_event) -> str:
    ui_queue.put(("log", f"[{task.title}] Postprocessing clip media...\n"))
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
        ffmpeg_cmd.extend(["-c:v", "copy", "-c:a", "copy"])

    ffmpeg_cmd.append(str(final_path))

    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

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
    wait_process_with_timeout(proc, timeout=600)

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
    update_download_status(task.id, "COMPLETED", file_path=output_file or "", file_size=file_size)
    ui_queue.put(("percent_complete", 1.0))
    ui_queue.put(("toast_success", {"title": task.title, "file_path": output_file or ""}))

def _set_failed_status(task, code, lang, ui_queue):
    task.status_code = TaskStatus.FAILED
    task.status = "Failed"
    update_download_status(task.id, "FAILED")
    ui_queue.put(("toast_error", {"code": code, "title": task.title}))

def _handle_exception(task, e, lang, ui_queue):
    task.status_code = TaskStatus.FAILED
    task.status = "Failed"
    update_download_status(task.id, "FAILED")
    ui_queue.put(("log", f"[{task.title}] post-processing error: {e}\n"))

def download_single_task(task: DownloadTask, state: AppState, ui_queue, cancel_event) -> None:
    lang = state.current_lang
    if cancel_event.is_set() or task.cancel_event.is_set():
        _handle_cancel(task, lang, ui_queue)
        return

    _set_downloading_status(task, lang, ui_queue)
    cmd = build_command(task, state.output_dir)
    _log_start(task, cmd, ui_queue)

    try:
        code, saw_http_403, saw_outdated = run_command_stream(cmd, task, state, ui_queue, cancel_event)
        _cleanup_temp_json(task)

        if saw_outdated:
            state.saw_outdated_warning = True
            ui_queue.put(("toast_outdated", None))

        if cancel_event.is_set() or task.cancel_event.is_set():
            _handle_cancel(task, lang, ui_queue)
            return

        if code != 0:
            should_retry = (
                saw_http_403
                and task.youtube_403
                and YOUTUBE_FALLBACK_EXTRACTOR_ARGS not in " ".join(cmd)
            )
            if should_retry:
                ui_queue.put(("log", f"[{task.title}] YouTube 403 Forbidden, triggering TV Client fallback...\n"))
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
                _handle_cancel(task, lang, ui_queue)
                return

            _set_completed_status(task, output_file, lang, ui_queue)
        else:
            _set_failed_status(task, code, lang, ui_queue)

    except Exception as e:
        _handle_exception(task, e, lang, ui_queue)
    finally:
        _cleanup_temp_json(task)
        ui_queue.put(("queue_sync", None))

def run_queue_executor(state: AppState, ui_queue, cancel_event) -> None:
    """Processes pending items in parallel utilizing ThreadPoolExecutor based on max_workers."""
    lang = state.current_lang
    state.is_executor_running = True
    refresh_path_env()
    
    # Query pending tasks
    tasks_to_run = [
        task for task in state.queue_list
        if task.status_code == TaskStatus.PENDING
    ]
    
    if not tasks_to_run:
        state.is_executor_running = False
        ui_queue.put(("queue_done", None))
        return

    status_message = "İşleniyor" if lang == "tr" else ("Procesando" if lang == "es" else "Processing")
    ui_queue.put(("status", ("●", "#4f46e5", f"{status_message} (Concurrently)")))

    max_workers = state.preferences.max_workers
    ui_queue.put(("log", f"[executor] Initiating parallel downloads (max_workers={max_workers}) for {len(tasks_to_run)} tasks...\n"))

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(download_single_task, task, state, ui_queue, cancel_event): task
            for task in tasks_to_run
        }
        wait(futures)

    state.is_executor_running = False
    ui_queue.put(("queue_done", None))
