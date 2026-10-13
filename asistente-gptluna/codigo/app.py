import os
import uuid
import psycopg
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_postgres import PostgresChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# --- LLM: GptLuna (API compatible con OpenAI) ---
llm = ChatOpenAI(
    base_url=os.getenv("GPTLUNA_BASE_URL"),
    api_key=os.getenv("GPTLUNA_API_KEY"),
    model=os.getenv("GPTLUNA_MODEL"),
    temperature=0.3,
)

# --- Retriever: Qdrant + embeddings de Ollama ---
embeddings = OllamaEmbeddings(
    model=os.getenv("EMBED_MODEL"),
    base_url=os.getenv("OLLAMA_URL"),
)
vectorstore = QdrantVectorStore.from_existing_collection(
    embedding=embeddings,
    collection_name=os.getenv("COLLECTION"),
    url=os.getenv("QDRANT_URL"),
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# --- Memoria del hilo en Postgres ---
conn = psycopg.connect(os.getenv("PG_URL"))
TABLA = "chat_history"
PostgresChatMessageHistory.create_tables(conn, TABLA)

def obtener_historial(session_id: str):
    return PostgresChatMessageHistory(TABLA, session_id, sync_connection=conn)

# --- Prompt y cadena RAG ---
SISTEMA = """Eres un asistente amable de atención al cliente.
Responde solo con la información del contexto.
Si no encuentras la respuesta, dilo con honestidad.

Contexto:
{context}"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SISTEMA),
    MessagesPlaceholder("history"),
    ("human", "{question}"),
])

def buscar_contexto(entrada):
    docs = retriever.invoke(entrada["question"])
    return "\n\n".join(d.page_content for d in docs)

cadena = (
    RunnablePassthrough.assign(context=buscar_contexto)
    | prompt
    | llm
    | StrOutputParser()
)

asistente = RunnableWithMessageHistory(
    cadena,
    obtener_historial,
    input_messages_key="question",
    history_messages_key="history",
)

# --- Chat por consola ---
if __name__ == "__main__":
    session_id = input("ID de hilo (Enter = nuevo): ").strip() or str(uuid.uuid4())
    print(f"Hilo: {session_id}  (escribe 'salir' para terminar)\n")
    while True:
        pregunta = input("Tú: ")
        if pregunta.lower() == "salir":
            break
        respuesta = asistente.invoke(
            {"question": pregunta},
            config={"configurable": {"session_id": session_id}},
        )
        print(f"Asistente: {respuesta}\n")
