/* Base de todas las escenas. Cada escena es una línea de tiempo de GSAP en pausa:
   el renderizador llama a window.seek(t) para cada fotograma.
   window.__CFG trae: dur (s), marcas (inicio de cada frase), subs, cap, n, caps, t0, total. */

const CFG = window.__CFG || { dur: 14, marcas: [0.7, 4, 7, 10], subs: [], cap: "Vista previa", n: 1, caps: 1, t0: 0, total: 14 };
const ID = new URLSearchParams(location.search).get("id");
const DUR = CFG.dur;
const M = CFG.marcas;
const m = (i) => (i < M.length ? M[i] : DUR);   // inicio de la frase i
const NS = "http://www.w3.org/2000/svg";

gsap.registerPlugin(SplitText, DrawSVGPlugin);
const tl = gsap.timeline({ paused: true });
const esc = document.querySelector("#escena");
const CUADRO = [];   // animaciones continuas: funciones f(t) que se llaman en cada fotograma

// ------------------------------------------------------------- DOM
function nuevo(tag, clase, html, padre = esc, estilo = "") {
  const e = document.createElement(tag);
  if (clase) e.className = clase;
  if (html !== undefined && html !== null) e.innerHTML = html;
  if (estilo) e.style.cssText = estilo;
  padre.appendChild(e);
  return e;
}
const emo = (e, tam = 48) => `<span class="emo" style="font-size:${tam}px">${e}</span>`;

function cabecera(kicker, html, sub) {
  const c = nuevo("div", "cabecera");
  const k = nuevo("div", "kicker", kicker, c);
  const h = nuevo("h1", "titulo", html, c);
  const s = sub ? nuevo("div", "subtitulo", sub, c) : null;
  const split = new SplitText(h, { type: "lines,words", linesClass: "linea-titulo" });
  tl.from(k, { y: 20, opacity: 0, duration: 0.5, ease: "power3.out" }, 0.1);
  tl.from(split.words, { yPercent: 110, duration: 0.8, stagger: 0.05, ease: "power4.out" }, 0.2);
  if (s) tl.from(s, { y: 20, opacity: 0, duration: 0.6, ease: "power3.out" }, 0.6);
  return c;
}
function salida() {
  tl.to(esc, { opacity: 0, duration: 0.45, ease: "power2.in" }, DUR - 0.45);
}
function entrada() {
  tl.from(esc, { opacity: 0, duration: 0.4, ease: "power1.out" }, 0);
}
function pop(elems, t, extra = {}) {
  tl.from(elems, { scale: 0.6, opacity: 0, duration: 0.6, ease: "back.out(1.8)", stagger: 0.08, transformOrigin: "50% 50%", ...extra }, t);
}
function subir(elems, t, extra = {}) {
  tl.from(elems, { y: 40, opacity: 0, duration: 0.7, ease: "power3.out", stagger: 0.1, ...extra }, t);
}
function aparecer(elems, t, dur = 0.6) {
  tl.from(elems, { opacity: 0, duration: dur, ease: "power1.out" }, t);
}
function resaltar(elem, t, color = "var(--oro)") {
  tl.to(elem, { borderColor: color, boxShadow: `0 0 0 3px ${color}, 0 24px 70px rgba(0,0,0,.4)`, duration: 0.45, ease: "power2.out" }, t);
}
function normal(elem, t) {
  tl.to(elem, { borderColor: "rgba(255,255,255,.12)", boxShadow: "0 24px 70px rgba(0,0,0,.35)", duration: 0.45 }, t);
}
function apagar(elem, t, op = 0.3) {
  tl.to(elem, { opacity: op, duration: 0.5 }, t);
}
function encender(elem, t) {
  tl.to(elem, { opacity: 1, duration: 0.5 }, t);
}

// Lista de pasos numerados; el paso k aparece con la frase marcas[k]
function pasos(items, x, y, ancho, marcas, padre = esc) {
  const caja = nuevo("div", "pasos", "", padre, `left:${x}px;top:${y}px;width:${ancho}px`);
  const filas = items.map((txt, i) => nuevo("div", "paso", `<div class="num">${i + 1}</div><div class="txt">${txt}</div>`, caja));
  filas.forEach((f, i) => {
    tl.from(f, { x: -40, opacity: 0, duration: 0.6, ease: "power3.out" }, marcas[i]);
    if (i > 0) resaltar(f, marcas[i] + 0.1);
    if (i > 0) normal(filas[i - 1], marcas[i]);
  });
  if (filas.length) resaltar(filas[0], marcas[0] + 0.1);
  return filas;
}

// Tarjeta de material o herramienta: dibujo + nombre + detalle
function item(padre, dibujo, nombre, detalle = "", cant = "") {
  return nuevo("div", "item",
    `<div class="dib">${dibujo}</div><div><div class="nom">${cant ? `<span class="cant">${cant}</span> ` : ""}${nombre}</div>${detalle ? `<div class="det">${detalle}</div>` : ""}</div>`, padre);
}

// ------------------------------------------------------------- SVG
function svg(x, y, w, h, padre = esc, vb) {
  const s = document.createElementNS(NS, "svg");
  s.setAttribute("width", w); s.setAttribute("height", h);
  s.setAttribute("viewBox", vb || `0 0 ${w} ${h}`);
  s.style.cssText = `position:absolute;left:${x}px;top:${y}px;overflow:visible`;
  padre.appendChild(s);
  return s;
}
function el(tag, attrs = {}, padre) {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "text") e.textContent = v;
    else e.setAttribute(k, v);
  }
  if (padre) padre.appendChild(e);
  return e;
}
const g = (padre, attrs = {}) => el("g", attrs, padre);
function texto(padre, x, y, t, clase = "lbl", anchor = "start", extra = {}) {
  return el("text", { x, y, class: clase, "text-anchor": anchor, ...extra, text: t }, padre);
}
function linea(padre, x1, y1, x2, y2, color = "#cfe0ff", ancho = 2.5, extra = {}) {
  return el("line", { x1, y1, x2, y2, stroke: color, "stroke-width": ancho, "stroke-linecap": "round", ...extra }, padre);
}
function camino(padre, d, color = "#cfe0ff", ancho = 2.5, relleno = "none", extra = {}) {
  return el("path", { d, stroke: color, "stroke-width": ancho, fill: relleno, "stroke-linecap": "round", "stroke-linejoin": "round", ...extra }, padre);
}

// Línea de cota con flechas y medida en el centro
function cota(padre, x1, y1, x2, y2, t, desplaz = 0, color = "#fcb333") {
  const gr = g(padre);
  const ang = Math.atan2(y2 - y1, x2 - x1);
  const nx = -Math.sin(ang) * desplaz, ny = Math.cos(ang) * desplaz;
  const a = [x1 + nx, y1 + ny], b = [x2 + nx, y2 + ny];
  if (desplaz) {
    linea(gr, x1, y1, a[0] + Math.sign(desplaz) * -Math.sin(ang) * 8, a[1] + Math.sign(desplaz) * Math.cos(ang) * 8, color, 1.5, { opacity: 0.6 });
    linea(gr, x2, y2, b[0] + Math.sign(desplaz) * -Math.sin(ang) * 8, b[1] + Math.sign(desplaz) * Math.cos(ang) * 8, color, 1.5, { opacity: 0.6 });
  }
  linea(gr, a[0], a[1], b[0], b[1], color, 2.2);
  const punta = (p, s) => {
    const dx = Math.cos(ang) * 13 * s, dy = Math.sin(ang) * 13 * s;
    const px = -Math.sin(ang) * 6, py = Math.cos(ang) * 6;
    el("path", { d: `M${p[0]},${p[1]} L${p[0] + dx + px},${p[1] + dy + py} L${p[0] + dx - px},${p[1] + dy - py} Z`, fill: color }, gr);
  };
  punta(a, 1); punta(b, -1);
  const cx = (a[0] + b[0]) / 2, cy = (a[1] + b[1]) / 2;
  const vertical = Math.abs(Math.sin(ang)) > 0.7;
  const tw = t.length * 12 + 18;
  if (vertical) {
    el("rect", { x: cx - tw / 2, y: cy - 16, width: tw, height: 32, rx: 9, fill: "#0b1528", stroke: color, "stroke-width": 1.5 }, gr);
    texto(gr, cx, cy + 7, t, "cota-t", "middle");
  } else {
    el("rect", { x: cx - tw / 2, y: cy - 16, width: tw, height: 32, rx: 9, fill: "#0b1528", stroke: color, "stroke-width": 1.5 }, gr);
    texto(gr, cx, cy + 7, t, "cota-t", "middle");
  }
  return gr;
}

// Etiqueta con línea guía: punto (x,y) -> texto en (tx,ty)
function etiqueta(padre, x, y, tx, ty, t, sub = "", color = "#fcb333") {
  const gr = g(padre);
  const izq = tx < x;
  camino(gr, `M${x},${y} L${tx + (izq ? 12 : -12)},${ty}`, color, 2);
  el("circle", { cx: x, cy: y, r: 6, fill: color }, gr);
  el("circle", { cx: x, cy: y, r: 12, fill: "none", stroke: color, "stroke-width": 1.5, opacity: 0.5 }, gr);
  const ancla = izq ? "end" : "start";
  const t1 = texto(gr, tx, ty + 7, t, "lbl", ancla);
  const t2 = sub ? texto(gr, tx, ty + 34, sub, "lbl-s", ancla) : null;
  // fondo oscuro detrás del texto, para que se lea sobre cualquier dibujo
  const cajas = [t1, t2].filter(Boolean).map((e) => e.getBBox());
  const x1 = Math.min(...cajas.map((b) => b.x)), y1 = Math.min(...cajas.map((b) => b.y));
  const x2 = Math.max(...cajas.map((b) => b.x + b.width)), y2 = Math.max(...cajas.map((b) => b.y + b.height));
  gr.insertBefore(el("rect", { x: x1 - 10, y: y1 - 5, width: x2 - x1 + 20, height: y2 - y1 + 10, rx: 9, fill: "rgba(8,14,28,.82)" }), t1);
  return gr;
}

function flecha(padre, x1, y1, x2, y2, color = "#fcb333", ancho = 3) {
  const gr = g(padre);
  linea(gr, x1, y1, x2, y2, color, ancho);
  const ang = Math.atan2(y2 - y1, x2 - x1);
  const a = 16, b = 8;
  el("path", { d: `M${x2},${y2} L${x2 - Math.cos(ang) * a - Math.sin(ang) * b},${y2 - Math.sin(ang) * a + Math.cos(ang) * b} L${x2 - Math.cos(ang) * a + Math.sin(ang) * b},${y2 - Math.sin(ang) * a - Math.cos(ang) * b} Z`, fill: color }, gr);
  return gr;
}

// Dibuja un trazo SVG progresivamente
function trazar(elems, t, dur = 1.0) {
  tl.from(elems, { drawSVG: "0%", duration: dur, ease: "power2.inOut", stagger: 0.1 }, t);
}

// Gradientes y filtros con id único por documento
let _ids = 0;
function uid(p = "id") { return `${p}${++_ids}`; }
function defs(s) {
  let d = s.querySelector("defs");
  if (!d) d = el("defs", {}, s);
  return d;
}
function gradRadial(s, paradas, extra = {}) {
  const id = uid("gr");
  const gr = el("radialGradient", { id, ...extra }, defs(s));
  paradas.forEach(([o, c, op = 1]) => el("stop", { offset: o, "stop-color": c, "stop-opacity": op }, gr));
  return `url(#${id})`;
}
function gradLineal(s, paradas, x1 = 0, y1 = 0, x2 = 0, y2 = 1) {
  const id = uid("gl");
  const gr = el("linearGradient", { id, x1, y1, x2, y2 }, defs(s));
  paradas.forEach(([o, c, op = 1]) => el("stop", { offset: o, "stop-color": c, "stop-opacity": op }, gr));
  return `url(#${id})`;
}
function filtroBrillo(s, desv = 6) {
  const id = uid("fb");
  const f = el("filter", { id, x: "-100%", y: "-100%", width: "300%", height: "300%" }, defs(s));
  el("feGaussianBlur", { stdDeviation: desv, result: "b" }, f);
  const mg = el("feMerge", {}, f);
  el("feMergeNode", { in: "b" }, mg);
  el("feMergeNode", { in: "SourceGraphic" }, mg);
  return `url(#${id})`;
}

// Números pseudoaleatorios repetibles (para que cada render sea idéntico)
function azar(semilla) {
  let s = semilla >>> 0;
  return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
}

// ------------------------------------------------------------- MARCO: nieve, barra, capítulo, subtítulos
const COPOS = [];
(function nieve() {
  const r = azar(7);
  const caja = document.querySelector("#copos");
  for (let i = 0; i < 70; i++) {
    const tam = 2 + r() * 5;
    const c = nuevo("div", "copo", "", caja, `width:${tam}px;height:${tam}px;opacity:${0.15 + r() * 0.45};filter:blur(${tam > 5 ? 1 : 0}px)`);
    COPOS.push({ c, x: r() * 1920, fase: r(), periodo: 14 + r() * 16, deriva: 20 + r() * 50, f2: r() * 6.28 });
  }
})();
document.querySelector("#capitulo").innerHTML = CFG.cap ? `<b>${CFG.n}/${CFG.caps}</b> · ${CFG.cap}` : "";
const SUB = document.querySelector("#sub span");
let _subActual = null;

function marco(t) {
  const global = CFG.t0 + t;
  for (const k of COPOS) {
    const p = (global / k.periodo + k.fase) % 1;
    k.c.style.transform = `translate(${k.x + Math.sin(global * 0.4 + k.f2) * k.deriva}px, ${-20 + p * 1120}px)`;
  }
  document.querySelector("#avance").style.width = `${(global / CFG.total) * 100}%`;
  let s = "";
  for (const [a, b, txt] of CFG.subs) if (t >= a && t < b) s = txt;
  if (s !== _subActual) { SUB.textContent = s; _subActual = s; }
}

// ------------------------------------------------------------- arranque
const ESCENAS = {};
function iniciar() {
  document.fonts.ready.then(() => {
    entrada();
    (ESCENAS[ID] || ESCENAS.portada)();
    tl.seek(0);
    window.seek(0);
    window.__listo = true;
  });
}
window.seek = (t) => {
  t = Math.max(0, Math.min(t, DUR));
  tl.seek(t, false);
  for (const f of CUADRO) f(t);
  marco(t);
  return 0;
};
