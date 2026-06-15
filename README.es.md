# yt-dlp Downloader Pro

<p align="center">
  <a href="README.md">🇺🇸 English</a> &nbsp;·&nbsp;
  <a href="README.tr.md">🇹🇷 Türkçe</a> &nbsp;·&nbsp;
  <b>🇪🇸 Español</b>
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-0078d4?logo=windows)](https://github.com/BayNuman/yt-dlp-downloader-pro/releases)
[![Platform: Android](https://img.shields.io/badge/Platform-Android%208%2B-3ddc84?logo=android)](https://github.com/BayNuman/yt-dlp-downloader-pro/releases)
[![Android CI](https://github.com/BayNuman/yt-dlp-downloader-pro/actions/workflows/android-ci.yml/badge.svg)](https://github.com/BayNuman/yt-dlp-downloader-pro/actions/workflows/android-ci.yml)
[![Stars](https://img.shields.io/github/stars/BayNuman/yt-dlp-downloader-pro?style=social)](https://github.com/BayNuman/yt-dlp-downloader-pro/stargazers)

> Un descargador de video y audio premium de alto rendimiento con una interfaz glassmorphic translúcida. Soporta recorte de intervalos de tiempo, integración de SponsorBlock, cola de descargas en paralelo, estructuras de carpetas inteligentes y un generador de recorte vertical 9:16 para Instagram Reels y YouTube Shorts. Desarrollado con tecnología `yt-dlp` y `FFmpeg`.

<div align="center">
  <img src="assets/screenshots/preview.gif" alt="yt-dlp Downloader Pro Vista Previa" width="680"/>
</div>

---

## 📥 Descargas Rápidas

| Plataforma | Tipo | Paquete de Lanzamiento |
| :--- | :--- | :--- |
| **🖥️ Windows** | Instalador (Recomendado) | [📥 Descargar Setup.exe](https://github.com/BayNuman/yt-dlp-downloader-pro/releases/latest/download/yt-dlp_Downloader_Pro_Setup.exe) |
| **🖥️ Windows** | Portable | [📥 Descargar Portable.exe](https://github.com/BayNuman/yt-dlp-downloader-pro/releases/latest/download/yt-dlp.Downloader.Pro.exe) |
| **📱 Android** | APK (Android 8.0+) | [📥 Descargar App.apk](https://github.com/BayNuman/yt-dlp-downloader-pro/releases/latest/download/app-release.apk) |

---

## 🚀 Características Destacadas

| Característica | Otras Interfaces | yt-dlp Downloader Pro |
| :--- | :--- | :--- |
| **Recorte de Tiempo** | ❌ (Solo descarga completa) | ✅ Deslizador de rango interactivo de doble control |
| **Multi-Clip Inteligente** | ❌ | ✅ Fusión de intervalos greedy (LeetCode 56) |
| **Recorte para Reels/Shorts** | ❌ | ✅ Perfil de formato con recorte central automático 9:16 |
| **SponsorBlock** | ❌ | ✅ Omitir o cortar segmentos de patrocinadores automáticamente |
| **Bypass de Error 403** | ❌ | ✅ Fallback automático al cliente de TV en firmas HTTPS |
| **Espectro de Audio** | ❌ | ✅ Vista previa del espectro de onda en solo 1.5s |
| **Cola en Paralelo** | ❌ en la mayoría | ✅ Cola de descargas thread-safe de alto rendimiento |

---

## 📦 Instalación y Configuración

### Binarios Pre-compilados

#### 🖥️ Configuración en Windows
1. Descarga [yt-dlp_Downloader_Pro_Setup.exe](https://github.com/BayNuman/yt-dlp-downloader-pro/releases/latest/download/yt-dlp_Downloader_Pro_Setup.exe).
2. Haz doble clic en el instalador y completa el asistente de configuración (tarda unos 30 segundos).
3. *Nota de SmartScreen:* Si Windows SmartScreen bloquea el lanzamiento, haz clic en **Más información** → **Ejecutar de todos modos**.

#### 📱 Configuración en Android
1. Descarga [app-release.apk](https://github.com/BayNuman/yt-dlp-downloader-pro/releases/latest/download/app-release.apk).
2. Habilita **Instalar desde fuentes desconocidas** en los ajustes de seguridad de Android.
3. Abre el archivo APK y pulsa **Instalar**.

---

## 🛠️ Compilación Desde el Código Fuente

### Requisitos para Escritorio
- **Python** (v3.10 o superior)
- **FFmpeg** y **FFprobe** (El script de compilación los descargará automáticamente si faltan)
- **Inno Setup 6** (Requerido solo para empaquetar el instalador de Windows)

### Comandos de Ejecución y Compilación
1. **Clona el repositorio:**
   ```bash
   git clone https://github.com/BayNuman/yt-dlp-downloader-pro.git
   cd yt-dlp-downloader-pro
   ```
2. **Instala las dependencias de Python:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Inicia la aplicación:**
   ```bash
   python app.py
   ```
4. **Compila el ejecutable (.EXE) y el instalador de Windows:**
   ```bash
   python build_full_distribution.py
   ```

### Requisitos y Compilación para Android
- **Android Studio** Hedgehog (2023.1.1) o superior
- **JDK 17**
- **Android SDK API 26+**

```bash
cd android
./gradlew assembleRelease
```
*El APK resultante se generará en: `android/app/build/outputs/apk/release/app-release.apk`*

---

## 🛠️ Ejemplos de Uso

### Modo GUI Visual
Simplemente ejecuta la aplicación. Pega la URL, elige tu perfil de formato (ej. *Best Quality*, *Full HD 1080p*, *Instagram Reels*), selecciona los rangos de recorte si lo deseas, y presiona **Iniciar Descargas**.

### Modo CLI sin Await (Ejecutable de Windows)
El archivo ejecutable standalone intercepta argumentos usando un cargador CLI personalizado. Si se ejecuta con `-m yt_dlp`, funciona como una interfaz de línea de comandos estándar:
```bash
"yt-dlp Downloader Pro.exe" -m yt_dlp "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --format bestvideo+bestaudio
```

### Hook de Código Programático (Python)
Los desarrolladores pueden importar los módulos directamente de `core/`. Por ejemplo, para generar argumentos de comandos programáticamente:
```python
from core.command_builder import build_ytdlp_args
from core.app_state import DownloadTask

# Crea la representación de estado de una tarea de descarga
task = DownloadTask(
    url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    preset="1080p",
    output_dir="downloads"
)

# Genera los argumentos puros para la CLI de yt-dlp
args = build_ytdlp_args(task)
print("Argumentos de yt-dlp:", args)
```

---

## 📸 Capturas de Pantalla

<table>
<tr>
<td><img src="assets/screenshots/desktop_dark_main.png" alt="Windows — Modo Oscuro" width="340"/></td>
<td><img src="assets/screenshots/desktop_light_main.png" alt="Windows — Modo Claro" width="340"/></td>
</tr>
<tr>
<td align="center"><em>Windows — Tema Oscuro</em></td>
<td align="center"><em>Windows — Tema Claro</em></td>
</tr>
</table>

<table>
<tr>
<td><img src="assets/screenshots/android_dark.jpg" alt="Android — Descargar" width="160"/></td>
<td><img src="assets/screenshots/android_queue.png" alt="Android — Cola" width="160"/></td>
<td><img src="assets/screenshots/android_history.png" alt="Android — Historial" width="160"/></td>
<td><img src="assets/screenshots/android_settings.png" alt="Android — Ajustes" width="160"/></td>
</tr>
<tr>
<td align="center"><em>Descarga</em></td>
<td align="center"><em>Cola</em></td>
<td align="center"><em>Historial</em></td>
<td align="center"><em>Ajustes</em></td>
</tr>
</table>

---

## 🏗️ Arquitectura del Proyecto

```text
yt-dlp-downloader-pro/
│
├── 🖥️  Escritorio (Python + CustomTkinter)
│   ├── app.py                    # Punto de entrada (Bootstrap) - solo llama a main()
│   ├── core/
│   │   ├── app_state.py          # Motor de estado con RLock y detección de idioma
│   │   ├── command_builder.py    # Funciones puras - genera argumentos de yt-dlp
│   │   ├── downloader.py         # Y ejecutor de cola con ThreadPoolExecutor
│   │   ├── clip.py               # Algoritmo de LeetCode 56 Greedy Interval Merging
│   │   ├── merger.py             # FFmpeg Concat Demuxer para unión sin pérdidas
│   │   ├── profiles.py           # Perfiles de conversión polimórficos de FFmpeg
│   │   ├── suggester.py          # Motor de sugerencia heurístico
│   │   ├── history.py            # SQLite + caché local de conexiones + modo WAL
│   │   ├── presets.py            # Capa de caché en memoria de perfiles JSON
│   │   ├── updater.py            # Verificador de versiones en PyPI
│   │   └── env.py                # Recargador de variables de entorno de Windows
│   └── ui/
│       ├── theme.py              # Paletas HSL y traducciones integradas (en/tr/es)
│       ├── main_window.py        # Interfaz de usuario con drenaje unificado de cola
│       ├── components/toast.py   # Jerarquía OOP de notificaciones toast
│       └── panels/               # Paneles modulares (Cola, Avanzado, Vista previa)
│
└── 📱  Android (Kotlin + Jetpack Compose)
    └── android/app/src/main/
        ├── MainActivity.kt
        ├── service/DownloadService.kt  # Servicio en primer plano vinculado al ciclo de vida
        ├── data/
        │   ├── DownloadModels.kt       # Modelos de solicitud/evento + serialización JSON
        │   ├── YtDlpCommandBuilder.kt  # Generador de CLI optimizado para clips
        │   ├── YtDlpRunner.kt          # Intérprete stdout con fallback multicanal
        │   └── algorithms/ClipOptimizer.kt  # Fusión de intervalos greedy (LeetCode 56)
        └── ui/
            ├── DownloaderScreen.kt
            ├── DownloaderViewModel.kt   # Arquitectura unificada de RuntimeState
            └── theme/Translations.kt
```

---

## 🌍 Sitios Soportados

Basado en `yt-dlp`, esta aplicación es compatible con más de **1000 sitios web**:

YouTube • YouTube Music • Vimeo • SoundCloud • Twitter/X • Instagram • TikTok • Facebook • Dailymotion • Twitch • Reddit • Bandcamp • y más...

→ [Lista completa de sitios compatibles](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)

---

## 🗺️ Mapa de Ruta

- [ ] Soporte para macOS
- [ ] Recorte de clips en Android (deslizador + perfiles de conversión)
- [ ] Integración con navegadores mediante extensión
- [ ] Descargas programadas con temporizador diferido
- [ ] Integración y etiquetado automático con Plex y Jellyfin
- [ ] Deslizador con fotogramas de video (filmstrip)

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas!
1. Lee nuestra [Guía de Contribución](CONTRIBUTING.md)
2. Realiza un fork del repositorio, crea una rama e inicia un Pull Request.

---

## ⚖️ Descargo de Responsabilidad

Este software es un cliente gráfico para [yt-dlp](https://github.com/yt-dlp/yt-dlp). Los usuarios son los únicos responsables de cumplir los términos de servicio de las plataformas desde las cuales descargan contenido.

---

## 📄 Licencia

Distribuido bajo la Licencia MIT. Consulta [LICENSE](LICENSE) para más detalles.

---

## 💡 Prácticas Recomendadas (Dos & Don'ts)

| Qué Hacer | Qué Evitar |
| :--- | :--- |
| **Usar rutas relativas** (`./assets/...` o enlaces del repositorio) para imágenes y recursos. | **Evitar rutas absolutas** (`C:/Users/nombre/...`) ya que no funcionarán en otros entornos. |
| **Especificar el lenguaje de programación** en los bloques de código (ej. ` ```bash `, ` ```python `) para habilitar el coloreado. | **No dejar bloques de código sin formatear** o usar bloques genéricos ` ``` `. |
| **Utilizar tablas y emojis** para estructurar textos largos y reducir la fatiga visual. | **No escribir bloques masivos de texto plano**, ya que dificultan la lectura. |
| **Mantener las instrucciones actualizadas** y verificar la ejecución de los comandos antes de publicar. | **No dejar pasos obsoletos** ni dependencias sin documentar que afecten la experiencia de desarrollo (DX). |

---

<div align="center">

Creado con ❤️ por [BayNuman](https://github.com/BayNuman)

[**🧡 Conviértete en Patrocinador en Patreon**](https://patreon.com/BayNuman?utm_medium=unknown&utm_source=join_link&utm_campaign=creatorshare_creator&utm_content=copyLink)

Si encuentras este proyecto útil, ¡no olvides apoyarnos con una ⭐!

</div>
