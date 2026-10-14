/* Escenas animadas del video de YARBYS (estilo plano y oscuro, sin degradados).
   Cada escena es una línea de tiempo de GSAP en pausa: el renderizador llama a
   window.seek(t) para cada fotograma.
   Parámetros de la URL: id (escena), dur (segundos), m (inicio de cada frase, en segundos). */

const P = new URLSearchParams(location.search);
const ID = P.get("id");
const DUR = parseFloat(P.get("dur") || "10");
const M = (P.get("m") || "0").split(",").map(Number);
const DATOS = JSON.parse(P.get("d") || "{}");  // datos extra de la escena (por ejemplo, qué modelo)

gsap.registerPlugin(SplitText, DrawSVGPlugin, MotionPathPlugin);
const tl = gsap.timeline({ paused: true });
const esc = document.querySelector("#escena");

const C = { azul: "#007bdf", celeste: "#00cbff", rojo: "#ff3c32", amarillo: "#fba905", verde: "#1fb36a",
            gris: "#53575a", suave: "#b8c0c7", sup: "#33393e", borde: "#41484e", fondo: "#282d31" };

// ------------------------------------------------------------- utilidades
function nuevo(tag, clase, html, padre = esc, estilo = "") {
  const e = document.createElement(tag);
  if (clase) e.className = clase;
  if (html !== undefined && html !== null) e.innerHTML = html;
  if (estilo) e.style.cssText = estilo;
  padre.appendChild(e);
  return e;
}
function ico(nombre, tam = 48, color = "currentColor") {
  return `<span class="icono" style="width:${tam}px;height:${tam}px;color:${color}">${ICONOS[nombre] || ""}</span>`;
}
const m = (i) => (i < M.length ? M[i] : DUR);  // inicio de la frase i

function cabecera(kicker, icono, html, sub) {
  const c = nuevo("div", "cabecera");
  const k = nuevo("div", "kicker", `${ico(icono, 24)}${kicker}`, c);
  const h = nuevo("h1", "titulo", html, c);
  const s = sub ? nuevo("div", "subtitulo", sub, c) : null;
  const split = new SplitText(h, { type: "lines,words", linesClass: "linea-titulo" });
  tl.from(k, { y: 20, opacity: 0, duration: 0.5, ease: "power3.out" }, 0.1);
  tl.from(split.words, { yPercent: 110, duration: 0.8, stagger: 0.05, ease: "power4.out" }, 0.2);
  if (s) tl.from(s, { y: 20, opacity: 0, duration: 0.6, ease: "power3.out" }, 0.6);
  return c;
}
// Formas planas decorativas (como en la portada)
function formas(variante = 0) {
  const sets = [
    [["circ", 1780, 92, 30, C.amarillo], ["cuad", 1700, 190, 26, C.rojo], ["anillo", 1810, 230, 40, C.celeste]],
    [["circ", 1820, 300, 26, C.celeste], ["cuad", 1745, 120, 24, C.amarillo], ["anillo", 1660, 70, 34, C.rojo]],
  ];
  sets[variante % sets.length].forEach(([tipo, x, y, s, c], i) => {
    let est = `position:absolute;left:${x}px;top:${y}px;width:${s}px;height:${s}px;`;
    if (tipo === "circ") est += `border-radius:50%;background:${c}`;
    if (tipo === "cuad") est += `border-radius:7px;background:${c};transform:rotate(18deg)`;
    if (tipo === "anillo") est += `border-radius:50%;border:9px solid ${c}`;
    const f = nuevo("div", "", "", esc, est);
    tl.from(f, { scale: 0, duration: 0.6, ease: "back.out(2)" }, 0.3 + i * 0.1);
    tl.to(f, { y: (i % 2 ? 14 : -14), rotation: tipo === "cuad" ? 60 : 0, duration: DUR, ease: "sine.inOut" }, 0);
  });
}
function salida() {
  tl.to(esc, { opacity: 0, duration: 0.45, ease: "power2.in" }, DUR - 0.45);
}
function pop(elems, t, extra = {}) {
  tl.from(elems, { scale: 0.6, opacity: 0, duration: 0.6, ease: "back.out(1.8)", stagger: 0.08, ...extra }, t);
}
function subir(elems, t, extra = {}) {
  tl.from(elems, { y: 40, opacity: 0, duration: 0.7, ease: "power3.out", stagger: 0.1, ...extra }, t);
}
function aparecer(elems, t, extra = {}) {
  tl.from(elems, { opacity: 0, duration: 0.5, ease: "power1.out", stagger: 0.08, ...extra }, t);
}
function resaltar(elem, t, color = C.amarillo) {
  tl.to(elem, { borderColor: color, scale: 1.04, duration: 0.45, ease: "power2.out" }, t);
}
function normal(elem, t) {
  tl.to(elem, { borderColor: C.borde, scale: 1, duration: 0.45, ease: "power2.out" }, t);
}
function apagar(elem, t, o = 0.35) {
  tl.to(elem, { opacity: o, duration: 0.5 }, t);
}
function svg(w, h, padre = esc, estilo = "") {
  const s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  s.setAttribute("width", w); s.setAttribute("height", h); s.setAttribute("viewBox", `0 0 ${w} ${h}`);
  s.style.cssText = "position:absolute;overflow:visible;" + estilo;
  padre.appendChild(s);
  return s;
}
function trazo(s, d, color = C.borde, ancho = 4, guiones = "") {
  const p = document.createElementNS("http://www.w3.org/2000/svg", "path");
  p.setAttribute("d", d); p.setAttribute("fill", "none"); p.setAttribute("stroke", color);
  p.setAttribute("stroke-width", ancho); p.setAttribute("stroke-linecap", "round"); p.setAttribute("stroke-linejoin", "round");
  if (guiones) p.setAttribute("stroke-dasharray", guiones);
  s.appendChild(p);
  return p;
}
// Flecha que se dibuja de (x1,y1) a (x2,y2) dentro de un svg de pantalla completa
let _lienzo = null;
function lienzo() {
  if (!_lienzo) _lienzo = svg(1920, 1080, esc, "left:0;top:0;pointer-events:none;z-index:1");
  return _lienzo;
}
function flecha(x1, y1, x2, y2, t, color = C.suave, ancho = 4, guiones = "") {
  const s = lienzo();
  const ang = Math.atan2(y2 - y1, x2 - x1);
  const a = 14;
  const p = trazo(s, `M${x1} ${y1} L${x2} ${y2}`, color, ancho, guiones);
  const punta = trazo(s, `M${x2 - a * Math.cos(ang - 0.5)} ${y2 - a * Math.sin(ang - 0.5)} L${x2} ${y2} L${x2 - a * Math.cos(ang + 0.5)} ${y2 - a * Math.sin(ang + 0.5)}`, color, ancho);
  if (guiones) tl.from(p, { opacity: 0, duration: 0.5 }, t);
  else tl.from(p, { drawSVG: 0, duration: 0.6, ease: "power2.inOut" }, t);
  tl.from(punta, { opacity: 0, duration: 0.2 }, t + 0.5);
  return [p, punta];
}
function contador(elem, t, desde, hasta, dur = 1.2, fmt = (v) => Math.round(v)) {
  const o = { v: desde };
  tl.to(o, { v: hasta, duration: dur, ease: "power2.out", onUpdate: () => (elem.textContent = fmt(o.v)) }, t);
  elem.textContent = fmt(desde);
}
function escribir(elem, texto, t, cps = 28) {
  const o = { n: 0 };
  elem.textContent = "";
  tl.to(o, { n: texto.length, duration: texto.length / cps, ease: "none", onUpdate: () => (elem.textContent = texto.slice(0, Math.round(o.n))) }, t);
}
// Tarjeta con ícono de color, título y subtítulo
function tarjeta(x, y, w, h, icono, titulo, sub, color, padre = esc) {
  return nuevo("div", "panel", `
    <div style="display:flex;align-items:center;gap:20px">
      <div class="cuadro-icono" style="width:72px;height:72px;background:${color}26;color:${color}">${ico(icono, 40)}</div>
      <div><div style="font:800 30px 'Open Sans'">${titulo}</div><div style="font:400 23px 'Lato';color:var(--suave);margin-top:4px">${sub}</div></div>
    </div>`, padre, `left:${x}px;top:${y}px;width:${w}px;height:${h}px;padding:0 28px;display:flex;align-items:center`);
}
const formatoMiles = (v) => String(Math.round(v)).replace(/\B(?=(\d{3})+(?!\d))/g, " ");

// Núcleo de YARBYS que gira (usa lib/nucleo.js)
function nucleo(padre, x, y, R, op = {}, velocidad = 1) {
  const tam = R * 2.4;
  const s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  s.setAttribute("width", tam); s.setAttribute("height", tam);
  s.setAttribute("viewBox", `${-tam / 2} ${-tam / 2} ${tam} ${tam}`);
  s.style.cssText = `position:absolute;left:${x - tam / 2}px;top:${y - tam / 2}px;overflow:visible`;
  padre.appendChild(s);
  dibujarNucleo(s, R, op);
  const giros = [["anillo-marcas", 2], ["anillo-segmentos", -6], ["anillo-puntos", 10], ["anillo-espectro", 1.5],
                 ["anillo-arcos", -12], ["anillo-luna", 20], ["anillo-interior", -4]];
  const gs = giros.map(([id, v]) => [s.querySelector("#" + id), v]);
  const o = { t: 0 };
  tl.to(o, { t: DUR, duration: DUR, ease: "none",
    onUpdate: () => gs.forEach(([g, v]) => g.setAttribute("transform", `rotate(${(o.t * v * velocidad * 2).toFixed(2)})`)) }, 0);
  return s;
}
function dibujarAnillos(s, t, dur = 1.4) {
  const partes = s.querySelectorAll("circle, path, line");
  tl.from(partes, { drawSVG: 0, duration: dur, stagger: { amount: 0.8 }, ease: "power2.out" }, t);
}

// Teléfono plano (marco + pantalla)
function telefono(padre, x, y, w, h, estilo = "") {
  const t = nuevo("div", "", "", padre, `position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;border-radius:${w * 0.14}px;background:#15181b;padding:${w * 0.035}px;${estilo}`);
  const p = nuevo("div", "", "", t, `width:100%;height:100%;border-radius:${w * 0.11}px;background:#0f1418;overflow:hidden;position:relative`);
  nuevo("div", "", "", p, `position:absolute;left:50%;top:${w * 0.03}px;width:${w * 0.26}px;height:${w * 0.07}px;border-radius:99px;background:#000;transform:translateX(-50%)`);
  return [t, p];
}

// ------------------------------------------------------------- escenas
const ESCENAS = {};

// La portada, animada
ESCENAS.intro = () => {
  esc.innerHTML = `
    <div class="forma circulo-grande"></div>
    <div class="forma punto-amarillo"></div>
    <div class="forma cuadro-rojo"></div>
    <div class="forma anillo-celeste"></div>
    <div class="forma puntos"></div>
    <div class="izq">
      <span class="kicker" id="k"></span>
      <h1 class="t1">Crea tu propio</h1>
      <div class="t2">YARBYS</div>
      <div class="t3"><span id="cien" style="position:relative;display:inline-block;z-index:0">100%<span id="subraya" style="position:absolute;left:-6px;right:-6px;bottom:6px;height:34%;background:var(--enfasis);z-index:-1;border-radius:6px"></span></span> en tu celular</div>
      <div class="sub">Un asistente de IA que funciona <b>sin internet</b>: lee tus documentos, recuerda tus conversaciones y te habla.</div>
      <div class="chips" id="chips"></div>
    </div>
    <div class="forma barra-azul"></div>
    <div class="insignias" id="insignias"></div>
    <div class="celular">
      <div class="pantalla">
        <div class="isla"></div>
        <div class="estado-tel"><span>9:41</span><span id="iconos-tel"></span></div>
        <div class="app-top"><h3>YARBYS</h3><span class="modo" id="modo"></span></div>
        <svg id="nucleo-app" width="320" height="320" viewBox="-160 -160 320 320"></svg>
        <div class="estado-app">MODO LOCAL · GEMMA 4</div>
        <div class="chat">
          <div class="msg tu" id="m1">¿Qué tengo el miércoles?</div>
          <div class="msg ia" id="m2">Tienes que entregar el proyecto de la tienda online antes de las 6 de la tarde.
            <div class="fuente-doc" id="fuente"></div></div>
        </div>
        <div class="entrada"><div class="campo">Habla con YARBYS...</div><div class="mic" id="mic"></div></div>
      </div>
    </div>`;
  const icoS = (n, c = "") => `<span class="icono" style="${c ? "color:" + c : ""}">${ICONOS[n] || ""}</span>`;
  document.querySelector("#k").innerHTML = icoS("smartphone") + "Curso · IA en tu celular";
  const chips = [["si_flutter", "Flutter", "#02569b"], ["brain", "Gemma 4", C.amarillo], ["binary", "EmbeddingGemma", C.celeste],
                 ["si_qdrant", "Qdrant Edge", C.rojo], ["si_sqlite", "SQLite", C.azul]];
  document.querySelector("#chips").innerHTML = chips.map(([i, t, c]) => `<span class="chip">${icoS(i, c)}${t}</span>`).join("");
  document.querySelector("#insignias").innerHTML =
    `<span>${icoS("si_android")}Android</span><span>${icoS("si_apple")}iPhone</span><span>${icoS("wifi-off")}Sin internet</span><span>${icoS("code")}Código en GitHub</span>`;
  document.querySelector("#iconos-tel").innerHTML = icoS("plane") + " " + icoS("battery-charging");
  document.querySelector("#modo").innerHTML = icoS("plane") + "Sin internet";
  document.querySelector("#fuente").innerHTML = icoS("file-text") + "agenda.txt";
  document.querySelector("#mic").innerHTML = icoS("mic");

  // núcleo de la app, con sus anillos girando
  const sv = document.querySelector("#nucleo-app");
  dibujarNucleo(sv, 132, { nombre: "YARBYS", estado: "EN LÍNEA" });
  const giros = [["anillo-marcas", 2], ["anillo-segmentos", -6], ["anillo-puntos", 10], ["anillo-espectro", 1.5],
                 ["anillo-arcos", -12], ["anillo-luna", 20], ["anillo-interior", -4]];
  const gs = giros.map(([id, v]) => [sv.querySelector("#" + id), v]);
  const o = { t: 0 };
  tl.to(o, { t: DUR, duration: DUR, ease: "none", onUpdate: () => gs.forEach(([g, v]) => g.setAttribute("transform", `rotate(${o.t * v * 2})`)) }, 0);

  tl.from(".circulo-grande", { scale: 0, duration: 1.0, ease: "back.out(1.4)" }, 0.05);
  tl.from([".punto-amarillo", ".cuadro-rojo", ".anillo-celeste"], { scale: 0, duration: 0.6, ease: "back.out(2)", stagger: 0.12 }, 0.5);
  tl.from(".puntos", { opacity: 0, duration: 0.8 }, 0.8);
  tl.to(".cuadro-rojo", { rotation: 120, duration: DUR, ease: "none" }, 0);
  tl.to(".punto-amarillo", { y: 30, duration: DUR / 2, yoyo: true, repeat: 1, ease: "sine.inOut" }, 0);
  tl.from(".celular", { x: 220, opacity: 0, duration: 1.0, ease: "power3.out" }, 0.4);
  dibujarAnillos(sv, 0.9, 1.6);
  tl.from("#k", { y: 20, opacity: 0, duration: 0.5, ease: "power3.out" }, 0.3);
  const t1 = new SplitText(".t1", { type: "words" });
  tl.from(t1.words, { yPercent: 100, opacity: 0, duration: 0.7, stagger: 0.08, ease: "power4.out" }, 0.45);
  const t2 = new SplitText(".t2", { type: "chars" });
  tl.from(t2.chars, { yPercent: 70, opacity: 0, rotationX: -90, duration: 0.8, stagger: 0.05, ease: "back.out(1.7)" }, 0.7);
  tl.from(".t3", { y: 30, opacity: 0, duration: 0.6, ease: "power3.out" }, 1.15);
  tl.from("#subraya", { scaleX: 0, transformOrigin: "left center", duration: 0.6, ease: "power3.out" }, 1.6);
  tl.from(".sub", { y: 20, opacity: 0, duration: 0.6, ease: "power3.out" }, 1.8);
  tl.from(".barra-azul", { scaleX: 0, transformOrigin: "left center", duration: 0.6 }, 2.0);
  pop(document.querySelectorAll(".chip"), Math.max(2.2, m(1)), { stagger: 0.1 });
  subir(document.querySelectorAll(".insignias span"), Math.max(2.8, m(2)), { stagger: 0.12 });
  pop("#m1", Math.max(2.6, m(1) + 0.4));
  pop("#m2", Math.max(3.4, m(1) + 1.6));
  tl.to("#mic", { scale: 1.12, duration: 0.5, yoyo: true, repeat: 3, ease: "sine.inOut" }, Math.max(3.6, m(2)));
  salida();
};

ESCENAS.ia_celular = () => {
  formas(0);
  cabecera("Teoría · Parte 1", "smartphone", "¿IA <span class='acento'>dentro</span> del celular?");
  // Izquierda: en la nube
  const izq = nuevo("div", "panel", "", esc, "left:140px;top:320px;width:790px;height:480px;padding:30px 36px");
  nuevo("div", "panel-titulo", `${ico("cloud", 34, C.suave)}En la nube <span style="font:400 24px Lato;color:var(--suave);margin-left:6px">ChatGPT, Claude...</span>`, izq);
  const [tel1] = telefono(izq, 50, 120, 120, 230);
  nuevo("div", "", ico("message-circle", 44, C.celeste), tel1.firstChild, "position:absolute;left:0;right:0;top:80px;text-align:center");
  const centro = nuevo("div", "", "", izq, "position:absolute;left:520px;top:110px;display:flex;gap:10px;flex-direction:column");
  for (let i = 0; i < 3; i++) nuevo("div", "", `${ico("server", 46, C.suave)}<span style="flex:1;height:8px;border-radius:4px;background:${C.borde}"></span><span style="width:12px;height:12px;border-radius:50%;background:${i === 1 ? C.verde : C.amarillo}"></span>`, centro, "display:flex;align-items:center;gap:14px;width:210px;padding:10px 16px;border-radius:14px;background:#2b3136;border:2px solid var(--borde)");
  nuevo("div", "etiqueta", "Centro de datos", izq, "position:absolute;left:520px;top:342px;width:210px;text-align:center");
  const camino = svg(360, 200, izq, "left:170px;top:140px");
  const ruta = trazo(camino, "M0 90 C 120 0, 240 0, 350 90", C.borde, 4, "10 12");
  nuevo("div", "etiqueta", "internet", izq, "position:absolute;left:300px;top:118px");
  const paquete = nuevo("div", "", "", izq, `position:absolute;left:0;top:0;width:22px;height:22px;border-radius:50%;background:${C.celeste}`);
  const vuelta = nuevo("div", "", "", izq, `position:absolute;left:0;top:0;width:22px;height:22px;border-radius:50%;background:${C.amarillo}`);
  const ida = trazo(camino, "M0 90 C 120 0, 240 0, 350 90", "transparent", 1);
  const regreso = trazo(camino, "M350 110 C 240 200, 120 200, 0 110", "transparent", 1);
  const regresoVisible = trazo(camino, "M350 110 C 240 200, 120 200, 0 110", C.borde, 4, "10 12");
  nuevo("div", "", "Tu pregunta viaja hasta computadoras gigantes y la respuesta regresa.", izq, "position:absolute;left:36px;right:36px;top:396px;font:400 24px Lato;color:var(--suave)");
  subir(izq, 0.6);
  for (let k = 0; k < 3; k++) {
    const t0 = 1.0 + k * 2.6;
    tl.fromTo(paquete, { opacity: 1 }, { motionPath: { path: ida, align: ida, alignOrigin: [0.5, 0.5] }, duration: 1.1, ease: "power1.inOut", immediateRender: false }, t0);
    tl.set(paquete, { opacity: 0 }, t0 + 1.15);
    tl.fromTo(vuelta, { opacity: 1 }, { motionPath: { path: regreso, align: regreso, alignOrigin: [0.5, 0.5] }, duration: 1.1, ease: "power1.inOut", immediateRender: false }, t0 + 1.3);
    tl.set(vuelta, { opacity: 0 }, t0 + 2.45);
  }
  tl.set([paquete, vuelta], { opacity: 0 }, 0);

  // Derecha: en el celular
  const der = nuevo("div", "panel", "", esc, `left:990px;top:320px;width:790px;height:480px;padding:30px 36px;border-color:${C.celeste}`);
  nuevo("div", "panel-titulo", `${ico("smartphone", 34, C.celeste)}En tu celular <span style="font:400 24px Lato;color:var(--suave);margin-left:6px">YARBYS</span>`, der);
  const [tel2, pan2] = telefono(der, 50, 100, 170, 340);
  nucleo(pan2, 74, 150, 60, { brillo: false, nombre: "", estado: "" });
  const notas = nuevo("div", "", "", der, "position:absolute;left:270px;top:120px;display:grid;gap:18px");
  const ns = [["hard-drive", "El modelo es un archivo dentro del teléfono"], ["cpu", "El procesador del celular hace todo el trabajo"], ["wifi-off", "No necesita internet"]]
    .map(([i, t]) => nuevo("div", "fila", `${ico(i, 34, C.celeste)}<span style="font:400 25px Lato">${t}</span>`, notas, "gap:16px"));
  subir(der, m(1));
  subir(ns, m(1) + 0.6, { stagger: 0.35 });

  // Ventajas y desventajas
  const filaV = nuevo("div", "", "", esc, "position:absolute;left:140px;top:830px;display:flex;gap:16px");
  const vs = [["lock", "Privacidad total"], ["wifi-off", "Funciona sin internet"], ["coins", "Gratis por pregunta"], ["zap", "Sin esperar a un servidor"]]
    .map(([i, t]) => nuevo("div", "pastilla", `${ico(i, 30, C.verde)}${t}`, filaV));
  pop(vs, m(2), { stagger: 0.25 });
  const filaD = nuevo("div", "", "", esc, "position:absolute;left:140px;top:922px;display:flex;gap:16px");
  const ds = [["brain", "Modelo más pequeño"], ["hard-drive", "Ocupa espacio"], ["memory-stick", "Usa la RAM"], ["battery-charging", "Gasta batería"]]
    .map(([i, t]) => nuevo("div", "pastilla", `${ico(i, 30, C.amarillo)}${t}`, filaD));
  pop(ds, m(3), { stagger: 0.25 });
  salida();
};

ESCENAS.piezas = () => {
  formas(1);
  cabecera("El plan", "layers", "Las <span class='acento'>5 piezas</span> de YARBYS");
  const marco = nuevo("div", "", "", esc, `position:absolute;left:120px;top:330px;width:1680px;height:640px;border:3px dashed ${C.borde};border-radius:40px`);
  const rotulo = nuevo("div", "pastilla", `${ico("smartphone", 28, C.celeste)}Todo vive dentro del celular`, esc, "position:absolute;left:170px;top:306px;padding:8px 20px;font-size:22px;background:var(--fondo)");
  aparecer(marco, 0.6);
  pop(rotulo, 0.9);
  const piezas = [
    ["brain", "Cerebro", "Gemma 4", "Entiende y responde", C.amarillo],
    ["binary", "Traductor", "EmbeddingGemma", "Convierte texto en números", C.celeste],
    ["scan-search", "Buscador", "Qdrant Edge", "Encuentra tu información", C.rojo],
    ["history", "Memoria", "SQLite", "Recuerda las charlas", C.azul],
    ["audio-lines", "Voz", "Motores del celular", "Escucha y habla", C.verde],
  ];
  const cards = piezas.map(([i, t, s, d, c], k) => nuevo("div", "panel", `
      <div class="cuadro-icono" style="width:92px;height:92px;background:${c}26;color:${c}">${ico(i, 52)}</div>
      <div style="font:800 34px 'Open Sans';margin-top:26px">${t}</div>
      <div style="font:700 25px Lato;color:${c};margin-top:8px">${s}</div>
      <div style="font:400 23px Lato;color:var(--suave);margin-top:12px;line-height:1.35">${d}</div>`,
    esc, `left:${170 + k * 322}px;top:390px;width:296px;height:340px;padding:34px 28px`));
  subir(cards, 1.0, { stagger: 0.12 });
  [[0, 1], [2, 3], [4]].forEach((grupo, j) => {
    grupo.forEach((k) => resaltar(cards[k], m(j + 1), piezas[k][4]));
    grupo.forEach((k) => normal(cards[k], (j < 2 ? m(j + 2) : DUR)));
  });
  const fl = nuevo("div", "panel", `${ico("si_flutter", 56, "#02569b")}<div><div style="font:800 32px 'Open Sans'">Flutter · el cuerpo de la app</div><div style="font:400 23px Lato;color:var(--suave);margin-top:4px">Une las piezas · un solo código para Android y iPhone</div></div>`,
    esc, "left:170px;top:770px;width:1580px;height:150px;display:flex;align-items:center;gap:26px;padding:0 40px");
  subir(fl, m(3) + 0.8);
  tl.to(fl, { borderColor: C.celeste, duration: 0.5 }, m(3) + 1.4);
  salida();
};

ESCENAS.llm = () => {
  formas(0);
  cabecera("Teoría · El cerebro", "brain", "¿Qué es un <span class='acento'>LLM</span>?", "Large Language Model · modelo de lenguaje grande");
  // Columna 1: aprendió de mucho texto
  const c1 = nuevo("div", "panel", "", esc, "left:140px;top:370px;width:470px;height:560px;padding:30px");
  nuevo("div", "etiqueta", "1 · Aprendió leyendo", c1);
  const libros = nuevo("div", "", "", c1, "position:absolute;left:30px;right:30px;top:90px;display:grid;grid-template-columns:repeat(5,1fr);gap:14px");
  const ls = [];
  for (let i = 0; i < 15; i++) ls.push(nuevo("div", "", ico(["book-open", "file-text", "messages-square"][i % 3], 40, [C.suave, C.celeste, C.amarillo][i % 3]), libros, "display:grid;place-items:center;height:54px;border-radius:12px;background:#2b3136"));
  const cerebro = nuevo("div", "", ico("brain", 120, C.amarillo), c1, "position:absolute;left:0;right:0;top:340px;display:grid;place-items:center");
  nuevo("div", "", "Muchísimo texto de libros, webs y conversaciones", c1, "position:absolute;left:30px;right:30px;bottom:28px;font:400 23px Lato;color:var(--suave);text-align:center");
  subir(c1, 0.6);
  pop(ls, 0.9, { stagger: 0.04 });
  tl.to(ls, { y: 200, scale: 0.2, opacity: 0, duration: 0.9, stagger: 0.04, ease: "power2.in" }, 2.2);
  pop(cerebro, 2.8);
  tl.to(cerebro, { y: -150, scale: 1.4, duration: 0.8, ease: "power3.inOut" }, 3.4);

  // Columna 2: predice el siguiente token
  const c2 = nuevo("div", "panel", "", esc, "left:650px;top:370px;width:700px;height:560px;padding:30px");
  nuevo("div", "etiqueta", "2 · Predice el siguiente token", c2);
  const frase = nuevo("div", "", "", c2, "position:absolute;left:30px;right:30px;top:90px;display:flex;flex-wrap:wrap;gap:10px");
  const toks = ["Mañana", " tengo", " que", " entregar", " el"].map((t, i) =>
    nuevo("span", "", t.trim(), frase, `padding:8px 14px;border-radius:10px;font:700 28px Lato;background:${[C.azul, C.celeste, C.amarillo, C.rojo, C.verde][i]}2b;border:2px solid ${[C.azul, C.celeste, C.amarillo, C.rojo, C.verde][i]}`));
  const nuevoTok = nuevo("span", "", "proyecto", frase, `padding:8px 14px;border-radius:10px;font:700 28px Lato;background:${C.amarillo};color:#1b1b1b`);
  const opciones = [["proyecto", 62], ["informe", 21], ["trabajo", 11], ["pastel", 1]];
  const lista = nuevo("div", "", "", c2, "position:absolute;left:30px;right:30px;top:230px;display:grid;gap:16px");
  const filas = opciones.map(([t, p], i) => {
    const f = nuevo("div", "fila", `<span style="width:150px;font:700 26px Lato">${t}</span><span style="flex:1;height:26px;border-radius:8px;background:#2b3136;position:relative;overflow:hidden"><span class="b" style="position:absolute;left:0;top:0;bottom:0;width:${p}%;background:${i === 0 ? C.amarillo : C.gris};border-radius:8px"></span></span><span class="mono" style="width:90px;text-align:right;font-size:24px">${p}%</span>`, lista, "gap:16px");
    return f;
  });
  nuevo("div", "", "Escribe token por token, eligiendo el más probable.", c2, "position:absolute;left:30px;right:30px;bottom:28px;font:400 23px Lato;color:var(--suave)");
  subir(c2, m(1));
  pop(toks, m(1) + 0.5, { stagger: 0.15 });
  subir(filas, m(1) + 1.5, { stagger: 0.12 });
  filas.forEach((f) => tl.from(f.querySelector(".b"), { width: 0, duration: 0.8, ease: "power2.out" }, m(1) + 1.8));
  tl.from(nuevoTok, { opacity: 0, scale: 0.4, duration: 0.5, ease: "back.out(2)" }, m(2));
  tl.to(filas.slice(1), { opacity: 0.3, duration: 0.4 }, m(2));
  const mas = ["antes", "de", "las", "6"].map((t) => nuevo("span", "", t, frase, `padding:8px 14px;border-radius:10px;font:700 28px Lato;background:#2b3136;border:2px solid ${C.borde}`));
  pop(mas, m(2) + 1.0, { stagger: 0.35 });

  // Columna 3: parámetros
  const c3 = nuevo("div", "panel", "", esc, "left:1390px;top:370px;width:390px;height:560px;padding:30px");
  nuevo("div", "etiqueta", "3 · Parámetros", c3);
  const puntos = nuevo("div", "", "", c3, "position:absolute;left:30px;right:30px;top:90px;display:grid;grid-template-columns:repeat(12,1fr);gap:7px");
  const ps = [];
  for (let i = 0; i < 96; i++) ps.push(nuevo("span", "", "", puntos, `height:20px;border-radius:5px;background:${[C.celeste, C.azul, C.amarillo, C.gris][(i * 7) % 4]}`));
  const num = nuevo("div", "mono", "0", c3, `position:absolute;left:0;right:0;top:330px;text-align:center;font-size:40px;font-weight:700;color:${C.amarillo}`);
  nuevo("div", "", "números que guardan lo que aprendió", c3, "position:absolute;left:30px;right:30px;top:390px;font:400 23px Lato;color:var(--suave);text-align:center");
  nuevo("div", "", "Más parámetros = más inteligente, pero más pesado", c3, `position:absolute;left:30px;right:30px;bottom:28px;font:700 23px Lato;text-align:center;color:${C.celeste}`);
  subir(c3, m(3));
  pop(ps, m(3) + 0.3, { stagger: { amount: 1.0, from: "random" } });
  contador(num, m(3) + 0.6, 0, 2000000000, 2.2, formatoMiles);
  salida();
};

ESCENAS.tamanos = () => {
  formas(1);
  cabecera("Teoría · Modelos para celular", "cpu", "Modelos que <span class='acento'>caben</span> en tu bolsillo");
  // Comparación de tamaños
  const a = nuevo("div", "panel", "", esc, "left:140px;top:320px;width:800px;height:330px;padding:30px 34px");
  nuevo("div", "etiqueta", "Tamaño", a);
  const filaN = nuevo("div", "", `<div class="fila" style="gap:12px;font:700 26px Lato">${ico("server", 32, C.suave)}Modelos de la nube</div>
    <div style="margin-top:12px;height:34px;border-radius:10px;background:#2b3136;position:relative;overflow:hidden"><div class="b" style="position:absolute;inset:0;background:${C.gris}"></div></div>
    <div style="font:400 22px Lato;color:var(--suave);margin-top:8px">Cientos de miles de millones de parámetros · centros de datos</div>`, a, "position:absolute;left:34px;right:34px;top:76px");
  const filaG = nuevo("div", "", `<div class="fila" style="gap:12px;font:700 26px Lato">${ico("smartphone", 32, C.celeste)}Gemma 4 E2B<span class="mono" style="margin-left:auto;color:${C.celeste};font-size:24px">2.6 GB</span></div>
    <div style="margin-top:12px;height:34px;border-radius:10px;background:#2b3136;position:relative;overflow:hidden"><div class="b" style="position:absolute;left:0;top:0;bottom:0;width:4%;background:${C.celeste}"></div></div>`, a, "position:absolute;left:34px;right:34px;top:208px");
  subir(a, 0.6);
  tl.from(filaN.querySelector(".b"), { scaleX: 0, transformOrigin: "left", duration: 1.4, ease: "power2.out" }, 1.0);
  subir(filaG, m(1) - 0.3 > 1.6 ? 1.6 : 1.6);
  tl.from(filaG.querySelector(".b"), { scaleX: 0, transformOrigin: "left", duration: 0.8, ease: "power2.out" }, 2.0);

  // Cuantización
  const q = nuevo("div", "panel", "", esc, "left:980px;top:320px;width:800px;height:330px;padding:30px 34px");
  nuevo("div", "etiqueta", "Cuantización · comprimir los números", q);
  const n16 = nuevo("div", "", `<div class="mono" style="font-size:36px;font-weight:700">0.73914826</div><div class="bits" style="display:flex;gap:5px;margin-top:12px"></div><div style="font:700 22px Lato;color:var(--suave);margin-top:10px">16 bits</div>`, q, "position:absolute;left:34px;top:80px");
  for (let i = 0; i < 16; i++) nuevo("span", "", "", n16.querySelector(".bits"), `width:18px;height:30px;border-radius:4px;background:${C.gris}`);
  const n4 = nuevo("div", "", `<div class="mono" style="font-size:36px;font-weight:700;color:${C.celeste}">0.74</div><div class="bits" style="display:flex;gap:5px;margin-top:12px"></div><div style="font:700 22px Lato;color:${C.celeste};margin-top:10px">4 bits</div>`, q, "position:absolute;left:520px;top:80px");
  for (let i = 0; i < 4; i++) nuevo("span", "", "", n4.querySelector(".bits"), `width:18px;height:30px;border-radius:4px;background:${C.celeste}`);
  nuevo("div", "", `${ico("image", 32, C.amarillo)}<span>Como comprimir una foto: pesa mucho menos y casi no se nota.</span>`, q, "position:absolute;left:34px;right:34px;bottom:30px;display:flex;gap:14px;align-items:center;font:400 24px Lato");
  subir(q, m(1));
  subir(n16, m(1) + 0.5);
  flecha(1440, 452, 1480, 452, m(1) + 1.2, C.suave);
  pop(n4, m(1) + 1.6);
  subir(q.lastChild, m(1) + 2.4);

  // Gemma 4 E2B
  const g = nuevo("div", "panel", "", esc, `left:140px;top:690px;width:800px;height:270px;padding:30px 34px;border-color:${C.amarillo}`);
  nuevo("div", "panel-titulo", `${ico("si_google", 36, C.amarillo)}Gemma 4 E2B <span style="font:400 24px Lato;color:var(--suave)">de Google</span>`, g);
  const gch = nuevo("div", "", "", g, "display:flex;flex-wrap:wrap;gap:12px;margin-top:26px");
  const gs = [["gem", "Gratis y abierto"], ["messages-square", "Entiende español"], ["hard-drive", "2.6 GB"], ["zap", "LiteRT-LM"]]
    .map(([i, t]) => nuevo("div", "pastilla", `${ico(i, 28, C.amarillo)}${t}`, gch, "font-size:24px;padding:12px 20px"));
  subir(g, m(2));
  pop(gs, m(2) + 0.6, { stagger: 0.2 });

  // Requisitos
  const r = nuevo("div", "panel", "", esc, "left:980px;top:690px;width:800px;height:270px;padding:30px 34px");
  nuevo("div", "panel-titulo", `${ico("smartphone", 34, C.celeste)}Tu celular necesita`, r);
  const req = nuevo("div", "", "", r, "display:grid;gap:14px;margin-top:22px");
  const rs = [["si_android", "Android 11 o superior (o iPhone con iOS 15+)"], ["memory-stick", "8 GB de RAM recomendados (mínimo 6)"], ["hard-drive", "Unos 3 GB libres"]]
    .map(([i, t]) => nuevo("div", "fila", `${ico(i, 30, C.celeste)}<span style="font:400 25px Lato">${t}</span>`, req, "gap:14px"));
  subir(r, m(3));
  subir(rs, m(3) + 0.5, { stagger: 0.3 });
  salida();
};

ESCENAS.embeddings = () => {
  formas(0);
  cabecera("Teoría · Embeddings", "binary", "Textos convertidos en <span class='acento'>números</span>");
  // Texto -> modelo -> vector
  const txt = nuevo("div", "panel", `${ico("file-text", 34, C.amarillo)}<span>Miércoles: entregar el proyecto</span>`, esc, "left:140px;top:340px;width:620px;height:96px;display:flex;align-items:center;gap:16px;padding:0 28px;font:700 28px Lato");
  const mod = nuevo("div", "panel", `${ico("binary", 40, C.celeste)}<div><div style="font:800 28px 'Open Sans'">EmbeddingGemma 2</div><div style="font:400 21px Lato;color:var(--suave)">165 MB · en el celular</div></div>`, esc, `left:140px;top:500px;width:620px;height:110px;display:flex;align-items:center;gap:18px;padding:0 28px;border-color:${C.celeste}`);
  const vec = nuevo("div", "panel", "", esc, "left:140px;top:676px;width:620px;height:240px;padding:24px 28px");
  const nums = nuevo("div", "mono", "", vec, `font-size:25px;line-height:1.6;color:${C.celeste}`);
  const valores = [0.12, -0.83, 0.44, 0.07, -0.29, 0.91, -0.15, 0.36, 0.58, -0.62, 0.03, 0.77];
  nums.textContent = "[" + valores.map((v) => v.toFixed(2)).join(", ") + ", ... ]";
  const cuenta = nuevo("div", "", "", vec, "position:absolute;left:28px;bottom:22px;font:700 26px Lato");
  const cn = nuevo("span", "mono", "0", cuenta, `color:${C.amarillo}`);
  nuevo("span", "", " números = un vector", cuenta);
  subir(txt, 0.7);
  flecha(450, 440, 450, 494, 1.3, C.suave);
  subir(mod, 1.5);
  flecha(450, 614, 450, 670, m(1));
  subir(vec, m(1) + 0.3);
  escribir(nums, nums.textContent, m(1) + 0.6, 40);
  contador(cn, m(1) + 1.2, 0, 768, 1.5);

  // Mapa de significados
  const mapa = nuevo("div", "panel", "", esc, "left:820px;top:340px;width:960px;height:576px");
  nuevo("div", "etiqueta", "Mapa de significados", mapa, "position:absolute;left:30px;top:24px");
  const puntos = [
    [210, 200, "Miércoles: entregar el proyecto", C.amarillo, 1], [130, 300, "Lunes: reunión con el equipo", C.amarillo, 0], [300, 330, "Jueves: clase de inglés", C.amarillo, 0],
    [650, 160, "Tengo un perro llamado Rocky", C.verde, 0], [760, 260, "Llevar a Rocky al veterinario", C.verde, 0],
    [560, 430, "Me gusta el café americano", C.rojo, 0], [740, 480, "Escucho rock de los 80", C.rojo, 0],
  ];
  const ps = puntos.map(([x, y, t, c, clave]) => {
    const p = nuevo("div", "", `<span style="display:block;width:22px;height:22px;border-radius:50%;background:${c};margin:auto"></span><span style="display:block;margin-top:8px;font:700 20px Lato;white-space:nowrap;color:${clave ? "#fff" : "var(--suave)"}">${t}</span>`, mapa, `position:absolute;left:${x}px;top:${y}px;transform:translateX(-50%);text-align:center`);
    return p;
  });
  subir(mapa, m(2) - 0.4);
  pop(ps, m(2), { stagger: 0.12 });
  const q = nuevo("div", "", `<span style="display:block;width:28px;height:28px;border-radius:7px;background:${C.celeste};margin:auto;transform:rotate(45deg)"></span><span style="display:block;margin-top:10px;font:800 22px 'Open Sans';white-space:nowrap;color:${C.celeste}">¿Qué tengo el miércoles?</span>`, mapa, "position:absolute;left:480px;top:196px;transform:translateX(-50%);text-align:center");
  tl.from(q, { x: 300, y: 260, opacity: 0, duration: 1.2, ease: "power3.out" }, m(3));
  const lienzoMapa = svg(960, 576, mapa, "left:0;top:0");
  const lin = trazo(lienzoMapa, "M466 212 L236 211", C.celeste, 4, "8 8");
  tl.from(lin, { opacity: 0, duration: 0.4 }, m(3) + 1.2);
  const cerca = nuevo("div", "pastilla", `${ico("check", 26, C.verde)}cerca = significado parecido`, mapa, "position:absolute;left:30px;bottom:24px;font-size:22px;padding:10px 18px");
  pop(cerca, m(3) + 1.5);
  salida();
};

ESCENAS.fragmentos = () => {
  formas(1);
  cabecera("Teoría · Fragmentos", "scissors", "Cortar en <span class='acento'>pedacitos</span>");
  const doc = nuevo("div", "panel", "", esc, "left:140px;top:330px;width:560px;height:620px;padding:30px");
  nuevo("div", "fila", `${ico("file-text", 30, C.amarillo)}<span style="font:800 26px 'Open Sans';margin-left:12px">mis_notas.txt</span>`, doc);
  const lineas = nuevo("div", "", "", doc, "position:absolute;left:30px;right:30px;top:90px;display:grid;gap:13px");
  const anchos = [92, 80, 88, 60, 0, 85, 94, 70, 0, 90, 76, 84, 55, 0, 88, 66];
  anchos.forEach((w) => nuevo("div", "", "", lineas, w ? `height:14px;width:${w}%;border-radius:7px;background:${C.gris}` : "height:14px"));
  subir(doc, 0.6);
  const tijera = nuevo("div", "", ico("scissors", 44, C.rojo), esc, "position:absolute;left:96px;top:520px");
  const cortes = [535, 643];
  const ls = svg(620, 1000, esc, "left:120px;top:0;z-index:2");
  const cs = cortes.map((y) => trazo(ls, `M10 ${y} L600 ${y}`, C.rojo, 4, "12 10"));
  tl.from(tijera, { opacity: 0, duration: 0.3 }, m(0) + 2.0);
  cortes.forEach((y, i) => {
    tl.fromTo(tijera, { y: y - 520 - 20, x: 0 }, { x: 560, duration: 0.9, ease: "power1.inOut" }, m(0) + 2.2 + i * 1.1);
    tl.from(cs[i], { scaleX: 0, transformOrigin: "0% 50%", duration: 0.9, ease: "power1.inOut" }, m(0) + 2.2 + i * 1.1);
  });
  tl.to(tijera, { opacity: 0, duration: 0.3 }, m(0) + 4.6);
  // tres fragmentos con su vector
  const frs = [0, 1, 2].map((i) => nuevo("div", "panel", `
      <div style="display:flex;align-items:center;gap:14px"><span class="mono" style="font-weight:700;color:${[C.amarillo, C.verde, C.rojo][i]}">#${i + 1}</span>
      <div style="flex:1;display:grid;gap:9px">${[90, 75, 60].map((w) => `<span style="height:11px;width:${w}%;border-radius:6px;background:${C.gris}"></span>`).join("")}</div></div>
      <div class="mono" style="margin-top:14px;font-size:21px;color:${C.celeste}">[${["0.12, -0.83, 0.44", "0.65, 0.08, -0.31", "-0.27, 0.59, 0.13"][i]}, ...]</div>`,
    esc, `left:800px;top:${330 + i * 165}px;width:500px;height:140px;padding:22px 26px`));
  subir(frs, m(1), { stagger: 0.25 });
  frs.forEach((f, i) => flecha(706, 420 + i * 175, 790, 400 + i * 165, m(1) + i * 0.25, C.suave, 3));
  const reglas = nuevo("div", "", "", esc, "position:absolute;left:1360px;top:340px;display:grid;gap:22px;width:420px");
  const rs = [["scissors", "Unos 800 caracteres", C.rojo], ["file-text", "Sin cortar los párrafos", C.amarillo], ["binary", "1 fragmento = 1 vector", C.celeste]]
    .map(([i, t, c]) => nuevo("div", "panel", `${ico(i, 34, c)}<span style="font:700 26px Lato">${t}</span>`, reglas, "position:relative;display:flex;gap:16px;align-items:center;padding:24px"));
  subir(rs, m(1) + 1.2, { stagger: 0.35 });
  salida();
};

ESCENAS.qdrant = () => {
  cabecera("Teoría · Base de datos vectorial", "database", "<span class='acento'>Qdrant Edge</span>: una biblioteca de significados");
  // Estantes
  const est = nuevo("div", "panel", "", esc, "left:140px;top:340px;width:760px;height:600px;padding:30px");
  nuevo("div", "etiqueta", "Fragmentos ordenados por significado", est);
  const grupos = [["Agenda", C.amarillo, 5], ["Mascota", C.verde, 3], ["Gustos", C.rojo, 4], ["Trabajo", C.azul, 5]];
  const libros = [];
  grupos.forEach(([n, c, k], gi) => {
    const fila = nuevo("div", "", `<div style="width:120px;font:700 22px Lato;color:${c}">${n}</div>`, est, `position:absolute;left:30px;right:30px;top:${90 + gi * 122}px;display:flex;align-items:flex-end;gap:10px;padding-bottom:10px;border-bottom:4px solid ${C.borde}`);
    for (let i = 0; i < k; i++) libros.push(nuevo("div", "", "", fila, `width:${46 + (i % 3) * 8}px;height:${70 + (i * 13) % 26}px;border-radius:8px;background:${c};opacity:${0.55 + (i % 3) * 0.2}`));
  });
  subir(est, 0.6);
  pop(libros, 1.0, { stagger: 0.05 });

  // Qdrant Edge
  const qd = nuevo("div", "panel", "", esc, `left:960px;top:340px;width:820px;height:230px;padding:30px;border-color:${C.rojo}`);
  nuevo("div", "panel-titulo", `${ico("si_qdrant", 40, C.rojo)}Qdrant Edge`, qd);
  const qch = nuevo("div", "", "", qd, "display:flex;flex-wrap:wrap;gap:12px;margin-top:24px");
  const qs = [["smartphone", "Vive dentro de la app"], ["cloud-off", "Sin servidor"], ["zap", "Búsqueda muy rápida"]]
    .map(([i, t]) => nuevo("div", "pastilla", `${ico(i, 28, C.rojo)}${t}`, qch, "font-size:24px;padding:12px 20px"));
  subir(qd, m(1));
  pop(qs, m(1) + 0.6, { stagger: 0.25 });

  // Búsqueda
  const bus = nuevo("div", "panel", "", esc, "left:960px;top:610px;width:820px;height:330px;padding:28px 30px");
  const pre = nuevo("div", "fila", `${ico("search", 30, C.celeste)}<span class="mono" style="font-size:25px;margin-left:14px">¿Qué tengo el miércoles?</span>`, bus);
  const res = [["Miércoles: entregar el proyecto...", 0.82, C.amarillo], ["Lunes: reunión con el equipo...", 0.61, C.amarillo], ["Jueves: clase de inglés...", 0.55, C.amarillo]];
  const lista = nuevo("div", "", "", bus, "display:grid;gap:14px;margin-top:22px");
  const fs = res.map(([t, v, c], i) => nuevo("div", "fila", `<span class="mono" style="color:var(--suave);width:36px">${i + 1}</span><span style="flex:1;font:${i ? 400 : 700} 24px Lato">${t}</span><span style="width:160px;height:16px;border-radius:8px;background:#2b3136;position:relative;overflow:hidden"><span class="b" style="position:absolute;left:0;top:0;bottom:0;width:${v * 100}%;background:${i ? C.gris : C.celeste}"></span></span><span class="mono" style="width:70px;text-align:right;font-size:23px;color:${i ? C.suave : C.celeste}">${v.toFixed(2)}</span>`, lista, "gap:12px"));
  nuevo("div", "", "puntaje de similitud: 1 = idéntico", bus, "position:absolute;right:30px;bottom:20px;font:400 20px Lato;color:var(--suave)");
  subir(bus, m(2));
  subir(fs, m(2) + 1.0, { stagger: 0.3 });
  fs.forEach((f) => tl.from(f.querySelector(".b"), { width: 0, duration: 0.8 }, m(2) + 1.4));
  tl.to(libros.slice(0, 3), { y: -16, duration: 0.4, stagger: 0.1 }, m(2) + 0.8);
  salida();
};

ESCENAS.rag = () => {
  formas(1);
  cabecera("Teoría · RAG", "workflow", "<span class='acento'>RAG</span>: buscar antes de responder", "Retrieval-Augmented Generation · generación aumentada por recuperación");
  const pasos = [
    ["message-circle", "Pregunta", "¿Qué tengo el miércoles?", C.azul],
    ["binary", "Vector", "EmbeddingGemma", C.celeste],
    ["database", "Buscar", "Qdrant · top 3", C.rojo],
    ["file-text", "Prompt", "docs + historial + pregunta", C.amarillo],
    ["brain", "Gemma 4", "genera la respuesta", C.amarillo],
    ["volume-2", "Respuesta", "con tus datos", C.verde],
  ];
  const nodos = pasos.map(([i, t, s, c], k) => nuevo("div", "panel", `
      <div class="cuadro-icono" style="width:70px;height:70px;background:${c}26;color:${c};margin:0 auto">${ico(i, 38)}</div>
      <div style="font:800 26px 'Open Sans';margin-top:16px">${t}</div>
      <div style="font:400 20px Lato;color:var(--suave);margin-top:6px">${s}</div>`,
    esc, `left:${140 + k * 280}px;top:390px;width:240px;height:220px;padding:26px 14px;text-align:center`));
  subir(nodos, 0.9, { stagger: 0.12 });
  for (let k = 0; k < 5; k++) flecha(140 + k * 280 + 244, 500, 140 + (k + 1) * 280 - 6, 500, 1.6 + k * 0.1, C.suave, 3);
  const grupos = [[0, 1, 2], [3], [4, 5]];
  grupos.forEach((g, j) => {
    g.forEach((k) => resaltar(nodos[k], m(j + 1), pasos[k][3]));
    g.forEach((k) => normal(nodos[k], j < 2 ? m(j + 2) : DUR));
  });
  const punto = nuevo("div", "", "", esc, `position:absolute;left:0;top:0;width:26px;height:26px;border-radius:50%;background:${C.celeste};z-index:2`);
  const rutaS = svg(1920, 1080, esc, "left:0;top:0");
  const camino = trazo(rutaS, "M260 640 L1660 640", "transparent", 1);
  tl.set(punto, { opacity: 0 }, 0);
  tl.set(punto, { opacity: 1 }, m(1));
  tl.fromTo(punto, { x: 247, y: 627 }, { x: 247 + 280 * 2, y: 627, duration: Math.max(1, m(2) - m(1) - 0.5), ease: "power1.inOut", immediateRender: false }, m(1));
  tl.to(punto, { x: 247 + 280 * 3, duration: 0.8, ease: "power1.inOut" }, m(2));
  tl.to(punto, { x: 247 + 280 * 5, duration: 1.2, ease: "power1.inOut" }, m(3));
  // El prompt que se arma
  const pr = nuevo("div", "codigo", "", esc, "position:absolute;left:140px;top:680px;width:1640px;height:280px;font-size:23px");
  const texto = "Información de los documentos del usuario:\n- Miércoles: entregar el proyecto de la tienda online antes de las 6:00 p. m.\nConversación hasta ahora:\nUsuario: Hola, YARBYS\nPregunta del usuario: ¿Qué tengo el miércoles?";
  subir(pr, m(2) + 0.3);
  escribir(pr, texto, m(2) + 0.8, 60);
  salida();
};

ESCENAS.memoria = () => {
  formas(0);
  cabecera("Teoría · Memoria", "history", "La <span class='acento'>memoria</span> de YARBYS");
  // Sin memoria
  const sin = nuevo("div", "panel", "", esc, "left:140px;top:330px;width:520px;height:620px;padding:30px");
  nuevo("div", "etiqueta", "Un LLM solo, sin memoria", sin);
  const b1 = nuevo("div", "burbuja tu", "¿Y cómo se llama mi perro?", sin, "position:absolute;right:30px;top:100px;max-width:400px");
  const b2 = nuevo("div", "burbuja ia", "¿Tu perro? No sé de qué me hablas.", sin, "position:absolute;left:30px;top:220px;max-width:400px");
  const x = nuevo("div", "", ico("x", 70, C.rojo), sin, "position:absolute;left:0;right:0;top:350px;text-align:center");
  const b3 = nuevo("div", "burbuja ia", "Se llama Rocky. ¡Me lo contaste hace un rato!", sin, `position:absolute;left:30px;top:440px;max-width:430px;border-color:${C.verde}`);
  subir(sin, 0.6);
  pop(b1, m(0) + 1.5);
  pop(b2, m(0) + 2.6);
  pop(x, m(0) + 3.4);

  // SQLite con dos tablas
  const db = nuevo("div", "panel", "", esc, `left:700px;top:330px;width:1080px;height:620px;padding:30px;border-color:${C.azul}`);
  nuevo("div", "panel-titulo", `${ico("si_sqlite", 38, C.azul)}SQLite <span class="mono" style="font-size:22px;color:var(--suave);font-weight:400">yarbys.db · un solo archivo</span>`, db);
  const tabla = (x0, w, titulo, cols, filas) => {
    const t = nuevo("div", "", `<div style="font:800 22px 'Open Sans';margin-bottom:10px;color:${C.celeste}">${titulo}</div>`, db, `position:absolute;left:${x0}px;top:96px;width:${w}px`);
    const head = nuevo("div", "", cols.map(([c, cw]) => `<span style="width:${cw}px">${c}</span>`).join(""), t, "display:flex;gap:10px;font:700 18px 'JetBrains Mono';color:var(--suave);padding:8px 12px;background:#2b3136;border-radius:10px 10px 0 0");
    const fs = filas.map((f) => nuevo("div", "", f.map((v, i) => `<span style="width:${cols[i][1]}px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${v}</span>`).join(""), t, `display:flex;gap:10px;font:400 18px 'JetBrains Mono';padding:8px 12px;border-bottom:2px solid ${C.borde}`));
    return [t, fs];
  };
  const [th, fh] = tabla(30, 300, "hilos", [["id", 40], ["titulo", 220]], [["1", "¿Qué tengo el miércoles?"], ["2", "Ideas para el video"]]);
  const msgs = [["1", "usuario", "¿Qué tengo el miércoles?"], ["1", "yarbys", "Entregar el proyecto..."], ["1", "usuario", "Gracias"], ["1", "yarbys", "¡De nada!"],
                ["1", "usuario", "¿Qué música me gusta?"], ["1", "yarbys", "El rock de los 80."], ["1", "usuario", "¿Tengo mascota?"], ["1", "yarbys", "Sí, un perro: Rocky."]];
  const [tm, fm] = tabla(370, 670, "mensajes", [["hilo", 60], ["rol", 110], ["texto", 440]], msgs);
  subir(db, m(1));
  subir([th, tm], m(1) + 0.6, { stagger: 0.2 });
  aparecer(fh, m(1) + 1.0, { stagger: 0.2 });
  aparecer(fm, m(1) + 1.4, { stagger: 0.25 });
  // últimos 6 mensajes
  const marco = nuevo("div", "", "", db, `position:absolute;left:362px;top:265px;width:690px;height:252px;border:3px solid ${C.amarillo};border-radius:12px`);
  const et = nuevo("div", "pastilla", `${ico("send", 26, C.amarillo)}Los últimos 6 mensajes van en el prompt`, db, "position:absolute;left:380px;bottom:28px;font-size:22px;padding:10px 18px");
  tl.from(marco, { opacity: 0, scale: 1.05, duration: 0.5 }, m(2) + 0.8);
  pop(et, m(2) + 1.2);
  pop(b3, m(2) + 2.2);
  tl.to(x, { opacity: 0, duration: 0.3 }, m(2) + 2.2);
  salida();
};

ESCENAS.voz = () => {
  formas(1);
  cabecera("Teoría · Voz", "audio-lines", "Escuchar y <span class='acento'>hablar</span>");
  const fila = (y, items) => items.map(([html, x, w, borde], i) => nuevo("div", "panel", html, esc, `left:${x}px;top:${y}px;width:${w}px;height:170px;display:flex;align-items:center;justify-content:center;gap:16px;padding:0 24px;${borde ? "border-color:" + borde : ""}`));
  const onda = (n, c) => `<div style="display:flex;gap:6px;align-items:center">${Array.from({ length: n }, (_, i) => `<span class="o" style="width:8px;height:${20 + ((i * 37) % 50)}px;border-radius:4px;background:${c}"></span>`).join("")}</div>`;
  const a = fila(360, [[ico("mic", 64, C.celeste), 140, 220], [onda(14, C.celeste), 410, 300], [`<div><div class="mono" style="font-size:26px;font-weight:700">speech_to_text</div><div style="font:400 21px Lato;color:var(--suave)">voz → texto</div></div>`, 760, 400, C.celeste], [`<span style="font:700 27px Lato">“¿Qué tengo el miércoles?”</span>`, 1210, 570]]);
  const b = fila(620, [[`<span style="font:700 27px Lato">“Tienes que entregar el proyecto...”</span>`, 140, 570], [`<div><div class="mono" style="font-size:26px;font-weight:700">flutter_tts</div><div style="font:400 21px Lato;color:var(--suave)">texto → voz</div></div>`, 760, 400, C.verde], [onda(14, C.verde), 1210, 300], [ico("volume-2", 64, C.verde), 1560, 220]]);
  subir(a, 0.8, { stagger: 0.2 });
  [[360, 410], [710, 760], [1160, 1210]].forEach(([x1, x2], i) => flecha(x1 + 4, 445, x2 - 8, 445, 1.4 + i * 0.2, C.suave, 3));
  subir(b, m(0) + 3, { stagger: 0.2 });
  [[710, 760], [1160, 1210], [1510, 1560]].forEach(([x1, x2], i) => flecha(x1 + 4, 705, x2 - 8, 705, m(0) + 3.6 + i * 0.2, C.suave, 3));
  document.querySelectorAll(".o").forEach((o, i) => tl.to(o, { scaleY: 0.3, duration: 0.25, yoyo: true, repeat: Math.floor(DUR / 0.5), ease: "sine.inOut" }, (i % 14) * 0.05));
  const nota = nuevo("div", "pastilla", `${ico("wifi-off", 30, C.amarillo)}Sin internet si tienes descargado el idioma español`, esc, "position:absolute;left:140px;top:870px");
  pop(nota, m(1));
  salida();
};

ESCENAS.flutter = () => {
  formas(0);
  cabecera("Flutter", "si_flutter", "Flutter: <span class='acento'>un código</span>, dos apps");
  const cod = nuevo("div", "codigo", `<span style="color:#569cd6">class</span> <span style="color:#4ec9b0">YarbysApp</span> <span style="color:#569cd6">extends</span> <span style="color:#4ec9b0">StatelessWidget</span> {
  <span style="color:#4ec9b0">Widget</span> <span style="color:#dcdcaa">build</span>(context) {
    <span style="color:#c586c0">return</span> <span style="color:#4ec9b0">MaterialApp</span>(
      title: <span style="color:#ce9178">'YARBYS'</span>,
      home: <span style="color:#4ec9b0">PantallaInicio</span>(),
    );
  }
}`, esc, "position:absolute;left:140px;top:330px;width:760px;font-size:23px");
  nuevo("div", "", `${ico("si_dart", 30, C.celeste)}<span>lib/main.dart · lenguaje Dart</span>`, esc, "position:absolute;left:140px;top:678px;display:flex;gap:12px;align-items:center;font:700 23px Lato;color:var(--suave)");
  subir(cod, 0.7);
  const so = [["si_android", "Android", "#3ddc84", 360], ["si_apple", "iPhone", "#ffffff", 520]].map(([i, t, c, y]) =>
    nuevo("div", "panel", `${ico(i, 44, c)}<span style="font:800 28px 'Open Sans'">${t}</span>`, esc, `left:1010px;top:${y}px;width:270px;height:120px;display:flex;align-items:center;gap:16px;padding:0 26px`));
  flecha(905, 450, 1000, 420, 1.6);
  flecha(905, 470, 1000, 575, 1.7);
  pop(so, 1.9, { stagger: 0.2 });

  // Widgets como bloques
  const wid = nuevo("div", "panel", "", esc, "left:1340px;top:320px;width:440px;height:640px;padding:24px");
  nuevo("div", "etiqueta", "Todo es un widget", wid);
  const bloque = (padre, nombre, color, estilo) => nuevo("div", "", `<span class="mono" style="font-size:18px;color:${color}">${nombre}</span>`, padre, `border:3px solid ${color};border-radius:14px;padding:10px 12px;${estilo}`);
  const scaf = bloque(wid, "Scaffold", C.azul, "position:absolute;left:24px;right:24px;top:70px;bottom:24px");
  const col = bloque(scaf, "Column", C.celeste, "margin-top:10px;height:480px;display:flex;flex-direction:column;gap:10px");
  const bs = [["Nucleo", C.amarillo, "height:120px"], ["ListView", C.verde, "flex:1"], ["TextField", C.rojo, "height:60px"]].map(([n, c, e]) => bloque(col, n, c, e));
  subir(wid, m(1));
  tl.from(scaf, { scale: 0.8, opacity: 0, duration: 0.5, ease: "back.out(1.6)" }, m(1) + 0.4);
  tl.from(col, { scale: 0.8, opacity: 0, duration: 0.5, ease: "back.out(1.6)" }, m(1) + 0.8);
  tl.from(bs, { y: -120, opacity: 0, duration: 0.6, stagger: 0.3, ease: "bounce.out" }, m(1) + 1.2);

  // pub.dev
  const pub = nuevo("div", "panel", "", esc, "left:140px;top:728px;width:1140px;height:232px;padding:24px 30px");
  nuevo("div", "panel-titulo", `${ico("package", 34, C.celeste)}Paquetes de <span class="mono" style="color:${C.celeste}">pub.dev</span>`, pub);
  const chips = nuevo("div", "", "", pub, "display:flex;flex-wrap:wrap;gap:12px;margin-top:22px");
  const pk = ["flutter_edge_ai", "flutter_edge_ai_litertlm", "flutter_edge_ai_rag", "flutter_edge_ai_qdrant", "sqflite", "speech_to_text", "flutter_tts"].map((n, i) =>
    nuevo("div", "pastilla mono", n, chips, `font:700 21px 'JetBrains Mono';padding:10px 18px;${i < 4 ? "border-color:" + C.celeste : ""}`));
  subir(pub, m(2));
  pop(pk, m(2) + 0.6, { stagger: 0.15 });
  salida();
};

ESCENAS.arquitectura = () => {
  cabecera("El plan completo", "network", "Arquitectura de <span class='acento'>YARBYS</span>");
  const cel = nuevo("div", "", "", esc, `position:absolute;left:140px;top:300px;width:1360px;height:680px;border:4px solid ${C.borde};border-radius:48px;background:#2b3035`);
  nuevo("div", "pastilla", `${ico("smartphone", 28, C.celeste)}Tu celular`, cel, "position:absolute;left:40px;top:-28px;background:var(--fondo);font-size:22px;padding:8px 18px");
  aparecer(cel, 0.5);
  const fila = (y, items, color, et) => {
    nuevo("div", "etiqueta", et, cel, `position:absolute;left:40px;top:${y - 34}px`);
    return items.map(([i, t, s], k) => nuevo("div", "panel", `${ico(i, 34, color)}<div><div style="font:800 23px 'Open Sans'">${t}</div><div class="mono" style="font-size:16px;color:var(--suave)">${s}</div></div>`,
      cel, `left:${40 + k * 322}px;top:${y}px;width:296px;height:96px;display:flex;align-items:center;gap:14px;padding:0 20px`));
  };
  const pant = fila(80, [["download", "Inicio", "inicio.dart"], ["message-circle", "Chat", "chat.dart"], ["file-text", "Documentos", "documentos.dart"], ["sliders-horizontal", "Ajustes", "ajustes.dart"]], "#02569b", "Pantallas · Flutter");
  const serv = fila(310, [["history", "Memoria", "memoria.dart"], ["scan-search", "Conocimiento", "conocimiento.dart"], ["audio-lines", "Voz", "voz.dart"], ["brain", "Cerebro", "cerebro.dart"]], C.celeste, "Servicios");
  const datos = fila(540, [["si_sqlite", "SQLite", "yarbys.db"], ["si_qdrant", "Qdrant Edge", "+ EmbeddingGemma"], ["mic", "Mic y parlante", "motores del sistema"], ["cpu", "Gemma 4", ".litertlm"]], C.amarillo, "Datos y modelos");
  subir(pant, m(0) + 0.8, { stagger: 0.1 });
  subir(serv, m(1), { stagger: 0.1 });
  for (let k = 0; k < 4; k++) flecha(140 + 40 + k * 322 + 240, 300 + 182, 140 + 40 + k * 322 + 240, 300 + 300, m(1) + 0.5, C.suave, 3);
  subir(datos, m(2), { stagger: 0.1 });
  for (let k = 0; k < 4; k++) flecha(140 + 40 + k * 322 + 240, 300 + 412, 140 + 40 + k * 322 + 240, 300 + 530, m(2) + 0.5, C.suave, 3);
  [1, 0, 3].forEach((k, i) => { resaltar(serv[k], m(2) + 0.8 + i * 0.8, C.amarillo); normal(serv[k], m(3)); });
  // Fuera del celular
  const hf = nuevo("div", "panel", `${ico("download", 34, C.suave)}<div><div style="font:800 23px 'Open Sans'">Hugging Face</div><div style="font:400 19px Lato;color:var(--suave)">descarga única de los modelos</div></div>`, esc, "left:1540px;top:780px;width:250px;height:150px;display:flex;flex-direction:column;justify-content:center;gap:8px;padding:0 20px");
  const ext = nuevo("div", "panel", `${ico("cloud", 34, C.amarillo)}<div><div style="font:800 23px 'Open Sans'">LLM externo</div><div style="font:400 19px Lato;color:var(--suave)">opcional · GPT-6 Luna o Claude Haiku</div></div>`, esc, `left:1540px;top:520px;width:250px;height:170px;display:flex;flex-direction:column;justify-content:center;gap:8px;padding:0 20px;border-style:dashed;border-color:${C.amarillo}`);
  subir(hf, m(3));
  flecha(1536, 860, 1460, 860, m(3) + 0.4, C.suave, 3, "10 10");
  subir(ext, m(3) + 1.6);
  flecha(1536, 640, 1458, 650, m(3) + 2.0, C.amarillo, 3, "10 10");
  salida();
};

ESCENAS.instalacion = () => {
  formas(1);
  cabecera("Instalación en Windows", "laptop", "Prepara tu <span class='acento'>computadora</span>");
  const pasos = [
    ["si_flutter", "1 · Flutter SDK", "flutter.dev → descomprime en C:\\flutter y agrega bin al PATH", "#02569b"],
    ["si_android", "2 · Android Studio", "Trae el Android SDK para compilar apps", "#3ddc84"],
    ["code", "3 · VS Code", "Con la extensión Flutter", C.azul],
    ["smartphone", "4 · Tu celular", "Con la depuración USB activada", C.celeste],
  ];
  const cs = pasos.map(([i, t, s, c], k) => nuevo("div", "panel", `
      <div class="cuadro-icono" style="width:76px;height:76px;background:${c}26;color:${c}">${ico(i, 42)}</div>
      <div style="font:800 30px 'Open Sans';margin-top:22px">${t}</div>
      <div style="font:400 23px Lato;color:var(--suave);margin-top:10px;line-height:1.4">${s}</div>`,
    esc, `left:${140 + (k % 2) * 500}px;top:${320 + Math.floor(k / 2) * 330}px;width:470px;height:300px;padding:30px`));
  pop(cs[0], m(0) + 0.6);
  pop(cs[1], m(1));
  pop(cs[2], m(2));
  pop(cs[3], m(2) + 2.0);
  [0, 1, 2, 3].forEach((k) => resaltar(cs[k], [m(0) + 0.8, m(1) + 0.2, m(2) + 0.2, m(2) + 2.2][k], pasos[k][3]));
  [0, 1, 2].forEach((k) => normal(cs[k], [m(1), m(2), m(2) + 2][k]));
  // Ajustes de Android (mini)
  const [tel, pan] = telefono(esc, 1230, 300, 400, 680);
  pan.style.background = "#1b1f23";
  const cont = nuevo("div", "", "", pan, "position:absolute;left:0;right:0;top:60px;padding:0 22px;font-family:Lato;color:#e8eef3");
  nuevo("div", "", "Acerca del teléfono", cont, "font:800 28px 'Open Sans';margin-bottom:22px");
  ["Nombre del dispositivo", "Versión de Android", "Número de compilación"].forEach((t, i) =>
    nuevo("div", "", `<div style="font:700 22px Lato">${t}</div><div style="font:400 18px Lato;color:#8a9aa8">${["Mi celular", "16", "BP2A.250805.005"][i]}</div>`, cont, `padding:16px 14px;border-radius:14px;${i === 2 ? "background:#2b3136" : ""}`));
  const toque = nuevo("div", "", "", pan, `position:absolute;left:210px;top:290px;width:60px;height:60px;border-radius:50%;background:${C.celeste}55;border:3px solid ${C.celeste}`);
  const toast = nuevo("div", "", "¡Ahora eres desarrollador!", pan, "position:absolute;left:30px;right:30px;bottom:200px;padding:14px;border-radius:14px;background:#e8eef3;color:#1b1f23;font:700 21px Lato;text-align:center");
  const usb = nuevo("div", "", `<div><div style="font:700 22px Lato">Depuración USB</div><div style="font:400 17px Lato;color:#8a9aa8">Opciones de desarrollador</div></div><span class="sw" style="margin-left:auto;width:62px;height:34px;border-radius:17px;background:#41484e;position:relative"><span class="bola" style="position:absolute;left:4px;top:4px;width:26px;height:26px;border-radius:50%;background:#e8eef3"></span></span>`, pan, "position:absolute;left:22px;right:22px;bottom:70px;display:flex;align-items:center;padding:16px 14px;border-radius:14px;background:#2b3136;color:#e8eef3");
  subir(tel, m(3) - 0.2);
  tl.set(toque, { opacity: 0 }, 0);
  for (let k = 0; k < 7; k++) {
    tl.set(toque, { opacity: 1, scale: 0.6 }, m(3) + 0.8 + k * 0.35);
    tl.to(toque, { scale: 1.2, opacity: 0, duration: 0.3 }, m(3) + 0.8 + k * 0.35);
  }
  tl.from(toast, { opacity: 0, y: 20, duration: 0.4 }, m(3) + 3.4);
  tl.to(toast, { opacity: 0, duration: 0.4 }, m(3) + 5.2);
  tl.from(usb, { opacity: 0, y: 30, duration: 0.5 }, m(3) + 5.6);
  tl.to(usb.querySelector(".sw"), { backgroundColor: C.verde, duration: 0.3 }, m(3) + 6.6);
  tl.to(usb.querySelector(".bola"), { x: 28, duration: 0.3 }, m(3) + 6.6);
  salida();
};

ESCENAS.negocio = () => {
  formas(0);
  cabecera("Bonus · Negocio", "hand-coins", "¿Cómo <span class='acento'>ganar dinero</span> con YARBYS?");
  const planes = [
    ["smartphone", "Gratis", "100% local", ["Sin límites ni anuncios", "Tus datos no salen del celular", "Atrae a muchos usuarios"], C.celeste],
    ["crown", "Pro · pago único", "Compra dentro de la app", ["LLM externo con tu API key", "Más funciones y temas", "Tú no pagas los tokens"], C.amarillo],
    ["building-2", "Empresas", "Privacidad como valor", ["Clínicas, estudios, colegios", "Datos sensibles sin nube", "Versión a medida"], C.verde],
  ];
  const cs = planes.map(([i, t, s, items, c], k) => nuevo("div", "panel", `
      <div class="fila" style="gap:18px"><div class="cuadro-icono" style="width:74px;height:74px;background:${c}26;color:${c}">${ico(i, 40)}</div>
      <div><div style="font:800 32px 'Open Sans'">${t}</div><div style="font:700 21px Lato;color:${c}">${s}</div></div></div>
      <div style="display:grid;gap:16px;margin-top:30px">${items.map((x) => `<div class="fila" style="gap:12px;font:400 25px Lato">${ico("check", 26, c)}${x}</div>`).join("")}</div>`,
    esc, `left:${140 + k * 555}px;top:330px;width:525px;height:420px;padding:34px`));
  subir(cs[0], m(1));
  subir(cs[1], m(2));
  subir(cs[2], m(3));
  resaltar(cs[1], m(2) + 0.6, C.amarillo);
  normal(cs[1], m(3));
  const nota = nuevo("div", "panel", `${ico("key-round", 36, C.amarillo)}<span style="font:400 26px Lato">La API key la pone cada usuario y se guarda cifrada en su celular. <b>Más adelante:</b> una suscripción con tu propio servidor.</span>`,
    esc, "left:140px;top:790px;width:1640px;height:130px;display:flex;align-items:center;gap:20px;padding:0 34px");
  subir(nota, m(4) || m(3) + 3);
  salida();
};

ESCENAS.resumen = () => {
  formas(1);
  cabecera("Resumen", "list-checks", "Lo que <span class='acento'>construimos</span>");
  const items = [
    ["brain", "Gemma 4 respondiendo dentro del celular"],
    ["binary", "EmbeddingGemma y Qdrant Edge para tus documentos"],
    ["history", "SQLite para recordar cada conversación"],
    ["audio-lines", "Voz con los motores del teléfono"],
    ["cloud", "LLM externo opcional para la versión Pro"],
    ["package", "El APK listo con GitHub Actions"],
  ];
  const lista = nuevo("div", "", "", esc, "position:absolute;left:140px;top:330px;display:grid;gap:20px;width:1000px");
  const fs = items.map(([i, t]) => nuevo("div", "panel", `<span class="cuadro-icono" style="width:56px;height:56px;background:${C.verde}26;color:${C.verde}">${ico("check", 32)}</span>${ico(i, 34, C.celeste)}<span style="font:700 28px Lato">${t}</span>`, lista, "position:relative;display:flex;align-items:center;gap:20px;padding:16px 24px"));
  subir(fs.slice(0, 1), 0.8);
  subir(fs.slice(1, 4), m(1), { stagger: 0.5 });
  subir(fs.slice(4), m(2), { stagger: 0.5 });
  const [tel, pan] = telefono(esc, 1290, 300, 400, 680);
  nuevo("div", "", "YARBYS", pan, `position:absolute;left:28px;top:56px;font:800 26px 'Open Sans';letter-spacing:.16em;color:${C.celeste}`);
  nucleo(pan, 186, 300, 120, { nombre: "YARBYS", estado: "EN LÍNEA" });
  nuevo("div", "pastilla", `${ico("plane", 24, C.verde)}Sin internet`, pan, `position:absolute;left:0;right:0;margin:auto;width:fit-content;top:540px;font-size:20px;padding:8px 16px;color:${C.verde}`);
  subir(tel, 0.6);
  salida();
};

ESCENAS.final = () => {
  const nu = nucleo(esc, 960, 260, 120, { nombre: "YARBYS", estado: "EN LÍNEA" });
  dibujarAnillos(nu, 0.1, 1.4);
  const t = nuevo("div", "", "¡Gracias por ver!", esc, "position:absolute;left:0;right:0;top:450px;text-align:center;font:800 84px 'Open Sans'");
  const sp = new SplitText(t, { type: "chars" });
  tl.from(sp.chars, { yPercent: 80, opacity: 0, duration: 0.6, stagger: 0.03, ease: "back.out(1.7)" }, 0.3);
  const gh = nuevo("div", "pastilla", `${ico("si_github", 32)}<span>Código en GitHub: <span class="mono" style="color:${C.celeste}">paulantezana/tutoriales</span></span>`, esc, "position:absolute;left:0;right:0;margin:auto;width:fit-content;top:590px");
  subir(gh, m(0) + 0.4);
  const fila = nuevo("div", "", "", esc, "position:absolute;left:0;right:0;top:710px;display:flex;justify-content:center;gap:30px");
  const bs = [["thumbs-up", "Me gusta", C.azul], ["bell", "Suscríbete", C.rojo], ["message-circle", "Comenta", C.amarillo]].map(([i, x, c]) =>
    nuevo("div", "", `${ico(i, 38, "#fff")}<span>${x}</span>`, fila, `display:flex;gap:14px;align-items:center;padding:22px 40px;border-radius:999px;background:${c};font:800 34px 'Open Sans';color:${c === C.amarillo ? "#1b1b1b" : "#fff"}`));
  pop(bs, m(1), { stagger: 0.2 });
  tl.to(bs[1], { scale: 1.08, duration: 0.35, yoyo: true, repeat: 5, ease: "sine.inOut" }, m(1) + 1.2);
  const nombre = nuevo("div", "", "Paul Antezana", esc, "position:absolute;left:0;right:0;top:880px;text-align:center;font:700 28px Lato;color:var(--suave);letter-spacing:.2em;text-transform:uppercase");
  subir(nombre, m(1) + 0.8);
  tl.to(esc, { opacity: 0, duration: 0.8 }, DUR - 0.8);
};

// ¿De dónde sale la URL de un modelo? (pasos en Hugging Face y partes del enlace)
ESCENAS.hf = () => {
  const D = DATOS;
  formas(0);
  cabecera("¿De dónde sale la URL?", "link", `El enlace de <span class='acento'>${D.nombre}</span>`, "Los modelos abiertos se publican en Hugging Face");
  const pasos = [
    ["globe", "1 · Entra a", `<span class="mono" style="color:${C.celeste}">huggingface.co</span>`],
    ["search", "2 · Busca", `<span class="mono" style="color:${C.amarillo}">${D.busqueda}</span>`],
    ["folder-open", "3 · Abre la pestaña", `<b>Files and versions</b>`],
    ["download", "4 · En el archivo", `clic derecho en <b>descargar</b> → <b>Copiar dirección del enlace</b>`],
  ];
  const cs = pasos.map(([i, t, d], k) => nuevo("div", "panel", `
      <div class="cuadro-icono" style="width:66px;height:66px;background:${C.celeste}26;color:${C.celeste}">${ico(i, 36)}</div>
      <div style="font:800 26px 'Open Sans';margin-top:18px">${t}</div>
      <div style="font:400 24px/1.4 Lato;margin-top:8px;word-break:break-word">${d}</div>`,
    esc, `left:${140 + k * 415}px;top:350px;width:390px;height:280px;padding:28px`));
  subir(cs, 0.8, { stagger: 0.15 });
  cs.forEach((c, k) => { resaltar(c, m(1) + k * Math.max(1.2, (m(2) - m(1)) / 4), C.amarillo); normal(c, m(1) + (k + 1) * Math.max(1.2, (m(2) - m(1)) / 4)); });

  // Las partes del enlace
  const caja = nuevo("div", "panel", "", esc, "left:140px;top:670px;width:1640px;height:290px;padding:28px 34px");
  nuevo("div", "etiqueta", "Las partes del enlace", caja);
  const fila = nuevo("div", "", "", caja, "position:relative;margin-top:26px;font:700 24px 'JetBrains Mono';white-space:nowrap");
  const partes = [
    ["https://huggingface.co/", C.gris, "el sitio"],
    [D.cuenta, C.amarillo, "quién lo publica"],
    ["/", null, ""],
    [D.repo, C.celeste, "el modelo"],
    ["/resolve/", C.gris, "descargar"],
    [D.version, C.verde, D.version_txt],
    ["/", null, ""],
    [D.archivo, C.rojo, `el archivo · ${D.peso}`],
  ];
  const largo = partes.reduce((n, p) => n + p[0].length, 0);
  fila.style.fontSize = `${Math.min(26, Math.floor(1560 / (largo * 0.6)))}px`;
  const spans = partes.map(([t, c]) => nuevo("span", "", t, fila, `color:${c || "#fff"};${c ? `border-bottom:4px solid ${c};padding-bottom:6px` : ""}`));
  // etiquetas debajo de cada parte, en dos filas para que no se encimen
  const etiquetas = [];
  let fila2 = 0;
  partes.forEach(([t, c, et], i) => {
    if (!c) return;
    const sp = spans[i];
    const e = nuevo("div", "", et, fila, `position:absolute;left:${sp.offsetLeft}px;top:${46 + (fila2 % 2) * 32}px;font:700 19px Lato;color:${c};white-space:nowrap`);
    fila2++;
    etiquetas.push([sp, e]);
  });
  const segs = etiquetas.flat();
  subir(caja, m(2));
  etiquetas.forEach(([sp, e], i) => {
    tl.from(sp, { opacity: 0.25, duration: 0.4 }, m(2) + 0.6 + i * 0.4);
    tl.from(e, { opacity: 0, y: 10, duration: 0.4 }, m(2) + 0.6 + i * 0.4);
  });
  if (D.nota) {
    const nota = nuevo("div", "pastilla", `${ico("check", 26, C.verde)}${D.nota}`, caja, "position:absolute;left:34px;bottom:24px;font-size:21px;padding:10px 18px");
    pop(nota, m(3) || m(2) + 3);
  }
  salida();
};

// ------------------------------------------------------------- arranque
document.fonts.ready.then(() => {
  (ESCENAS[ID] || (() => {}))();
  tl.seek(0);
  window.__listo = true;
});
window.seek = (t) => { tl.seek(Math.max(0, Math.min(t, DUR)), false); return 0; };

// ============================================================= CURSO (9 videos)
// Núcleo de la app final: tres anillos que giran y un centro (igual que widgets/nucleo.dart)
function nucleo3(padre, x, y, R, velocidad = 1, color = C.celeste) {
  const s = svg(R * 2.2, R * 2.2, padre, `left:${x - R * 1.1}px;top:${y - R * 1.1}px`);
  s.setAttribute("viewBox", `${-R * 1.1} ${-R * 1.1} ${R * 2.2} ${R * 2.2}`);
  const arco = (r, a0, largo, ancho) => {
    const p0 = [r * Math.cos(a0), r * Math.sin(a0)], p1 = [r * Math.cos(a0 + largo), r * Math.sin(a0 + largo)];
    return trazo(s, `M${p0[0]} ${p0[1]} A${r} ${r} 0 ${largo > Math.PI ? 1 : 0} 1 ${p1[0]} ${p1[1]}`, color, ancho);
  };
  const ext = trazo(s, `M${R * 0.95} 0 A${R * 0.95} ${R * 0.95} 0 1 1 ${-R * 0.95} 0 A${R * 0.95} ${R * 0.95} 0 1 1 ${R * 0.95} 0`, color, R * 0.02);
  const g1 = document.createElementNS("http://www.w3.org/2000/svg", "g");
  const g2 = document.createElementNS("http://www.w3.org/2000/svg", "g");
  s.appendChild(g1); s.appendChild(g2);
  g1.appendChild(arco(R * 0.8, 0, Math.PI * 0.7, R * 0.07));
  g1.appendChild(arco(R * 0.8, Math.PI, Math.PI * 0.7, R * 0.07));
  g2.appendChild(arco(R * 0.64, 0, Math.PI * 1.2, R * 0.03));
  const cen = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  cen.setAttribute("r", R * 0.42); cen.setAttribute("fill", color + "28"); cen.setAttribute("stroke", color); cen.setAttribute("stroke-width", R * 0.02);
  s.appendChild(cen);
  const o = { t: 0 };
  tl.to(o, { t: DUR, duration: DUR, ease: "none", onUpdate: () => {
    g1.setAttribute("transform", `rotate(${(o.t * 34 * velocidad).toFixed(2)})`);
    g2.setAttribute("transform", `rotate(${(-o.t * 52 * velocidad).toFixed(2)})`);
  } }, 0);
  return s;
}

// Portada de cada video: número, título, qué se hace hoy y el resultado
ESCENAS.portada = () => {
  const D = DATOS;
  formas(0);
  // columna izquierda: todo fluye hacia abajo, así un título largo no tapa el resto
  const col = nuevo("div", "", "", esc, "position:absolute;left:140px;top:130px;width:1040px;display:flex;flex-direction:column;gap:18px");
  const k = nuevo("div", "kicker", `${ico("clapperboard", 24)}Curso YARBYS · Video ${D.num} de ${D.total}`, col, "position:relative;align-self:flex-start");
  const h = nuevo("h1", "titulo", D.titulo, col, "position:relative;margin:0");
  const sp = new SplitText(h, { type: "lines,words", linesClass: "linea-titulo" });
  tl.from(k, { y: 20, opacity: 0, duration: 0.5 }, 0.1);
  tl.from(sp.words, { yPercent: 110, duration: 0.8, stagger: 0.05, ease: "power4.out" }, 0.25);
  const sub = nuevo("div", "subtitulo", D.sub, col, "position:relative;margin:0");
  subir(sub, 0.7);
  nuevo("div", "etiqueta", "Hoy vamos a", col, "position:relative;margin-top:18px");
  const ps = D.puntos.map(([i, t]) => nuevo("div", "panel", `${ico(i, 34, C.celeste)}<span style="font:700 27px Lato">${t}</span>`, col, "position:relative;display:flex;align-items:center;gap:18px;padding:14px 22px;width:900px"));
  subir(ps, m(1), { stagger: 0.35 });
  const res = nuevo("div", "panel", `<div class="etiqueta" style="position:relative;color:${C.verde}">${ico("circle-check", 22, C.verde)} Al final del video</div>
      <div style="display:flex;align-items:center;gap:20px;margin-top:18px">${ico(D.icono || "smartphone", 64, C.amarillo)}
      <div style="font:800 32px/1.25 'Open Sans'">${D.resultado}</div></div>`, esc,
    `left:1250px;top:560px;width:540px;padding:28px 30px;border-color:${C.verde}`);
  pop(res, m(2));
  salida();
};

// Dónde estamos: las tres capas de la arquitectura; lo hecho, lo de hoy y lo que falta
ESCENAS.mapa = () => {
  const D = DATOS;
  const hechos = new Set(D.hechos || []), hoy = new Set(D.hoy || []);
  formas(1);
  cabecera(D.kicker || "Dónde estamos", "map", D.titulo || "La arquitectura de <span class='acento'>YARBYS</span>");
  const cel = nuevo("div", "", "", esc, `position:absolute;left:140px;top:300px;width:1400px;height:680px;border:4px solid ${C.borde};border-radius:48px;background:#2b3035`);
  nuevo("div", "pastilla", `${ico("smartphone", 28, C.celeste)}Tu celular`, cel, "position:absolute;left:40px;top:-28px;background:var(--fondo);font-size:22px;padding:8px 18px");
  aparecer(cel, 0.4);
  const caja = (id, x, y, w, icono, titulo, sub, color) => {
    const e = nuevo("div", "panel", `${ico(icono, 34, color)}<div><div style="font:800 24px 'Open Sans'">${titulo}</div><div class="mono" style="font-size:16px;color:var(--suave)">${sub}</div></div>`,
      cel, `left:${x}px;top:${y}px;width:${w}px;height:96px;display:flex;align-items:center;gap:14px;padding:0 20px`);
    e.dataset.id = id;
    return e;
  };
  const filas = [
    ["Pantallas · lo que ves", 70, [["inicio", "download", "Inicio", "inicio.dart"], ["chat", "message-circle", "Chat", "chat.dart"], ["documentos", "file-text", "Documentos", "documentos.dart"]], "#02569b"],
    ["El asistente", 300, [["yarbys", "sparkles", "Yarbys", "yarbys.dart · preguntar()"]], C.amarillo],
    ["Servicios · sin pantallas", 530, [["modelos", "download", "Modelos", "modelos.dart"], ["cerebro", "brain", "Cerebro", "cerebro.dart"], ["memoria", "history", "Memoria", "memoria.dart"], ["conocimiento", "scan-search", "Conocimiento", "conocimiento.dart"], ["voz", "audio-lines", "Voz", "voz.dart"]], C.celeste],
  ];
  const cajas = [];
  filas.forEach(([et, y, items, color], f) => {
    const etq = nuevo("div", "etiqueta", et, cel, `position:absolute;left:40px;top:${y - 34}px`);
    const ancho = (1320 - 24 * (items.length - 1)) / items.length;
    const fila = items.map(([id, i, t, s], k) => caja(id, 40 + k * (ancho + 24), y, ancho, i, t, s, color));
    subir([etq, ...fila], (D.explicar ? m(f) : 0.5 + f * 0.25) + 0.3, { stagger: 0.08 });
    cajas.push(...fila);
  });
  // flechas: pantallas → yarbys → servicios
  flecha(840, 300 + 166, 840, 300 + 296, (D.explicar ? m(1) : 1.0) + 0.4, C.suave, 3);
  flecha(840, 300 + 396, 840, 300 + 526, (D.explicar ? m(2) : 1.2) + 0.4, C.suave, 3);
  if (D.explicar) {
    // Recorrido por las capas y la regla: las pantallas solo hablan con Yarbys
    const regla = nuevo("div", "pastilla", `${ico("shield-check", 26, C.verde)}Las pantallas solo hablan con Yarbys`, cel, `position:absolute;right:40px;top:240px;font-size:22px;color:${C.verde}`);
    pop(regla, m(3));
    cajas.filter((c) => c.dataset.id === "yarbys").forEach((c) => resaltar(c, m(3), C.verde));
  } else {
    const tHoy = m(1);
    cajas.forEach((c) => {
      const id = c.dataset.id;
      if (hoy.has(id)) {
        resaltar(c, tHoy, C.amarillo);
        const b = nuevo("div", "", "Hoy", c, `position:absolute;right:-12px;top:-14px;padding:3px 12px;border-radius:99px;background:${C.amarillo};color:#1b1b1b;font:800 16px 'Open Sans'`);
        pop(b, tHoy + 0.2);
      } else if (!hechos.has(id)) {
        apagar(c, tHoy, 0.3);
      } else {
        const b = nuevo("div", "", ico("check", 18, "#fff"), c, `position:absolute;right:-10px;top:-12px;width:30px;height:30px;border-radius:50%;background:${C.verde};display:grid;place-items:center`);
        pop(b, tHoy + 0.2);
      }
    });
  }
  salida();
};

// Cierre de cada video: lo que logramos y lo que sigue
ESCENAS.siguiente = () => {
  const D = DATOS;
  formas(0);
  cabecera("Fin del video " + D.num, "circle-check", D.titulo || "¡Lo <span class='acento'>logramos</span>!");
  const lista = nuevo("div", "", "", esc, "position:absolute;left:140px;top:330px;width:880px;display:grid;gap:18px");
  const ls = D.logros.map((t) => nuevo("div", "panel", `<span class="cuadro-icono" style="width:52px;height:52px;background:${C.verde}26;color:${C.verde}">${ico("check", 30)}</span><span style="font:700 27px/1.3 Lato">${t}</span>`, lista, "position:relative;display:flex;align-items:center;gap:20px;padding:14px 22px"));
  subir(ls, 0.6, { stagger: 0.3 });
  if (D.sig) {
    const card = nuevo("div", "panel", `<div class="etiqueta" style="position:relative;color:${C.amarillo}">${ico("arrow-right", 22, C.amarillo)} En el próximo video</div>
        <div style="font:800 24px 'Open Sans';color:var(--suave);margin-top:22px">Video ${D.sig.num}</div>
        <div style="font:800 44px/1.15 'Open Sans';margin-top:6px">${D.sig.titulo}</div>
        <div style="font:400 26px/1.4 Lato;color:var(--suave);margin-top:16px">${D.sig.sub}</div>`, esc,
      `left:1100px;top:330px;width:680px;padding:34px 36px;border-color:${C.amarillo}`);
    pop(card, Math.min(m(1), 3.2));
  } else {
    const nu = nucleo3(esc, 1440, 560, 200, 1);
    dibujarAnillos(nu, m(1), 1.2);
  }
  salida();
};

// Los 9 videos del curso y lo que se ve funcionando al final de cada uno
ESCENAS.temario = () => {
  const D = DATOS;
  formas(1);
  cabecera("El curso", "list-checks", "9 videos, y en cada uno <span class='acento'>algo funciona</span>");
  const cs = D.videos.map(([t, r, i], k) => {
    const actual = D.actual === k + 1;
    return nuevo("div", "panel", `<div style="display:flex;align-items:center;gap:14px">
        <span style="width:46px;height:46px;border-radius:12px;display:grid;place-items:center;background:${actual ? C.amarillo : C.celeste + "26"};color:${actual ? "#1b1b1b" : C.celeste};font:800 24px 'Open Sans'">${k + 1}</span>
        <span style="font:800 25px/1.15 'Open Sans'">${t}</span></div>
        <div style="display:flex;align-items:center;gap:10px;margin-top:14px;font:400 20px/1.3 Lato;color:var(--suave)">${ico(i, 26, C.verde)}${r}</div>`,
      esc, `left:${140 + (k % 3) * 560}px;top:${300 + Math.floor(k / 3) * 230}px;width:530px;height:200px;padding:24px 26px;${actual ? `border-color:${C.amarillo}` : ""}`);
  });
  subir(cs.slice(0, 3), m(0) + 0.6, { stagger: 0.12 });
  subir(cs.slice(3, 6), m(1), { stagger: 0.12 });
  subir(cs.slice(6), m(2), { stagger: 0.12 });
  salida();
};
