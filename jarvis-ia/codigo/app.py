from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from asistente import preguntar_a_jarvis

app = FastAPI(title="JARVIS")

class Mensaje(BaseModel):
    texto: str
    hilo: str

@app.post("/api/chat")
def chat(mensaje: Mensaje):
    respuesta = preguntar_a_jarvis(mensaje.texto, mensaje.hilo)
    return {"respuesta": respuesta}

# La página web (carpeta web/)
app.mount("/", StaticFiles(directory="web", html=True), name="web")
