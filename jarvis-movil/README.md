# YARBYS: asistente de IA 100% en tu celular

Curso en video y código de **YARBYS**, un asistente de inteligencia artificial que vive dentro del celular. Lee tus documentos, recuerda tus conversaciones y te habla, todo sin internet.

| Carpeta | Contenido |
|---|---|
| [`yarbys/`](yarbys/) | La app de Flutter (Android y iPhone). Su README explica cómo compilarla y probarla. |
| [`curso/`](curso/) | El código tal como queda al final de cada uno de los 9 videos del curso. |
| [`documentos-ejemplo/`](documentos-ejemplo/) | `agenda.txt` y `perfil.txt`, los documentos que se usan en el video. |
| [`video/`](video/) | El generador del video tutorial (`render.py`) con sus escenas animadas. |

## El stack (todo dentro del celular)

| Pieza | Herramienta |
|---|---|
| Cerebro (LLM) | Gemma 4 E2B con `flutter_edge_ai` + LiteRT-LM |
| Embeddings | EmbeddingGemma 2 |
| Base de datos vectorial | Qdrant Edge (`flutter_edge_ai_qdrant`) |
| Memoria | SQLite (`sqflite`) |
| Voz | `speech_to_text` y `flutter_tts` |

## Descargar el APK

**Descarga directa** (ábrelo desde el celular): https://github.com/paulantezana/tutoriales/releases/download/yarbys-latest/yarbys.apk

El workflow [`.github/workflows/yarbys-apk.yml`](../.github/workflows/yarbys-apk.yml) compila el APK en GitHub Actions cada vez que cambia `yarbys/`. Búscalo en la pestaña **Actions** → **YARBYS APK** → artefacto **yarbys-apk**. Si publicas un **Release** en GitHub, el APK se adjunta a ese Release.

## Videos del curso (`video/`)

`render.py` genera cada video del curso (1080p, narrado en español). El guion de cada uno está en `video/guiones/videoNN.py`:

- **Motion graphics** con HTML + GSAP (`video/escenas/escenas.js`) en estilo plano y oscuro, renderizados cuadro a cuadro con Chromium: portada, "dónde estamos" en la arquitectura y el cierre con lo que sigue.
- **VS Code en Windows**: el código se escribe y se explica **línea por línea**. Cada archivo pasa exactamente del código del video anterior al del video actual (`curso/NN-*`), y el guion verifica que quede idéntico.
- **Debug Console y depurador**: F5, `debugPrint`, puntos de parada y el valor de las variables.
- **La app en el celular**: `video/escenas/celular.html` es una réplica de las pantallas en cada etapa (interfaz básica de Material y diseño final). Las respuestas de YARBYS en los videos son de ejemplo, basadas en `documentos-ejemplo/`.
- **Voz** con [Kokoro](https://github.com/thewh1teagle/kokoro-onnx), sin internet. El logo del canal aparece en una esquina y los subtítulos van aparte (`.srt`).

```bash
pip install pillow pygments kokoro-onnx soundfile playwright   # + ffmpeg y Chromium
# Modelo de voz en video/modelos/ (kokoro-v1.0.onnx + voices-v1.0.bin, ver el README de jarvis-ia)
python video/render.py --video 2              # video/videos/02-gemma-en-consola.mp4 (+ .md y .srt)
python video/render.py --video 2 --preview 20 # una captura cada 20 s en video/preview/
```
