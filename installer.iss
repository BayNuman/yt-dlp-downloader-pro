; yt-dlp Downloader Pro - Inno Setup Configuration Script
[Setup]
AppName=yt-dlp Downloader Pro
AppVersion=1.2.0
DefaultDirName={autopf}\yt-dlp Downloader Pro
DefaultGroupName=yt-dlp Downloader Pro
OutputDir=dist
OutputBaseFilename=yt-dlp_Downloader_Pro_Setup
Compression=lzma2
SolidCompression=yes
DisableProgramGroupPage=yes
DisableWelcomePage=no
SetupIconFile=assets\logo.ico
UninstallDisplayIcon={app}\yt-dlp Downloader Pro.exe

[Files]
; Copy the compiled PyInstaller executable
Source: "dist\yt-dlp Downloader Pro.exe"; DestDir: "{app}"; Flags: ignoreversion
; Copy the ffmpeg static binaries so they are placed directly next to the executable
Source: "bin\ffmpeg.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "bin\ffprobe.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\yt-dlp Downloader Pro"; Filename: "{app}\yt-dlp Downloader Pro.exe"
Name: "{autodesktop}\yt-dlp Downloader Pro"; Filename: "{app}\yt-dlp Downloader Pro.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Masaüstü kısayolu oluştur (Create a desktop shortcut)"; GroupDescription: "Ek kısayollar (Additional icons):"

[Run]
Filename: "{app}\yt-dlp Downloader Pro.exe"; Description: "yt-dlp Downloader Pro Uygulamasını Başlat"; Flags: postinstall nowait
