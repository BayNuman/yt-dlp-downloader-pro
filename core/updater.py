# core/updater.py
import urllib.request
import urllib.error
import json
import threading
import yt_dlp

class UpdateChecker:
    """Schedules background checks to query PyPI repository releases for the yt-dlp package."""
    
    def __init__(self, ui_callback):
        """
        ui_callback: Function to invoke inside UI thread when an upgrade is found.
                     Prototype: callback(current_version_str, latest_version_str)
        """
        self.ui_callback = ui_callback
        self.pypi_url = "https://pypi.org/pypi/yt-dlp/json"

    def check_in_background(self):
        """Spawns a daemon worker thread to prevent UI freezing on slow networks."""
        thread = threading.Thread(target=self._network_task, daemon=True)
        thread.start()

    def _network_task(self):
        try:
            # 1. Fetch current local package version
            current_version = yt_dlp.version.__version__
            
            # 2. Query PyPI JSON endpoint (limit socket connect timeouts to 3s)
            req = urllib.request.Request(self.pypi_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3.0) as response:
                data = json.loads(response.read().decode('utf-8'))
                latest_version = data["info"]["version"]

            # 3. Numeric comparisons (split release dates, e.g. '2024.03.10' -> (2024, 3, 10))
            current_tuple = tuple(map(int, current_version.split('.')))
            latest_tuple = tuple(map(int, latest_version.split('.')))

            if latest_tuple > current_tuple:
                # Upgrade found! Dispatch thread-safe callback
                self.ui_callback(current_version, latest_version)

        except (urllib.error.URLError, json.JSONDecodeError, ValueError, Exception) as e:
            # Critically Important: Fail silently on socket/parse errors!
            # Never throw popup error dialogs on internet disconnects at launch.
            print(f"[Updater] Silently ignored network check failure: {e}")
            pass
