# core/controller.py
import re
import os
import uuid
import threading
import queue
import dataclasses
from pathlib import Path
from core.app_state import AppState, DownloadTask, TaskStatus
from core.services import fetch_video_metadata
from core.clip import parse_time_to_seconds, format_seconds_to_mmss, decide_clip_strategy

class AppController:
    """
    Presenter/Controller layer coordinating the business logic, service layer, 
    and GUI AppState model.
    """
    def __init__(self, state: AppState):
        self.state = state
        self._lock = threading.Lock()

    def extract_video_id(self, url: str) -> str:
        patterns = [
            r"(?:v=|\/v\/|embed\/|shorts\/|youtu\.be\/|\/embed\/|\/shorts\/)([a-zA-Z0-9_-]{11})",
            r"(?:\/shorts\/|youtu\.be\/|v\/|embed\/)([a-zA-Z0-9_-]{11})"
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return ""

    def fetch_metadata_async(self, url: str, cookies_file: str, browser_cookies: str, scratch_dir: Path, app_data_dir: Path, on_success, on_error):
        """Dispatches video metadata extraction to a background thread and fires callbacks."""
        def run():
            try:
                metadata = fetch_video_metadata(
                    url=url,
                    cookies_file=cookies_file,
                    browser_cookies=browser_cookies,
                    scratch_dir=scratch_dir,
                    app_data_dir=app_data_dir
                )
                on_success(metadata)
            except Exception as e:
                on_error(str(e))

        threading.Thread(target=run, daemon=True, name="metadata-fetcher").start()

    def check_duplicate(self, url: str, item_cfg: dict) -> tuple[bool, str, str]:
        """
        Runs a 3-tier check (RAM Active Queue, Database History, and Disk Presence) 
        to detect if the video has already been queued or downloaded.
        Returns: (is_duplicate, title, format_description)
        """
        video_id = self.extract_video_id(url)
        
        # Tier A: RAM check (Active queue)
        for task in self.state.queue_list:
            if task.url == url or (video_id and video_id in task.url):
                return True, task.title, f"{task.mode} ({task.video_profile if task.mode == 'Video' else task.audio_quality})"
                
        # Tier B: Database check
        from core.history import find_completed_download_in_db
        format_desc = f"{item_cfg.get('mode', 'Video')} ({item_cfg.get('video_profile', 'Custom') if item_cfg.get('mode', 'Video') == 'Video' else item_cfg.get('audio_quality', 'Dengeli (192K)')})"
        record = find_completed_download_in_db(video_id, url, format_desc)
        if record:
            # Tier C: Physical presence check on disk
            file_path = record.get("file_path", "")
            if file_path and os.path.exists(file_path):
                return True, record.get("title", "Video"), record.get("format", "")
            else:
                ext = item_cfg.get("video_container", "mp4") if item_cfg.get("mode", "Video") == "Video" else item_cfg.get("audio_format", "mp3")
                possible_paths = [
                    os.path.join(self.state.output_dir, f"{record.get('title')}.{ext}"),
                    os.path.join(self.state.output_dir, f"{record.get('title')} [{video_id}].{ext}"),
                    os.path.join(self.state.output_dir, f"{record.get('title')}-{video_id}.{ext}")
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        return True, record.get("title", "Video"), record.get("format", "")
                        
        return False, "", ""

    def validate_and_add_tasks(self, url: str, item_cfg: dict, multi_clips: list, lang: str) -> tuple[bool, str, int]:
        """
        Validates the configuration and adds corresponding DownloadTask instances 
        to the state queue list.
        Returns: (success_bool, message_str, added_count)
        """
        valid_task_fields = {f.name for f in dataclasses.fields(DownloadTask)}
        base_cfg = {k: v for k, v in item_cfg.items() if k in valid_task_fields}

        # Headless Channel Rules Engine
        if base_cfg.get("options_source") == "Default" and self.state.current_video_info and not self.state.is_batch_mode:
            ch_id = self.state.current_video_info.get("channel_id")
            if ch_id:
                from core.history import get_channel_rule
                rule = get_channel_rule(ch_id)
                if rule and rule.get("settings_dict"):
                    base_cfg.update(rule["settings_dict"])
                    base_cfg["options_source"] = "Default"

        # Decide seek strategy if clipping is enabled
        clip_strategy = "stream_seek"
        if base_cfg.get("clip_enabled") and self.state.current_video_info:
            start = parse_time_to_seconds(base_cfg.get("clip_start", "00:00")) or 0.0
            end = parse_time_to_seconds(base_cfg.get("clip_end", "00:00")) or 0.0
            clip_strategy = decide_clip_strategy(self.state.current_video_info, start, end)

        added_count = 0
        
        # Batch Mode vs Single Mode
        if self.state.is_batch_mode:
            with self.state._lock:
                for raw_url in self.state.batch_urls:
                    if raw_url.startswith(("http://", "https://")):
                        item_id = uuid.uuid4().hex
                        task_params = {
                            "id": item_id,
                            "url": raw_url,
                            "title": f"Batch Link [{item_id[:6]}]",
                            "duration": "00:00",
                            "preset": base_cfg.get("video_profile", "Custom"),
                            "status": "Bekliyor" if lang == "tr" else ("Esperando" if lang == "es" else "Waiting"),
                            "clip_strategy": clip_strategy
                        }
                        task_params.update(base_cfg)
                        task = DownloadTask(**task_params)
                        self.state.queue_list.append(task)
                        added_count += 1
            return True, "", added_count
            
        else:
            # Single mode
            title_base = self.state.current_video_info.get("title", "Video Title") if self.state.current_video_info else "Downloading video"
            duration_total = self.state.current_video_info.get("duration", 0) if self.state.current_video_info else 0
            duration = format_seconds_to_mmss(duration_total)
            
            if multi_clips:
                from core.clip import MicroClip, optimize_clip_intervals
                micro_list = []
                for i, c in enumerate(multi_clips):
                    micro_list.append(MicroClip(
                        id=f"clip_{i+1}",
                        start=c["start"],
                        end=c["end"],
                        export_profile=c["profile"],
                        output_name=f"_clip{i+1}"
                    ))
                
                # LeetCode 56 Greedy Merging
                macro_list = optimize_clip_intervals(micro_list, threshold_sec=30.0)
                
                with self.state._lock:
                    for idx_macro, macro in enumerate(macro_list):
                        item_id = uuid.uuid4().hex
                        macro_start_str = format_seconds_to_mmss(macro.start)
                        macro_end_str = format_seconds_to_mmss(macro.end)
                        
                        macro_item_params = {
                            "id": item_id,
                            "url": url,
                            "preset": base_cfg.get("video_profile", "Custom"),
                            "status": "Bekliyor" if lang == "tr" else ("Esperando" if lang == "es" else "Waiting"),
                            "status_code": TaskStatus.PENDING,
                            "title": f"{title_base} [Part {idx_macro+1}]",
                            "duration": f"{macro_start_str}-{macro_end_str}",
                            "clip_enabled": True,
                            "clip_start": macro_start_str,
                            "clip_end": macro_end_str,
                            "clip_strategy": decide_clip_strategy(self.state.current_video_info, macro.start, macro.end)
                        }
                        
                        macro_item_params.update({k: v for k, v in base_cfg.items() if k not in macro_item_params})
                        
                        # Pack target micro-clips inside macro task metadata so downloader knows how to slice them later
                        macro_item_params["_micro_clips"] = [
                            {"start": m.start, "end": m.end, "profile": m.export_profile, "name": m.output_name}
                            for m in macro.sub_clips
                        ]
                        
                        task = DownloadTask(**macro_item_params)
                        self.state.queue_list.append(task)
                        added_count += 1
            else:
                # Normal single download
                item_id = uuid.uuid4().hex
                task_params = {
                    "id": item_id,
                    "url": url,
                    "title": title_base,
                    "duration": duration,
                    "preset": base_cfg.get("video_profile", "Custom"),
                    "status": "Bekliyor" if lang == "tr" else ("Esperando" if lang == "es" else "Waiting"),
                    "status_code": TaskStatus.PENDING,
                    "clip_strategy": clip_strategy
                }
                task_params.update({k: v for k, v in base_cfg.items() if k not in task_params})
                
                task = DownloadTask(**task_params)
                with self.state._lock:
                    self.state.queue_list.append(task)
                added_count += 1
                
            return True, "", added_count
