# Emulator Smoke Checklist

Bu dokuman, tek ekranli Android istemci icin hizli regresyon kontrolunu standartlastirir.

## Kapsam

- S1: URL valid tek video indirme
- S2: Playlist indirme
- S3: Depolama izin akisi
- S4: 403 uyumluluk modu (fallback) davranisi

## Hedef

- Baslat CTA her durumda erisilebilir olmali.
- Indirme tamamlandiginda dosya cihaza yazilmis olmali.
- Izin/hata durumlari teknik olmayan metinle gorunmeli.
- Uygulama hata alinca kapanmamali.

## Hizli Calistirma

`android/` klasorunde:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\emulator_smoke.ps1
```

Opsiyonlar:

```powershell
# Belirli emulator
powershell -ExecutionPolicy Bypass -File .\scripts\emulator_smoke.ps1 -DeviceId emulator-5554

# Build/kurulum adimini atla (APK zaten yukluyse)
powershell -ExecutionPolicy Bypass -File .\scripts\emulator_smoke.ps1 -SkipBuild -SkipInstall

# Rapor ciktilarini ozel klasore yaz
powershell -ExecutionPolicy Bypass -File .\scripts\emulator_smoke.ps1 -ReportDir ".\reports\smoke"
```

## Beklenen Sonuc

Script sonunda tablo verir:

- `PASS`: kontrol otomatik dogrulandi.
- `CHECK`: manuel dogrulama gerekli.

Ek olarak rapor dosyalari olusur:

- `smoke-<timestamp>.json`
- `smoke-<timestamp>.csv`

Script otomatik dogrulama icin logcat'te su tag'leri de kullanir:

- `YTDownloaderTelemetry`
- `YTDownloaderRunner`

Bu tag'lerdeki log satirlari JSON formatindadir:

```json
{"event":"download_completed","source":"ui","ts":1739960000000}
```

Ornek eventler:

- `url_valid_video`, `url_valid_playlist`
- `permission_granted`
- `download_completed`, `download_process_success`
- `event_403_fallback_triggered`

`CHECK` durumunda:

1. Uygulama icindeki `Canli Log` panelini kontrol et.
2. Emulator dosya klasorunu kontrol et:
   - `/storage/emulated/0/Android/data/com.salih.ytdownloader/files/Download/yt-downloads`
3. Gerekirse logcat filtrele:
   - `adb logcat -d | Select-String -Pattern "YTDownloaderTelemetry|YTDownloaderRunner|403|permission|yt-dlp|Forbidden"`
