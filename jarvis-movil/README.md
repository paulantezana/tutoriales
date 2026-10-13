# YARBYS: asistente de IA 100% en tu celular

Curso en video y código de **YARBYS**, un asistente de inteligencia artificial que vive dentro del celular. Lee tus documentos, recuerda tus conversaciones y te habla, todo sin internet.

| Carpeta | Contenido |
|---|---|
| [`yarbys/`](yarbys/) | La app de Flutter (Android y iPhone). Su README explica cómo compilarla y probarla. |
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
| LLM externo (opcional, Pro) | OpenAI o Anthropic con la API key del usuario |

## Descargar el APK

**Descarga directa** (ábrelo desde el celular): https://github.com/paulantezana/tutoriales/releases/download/yarbys-latest/yarbys.apk

El workflow [`.github/workflows/yarbys-apk.yml`](../.github/workflows/yarbys-apk.yml) compila el APK en GitHub Actions cada vez que cambia `yarbys/`. Búscalo en la pestaña **Actions** → **YARBYS APK** → artefacto **yarbys-apk**. Si publicas un **Release** en GitHub, el APK se adjunta a ese Release.

## Video tutorial (`video/`)

`render.py` genera la clase completa (1080p, narrada en español):

- **Motion graphics** con HTML + GSAP (`video/escenas/escenas.js`) en estilo plano y oscuro, renderizados cuadro a cuadro con Chromium.
- **VS Code en Windows**: explorador, pestañas, autocompletado, PowerShell y notas que explican cada bloque. El código se lee de `yarbys/`, así que el video coincide con el proyecto.
- **La app en el celular**: `video/escenas/app.html` es una réplica visual de las pantallas de Flutter (mismo diseño y el mismo núcleo animado), manejada por eventos. Las respuestas de YARBYS en el video son de ejemplo, basadas en `documentos-ejemplo/`.
- **Voz** con [Kokoro](https://github.com/thewh1teagle/kokoro-onnx), sin internet. El logo del canal aparece en una esquina durante todo el video y no lleva subtítulos incrustados (`subtitulos.srt` queda aparte para YouTube).

```bash
pip install pillow pygments kokoro-onnx soundfile playwright   # + ffmpeg y Chromium
# Modelo de voz en video/modelos/ (kokoro-v1.0.onnx + voices-v1.0.bin, ver el README de jarvis-ia)
python video/render.py              # tutorial.mp4 + guion.md + subtitulos.srt
python video/render.py --preview 20 # una captura cada 20 s en video/preview/
```
