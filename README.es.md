<div align="center">

<img src="assets/screenshots/preview.gif" alt="yt-dlp Downloader Pro" width="680"/>

# yt-dlp Downloader Pro

**Descargador de videos y música en un solo clic — Windows y Android**

<p align="center">
  <a href="README.md">🇺🇸 English</a> &nbsp;·&nbsp;
  <a href="README.tr.md">🇹🇷 Türkçe</a> &nbsp;·&nbsp;
  <b>🇪🇸 Español</b>
</p>

Descarga videos, música y listas de reproducción de YouTube, Vimeo, SoundCloud y más de 1000 sitios.  
Recorte, conversión de formatos, gestión de colas — todo en una sola aplicación.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-0078d4?logo=windows)](https://github.com/BayNuman/yt-dlp-downloader-pro/releases)
[![Platform: Android](https://img.shields.io/badge/Platform-Android%208%2B-3ddc84?logo=android)](https://github.com/BayNuman/yt-dlp-downloader-pro/releases)
[![Android CI](https://github.com/BayNuman/yt-dlp-downloader-pro/actions/workflows/android-ci.yml/badge.svg)](https://github.com/BayNuman/yt-dlp-downloader-pro/actions/workflows/android-ci.yml)
[![Stars](https://img.shields.io/github/stars/BayNuman/yt-dlp-downloader-pro?style=social)](https://github.com/BayNuman/yt-dlp-downloader-pro/stargazers)
[![Patreon](https://img.shields.io/badge/Patreon-Sponsor-F96854?logo=patreon)](https://patreon.com/BayNuman?utm_medium=unknown&utm_source=join_link&utm_campaign=creatorshare_creator&utm_content=copyLink)

[**⬇️ Descargar Windows**](https://github.com/BayNuman/yt-dlp-downloader-pro/releases/latest/download/yt-dlp_Downloader_Pro_Setup.exe) &nbsp;·&nbsp;
[**📱 APK de Android**](https://github.com/BayNuman/yt-dlp-downloader-pro/releases/latest/download/app-release.apk) &nbsp;·&nbsp;
[**🐛 Reportar Error**](https://github.com/BayNuman/yt-dlp-downloader-pro/issues/new?template=bug_report.md) &nbsp;·&nbsp;
[**💡 Solicitar Función**](https://github.com/BayNuman/yt-dlp-downloader-pro/issues/new?template=feature_request.md) &nbsp;·&nbsp;
[**🧡 Patrocinar en Patreon**](https://patreon.com/BayNuman?utm_medium=unknown&utm_source=join_link&utm_campaign=creatorshare_creator&utm_content=copyLink)

</div>

---

## ✨ ¿Por qué es diferente?

Existen docenas de interfaces para yt-dlp. Este proyecto es diferente porque ofrece:

| Función | Otras GUIs | Esta Aplicación |
|---|---|---|
| Recorte de intervalo (trimming) | ❌ | ✅ Deslizador de rango con doble control |
| Soporte de capítulos | ❌ | ✅ Clic para auto-rellenar intervalo |
| Multi-clip del mismo video | ❌ | ✅ Fusión de intervalos greedy |
| Exportación para Reels / Shorts | ❌ | ✅ Auto-recorte vertical 9:16 |
| Límite de tamaño Discord/WhatsApp | ❌ | ✅ Bitrate calculado automáticamente |
| Fallback automático YouTube 403 | ❌ | ✅ Reintento automático con TV Client |
| Sugerencia inteligente de formato | ❌ | ✅ Análisis automático de metadatos |
| Descarga paralela en cola | ❌ en la mayoría | ✅ ThreadPoolExecutor |

---

## ⬇️ Instalación

> No necesitas instalar Python, ffmpeg ni utilizar la terminal. Todo viene pre-empaquetado y listo para ejecutar.

| Plataforma | Paquete | Descarga |
|---|---|---|
| 🖥️ Windows | Instalador (.exe) — Recomendado | [📥 Descargar Setup](https://github.com/BayNuman/yt-dlp-downloader-pro/releases/latest/download/yt-dlp_Downloader_Pro_Setup.exe) |
| 🖥️ Windows | Portable (.exe) — Sin instalación | [📥 Descargar Portable](https://github.com/BayNuman/yt-dlp-downloader-pro/releases/latest/download/yt-dlp.Downloader.Pro.exe) |
| 📱 Android | APK (Android 8.0+) | [📥 Descargar APK](https://github.com/BayNuman/yt-dlp-downloader-pro/releases/latest/download/app-release.apk) |

**Advertencia de SmartScreen en Windows:** Si aparece una alerta de SmartScreen, haz clic en "Más información" → "Ejecutar de todos modos". La aplicación es completamente de código abierto; puedes revisar el código tú mismo.

**Instalación en Android:** Ve a Ajustes → Aplicaciones → Permitir la instalación desde fuentes desconocidas → Pulsa el APK descargado para instalar.

---

## 📸 Capturas de pantalla

<table>
<tr>
<td><img src="assets/screenshots/desktop_dark_main.png" alt="Windows — Dark Mode" width="340"/></td>
<td><img src="assets/screenshots/desktop_light_main.png" alt="Windows — Light Mode" width="340"/></td>
</tr>
<tr>
<td align="center"><em>Windows — Tema Oscuro</em></td>
<td align="center"><em>Windows — Tema Claro</em></td>
</tr>
</table>

<table>
<tr>
<td><img src="assets/screenshots/android_dark.jpg" alt="Android — Download" width="160"/></td>
<td><img src="assets/screenshots/android_queue.png" alt="Android — Queue" width="160"/></td>
<td><img src="assets/screenshots/android_history.png" alt="Android — History" width="160"/></td>
<td><img src="assets/screenshots/android_settings.png" alt="Android — Settings" width="160"/></td>
</tr>
<tr>
<td align="center"><em>Descarga</em></td>
<td align="center"><em>Cola</em></td>
<td align="center"><em>Historial</em></td>
<td align="center"><em>Ajustes</em></td>
</tr>
</table>

---

## 🎯 Características

### ✂️ Clip Engine — Único en esta App

Descarga únicamente la sección que te interese de un video. Obtén un fragmento de 30 segundos a partir de un video de 30 minutos en cuestión de segundos.

- **Deslizador de doble control** — arrastra los controles izquierdo y derecho para ajustar el tiempo de inicio y fin.
- **Soporte de capítulos** — al pulsar sobre un capítulo del video, los tiempos de intervalo se rellenan automáticamente.
- **Múltiples recortes** — selecciona varios intervalos de tiempo del mismo enlace y agrégalos a la cola de una sola vez.
- **Cortes rápidos y precisos** — admite el ajuste rápido por fotogramas clave (instantáneo) o precisión de milisegundos (re-codificación local).
- **Estrategia híbrida** — optimiza las descargas mediante stream seeking si el fragmento es menor al 15% del total, o descarga amortiguada + recorte local para fragmentos mayores.

### 🎨 Perfiles de Exportación

| Perfil | Salida |
|---|---|
| Instagram Reels (máx 90s) | Recorte central vertical 9:16 en MP4 |
| YouTube Shorts (máx 60s) | Recorte central vertical 9:16 en MP4 |
| Discord (máx 25MB) | Calcula automáticamente la tasa de bits óptima |
| WhatsApp (máx 16MB) | Calcula automáticamente la tasa de bits óptima |
| Creador de GIF/Memes | 15fps, ancho de 480px, optimización de paleta premium |
| Nota de voz / Audiolibro | Canal mono, 48kbps M4A optimizado para voz |

### 📋 Gestión de Colas

- Descargas en paralelo mediante `ThreadPoolExecutor` de Python (`max_workers` configurable).
- Historial persistente (SQLite) — vuelve a descargar con un solo clic.
- Plantillas personalizadas configuradas (ej. MP3 para Podcasts, Archivo 4K).
- Ajustes de descargas: rango de lista de reproducción, límite de velocidad y fragmentos concurrentes.

### 🔧 Características Avanzadas

- **SponsorBlock** — omite secciones patrocinadas de forma automática.
- **Soporte de Cookies** — importa cookies desde un archivo de texto o directamente desde navegadores conocidos (Chrome, Edge, Firefox, etc.).
- **Auto-fallback 403** — cambia el cliente de scraping a la interfaz de TV ante fallos de firma HTTP 403.
- Incrustación de metadatos, reescalado de miniaturas en alta resolución y descarga de subtítulos.
- **Sugeridor Inteligente** — analiza las dimensiones, duración y etiquetas del video para sugerir crop vertical, MP4 estándar o audiolibro MP3.
- Campo libre de argumentos yt-dlp para una flexibilidad total mediante línea de comandos.

### 🌍 Resumen de Plataformas

| Característica | Windows | Android |
|---|---|---|
| Tema Claro / Oscuro | ✅ | ✅ |
| Español / Inglés / Turco | ✅ | ✅ |
| Descargas en segundo plano | ✅ | ✅ ForegroundService |
| Compartir enlace directo (Share Menu) | — | ✅ Share Intent |
| Notificaciones | ✅ Toast deslizante | ✅ Notificación nativa |

---

## 🚀 Inicio Rápido

### Windows

```
1. Descarga el instalador "yt-dlp_Downloader_Pro_Setup.exe".
2. Haz doble clic y selecciona "Siguiente" → "Instalar" (~30 segundos).
3. Abre el acceso directo, pega tu enlace y haz clic en Descargar!
```

### Android

```
1. Descarga el archivo "app-release.apk" en tu teléfono.
2. Permite la opción "Instalar aplicaciones de fuentes desconocidas".
3. Abre el archivo APK descargado, confirma los permisos y empieza!
```

---

## 🛠️ Compilación desde el origen

### Requisitos (Windows)

- Python 3.10+
- Inno Setup 6 (para empaquetar el instalador setup)

```bash
git clone https://github.com/BayNuman/yt-dlp-downloader-pro.git
cd yt-dlp-downloader-pro

pip install customtkinter yt-dlp pillow requests pyinstaller tkinterdnd2

# Ejecutar aplicación
python app.py

# Compilar EXE portable + instalador setup
python build_full_distribution.py
```

El script de compilación descarga automáticamente las dependencias (ffmpeg.exe, ffprobe.exe), las empaqueta con PyInstaller y genera el instalador mediante Inno Setup.

### Requisitos (Android)

- Android Studio Hedgehog (2023.1.1)+
- JDK 17+
- SDK de Android API 26+

```bash
cd android
./gradlew assembleRelease
# El archivo resultante se ubicará en: android/app/build/outputs/apk/release/app-release.apk
```

---

## 🏗️ Arquitectura

```
yt-dlp-downloader-pro/
│
├── 🖥️  Desktop (Python + CustomTkinter)
│   ├── app.py                    # Punto de entrada de la aplicación - llama a main()
│   ├── core/
│   │   ├── app_state.py          # Motor de estado thread-safe con RLock + detección automática de idioma
│   │   ├── command_builder.py    # Funciones puras - genera los argumentos de yt-dlp
│   │   ├── downloader.py         # Ejecutor concurrente mediante ThreadPoolExecutor
│   │   ├── clip.py               # Algoritmo de LeetCode 56 Greedy Interval Merging
│   │   ├── merger.py             # FFmpeg Concat Demuxer para uniones sin pérdida
│   │   ├── profiles.py           # Perfiles polimórficos de salida ffmpeg
│   │   ├── suggester.py          # Motor de sugerencias heurísticas
│   │   ├── history.py            # SQLite + caché de conexión thread-local + modo WAL
│   │   ├── presets.py            # Presets JSON con capa de caché en memoria
│   │   ├── updater.py            # Comprobación de actualizaciones en PyPI
│   │   └── env.py                # Actualización en vivo del PATH en Windows
│   └── ui/
│       ├── theme.py              # Paletas de color HSL + traducciones i18n (en/tr/es)
│       ├── main_window.py        # Orquestador GUI con vaciado de cola UI coalescente
│       ├── components/toast.py   # Jerarquía OOP BaseToast (ActionableToast, NotificationToast)
│       └── panels/               # Paneles modulares con diffing inteligente de widgets
│
└── 📱  Android (Kotlin + Jetpack Compose)
    └── android/app/src/main/
        ├── MainActivity.kt
        ├── service/DownloadService.kt  # ForegroundService con enlace de ciclo de vida
        ├── data/
        │   ├── DownloadModels.kt       # Modelos Request/Event/Record + serialización JSON
        │   ├── YtDlpCommandBuilder.kt  # Constructor CLI con optimización de secciones de clips
        │   ├── YtDlpRunner.kt          # Parser stdout basado en regex + fallback multi-ruta
        │   └── algorithms/ClipOptimizer.kt  # Fusión de intervalos greedy
        └── ui/
            ├── DownloaderScreen.kt
            ├── DownloaderViewModel.kt   # Arquitectura RuntimeState de 4 flujos
            └── theme/Translations.kt
```

**Decisiones de Diseño Clave:**
- Capa `core/` totalmente desacoplada de la interfaz gráfica — código limpio y portable.
- `command_builder.py` implementa únicamente funciones puras sin referencias a `self`, ideales para testing.
- `AppState` thread-safe con `RLock` — compartido de forma segura entre hilos de descarga y UI.
- Caché de conexión SQLite thread-local con modo WAL — elimina la sobrecarga de apertura/cierre redundante.
- Diffing inteligente de widgets en `QueuePanel` — solo reconstruye tarjetas cuando cambia la composición de la lista de tareas, eliminando el parpadeo.
- `RuntimeState` data class en Android — consolida 11 StateFlows en una arquitectura type-safe de 4 flujos combine.
- Archivo central de descargas en `app-data-dir/download_archive.txt` — previene re-descargas entre carpetas en ambas plataformas.

---

## 🌍 Sitios soportados

Gracias a la integración con yt-dlp, la aplicación admite más de **1000 sitios**:

YouTube • YouTube Music • Vimeo • SoundCloud • Twitter/X • Instagram • TikTok • Facebook • Dailymotion • Twitch • Reddit • Bandcamp • y más...

→ [Lista completa de sitios soportados](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)

---

## 🗺️ Hoja de Ruta

- [ ] Soporte de escritorio para macOS
- [ ] Engine de recorte en Android (deslizador de rango + perfiles de exportación)
- [ ] Extensión del navegador (integración en Chrome/Firefox en un solo clic)
- [ ] Programación de descargas (ej. iniciar descargas a las 2:00 AM)
- [ ] Integración con Plex / Jellyfin (auto-etiquetado de directorios de medios)
- [ ] Deslizador de miniaturas visuales (filmstrip)

¿Tienes sugerencias? [¡Crea una solicitud de función!](https://github.com/BayNuman/yt-dlp-downloader-pro/issues/new?template=feature_request.md)

---

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas — correcciones de errores, nuevas traducciones o sugerencias!

1. Lee nuestra [Guía de Contribución](CONTRIBUTING.md)
2. Explora los [Temas Abiertos](https://github.com/BayNuman/yt-dlp-downloader-pro/issues)
3. ¡Haz un fork, crea tu rama de desarrollo y abre un Pull Request!

---

## ⚖️ Descargo de Responsabilidad

Este software es un cliente gráfico para [yt-dlp](https://github.com/yt-dlp/yt-dlp). Los usuarios son los únicos responsables de cumplir con las condiciones de uso de las respectivas plataformas desde las que descargan contenido multimedia. Descarga únicamente materiales sobre los cuales poseas derechos legales de acceso.

---

## 📄 Licencia

Distribuido bajo la Licencia MIT. Consulta [LICENSE](LICENSE) para más detalles.

---

<div align="center">

Hecho con ❤️ por [BayNuman](https://github.com/BayNuman)

[**🧡 Conviértete en un Patrón en Patreon**](https://patreon.com/BayNuman?utm_medium=unknown&utm_source=join_link&utm_campaign=creatorshare_creator&utm_content=copyLink)

Si te gusta este proyecto, no olvides darle una ⭐ para que otros puedan descubrirlo!

</div>
