# core/merger.py
import subprocess
import os
import tempfile
from pathlib import Path

class LosslessMerger:
    """Combines multiple sliced audio/video clips of the same origin losslessly using FFmpeg Concat Demuxer."""
    
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path

    def merge_clips(self, clip_paths: list[str], output_path: str, cleanup: bool = False) -> bool:
        """
        Concatenates all clip_paths into output_path using zero re-encoding stream copies.
        Returns True on success, False otherwise.
        """
        if len(clip_paths) < 2:
            print("[Merge Engine] At least 2 clips are required to perform merge.")
            return False

        # Create temporary file to store concat list.
        # delete=False is used because outside FFmpeg processes need to read it.
        fd, list_file_path = tempfile.mkstemp(suffix=".txt", text=True)
        
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                for clip in clip_paths:
                    # Critical Safety Guard: Windows paths must use forward slashes.
                    # Otherwise, FFmpeg will read '\U' or '\D' as escapes and crash with "file not found"!
                    safe_path = str(Path(clip).resolve()).replace('\\', '/')
                    
                    # Concat demuxer syntax: file 'path_to_file'
                    # Escape any single quotes inside filename to prevent demuxer injection crashes
                    safe_path = safe_path.replace("'", r"'\''")
                    f.write(f"file '{safe_path}'\n")

            # Construct Demuxer Command:
            # -f concat: force Demuxer
            # -safe 0: disable safety protocols to allow absolute hardware paths
            # -c copy: lossless fast copy, no video/audio decoding or re-encoding!
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", list_file_path,
                "-c", "copy",
                output_path
            ]

            print(f"[Merge Engine] Starting demux concatenation of {len(clip_paths)} clips...")
            
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
                startupinfo=startupinfo
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
            # Garbage-collect temp list file under all circumstances to prevent memory/temp leaks
            if os.path.exists(list_file_path):
                try:
                    os.remove(list_file_path)
                except Exception:
                    pass

    def _cleanup_clips(self, clip_paths: list[str]):
        """Discards individual sliced clip components post merge."""
        for clip in clip_paths:
            try:
                if os.path.exists(clip):
                    os.remove(clip)
            except Exception as e:
                print(f"[Merge Engine] Cleanup failed for {clip}: {e}")
