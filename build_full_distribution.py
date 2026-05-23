import os
import sys
import urllib.request
import zipfile
import subprocess
import shutil

FFMPEG_ZIP_URL = "https://github.com/ffbinaries/ffbinaries-prebuilt/releases/download/v4.4.1/ffmpeg-4.4.1-win-64.zip"
FFPROBE_ZIP_URL = "https://github.com/ffbinaries/ffbinaries-prebuilt/releases/download/v4.4.1/ffprobe-4.4.1-win-64.zip"

def download_and_unzip(url, dest_dir, filename):
    zip_path = os.path.join(dest_dir, f"{filename}.zip")
    print(f"[*] {filename} indiriliyor (Kaynaktan: {url})...")
    
    # Custom User-Agent to avoid HTTP 403 Forbidden errors
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    
    with urllib.request.urlopen(req) as response, open(zip_path, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)
        
    print(f"[+] {filename} zip dosyası indirildi. Çıkartılıyor...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(dest_dir)
        
    # Clean up the downloaded zip file
    os.remove(zip_path)
    print(f"[+] {filename} başarıyla hazırlandı.")

def main():
    print("==================================================")
    print("   yt-dlp Downloader Pro - Full Distribution      ")
    print("==================================================")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 1. Create bin/ directory and download ffmpeg if missing
    bin_dir = os.path.join(script_dir, "bin")
    os.makedirs(bin_dir, exist_ok=True)
    
    ffmpeg_exe = os.path.join(bin_dir, "ffmpeg.exe")
    ffprobe_exe = os.path.join(bin_dir, "ffprobe.exe")
    
    if not os.path.exists(ffmpeg_exe):
        try:
            download_and_unzip(FFMPEG_ZIP_URL, bin_dir, "ffmpeg")
        except Exception as e:
            print(f"[!] ffmpeg indirme hatası: {e}")
            sys.exit(1)
    else:
        print("[*] ffmpeg.exe zaten mevcut, indirme atlanıyor.")
        
    if not os.path.exists(ffprobe_exe):
        try:
            download_and_unzip(FFPROBE_ZIP_URL, bin_dir, "ffprobe")
        except Exception as e:
            print(f"[!] ffprobe indirme hatası: {e}")
            sys.exit(1)
    else:
        print("[*] ffprobe.exe zaten mevcut, indirme atlanıyor.")
        
    # 2. Run pyinstaller desktop build script
    print("\n[*] 1. AŞAMA: PyInstaller ile tekil .exe derleme başlatılıyor...")
    venv_python = os.path.join(script_dir, ".venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        venv_python = sys.executable
        
    try:
        subprocess.run([venv_python, "build_desktop.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] PyInstaller derlemesi başarısız oldu: {e}")
        sys.exit(1)
        
    # 3. Locate and execute Inno Setup compiler
    print("\n[*] 2. AŞAMA: Inno Setup ile kurulum paketi (setup.exe) derleme başlatılıyor...")
    iscc_path = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    
    if not os.path.exists(iscc_path):
        print(f"[!] Inno Setup derleyicisi '{iscc_path}' konumunda bulunamadı!")
        print("[!] Lütfen Inno Setup'ın doğru kurulduğundan emin olun.")
        sys.exit(1)
        
    try:
        subprocess.run([iscc_path, "installer.iss"], check=True)
        print("\n==================================================")
        print("   BAŞARILI: Tümü Derlendi ve Paketlendi!        ")
        print("==================================================")
        print("[+] Tüm süreç sıfır hata ile tamamlandı.")
        print("[+] 1. Çalıştırılabilir Uygulama: dist/yt-dlp Downloader Pro.exe")
        print("[+] 2. Windows Kurulum Paketi (Setup): dist/yt-dlp_Downloader_Pro_Setup.exe")
        print("[+] Kurulum paketi ffmpeg, ffprobe ve görselleri içine gömmüştür!")
        print("==================================================")
    except subprocess.CalledProcessError as e:
        print(f"[!] Inno Setup derlemesi hata kodu ile başarısız oldu: {e.returncode}")
        sys.exit(1)

if __name__ == "__main__":
    main()
