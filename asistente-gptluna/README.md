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

- `tutorial.mp4`: video 1080p de unos 5 minutos, con subtítulos incrustados y sin voz (pista de audio silenciosa).
- `guion.md`: guion de narración con tiempos, para grabar tu voz encima, más los capítulos para la descripción de YouTube.
- `subtitulos.srt`: subtítulos para subir a YouTube.
- `render.py`: genera todo lo anterior. Lee el código desde `codigo/`, así que si cambias el código, vuelve a renderizar.

```bash
pip install pillow pygments     # y ffmpeg instalado
python video/render.py           # o --preview para ver un PNG por escena
```
