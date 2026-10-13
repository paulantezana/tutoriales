import os
import psycopg
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_postgres import PostgresChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# --- 1. El cerebro: GPT-6 Luna ---
llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    use_responses_api=True,
)

# --- 2. La búsqueda: Qdrant + embeddings de Ollama ---
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

# --- 3. La memoria: PostgreSQL ---
conn = psycopg.connect(os.getenv("PG_URL"), autocommit=True)
TABLA = "chat_history"
PostgresChatMessageHistory.create_tables(conn, TABLA)

def obtener_historial(session_id: str):
    return PostgresChatMessageHistory(TABLA, session_id, sync_connection=conn)

# --- 4. La personalidad de JARVIS ---
SISTEMA = """Eres JARVIS, un asistente personal inteligente y amable.
Responde en español, en máximo 3 oraciones,
porque tus respuestas se leerán en voz alta.
Usa la información personal del contexto cuando sea útil.
Si no sabes algo, dilo con honestidad.

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

# --- 5. Preguntar a JARVIS (con memoria) ---
def preguntar_a_jarvis(pregunta: str, hilo: str) -> str:
    historial = obtener_historial(hilo)
    respuesta = cadena.invoke({
        "question": pregunta,
        "history": historial.messages[-10:],  # los últimos 10 mensajes
    })
    historial.add_messages([HumanMessage(pregunta), AIMessage(respuesta)])
    return respuesta
