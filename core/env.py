# core/env.py
import os
import sys

def refresh_path_env() -> None:
    """
    Dynamically loads the latest Windows PATH environment variables from the registry
    to pick up newly installed tools (like Deno or Node.js via winget) without requiring 
    a system or application restart.
    """
    if os.name != 'nt':
        return

    try:
        import winreg
        paths = []
        
        # 1. Query Registry for User-level Environment PATH
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ) as key:
                val, _ = winreg.QueryValueEx(key, "Path")
                if val:
                    paths.extend(val.split(os.pathsep))
        except Exception:
            pass

        # 2. Query Registry for System-level (Machine) Environment PATH
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"System\CurrentControlSet\Control\Session Manager\Environment", 0, winreg.KEY_READ) as key:
                val, _ = winreg.QueryValueEx(key, "Path")
                if val:
                    paths.extend(val.split(os.pathsep))
        except Exception:
            pass

        # 3. Add explicit check for Winget Local Packages directory where Deno/Node.js is usually extracted
        winget_packages_dir = os.path.expandvars(r"%USERPROFILE%\AppData\Local\Microsoft\WinGet\Packages")
        if os.path.exists(winget_packages_dir):
            for root, dirs, files in os.walk(winget_packages_dir):
                if "deno.exe" in files or "node.exe" in files:
                    paths.append(root)

        # 4. Filter empty/duplicate paths and update the active process environment
        seen = set()
        cleaned_paths = []
        
        # Prepend the current path elements to avoid losing any dynamic paths added at runtime
        current_env_paths = os.environ.get("PATH", "").split(os.pathsep)
        for p in current_env_paths + paths:
            p_clean = os.path.expandvars(p.strip())
            if p_clean and p_clean not in seen:
                seen.add(p_clean)
                cleaned_paths.append(p_clean)
                
        os.environ["PATH"] = os.pathsep.join(cleaned_paths)
    except Exception as e:
        print(f"Error refreshing PATH: {e}")
