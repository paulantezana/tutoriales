/* Réplica de la app YARBYS en cada etapa del curso, manejada por eventos en tiempo virtual.
   render.py escribe los eventos en _demos/<id>.js y llama a seek(t) en cada fotograma.
   Temas: "contador" (la app de ejemplo de Flutter), "basico" (Material 3 sin tema propio)
   y "final" (tema oscuro de tema.dart con el núcleo de widgets/nucleo.dart). */
const P = new URLSearchParams(location.search);
const ID = P.get("id");
const W_S = 468, H_S = 968, DP = 468 / 412;   // la pantalla mide 412 dp de ancho
const I = (n, tam = 24, color = "currentColor") => `<span class="i" style="width:${tam}px;height:${tam}px;color:${color}">${ICONOS[n] || ""}</span>`;
const ease = (x) => 1 - Math.pow(1 - Math.max(0, Math.min(1, x)), 3);
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
let EV = [];

// Colores de cada tema
const TEMAS = {
  contador: { bg: "#fdf7ff", on: "#1d1b20", var: "#49454f", barra: "#cfbcff", primary: "#65558f", cont: "#e9ddff", onCont: "#22005d", teclado: "claro" },
  basico: { bg: "#fef7ff", on: "#1d1b20", var: "#49454f", barra: "#fef7ff", primary: "#6750a4", cont: "#eaddff", onCont: "#4f378b", track: "#e6e0e9", gris: "#9e9e9e", teclado: "claro" },
  final: { bg: "#0f1418", on: "#ffffff", var: "#c4c9cc", barra: "#0f1418", primary: "#007bdf", sup: "#1f272e", celeste: "#00cbff", dorado: "#fba905", suave: "#8a9aa8", cont: "#1f3a52", onCont: "#cfe6ff", teclado: "oscuro" },
};

// ------------------------------------------------------------------ estado en el tiempo t
function estadoEn(t) {
  const s = {
    tema: "basico", etapa: 3, debug: true, avion: false,
    pantalla: "chat", anterior: null, pantallaT0: -99, dir: 1,
    contTitulo: "Flutter Demo Home Page", contador: 0,
    aviso: "Necesito descargar mis modelos de IA. Usa Wi-Fi.", progreso: null, ocupado: false, prog: null,
    campo: "", foco: false, msgs: [], estado: "reposo",
    docs: [], aprendiendo: false, selector: false, selectorT0: -99,
    toque: null, toqueT0: -99, notas: [], kicker: ["smartphone", ""], titulo: "",
  };
  for (const [te, tipo, ...a] of EV) {
    if (te > t) break;
    switch (tipo) {
      case "tema": s.tema = a[0]; break;
      case "etapa": s.etapa = a[0]; break;
      case "debug": s.debug = a[0]; break;
      case "avion": s.avion = a[0]; break;
      case "pantalla": s.anterior = s.pantalla; s.pantalla = a[0]; s.dir = a[1] || 1; s.pantallaT0 = te; break;
      case "contador_titulo": s.contTitulo = a[0]; break;
      case "contador": s.contador = a[0]; break;
      case "inicio": Object.assign(s, a[0]); break;
      case "progreso": { const [desde, hasta, dur] = a; s.progreso = desde + (hasta - desde) * Math.min(1, Math.max(0, (t - te) / dur)); break; }
      case "campo": s.campo = a[0]; break;
      case "foco": s.foco = a[0]; break;
      case "estado": s.estado = a[0]; break;
      case "msg": s.msgs.push({ rol: a[0], texto: a[1], fuentes: a[2] || [] }); break;
      case "pendiente": s.msgs.push({ rol: "y", texto: "", fuentes: [] }); break;
      case "stream": {
        const [texto, dur, fuentes] = a;
        const k = Math.min(1, (t - te) / dur);
        let n = Math.round(texto.length * k);
        if (n < texto.length) { const sp = texto.indexOf(" ", n); n = sp < 0 ? texto.length : sp; }
        s.msgs[s.msgs.length - 1] = { rol: "y", texto: texto.slice(0, n), fuentes: fuentes || [] };
        break;
      }
      case "cargar_chat": s.msgs = a[0].map(([rol, texto, fuentes]) => ({ rol, texto, fuentes: fuentes || [] })); break;
      case "limpiar_chat": s.msgs = []; break;
      case "docs": s.docs = a[0]; break;
      case "aprendiendo": s.aprendiendo = a[0]; break;
      case "selector": s.selector = a[0]; s.selectorT0 = te; break;
      case "toque": s.toque = a; s.toqueT0 = te; break;
      case "titulo": s.kicker = a[0]; s.titulo = a[1]; s.notas = []; break;
      case "nota": s.notas.push({ icono: a[0], texto: a[1], color: a[2], t0: te }); break;
    }
  }
  return s;
}

// El núcleo gira según el estado (como _velocidad() en nucleo.dart)
const VEL = { reposo: 0.6, escuchando: 1.5, pensando: 4.0, hablando: 1.5 };
function giroEn(t) {
  let g = 0, prev = 0, est = "reposo";
  for (const [te, tipo, ...a] of EV) {
    if (te > t) break;
    if (tipo !== "estado") continue;
    g += (te - prev) * VEL[est];
    prev = te; est = a[0];
  }
  return g + (t - prev) * VEL[est];
}

// ------------------------------------------------------------------ núcleo (port de widgets/nucleo.dart)
function nucleo(tam, s, t) {
  const c = document.createElement("canvas");
  c.width = c.height = Math.round(tam * 2);
  c.style.cssText = `width:${tam}px;height:${tam}px;display:block`;
  const ctx = c.getContext("2d");
  ctx.scale(2, 2);
  const T = TEMAS.final;
  const color = s.estado === "pensando" ? T.dorado : T.celeste;
  const r = tam / 2, giro = giroEn(t);
  ctx.translate(r, r);
  const linea = (g) => { ctx.strokeStyle = color; ctx.lineWidth = g * DP; ctx.lineCap = "round"; };
  ctx.beginPath(); linea(2); ctx.arc(0, 0, r * 0.95, 0, Math.PI * 2); ctx.stroke();
  linea(8);
  ctx.beginPath(); ctx.arc(0, 0, r * 0.8, giro, giro + Math.PI * 0.7); ctx.stroke();
  ctx.beginPath(); ctx.arc(0, 0, r * 0.8, giro + Math.PI, giro + Math.PI * 1.7); ctx.stroke();
  linea(3);
  ctx.beginPath(); ctx.arc(0, 0, r * 0.64, -giro * 1.5, -giro * 1.5 + Math.PI * 1.2); ctx.stroke();
  const activo = s.estado === "escuchando" || s.estado === "hablando";
  const radio = r * (0.42 + (activo ? 0.04 * Math.sin(t * 8) : 0));
  ctx.fillStyle = color + "28"; ctx.beginPath(); ctx.arc(0, 0, radio, 0, Math.PI * 2); ctx.fill();
  linea(2); ctx.beginPath(); ctx.arc(0, 0, radio, 0, Math.PI * 2); ctx.stroke();
  return c;
}

// ------------------------------------------------------------------ piezas
function appbar(T, titulo, acciones = "", atras = false) {
  return `<div class="appbar" style="background:${T.barra};color:${T.on}">
    ${atras ? `<span class="btn-i atras" id="atras">${I("arrow-left", 26)}</span>` : ""}
    <span class="tit">${titulo}</span>${acciones}</div>`;
}
function accion(id, icono, activa = true) {
  return `<span class="btn-i${activa ? "" : " off"}" id="${id}">${I(icono, 26)}</span>`;
}
function teclado(T) {
  const claro = T.teclado === "claro";
  const fondo = claro ? "#e8eaed" : "#202124", tecla = claro ? "#ffffff" : "#3c4043", txt = claro ? "#202124" : "#e8eaed";
  const fila = (letras) => `<div class="fila">${letras.split("").map((l) => `<span class="k" style="background:${tecla};color:${txt}">${l}</span>`).join("")}</div>`;
  return `<div id="teclado" style="background:${fondo}">${fila("qwertyuiop")}${fila("asdfghjklñ")}
    <div class="fila"><span class="k esp" style="background:${claro ? "#d2d5db" : "#5f6368"};color:${txt}">${I("arrow-up-from-line", 20)}</span>${"zxcvbnm".split("").map((l) => `<span class="k" style="background:${tecla};color:${txt}">${l}</span>`).join("")}<span class="k esp" style="background:${claro ? "#d2d5db" : "#5f6368"};color:${txt}">⌫</span></div>
    <div class="fila"><span class="k esp" style="background:${claro ? "#d2d5db" : "#5f6368"};color:${txt};font-size:15px">?123</span><span class="k" style="background:${tecla};color:${txt}">,</span><span class="k ancha" style="background:${tecla};color:${txt};font-size:14px">Español</span><span class="k" style="background:${tecla};color:${txt}">.</span><span class="k esp" id="tecla-enviar" style="background:${claro ? "#0b57d0" : "#a8c7fa"};color:${claro ? "#fff" : "#062e6f"}">${I("send", 22)}</span></div></div>`;
}

// ------------------------------------------------------------------ pantallas
function pContador(s, T) {
  return `${appbar(T, esc(s.contTitulo))}
    <div class="centro" style="top:124px;color:${T.on}"><div style="font:400 18px Roboto">You have pushed the button this many times:</div>
    <div style="font:400 40px Roboto;margin-top:6px">${s.contador}</div></div>
    <span class="fab cuadrado" id="fab" style="background:${T.cont};color:${T.onCont}">${I("plus", 30)}</span>`;
}
function pConsola(s, T) {
  return `<div class="centro" style="color:${T.on};font:400 17px Roboto">Mira la consola</div>`;
}
function pInicio(s, T) {
  const final = s.tema === "final";
  const nuc = final ? `<div id="nucleo-inicio" style="margin-bottom:${32 * DP}px"></div>` : "";
  const prog = s.progreso !== null
    ? `<div class="progreso" style="background:${final ? "#1f3a52" : T.track};margin-top:${16 * DP}px"><span style="width:${(s.progreso * 100).toFixed(1)}%;background:${T.primary}"></span></div>` : "";
  const boton = s.ocupado ? "" : `<span class="filled" id="btn-descargar" style="background:${T.primary};color:#fff">Descargar modelos</span>`;
  return `<div class="centro" style="color:${T.on}">${nuc}<div style="font:400 17px/1.45 Roboto">${esc(s.aviso)}</div>${prog}${boton}</div>`;
}
function pChat(s, T, t) {
  const final = s.tema === "final";
  const libre = s.estado === "reposo";
  let acciones = "";
  if (s.etapa >= 6) acciones += accion("accion-docs", "file-text");
  if (s.etapa >= 4) acciones += accion("accion-nueva", "message-square-plus", libre);
  const tecl = s.foco ? 300 : 0;
  const baseEntrada = tecl + 16;
  const altoEntrada = 60;
  // mensajes
  let msgs;
  if (final) {
    msgs = s.msgs.map((m) => {
      const u = m.rol === "u";
      const f = m.fuentes.length ? `<div class="fuente" style="color:${T.suave}">Fuente: ${m.fuentes.join(", ")}</div>` : "";
      return `<div class="burbuja ${u ? "u" : "y"}" style="background:${u ? T.primary : T.sup};color:#fff">${m.texto ? esc(m.texto) : "..."}${f}</div>`;
    }).join("");
  } else {
    msgs = s.msgs.map((m) => {
      const f = m.fuentes.length ? `<div class="fuente" style="color:${T.gris}">Fuente: ${m.fuentes.join(", ")}</div>` : "";
      return `<div class="linea-msg" style="color:${T.on}">${m.rol === "u" ? "Tú" : "YARBYS"}: ${esc(m.texto)}${f}</div>`;
    }).join("");
  }
  const tamNuc = final ? (s.msgs.length ? 140 : 260) * DP : 0;
  const top = 124 + tamNuc;
  const lista = `<div class="lista" style="top:${top}px;bottom:${baseEntrada + altoEntrada + 8}px"><div class="lista-int">${msgs}</div></div>`;
  const cursor = s.foco ? `<span class="cursor" style="background:${T.primary}"></span>` : "";
  const texto = s.campo ? `<span style="color:${T.on}">${esc(s.campo)}</span>` : `<span style="color:${T.var}">Pregúntale a YARBYS</span>`;
  const campo = final
    ? `<span class="campo-lleno" id="campo" style="background:${T.sup}">${s.campo ? texto + cursor : cursor + texto}</span>`
    : `<span class="campo-sub" id="campo" style="border-color:${s.foco ? T.primary : T.var}">${s.campo ? texto + cursor : cursor + texto}</span>`;
  const mic = s.etapa >= 7
    ? `<span class="mic" id="mic" style="background:${libre || s.estado === "escuchando" ? T.primary : (final ? "#2a3138" : "#e6e0e9")};color:${libre || s.estado === "escuchando" ? "#fff" : T.var}">${I(s.estado === "escuchando" ? "square" : "mic", 24)}</span>` : "";
  const entrada = `<div class="entrada" style="bottom:${baseEntrada}px;opacity:${libre || s.estado === "escuchando" || s.campo ? 1 : 0.6}">${campo}${mic}</div>`;
  const nuc = final ? `<div id="nucleo-chat" style="position:absolute;left:${(W_S - tamNuc) / 2}px;top:124px"></div>` : "";
  return `${appbar(T, "YARBYS", acciones)}${nuc}${lista}${entrada}${s.foco ? teclado(T) : ""}`;
}
function pDocumentos(s, T) {
  const items = s.docs.map(([nombre, frag], i) => `<div class="tile" style="color:${T.on}">${I("file-text", 26, T.var)}
      <div class="txt"><div class="t1">${esc(nombre)}</div><div class="t2" style="color:${T.var}">${frag} fragmentos</div></div>
      <span class="btn-i" id="borrar-${i}">${I("trash-2", 24, T.var)}</span></div>`).join("");
  const fab = `<span class="fab" id="fab" style="background:${T.cont};color:${T.onCont};opacity:${s.aprendiendo ? 0.6 : 1}">${I("plus", 26)}${s.aprendiendo ? "Aprendiendo..." : "Agregar archivo"}</span>`;
  const sel = s.selector ? selector(s, T) : "";
  return `${appbar(T, "Mis documentos", "", true)}<div class="cuerpo" style="padding-top:6px">${items}</div>${fab}${sel}`;
}
function selector(s, T) {
  const archivos = [["agenda.txt", "2 KB · 14 oct"], ["perfil.txt", "1 KB · 14 oct"], ["foto.jpg", "3,2 MB · 12 oct"]];
  const filas = archivos.map(([n, d], i) => `<div class="archivo" id="archivo-${i}" style="opacity:${n.endsWith(".jpg") ? 0.38 : 1}">
      ${I("file-text", 30, n.endsWith(".jpg") ? "#5f6368" : "#0b57d0")}<div><div style="color:#1f1f1f">${n}</div><div style="font-size:15px;color:#5f6368">${d}</div></div></div>`).join("");
  return `<div id="selector" style="background:rgba(0,0,0,.45)"><div class="hoja" style="background:#fff">
      <div style="font:400 24px Roboto;color:#1f1f1f">Descargas</div><div style="font:400 15px Roboto;color:#5f6368;margin:6px 0 16px">Elige un archivo</div>${filas}</div></div>`;
}
const PANTALLAS = { contador: pContador, consola: pConsola, inicio: pInicio, chat: pChat, documentos: pDocumentos };

// ------------------------------------------------------------------ pintar el fotograma
const app = document.querySelector("#app");
const toque = document.querySelector("#toque");
function capa(nombre, s, T, t, x, z) {
  return `<div class="capa" data-p="${nombre}" style="background:${T.bg};transform:translateX(${x}px);z-index:${z}">${PANTALLAS[nombre](s, T, t)}</div>`;
}
function pintar(t) {
  const s = estadoEn(t);
  const T = TEMAS[s.tema];
  const oscuro = s.tema === "final";
  document.querySelector("#pantalla").style.background = T.bg;
  const est = document.querySelector("#estado");
  est.style.color = oscuro ? "#e8eef3" : "#1d1b20";
  document.querySelector("#iconos-estado").innerHTML =
    (s.avion ? I("plane", 20) : I("signal", 19) + I("wifi", 20)) + I("battery-full", 24);
  // transición entre pantallas (push / pop)
  const k = ease((t - s.pantallaT0) / 0.35);
  if (s.anterior && s.anterior !== s.pantalla && k < 1) {
    const ida = s.dir > 0;
    app.innerHTML = capa(s.anterior, s, T, t, ida ? -k * W_S * 0.3 : k * W_S, ida ? 1 : 3)
                  + capa(s.pantalla, s, T, t, ida ? (1 - k) * W_S : -(1 - k) * W_S * 0.3, ida ? 3 : 1);
  } else {
    app.innerHTML = capa(s.pantalla, s, T, t, 0, 1);
  }
  // los núcleos (canvas) van dentro de su pantalla
  app.querySelectorAll("#nucleo-chat, #nucleo-inicio").forEach((h) => {
    const tam = h.id === "nucleo-inicio" ? 220 * DP : (s.msgs.length ? 140 : 260) * DP;
    h.appendChild(nucleo(tam, s, t));
  });
  document.querySelector("#debug").style.display = s.debug ? "grid" : "none";
  // toque del dedo: coordenadas o el id de un elemento
  const kt = (t - s.toqueT0) / 0.45;
  if (s.toque && kt >= 0 && kt < 1) {
    let [x, y] = s.toque;
    if (typeof x === "string") {
      const e = document.querySelector("#" + x);
      const p = document.querySelector("#pantalla").getBoundingClientRect();
      if (e) { const r = e.getBoundingClientRect(); x = r.left - p.left + r.width / 2; y = r.top - p.top + r.height / 2; }
      else { x = -100; y = -100; }
    }
    toque.style.display = "block";
    toque.style.left = x + "px"; toque.style.top = y + "px";
    toque.style.opacity = 1 - kt; toque.style.transform = `scale(${0.6 + kt * 0.7})`;
  } else toque.style.display = "none";
  // panel derecho
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
