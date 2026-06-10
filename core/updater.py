# core/updater.py
import urllib.request
import urllib.error
import json
import threading
import hashlib
from dataclasses import dataclass
import yt_dlp

@dataclass
class UpdatePayload:
    """Strongly-typed data container representing an update check result."""
    current_version: str
    latest_version: str
    download_url: str = None
    sha256: str = None
    action: str = "upgrade"  # "upgrade" or "downgrade"
    is_fallback: bool = False

def calculate_sha256(file_path: str) -> str:
    """Computes the SHA-256 checksum of a local file in memory-efficient chunks."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"[Updater] Failed to compute file hash: {e}")
        return ""

class UpdateChecker:
    """Schedules background update checks, routing query streams through a two-tiered fallback pipeline."""
    
    def __init__(self, ui_callback):
        """
        ui_callback: Function to invoke inside UI thread when an update/rollback action is detected.
                     Prototype: callback(payload: UpdatePayload)
        """
        self.ui_callback = ui_callback
        self.bff_url = "https://api.baynuman.com/v1/update/desktop"
        self.pypi_url = "https://pypi.org/pypi/yt-dlp/json"

    def check_in_background(self):
        """Spawns a background daemon thread to perform update queries without locking the GUI thread."""
        thread = threading.Thread(target=self._network_task, daemon=True, name="update-checker")
        thread.start()

    def _network_task(self):
        current_version = yt_dlp.version.__version__
        
        # --- TIER 1: Unified Update Broker BFF ---
        try:
            print("[Updater] Tier 1: Querying custom Update Broker BFF...")
            req = urllib.request.Request(self.bff_url, headers={'User-Agent': 'yt-dlp-Pro-Desktop'})
            with urllib.request.urlopen(req, timeout=3.0) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                latest_version = data.get("validated_version", "")
                download_url = data.get("download_url", None)
                expected_sha256 = data.get("sha256", None)
                action = data.get("action", "upgrade")
                
                if latest_version and latest_version != current_version:
                    # Deterministic update/rollback detected!
                    payload = UpdatePayload(
                        current_version=current_version,
                        latest_version=latest_version,
                        download_url=download_url,
                        sha256=expected_sha256,
                        action=action,
                        is_fallback=False
                    )
                    self.ui_callback(payload)
                    return  # Early exit on successful Tier 1 resolution!

        except Exception as e:
            # Catch all DNS resolution, timeout, and response parse errors silently
            print(f"[Updater] Tier 1 failed or timed out: {e}. Transitioning to Tier 2 (Plan B Fallback)...")
            
        # --- TIER 2: Plan B Official PyPI Fallback ---
        try:
            req = urllib.request.Request(self.pypi_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3.0) as response:
                data = json.loads(response.read().decode('utf-8'))
                latest_version = data["info"]["version"]
                
            try:
                current_tuple = tuple(int(x) for x in current_version.split('.') if x.isdigit())
                latest_tuple = tuple(int(x) for x in latest_version.split('.') if x.isdigit())
            except Exception:
                return

            if latest_tuple > current_tuple:
                # Official upgrade found!
                payload = UpdatePayload(
                    current_version=current_version,
                    latest_version=latest_version,
                    download_url=None, # Falls back to standard pip install
                    sha256=None,
                    action="upgrade",
                    is_fallback=True
                )
                self.ui_callback(payload)

        except Exception as fallback_err:
            print(f"[Updater] Tier 2 fallback query failed: {fallback_err}. Update check aborted.")
            pass

def execute_update(payload: UpdatePayload, scratch_dir: str) -> tuple[bool, str]:
    """
    Executes the update/downgrade process in a background-safe service layer.
    Verifies cryptographic hashes (SHA-256) of downloaded update package.
    Returns: (success_bool, message_str)
    """
    import sys
    import os
    import subprocess
    import urllib.request
    
    if getattr(sys, "frozen", False):
        # Standalone portable EXE build doesn't support pip upgrades
        return False, "Self-updates are not supported in the standalone portable version. Please download the latest version from GitHub!"

    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW

    # If we don't have a download URL (Plan B Fallback / PyPI), do standard pip upgrade
    if payload.is_fallback or not payload.download_url:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-U", "yt-dlp"],
                capture_output=True,
                creationflags=creationflags,
                shell=False
            )
            success = (result.returncode == 0)
            msg = "Fallback pip upgrade finished." if success else result.stderr.decode("utf-8", errors="replace")
            return success, msg
        except Exception as e:
            return False, str(e)

    # Tier 1 Custom Update Broker Flow
    try:
        # 1. Download target archive
        temp_filename = f"yt_dlp_update_{payload.latest_version}.tar.gz"
        temp_path = os.path.join(scratch_dir, temp_filename)
        
        print(f"[Updater] Downloading verified update package: {payload.download_url} -> {temp_path}")
        req = urllib.request.Request(payload.download_url, headers={'User-Agent': 'yt-dlp-Pro-Desktop'})
        with urllib.request.urlopen(req, timeout=10.0) as response, open(temp_path, "wb") as out_file:
            out_file.write(response.read())
            
        # 2. Cryptographic Integrity Verification (Supply Chain Protection)
        if payload.sha256:
            computed_hash = calculate_sha256(temp_path)
            print(f"[Updater] Verifying SHA-256 Checksum... Expected: {payload.sha256}, Computed: {computed_hash}")
            
            if computed_hash.lower() != payload.sha256.lower():
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
                return False, "Güvenlik İhlali: SHA-256 Bütünlük Doğrulaması Başarısız! (Security Breach: Checksum Mismatch)"
        
        # 3. Secure Installation
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--no-deps", temp_path],
            capture_output=True,
            creationflags=creationflags,
            shell=False
        )
        success = (result.returncode == 0)
        msg = result.stderr.decode("utf-8", errors="replace") if not success else "Success"
        
        # Cleanup downloaded archive
        try:
            os.remove(temp_path)
        except Exception:
            pass
            
        return success, msg

    except Exception as e:
        return False, str(e)
