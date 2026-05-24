import os
import sys
import subprocess
import shutil

def main():
    print("==================================================")
    print("   yt-dlp Downloader Pro - Desktop Packaging      ")
    print("==================================================")
    
    # 1. Ensure we are in the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 2. Check virtual environment python
    venv_python = os.path.join(script_dir, ".venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        venv_python = sys.executable  # Fallback to current system python
        print(f"[*] Sanal ortam python bulunamadi. Sistem python kullaniliyor: {venv_python}")
    else:
        print(f"[*] Sanal ortam python bulundu: {venv_python}")
        
    # 3. Ensure required packaging tools and dependencies are installed
    print("[*] Gerekli bağımlılıklar kontrol ediliyor/kuruluyor...")
    try:
        subprocess.run([venv_python, "-m", "pip", "install", "--upgrade", "pyinstaller", "customtkinter", "pywinstyles", "Pillow", "yt-dlp"], check=True)
    except Exception as e:
        print(f"[!] Bağımlılıkların kurulumu başarısız: {e}")
        sys.exit(1)
        
    # 4. Import customtkinter in the target environment to find its package location
    try:
        import customtkinter
        ctk_dir = os.path.dirname(customtkinter.__file__)
        print(f"[*] CustomTkinter kütüphane yolu: {ctk_dir}")
    except ImportError:
        print("[!] CustomTkinter yüklenemedi. Paketleme durduruluyor.")
        sys.exit(1)
    
    # 5. Formulate PyInstaller command
    # Formatting the add-data format according to OS (Windows uses semicolon ';')
    separator = ";" if sys.platform.startswith("win") else ":"
    
    pyinstaller_cmd = [
        "pyinstaller",
        "--noconsole",                                             # Hide command prompt window
        "--onefile",                                               # Single executable file
        "--name=yt-dlp Downloader Pro",                           # Output .exe name
        f"--add-data={ctk_dir}{separator}customtkinter",           # CustomTkinter theme assets
        f"--add-data=assets{separator}assets",                     # Glass background images
        "--hidden-import=yt_dlp_ejs",                              # EJS challenge solver package
        "--hidden-import=websockets",                              # Required by EJS solver
        "--hidden-import=brotli",                                  # Optional performance compression
        "--hidden-import=mutagen",                                 # Audio tags postprocessing
        "--hidden-import=pycryptodomex",                           # Cryptographic signature support
        "--hidden-import=requests",                                # Update queries and API requests
        "--icon=assets/logo.ico",                                  # High-fidelity multi-resolution application logo
        "app.py"                                                   # Target script
    ]
    
    print("[*] PyInstaller derleme işlemi başlatılıyor...")
    print(f"    Çalıştırılacak Komut: {' '.join(pyinstaller_cmd)}")
    
    try:
        # Run pyinstaller from the current python package environment
        pyinstaller_bin = os.path.join(os.path.dirname(venv_python), "pyinstaller.exe")
        if not os.path.exists(pyinstaller_bin):
            pyinstaller_bin = "pyinstaller"  # Fallback to system path
            
        subprocess.run([pyinstaller_bin] + pyinstaller_cmd[1:], check=True)
        
        print("\n==================================================")
        print("   BAŞARILI: Masaüstü Paketleme Tamamlandı!       ")
        print("==================================================")
        print(f"[+] Oluşturulan Tekil .exe Konumu:")
        print(f"    {os.path.join(script_dir, 'dist', 'yt-dlp Downloader Pro.exe')}")
        print("[+] Bu .exe dosyasını dilediğiniz kullanıcıyla paylaşabilirsiniz.")
        print("[+] Karşı tarafın bilgisayarında Python veya bağımlılık olması gerekmez!")
        print("==================================================")
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Paketleme işlemi hata koduyla başarısız oldu: {e.returncode}")
        sys.exit(1)

if __name__ == "__main__":
    main()
