# core/downloader.py
import os
import re
import sys
import shlex
import subprocess
from pathlib import Path
from core.app_state import AppState
from core.command_builder import build_command, format_cmd_for_log, YOUTUBE_FALLBACK_EXTRACTOR_ARGS
from core.history import add_download_record, update_download_status
from core.clip import parse_time_to_seconds
from core.env import refresh_path_env

def resolve_ffmpeg_path() -> str:
    """Finds the ffmpeg binary, checking bundled paths or standard locations."""
    # 1. Check if we are running from PyInstaller bundle
    try:
        base_path = sys._MEIPASS
        bundled = os.path.join(base_path, "ffmpeg.exe" if os.name == "nt" else "ffmpeg")
        if os.path.exists(bundled):
            return bundled
    except Exception:
        pass

    # 2. Check local bin directory
    local_bin = Path(".") / "bin" / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    if local_bin.exists():
        return str(local_bin.resolve())

    # 3. Fallback to system path
    return "ffmpeg"

def append_options_before_urls(cmd: list[str], urls: list[str], options: list[str]) -> list[str]:
    if not urls:
        return cmd + options
    option_area = cmd[:-len(urls)]
    url_area = cmd[-len(urls):]
    return option_area + options + url_area

def run_command_stream(cmd: list[str], item_idx: int, state: AppState, ui_queue, cancel_event) -> tuple[int, bool, bool]:
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
    )
    assert process.stdout is not None

    for line in process.stdout:
        ui_queue.put(("log", line))

        # Check if cancel has been requested
        if cancel_event.is_set():
            process.terminate()
            break

        match = progress_re.search(line)
        if match:
            value = max(0.0, min(100.0, float(match.group(1))))
            size_str = match.group(2)
            speed_str = match.group(3)
            eta_str = match.group(4)

            stats_payload = {
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
            ui_queue.put(("active_file", filename))
            # Cache output file path inside item so post-processing knows where it is
            state.queue_list[item_idx]["_output_file"] = full_path

        if "HTTP Error 403: Forbidden" in line:
            saw_http_403 = True
        if "version" in line and "older than 90 days" in line:
            saw_outdated_warning = True

    return process.wait(), saw_http_403, saw_outdated_warning

def run_queue_executor(state: AppState, ui_queue, cancel_event) -> None:
    """Processes each item in the download queue sequentially one by one in a background worker thread."""
    lang = state.current_lang
    state.is_executor_running = True
    
    # Dynamically refresh PATH environment to pick up Deno or Node.js without requiring app/system restart
    refresh_path_env()
    
    while state.current_item_index < len(state.queue_list) and not cancel_event.is_set():
        idx = state.current_item_index
        item = state.queue_list[idx]

        active_downloading_str = "İndiriliyor" if lang == "tr" else ("Descargando" if lang == "es" else "Downloading")
        item["status"] = active_downloading_str
        ui_queue.put(("queue_sync", None))

        # Build command and setup stats
        cmd = build_command(item, state.output_dir)
        ui_queue.put(("active_file", item['title']))
        ui_queue.put(("log", f"\n[queue] Download Started [{idx+1}/{len(state.queue_list)}]: {item['title']}\n"))
        ui_queue.put(("log", f"$ {format_cmd_for_log(cmd)}\n"))
        
        status_message = "İşleniyor" if lang == "tr" else ("Procesando" if lang == "es" else "Processing")
        ui_queue.put(("status", ("●", "#4f46e5", f"{status_message} ({idx+1}/{len(state.queue_list)})")))

        # SQLite History Transitions: Insert or update state as DOWNLOADING
        add_download_record(
            item_id=item["id"],
            title=item["title"],
            url=item["url"],
            format_desc=f"{item['mode']} ({item.get('video_profile', 'mp3')})",
            file_path="",
            status="DOWNLOADING",
            file_size=0,
            duration=int(parse_time_to_seconds(item.get("duration", "0")) or 0)
        )

        try:
            # Run the subprocess downloader
            code, saw_http_403, saw_outdated = run_command_stream(cmd, idx, state, ui_queue, cancel_event)

            # Clean up temporary info-json metadata file if one was injected
            temp_json_file = item.get("_temp_info_json")
            if temp_json_file and os.path.exists(temp_json_file):
                try:
                    os.remove(temp_json_file)
                except Exception:
                    pass

            # Bug Fix 2: Handle Outdated warning state trigger
            if saw_outdated:
                state.saw_outdated_warning = True
                ui_queue.put(("toast_outdated", None))

            if cancel_event.is_set():
                item["status"] = "İptal Edildi" if lang == "tr" else ("Cancelado" if lang == "es" else "Cancelled")
                update_download_status(item["id"], "CANCELLED")
                ui_queue.put(("toast_cancel", item["title"]))
                break

            if code == 0:
                # ----------------- TIME RANGE & EXPORT PROFILE POST-PROCESSING -----------------
                output_file = item.get("_output_file")
                clip_strategy = item.get("clip_strategy", "stream_seek")
                
                # Fetch Selected Profile
                profile_name = item.get("export_profile", "Default (No Profile)")
                from core.profiles import EXPORT_PROFILES
                profile = EXPORT_PROFILES.get(profile_name)
                
                has_clip = item.get("clip_enabled")
                has_profile = profile and profile.name != "Default"
                
                # Check if we have an optimized Macro-Clip with multiple sub-clips (Task 3: LeetCode 56)
                macro_clips = item.get("macro_clips_data")
                
                if macro_clips and output_file and os.path.exists(output_file):
                    ui_queue.put(("log", f"[post-processing] Starting LeetCode 56 Multi-Clip Macro-slicing for {len(macro_clips)} clips...\n"))
                    
                    ffmpeg_bin = resolve_ffmpeg_path()
                    input_path = Path(output_file)
                    macro_start = parse_time_to_seconds(item.get("clip_start", "00:00")) or 0.0
                    
                    micro_paths = []
                    
                    # We slice the macro file into individual micro clips
                    for idx_m, micro in enumerate(macro_clips):
                        micro_start = micro["start"]
                        micro_end = micro["end"]
                        micro_profile_name = micro.get("profile", "Default (No Profile)")
                        micro_profile = EXPORT_PROFILES.get(micro_profile_name)
                        
                        rel_start = max(0.0, micro_start - macro_start)
                        rel_end = max(0.0, micro_end - macro_start)
                        duration_sec = rel_end - rel_start
                        
                        # Dynamically mutate filename to avoid overwrite, append suffix
                        target_ext = micro_profile.ext if (micro_profile and micro_profile.name != "Default") else input_path.suffix.lstrip(".")
                        suffix = micro.get("output_suffix", f"_clip{idx_m+1}")
                        micro_output_path = input_path.parent / f"{input_path.stem}{suffix}.{target_ext}"
                        
                        ffmpeg_cmd = [ffmpeg_bin, "-y", "-ss", str(rel_start), "-to", str(rel_end), "-i", str(input_path)]
                        
                        if micro_profile and micro_profile.name != "Default":
                            ffmpeg_cmd.extend(micro_profile.get_ffmpeg_args(duration_sec))
                        else:
                            ffmpeg_cmd.extend(["-c:v", "copy", "-c:a", "copy"])
                            
                        ffmpeg_cmd.append(str(micro_output_path))
                        
                        ui_queue.put(("log", f"[post-processing] Slicing clip {idx_m+1}/{len(macro_clips)}: {micro_output_path.name}\n"))
                        ui_queue.put(("log", f"$ {' '.join(ffmpeg_cmd)}\n"))
                        
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
                            startupinfo=startupinfo
                        )
                        
                        if proc.stdout:
                            for line in proc.stdout:
                                pass # Keep silent
                        proc.wait()
                        
                        # Add download record in history for each micro clip
                        if micro_output_path.exists():
                            micro_paths.append(str(micro_output_path))
                            add_download_record(
                                item_id=f"{item['id']}_clip{idx_m+1}",
                                title=f"{item['title']} (Clip {idx_m+1})",
                                url=item["url"],
                                format_desc=f"{item['mode']} ({micro_profile_name})",
                                file_path=str(micro_output_path),
                                status="COMPLETED",
                                file_size=os.path.getsize(micro_output_path),
                                duration=int(duration_sec)
                            )
                    
                    # Delete the temporary macro master file
                    try:
                        os.remove(input_path)
                        output_file = str(input_path.parent / f"{input_path.stem}_clips_generated") # placeholder path
                        ui_queue.put(("log", "[post-processing] LeetCode 56 Macro-slicing finished. Cleaned up master temp file.\n"))
                    except Exception as file_err:
                        ui_queue.put(("log", f"[warning] Failed to remove macro master file: {file_err}\n"))

                    # If merge_clips option is active, losslessly concatenate fanned out MicroClips
                    if item.get("merge_clips") and len(micro_paths) > 1:
                        ui_queue.put(("log", "[post-processing] Merging sliced clips losslessly via FFmpeg demuxer...\n"))
                        from core.merger import LosslessMerger
                        merger = LosslessMerger(ffmpeg_bin)
                        
                        # Generate clean merged output path
                        merged_ext = EXPORT_PROFILES[macro_clips[0].get("profile", "Default (No Profile)")].ext if EXPORT_PROFILES.get(macro_clips[0].get("profile")) else input_path.suffix.lstrip(".")
                        merged_output_path = input_path.parent / f"{input_path.stem}_merged.{merged_ext}"
                        
                        success = merger.merge_clips(micro_paths, str(merged_output_path), cleanup=True)
                        if success and merged_output_path.exists():
                            output_file = str(merged_output_path)
                            ui_queue.put(("log", f"[post-processing] Lossless merge finished successfully. Final output: {merged_output_path.name}\n"))
                            
                            # Add a unified history record for the merged file
                            add_download_record(
                                item_id=f"{item['id']}_merged",
                                title=f"{item['title']} (Merged)",
                                url=item["url"],
                                format_desc=f"{item['mode']} (Merged Clips)",
                                file_path=str(merged_output_path),
                                status="COMPLETED",
                                file_size=os.path.getsize(merged_output_path),
                                duration=int(sum(max(0.0, mc["end"] - mc["start"]) for mc in macro_clips))
                            )
                        else:
                            ui_queue.put(("log", "[error] Lossless merging failed.\n"))
                        
                elif (has_clip or has_profile) and output_file and os.path.exists(output_file):
                    ui_queue.put(("log", f"[post-processing] Starting single-pass postprocessing (Clip={has_clip}, Profile={profile_name})...\n"))
                    
                    ffmpeg_bin = resolve_ffmpeg_path()
                    input_path = Path(output_file)
                    
                    # Target path (dynamically mutate output file extension if profile requires it, e.g. converting .mp4 to .gif)
                    target_ext = profile.ext if (profile and has_profile) else input_path.suffix.lstrip(".")
                    final_path = input_path.parent / f"processed_{input_path.stem}.{target_ext}"
                    
                    start_str = item.get("clip_start", "00:00").strip()
                    end_str = item.get("clip_end", "00:00").strip()
                    start = parse_time_to_seconds(start_str) or 0.0
                    end = parse_time_to_seconds(end_str) or 0.0
                    
                    # Compute duration for bitrate allocation
                    duration_sec = (end - start) if has_clip else (parse_time_to_seconds(item.get("duration", "0")) or 10.0)
                    
                    ffmpeg_cmd = [ffmpeg_bin, "-y"]
                    
                    # Add seek/clipping arguments if clip is enabled and it was not pre-trimmed by stream_seek
                    if has_clip and clip_strategy in ("hybrid", "full_trim"):
                        if clip_strategy == "hybrid":
                            # Raw clip buffer was 5s, so start offset is 5.0s (or less if clip started near 0)
                            buffered_start = max(0.0, start - 5.0)
                            offset_start = start - buffered_start
                            offset_end = end - buffered_start
                            ffmpeg_cmd.extend(["-ss", str(offset_start), "-to", str(offset_end)])
                        else: # full_trim
                            ffmpeg_cmd.extend(["-ss", str(start), "-to", str(end)])
                            
                    # Add input file
                    ffmpeg_cmd.extend(["-i", str(input_path)])
                    
                    # Add export profile re-encoding arguments
                    if has_profile:
                        ffmpeg_cmd.extend(profile.get_ffmpeg_args(duration_sec))
                    else:
                        # Lossless fast copy
                        ffmpeg_cmd.extend(["-c:v", "copy", "-c:a", "copy"])
                        
                    # Add output path
                    ffmpeg_cmd.append(str(final_path))
                    
                    ui_queue.put(("log", f"$ {' '.join(ffmpeg_cmd)}\n"))
                    
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
                        startupinfo=startupinfo
                    )
                    
                    # Consume ffmpeg logs to append to terminal
                    if proc.stdout:
                        for line in proc.stdout:
                            ui_queue.put(("log", f"[ffmpeg] {line}"))
                            
                    ffmpeg_code = proc.wait()
                    
                    if ffmpeg_code == 0 and final_path.exists():
                        # Delete the original downloaded file and replace/rename it
                        try:
                            os.remove(input_path)
                            # Rename final path to be our final clean output file
                            clean_output_path = input_path.with_suffix(f".{target_ext}")
                            if final_path != clean_output_path:
                                if os.path.exists(clean_output_path):
                                    os.remove(clean_output_path)
                                os.rename(final_path, clean_output_path)
                            output_file = str(clean_output_path)
                            ui_queue.put(("log", f"[post-processing] Finished successfully. Final Output: {clean_output_path.name}\n"))
                        except Exception as file_err:
                            ui_queue.put(("log", f"[warning] Could not clean up temporary processing files: {file_err}\n"))
                    else:
                        ui_queue.put(("log", f"[error] ffmpeg processing failed with code {ffmpeg_code}\n"))
                        ui_queue.put(("log", f"[error] ffmpeg processing failed with code {ffmpeg_code}\n"))
                
                # Update State to COMPLETED
                item["status"] = "Tamamlandı" if lang == "tr" else ("Completado" if lang == "es" else "Completed")
                file_size = 0
                if output_file and os.path.exists(output_file):
                    file_size = os.path.getsize(output_file)
                
                update_download_status(
                    item["id"],
                    "COMPLETED",
                    file_path=output_file or "",
                    file_size=file_size
                )
                
                ui_queue.put(("percent_complete", 1.0))
                ui_queue.put(("toast_success", {"title": item["title"], "file_path": output_file or ""}))
            else:
                # Check for 403 automatic fallback
                should_retry = (
                    saw_http_403
                    and item.get("youtube_403")
                    and YOUTUBE_FALLBACK_EXTRACTOR_ARGS not in " ".join(cmd)
                )
                if should_retry:
                    ui_queue.put(("log", "[warning] YouTube 403 Forbidden detected, trying TV Client fallback...\n"))
                    retry_cmd = append_options_before_urls(cmd, [item["url"]], ["--extractor-args", YOUTUBE_FALLBACK_EXTRACTOR_ARGS])
                    
                    code, saw_http_403, saw_outdated = run_command_stream(retry_cmd, idx, state, ui_queue, cancel_event)
                    
                    if code == 0:
                        item["status"] = "Tamamlandı" if lang == "tr" else ("Completado" if lang == "es" else "Completed")
                        
                        output_file = item.get("_output_file")
                        file_size = 0
                        if output_file and os.path.exists(output_file):
                            file_size = os.path.getsize(output_file)
                            
                        update_download_status(item["id"], "COMPLETED", file_path=output_file or "", file_size=file_size)
                        ui_queue.put(("percent_complete", 1.0))
                        ui_queue.put(("toast_success", {"title": item["title"], "file_path": output_file or ""}))
                    else:
                        item["status"] = "Hata" if lang == "tr" else ("Error" if lang == "es" else "Error")
                        update_download_status(item["id"], "FAILED")
                        ui_queue.put(("toast_error", {"code": code, "title": item["title"]}))
                else:
                    item["status"] = "Hata" if lang == "tr" else ("Error" if lang == "es" else "Error")
                    update_download_status(item["id"], "FAILED")
                    ui_queue.put(("toast_error", {"code": code, "title": item["title"]}))

        except Exception as e:
            item["status"] = "Hata" if lang == "tr" else ("Error" if lang == "es" else "Error")
            update_download_status(item["id"], "FAILED")
            ui_queue.put(("log", f"[error] {e}\n"))

        ui_queue.put(("queue_sync", None))
        state.current_item_index += 1

    state.is_executor_running = False
    ui_queue.put(("queue_done", None))
