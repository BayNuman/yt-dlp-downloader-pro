# build_sidecar.py
"""
yt-dlp Downloader Pro - Sidecar PyInstaller Build Script
Compiles the FastAPI backend into a single executable and places it in the Tauri bin folder.
"""
import os
import sys
import subprocess
import shutil

def main():
    print("==================================================")
    print("   yt-dlp Downloader Pro - Sidecar Compilation    ")
    print("==================================================")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # 1. Resolve virtual environment python
    venv_python = os.path.join(script_dir, ".venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        venv_python = sys.executable
        print(f"[*] Sanal ortam python bulunamadı. Sistem python kullanılıyor: {venv_python}")
    else:
        print(f"[*] Sanal ortam python bulundu: {venv_python}")

    # 2. Formulate PyInstaller command
    pyinstaller_bin = os.path.join(os.path.dirname(venv_python), "pyinstaller.exe")
    if not os.path.exists(pyinstaller_bin):
        pyinstaller_bin = "pyinstaller"

    pyinstaller_cmd = [
        pyinstaller_bin,
        "--noconsole",                                     # Hide console window
        "--onefile",                                       # Single executable
        "--name=server-sidecar",                           # Target executable name
        "--hidden-import=uvicorn.protocols.http.h11_impl",
        "--hidden-import=uvicorn.protocols.http.flow_control",
        "--hidden-import=uvicorn.protocols.websockets.websockets_impl",
        "--hidden-import=uvicorn.lifespan.on",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=fastapi",
        "--hidden-import=yt_dlp",
        "--hidden-import=yt_dlp_ejs",
        "--hidden-import=websockets",
        "--hidden-import=brotli",
        "--hidden-import=mutagen",
        "--hidden-import=pycryptodomex",
        "--hidden-import=requests",
        "--hidden-import=sqlite3",
        "--hidden-import=server.main",
        "--hidden-import=server.routers.metadata",
        "--hidden-import=server.routers.queue",
        "--hidden-import=server.routers.download",
        "--hidden-import=server.routers.history",
        "--hidden-import=server.routers.config",
        "server_app.py"
    ]

    print("[*] PyInstaller ile sidecar derleme başlatılıyor...")
    try:
        subprocess.run(pyinstaller_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Derleme işlemi hata koduyla başarısız oldu: {e.returncode}")
        sys.exit(1)

    # 3. Determine host architecture target triple
    # In Windows 64-bit: x86_64-pc-windows-msvc
    target_triple = "x86_64-pc-windows-msvc"
    if sys.platform.startswith("darwin"):
        target_triple = "x86_64-apple-darwin"
    elif sys.platform.startswith("linux"):
        target_triple = "x86_64-unknown-linux-gnu"

    # 4. Copy build result to tauri/bin folder with target triple suffix
    tauri_bin_dir = os.path.join(script_dir, "frontend", "src-tauri", "bin")
    os.makedirs(tauri_bin_dir, exist_ok=True)

    src_exe = os.path.join(script_dir, "dist", "server-sidecar.exe")
    dest_exe = os.path.join(tauri_bin_dir, f"server-sidecar-{target_triple}.exe")

    print(f"[*] Derlenen sidecar kopyalanıyor:")
    print(f"    Kaynak: {src_exe}")
    print(f"    Hedef:  {dest_exe}")

    try:
        shutil.copy2(src_exe, dest_exe)
        print("\n==================================================")
        print("   BAŞARILI: Sidecar Paketlendi ve Kopyalandı!    ")
        print("==================================================")
    except Exception as e:
        print(f"[!] Kopyalama işlemi başarısız: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
