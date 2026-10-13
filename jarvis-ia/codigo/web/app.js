// Cada navegador tiene su propio hilo de conversación (se guarda en el navegador)
const hilo = localStorage.getItem("hilo") || crypto.randomUUID();
localStorage.setItem("hilo", hilo);

const chat = document.querySelector("#chat");
const form = document.querySelector("#form");
const texto = document.querySelector("#texto");
const orbe = document.querySelector("#orbe");
const estado = document.querySelector("#estado");
const mic = document.querySelector("#mic");

function cambiarEstado(nombre, etiqueta) {
  orbe.dataset.estado = nombre;
  estado.textContent = etiqueta;
}

function agregarMensaje(quien, contenido) {
  const div = document.createElement("div");
  div.className = `mensaje ${quien}`;
  div.textContent = contenido;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

// JARVIS lee su respuesta en voz alta
function hablar(respuesta) {
  const voz = new SpeechSynthesisUtterance(respuesta);
  voz.lang = "es-ES";
  voz.onend = voz.onerror = () => cambiarEstado("listo", "En línea");
  cambiarEstado("hablando", "Hablando");
  speechSynthesis.speak(voz);
}

async function preguntar(pregunta) {
  agregarMensaje("tu", pregunta);
  cambiarEstado("pensando", "Pensando");
  try {
    const r = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto: pregunta, hilo }),
    });
    const datos = await r.json();
    agregarMensaje("jarvis", datos.respuesta);
    hablar(datos.respuesta);
  } catch (error) {
    agregarMensaje("jarvis", "Lo siento, no pude conectarme con el servidor.");
    cambiarEstado("listo", "En línea");
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const pregunta = texto.value.trim();
  if (!pregunta) return;
  texto.value = "";
  preguntar(pregunta);
});

// Hablarle a JARVIS con el micrófono (Chrome y Edge)
const Reconocimiento = window.SpeechRecognition || window.webkitSpeechRecognition;
if (Reconocimiento) {
  const oido = new Reconocimiento();
  oido.lang = "es-ES";
  oido.onresult = (e) => preguntar(e.results[0][0].transcript);
  oido.onend = () => {
    if (orbe.dataset.estado === "escuchando") cambiarEstado("listo", "En línea");
  };
  mic.addEventListener("click", () => {
    cambiarEstado("escuchando", "Escuchando");
    oido.start();
  });
} else {
  mic.hidden = true;
}
