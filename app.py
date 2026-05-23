import os
import queue
import re
import shlex
import shutil
import sys
import threading
import urllib.request
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageTk

try:
    import pywinstyles
except ImportError:
    pywinstyles = None

def resolve_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# Premium Glassmorphic Theme Palette Colors (Light, Dark)
THEME_BG = ("#f1f5f9", "#090d16")                 # Soft Slate-Blue / Deep Space Obsidian
THEME_CARD_BG = ("#ffffff", "#121b2d")             # Translucent white glass / Deep Slate card glass
THEME_CARD_BORDER = ("#cbd5e1", "#22334f")         # Soft borders / Glass glow border
THEME_TEXT_PRIMARY = ("#0f172a", "#f8fafc")        # Title / strong text
THEME_TEXT_SECONDARY = ("#475569", "#94a3b8")      # Muted body text
THEME_ACCENT_BLUE = ("#2563eb", "#00d2ff")         # Accent cyan/blue
THEME_ACCENT_INDIGO = ("#4f46e5", "#6366f1")       # Violet-Indigo main
THEME_ACCENT_GREEN = ("#16a34a", "#10b981")        # Success states
THEME_ACCENT_RED = ("#dc2626", "#f43f5e")          # Error/Cancel states
THEME_CARD_SUBTITLE = ("#64748b", "#38bdf8")

VIDEO_PRESET_HEIGHT = {
    "Maksimum (Best)": "Best",
    "Ultra HD (2160p)": "2160",
    "QHD (1440p)": "1440",
    "Full HD (1080p)": "1080",
    "Dengeli (720p)": "720",
    "Hizli (480p)": "480",
    "Ekonomi (360p)": "360",
    "Ozel (Custom)": "CUSTOM",
}

AUDIO_PRESET_QUALITY = {
    "Best": "0",
    "Yuksek (320K)": "320K",
    "Dengeli (192K)": "192K",
    "Kucuk Boyut (128K)": "128K",
}

VIDEO_AUDIO_CODEC_OPTIONS = ["AAC", "OPUS (OPEC)"]
DEFAULT_OUTPUT_TEMPLATE = "%(title)s [%(id)s].%(ext)s"
YOUTUBE_FALLBACK_EXTRACTOR_ARGS = "youtube:player-client=tv"
BROWSER_COOKIE_SOURCES = ["Kapali", "chrome", "edge", "firefox", "brave", "opera", "vivaldi"]

# Premium UI Multi-Language Dictionary (English default, Turkish & Spanish options)
TRANSLATIONS = {
    "en": {
        "title": "yt-dlp Downloader Pro",
        "subtitle": "Smart multi-video and audio download manager with semi-translucent glassmorphic depth.",
        "theme_light": "☀️ Light Mode",
        "theme_dark": "🌙 Dark Mode",
        "url_label": "Video / Playlist Address",
        "paste_btn": "📋 Paste from Clipboard",
        "batch_switch": "Batch List Mode",
        "url_placeholder": "Paste your YouTube, Vimeo, SoundCloud or other video links here...",
        "save_folder_label": "Output Folder Location",
        "browse_btn": "📂 Choose Folder",
        "preset_label": "Quick Download Format Profile",
        "preset_best": "🚀 Best Quality\n(Max Video & Audio)",
        "preset_1080p": "📺 Full HD 1080p\n(Balanced MP4)",
        "preset_720p": "⚡ Balanced Fast\n(Speedy 720p)",
        "preset_mp3": "🎵 High Quality Audio\n(320kbps MP3 Müzik)",
        "active_profile_best": "Active Profile: 🚀 Best Resolution (Maximum video quality and audio)",
        "active_profile_1080p": "Active Profile: 📺 Full HD 1080p limited video (AAC/MP4 encoding)",
        "active_profile_720p": "Active Profile: ⚡ Speedy 720p download (Balanced file size)",
        "active_profile_audio": "Active Profile: 🎵 High Quality Audio ({format} - {quality})",
        "active_profile_custom": "Active Profile: Custom formats selected via advanced panel.",
        "queue_label": "Download Queue & Manager",
        "add_queue_btn": "➕ Add to Queue",
        "queue_placeholder": "No videos in download queue. Add links from above.",
        "advanced_toggle": "Show Advanced Download & File Settings",
        "advanced_hint": "(Resolution, codec formats, cookies, speed limits and extra yt-dlp arguments)",
        "tab_codecs": "Resolution & Codec",
        "tab_limits": "Limits & Cookies",
        "tab_flags": "Permissions",
        "lbl_mode": "Download Mode:",
        "lbl_profile": "Quality Profile:",
        "lbl_max_res": "Max Resolution:",
        "lbl_format": "Video Format:",
        "lbl_audio_ext": "Audio Extension:",
        "lbl_audio_qual": "Audio Quality:",
        "lbl_audio_codec": "Audio Codec (Video):",
        "lbl_playlist_range": "Playlist Range:",
        "lbl_max_dl": "Max Downloads:",
        "lbl_speed_limit": "Speed Limit:",
        "lbl_cookie_file": "Cookie File (.txt):",
        "lbl_browser_cookie": "Browser Cookies:",
        "lbl_retry": "Retry Counts:",
        "lbl_concurrent": "Concurrent Fragments:",
        "lbl_header_addons": "Media Add-ons",
        "chk_thumb": "Download Visual (Thumbnail)",
        "chk_subs": "Download Subtitle Files",
        "chk_auto_subs": "Auto Translation Subtitles",
        "lbl_header_behavior": "Download Behaviors",
        "chk_playlist": "Process as Playlist",
        "chk_metadata": "Add Metadata Tags",
        "chk_restrict_names": "Clean Filenames (Safe Characters)",
        "chk_archive": "Use Download Archive (Skip existing)",
        "chk_youtube_403": "TV Client Fallback on YouTube 403",
        "chk_sponsorblock": "SponsorBlock (Cut sponsor segments)",
        "lbl_template": "Filename Template:",
        "btn_update": "🔄 Update yt-dlp",
        "lbl_extra_params": "Extra Parameters:",
        "lbl_dashboard_title": "Active Download Progress Panel",
        "lbl_active_dl": "Currently Downloading: Idle",
        "lbl_speed": "Download Speed",
        "lbl_eta": "Remaining Time (ETA)",
        "lbl_size": "Total File Size",
        "btn_start": "🚀 Start Downloads",
        "btn_cancel": "🛑 Cancel",
        "btn_clear": "🧹 Clear Logs",
        "btn_open_folder": "📂 Open Folder",
        "lbl_status_ready": "Ready (Waiting)",
        "lbl_status_pasted": "URL Pasted from Clipboard",
        "lbl_status_added": "Added {count} new downloads to queue",
        "lbl_status_processing": "Processing Queue ({curr}/{total})...",
        "lbl_status_cancelled": "Download Queue Process Cancelled",
        "lbl_status_completed": "All Downloads Completed!",
        "lbl_status_active_dl": "Currently Downloading: {title}",
        "lbl_preview_loading": "Fetching video info, please wait...",
        "lbl_preview_title": "Video Title Loading...",
        "lbl_preview_author": "Channel Name",
        "lbl_preview_dur": "Duration: --:--",
        "lbl_preview_err": "Failed to fetch video details (Unsupported URL or no internet).",
        "lbl_toast_success_title": "Download Successful!",
        "lbl_toast_success_desc": "'{title}' successfully downloaded.",
        "lbl_toast_err_title": "Download Failed",
        "lbl_toast_err_desc": "Error code {code} - '{title}'",
        "lbl_toast_all_title": "All Tasks Completed!",
        "lbl_toast_all_desc": "All queued videos successfully downloaded.",
        "lbl_logs_toggle": "Show Advanced System and Terminal Logs",
        "lbl_toast_update_title": "Update Successful",
        "lbl_toast_update_desc": "yt-dlp packages updated to the latest version!",
        "lbl_placeholder_range": "Ex: 1-10, 15",
        "lbl_placeholder_max": "Ex: 5",
        "lbl_placeholder_speed": "Ex: 2M or 500K",
        "lbl_placeholder_cookies": "Select text file...",
        "lbl_placeholder_retry": "Ex: 10",
        "lbl_placeholder_fragments": "Ex: 4",
        "lbl_placeholder_extra": "Ex: --sleep-interval 1",
        "lbl_queue_item_placeholder": "Queue empty. Add links above to download.",
        "lbl_queue_remove": "❌ Remove",
        "lbl_dialog_close_title": "Exit",
        "lbl_dialog_close_desc": "Downloads are in progress. Are you sure you want to exit?",
        "lbl_dialog_deps_title": "Missing Packages",
        "lbl_dialog_deps_desc": "yt-dlp is not installed.\nTerminal: pip install -r requirements.txt",
        "lbl_dialog_err_title": "Invalid Value",
        "lbl_dialog_err_digit": "{field_name} must be a number.",
        "lbl_dialog_err_min": "{field_name} must be at least {min_value}.",
        "lbl_dialog_err_template": "Filename template cannot be empty.",
        "lbl_dialog_info_title": "Information",
        "lbl_dialog_info_running": "Downloads are already in progress.",
        "lbl_dialog_warning_title": "Missing Info",
        "lbl_dialog_warning_url": "Please enter a valid URL.",
        "preview_name_label": "Output Filename Preview: {preview}",
    },
    "tr": {
        "title": "yt-dlp Downloader Pro",
        "subtitle": "Yarı saydam glassmorphic derinlik ile akıllı çoklu video ve ses indirme yöneticisi.",
        "theme_light": "☀️ Aydınlık Mod",
        "theme_dark": "🌙 Karanlık Mod",
        "url_label": "Video / Playlist Adresi",
        "paste_btn": "📋 Panodan Yapıştır",
        "batch_switch": "Çoklu Liste Modu",
        "url_placeholder": "Kopyaladığınız YouTube, Vimeo, SoundCloud veya diğer video linklerini buraya ekleyin...",
        "save_folder_label": "İndirilen Dosyaların Kaydedileceği Klasör",
        "browse_btn": "📂 Klasör Seç",
        "preset_label": "Hızlı İndirme Format Profili",
        "preset_best": "🚀 En İyi Kalite\n(Maksimum Görüntü & Ses)",
        "preset_1080p": "📺 Full HD 1080p\n(Dengeli Standart MP4)",
        "preset_720p": "⚡ Dengeli Fast\n(Hızlı 720p İndirme)",
        "preset_mp3": "🎵 Yüksek Kalite Ses\n(320kbps MP3 Müzik)",
        "active_profile_best": "Aktif Profil: 🚀 En İyi Çözünürlük (Maksimum video kalitesi ve ses kodeği)",
        "active_profile_1080p": "Aktif Profil: 📺 Full HD 1080p limitli video (AAC/MP4 kodlama)",
        "active_profile_720p": "Aktif Profil: ⚡ Hızlı 720p indirme (Dengeli dosya boyutu)",
        "active_profile_audio": "Aktif Profil: 🎵 Yüksek Kalite Ses çıkışı ({format} - {quality})",
        "active_profile_custom": "Aktif Profil: Gelişmiş panel üzerinden özel format seçildi.",
        "queue_label": "İndirme Sırası ve Kuyruk Yöneticisi",
        "add_queue_btn": "➕ Kuyruğa Ekle",
        "queue_placeholder": "Kuyrukta indirilecek video bulunmuyor. Yukarıdan video ekleyin.",
        "advanced_toggle": "Gelişmiş İndirme ve Dosya Ayarlarını Göster",
        "advanced_hint": "(Çözünürlük, kodek formatları, çerezler, hız limitleri ve ek yt-dlp komutları)",
        "tab_codecs": "Çözünürlük & Kodek",
        "tab_limits": "Limitler & Çerezler",
        "tab_flags": "İndirme İzinleri",
        "lbl_mode": "İndirme Modu:",
        "lbl_profile": "Kalite Profili:",
        "lbl_max_res": "Maks Çözünürlük:",
        "lbl_format": "Video Formatı:",
        "lbl_audio_ext": "Ses Uzantısı:",
        "lbl_audio_qual": "Ses Kalitesi:",
        "lbl_audio_codec": "Ses Kodeği (Video):",
        "lbl_playlist_range": "Playlist Aralığı:",
        "lbl_max_dl": "Maks İndirme:",
        "lbl_speed_limit": "Hız Limiti:",
        "lbl_cookie_file": "Çerez (.txt):",
        "lbl_browser_cookie": "Tarayıcı Çerezleri:",
        "lbl_retry": "Retry Sayısı:",
        "lbl_concurrent": "Eşzamanlı Parça:",
        "lbl_header_addons": "Medya Eklentileri",
        "chk_thumb": "Görsel (Thumbnail) İndir",
        "chk_subs": "Altyazı Dosyalarını İndir",
        "chk_auto_subs": "Otomatik Altyazı Ekle (Çeviri)",
        "lbl_header_behavior": "İndirme Yöntemleri",
        "chk_playlist": "Playlist Olarak İşle",
        "chk_metadata": "Etiket/Meta Veri Ekle",
        "chk_restrict_names": "Karakterleri Temizle (Güvenli Ad)",
        "chk_archive": "Arşiv Dosyası Kullan (Zaten inenleri atlar)",
        "chk_youtube_403": "YouTube 403 Fallback (TV Client)",
        "chk_sponsorblock": "SponsorBlock (Sponsor reklamları kes)",
        "lbl_template": "Dosya Adı Şablonu:",
        "btn_update": "🔄 yt-dlp Güncelle",
        "lbl_extra_params": "Ek Parametreler:",
        "lbl_dashboard_title": "Aktif İndirme Süreci Göstergeleri",
        "lbl_active_dl": "Şu Anda İndirilen: Boşta",
        "lbl_speed": "İndirme Hızı",
        "lbl_eta": "Kalan Süre (ETA)",
        "lbl_size": "Toplam Dosya Boyutu",
        "btn_start": "🚀 İndirmeyi Başlat",
        "btn_cancel": "🛑 İptal Et",
        "btn_clear": "🧹 Temizle",
        "btn_open_folder": "📂 Klasörü Aç",
        "lbl_status_ready": "Hazır (Beklemede)",
        "lbl_status_pasted": "URL Pano Üzerinden Yapıştırıldı",
        "lbl_status_added": "Kuyruğa {count} Yeni İndirme Eklendi",
        "lbl_status_processing": "Kuyruk İşleniyor ({curr}/{total})...",
        "lbl_status_cancelled": "Sıra İndirme İşlemi İptal Edildi",
        "lbl_status_completed": "Sıradaki Tüm İndirmeler Tamamlandı!",
        "lbl_status_active_dl": "Şu Anda İndirilen: {title}",
        "lbl_preview_loading": "Video bilgileri alınıyor, lütfen bekleyin...",
        "lbl_preview_title": "Video Başlığı Yükleniyor...",
        "lbl_preview_author": "Kanal Adı",
        "lbl_preview_dur": "Süre: --:--",
        "lbl_preview_err": "Video bilgileri yüklenemedi (Desteklenmeyen URL veya internet yok).",
        "lbl_toast_success_title": "İndirme Başarılı!",
        "lbl_toast_success_desc": "'{title}' başarıyla indirildi.",
        "lbl_toast_err_title": "İndirme Başarısız",
        "lbl_toast_err_desc": "Hata kodu {code} - '{title}'",
        "lbl_toast_all_title": "Tüm Görevler Bitti!",
        "lbl_toast_all_desc": "Kuyruktaki tüm videolar başarıyla indirildi.",
        "lbl_logs_toggle": "Gelişmiş Sistem Hata ve Terminal Günlüklerini Göster",
        "lbl_toast_update_title": "Güncelleme Başarılı",
        "lbl_toast_update_desc": "yt-dlp paketleri başarıyla son sürüme güncellendi!",
        "lbl_placeholder_range": "Örn: 1-10, 15",
        "lbl_placeholder_max": "Örn: 5",
        "lbl_placeholder_speed": "Örn: 2M veya 500K",
        "lbl_placeholder_cookies": "Metin dosyası seç...",
        "lbl_placeholder_retry": "Örn: 10",
        "lbl_placeholder_fragments": "Örn: 4",
        "lbl_placeholder_extra": "Örn: --sleep-interval 1",
        "lbl_queue_item_placeholder": "Kuyrukta indirilecek video bulunmuyor. Yukarıdan video ekleyin.",
        "lbl_queue_remove": "❌ Kaldır",
        "lbl_dialog_close_title": "Çıkış",
        "lbl_dialog_close_desc": "Devam eden indirme işlemi var. Çıkmak istediğinizden emin misiniz?",
        "lbl_dialog_deps_title": "Eksik Paket",
        "lbl_dialog_deps_desc": "yt-dlp kurulmamış.\nTerminal: pip install -r requirements.txt",
        "lbl_dialog_err_title": "Geçersiz Değer",
        "lbl_dialog_err_digit": "{field_name} sayı olmalıdır.",
        "lbl_dialog_err_min": "{field_name} en az {min_value} olmalıdır.",
        "lbl_dialog_err_template": "Dosya adı şablonu boş olamaz.",
        "lbl_dialog_info_title": "Bilgi",
        "lbl_dialog_info_running": "İndirme zaten devam ediyor.",
        "lbl_dialog_warning_title": "Eksik Bilgi",
        "lbl_dialog_warning_url": "Lütfen geçerli bir video URL adresi girin.",
        "preview_name_label": "Çıktı İsmi Önizleme: {preview}",
    },
    "es": {
        "title": "yt-dlp Downloader Pro",
        "subtitle": "Gestor inteligente de descargas de video y audio con profundidad glassmorphic translúcida.",
        "theme_light": "☀️ Modo Claro",
        "theme_dark": "🌙 Modo Oscuro",
        "url_label": "Dirección del Video / Lista de Reproducción",
        "paste_btn": "📋 Pegar del Portapapeles",
        "batch_switch": "Modo de Lista",
        "url_placeholder": "Pegue sus enlaces de YouTube, Vimeo, SoundCloud u otros aquí...",
        "save_folder_label": "Carpeta de Destino de Descarga",
        "browse_btn": "📂 Seleccionar Carpeta",
        "preset_label": "Perfil Rápido de Calidad de Descarga",
        "preset_best": "🚀 Mejor Calidad\n(Máximo Video y Audio)",
        "preset_1080p": "📺 Full HD 1080p\n(MP4 Equilibrado)",
        "preset_720p": "⚡ Rápido Equilibrado\n(Descarga Veloz 720p)",
        "preset_mp3": "🎵 Audio de Alta Calidad\n(MP3 de 320kbps)",
        "active_profile_best": "Perfil Activo: 🚀 Mejor resolución (Máxima calidad de video y audio)",
        "active_profile_1080p": "Perfil Activo: 📺 Video limitado a Full HD 1080p (Codificación AAC/MP4)",
        "active_profile_720p": "Perfil Activo: ⚡ Descarga veloz de 720p (Tamaño de archivo equilibrado)",
        "active_profile_audio": "Perfil Activo: 🎵 Audio de alta calidad ({format} - {quality})",
        "active_profile_custom": "Perfil Activo: Formatos personalizados seleccionados en el panel avanzado.",
        "queue_label": "Cola de Descarga y Administrador",
        "add_queue_btn": "➕ Añadir a la Cola",
        "queue_placeholder": "No hay videos en la cola de descarga. Añada enlaces arriba.",
        "advanced_toggle": "Mostrar Ajustes Avanzados de Archivos y Descargas",
        "advanced_hint": "(Resolución, formatos de códec, cookies, límites de velocidad y argumentos adicionales de yt-dlp)",
        "tab_codecs": "Resolución y Códec",
        "tab_limits": "Límites y Cookies",
        "tab_flags": "Permisos",
        "lbl_mode": "Modo de Descarga:",
        "lbl_profile": "Perfil de Calidad:",
        "lbl_max_res": "Resolución Máxima:",
        "lbl_format": "Formato de Video:",
        "lbl_audio_ext": "Extensión de Audio:",
        "lbl_audio_qual": "Calidad de Audio:",
        "lbl_audio_codec": "Códec de Audio (Video):",
        "lbl_playlist_range": "Rango de Lista:",
        "lbl_max_dl": "Descargas Máximas:",
        "lbl_speed_limit": "Límite de Velocidad:",
        "lbl_cookie_file": "Archivo de Cookies (.txt):",
        "lbl_browser_cookie": "Cookies del Navegador:",
        "lbl_retry": "Intentos de Reintento:",
        "lbl_concurrent": "Fragmentos Simultáneos:",
        "lbl_header_addons": "Complementos de Medios",
        "chk_thumb": "Descargar Miniatura (Thumbnail)",
        "chk_subs": "Descargar Archivos de Subtítulos",
        "chk_auto_subs": "Subtítulos de Traducción Automática",
        "lbl_header_behavior": "Comportamientos de Descarga",
        "chk_playlist": "Procesar como Lista de Reproducción",
        "chk_metadata": "Añadir Etiquetas de Metadatos",
        "chk_restrict_names": "Nombres Limpios (Caracteres Seguros)",
        "chk_archive": "Usar Archivo de Descargas (Omitir existentes)",
        "chk_youtube_403": "Retorno de Cliente de TV en YouTube 403",
        "chk_sponsorblock": "SponsorBlock (Cortar segmentos publicitarios)",
        "lbl_template": "Plantilla de Nombre:",
        "btn_update": "🔄 Actualizar yt-dlp",
        "lbl_extra_params": "Parámetros Adicionales:",
        "lbl_dashboard_title": "Panel de Progreso de Descarga Activa",
        "lbl_active_dl": "Descargando Actualmente: Inactivo",
        "lbl_speed": "Velocidad de Descarga",
        "lbl_eta": "Tiempo Restante (ETA)",
        "lbl_size": "Tamaño de Archivo Total",
        "btn_start": "🚀 Iniciar Descargas",
        "btn_cancel": "🛑 Cancelar",
        "btn_clear": "🧹 Limpiar Registros",
        "btn_open_folder": "📂 Abrir Carpeta",
        "lbl_status_ready": "Listo (En espera)",
        "lbl_status_pasted": "URL Pegada desde el Portapapeles",
        "lbl_status_added": "Añadidas {count} nuevas descargas a la cola",
        "lbl_status_processing": "Procesando Cola ({curr}/{total})...",
        "lbl_status_cancelled": "Proceso de Cola de Descarga Cancelado",
        "lbl_status_completed": "¡Todas las Descargas Completadas!",
        "lbl_status_active_dl": "Descargando Actualmente: {title}",
        "lbl_preview_loading": "Obteniendo información del video, espere...",
        "lbl_preview_title": "Cargando Título del Video...",
        "lbl_preview_author": "Nombre del Canal",
        "lbl_preview_dur": "Duración: --:--",
        "lbl_preview_err": "Error al obtener detalles (Enlace no admitido o sin internet).",
        "lbl_toast_success_title": "¡Descarga Exitosa!",
        "lbl_toast_success_desc": "'{title}' descargado con éxito.",
        "lbl_toast_err_title": "Descarga Fallida",
        "lbl_toast_err_desc": "Código de error {code} - '{title}'",
        "lbl_toast_all_title": "¡Todas las Tareas Completadas!",
        "lbl_toast_all_desc": "Todos los videos en cola descargados con éxito.",
        "lbl_logs_toggle": "Mostrar Registros Avanzados de Terminal y Sistema",
        "lbl_toast_update_title": "Actualización Exitosa",
        "lbl_toast_update_desc": "¡Los paquetes de yt-dlp se actualizaron a la última versión!",
        "lbl_placeholder_range": "Ej: 1-10, 15",
        "lbl_placeholder_max": "Ej: 5",
        "lbl_placeholder_speed": "Ej: 2M o 500K",
        "lbl_placeholder_cookies": "Seleccionar archivo txt...",
        "lbl_placeholder_retry": "Ej: 10",
        "lbl_placeholder_fragments": "Ej: 4",
        "lbl_placeholder_extra": "Ej: --sleep-interval 1",
        "lbl_queue_item_placeholder": "Cola vacía. Añada enlaces arriba.",
        "lbl_queue_remove": "❌ Eliminar",
        "lbl_dialog_close_title": "Salir",
        "lbl_dialog_close_desc": "Las descargas están en curso. ¿Está seguro de que desea salir?",
        "lbl_dialog_deps_title": "Paquetes Faltantes",
        "lbl_dialog_deps_desc": "yt-dlp no está instalado.\nTerminal: pip install -r requirements.txt",
        "lbl_dialog_err_title": "Valor No Válido",
        "lbl_dialog_err_digit": "{field_name} debe ser un número.",
        "lbl_dialog_err_min": "{field_name} debe ser al menos {min_value}.",
        "lbl_dialog_err_template": "La plantilla no puede estar vacía.",
        "lbl_dialog_info_title": "Información",
        "lbl_dialog_info_running": "Las descargas ya están en curso.",
        "lbl_dialog_warning_title": "Información Faltante",
        "lbl_dialog_warning_url": "Por favor, introduzca una URL válida.",
        "preview_name_label": "Vista Previa del Nombre: {preview}",
    }
}


class YtDlpGuiApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("yt-dlp Downloader Pro")
        self._set_initial_geometry()

        # Dynamic localization
        self.current_lang = "en"

        # Dynamic theme settings
        self.theme_mode = "dark"
        ctk.set_appearance_mode(self.theme_mode)
        self.configure(fg_color=THEME_BG)

        # Temp directory for fetched thumbnails
        self.scratch_dir = Path(os.getenv("APPDATA", str(Path.home()))) / "yt-dlp-downloader-pro"
        self.scratch_dir.mkdir(parents=True, exist_ok=True)

        # Background assets loading
        self._load_bg_assets()

        # Queue management variables
        self.queue_list: list[dict] = []
        self.current_queue_idx = -1
        self.is_queue_running = False

        # Worker & Process variables
        self.worker_thread: threading.Thread | None = None
        self.process: subprocess.Popen[str] | None = None
        self.cancel_event = threading.Event()
        self.ui_queue: "queue.Queue[tuple[str, object]]" = queue.Queue()

        # Metadata fetch lock & cache
        self.metadata_thread: threading.Thread | None = None
        self.last_fetched_url = ""
        self.fetched_metadata: dict | None = None

        # Clipboard Auto-Paste monitoring variables
        self.last_clipboard_value = ""
        self.detected_url = ""

        # UI variables
        self.ui_scale_var = ctk.StringVar(value="100%")
        self.selected_preset_var = ctk.StringVar(value="1080p")
        self.batch_mode_var = ctk.BooleanVar(value=False)
        self.active_file_var = ctk.StringVar(value="Currently Downloading: Idle")

        # Build GUI Components
        self._build_ui()
        self._apply_glass_blur()

        # Load dynamic language labels initially
        self._translate_ui()

        # Event Bindings
        self.bind("<FocusIn>", lambda _: self._check_clipboard())
        self.bind("<Configure>", self._on_resize)

        # Clipboard & Queue Monitor loops
        self.after(1500, self._check_clipboard)
        self.after(100, self._drain_ui_queue)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _set_initial_geometry(self) -> None:
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        width = min(1200, max(960, screen_w - 80))
        height = min(1000, max(820, screen_h - 80))
        self.geometry(f"{width}x{height}")
        self.minsize(920, 720)

    def _load_bg_assets(self) -> None:
        """Loads and pre-sizes Pillow background images for both modes."""
        self.bg_image_dark_path = Path(resolve_resource_path("assets/glass_bg_dark.png"))
        self.bg_image_light_path = Path(resolve_resource_path("assets/glass_bg_light.png"))

        # Fallback to solid canvas if images not present
        self.use_bg_images = self.bg_image_dark_path.exists() and self.bg_image_light_path.exists()

        if self.use_bg_images:
            try:
                self.pil_dark_bg = Image.open(self.bg_image_dark_path)
                self.pil_light_bg = Image.open(self.bg_image_light_path)
                self.bg_ctk_image = ctk.CTkImage(
                    light_image=self.pil_light_bg,
                    dark_image=self.pil_dark_bg,
                    size=(1200, 960)
                )
                self.bg_label = ctk.CTkLabel(self, image=self.bg_ctk_image, text="")
                self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            except Exception as e:
                print(f"Failed to load background images: {e}")
                self.use_bg_images = False

    def _on_resize(self, event) -> None:
        """Triggers dynamic scaling of the abstract mesh background to match the window perfectly."""
        if self.use_bg_images and event.widget == self:
            w = event.width
            h = event.height
            self.bg_ctk_image.configure(size=(w, h))

    def _apply_glass_blur(self) -> None:
        """Applies native Acrylic blur style at startup if dark mode is active."""
        if pywinstyles:
            try:
                if self.theme_mode == "dark":
                    pywinstyles.apply_style(self, "acrylic")
                else:
                    pywinstyles.apply_style(self, "normal")
                self._update_header_color()
            except Exception as e:
                print(f"Failed to apply pywinstyles glass effect: {e}")

    def _update_header_color(self) -> None:
        """Updates the titlebar/header color dynamically and switches styling mode safely to prevent crashes."""
        if pywinstyles:
            try:
                # Interlock: Apply Win32 blur only in dark mode, reset to normal window context in light mode
                if self.theme_mode == "dark":
                    pywinstyles.apply_style(self, "acrylic")
                else:
                    pywinstyles.apply_style(self, "normal")

                header_color = "#090d16" if self.theme_mode == "dark" else "#f1f5f9"
                pywinstyles.change_header_color(self, header_color)
            except Exception as e:
                pass

    def _toggle_theme(self) -> None:
        """Toggles theme mode dynamically at runtime."""
        if self.theme_mode == "dark":
            self.theme_mode = "light"
        else:
            self.theme_mode = "dark"

        ctk.set_appearance_mode(self.theme_mode)
        self._update_header_color()
        self._translate_ui()
        self._update_queue_ui()

    def _on_language_menu_changed(self, lang_name: str) -> None:
        """Language OptionMenu selection callback."""
        if lang_name == "Türkçe":
            self.current_lang = "tr"
        elif lang_name == "Español":
            self.current_lang = "es"
        else:
            self.current_lang = "en"

        self._translate_ui()
        self._update_queue_ui()
        self._update_quality_hint()
        self._update_template_preview()

    def _translate_ui(self) -> None:
        """Dynamically translates all UI text labels, switches, buttons, and placeholders at runtime without window reload."""
        lang = self.current_lang

        # Header Titles
        self.title_lbl.configure(text=TRANSLATIONS[lang]["title"])

        # Header Buttons & Menus
        self.theme_btn.configure(text=TRANSLATIONS[lang]["theme_light"] if self.theme_mode == "light" else TRANSLATIONS[lang]["theme_dark"])

        # Input Card 1
        self.url_lbl.configure(text=TRANSLATIONS[lang]["url_label"])
        self.clipboard_badge.configure(text=TRANSLATIONS[lang]["paste_btn"])
        self.batch_mode_switch.configure(text=TRANSLATIONS[lang]["batch_switch"])
        self.url_entry.configure(placeholder_text=TRANSLATIONS[lang]["url_placeholder"])
        self.save_folder_lbl.configure(text=TRANSLATIONS[lang]["save_folder_label"])
        self.browse_btn.configure(text=TRANSLATIONS[lang]["browse_btn"])

        # Preview Card 2
        self.preview_title_lbl.configure(text=TRANSLATIONS[lang]["lbl_preview_title"])
        self.preview_author_lbl.configure(text=TRANSLATIONS[lang]["lbl_preview_author"])
        self.preview_dur_lbl.configure(text=TRANSLATIONS[lang]["lbl_preview_dur"])

        # Presets Card 3
        self.preset_lbl.configure(text=TRANSLATIONS[lang]["preset_label"])
        self.preset_buttons["best"].configure(text=TRANSLATIONS[lang]["preset_best"])
        self.preset_buttons["1080p"].configure(text=TRANSLATIONS[lang]["preset_1080p"])
        self.preset_buttons["720p"].configure(text=TRANSLATIONS[lang]["preset_720p"])
        self.preset_buttons["mp3"].configure(text=TRANSLATIONS[lang]["preset_mp3"])

        # Queue Card 4
        self.queue_lbl.configure(text=TRANSLATIONS[lang]["queue_label"])
        self.add_queue_btn.configure(text=TRANSLATIONS[lang]["add_queue_btn"])

        # Advanced Settings switch Card 5
        self.advanced_switch.configure(text=TRANSLATIONS[lang]["advanced_toggle"])
        self.adv_hint_lbl.configure(text=TRANSLATIONS[lang]["advanced_hint"])

        # Tab view internal sub-headers & options
        self.lbl_mode.configure(text=TRANSLATIONS[lang]["lbl_mode"])
        self.lbl_profile.configure(text=TRANSLATIONS[lang]["lbl_profile"])
        self.lbl_max_res.configure(text=TRANSLATIONS[lang]["lbl_max_res"])
        self.lbl_format.configure(text=TRANSLATIONS[lang]["lbl_format"])
        self.lbl_audio_ext.configure(text=TRANSLATIONS[lang]["lbl_audio_ext"])
        self.lbl_audio_qual.configure(text=TRANSLATIONS[lang]["lbl_audio_qual"])
        self.video_audio_codec_lbl.configure(text=TRANSLATIONS[lang]["lbl_audio_codec"])

        # Tab 2 inputs
        self.lbl_playlist_range.configure(text=TRANSLATIONS[lang]["lbl_playlist_range"])
        self.lbl_max_dl.configure(text=TRANSLATIONS[lang]["lbl_max_dl"])
        self.lbl_speed_limit.configure(text=TRANSLATIONS[lang]["lbl_speed_limit"])
        self.lbl_cookie_file.configure(text=TRANSLATIONS[lang]["lbl_cookie_file"])
        self.lbl_browser_cookie.configure(text=TRANSLATIONS[lang]["lbl_browser_cookie"])
        self.lbl_retry.configure(text=TRANSLATIONS[lang]["lbl_retry"])
        self.lbl_concurrent.configure(text=TRANSLATIONS[lang]["lbl_concurrent"])

        # Tab 3 check boxes
        self.lbl_header_addons.configure(text=TRANSLATIONS[lang]["lbl_header_addons"])
        self.chk_thumb.configure(text=TRANSLATIONS[lang]["chk_thumb"])
        self.chk_subs.configure(text=TRANSLATIONS[lang]["chk_subs"])
        self.auto_subs_check.configure(text=TRANSLATIONS[lang]["chk_auto_subs"])

        self.lbl_header_behavior.configure(text=TRANSLATIONS[lang]["lbl_header_behavior"])
        self.chk_playlist.configure(text=TRANSLATIONS[lang]["chk_playlist"])
        self.chk_metadata.configure(text=TRANSLATIONS[lang]["chk_metadata"])
        self.chk_restrict_names.configure(text=TRANSLATIONS[lang]["chk_restrict_names"])
        self.chk_archive.configure(text=TRANSLATIONS[lang]["chk_archive"])
        self.chk_youtube_403.configure(text=TRANSLATIONS[lang]["chk_youtube_403"])
        self.chk_sponsorblock.configure(text=TRANSLATIONS[lang]["chk_sponsorblock"])

        # Placeholders
        self.playlist_items_entry.configure(placeholder_text=TRANSLATIONS[lang]["lbl_placeholder_range"])
        self.max_downloads_entry.configure(placeholder_text=TRANSLATIONS[lang]["lbl_placeholder_max"])
        self.rate_limit_entry.configure(placeholder_text=TRANSLATIONS[lang]["lbl_placeholder_speed"])
        self.cookies_entry.configure(placeholder_text=TRANSLATIONS[lang]["lbl_placeholder_cookies"])
        self.retries_entry.configure(placeholder_text=TRANSLATIONS[lang]["lbl_placeholder_retry"])
        self.concurrent_fragments_entry.configure(placeholder_text=TRANSLATIONS[lang]["lbl_placeholder_fragments"])
        self.extra_args_entry.configure(placeholder_text=TRANSLATIONS[lang]["lbl_placeholder_extra"])

        # Tab 3 bottom row
        self.lbl_template.configure(text=TRANSLATIONS[lang]["lbl_template"])
        self.update_btn.configure(text=TRANSLATIONS[lang]["btn_update"])
        self.lbl_extra_params.configure(text=TRANSLATIONS[lang]["lbl_extra_params"])

        # Stats Dashboard Card 6
        self.dashboard_title_lbl.configure(text=TRANSLATIONS[lang]["lbl_dashboard_title"])
        self.speed_card_lbl.configure(text=TRANSLATIONS[lang]["lbl_speed"])
        self.eta_card_lbl.configure(text=TRANSLATIONS[lang]["lbl_eta"])
        self.size_card_lbl.configure(text=TRANSLATIONS[lang]["lbl_size"])

        # Actions Card 7
        self.start_btn.configure(text=TRANSLATIONS[lang]["btn_start"])
        self.cancel_btn.configure(text=TRANSLATIONS[lang]["btn_cancel"])
        self.clear_btn.configure(text=TRANSLATIONS[lang]["btn_clear"])
        self.open_folder_btn.configure(text=TRANSLATIONS[lang]["btn_open_folder"])

        # Logs Toggle 8
        self.logs_switch.configure(text=TRANSLATIONS[lang]["lbl_logs_toggle"])

        # Update dynamic active labels
        if not self.is_queue_running:
            self.active_file_var.set(TRANSLATIONS[lang]["lbl_active_dl"])
            self.status_var.set(TRANSLATIONS[lang]["lbl_status_ready"])

    def _show_toast(self, title: str, message: str) -> None:
        """Dispatches a zero-dependency PowerShell command to show a native Windows 10/11 Toast Notification."""
        clean_title = title.replace("'", "`'")
        clean_message = message.replace("'", "`'")

        ps_script = f"""
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
        $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
        $toastXml = [Windows.Data.Xml.Dom.XmlDocument]::new()
        $toastXml.LoadXml($template.GetXml())
        $toastText = $toastXml.GetElementsByTagName('text')
        $toastText.Item(0).AppendChild($toastXml.CreateTextNode('{clean_title}')) | Out-Null
        $toastText.Item(1).AppendChild($toastXml.CreateTextNode('{clean_message}')) | Out-Null
        $toast = [Windows.UI.Notifications.ToastNotification]::new($toastXml)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('yt-dlp Downloader Pro').Show($toast)
        """
        def run_ps():
            try:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                subprocess.run(["powershell", "-Command", ps_script], startupinfo=startupinfo, capture_output=True)
            except Exception:
                pass
        threading.Thread(target=run_ps, daemon=True).start()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ---------------- APP HEADER ----------------
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=24, pady=(20, 8), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure((1, 2, 3), weight=0)

        # Title Block
        title_block = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_block.grid(row=0, column=0, sticky="w")

        self.title_lbl = ctk.CTkLabel(
            title_block,
            text="yt-dlp Downloader Pro",
            font=ctk.CTkFont(family="Segoe UI", size=30, weight="bold"),
            text_color=THEME_TEXT_PRIMARY,
        )
        self.title_lbl.grid(row=0, column=0, sticky="w")

        # Dynamic Theme Switcher Button
        self.theme_btn = ctk.CTkButton(
            header_frame,
            text="☀️ Light Mode",
            fg_color=THEME_CARD_BG,
            text_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_CARD_BORDER,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            width=130,
            height=36,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self._toggle_theme,
        )
        self.theme_btn.grid(row=0, column=1, padx=(0, 12), sticky="e")

        # Dynamic Language Selector Menu
        self.lang_menu = ctk.CTkOptionMenu(
            header_frame,
            values=["English", "Türkçe", "Español"],
            width=110,
            height=36,
            corner_radius=10,
            fg_color=THEME_CARD_BG,
            button_color=THEME_CARD_BG,
            button_hover_color=THEME_CARD_BORDER,
            text_color=THEME_TEXT_PRIMARY,
            dropdown_fg_color=THEME_CARD_BG,
            dropdown_hover_color=THEME_CARD_BORDER,
            dropdown_text_color=THEME_TEXT_PRIMARY,
            command=self._on_language_menu_changed,
        )
        self.lang_menu.grid(row=0, column=2, padx=(0, 12), sticky="e")
        self.lang_menu.set("English")

        # UI Scale OptionMenu
        self.ui_scale_menu = ctk.CTkOptionMenu(
            header_frame,
            values=["80%", "90%", "100%", "110%", "120%"],
            variable=self.ui_scale_var,
            width=90,
            height=36,
            corner_radius=10,
            fg_color=THEME_CARD_BG,
            button_color=THEME_CARD_BG,
            button_hover_color=THEME_CARD_BORDER,
            text_color=THEME_TEXT_PRIMARY,
            dropdown_fg_color=THEME_CARD_BG,
            dropdown_hover_color=THEME_CARD_BORDER,
            dropdown_text_color=THEME_TEXT_PRIMARY,
            command=self._apply_ui_scale,
        )
        self.ui_scale_menu.grid(row=0, column=3, sticky="e")

        # ---------------- MAIN SCROLLABLE WINDOW ----------------
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 10))
        main = self.main_scroll
        main.grid_columnconfigure(0, weight=1)

        # 1. URL & Folder input Card
        self._build_input_card(main)

        # 2. Video Preview Card
        self._build_preview_card(main)

        # 3. Quick Presets Card
        self._build_preset_card(main)

        # 4. Multi-Video Queue Card
        self._build_queue_card(main)

        # 5. Advanced Settings Tabbed Drawer
        self._build_advanced_card(main)

        # 6. Stats Dashboard Card
        self._build_dashboard_card(main)

        # 7. Actions Button Card
        self._build_actions_card(main)

        # 8. Collapsible raw system log Drawer
        self._build_logs_card(main)

        # Set default presets
        self._select_preset("1080p")
        self._refresh_mode_state()

    def _apply_ui_scale(self, value: str) -> None:
        try:
            scale = float(value.strip().replace("%", "")) / 100.0
        except ValueError:
            return
        ctk.set_widget_scaling(scale)
        ctk.set_window_scaling(scale)

    # ================= CARD 1: INPUT BAR REDESIGN =================
    def _build_input_card(self, parent: ctk.CTkFrame) -> None:
        self.input_card = ctk.CTkFrame(
            parent,
            fg_color=THEME_CARD_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            corner_radius=16,
        )
        self.input_card.grid(row=0, column=0, padx=4, pady=6, sticky="ew")
        self.input_card.grid_columnconfigure(0, weight=1)

        # URL Input section
        url_label_row = ctk.CTkFrame(self.input_card, fg_color="transparent")
        url_label_row.grid(row=0, column=0, padx=20, pady=(14, 4), sticky="ew")
        url_label_row.grid_columnconfigure(0, weight=1)
        url_label_row.grid_columnconfigure((1, 2), weight=0)

        self.url_lbl = ctk.CTkLabel(
            url_label_row,
            text="Video / Playlist Address",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=THEME_TEXT_PRIMARY,
        )
        self.url_lbl.grid(row=0, column=0, sticky="w")

        self.clipboard_badge = ctk.CTkButton(
            url_label_row,
            text="📋 Paste from Clipboard",
            fg_color=THEME_ACCENT_BLUE,
            hover_color=THEME_ACCENT_INDIGO,
            text_color="#ffffff",
            height=26,
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._paste_clipboard,
        )
        self.clipboard_badge.grid(row=0, column=1, padx=(0, 8), sticky="e")
        self.clipboard_badge.grid_remove()

        self.batch_mode_switch = ctk.CTkSwitch(
            url_label_row,
            text="Batch List Mode",
            variable=self.batch_mode_var,
            progress_color=THEME_ACCENT_INDIGO,
            text_color=THEME_TEXT_SECONDARY,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._toggle_batch_mode,
        )
        self.batch_mode_switch.grid(row=0, column=2, sticky="e")

        # URL Fields
        self.url_frame = ctk.CTkFrame(self.input_card, fg_color="transparent")
        self.url_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.url_frame.grid_columnconfigure(0, weight=1)

        # Single-line URL Input
        self.url_entry = ctk.CTkEntry(
            self.url_frame,
            placeholder_text="Paste your YouTube, Vimeo, SoundCloud or other video links here...",
            height=38,
            corner_radius=10,
            fg_color=THEME_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            text_color=THEME_TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self.url_entry.grid(row=0, column=0, sticky="ew")
        self.url_entry.insert(0, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        self.url_entry.bind("<KeyRelease>", self._on_url_keyrelease)

        # Multi-line URL Input (hidden by default)
        self.url_textbox = ctk.CTkTextbox(
            self.url_frame,
            height=86,
            corner_radius=10,
            fg_color=THEME_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            text_color=THEME_TEXT_PRIMARY,
            font=ctk.CTkFont(family="Consolas", size=12),
        )
        self.url_textbox.grid(row=0, column=0, sticky="ew")
        self.url_textbox.grid_remove()

        # Output Folder Section
        self.save_folder_lbl = ctk.CTkLabel(
            self.input_card,
            text="Output Folder Location",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=THEME_TEXT_PRIMARY,
        )
        self.save_folder_lbl.grid(row=2, column=0, padx=20, pady=(4, 4), sticky="w")

        folder_row = ctk.CTkFrame(self.input_card, fg_color="transparent")
        folder_row.grid(row=3, column=0, padx=20, pady=(0, 16), sticky="ew")
        folder_row.grid_columnconfigure(0, weight=1)
        folder_row.grid_columnconfigure(1, weight=0)

        self.output_var = ctk.StringVar(value=str(Path.home() / "Downloads" / "yt-downloads"))
        self.output_entry = ctk.CTkEntry(
            folder_row,
            textvariable=self.output_var,
            height=38,
            corner_radius=10,
            fg_color=THEME_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            text_color=THEME_TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self.output_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.browse_btn = ctk.CTkButton(
            folder_row,
            text="📂 Choose Folder",
            width=110,
            height=38,
            corner_radius=10,
            fg_color=THEME_BG,
            text_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_CARD_BORDER,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self._pick_output_dir,
        )
        self.browse_btn.grid(row=0, column=1, sticky="e")

    def _toggle_batch_mode(self) -> None:
        if self.batch_mode_var.get():
            self.url_entry.grid_remove()
            self.url_textbox.grid()
            self.url_textbox.delete("1.0", "end")
            self.url_textbox.insert("1.0", self.url_entry.get())
            self.preview_card.grid_remove()
        else:
            self.url_textbox.grid_remove()
            self.url_entry.grid()
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, self.url_textbox.get("1.0", "end-1c").splitlines()[0] if self.url_textbox.get("1.0", "end-1c").strip() else "")
            self._trigger_metadata_fetch()

    def _on_url_keyrelease(self, event) -> None:
        self._trigger_metadata_fetch()

    # ================= CARD 2: VIDEO PREVIEW CARD (FETCH) =================
    def _build_preview_card(self, parent: ctk.CTkFrame) -> None:
        self.preview_card = ctk.CTkFrame(
            parent,
            fg_color=THEME_CARD_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            corner_radius=16,
        )
        self.preview_card.grid(row=1, column=0, padx=4, pady=6, sticky="ew")
        self.preview_card.grid_columnconfigure(1, weight=1)

        # Loading visual overlay
        self.preview_loading_lbl = ctk.CTkLabel(
            self.preview_card,
            text="Fetching video info, please wait...",
            font=ctk.CTkFont(family="Segoe UI", size=13, slant="italic"),
            text_color=THEME_TEXT_SECONDARY,
        )
        self.preview_loading_lbl.grid(row=0, column=0, columnspan=2, padx=20, pady=24, sticky="ew")
        self.preview_loading_lbl.grid_remove()

        # Thumbnail display frame
        self.thumb_label = ctk.CTkLabel(self.preview_card, text="No Thumbnail", width=160, height=90, fg_color=THEME_BG, corner_radius=10)
        self.thumb_label.grid(row=0, column=0, padx=16, pady=16, sticky="w")

        # Metadata Details Frame
        meta_info = ctk.CTkFrame(self.preview_card, fg_color="transparent")
        meta_info.grid(row=0, column=1, padx=(4, 16), pady=16, sticky="nsew")
        meta_info.grid_columnconfigure(0, weight=1)

        self.preview_title_lbl = ctk.CTkLabel(
            meta_info,
            text="Video Title Loading...",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=THEME_TEXT_PRIMARY,
            anchor="w",
            justify="left",
        )
        self.preview_title_lbl.grid(row=0, column=0, sticky="w")

        self.preview_author_lbl = ctk.CTkLabel(
            meta_info,
            text="Channel Name",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME_ACCENT_BLUE,
            anchor="w",
        )
        self.preview_author_lbl.grid(row=1, column=0, sticky="w", pady=(2, 0))

        self.preview_dur_lbl = ctk.CTkLabel(
            meta_info,
            text="Duration: --:--",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=THEME_TEXT_SECONDARY,
            anchor="w",
        )
        self.preview_dur_lbl.grid(row=2, column=0, sticky="w", pady=(2, 0))

        self.preview_card.grid_remove()

    def _trigger_metadata_fetch(self) -> None:
        """Fires off an async background thread to fetch video details using in-memory yt-dlp queries."""
        if self.batch_mode_var.get():
            return

        url = self.url_entry.get().strip()
        if not url or not url.startswith(("http://", "https://")):
            self.preview_card.grid_remove()
            return

        if url == self.last_fetched_url:
            return

        self.last_fetched_url = url
        self.preview_card.grid()
        self.preview_loading_lbl.grid()
        self.thumb_label.grid_remove()
        
        self.preview_title_lbl.configure(text=TRANSLATIONS[self.current_lang]["lbl_preview_title"])
        self.preview_author_lbl.configure(text="...")
        self.preview_dur_lbl.configure(text=TRANSLATIONS[self.current_lang]["lbl_preview_dur"])

        self.metadata_thread = threading.Thread(target=self._run_metadata_fetch, args=(url,), daemon=True)
        self.metadata_thread.start()

    def _run_metadata_fetch(self, url: str) -> None:
        try:
            import yt_dlp
            ydl_opts = {
                'extract_flat': True,
                'skip_download': True,
                'quiet': True,
                'no_warnings': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            if not info:
                raise ValueError("No info extracted")

            title = info.get("title", "Unknown Video")
            uploader = info.get("uploader", info.get("channel", "Unknown Channel"))
            duration_sec = info.get("duration")

            if duration_sec:
                mins = int(duration_sec // 60)
                secs = int(duration_sec % 60)
                duration_str = f"{mins:02d}:{secs:02d}"
            else:
                duration_str = "--:--"

            thumbnail_url = info.get("thumbnail")
            local_thumb_img = None

            if thumbnail_url:
                try:
                    import hashlib
                    url_hash = hashlib.md5(url.encode()).hexdigest()
                    local_thumb_path = self.scratch_dir / f"thumb_{url_hash}.jpg"
                    
                    req = urllib.request.Request(thumbnail_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req) as response:
                        with open(local_thumb_path, 'wb') as out_file:
                            out_file.write(response.read())

                    pil_img = Image.open(local_thumb_path)
                    pil_img = pil_img.resize((160, 90), Image.Resampling.LANCZOS)
                    local_thumb_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(160, 90))
                except Exception as e:
                    print(f"Thumbnail download failed: {e}")

            self.fetched_metadata = {
                "url": url,
                "title": title,
                "uploader": uploader,
                "duration": duration_str,
                "thumbnail_img": local_thumb_img
            }
            self.ui_queue.put(("metadata_ready", self.fetched_metadata))

        except Exception as e:
            print(f"Metadata fetch failed: {e}")
            self.ui_queue.put(("metadata_error", str(e)))

    # ================= CARD 3: PRESETS SECTION REDESIGN =================
    def _build_preset_card(self, parent: ctk.CTkFrame) -> None:
        card = ctk.CTkFrame(
            parent,
            fg_color=THEME_CARD_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            corner_radius=16,
        )
        card.grid(row=2, column=0, padx=4, pady=6, sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        # Section Header
        self.preset_lbl = ctk.CTkLabel(
            card,
            text="Quick Download Format Profile",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=THEME_TEXT_PRIMARY,
        )
        self.preset_lbl.grid(row=0, column=0, padx=20, pady=(14, 4), sticky="w")

        # Grid view for quick quality cards
        presets_grid = ctk.CTkFrame(card, fg_color="transparent")
        presets_grid.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        presets_grid.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.preset_buttons: dict[str, ctk.CTkButton] = {}
        self.preset_definitions = [
            ("best", "🚀 Best Quality\n(Max Video & Audio)", "Maksimum (Best)"),
            ("1080p", "📺 Full HD 1080p\n(Balanced MP4)", "Full HD (1080p)"),
            ("720p", "⚡ Balanced Fast\n(Speedy 720p)", "Dengeli (720p)"),
            ("mp3", "🎵 High Quality Audio\n(320kbps MP3 Müzik)", "Audio"),
        ]

        for idx, (p_id, title_text, _) in enumerate(self.preset_definitions):
            btn = ctk.CTkButton(
                presets_grid,
                text=title_text,
                height=56,
                corner_radius=12,
                fg_color=THEME_BG,
                border_color=THEME_CARD_BORDER,
                border_width=1,
                text_color=THEME_TEXT_PRIMARY,
                hover_color=THEME_CARD_BORDER,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                command=lambda p=p_id: self._select_preset(p),
            )
            btn.grid(row=0, column=idx, padx=6, pady=4, sticky="ew")
            self.preset_buttons[p_id] = btn

        # Select confirm label (quality status verification)
        self.quality_hint_var = ctk.StringVar(value="")
        self.hint_label = ctk.CTkLabel(
            card,
            textvariable=self.quality_hint_var,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME_CARD_SUBTITLE,
        )
        self.hint_label.grid(row=2, column=0, padx=20, pady=(0, 14), sticky="w")

    def _select_preset(self, preset_id: str) -> None:
        """Sets the selected preset string and styles the buttons accordingly."""
        self.selected_preset_var.set(preset_id)

        for p_id, btn in self.preset_buttons.items():
            btn.configure(
                border_color=THEME_CARD_BORDER,
                fg_color=THEME_BG,
                border_width=1,
            )

        active_btn = self.preset_buttons.get(preset_id)
        if active_btn:
            active_btn.configure(
                border_color=THEME_ACCENT_BLUE,
                fg_color=THEME_CARD_BG,
                border_width=2,
            )

        # Set specific settings variables
        if preset_id == "best":
            self.mode_var.set("Video")
            self.video_profile_var.set("Maksimum (Best)")
            self.video_container_var.set("mp4")
            self.video_audio_codec_var.set("AAC")
        elif preset_id == "1080p":
            self.mode_var.set("Video")
            self.video_profile_var.set("Full HD (1080p)")
            self.video_container_var.set("mp4")
            self.video_audio_codec_var.set("AAC")
        elif preset_id == "720p":
            self.mode_var.set("Video")
            self.video_profile_var.set("Dengeli (720p)")
            self.video_container_var.set("mp4")
            self.video_audio_codec_var.set("AAC")
        elif preset_id == "mp3":
            self.mode_var.set("Audio")
            self.audio_format_var.set("mp3")
            self.audio_quality_var.set("Best")

        # Refreshes states
        self._refresh_mode_state()
        self._update_quality_hint()

    # ================= CARD 4: DOWNLOAD QUEUE MANAGER =================
    def _build_queue_card(self, parent: ctk.CTkFrame) -> None:
        self.queue_card = ctk.CTkFrame(
            parent,
            fg_color=THEME_CARD_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            corner_radius=16,
        )
        self.queue_card.grid(row=3, column=0, padx=4, pady=6, sticky="ew")
        self.queue_card.grid_columnconfigure(0, weight=1)

        # Title and stats header
        header = ctk.CTkFrame(self.queue_card, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(14, 6), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        self.queue_lbl = ctk.CTkLabel(
            header,
            text="Download Queue & Manager",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=THEME_TEXT_PRIMARY,
        )
        self.queue_lbl.grid(row=0, column=0, sticky="w")

        # Add to Queue Button
        self.add_queue_btn = ctk.CTkButton(
            header,
            text="➕ Add to Queue",
            fg_color=THEME_ACCENT_BLUE,
            hover_color=THEME_ACCENT_INDIGO,
            text_color="#ffffff",
            height=30,
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self._add_to_queue,
        )
        self.add_queue_btn.grid(row=0, column=1, sticky="e")

        # Visual Scroll area for queue items
        self.queue_scroll = ctk.CTkScrollableFrame(self.queue_card, height=130, fg_color=THEME_BG, corner_radius=12)
        self.queue_scroll.grid(row=1, column=0, padx=20, pady=(0, 16), sticky="ew")
        self.queue_scroll.grid_columnconfigure(0, weight=1)

        # Render placeholder
        self.queue_placeholder = ctk.CTkLabel(
            self.queue_scroll,
            text="Queue empty. Add links above to download.",
            font=ctk.CTkFont(family="Segoe UI", size=12, slant="italic"),
            text_color=THEME_TEXT_SECONDARY,
        )
        self.queue_placeholder.grid(row=0, column=0, pady=40, sticky="ew")

    def _add_to_queue(self) -> None:
        """Captures all currently selected options and pushes them to the queue as a self-contained dict object."""
        urls = []
        if self.batch_mode_var.get():
            urls = [line.strip() for line in self.url_textbox.get("1.0", "end").splitlines() if line.strip()]
        else:
            url = self.url_entry.get().strip()
            if url:
                urls = [url]

        if not urls:
            messagebox.showwarning(TRANSLATIONS[self.current_lang]["lbl_dialog_warning_title"], TRANSLATIONS[self.current_lang]["lbl_dialog_warning_url"])
            return

        for url in urls:
            title = url
            thumb_img = None
            if self.fetched_metadata and self.fetched_metadata["url"] == url:
                title = self.fetched_metadata["title"]
                thumb_img = self.fetched_metadata["thumbnail_img"]

            queue_item = {
                "url": url,
                "title": title,
                "thumb_img": thumb_img,
                "preset": self.selected_preset_var.get(),
                "status": "Bekliyor" if self.current_lang == "tr" else ("Pendiente" if self.current_lang == "es" else "Waiting"),
                "progress": 0.0,
                # Option States Captured
                "mode": self.mode_var.get(),
                "video_profile": self.video_profile_var.get(),
                "video_limit": self.custom_video_height_var.get(),
                "video_container": self.video_container_var.get(),
                "audio_format": self.audio_format_var.get(),
                "audio_quality": self.audio_quality_var.get(),
                "video_audio_codec": self.video_audio_codec_var.get(),
                "playlist_items": self.playlist_items_var.get(),
                "max_downloads": self.max_downloads_var.get(),
                "rate_limit": self.rate_limit_var.get(),
                "cookies": self.cookies_var.get(),
                "browser_cookies": self.browser_cookies_var.get(),
                "retries": self.retries_var.get(),
                "concurrent_fragments": self.concurrent_fragments_var.get(),
                "playlist": self.playlist_var.get(),
                "metadata": self.metadata_var.get(),
                "thumbnail_flag": self.thumbnail_var.get(),
                "subs": self.subs_var.get(),
                "auto_subs": self.auto_subs_var.get(),
                "restrict_names": self.restrict_names_var.get(),
                "archive": self.download_archive_var.get(),
                "youtube_403": self.youtube_403_fallback_var.get(),
                "extra_args": self.extra_args_var.get(),
                "output_template": self.output_template_var.get()
            }
            self.queue_list.append(queue_item)

        if not self.batch_mode_var.get():
            self.url_entry.delete(0, "end")
            self.preview_card.grid_remove()

        self._update_queue_ui()
        self._update_status_indicator("●", THEME_ACCENT_BLUE, TRANSLATIONS[self.current_lang]["lbl_status_added"].format(count=len(urls)))

    def _remove_from_queue(self, idx: int) -> None:
        if 0 <= idx < len(self.queue_list):
            if self.is_queue_running and self.current_queue_idx == idx:
                messagebox.showwarning("Blocked" if self.current_lang == "en" else "Bloqueado", "Cannot remove active downloading item.")
                return
            self.queue_list.pop(idx)
            self._update_queue_ui()

    def _update_queue_ui(self) -> None:
        """Cleans and re-renders all visual queue frame components styled like rounded glassy list elements."""
        for w in self.queue_scroll.winfo_children():
            w.destroy()

        if not self.queue_list:
            self.queue_placeholder = ctk.CTkLabel(
                self.queue_scroll,
                text=TRANSLATIONS[self.current_lang]["lbl_queue_item_placeholder"],
                font=ctk.CTkFont(family="Segoe UI", size=12, slant="italic"),
                text_color=THEME_TEXT_SECONDARY,
            )
            self.queue_placeholder.grid(row=0, column=0, pady=40, sticky="ew")
            return

        for idx, item in enumerate(self.queue_list):
            card = ctk.CTkFrame(
                self.queue_scroll,
                fg_color=THEME_CARD_BG,
                border_color=THEME_CARD_BORDER,
                border_width=1,
                corner_radius=10
            )
            card.grid(row=idx, column=0, padx=6, pady=4, sticky="ew")
            card.grid_columnconfigure(1, weight=1)
            card.grid_columnconfigure((0, 2, 3, 4), weight=0)

            # 1. Status Dot Indicator
            dot_color = THEME_TEXT_SECONDARY
            active_status = item["status"]
            if "Wait" in active_status or "Bek" in active_status or "Pen" in active_status:
                dot_color = THEME_ACCENT_BLUE
            elif "İndir" in active_status or "Down" in active_status or "Desc" in active_status:
                dot_color = THEME_ACCENT_INDIGO
            elif "Tamam" in active_status or "Comp" in active_status or "Exit" in active_status:
                dot_color = THEME_ACCENT_GREEN
            elif "Hata" in active_status or "Err" in active_status or "Iptal" in active_status or "Canc" in active_status:
                dot_color = THEME_ACCENT_RED

            ctk.CTkLabel(card, text="●", text_color=dot_color, font=ctk.CTkFont(size=14)).grid(row=0, column=0, padx=(12, 6))

            # 2. Text Title
            title_text = item["title"]
            if len(title_text) > 60:
                title_text = title_text[:57] + "..."
            title_lbl = ctk.CTkLabel(card, text=title_text, font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=THEME_TEXT_PRIMARY, anchor="w")
            title_lbl.grid(row=0, column=1, padx=6, pady=8, sticky="w")

            # 3. Format badge
            badge_text = f"[{item['preset'].upper()}]"
            badge_color = THEME_CARD_SUBTITLE
            if item["mode"] == "Audio":
                badge_color = ("#8b5cf6", "#a78bfa")
            badge_lbl = ctk.CTkLabel(card, text=badge_text, text_color=badge_color, font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"))
            badge_lbl.grid(row=0, column=2, padx=10)

            # 4. Progress or Status Label
            status_lbl = ctk.CTkLabel(card, text=item["status"], font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=THEME_TEXT_SECONDARY)
            status_lbl.grid(row=0, column=3, padx=10)

            # 5. Remove Button
            rem_btn = ctk.CTkButton(
                card,
                text=TRANSLATIONS[self.current_lang]["lbl_queue_remove"],
                width=60,
                height=26,
                fg_color=THEME_BG,
                hover_color=THEME_ACCENT_RED,
                text_color=THEME_TEXT_PRIMARY,
                border_color=THEME_CARD_BORDER,
                border_width=1,
                corner_radius=6,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                command=lambda i=idx: self._remove_from_queue(i)
            )
            rem_btn.grid(row=0, column=4, padx=(6, 12))

    # ================= CARD 5: TABBED ADVANCED DRAWER =================
    def _build_advanced_card(self, parent: ctk.CTkFrame) -> None:
        self.show_advanced_var = ctk.BooleanVar(value=False)

        self.adv_header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.adv_header_frame.grid(row=4, column=0, padx=8, pady=4, sticky="w")

        self.advanced_switch = ctk.CTkSwitch(
            self.adv_header_frame,
            text="Show Advanced Download & File Settings",
            variable=self.show_advanced_var,
            progress_color=THEME_ACCENT_INDIGO,
            text_color=THEME_TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self._toggle_advanced_section,
        )
        self.advanced_switch.grid(row=0, column=0, sticky="w")

        # Descriptive visual hint label
        self.adv_hint_lbl = ctk.CTkLabel(
            self.adv_header_frame,
            text="(Resolution, codec formats, cookies, speed limits and extra yt-dlp arguments)",
            font=ctk.CTkFont(family="Segoe UI", size=11, slant="italic"),
            text_color=THEME_TEXT_SECONDARY,
        )
        self.adv_hint_lbl.grid(row=1, column=0, sticky="w", padx=26)

        # Collapsible Main Frame
        self.advanced_frame = ctk.CTkFrame(
            parent,
            fg_color=THEME_CARD_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            corner_radius=16,
        )
        self.advanced_frame.grid(row=5, column=0, padx=4, pady=(2, 6), sticky="ew")
        self.advanced_frame.grid_columnconfigure(0, weight=1)

        # Tabview Integration for Premium Organization
        self.tabview = ctk.CTkTabview(
            self.advanced_frame,
            height=280,
            corner_radius=12,
            fg_color=THEME_CARD_BG,
            segmented_button_selected_color=THEME_ACCENT_INDIGO,
            segmented_button_selected_hover_color=THEME_ACCENT_BLUE,
            segmented_button_unselected_color=THEME_BG,
            segmented_button_unselected_hover_color=THEME_CARD_BORDER,
            text_color=THEME_TEXT_PRIMARY,
        )
        self.tabview.grid(row=0, column=0, padx=16, pady=12, sticky="nsew")

        tab_codec = self.tabview.add("Çözünürlük & Kodek")
        tab_limits = self.tabview.add("Limitler & Çerezler")
        tab_flags = self.tabview.add("İndirme İzinleri")

        # ------------ TAB 1: CODECS ------------
        tab_codec.grid_columnconfigure((0, 1), weight=1)

        c1 = ctk.CTkFrame(tab_codec, fg_color="transparent")
        c1.grid(row=0, column=0, padx=10, pady=8, sticky="nsew")
        c1.grid_columnconfigure(1, weight=1)

        self.lbl_mode = ctk.CTkLabel(c1, text="Download Mode:", text_color=THEME_TEXT_PRIMARY)
        self.lbl_mode.grid(row=0, column=0, sticky="w", padx=6, pady=6)
        
        self.mode_var = ctk.StringVar(value="Video")
        self.mode_switch = ctk.CTkSegmentedButton(
            c1,
            values=["Video", "Audio"],
            variable=self.mode_var,
            selected_color=THEME_ACCENT_INDIGO,
            unselected_color=THEME_BG,
            unselected_hover_color=THEME_CARD_BORDER,
            text_color=THEME_TEXT_PRIMARY,
            command=self._on_mode_changed,
        )
        self.mode_switch.grid(row=0, column=1, sticky="ew", padx=6, pady=6)

        self.lbl_profile = ctk.CTkLabel(c1, text="Quality Profile:", text_color=THEME_TEXT_PRIMARY)
        self.lbl_profile.grid(row=1, column=0, sticky="w", padx=6, pady=6)
        
        self.video_profile_var = ctk.StringVar(value="Full HD (1080p)")
        self.video_profile_menu = ctk.CTkOptionMenu(
            c1,
            values=list(VIDEO_PRESET_HEIGHT.keys()),
            variable=self.video_profile_var,
            fg_color=THEME_BG,
            button_color=THEME_BG,
            button_hover_color=THEME_CARD_BORDER,
            text_color=THEME_TEXT_PRIMARY,
            dropdown_fg_color=THEME_CARD_BG,
            dropdown_hover_color=THEME_CARD_BORDER,
            dropdown_text_color=THEME_TEXT_PRIMARY,
            command=self._on_video_profile_changed,
        )
        self.video_profile_menu.grid(row=1, column=1, sticky="ew", padx=6, pady=6)

        self.lbl_max_res = ctk.CTkLabel(c1, text="Max Resolution:", text_color=THEME_TEXT_PRIMARY)
        self.lbl_max_res.grid(row=2, column=0, sticky="w", padx=6, pady=6)
        
        self.custom_video_height_var = ctk.StringVar(value="1080")
        self.video_limit_menu = ctk.CTkOptionMenu(
            c1,
            values=["2160", "1440", "1080", "720", "480", "360"],
            variable=self.custom_video_height_var,
            fg_color=THEME_BG,
            button_color=THEME_BG,
            button_hover_color=THEME_CARD_BORDER,
            text_color=THEME_TEXT_PRIMARY,
            dropdown_fg_color=THEME_CARD_BG,
            dropdown_hover_color=THEME_CARD_BORDER,
            dropdown_text_color=THEME_TEXT_PRIMARY,
            command=lambda _: self._update_quality_hint(),
        )
        self.video_limit_menu.grid(row=2, column=1, sticky="ew", padx=6, pady=6)

        c2 = ctk.CTkFrame(tab_codec, fg_color="transparent")
        c2.grid(row=0, column=1, padx=10, pady=8, sticky="nsew")
        c2.grid_columnconfigure(1, weight=1)

        self.lbl_format = ctk.CTkLabel(c2, text="Video Format:", text_color=THEME_TEXT_PRIMARY)
        self.lbl_format.grid(row=0, column=0, sticky="w", padx=6, pady=6)
        
        self.video_container_var = ctk.StringVar(value="mp4")
        self.video_container_menu = ctk.CTkOptionMenu(
            c2,
            values=["mp4", "mkv", "webm"],
            variable=self.video_container_var,
            fg_color=THEME_BG,
            button_color=THEME_BG,
            button_hover_color=THEME_CARD_BORDER,
            text_color=THEME_TEXT_PRIMARY,
            dropdown_fg_color=THEME_CARD_BG,
            dropdown_hover_color=THEME_CARD_BORDER,
            dropdown_text_color=THEME_TEXT_PRIMARY,
        )
        self.video_container_menu.grid(row=0, column=1, sticky="ew", padx=6, pady=6)

        self.lbl_audio_ext = ctk.CTkLabel(c2, text="Audio Extension:", text_color=THEME_TEXT_PRIMARY)
        self.lbl_audio_ext.grid(row=1, column=0, sticky="w", padx=6, pady=6)
        
        self.audio_format_var = ctk.StringVar(value="mp3")
        self.audio_format_menu = ctk.CTkOptionMenu(
            c2,
            values=["mp3", "aac", "opus", "m4a", "wav", "flac"],
            variable=self.audio_format_var,
            fg_color=THEME_BG,
            button_color=THEME_BG,
            button_hover_color=THEME_CARD_BORDER,
            text_color=THEME_TEXT_PRIMARY,
            dropdown_fg_color=THEME_CARD_BG,
            dropdown_hover_color=THEME_CARD_BORDER,
            dropdown_text_color=THEME_TEXT_PRIMARY,
            command=lambda _: self._update_quality_hint(),
        )
        self.audio_format_menu.grid(row=1, column=1, sticky="ew", padx=6, pady=6)

        self.lbl_audio_qual = ctk.CTkLabel(c2, text="Audio Quality:", text_color=THEME_TEXT_PRIMARY)
        self.lbl_audio_qual.grid(row=2, column=0, sticky="w", padx=6, pady=6)
        
        self.audio_quality_var = ctk.StringVar(value="Dengeli (192K)")
        self.audio_quality_menu = ctk.CTkOptionMenu(
            c2,
            values=list(AUDIO_PRESET_QUALITY.keys()),
            variable=self.audio_quality_var,
            fg_color=THEME_BG,
            button_color=THEME_BG,
            button_hover_color=THEME_CARD_BORDER,
            text_color=THEME_TEXT_PRIMARY,
            dropdown_fg_color=THEME_CARD_BG,
            dropdown_hover_color=THEME_CARD_BORDER,
            dropdown_text_color=THEME_TEXT_PRIMARY,
            command=lambda _: self._update_quality_hint(),
        )
        self.audio_quality_menu.grid(row=2, column=1, sticky="ew", padx=6, pady=6)

        self.video_audio_codec_var = ctk.StringVar(value="AAC")
        self.video_audio_codec_menu = ctk.CTkOptionMenu(
            c2,
            values=VIDEO_AUDIO_CODEC_OPTIONS,
            variable=self.video_audio_codec_var,
            fg_color=THEME_BG,
            button_color=THEME_BG,
            button_hover_color=THEME_CARD_BORDER,
            text_color=THEME_TEXT_PRIMARY,
            dropdown_fg_color=THEME_CARD_BG,
            dropdown_hover_color=THEME_CARD_BORDER,
            dropdown_text_color=THEME_TEXT_PRIMARY,
            command=lambda _: self._update_quality_hint(),
        )
        self.video_audio_codec_menu.grid(row=3, column=1, sticky="ew", padx=6, pady=6)
        self.video_audio_codec_lbl = ctk.CTkLabel(c2, text="Audio Codec (Video):", text_color=THEME_TEXT_PRIMARY)
        self.video_audio_codec_lbl.grid(row=3, column=0, sticky="w", padx=6, pady=6)

        # ------------ TAB 2: LIMITS & COOKIES ------------
        tab_limits.grid_columnconfigure((0, 1), weight=1)

        l1 = ctk.CTkFrame(tab_limits, fg_color="transparent")
        l1.grid(row=0, column=0, padx=10, pady=8, sticky="nsew")
        l1.grid_columnconfigure(1, weight=1)

        self.lbl_playlist_range = ctk.CTkLabel(l1, text="Playlist Range:", text_color=THEME_TEXT_PRIMARY)
        self.lbl_playlist_range.grid(row=0, column=0, sticky="w", padx=6, pady=6)
        
        self.playlist_items_var = ctk.StringVar(value="")
        self.playlist_items_entry = ctk.CTkEntry(l1, textvariable=self.playlist_items_var, placeholder_text="Ex: 1-10, 15", height=30, fg_color=THEME_BG, border_color=THEME_CARD_BORDER, border_width=1, text_color=THEME_TEXT_PRIMARY)
        self.playlist_items_entry.grid(row=0, column=1, sticky="ew", padx=6, pady=6)

        self.lbl_max_dl = ctk.CTkLabel(l1, text="Max Downloads:", text_color=THEME_TEXT_PRIMARY)
        self.lbl_max_dl.grid(row=1, column=0, sticky="w", padx=6, pady=6)
        
        self.max_downloads_var = ctk.StringVar(value="")
        self.max_downloads_entry = ctk.CTkEntry(l1, textvariable=self.max_downloads_var, placeholder_text="Ex: 5", height=30, fg_color=THEME_BG, border_color=THEME_CARD_BORDER, border_width=1, text_color=THEME_TEXT_PRIMARY)
        self.max_downloads_entry.grid(row=1, column=1, sticky="ew", padx=6, pady=6)

        self.lbl_speed_limit = ctk.CTkLabel(l1, text="Speed Limit:", text_color=THEME_TEXT_PRIMARY)
        self.lbl_speed_limit.grid(row=2, column=0, sticky="w", padx=6, pady=6)
        
        self.rate_limit_var = ctk.StringVar(value="")
        self.rate_limit_entry = ctk.CTkEntry(l1, textvariable=self.rate_limit_var, placeholder_text="Ex: 2M or 500K", height=30, fg_color=THEME_BG, border_color=THEME_CARD_BORDER, border_width=1, text_color=THEME_TEXT_PRIMARY)
        self.rate_limit_entry.grid(row=2, column=1, sticky="ew", padx=6, pady=6)

        l2 = ctk.CTkFrame(tab_limits, fg_color="transparent")
        l2.grid(row=0, column=1, padx=10, pady=8, sticky="nsew")
        l2.grid_columnconfigure(1, weight=1)

        self.lbl_cookie_file = ctk.CTkLabel(l2, text="Cookie File (.txt):", text_color=THEME_TEXT_PRIMARY)
        self.lbl_cookie_file.grid(row=0, column=0, sticky="w", padx=6, pady=6)
        
        cookies_row = ctk.CTkFrame(l2, fg_color="transparent")
        cookies_row.grid(row=0, column=1, sticky="ew", padx=6, pady=6)
        cookies_row.grid_columnconfigure(0, weight=1)
        self.cookies_var = ctk.StringVar(value="")
        self.cookies_entry = ctk.CTkEntry(cookies_row, textvariable=self.cookies_var, placeholder_text="Select path...", height=30, fg_color=THEME_BG, border_color=THEME_CARD_BORDER, border_width=1, text_color=THEME_TEXT_PRIMARY)
        self.cookies_entry.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ctk.CTkButton(cookies_row, text="Select" if self.current_lang=="en" else ("Sec" if self.current_lang=="tr" else "Selec"), width=40, height=30, fg_color=THEME_BG, text_color=THEME_TEXT_PRIMARY, hover_color=THEME_CARD_BORDER, border_color=THEME_CARD_BORDER, border_width=1, command=self._pick_cookies_file).grid(row=0, column=1)

        self.lbl_browser_cookie = ctk.CTkLabel(l2, text="Browser Cookies:", text_color=THEME_TEXT_PRIMARY)
        self.lbl_browser_cookie.grid(row=1, column=0, sticky="w", padx=6, pady=6)
        
        self.browser_cookies_var = ctk.StringVar(value="Kapali")
        self.browser_cookies_menu = ctk.CTkOptionMenu(l2, values=BROWSER_COOKIE_SOURCES, variable=self.browser_cookies_var, fg_color=THEME_BG, button_color=THEME_BG, button_hover_color=THEME_CARD_BORDER, text_color=THEME_TEXT_PRIMARY, dropdown_fg_color=THEME_CARD_BG, dropdown_hover_color=THEME_CARD_BORDER, dropdown_text_color=THEME_TEXT_PRIMARY, height=30)
        self.browser_cookies_menu.grid(row=1, column=1, sticky="ew", padx=6, pady=6)

        self.lbl_retry = ctk.CTkLabel(l2, text="Retry Counts:", text_color=THEME_TEXT_PRIMARY)
        self.lbl_retry.grid(row=2, column=0, sticky="w", padx=6, pady=6)
        
        self.retries_var = ctk.StringVar(value="")
        self.retries_entry = ctk.CTkEntry(l2, textvariable=self.retries_var, placeholder_text="Ex: 10", height=30, fg_color=THEME_BG, border_color=THEME_CARD_BORDER, border_width=1, text_color=THEME_TEXT_PRIMARY)
        self.retries_entry.grid(row=2, column=1, sticky="ew", padx=6, pady=6)

        # ------------ TAB 3: FLAGS & CHECKBOXES ------------
        tab_flags.grid_columnconfigure((0, 1), weight=1)

        f1 = ctk.CTkFrame(tab_flags, fg_color="transparent")
        f1.grid(row=0, column=0, padx=10, pady=4, sticky="nsew")
        
        self.lbl_header_addons = ctk.CTkLabel(f1, text="Media Add-ons", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=THEME_ACCENT_BLUE)
        self.lbl_header_addons.grid(row=0, column=0, sticky="w", padx=6, pady=2)

        self.thumbnail_var = ctk.BooleanVar(value=False)
        self.subs_var = ctk.BooleanVar(value=False)
        self.auto_subs_var = ctk.BooleanVar(value=False)

        self.chk_thumb = ctk.CTkCheckBox(f1, text="Download Visual (Thumbnail)", variable=self.thumbnail_var, fg_color=THEME_ACCENT_INDIGO, text_color=THEME_TEXT_PRIMARY)
        self.chk_thumb.grid(row=1, column=0, padx=6, pady=4, sticky="w")
        
        self.chk_subs = ctk.CTkCheckBox(f1, text="Download Subtitle Files", variable=self.subs_var, fg_color=THEME_ACCENT_INDIGO, text_color=THEME_TEXT_PRIMARY, command=self._on_subs_toggled)
        self.chk_subs.grid(row=2, column=0, padx=6, pady=4, sticky="w")
        
        self.auto_subs_check = ctk.CTkCheckBox(f1, text="Auto Translation Subtitles", variable=self.auto_subs_var, fg_color=THEME_ACCENT_INDIGO, text_color=THEME_TEXT_PRIMARY)
        self.auto_subs_check.grid(row=3, column=0, padx=18, pady=4, sticky="w")

        f2 = ctk.CTkFrame(tab_flags, fg_color="transparent")
        f2.grid(row=0, column=1, padx=10, pady=4, sticky="nsew")
        
        self.lbl_header_behavior = ctk.CTkLabel(f2, text="Download Behaviors", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=THEME_ACCENT_BLUE)
        self.lbl_header_behavior.grid(row=0, column=0, sticky="w", padx=6, pady=2)

        self.playlist_var = ctk.BooleanVar(value=True)
        self.metadata_var = ctk.BooleanVar(value=True)
        self.restrict_names_var = ctk.BooleanVar(value=False)
        self.download_archive_var = ctk.BooleanVar(value=True)
        self.youtube_403_fallback_var = ctk.BooleanVar(value=True)
        self.sponsorblock_var = ctk.BooleanVar(value=False)

        self.chk_playlist = ctk.CTkCheckBox(f2, text="Process as Playlist", variable=self.playlist_var, fg_color=THEME_ACCENT_INDIGO, text_color=THEME_TEXT_PRIMARY)
        self.chk_playlist.grid(row=1, column=0, padx=6, pady=2, sticky="w")
        
        self.chk_metadata = ctk.CTkCheckBox(f2, text="Add Metadata Tags", variable=self.metadata_var, fg_color=THEME_ACCENT_INDIGO, text_color=THEME_TEXT_PRIMARY)
        self.chk_metadata.grid(row=2, column=0, padx=6, pady=2, sticky="w")
        
        self.chk_restrict_names = ctk.CTkCheckBox(f2, text="Clean Filenames (Safe Characters)", variable=self.restrict_names_var, fg_color=THEME_ACCENT_INDIGO, text_color=THEME_TEXT_PRIMARY)
        self.chk_restrict_names.grid(row=3, column=0, padx=6, pady=2, sticky="w")
        
        self.chk_archive = ctk.CTkCheckBox(f2, text="Use Download Archive (Skip existing)", variable=self.download_archive_var, fg_color=THEME_ACCENT_INDIGO, text_color=THEME_TEXT_PRIMARY)
        self.chk_archive.grid(row=4, column=0, padx=6, pady=2, sticky="w")
        
        self.chk_youtube_403 = ctk.CTkCheckBox(f2, text="TV Client Fallback on YouTube 403", variable=self.youtube_403_fallback_var, fg_color=THEME_ACCENT_INDIGO, text_color=THEME_TEXT_PRIMARY)
        self.chk_youtube_403.grid(row=5, column=0, padx=6, pady=2, sticky="w")
        
        self.chk_sponsorblock = ctk.CTkCheckBox(f2, text="SponsorBlock (Cut sponsor segments)", variable=self.sponsorblock_var, fg_color=THEME_ACCENT_INDIGO, text_color=THEME_TEXT_PRIMARY)
        self.chk_sponsorblock.grid(row=6, column=0, padx=6, pady=2, sticky="w")

        # Bottom drawer templates & updates
        bottom_options = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
        bottom_options.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="ew")
        bottom_options.grid_columnconfigure(1, weight=1)
        bottom_options.grid_columnconfigure(2, weight=0)

        self.lbl_template = ctk.CTkLabel(bottom_options, text="Filename Template:", text_color=THEME_TEXT_PRIMARY)
        self.lbl_template.grid(row=0, column=0, sticky="w", padx=6, pady=4)
        
        self.output_template_var = ctk.StringVar(value=DEFAULT_OUTPUT_TEMPLATE)
        self.output_template_entry = ctk.CTkEntry(bottom_options, textvariable=self.output_template_var, height=30, fg_color=THEME_BG, border_color=THEME_CARD_BORDER, border_width=1, text_color=THEME_TEXT_PRIMARY)
        self.output_template_entry.grid(row=0, column=1, sticky="ew", padx=6, pady=4)
        self.output_template_entry.bind("<KeyRelease>", self._update_template_preview)

        # Version & Update Button
        self.update_btn = ctk.CTkButton(
            bottom_options,
            text="🔄 Update yt-dlp",
            width=130,
            height=30,
            fg_color=THEME_BG,
            text_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_ACCENT_BLUE,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._update_ytdlp,
        )
        self.update_btn.grid(row=0, column=2, padx=6, pady=4)

        # Template Preview Label
        self.template_preview_var = ctk.StringVar(value="")
        self.template_preview_lbl = ctk.CTkLabel(
            bottom_options,
            textvariable=self.template_preview_var,
            font=ctk.CTkFont(family="Segoe UI", size=11, slant="italic"),
            text_color=THEME_CARD_SUBTITLE,
        )
        self.template_preview_lbl.grid(row=1, column=1, sticky="w", padx=6)

        # Concurrent fragments & Extra args
        bottom_options2 = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
        bottom_options2.grid(row=2, column=0, padx=16, pady=(0, 16), sticky="ew")
        bottom_options2.grid_columnconfigure(1, weight=1)
        bottom_options2.grid_columnconfigure(3, weight=1)

        self.lbl_concurrent = ctk.CTkLabel(bottom_options2, text="Concurrent Fragments:", text_color=THEME_TEXT_PRIMARY)
        self.lbl_concurrent.grid(row=0, column=0, sticky="w", padx=6, pady=4)
        
        self.concurrent_fragments_var = ctk.StringVar(value="")
        self.concurrent_fragments_entry = ctk.CTkEntry(bottom_options2, textvariable=self.concurrent_fragments_var, placeholder_text="Ex: 4", height=30, fg_color=THEME_BG, border_color=THEME_CARD_BORDER, border_width=1, text_color=THEME_TEXT_PRIMARY)
        self.concurrent_fragments_entry.grid(row=0, column=1, sticky="ew", padx=6, pady=4)

        self.lbl_extra_params = ctk.CTkLabel(bottom_options2, text="Extra Parameters:", text_color=THEME_TEXT_PRIMARY)
        self.lbl_extra_params.grid(row=0, column=2, sticky="w", padx=6, pady=4)
        
        self.extra_args_var = ctk.StringVar(value="")
        self.extra_args_entry = ctk.CTkEntry(bottom_options2, textvariable=self.extra_args_var, placeholder_text="Ex: --sleep-interval 1", height=30, fg_color=THEME_BG, border_color=THEME_CARD_BORDER, border_width=1, text_color=THEME_TEXT_PRIMARY)
        self.extra_args_entry.grid(row=0, column=3, sticky="ew", padx=6, pady=4)

        self._toggle_advanced_section()
        self._on_subs_toggled()
        self._update_template_preview()

    def _on_subs_toggled(self) -> None:
        """Enforces dependency check: disables auto-subs unless subtitle downloads is checked."""
        if self.subs_var.get():
            self.auto_subs_check.configure(state="normal")
        else:
            self.auto_subs_check.configure(state="disabled")
            self.auto_subs_var.set(False)

    def _update_template_preview(self, event=None) -> None:
        template = self.output_template_var.get().strip()
        if not template:
            template = DEFAULT_OUTPUT_TEMPLATE

        mock_title = "Rick Astley - Never Gonna Give You Up"
        mock_id = "dQw4w9WgXcQ"
        mock_ext = "mp3" if self.mode_var.get() == "Audio" else self.video_container_var.get()

        preview = template.replace("%(title)s", mock_title).replace("%(id)s", mock_id).replace("%(ext)s", mock_ext)
        preview_text = TRANSLATIONS[self.current_lang]["preview_name_label"].format(preview=preview)
        self.template_preview_var.set(preview_text)

    def _update_ytdlp(self) -> None:
        self.update_btn.configure(state="disabled", text="Guncelleniyor..." if self.current_lang=="tr" else ("Actualizando..." if self.current_lang=="es" else "Updating..."))
        self._append_log(f"[info] yt-dlp update process started...\n")
        
        def run_update():
            try:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                p = subprocess.run([sys.executable, "-m", "pip", "install", "-U", "yt-dlp"], startupinfo=startupinfo, capture_output=True, text=True)
                if p.returncode == 0:
                    self.ui_queue.put(("log", "[info] yt-dlp updated to the latest version successfully!\n"))
                    self.ui_queue.put(("toast_update", None))
                else:
                    self.ui_queue.put(("log", f"[error] Update failed: {p.stderr}\n"))
            except Exception as e:
                self.ui_queue.put(("log", f"[error] {e}\n"))
            finally:
                self.ui_queue.put(("update_done", None))

        threading.Thread(target=run_update, daemon=True).start()

    # ================= CARD 6: STATS DASHBOARD CARD =================
    def _build_dashboard_card(self, parent: ctk.CTkFrame) -> None:
        self.dashboard_card = ctk.CTkFrame(
            parent,
            fg_color=THEME_CARD_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            corner_radius=16,
        )
        self.dashboard_card.grid(row=6, column=0, padx=4, pady=6, sticky="ew")
        self.dashboard_card.grid_columnconfigure(0, weight=1)

        # Header Title
        self.dashboard_title_lbl = ctk.CTkLabel(
            self.dashboard_card,
            text="Active Download Progress Panel",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=THEME_TEXT_PRIMARY,
        )
        self.dashboard_title_lbl.grid(row=0, column=0, padx=20, pady=(14, 6), sticky="w")

        # Current Downloading Video Title
        self.active_file_label = ctk.CTkLabel(
            self.dashboard_card,
            textvariable=self.active_file_var,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME_ACCENT_BLUE,
            anchor="w",
            justify="left",
        )
        self.active_file_label.grid(row=1, column=0, padx=20, pady=(0, 8), sticky="ew")

        # Dynamic Grid of Stats Metrics (3 columns)
        stats_grid = ctk.CTkFrame(self.dashboard_card, fg_color="transparent")
        stats_grid.grid(row=2, column=0, padx=20, pady=(4, 16), sticky="ew")
        stats_grid.grid_columnconfigure((0, 1, 2), weight=1)

        # Metric 1: Speed Card
        s_card = ctk.CTkFrame(stats_grid, fg_color=THEME_BG, corner_radius=12, border_color=THEME_CARD_BORDER, border_width=1)
        s_card.grid(row=0, column=0, padx=6, pady=4, sticky="ew")
        self.speed_card_lbl = ctk.CTkLabel(s_card, text="Download Speed", text_color=THEME_TEXT_SECONDARY, font=ctk.CTkFont(size=11))
        self.speed_card_lbl.pack(pady=(8, 2))
        self.speed_stat_var = ctk.StringVar(value="0.0 MB/s")
        ctk.CTkLabel(s_card, textvariable=self.speed_stat_var, text_color=THEME_TEXT_PRIMARY, font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(0, 8))

        # Metric 2: ETA Card
        e_card = ctk.CTkFrame(stats_grid, fg_color=THEME_BG, corner_radius=12, border_color=THEME_CARD_BORDER, border_width=1)
        e_card.grid(row=0, column=1, padx=6, pady=4, sticky="ew")
        self.eta_card_lbl = ctk.CTkLabel(e_card, text="Remaining Time (ETA)", text_color=THEME_TEXT_SECONDARY, font=ctk.CTkFont(size=11))
        self.eta_card_lbl.pack(pady=(8, 2))
        self.eta_stat_var = ctk.StringVar(value="00:00")
        ctk.CTkLabel(e_card, textvariable=self.eta_stat_var, text_color=THEME_TEXT_PRIMARY, font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(0, 8))

        # Metric 3: File Size Card
        sz_card = ctk.CTkFrame(stats_grid, fg_color=THEME_BG, corner_radius=12, border_color=THEME_CARD_BORDER, border_width=1)
        sz_card.grid(row=0, column=2, padx=6, pady=4, sticky="ew")
        self.size_card_lbl = ctk.CTkLabel(sz_card, text="Total File Size", text_color=THEME_TEXT_SECONDARY, font=ctk.CTkFont(size=11))
        self.size_card_lbl.pack(pady=(8, 2))
        self.size_stat_var = ctk.StringVar(value="0.0 MB")
        ctk.CTkLabel(sz_card, textvariable=self.size_stat_var, text_color=THEME_TEXT_PRIMARY, font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(0, 8))

    # ================= CARD 7: BUTTON HIERARCHY OVERHAUL =================
    def _build_actions_card(self, parent: ctk.CTkFrame) -> None:
        card = ctk.CTkFrame(
            parent,
            fg_color=THEME_CARD_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            corner_radius=16,
        )
        card.grid(row=7, column=0, padx=4, pady=6, sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        # Primary vs Secondary visual structure
        btn_grid = ctk.CTkFrame(card, fg_color="transparent")
        btn_grid.grid(row=0, column=0, padx=20, pady=(16, 12), sticky="ew")
        btn_grid.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # 1. Start Button (Huge primary action)
        self.start_btn = ctk.CTkButton(
            btn_grid,
            text="🚀 Start Downloads",
            height=44,
            corner_radius=10,
            fg_color=THEME_ACCENT_INDIGO,
            text_color="#ffffff",
            hover_color=THEME_ACCENT_BLUE,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            command=self._start_download,
        )
        self.start_btn.grid(row=0, column=0, columnspan=2, padx=6, pady=2, sticky="ew")

        # 2. Cancel Button (Secondary destructive)
        self.cancel_btn = ctk.CTkButton(
            btn_grid,
            text="🛑 Cancel",
            height=44,
            corner_radius=10,
            fg_color="transparent",
            text_color=THEME_ACCENT_RED,
            hover_color=("#fee2e2", "#271c24"),
            border_color=THEME_ACCENT_RED,
            border_width=1.5,
            state="disabled",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self._cancel_download,
        )
        self.cancel_btn.grid(row=0, column=2, padx=6, pady=2, sticky="ew")

        # 3. Clean Outline actions (neutral buttons)
        neutral_frame = ctk.CTkFrame(btn_grid, fg_color="transparent")
        neutral_frame.grid(row=0, column=3, padx=6, pady=2, sticky="ew")
        neutral_frame.grid_columnconfigure((0, 1), weight=1)

        self.clear_btn = ctk.CTkButton(
            neutral_frame,
            text="🧹 Clear Logs",
            height=44,
            corner_radius=10,
            fg_color=THEME_BG,
            text_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_CARD_BORDER,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self._clear_logs,
        )
        self.clear_btn.grid(row=0, column=0, padx=3, sticky="ew")

        self.open_folder_btn = ctk.CTkButton(
            neutral_frame,
            text="📂 Open Folder",
            height=44,
            corner_radius=10,
            fg_color=THEME_BG,
            text_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_CARD_BORDER,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self._open_output_dir,
        )
        self.open_folder_btn.grid(row=0, column=1, padx=3, sticky="ew")

        # Thick progress bar
        progress_container = ctk.CTkFrame(card, fg_color="transparent")
        progress_container.grid(row=1, column=0, padx=20, pady=(6, 12), sticky="ew")
        progress_container.grid_columnconfigure(0, weight=1)
        progress_container.grid_columnconfigure(1, weight=0)

        self.progress = ctk.CTkProgressBar(
            progress_container,
            height=12,
            corner_radius=6,
            fg_color=THEME_BG,
            progress_color=THEME_ACCENT_INDIGO,
        )
        self.progress.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.progress.set(0)

        self.percent_stat_var = ctk.StringVar(value="0%")
        self.percent_label = ctk.CTkLabel(
            progress_container,
            textvariable=self.percent_stat_var,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=THEME_ACCENT_INDIGO,
        )
        self.percent_label.grid(row=0, column=1, sticky="e")

        # Status text row
        status_row = ctk.CTkFrame(card, fg_color="transparent")
        status_row.grid(row=2, column=0, padx=20, pady=(0, 16), sticky="ew")
        status_row.grid_columnconfigure(1, weight=1)

        self.status_dot = ctk.CTkLabel(
            status_row,
            text="●",
            font=ctk.CTkFont(size=16),
            text_color=THEME_ACCENT_GREEN,
        )
        self.status_dot.grid(row=0, column=0, padx=(0, 6))

        self.status_var = ctk.StringVar(value="Ready (Waiting)")
        self.status_label = ctk.CTkLabel(
            status_row,
            textvariable=self.status_var,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME_TEXT_SECONDARY,
        )
        self.status_label.grid(row=0, column=1, sticky="w")

    # ================= CARD 8: SYSTEM LOG ACCORDION =================
    def _build_logs_card(self, parent: ctk.CTkFrame) -> None:
        self.show_logs_var = ctk.BooleanVar(value=False)

        self.logs_header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.logs_header_frame.grid(row=8, column=0, padx=8, pady=4, sticky="w")

        self.logs_switch = ctk.CTkSwitch(
            self.logs_header_frame,
            text="Show Advanced System and Terminal Logs",
            variable=self.show_logs_var,
            progress_color=THEME_ACCENT_INDIGO,
            text_color=THEME_TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self._toggle_logs_section,
        )
        self.logs_switch.grid(row=0, column=0, sticky="w")

        # The collapsible log box
        self.logs_box_frame = ctk.CTkFrame(
            parent,
            fg_color=THEME_CARD_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            corner_radius=16,
        )
        self.logs_box_frame.grid(row=9, column=0, padx=4, pady=(2, 12), sticky="ew")
        self.logs_box_frame.grid_columnconfigure(0, weight=1)

        self.log_box = ctk.CTkTextbox(
            self.logs_box_frame,
            height=150,
            corner_radius=12,
            fg_color=THEME_BG,
            border_color=THEME_CARD_BORDER,
            border_width=1,
            text_color=THEME_TEXT_PRIMARY,
            font=ctk.CTkFont(family="Consolas", size=11),
        )
        self.log_box.grid(row=0, column=0, padx=16, pady=16, sticky="ew")
        self.log_box.insert("end", "System logging active.\n")

        self._toggle_logs_section()

    def _toggle_logs_section(self) -> None:
        if self.show_logs_var.get():
            self.logs_box_frame.grid()
        else:
            self.logs_box_frame.grid_remove()

    def _toggle_advanced_section(self) -> None:
        if self.show_advanced_var.get():
            self.advanced_frame.grid()
        else:
            self.advanced_frame.grid_remove()

    # ================= SMART FOCUS & CLIPBOARD =================
    def _check_clipboard(self) -> None:
        """Inspects clipboard when app gets focus, popping up auto-paste banner if link detected."""
        try:
            clipboard = self.clipboard_get().strip()
            is_valid_url = False
            if clipboard.startswith(("http://", "https://")):
                if any(domain in clipboard.lower() for domain in ["youtube.com", "youtu.be", "vimeo.com", "dailymotion.com", "instagram.com", "facebook.com", "twitter.com"]):
                    is_valid_url = True

            if is_valid_url:
                if clipboard != self.last_clipboard_value:
                    self.detected_url = clipboard
                    self.clipboard_badge.configure(text=f"{TRANSLATIONS[self.current_lang]['paste_btn']}: {clipboard[:30]}...")
                    self.clipboard_badge.grid()
            else:
                self.clipboard_badge.grid_remove()
        except Exception:
            pass
        self.after(1500, self._check_clipboard)

    def _paste_clipboard(self) -> None:
        if self.detected_url:
            if self.batch_mode_var.get():
                self.url_textbox.insert("end", f"\n{self.detected_url}")
            else:
                self.url_entry.delete(0, "end")
                self.url_entry.insert(0, self.detected_url)
                self._trigger_metadata_fetch()
            self.last_clipboard_value = self.detected_url
            self.clipboard_badge.grid_remove()
            self._update_status_indicator("●", THEME_ACCENT_GREEN, TRANSLATIONS[self.current_lang]["lbl_status_pasted"])

    # ================= LOGIC CONTROL STATES (MUTUAL EXCLUSION) =================
    def _on_mode_changed(self, _: str) -> None:
        self._refresh_mode_state()
        self._update_quality_hint()
        self._update_template_preview()

    def _on_video_profile_changed(self, _: str) -> None:
        self._refresh_mode_state()
        self._update_quality_hint()

    def _refresh_mode_state(self) -> None:
        """Enforces visual interlock dimming. Disables video-only drop-downs when Audio mode active, and vice versa."""
        mode = self.mode_var.get()
        profile = self.video_profile_var.get()
        is_custom = VIDEO_PRESET_HEIGHT.get(profile) == "CUSTOM"

        if mode == "Video":
            self.video_profile_menu.configure(state="normal")
            self.video_limit_menu.configure(state="normal" if is_custom else "disabled")
            self.video_container_menu.configure(state="normal")
            self.video_audio_codec_menu.configure(state="normal")
            self.video_audio_codec_lbl.configure(text_color=THEME_TEXT_PRIMARY)
            
            self.audio_format_menu.configure(state="disabled")
            self.audio_quality_menu.configure(state="disabled")
        else:
            self.video_profile_menu.configure(state="disabled")
            self.video_limit_menu.configure(state="disabled")
            self.video_container_menu.configure(state="disabled")
            self.video_audio_codec_menu.configure(state="disabled")
            self.video_audio_codec_lbl.configure(text_color=THEME_TEXT_SECONDARY)
            
            self.audio_format_menu.configure(state="normal")
            self.audio_quality_menu.configure(state="normal")

    def _effective_video_height(self, item_config: dict) -> str:
        selected = VIDEO_PRESET_HEIGHT.get(item_config["video_profile"], "1080")
        if selected == "CUSTOM":
            return item_config["video_limit"]
        return selected

    def _update_quality_hint(self) -> None:
        preset = self.selected_preset_var.get()
        lang = self.current_lang
        
        if preset == "best":
            hint = TRANSLATIONS[lang]["active_profile_best"]
        elif preset == "1080p":
            hint = TRANSLATIONS[lang]["active_profile_1080p"]
        elif preset == "720p":
            hint = TRANSLATIONS[lang]["active_profile_720p"]
        elif preset == "mp3":
            hint = TRANSLATIONS[lang]["active_profile_audio"].format(format=self.audio_format_var.get().upper(), quality=self.audio_quality_var.get())
        else:
            hint = TRANSLATIONS[lang]["active_profile_custom"]

        self.quality_hint_var.set(hint)

    # ================= GENERAL UTILS =================
    def _pick_output_dir(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.output_var.get() or str(Path.home()))
        if selected:
            self.output_var.set(selected)

    def _pick_cookies_file(self) -> None:
        selected = filedialog.askopenfilename(
            title="cookies.txt seç",
            filetypes=[("Text", "*.txt"), ("All files", "*.*")],
        )
        if selected:
            self.cookies_var.set(selected)

    def _open_output_dir(self) -> None:
        path = Path(self.output_var.get()).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        os.startfile(path)  # type: ignore[attr-defined]

    def _clear_logs(self) -> None:
        self.log_box.delete("1.0", "end")

    def _append_log(self, line: str) -> None:
        self.log_box.insert("end", line)
        self.log_box.see("end")

    def _update_status_indicator(self, dot: str, color: tuple[str, str], message: str) -> None:
        self.status_dot.configure(text=dot, text_color=color)
        self.status_var.set(message)

    def _ensure_dependencies(self) -> bool:
        try:
            import yt_dlp  # noqa: F401
        except Exception:
            messagebox.showerror(
                TRANSLATIONS[self.current_lang]["lbl_dialog_deps_title"],
                TRANSLATIONS[self.current_lang]["lbl_dialog_deps_desc"],
            )
            return False
        return True

    def _validate_optional_int(self, value: str, field_name: str, min_value: int = 1) -> bool:
        raw = value.strip()
        if not raw:
            return True
        if not raw.isdigit():
            messagebox.showwarning(
                TRANSLATIONS[self.current_lang]["lbl_dialog_err_title"], 
                TRANSLATIONS[self.current_lang]["lbl_dialog_err_digit"].format(field_name=field_name)
            )
            return False
        if int(raw) < min_value:
            messagebox.showwarning(
                TRANSLATIONS[self.current_lang]["lbl_dialog_err_title"], 
                TRANSLATIONS[self.current_lang]["lbl_dialog_err_min"].format(field_name=field_name, min_value=min_value)
            )
            return False
        return True

    def _validate_inputs(self) -> bool:
        if not self._ensure_dependencies():
            return False

        template = self.output_template_var.get().strip()
        if not template:
            messagebox.showwarning(TRANSLATIONS[self.current_lang]["lbl_dialog_err_title"], TRANSLATIONS[self.current_lang]["lbl_dialog_err_template"])
            return False

        checks = [
            (self.max_downloads_var.get(), "Max Downloads" if self.current_lang=="en" else "Maks İndirme", 1),
            (self.retries_var.get(), "Retry", 0),
            (self.concurrent_fragments_var.get(), "Concurrent fragments", 1),
        ]
        for value, name, minimum in checks:
            if not self._validate_optional_int(value, name, minimum):
                return False
        return True

    # ================= SEQUENTIAL QUEUE COMMAND BUILDER =================
    def _build_command(self, item: dict) -> list[str]:
        out_dir = str(Path(self.output_var.get()).expanduser())
        output_template = item["output_template"].strip() or DEFAULT_OUTPUT_TEMPLATE
        cmd: list[str] = [sys.executable, "-m", "yt_dlp", "--newline", "-P", out_dir, "-o", output_template]

        mode = item["mode"]
        if mode == "Video":
            quality = self._effective_video_height(item)
            audio_codec = item["video_audio_codec"].strip().upper()
            if audio_codec.startswith("AAC"):
                preferred_audio_selector = "ba[acodec^=mp4a]"
                secondary_audio_selector = "ba[ext=m4a]"
            else:
                preferred_audio_selector = "ba[acodec*=opus]"
                secondary_audio_selector = "ba[ext=webm]"
            if quality == "Best":
                video_selector = "bv*"
                fallback_selector = "b"
            else:
                video_selector = f"bv*[height<=?{quality}]"
                fallback_selector = f"b[height<=?{quality}]"

            selector = (
                f"{video_selector}+{preferred_audio_selector}/"
                f"{video_selector}+{secondary_audio_selector}/"
                f"{video_selector}+ba/"
                f"{fallback_selector}"
            )
            cmd.extend(["-f", selector, "--merge-output-format", item["video_container"]])
        else:
            audio_quality = AUDIO_PRESET_QUALITY.get(item["audio_quality"], "0")
            cmd.extend(["-x", "--audio-format", item["audio_format"], "--audio-quality", audio_quality])

        if not item["playlist"]:
            cmd.append("--no-playlist")
        if item["metadata"]:
            cmd.append("--add-metadata")
        if item["thumbnail_flag"]:
            cmd.extend(["--write-thumbnail", "--convert-thumbnails", "jpg"])
            if mode == "Audio":
                cmd.append("--embed-thumbnail")
        if item["subs"]:
            cmd.extend(["--write-subs", "--sub-langs", "all,-live_chat"])
        if item["auto_subs"]:
            cmd.append("--write-auto-subs")
        if item["restrict_names"]:
            cmd.append("--restrict-filenames")

        # SponsorBlock Remove
        if self.sponsorblock_var.get():
            cmd.extend(["--sponsorblock-remove", "all"])

        playlist_items = item["playlist_items"].strip()
        if playlist_items:
            cmd.extend(["--playlist-items", playlist_items.replace(" ", "")])

        max_downloads = item["max_downloads"].strip()
        if max_downloads:
            cmd.extend(["--max-downloads", max_downloads])

        rate_limit = item["rate_limit"].strip()
        if rate_limit:
            cmd.extend(["--limit-rate", rate_limit])

        if item["archive"]:
            archive_file = str(Path(out_dir) / ".downloaded_archive.txt")
            cmd.extend(["--download-archive", archive_file])

        retries = item["retries"].strip()
        if retries:
            cmd.extend(["--retries", retries])

        concurrent_fragments = item["concurrent_fragments"].strip()
        if concurrent_fragments:
            cmd.extend(["--concurrent-fragments", concurrent_fragments])

        cookies_file = item["cookies"].strip()
        if cookies_file:
            cmd.extend(["--cookies", cookies_file])
        else:
            browser_cookies = item["browser_cookies"].strip().lower()
            if browser_cookies and browser_cookies != "kapali":
                cmd.extend(["--cookies-from-browser", browser_cookies])

        extra_args = item["extra_args"].strip()
        if extra_args:
            cmd.extend(shlex.split(extra_args, posix=False))

        cmd.append(item["url"])
        return cmd

    def _format_cmd_for_log(self, cmd: list[str]) -> str:
        safe_parts = []
        for part in cmd:
            if " " in part or "\t" in part:
                safe_parts.append(f'"{part}"')
            else:
                safe_parts.append(part)
        return " ".join(safe_parts)

    # ================= START DOWNLOAD SEQUENTIAL EXECUTION =================
    def _start_download(self) -> None:
        if self.is_queue_running:
            messagebox.showinfo(TRANSLATIONS[self.current_lang]["lbl_dialog_info_title"], TRANSLATIONS[self.current_lang]["lbl_dialog_info_running"])
            return

        if not self._validate_inputs():
            return

        # Auto add URL inputs to queue if queue is empty
        if not self.queue_list:
            url = ""
            if self.batch_mode_var.get():
                url = self.url_textbox.get("1.0", "end-1c").strip()
            else:
                url = self.url_entry.get().strip()
            
            if url:
                self._add_to_queue()
            else:
                messagebox.showwarning(TRANSLATIONS[self.current_lang]["lbl_dialog_warning_title"], TRANSLATIONS[self.current_lang]["lbl_queue_item_placeholder"])
                return

        self.cancel_event.clear()
        self.is_queue_running = True
        self.current_queue_idx = 0
        self.start_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")

        # Start Queue execution thread
        self.worker_thread = threading.Thread(target=self._run_queue_executor, daemon=True)
        self.worker_thread.start()

    def _cancel_download(self) -> None:
        self.cancel_event.set()
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self._update_status_indicator("●", THEME_ACCENT_RED, TRANSLATIONS[self.current_lang]["lbl_status_cancelled"])

    def _run_queue_executor(self) -> None:
        """Processes each item in the download queue sequentially one by one in a background worker thread."""
        lang = self.current_lang
        while self.current_queue_idx < len(self.queue_list) and not self.cancel_event.is_set():
            idx = self.current_queue_idx
            item = self.queue_list[idx]

            active_downloading_str = "İndiriliyor" if lang=="tr" else ("Descargando" if lang=="es" else "Downloading")
            item["status"] = active_downloading_str
            self.ui_queue.put(("queue_sync", None))

            # Build command and setup stats
            cmd = self._build_command(item)
            self.ui_queue.put(("active_file", TRANSLATIONS[self.current_lang]["lbl_status_active_dl"].format(title=item['title'])))
            self.ui_queue.put(("log", f"\n[queue] Download Started [{idx+1}/{len(self.queue_list)}]: {item['title']}\n"))
            self.ui_queue.put(("log", f"$ {self._format_cmd_for_log(cmd)}\n"))
            self.ui_queue.put(("status", ("●", THEME_ACCENT_BLUE, TRANSLATIONS[self.current_lang]["lbl_status_processing"].format(curr=idx+1, total=len(self.queue_list)))))

            try:
                # Run the subprocess downloader
                code, saw_http_403, saw_outdated = self._run_command_stream(cmd, idx)

                if self.cancel_event.is_set():
                    item["status"] = "İptal Edildi" if lang=="tr" else ("Cancelado" if lang=="es" else "Cancelled")
                    self.ui_queue.put(("toast_cancel", item["title"]))
                    break

                if code == 0:
                    item["status"] = "Tamamlandı" if lang=="tr" else ("Completado" if lang=="es" else "Completed")
                    self.ui_queue.put(("percent_complete", 1.0))
                    self.ui_queue.put(("toast_success", item["title"]))
                else:
                    # Check for 403 automatic fallback
                    should_retry = (
                        saw_http_403
                        and item["youtube_403"]
                        and YOUTUBE_FALLBACK_EXTRACTOR_ARGS not in " ".join(cmd)
                    )
                    if should_retry:
                        self.ui_queue.put(("log", "[warning] YouTube 403 Forbidden detected, trying TV Client fallback...\n"))
                        retry_cmd = self._append_options_before_urls(cmd, [item["url"]], ["--extractor-args", YOUTUBE_FALLBACK_EXTRACTOR_ARGS])
                        code, saw_http_403, saw_outdated = self._run_command_stream(retry_cmd, idx)
                        
                        if code == 0:
                            item["status"] = "Tamamlandı" if lang=="tr" else ("Completado" if lang=="es" else "Completed")
                            self.ui_queue.put(("percent_complete", 1.0))
                            self.ui_queue.put(("toast_success", item["title"]))
                        else:
                            item["status"] = "Hata" if lang=="tr" else ("Error" if lang=="es" else "Error")
                            self.ui_queue.put(("toast_error", {"code": code, "title": item["title"]}))
                    else:
                        item["status"] = "Hata" if lang=="tr" else ("Error" if lang=="es" else "Error")
                        self.ui_queue.put(("toast_error", {"code": code, "title": item["title"]}))

            except Exception as e:
                item["status"] = "Hata" if lang=="tr" else ("Error" if lang=="es" else "Error")
                self.ui_queue.put(("log", f"[error] {e}\n"))

            self.ui_queue.put(("queue_sync", None))
            self.current_queue_idx += 1

        self.is_queue_running = False
        self.ui_queue.put(("queue_done", None))

    def _run_command_stream(self, cmd: list[str], item_idx: int) -> tuple[int, bool, bool]:
        progress_re = re.compile(
            r"\[download\]\s+(\d{1,3}(?:\.\d+)?)%\s+of\s+(~?\d+(?:\.\d+)?\w+)\s+at\s+(\d+(?:\.\d+)?\w+/s|Unknown speed)\s+ETA\s+(\d{2}:\d{2}|\w+)"
        )
        dest_re = re.compile(r"\[download\]\s+Destination:\s+(.+)")

        saw_http_403 = False
        saw_outdated_warning = False

        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            startupinfo=startupinfo,
        )
        assert self.process.stdout is not None

        for line in self.process.stdout:
            self.ui_queue.put(("log", line))

            match = progress_re.search(line)
            if match:
                value = max(0.0, min(100.0, float(match.group(1))))
                size_str = match.group(2)
                speed_str = match.group(3)
                eta_str = match.group(4)

                stats_payload = {
                    "percent": value,
                    "size": size_str,
                    "speed": speed_str,
                    "eta": eta_str,
                }
                self.ui_queue.put(("stats", stats_payload))

            dest_match = dest_re.search(line)
            if dest_match:
                full_path = dest_match.group(1).strip()
                filename = Path(full_path).name
                self.ui_queue.put(("active_file", TRANSLATIONS[self.current_lang]["lbl_status_active_dl"].format(title=filename)))

            if "HTTP Error 403: Forbidden" in line:
                saw_http_403 = True
            if "version" in line and "older than 90 days" in line:
                saw_outdated_warning = True

        return self.process.wait(), saw_http_403, saw_outdated_warning

    def _append_options_before_urls(self, cmd: list[str], urls: list[str], options: list[str]) -> list[str]:
        if not urls:
            return cmd + options
        option_area = cmd[:-len(urls)]
        url_area = cmd[-len(urls):]
        return option_area + options + url_area

    # ================= ASYNC UI METRIC DRAINING =================
    def _drain_ui_queue(self) -> None:
        while True:
            try:
                kind, payload = self.ui_queue.get_nowait()
            except queue.Empty:
                break

            if kind == "log":
                self._append_log(str(payload))
            elif kind == "stats":
                stats = payload  # type: ignore[assignment]
                percent_val = float(stats["percent"])
                self.progress.set(percent_val / 100.0)
                self.percent_stat_var.set(f"{int(percent_val)}%")
                self.speed_stat_var.set(str(stats["speed"]))
                self.eta_stat_var.set(str(stats["eta"]))
                self.size_stat_var.set(str(stats["size"]))
            elif kind == "active_file":
                self.active_file_var.set(str(payload))
            elif kind == "percent_complete":
                self.progress.set(float(payload))
                self.percent_stat_var.set("100%")
            elif kind == "status":
                dot, color, message = payload  # type: ignore[value-type]
                self._update_status_indicator(dot, color, message)
            elif kind == "queue_sync":
                self._update_queue_ui()
            elif kind == "metadata_ready":
                meta = payload  # type: ignore[assignment]
                self.preview_loading_lbl.grid_remove()
                self.thumb_label.grid()
                
                if meta["thumbnail_img"]:
                    self.thumb_label.configure(image=meta["thumbnail_img"], text="")
                else:
                    self.thumb_label.configure(image="", text="No Image")

                self.preview_title_lbl.configure(text=meta["title"])
                self.preview_author_lbl.configure(text=meta["uploader"])
                self.preview_dur_lbl.configure(text=f"Duration: {meta['duration']}")
            elif kind == "metadata_error":
                self.preview_loading_lbl.configure(text=TRANSLATIONS[self.current_lang]["lbl_preview_err"])
            elif kind == "toast_update":
                self._show_toast(TRANSLATIONS[self.current_lang]["lbl_toast_update_title"], TRANSLATIONS[self.current_lang]["lbl_toast_update_desc"])
            elif kind == "toast_success":
                self._show_toast(TRANSLATIONS[self.current_lang]["lbl_toast_success_title"], TRANSLATIONS[self.current_lang]["lbl_toast_success_desc"].format(title=payload))
            elif kind == "toast_cancel":
                self._show_toast(TRANSLATIONS[self.current_lang]["lbl_dialog_close_title"], f"Download queue cancelled for '{payload}'")
            elif kind == "toast_error":
                err_data = payload  # type: ignore[assignment]
                self._show_toast(TRANSLATIONS[self.current_lang]["lbl_toast_err_title"], TRANSLATIONS[self.current_lang]["lbl_toast_err_desc"].format(code=err_data["code"], title=err_data["title"]))
            elif kind == "update_done":
                self.update_btn.configure(state="normal", text=TRANSLATIONS[self.current_lang]["btn_update"])
            elif kind == "queue_done":
                self.start_btn.configure(state="normal")
                self.cancel_btn.configure(state="disabled")
                self.process = None
                self.current_queue_idx = -1
                self.active_file_var.set(TRANSLATIONS[self.current_lang]["lbl_active_dl"])
                
                if self.cancel_event.is_set():
                    self._update_status_indicator("●", THEME_ACCENT_RED, TRANSLATIONS[self.current_lang]["lbl_status_cancelled"])
                else:
                    self._update_status_indicator("●", THEME_ACCENT_GREEN, TRANSLATIONS[self.current_lang]["lbl_status_completed"])
                    self._show_toast(TRANSLATIONS[self.current_lang]["lbl_toast_all_title"], TRANSLATIONS[self.current_lang]["lbl_toast_all_desc"])

        self.after(100, self._drain_ui_queue)

    def _on_close(self) -> None:
        if self.process and self.process.poll() is None:
            if not messagebox.askyesno(TRANSLATIONS[self.current_lang]["lbl_dialog_close_title"], TRANSLATIONS[self.current_lang]["lbl_dialog_close_desc"]):
                return
            self._cancel_download()
        
        try:
            shutil.rmtree(self.scratch_dir, ignore_errors=True)
        except Exception:
            pass

        self.destroy()


def main() -> None:
    app = YtDlpGuiApp()
    app.mainloop()


if __name__ == "__main__":
    main()
