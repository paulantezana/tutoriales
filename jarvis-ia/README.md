# JARVIS: tu asistente personal con IA (Windows, sin Docker)

Un asistente personal que conoce **tu información** (RAG), **recuerda** cada conversación y **te responde con voz** desde una página web.

| Pieza | Herramienta | Para qué |
|---|---|---|
| Cerebro (LLM) | **GPT-6 Luna** de OpenAI (`gpt-6-luna`) | Entiende tu pregunta y responde |
| Embeddings | **Ollama** + `bge-m3` (local, gratis, +100 idiomas) | Convierte textos en vectores |
| Búsqueda | **Qdrant** (`qdrant.exe` para Windows) | Encuentra la información más parecida |
| Memoria | **PostgreSQL** (instalador para Windows) | Guarda cada hilo de conversación |
| Unión | **LangChain** | Conecta todas las piezas |
| Web | **FastAPI** + HTML/CSS/JS | Chat con voz en el navegador |

## 1. Instalación en Windows

1. **Python 3.10+** desde [python.org](https://www.python.org/downloads/). En el instalador, marca **"Add python.exe to PATH"**.
2. **Ollama** desde [ollama.com](https://ollama.com/download). Luego, en PowerShell:
   ```powershell
   ollama pull bge-m3
   ```
3. **Qdrant**: en [github.com/qdrant/qdrant/releases](https://github.com/qdrant/qdrant/releases), descarga el `.zip` para Windows de la última versión y descomprímelo en `C:\qdrant`. Para encenderlo:
   ```powershell
   C:\qdrant\qdrant.exe
   ```
   Panel web: http://localhost:6333/dashboard
4. **PostgreSQL** con el instalador oficial para Windows ([postgresql.org/download/windows](https://www.postgresql.org/download/windows/)). Anota la contraseña del usuario `postgres`. Usamos la base de datos `postgres` que viene por defecto.
5. **API key de OpenAI** en [platform.openai.com](https://platform.openai.com/api-keys).

## 2. Ejecutar el proyecto (`codigo/`)

```powershell
cd codigo
python -m venv .venv
.venv\Scripts\activate          # si da error de permisos: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements.txt
copy .env.example .env           # pon tu API key y la contraseña de PostgreSQL

python ingest.py                 # carga docs\*.txt en Qdrant
uvicorn app:app --reload         # abre http://127.0.0.1:8000
```

- `docs/`: tu información (perfil, agenda...). Si la cambias, vuelve a ejecutar `python ingest.py`.
- `asistente.py`: el cerebro: GPT-6 Luna, búsqueda en Qdrant y memoria en PostgreSQL.
- `app.py`: servidor FastAPI (`POST /api/chat`) que además sirve la página de `web/`.
- `web/`: la interfaz de JARVIS. La voz (hablar y escuchar) usa las APIs del navegador; el micrófono funciona en Chrome y Edge.

### ¿Por qué GPT-6 Luna?

Según [Artificial Analysis](https://artificialanalysis.ai) (octubre de 2026, Intelligence Index v4.3.2, modo de razonamiento máximo):

| Modelo | Inteligencia | Precio por millón de tokens (entrada / salida) |
|---|---|---|
| Claude Opus 5.5 | 58 | $4 / $20 |
| Claude Sonnet 5.5 | 56 | $2 / $10 |
| Gemini 4 Argon | 53 | $2 / $10 (promoción) |
| GPT-6 Sol | 48 | $2 / $10 |
| Claude Haiku 5.5 | 43 | $0.10 / $0.50 |
| DeepSeek V4.1 Flash | 39 | $0.30 / $1.20 |
| **GPT-6 Luna** | **38** | **$0.10 / $0.50** |

Para un asistente personal no hace falta el modelo más caro. Claude Haiku 5.5 es una alternativa con el mismo precio. Los precios cambian seguido: revísalos antes de usarlos.

## 3. Video tutorial (`video/`)

`render.py` genera la clase completa (unos 25 minutos, 1080p, narrada en español):

- **Motion graphics** hechos con HTML + GSAP (`video/escenas/`), renderizados cuadro a cuadro con Chromium.
- **VS Code en Windows**: explorador, pestañas, autocompletado, PowerShell, varias terminales y notas que explican cada bloque.
- **La página real de JARVIS** grabada en Chromium. Las respuestas de JARVIS en el video son de ejemplo: no se llamó a la API de OpenAI.
- **Voz**: narrador y JARVIS con [Kokoro](https://github.com/thewh1teagle/kokoro-onnx), sin internet. El logo del canal (`video/marca/logo.png`) aparece en una esquina durante todo el video.

```bash
pip install pillow pygments kokoro-onnx soundfile playwright   # + ffmpeg y Chromium
mkdir -p video/modelos && cd video/modelos
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.onnx
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin
cd ../.. && python video/render.py
```

Archivos generados: `tutorial.mp4`, `guion.md` (narración con tiempos y capítulos para YouTube) y `subtitulos.srt`.

| Variable en `render.py` | Para qué sirve |
|---|---|
| `VOZ`, `VOZ_JARVIS`, `VELOCIDAD` | Voces (`em_alex`, `ef_dora`, `em_santa`) y velocidad |
| `NARRACION = False` | Video sin voz, para grabar la tuya con `guion.md` |
| `TECLADO = False` | Quita el sonido de teclado y clics |
| `PRONUNCIACION` | Cómo debe leer la voz cada término técnico |
