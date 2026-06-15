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
import logging
import signal
from typing import NamedTuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, wait

class CommandResult(NamedTuple):
    returncode: int
    saw_http_403: bool
    saw_outdated: bool

# Windows Sleep prevention constants
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001

def prevent_sleep():
    if os.name == 'nt':
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
        except Exception as e:
            logging.error(f"[Sleep Prevention] Failed to prevent sleep: {e}")

def allow_sleep():
    if os.name == 'nt':
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
        except Exception as e:
            logging.error(f"[Sleep Prevention] Failed to restore sleep state: {e}")

def get_subprocess_encoding() -> str:
    import locale
    if os.name == 'nt':
        try:
            return locale.getpreferredencoding(False) or "utf-8"
        except Exception:
            return "utf-8"
    return "utf-8"

def safe_put_ui(ui_queue, item):
    try:
        # Bloklanmaya veya timeout'a kesinlikle izin yok
        ui_queue.put_nowait(item)
    except queue.Full:
        # Load Shedding: UI yetişemiyorsa paketi düşür (drop).
        # Progress stat'ları veya terminal logları anlıktır, bir sonraki tick'te yenisi gelir.
        # Worker thread asla UI'ı beklememeli.
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

def resume_subprocess(proc):
    try:
        if os.name == 'nt':
            import ctypes
            ctypes.windll.ntdll.NtResumeProcess(proc._handle)
        else:
            import signal
            os.kill(proc.pid, signal.SIGCONT)
    except Exception:
        pass

def kill_all_active_subprocesses():
    with active_subprocess_lock:
        for proc in list(active_subprocesses):
            try:
                # Safe resume first to ensure it processes termination signals on POSIX/Windows
                resume_subprocess(proc)
                proc.terminate()
                proc.wait(timeout=1)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        active_subprocesses.clear()

from core.waveform import enqueue_waveform_generation
from core.utils import clean_empty_directories, extract_video_id

def _on_waveform_done(task_id, png_path, ui_queue):
    update_download_status(task_id, "COMPLETED", thumbnail_path=png_path)
    safe_put_ui(ui_queue, ("queue_sync", None))

# Core state & DB models
from core.app_state import AppState, DownloadTask, TaskStatus
from core.command_builder import build_command, format_cmd_for_log, YOUTUBE_FALLBACK_EXTRACTOR_ARGS
from core.history import add_download_record, update_download_status
from core.clip import parse_time_to_seconds

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

def run_command_stream(cmd: list[str], task: DownloadTask, state: AppState, ui_queue, cancel_event) -> CommandResult:
    progress_re = re.compile(
        r"\[download\]\s+(\d{1,3}(?:\.\d+)?)%\s+of\s+(~?\d+(?:\.\d+)?\w+)\s+at\s+(\d+(?:\.\d+)?\w+/s|Unknown speed)\s+ETA\s+(\d{2}:\d{2}|\w+)"
    )
    dest_re = re.compile(r"\[download\]\s+Destination:\s+(.+)")
    already_re = re.compile(r"\[download\]\s+(.+)\s+has already been downloaded")
    merge_re = re.compile(r"\[Merger\]\s+Merging\s+formats\s+into\s+\"(.+?)\"")
    post_re = re.compile(r"\[(ExtractAudio|RecodeVideo|Metadata)\]\s+(?:Destination:\s+|\w+\s+to\s+\")(.+?)\"?$")

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
        encoding=get_subprocess_encoding(),
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

            merge_match = merge_re.search(line)
            if merge_match:
                full_path = merge_match.group(1).strip()
                filename = Path(full_path).name
                safe_put_ui(ui_queue, ("active_file", (task.id, filename)))
                task._output_file = full_path

            post_match = post_re.search(line)
            if post_match:
                full_path = post_match.group(2).strip()
                filename = Path(full_path).name
                safe_put_ui(ui_queue, ("active_file", (task.id, filename)))
                task._output_file = full_path

            if "HTTP Error 403: Forbidden" in line:
                saw_http_403 = True
            if "version" in line and "older than 90 days" in line:
                saw_outdated_warning = True

        return CommandResult(
            returncode=process.wait(),
            saw_http_403=saw_http_403,
            saw_outdated=saw_outdated_warning
        )
    finally:
        unregister_active_subprocess(process)

def wait_process_with_timeout(proc, timeout=120) -> int:
    try:
        return proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()  # sweep zombie process
        raise RuntimeError(f"Process timed out after {timeout} seconds")

# clean_empty_directories is now imported from core.utils

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

def _apply_clip_profile(task, ffmpeg_bin: str, input_path: Path, output_path: Path, 
                        start_offset: float, end_offset: float, profile, 
                        precise_override: bool = False, timeout: int = 600) -> bool:
    """
    Helper function to apply seeking, re-encoding, and profiles to a clip segment via FFmpeg.
    """
    duration_sec = end_offset - start_offset
    ffmpeg_cmd = [ffmpeg_bin, "-y", "-ss", str(start_offset), "-to", str(end_offset), "-i", str(input_path)]

    if profile and profile.name != "Default":
        ffmpeg_cmd.extend(profile.get_ffmpeg_args(duration_sec))
    else:
        # Smart Transcoding: Re-encode video+audio if Precise Cut is enabled
        if precise_override:
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

    ffmpeg_cmd.append(str(output_path))

    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    proc = None
    try:
        proc = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            startupinfo=startupinfo,
            shell=False,
        )
        register_active_subprocess(proc)
        wait_process_with_timeout(proc, timeout=timeout)
    finally:
        if proc:
            unregister_active_subprocess(proc)

    return proc is not None and proc.returncode == 0 and output_path.exists()

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

        safe_put_ui(ui_queue, ("log", f"[{task.title}] Slicing segment {idx_m+1}/{len(macro_clips)}: {micro_output_path.name}\n"))

        success = _apply_clip_profile(
            task=task,
            ffmpeg_bin=ffmpeg_bin,
            input_path=input_path,
            output_path=micro_output_path,
            start_offset=rel_start,
            end_offset=rel_end,
            profile=micro_profile,
            precise_override=micro.get("clip_precise") or getattr(task, "clip_precise", False),
            timeout=300
        )

        if success:
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
        merged_ext = EXPORT_PROFILES[macro_clips[0].get("profile", "Default (No Profile)")].ext if EXPORT_PROFILES.get(macro_clips[0].get("profile")) else input_path.suffix.lstrip(".")
        merged_output_path = input_path.parent / f"{input_path.stem}_merged.{merged_ext}"

        # Homogeneity Check: Verify all clips have the exact same export profile
        profiles_used = {mc.get("profile", "Default (No Profile)") for mc in macro_clips}
        is_homogeneous = len(profiles_used) == 1

        if is_homogeneous:
            safe_put_ui(ui_queue, ("log", f"[{task.title}] Profiller eşleşti. Concat Demuxer ile kayıpsız birleştiriliyor...\n"))
            from core.merger import LosslessMerger
            merger = LosslessMerger(ffmpeg_bin)
            success = merger.merge_clips(
                micro_paths,
                str(merged_output_path),
                cleanup=True,
                register_proc_cb=register_active_subprocess,
                unregister_proc_cb=unregister_active_subprocess
            )
        else:
            safe_put_ui(ui_queue, ("log", f"[{task.title}] Heterojen profiller tespit edildi. Filtreleme ile yeniden kodlanıyor (Transcode Merge)...\n"))
            transcode_cmd = [ffmpeg_bin, "-y"]
            for mp in micro_paths:
                transcode_cmd.extend(["-i", mp])
            
            n = len(micro_paths)
            if task.mode == "audio":
                filter_str = "".join([f"[{i}:a]" for i in range(n)]) + f"concat=n={n}:v=0:a=1[a]"
                transcode_cmd.extend([
                    "-filter_complex", filter_str,
                    "-map", "[a]",
                    "-c:a", "aac", "-b:a", "192k",
                    str(merged_output_path)
                ])
            else:
                filter_str = "".join([f"[{i}:v][{i}:a]" for i in range(n)]) + f"concat=n={n}:v=1:a=1[v][a]"
                transcode_cmd.extend([
                    "-filter_complex", filter_str,
                    "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                    "-c:a", "aac", "-b:a", "192k",
                    str(merged_output_path)
                ])

            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            process = subprocess.Popen(
                transcode_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                startupinfo=startupinfo,
                text=True,
                encoding=get_subprocess_encoding(),
                errors="replace"
            )
            
            register_active_subprocess(process)
            try:
                stdout_data, _ = process.communicate()
            finally:
                unregister_active_subprocess(process)
                
            success = merged_output_path.exists() and process.returncode == 0
            
            if success:
                for mp in micro_paths:
                    try:
                        os.remove(mp)
                    except:
                        pass

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

    if task.clip_enabled and task.clip_strategy in ("hybrid", "full_trim"):
        if task.clip_strategy == "hybrid":
            buffered_start = max(0.0, start - 5.0)
            rel_start = start - buffered_start
            rel_end = end - buffered_start
        else:
            rel_start = start
            rel_end = end
    else:
        rel_start = 0.0
        rel_end = duration_sec

    success = _apply_clip_profile(
        task=task,
        ffmpeg_bin=ffmpeg_bin,
        input_path=input_path,
        output_path=final_path,
        start_offset=rel_start,
        end_offset=rel_end,
        profile=profile,
        precise_override=getattr(task, "clip_precise", False),
        timeout=600
    )

    if success:
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

def resolve_actual_file_path(output_file: str, url: str) -> str:
    if not output_file:
        return ""
    if os.path.exists(output_file):
        return output_file
        
    # If file doesn't exist directly (e.g., due to Windows CP1254 character set conversions or unicode replacement slashes like ⧸),
    # let's find a file in the same directory that has the exact video ID in its name.
    # To prevent collisions in concurrent downloads (e.g. video and audio of the same ID), we normalize names for comparison.
    try:
        path = Path(output_file)
        parent = path.parent
        if not parent.exists():
            return output_file
            
        # Extract video ID from URL
        video_id = extract_video_id(url)
        if not video_id:
            return output_file
            
        # Helper to normalize string names (keep alphanumeric only)
        expected_norm_no_ext = re.sub(r'[^a-zA-Z0-9]', '', path.stem).lower()
        
        # 1. First Pass: Exact extension match + normalized stem match
        for child in parent.iterdir():
            if child.is_file() and video_id in child.name:
                if child.suffix.lower() == path.suffix.lower():
                    child_norm_no_ext = re.sub(r'[^a-zA-Z0-9]', '', child.stem).lower()
                    if child_norm_no_ext == expected_norm_no_ext:
                        return str(child)
                        
        # 2. Second Pass: Allow different media extension + normalized stem match (e.g. merged to .mkv instead of .mp4)
        MEDIA_SUFFIXES = {".mp4", ".mkv", ".webm", ".mp3", ".m4a", ".aac"}
        for child in parent.iterdir():
            if child.is_file() and video_id in child.name:
                if child.suffix.lower() in MEDIA_SUFFIXES:
                    child_norm_no_ext = re.sub(r'[^a-zA-Z0-9]', '', child.stem).lower()
                    if child_norm_no_ext == expected_norm_no_ext:
                        return str(child)
                        
        # 3. Third Pass: Legacy Fallback in case name was severely truncated
        for child in parent.iterdir():
            if child.is_file() and video_id in child.name:
                if child.suffix.lower() == path.suffix.lower():
                    return str(child)
                    
        for child in parent.iterdir():
            if child.is_file() and video_id in child.name:
                if child.suffix.lower() in MEDIA_SUFFIXES:
                    return str(child)
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
        result = run_command_stream(cmd, task, state, ui_queue, cancel_event)
        _cleanup_temp_json(task)

        if result.saw_outdated:
            state.saw_outdated_warning = True
            safe_put_ui(ui_queue, ("toast_outdated", None))

        if cancel_event.is_set() or task.cancel_event.is_set():
            _handle_cancel(task, lang, ui_queue, state.output_dir)
            return

        if result.returncode != 0:
            should_retry = (
                result.saw_http_403
                and task.youtube_403
                and YOUTUBE_FALLBACK_EXTRACTOR_ARGS not in " ".join(cmd)
            )
            if should_retry:
                safe_put_ui(ui_queue, ("log", f"[{task.title}] YouTube 403 Forbidden, triggering TV Client fallback...\n"))
                retry_cmd = append_options_before_urls(cmd, [task.url], ["--extractor-args", YOUTUBE_FALLBACK_EXTRACTOR_ARGS])
                result = run_command_stream(retry_cmd, task, state, ui_queue, cancel_event)

        if result.returncode == 0:
            output_file = task._output_file
            
            # Resolve actual physical path (fixes Windows double-spaces and Unicode slashes ⧸ cp1254 mismatches)
            output_file = resolve_actual_file_path(output_file, task.url)
            
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
            _set_failed_status(task, result.returncode, lang, ui_queue, state.output_dir)

    except Exception as e:
        _handle_exception(task, e, lang, ui_queue, state.output_dir)
    finally:
        _cleanup_temp_json(task)
        safe_put_ui(ui_queue, ("queue_sync", None))

def run_queue_executor(state: AppState, ui_queue, cancel_event) -> None:
    """Processes pending items in parallel utilizing ThreadPoolExecutor based on max_workers."""
    lang = state.current_lang
    state.is_executor_running = True
    
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
    """
    Toggles the pause/resume state of a download task.
    Note: This suspends/resumes the external child process (the yt-dlp executable subprocess)
    at the OS level (using NtSuspendProcess on Windows and SIGSTOP on Unix). It does NOT
    suspend python worker threads inside our process, avoiding TCP socket corruptions or thread deadlocks.
    """
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
        if os.name == 'nt':
            try:
                if task.is_paused:
                    ctypes.windll.ntdll.NtSuspendProcess(proc._handle)
                else:
                    ctypes.windll.ntdll.NtResumeProcess(proc._handle)
            except Exception as e:
                logging.error(f"[!] WinAPI Suspend/Resume error: {e}")
        else:
            try:
                if task.is_paused:
                    os.kill(proc.pid, signal.SIGSTOP)
                else:
                    os.kill(proc.pid, signal.SIGCONT)
            except Exception as e:
                logging.error(f"[!] POSIX Suspend/Resume error: {e}")
