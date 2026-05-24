# core/merger.py
import subprocess
import os
import tempfile
from pathlib import Path

class LosslessMerger:
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path

    def merge_clips(self, clip_paths: list[str], output_path: str, cleanup: bool = False) -> bool:
        if len(clip_paths) < 2:
            print("[Merge Engine] At least 2 clips are required to perform merge.")
            return False

        working_dir = Path(output_path).parent.resolve()
        fd, list_file_path = tempfile.mkstemp(dir=str(working_dir), suffix=".txt", text=True)
        
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                for clip in clip_paths:
                    try:
                        # Calculate path relative to the working directory (output folder)
                        rel_path = os.path.relpath(clip, start=working_dir).replace('\\', '/')
                    except ValueError:
                        # Fallback to absolute path on cross-drive scenarios on Windows
                        rel_path = os.path.abspath(clip).replace('\\', '/')
                    # Safe quoting for ffmpeg concat demuxer format
                    rel_path = rel_path.replace("'", "\\'")
                    f.write(f"file '{rel_path}'\n")

            # Convert output path relative to working directory
            try:
                rel_output = os.path.relpath(output_path, start=working_dir).replace('\\', '/')
            except ValueError:
                rel_output = os.path.abspath(output_path).replace('\\', '/')
            
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", list_file_path,
                "-c", "copy",
                rel_output
            ]

            print(f"[Merge Engine] Starting demux concatenation of {len(clip_paths)} clips in {working_dir}...")
            
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                startupinfo=startupinfo,
                cwd=str(working_dir),
                shell=False
            )

            if result.returncode != 0:
                print(f"[Merge Engine] FFmpeg demux failed with returncode {result.returncode}:\n{result.stderr}")
                return False

            print(f"[Merge Engine] Finished successfully: {output_path}")

            if cleanup:
                self._cleanup_clips(clip_paths)

            return True

        except Exception as e:
            print(f"[Merge Engine] Unexpected failure: {e}")
            return False

        finally:
            if os.path.exists(list_file_path):
                try:
                    os.remove(list_file_path)
                except Exception:
                    pass

    def _cleanup_clips(self, clip_paths: list[str]):
        for clip in clip_paths:
            try:
                if os.path.exists(clip):
                    os.remove(clip)
            except Exception as e:
                print(f"[Merge Engine] Cleanup failed for {clip}: {e}")
