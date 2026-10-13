# Asistente IA con GptLuna + LangChain + Qdrant + Ollama + PostgreSQL

Chat por consola con **RAG** (responde usando tus documentos) y **memoria por hilo**.

| Pieza | Rol |
|---|---|
| GptLuna | LLM (API compatible con OpenAI, vía `ChatOpenAI` + `base_url`) |
| Ollama (`nomic-embed-text`) | Genera los embeddings |
| Qdrant | Base de datos vectorial |
| PostgreSQL | Historial de cada hilo de chat (`chat_history`) |
| LangChain | Une todo |

## Ejecutar el proyecto (`codigo/`)

```bash
cd codigo
docker compose up -d
docker compose exec ollama ollama pull nomic-embed-text

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # pon tu URL, API key y modelo de GptLuna

python ingest.py            # carga docs/*.txt en Qdrant
python app.py               # Enter = hilo nuevo; pega un ID para retomar un hilo
```

> Revisa en el panel de GptLuna la URL base y el nombre del modelo exactos;
> los de `.env.example` son de ejemplo.

## Video tutorial (`video/`)

Clase de unos 19 minutos para principiantes, **narrada en español**, que simula a una persona programando en **VS Code**: explorador de archivos, pestañas, autocompletado, algún error de tipeo corregido, `Ctrl + S`, terminal integrada, mouse y sonido de teclado. Cada bloque de código se selecciona y se explica con una nota en pantalla.

- `tutorial.mp4`: video 1080p con narración y subtítulos incrustados.
- `guion.md`: guion con tiempos (por si prefieres grabar tu propia voz), más los capítulos para la descripción de YouTube.
- `subtitulos.srt`: subtítulos para subir a YouTube.
- `render.py`: genera todo lo anterior. Lee el código desde `codigo/`, así que si cambias el código vuelves a renderizar.

### La voz

La narración se genera en tu PC, sin internet, con [Kokoro](https://github.com/thewh1teagle/kokoro-onnx) (voces en español: `em_alex`, `ef_dora`, `em_santa`). Descarga el modelo y las voces en `video/modelos/`:

```bash
mkdir -p video/modelos && cd video/modelos
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.onnx
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin
```

La pronunciación de los términos técnicos (`ingest.py`, `PostgreSQL`, `LangChain`...) se ajusta en la lista `PRONUNCIACION` de `render.py`. Solo cambia el audio; los subtítulos no se modifican.

### Generar el video

```bash
pip install pillow pygments kokoro-onnx soundfile   # y ffmpeg instalado
python video/render.py                # usa todos los núcleos de la CPU
python video/render.py --preview 15   # una captura PNG cada 15 segundos
```

Opciones al inicio de `render.py`:

| Variable | Para qué sirve |
|---|---|
| `CANAL`, `CURSO`, `CLASE`, `MARCA`, `MARCA2` | Nombre y colores de tu canal |
| `VOZ`, `VELOCIDAD` | Voz de la narración y su velocidad |
| `NARRACION = False` | Video sin voz, para grabar la tuya con `guion.md` |
| `TECLADO = False` | Quita el sonido de teclado y clics |
| `SUBTITULOS = False` | Quita los subtítulos incrustados |
