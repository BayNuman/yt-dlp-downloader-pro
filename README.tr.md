# yt-dlp Downloader Pro

<p align="center">
  <a href="README.md">🇺🇸 English</a> &nbsp;·&nbsp;
  <b>🇹🇷 Türkçe</b> &nbsp;·&nbsp;
  <a href="README.es.md">🇪🇸 Español</a>
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-0078d4?logo=windows)](https://github.com/BayNuman/yt-dlp-downloader-pro/releases)
[![Platform: Android](https://img.shields.io/badge/Platform-Android%208%2B-3ddc84?logo=android)](https://github.com/BayNuman/yt-dlp-downloader-pro/releases)
[![Android CI](https://github.com/BayNuman/yt-dlp-downloader-pro/actions/workflows/android-ci.yml/badge.svg)](https://github.com/BayNuman/yt-dlp-downloader-pro/actions/workflows/android-ci.yml)
[![Stars](https://img.shields.io/github/stars/BayNuman/yt-dlp-downloader-pro?style=social)](https://github.com/BayNuman/yt-dlp-downloader-pro/stargazers)

> Yarı saydam cam derinliği (glassmorphic) arayüzüne sahip, Windows ve Android için geliştirilmiş premium, yüksek performanslı bir video ve ses indirme aracı. Çift tutamaçlı zaman aralığı kırpma, SponsorBlock entegrasyonu, paralel indirme kuyruğu, akıllı klasör yapıları ve Instagram Reels / YouTube Shorts için 9:16 dikey otomatik kırpma motoru sunar. Gücünü `yt-dlp` ve `FFmpeg`'den alır.

<div align="center">
  <img src="assets/screenshots/preview.gif" alt="yt-dlp Downloader Pro Önizleme" width="680"/>
</div>

---

## 📥 Hızlı İndirme Linkleri

| Platform | Tür | Yayın Paketi |
| :--- | :--- | :--- |
| **🖥️ Windows** | Kurulumcu (Önerilen) | [📥 Setup.exe İndir](https://github.com/BayNuman/yt-dlp-downloader-pro/releases/latest/download/yt-dlp_Downloader_Pro_Setup.exe) |
| **🖥️ Windows** | Taşınabilir (Kurulumsuz) | [📥 Portable.exe İndir](https://github.com/BayNuman/yt-dlp-downloader-pro/releases/latest/download/yt-dlp.Downloader.Pro.exe) |
| **📱 Android** | APK (Android 8.0+) | [📥 Uygulama APK İndir](https://github.com/BayNuman/yt-dlp-downloader-pro/releases/latest/download/app-release.apk) |

---

## 🚀 Öne Çıkan Özellikler

| Özellik | Diğer Arayüzler | yt-dlp Downloader Pro |
| :--- | :--- | :--- |
| **Zaman Aralığı Kırpma** | ❌ (Sadece tam video indirilir) | ✅ Çift tutamaçlı etkileşimli zaman slider'ı |
| **Akıllı Çoklu Kırpma** | ❌ | ✅ LeetCode 56 Greedy Interval Merging |
| **Reels/Shorts Çıktısı** | ❌ | ✅ 9:16 dikey dairesel odaklı otomatik dikey kırpma |
| **SponsorBlock** | ❌ | ✅ Sponsor bölümlerini otomatik atlama ve kesme |
| **403 Hata Bypass** | ❌ | ✅ TV istemcisi otomatik yedek imza mekanizması |
| **Ses Dalga Formu (Waveform)** | ❌ | ✅ 1.5 saniyede düşük gecikmeli envelope görsel önizlemesi |
| **Paralel Kuyruk** | ❌ çoğunda | ✅ Yüksek performanslı ve thread-safe kuyruk yönetimi |

---

## 📦 Kurulum ve Çalıştırma

### Hazır Derlenmiş Sürümler

#### 🖥️ Windows Kurulumu
1. [yt-dlp_Downloader_Pro_Setup.exe](https://github.com/BayNuman/yt-dlp-downloader-pro/releases/latest/download/yt-dlp_Downloader_Pro_Setup.exe) dosyasını indirin.
2. Kurulum programını çift tıklayıp yönergeleri takip edin (~30 saniye sürer).
3. *SmartScreen Uyarısı:* Windows SmartScreen uyarısı alırsanız **Ek Bilgi** → **Yine de Çalıştır** seçeneğine tıklayın.

#### 📱 Android Kurulumu
1. [app-release.apk](https://github.com/BayNuman/yt-dlp-downloader-pro/releases/latest/download/app-release.apk) dosyasını telefonunuza indirin.
2. Android güvenlik ayarlarınızda **Bilinmeyen Kaynaklardan Yükleme** iznini etkinleştirin.
3. İndirilen APK dosyasını açıp **Yükle** butonuna dokunun.

---

## 🛠️ Kaynak Koddan Derleme

### Masaüstü Gereksinimleri
- **Python** (v3.10 veya üzeri)
- **FFmpeg** ve **FFprobe** (Eksikse derleyici script tarafından otomatik olarak indirilir)
- **Inno Setup 6** (Yalnızca Windows Setup Installer paketlemek istiyorsanız gereklidir)

### Masaüstü Komutları (Çalıştırma & Paketleme)
1. **Depoyu klonlayın:**
   ```bash
   git clone https://github.com/BayNuman/yt-dlp-downloader-pro.git
   cd yt-dlp-downloader-pro
   ```
2. **Python bağımlılıklarını yükleyin:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Uygulamayı başlatın:**
   ```bash
   python app.py
   ```
4. **Tek başına çalışan (.EXE) ve Windows Kurulumcuyu derleyin:**
   ```bash
   python build_full_distribution.py
   ```

### Android Gereksinimleri & Derleme
- **Android Studio** Hedgehog (2023.1.1) veya üzeri
- **JDK 17**
- **Android SDK API 26+**

```bash
cd android
./gradlew assembleRelease
```
*Derlenen APK çıktısı şu dizinde oluşur: `android/app/build/outputs/apk/release/app-release.apk`*

---

## 🛠️ Kullanım Örnekleri

### Görsel Arayüz (GUI) Modu
Uygulamayı çalıştırın veya kısayoluna çift tıklayın. Adresi yapıştırın, format profilinizi seçin (örneğin *En İyi Kalite*, *Full HD 1080p*, *Instagram Reels*), gerekirse zaman aralığı sınırlarını belirleyin ve **İndirmeleri Başlat** butonuna basın.

### Başsız CLI Modu (Windows Derlenmiş Dosya)
Tek başına çalışan derlenmiş EXE, argümanları yakalayan özel bir CLI önyükleyici içerir. `-m yt_dlp` bayrağı ile çalıştırıldığında arka planda doğrudan terminal aracı gibi çalışır:
```bash
"yt-dlp Downloader Pro.exe" -m yt_dlp "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --format bestvideo+bestaudio
```

### Programatik Kod Çağrısı (Python)
Geliştiriciler `core/` dizinindeki modülleri doğrudan projelerine dahil edebilirler. Örneğin, programatik olarak raw yt-dlp argümanları üretmek için:
```python
from core.command_builder import build_ytdlp_args
from core.app_state import DownloadTask

# İndirme görevinin durum temsilini oluşturun
task = DownloadTask(
    url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    preset="1080p",
    output_dir="downloads"
)

# Saf yt-dlp CLI argümanlarını üretin
args = build_ytdlp_args(task)
print("yt-dlp argümanları:", args)
```

---

## 📸 Ekran Görüntüleri

<table>
<tr>
<td><img src="assets/screenshots/desktop_dark_main.png" alt="Windows — Koyu Tema" width="340"/></td>
<td><img src="assets/screenshots/desktop_light_main.png" alt="Windows — Açık Tema" width="340"/></td>
</tr>
<tr>
<td align="center"><em>Windows — Koyu Tema</em></td>
<td align="center"><em>Windows — Açık Tema</em></td>
</tr>
</table>

<table>
<tr>
<td><img src="assets/screenshots/android_dark.jpg" alt="Android — İndir" width="160"/></td>
<td><img src="assets/screenshots/android_queue.png" alt="Android — Kuyruk" width="160"/></td>
<td><img src="assets/screenshots/android_history.png" alt="Android — Geçmiş" width="160"/></td>
<td><img src="assets/screenshots/android_settings.png" alt="Android — Ayarlar" width="160"/></td>
</tr>
<tr>
<td align="center"><em>İndirme Ekranı</em></td>
<td align="center"><em>İndirme Kuyruğu</em></td>
<td align="center"><em>Geçmiş</em></td>
<td align="center"><em>Ayarlar</em></td>
</tr>
</table>

---

## 🏗️ Proje Mimarisi

```text
yt-dlp-downloader-pro/
│
├── 🖥️  Masaüstü (Python + CustomTkinter)
│   ├── app.py                    # Giriş noktası (Bootstrap) - sadece main() çağırır
│   ├── core/
│   │   ├── app_state.py          # RLock ile korunan thread-safe durum motoru + dil algılama
│   │   ├── command_builder.py    # Saf fonksiyonlar - yt-dlp CLI argümanlarını üretir
│   │   ├── downloader.py         # ThreadPoolExecutor eşzamanlı kuyruk yürütücüsü
│   │   ├── clip.py               # LeetCode 56 Greedy Interval Merging + seek yöneticisi
│   │   ├── merger.py             # FFmpeg Concat Demuxer kayıpsız birleştirme motoru
│   │   ├── profiles.py           # Polimorfik ffmpeg çıktı dönüştürme profilleri
│   │   ├── suggester.py          # Helezonik analiz tabanlı öneri motoru
│   │   ├── history.py            # SQLite + thread-local bağlantı önbelleği + WAL modu
│   │   ├── presets.py            # Bellek önbellekli JSON şablonları katmanı
│   │   ├── updater.py            # PyPI paket güncelleme denetleyicisi
│   │   └── env.py                # Canlı Windows kayıt defteri (Registry) yenileyici
│   └── ui/
│       ├── theme.py              # HSL renk paletleri + i18n çevirileri (en/tr/es)
│       ├── main_window.py        # Coalesced UI kuyruk drenajlı ana arayüz tasarımı
│       ├── components/toast.py   # BaseToast nesne yönelimli bildirim mimarisi
│       └── panels/               # Modüler paneller (Kuyruk, Gelişmiş, Önizleme)
│
└── 📱  Android (Kotlin + Jetpack Compose)
    └── android/app/src/main/
        ├── MainActivity.kt
        ├── service/DownloadService.kt  # Yaşam döngüsü bağlamalı ön plan servis
        ├── data/
        │   ├── DownloadModels.kt       # İstek/Olay/Kayıt modelleri + JSON serileştirme
        │   ├── YtDlpCommandBuilder.kt  # Kırpma aralığı optimizasyonlu komut oluşturucu
        │   ├── YtDlpRunner.kt          # Regex tabanlı çıktı ayrıştırıcı + çoklu yol alternatifi
        │   └── algorithms/ClipOptimizer.kt  # LeetCode 56 aralık birleştirme algoritması
        └── ui/
            ├── DownloaderScreen.kt
            ├── DownloaderViewModel.kt   # Birleştirilmiş RuntimeState mimarisi
            └── theme/Translations.kt
```

---

## 🌍 Desteklenen Platformlar

Gücünü `yt-dlp`'den alan bu uygulama **1000'den fazla** web sitesini destekler:

YouTube • YouTube Music • Vimeo • SoundCloud • Twitter/X • Instagram • TikTok • Facebook • Dailymotion • Twitch • Reddit • Bandcamp • ve daha fazlası...

→ [Desteklenen sitelerin tam listesi](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)

---

## 🗺️ Yol Haritası

- [ ] macOS masaüstü desteği
- [ ] Android zaman aralığı kırpma paneli (slider + dönüştürme profilleri)
- [ ] Tarayıcı eklentisi (tek tıkla entegrasyon)
- [ ] Zamanlanmış indirmeler (belirli bir saate kurma sayacı)
- [ ] Plex / Jellyfin medya kütüphanesi otomatik etiketleme entegrasyonu
- [ ] Küçük resim kare şerit (filmstrip) slider'ı

---

## 🤝 Katkıda Bulunma

Katkılarınızı bekliyoruz!
1. [Katkı Kılavuzumuzu](CONTRIBUTING.md) inceleyin.
2. Depoyu forklayın, yeni bir özellik dalı açın ve Pull Request gönderin.

---

## ⚖️ Yasal Uyarı

Bu yazılım [yt-dlp](https://github.com/yt-dlp/yt-dlp) için geliştirilmiş bir GUI arayüz istemcisidir. Kullanıcılar, indirme yaptıkları platformların hizmet şartlarına uymaktan tamamen kendileri sorumludur.

---

## 📄 Lisans

MIT Lisansı ile dağıtılmaktadır. Detaylar için [LICENSE](LICENSE) dosyasına göz atabilirsiniz.

---

## 💡 Yapılması ve Kaçınılması Gerekenler (Dos & Don'ts)

| Yapılması Gerekenler | Kaçınılması Gerekenler |
| :--- | :--- |
| **Göreceli yollar kullanın** (repo içi `./assets/...` gibi) resimler ve kısayollar için. | **Mutlak yollar kullanmaktan kaçının** (`C:/Users/isim/...` gibi yollar diğer geliştiricilerde çalışmaz). |
| **Kod bloklarında dili tam belirtin** (örneğin ` ```bash `, ` ```python `) böylece kod renklendirmesi düzgün çalışır. | **Dili belirtilmemiş** veya boş bırakılmış ` ``` ` blokları kullanmayın. |
| **Tablolar ve emojiler kullanın** metinleri bölmek ve bilişsel yükü en aza indirmek için. | **Düz yazılardan oluşan devasa metin blokları yazmayın**; bu okuma yorgunluğu yaratır. |
| **Kurulum talimatlarını güncel tutun** ve yayınlamadan önce komutları yerel terminalde test edin. | **Eski veya eksik bağımlılık talimatları bırakmayın**, bu durum Geliştirici Deneyimini (DX) olumsuz etkiler. |

---

<div align="center">

[BayNuman](https://github.com/BayNuman) tarafından ❤️ ile yapılmıştır

[**🧡 Patreon'da Destek Olun**](https://patreon.com/BayNuman?utm_medium=unknown&utm_source=join_link&utm_campaign=creatorshare_creator&utm_content=copyLink)

Bu projeyi yararlı bulduysanız, diğer geliştiricilerin de keşfetmesi için bir ⭐ vermeyi unutmayın!

</div>
