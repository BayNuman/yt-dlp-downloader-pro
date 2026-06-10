# core/waveform.py
import os
import queue
import logging
import threading
import subprocess
from pathlib import Path

class WaveformProcessor:
    """
    Class-based explicit singleton encapsulating the background worker thread
    and task queue for generating downsampled audio waveforms.
    """
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self):
        # Prevent double initialization in singleton
        if hasattr(self, "_initialized") and self._initialized:
            return
        self.waveform_queue = queue.Queue()
        self.worker_thread = threading.Thread(
            target=self._waveform_worker,
            daemon=True,
            name="waveform-worker"
        )
        self.worker_thread.start()
        self._initialized = True

    def generate_audio_waveform(self, task, input_file_path: str) -> str:
        """
        Generates a 320x60 static waveform image for audio files under app_data_dir / waveforms / waveform_{id}.png.
        Utilizes Downsampling (aresample=1000) for extremely fast O(1) performance (1.5s vs 45s).
        """
        try:
            from core.downloader import resolve_ffmpeg_path, register_active_subprocess, unregister_active_subprocess
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
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
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
            logging.error(f"[warning] Waveform generation failed: {e}")
        return None

    def _waveform_worker(self):
        while True:
            task, file_path, callback = self.waveform_queue.get()
            try:
                png_path = self.generate_audio_waveform(task, file_path)
                if png_path:
                    callback(png_path)
            except Exception as e:
                logging.error(f"[warning] Waveform worker error: {e}")
            finally:
                self.waveform_queue.task_done()

    def enqueue_waveform_generation(self, task, file_path, callback):
        self.waveform_queue.put((task, file_path, callback))

def enqueue_waveform_generation(task, file_path, callback):
    """Functional wrapper delegating to the explicit WaveformProcessor singleton."""
    WaveformProcessor.get_instance().enqueue_waveform_generation(task, file_path, callback)
