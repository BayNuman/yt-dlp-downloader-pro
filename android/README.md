# Android Uygulamasi

Bu klasor, `yt-dlp` tabanli downloader projesinin Android (Kotlin + Jetpack Compose) surumunu icerir.

## Dosya Yapisi

- `app/src/main/java/com/baynuman/ytdownloader/ui`: Compose ekranlari + ViewModel
- `app/src/main/java/com/baynuman/ytdownloader/data`: yt-dlp komut builder + process runner
- `app/build.gradle.kts`: Android modul bagimliliklari

## Calistirma

1. Android Studio ile `android/` klasorunu ac.
2. Gradle sync bittikten sonra `app` modulunu build et.
3. Emulator veya cihazda calistir.

## Notlar

- Uygulama `io.github.junkfood02:youtubedl-android` runtime'i ile acilista yt-dlp altyapisini otomatik hazirlar.
- Runtime hazir olduktan sonra periyodik olarak otomatik yt-dlp guncelleme kontrolu yapar (basarisiz olursa uygulama yine calisir).
- Normal kullanimda kullanicidan `yt-dlp` binary secmesi beklenmez.
- Cookies dosyasi da dosya secici ile uygulama icine kopyalanir (`files/cookies/cookies.txt`).
- `Medya Izni Ver` butonu Android surumune gore gerekli media izinlerini ister.
- Output klasoru varsayilan olarak uygulamanin dis dosya alaninda `yt-downloads` dizinidir.

## Emulator Smoke Test

Hizli regresyon akisi icin:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\emulator_smoke.ps1
```

Raporlari farkli klasore yazmak icin:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\emulator_smoke.ps1 -ReportDir ".\reports\smoke"
```

Bu script su senaryolari sirayla calistirir:

- URL valid tek video
- Playlist
- Permission (izin revoke + tekrar verme)
- 403 uyumluluk modu

Not: Otomatik dogrulama icin logcat'teki `YTDownloaderTelemetry` ve `YTDownloaderRunner` JSON eventlerini kullanir.

Detayli checklist:

- `docs/emulator-smoke-checklist.md`

## Gradle Wrapper

- `gradlew`, `gradlew.bat` ve `gradle/wrapper/gradle-wrapper.properties` eklendi.
- `gradle-wrapper.jar` yerelde olusturulmalidir (`cd android && gradle wrapper`).
- Otomatik deneme icin:
  - `powershell -ExecutionPolicy Bypass -File android/scripts/bootstrap_wrapper.ps1`
