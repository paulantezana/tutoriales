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

Clase de unos 20 minutos para principiantes, que simula a una persona programando en **VS Code**: explorador de archivos, pestañas, autocompletado, algún error de tipeo corregido, `Ctrl + S`, terminal integrada y mouse. Cada bloque de código se selecciona y se explica con una nota en pantalla.

- `tutorial.mp4`: video 1080p con subtítulos incrustados y sin voz (pista de audio silenciosa).
- `guion.md`: guion de narración con tiempos para grabar tu voz, más los capítulos para la descripción de YouTube.
- `subtitulos.srt`: subtítulos para subir a YouTube.
- `render.py`: genera todo lo anterior. Lee el código desde `codigo/`, así que si cambias el código vuelves a renderizar.

Para adaptar el video al estilo de tu canal, edita las variables `CANAL`, `CURSO`, `CLASE`, `MARCA` y `MARCA2` al inicio de `render.py`. Si grabas tu voz, puedes quitar los subtítulos incrustados con `SUBTITULOS = False`.

```bash
pip install pillow pygments     # y ffmpeg instalado
python video/render.py           # usa todos los núcleos de la CPU
python video/render.py --preview 15   # una captura PNG cada 15 segundos
```
