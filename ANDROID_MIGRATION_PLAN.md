# Android Geçiş Kılavuzu: Masaüstü Devrimini Mobil Aplikasyona Taşıma
## 📱 Sprint 8 & 9 Mobil Entegrasyon ve Yol Haritası

Bu belge, **Sprint 8 (Multi-Clip Motoru)** ve **Sprint 9 (Akıllı Format Önerileri, Kayıpsız Demux Birleştirici, JS Çözücü)** kapsamında masaüstü uygulamamızda gerçekleştirdiğimiz devrim niteliğindeki mühendislik çözümlerini ve bu çözümleri **Android (Kotlin + Jetpack Compose)** uygulamamıza nasıl entegre edebileceğimizi adım adım açıklar.

---

## 🖥️ 1. Masaüstünde Neler Yaptık? (Android'de Olmayanlar)

Masaüstü uygulamamızda sıradan bir "video indirici" olmanın ötesine geçerek kurumsal seviyede bir **medya iş istasyonu** inşa ettik:

1. **Single-Fetch, Multiple-Extract (SFME) Kırpma Motoru:** 
   * Kullanıcının seçtiği çoklu aralıkları (Örn: 0-10sn, 8-20sn, 45-60sn) **LeetCode 56 (Aralık Birleştirme)** algoritmasıyla optimize edip tek bir **MacroClip** haline getirdik.
   * YouTube'dan tek seferde indirme yapıp, yerelde `ffmpeg -c copy` kullanarak SSD hızında ve sıfır kalite kaybıyla böldük (Böylece YouTube'un ardışık isteklerde attığı **HTTP 429 Too Many Requests** banını tamamen engelledik).
2. **Kayıpsız Concat Demuxer Birleştirici:**
   * Çoklu kesilen klipleri, telefonda/bilgisayarda yeniden kodlama yapmadan saniyeler içinde tek bir özet dosyada birleştiren FFmpeg Concat altyapısını kurduk.
3. **Akıllı Format Öneri Motoru (SmartFormatSuggester):**
   * Video en boy oranını (aspect ratio), başlığını ve süresini analiz ederek dikey Shorts tespiti (ve dikey 9:16 kırpma önerisi) veya müzik videoları için hafif ses (M4A Mono) önerisi yapan akıllı karar mekanizması yazdık.
4. **Çalışma Anı JS Runtime (Deno) Kurulum ve PATH Enjeksiyonu:**
   * YouTube'un hız sınırlamasını (n-challenge) çözmek için Deno çalışma ortamını otomatik kurup, bilgisayarı yeniden başlatmaya gerek kalmadan PATH yollarını Python içerisinden anında tazeledik (`core/env.py`).

---

## 📱 2. Bunları Android'e Nasıl Entegre Edebiliriz? (Geçiş Planı)

Android uygulamamız şu anda geleneksel yöntemlerle tek bir kırpma alanı sunuyor ve ardışık indirmelerde YouTube engeline takılma riski barındırıyor. İşte bu özellikleri Android'e taşıma planı:

### 🏁 Adım 1: Android'de JavaScript Runtimes (n-Challenge Çözümü)
Android cihazlarda `yt-dlp` çalışırken imza şifresini çözebilmek ve hız sınırına takılmamak için telefonda da bir JS çalışma ortamı bulunmalıdır.
* **Mühendislik Çözümü:** Android uygulamasının Gradle bağımlılıklarına **QuickJS** (`com.github.quickjs-android`) veya hafif bir V8 engine entegre edilmelidir.
* **Entegrasyon:** `yt-dlp`'nin mobil ortamda QuickJS'i tanıması için termux veya python-for-android ortamında `--js-runtimes "quickjs"` parametresi aktif edilmeli, `yt-dlp-ejs` kütüphanesi Android Python paketi içerisine derleme aşamasında eklenmelidir.

### 🎨 Adım 2: Jetpack Compose ile Çoklu Klip Arayüzü
Masaüstündeki scrollable `ClipRow` yapısı Jetpack Compose'a taşınmalıdır.
* **Arayüz Tasarımı:** `DownloaderScreen.kt` içerisine bir `LazyColumn` eklenerek dinamik olarak arttırılabilen klip kartları (`ClipCard`) oluşturulmalıdır.
* **Çift Düğümlü Slider:** Material 3'ün `RangeSlider` bileşeni kullanılarak, başlangıç ve bitiş düğümlerinin kullanıcı tarafından pürüzsüzce kaydırılması sağlanmalıdır.
* **Bölümler (Chapters) Entegrasyonu:** Çekilen video detaylarındaki bölümler yatay bir `LazyRow` olarak listelenmeli; kullanıcı bir bölüme tıkladığında `LazyColumn`'a o bölümün süreleriyle yeni bir `ClipCard` otomatik olarak eklenmelidir.

### ⚙️ Adım 3: SFME Kırpma Motorunun Python/Kotlin Portu
Aralık birleştirme algoritması mobil tarafa taşınmalıdır.
* **Algoritma Portu:** `core/clip.py` içindeki aralık birleştirme kodu Kotlin tarafında (`DownloaderViewModel.kt`) yazılmalıdır.
* **Mobil FFmpeg Entegrasyonu:** Gradle'a **`com.arthenica:ffmpeg-kit-full`** bağımlılığı eklenmelidir. İndirme bittiğinde Kotlin tarafında FFmpeg-Kit çağrılarak MacroClip dosyası yerelde saniyeler içinde bölünmelidir.
  ```kotlin
  // Örnek Lossless Trim Komutu
  FFmpegKit.execute("-ss 00:01:20 -to 00:01:50 -i input.mp4 -c copy output.mp4")
  ```

### 🔗 Adım 4: Mobilde Kayıpsız Birleştirme (Concat)
* **Demux List Oluşturma:** Kullanıcının böldüğü tüm kliplerin yolları, uygulamanın `context.cacheDir` klasörü altında geçici bir `files.txt` dosyasına yazılmalıdır.
* **Kayıpsız Birleştirme:** FFmpeg-Kit üzerinden `-f concat -safe 0 -i files.txt -c copy final_summary.mp4` komutu çalıştırılarak telefon hafızasında saniyeler içinde tek bir birleşik video oluşturulmalıdır.

### 💡 Adım 5: Akıllı Format Önerileri (Suggester)
* **Viewmodel Entegrasyonu:** `SmartFormatSuggester.kt` yazılarak video başlığı ve süresine göre dikey Shorts (9:16) tespiti yapılmalıdır.
* **Arayüz Kartı:** Arayüzün üstünde parlayan, glassmorphic bir `💡 Öneri: Dikey Shorts Tespit Edildi. Uygulamak için tıklayın` banner'ı gösterilmeli, tıklandığında ilgili klip dikey kesim moduna (crop) geçmelidir.

---

## 🛠️ Gelecek Sefer Nereden Başlayacağız?

Bir sonraki sprint için geldiğimizde izleyeceğimiz rota sırasıyla şudur:
1. **Android Projesinin İncelenmesi:** `android/` klasörü altındaki Gradle yapısını ve `ffmpeg-kit` entegrasyonunu kontrol edeceğiz.
2. **QuickJS / JS Runtime Kurulumu:** Android emülatör/cihaz üzerinde `yt-dlp`'nin hız sınırlamasına takılmadan çalışmasını güvence altına alacağız.
3. **Jetpack Compose UI Güncellemesi:** Çoklu slider ve klip satırları (ClipRow) arayüzünü tasarlamaya başlayacağız.

*Bu yol haritası, gelecekte Android projesini de tıpkı masaüstü gibi profesyonel bir dev haline getirmemizi sağlayacaktır.*
