/* Motor de la réplica de la app: estado en el tiempo t a partir de eventos, transiciones entre
   pantallas, toques del dedo y el panel de notas de la derecha. render.py escribe los eventos en
   _demos/<id>.js y llama a seek(t) en cada fotograma.
   Las pantallas (PANTALLAS) y los temas (TEMAS) de cada curso están en app_pantallas.js. */
const P = new URLSearchParams(location.search);
const ID = P.get("id");
const I = (n, tam = 24, color = "currentColor") => `<span class="i" style="width:${tam}px;height:${tam}px;color:${color}">${ICONOS[n] || ""}</span>`;
const ease = (x) => 1 - Math.pow(1 - Math.max(0, Math.min(1, x)), 3);
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
let EV = [];

// Eventos: ["titulo", [icono, kicker], html] · ["nota", icono, texto, color] · ["marco", "celular"|"navegador"]
// ["tema", id] · ["pantalla", id, dir] · ["url", texto] · ["set", clave, valor] · ["datos", {..}] · ["debug", bool]
// ["avion", bool] · ["campo", texto] · ["foco", bool] · ["estado", e] · ["toque", idElemento | x, y]
// Chat: ["msg", rol, texto, fuentes] · ["pendiente"] · ["stream", texto, segundos, fuentes] · ["cargar_chat", [[rol, texto]]] · ["limpiar_chat"]
// Animación de un número: ["animar", clave, desde, hasta, segundos]
function estadoEn(t) {
  const s = { marco: "celular", tema: Object.keys(TEMAS)[0], pantalla: Object.keys(PANTALLAS)[0], anterior: null, pantallaT0: -99, dir: 1,
              url: "localhost:3000", debug: false, avion: false, campo: "", foco: false, estado: "reposo", msgs: [],
              toque: null, toqueT0: -99, notas: [], kicker: ["smartphone", ""], titulo: "", ...(window.ESTADO_INICIAL || {}) };
  for (const [te, tipo, ...a] of EV) {
    if (te > t) break;
    switch (tipo) {
      case "marco": s.marco = a[0]; break;
      case "tema": s.tema = a[0]; break;
      case "pantalla": s.anterior = s.pantalla; s.pantalla = a[0]; s.dir = a[1] || 1; s.pantallaT0 = te; break;
      case "url": s.url = a[0]; break;
      case "set": s[a[0]] = a[1]; break;
      case "datos": Object.assign(s, a[0]); break;
      case "animar": { const [k, desde, hasta, dur] = a; s[k] = desde + (hasta - desde) * Math.min(1, Math.max(0, (t - te) / dur)); break; }
      case "debug": s.debug = a[0]; break;
      case "avion": s.avion = a[0]; break;
      case "campo": s.campo = a[0]; break;
      case "foco": s.foco = a[0]; break;
      case "estado": s.estado = a[0]; break;
      case "msg": s.msgs.push({ rol: a[0], texto: a[1], fuentes: a[2] || [] }); break;
      case "pendiente": s.msgs.push({ rol: "y", texto: "", fuentes: [] }); break;
      case "stream": {
        const [texto, dur, fuentes] = a;
        let n = Math.round(texto.length * Math.min(1, (t - te) / dur));
        if (n < texto.length) { const sp = texto.indexOf(" ", n); n = sp < 0 ? texto.length : sp; }
        s.msgs[s.msgs.length - 1] = { rol: "y", texto: texto.slice(0, n), fuentes: fuentes || [] };
        break;
      }
      case "cargar_chat": s.msgs = a[0].map(([rol, texto, fuentes]) => ({ rol, texto, fuentes: fuentes || [] })); break;
      case "limpiar_chat": s.msgs = []; break;
      case "toque": s.toque = a; s.toqueT0 = te; break;
      case "titulo": s.kicker = a[0]; s.titulo = a[1]; s.notas = []; break;
      case "nota": s.notas.push({ icono: a[0], texto: a[1], color: a[2], t0: te }); break;
    }
  }
  return s;
}

function marcoHTML(s) {
  if (s.marco === "navegador") {
    document.body.classList.add("navegador");
    return `<div id="nav"><div class="barra">${I("arrow-left", 22)}${I("arrow-right", 22, "#80868b")}${I("rotate-cw", 20)}
      <div class="url">${I("lock", 16, "#9aa0a6")}&nbsp;&nbsp;${esc(s.url)}</div></div><div id="pantalla"><div id="app"></div><div id="toque"></div></div></div>`;
  }
  document.body.classList.remove("navegador");
  return `<div id="tel"><div id="pantalla"><div id="isla"></div><div id="estado"><span>9:41</span><span class="der" id="iconos-estado"></span></div>
    <div id="app"></div><div id="debug">DEBUG</div><div id="toque"></div></div></div>`;
}

let marcoActual = null;
function pintar(t) {
  const s = estadoEn(t);
  const T = TEMAS[s.tema];
  if (marcoActual !== s.marco) { document.querySelector("#marco").innerHTML = marcoHTML(s); marcoActual = s.marco; }
  if (s.marco === "navegador") document.querySelector("#nav .url").innerHTML = `${I("lock", 16, "#9aa0a6")}&nbsp;&nbsp;${esc(s.url)}`;
  const pan = document.querySelector("#pantalla");
  pan.style.background = T.bg;
  const est = document.querySelector("#estado");
  if (est) {
    est.style.color = T.oscuro ? "#e8eef3" : "#1d1b20";
    document.querySelector("#iconos-estado").innerHTML = (s.avion ? I("plane", 20) : I("signal", 19) + I("wifi", 20)) + I("battery-full", 24);
  }
  const app = document.querySelector("#app");
  const W_S = pan.clientWidth;
  const capa = (nombre, x, z) => `<div class="capa" style="background:${T.bg};transform:translateX(${x}px);z-index:${z}">${PANTALLAS[nombre](s, T, t)}</div>`;
  const k = ease((t - s.pantallaT0) / 0.35);
  if (s.anterior && s.anterior !== s.pantalla && k < 1) {
    const ida = s.dir > 0;
    app.innerHTML = capa(s.anterior, ida ? -k * W_S * 0.3 : k * W_S, ida ? 1 : 3) + capa(s.pantalla, ida ? (1 - k) * W_S : -(1 - k) * W_S * 0.3, ida ? 3 : 1);
  } else {
    app.innerHTML = capa(s.pantalla, 0, 1);
  }
  if (window.DESPUES_DE_PINTAR) window.DESPUES_DE_PINTAR(s, T, t, app);   // por ejemplo, dibujar en un <canvas>
  const dbg = document.querySelector("#debug");
  if (dbg) dbg.style.display = s.debug ? "grid" : "none";
  const toque = document.querySelector("#toque");
  const kt = (t - s.toqueT0) / 0.45;
  if (s.toque && kt >= 0 && kt < 1) {
    let [x, y] = s.toque;
    if (typeof x === "string") {
      const e = document.querySelector("#" + x);
      const p = pan.getBoundingClientRect();
      if (e) { const r = e.getBoundingClientRect(); x = r.left - p.left + r.width / 2; y = r.top - p.top + r.height / 2; } else { x = y = -100; }
    }
    toque.style.display = "block"; toque.style.left = x + "px"; toque.style.top = y + "px";
    toque.style.opacity = 1 - kt; toque.style.transform = `scale(${0.6 + kt * 0.7})`;
  } else toque.style.display = "none";
  document.querySelector("#kicker").innerHTML = `${I(s.kicker[0], 24)}${s.kicker[1]}`;
  document.querySelector("#titulo").innerHTML = s.titulo;
  document.querySelector("#notas").innerHTML = s.notas.map((n) => {
    const kn = ease((t - n.t0) / 0.5);
    return `<div class="nota" style="opacity:${kn};transform:translateY(${(1 - kn) * 30}px)"><span class="cuadro" style="background:${n.color}26;color:${n.color}">${I(n.icono, 36)}</span><span>${n.texto}</span></div>`;
  }).join("");
}

window.seek = (t) => { pintar(t); return 0; };
const sc = document.createElement("script");
sc.src = `_demos/${ID}.js?v=${P.get("v") || 0}`;
sc.onload = () => {
  EV = (window.DEMO.eventos || []).slice().sort((a, b) => a[0] - b[0]);
  document.fonts.ready.then(() => { pintar(0); window.__listo = true; });
};
document.body.appendChild(sc);
