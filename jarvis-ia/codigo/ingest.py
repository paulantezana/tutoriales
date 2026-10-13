import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore

load_dotenv()

# 1. Leer tus documentos de la carpeta docs
documentos = [
    Document(page_content=p.read_text(encoding="utf-8"), metadata={"source": p.name})
    for p in Path("docs").glob("*.txt")
]

# 2. Dividirlos en fragmentos
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
fragmentos = splitter.split_documents(documentos)

# 3. Embeddings con Ollama (bge-m3)
embeddings = OllamaEmbeddings(
    model=os.getenv("EMBED_MODEL"),
    base_url=os.getenv("OLLAMA_URL"),
)

# 4. Guardar los vectores en Qdrant
QdrantVectorStore.from_documents(
    fragmentos,
    embeddings,
    url=os.getenv("QDRANT_URL"),
    collection_name=os.getenv("COLLECTION"),
)

print(f"Listo: {len(fragmentos)} fragmentos guardados en Qdrant")
