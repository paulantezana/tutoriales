/* Escenas animadas del curso (estilo plano y oscuro, sin degradados).
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

// Portada de cada video: número, título, qué se hace hoy y el resultado.
// DATOS: {num, total, titulo (html), sub, puntos: [[icono, texto]], resultado, icono}
// Frases: 0 saludo · 1 "hoy vamos a..." · 2 "al final del video..."
ESCENAS.portada = () => {
  const D = DATOS;
  formas(0);
  const col = nuevo("div", "", "", esc, "position:absolute;left:140px;top:130px;width:1040px;display:flex;flex-direction:column;gap:18px");
  const k = nuevo("div", "kicker", `${ico("clapperboard", 24)}${D.curso || "Curso"} · Video ${D.num} de ${D.total}`, col, "position:relative;align-self:flex-start");
  const h = nuevo("h1", "titulo", D.titulo, col, "position:relative;margin:0");
  const sp = new SplitText(h, { type: "lines,words", linesClass: "linea-titulo" });
  tl.from(k, { y: 20, opacity: 0, duration: 0.5 }, 0.1);
  tl.from(sp.words, { yPercent: 110, duration: 0.8, stagger: 0.05, ease: "power4.out" }, 0.25);
  const sub = nuevo("div", "subtitulo", D.sub || "", col, "position:relative;margin:0");
  subir(sub, 0.7);
  nuevo("div", "etiqueta", "Hoy vamos a", col, "position:relative;margin-top:18px");
  const ps = D.puntos.map(([i, t]) => nuevo("div", "panel", `${ico(i, 34, C.celeste)}<span style="font:700 27px Lato">${t}</span>`, col, "position:relative;display:flex;align-items:center;gap:18px;padding:14px 22px;width:900px"));
  subir(ps, m(1), { stagger: 0.35 });
  const res = nuevo("div", "panel", `<div class="etiqueta" style="position:relative;color:${C.verde}">${ico("circle-check", 22, C.verde)} Al final del video</div>
      <div style="display:flex;align-items:center;gap:20px;margin-top:18px">${ico(D.icono || "monitor", 64, C.amarillo)}
      <div style="font:800 32px/1.25 'Open Sans'">${D.resultado}</div></div>`, esc,
    `left:1250px;top:560px;width:540px;padding:28px 30px;border-color:${C.verde}`);
  pop(res, m(2));
  salida();
};

// El temario: todos los videos del curso y lo que se ve funcionando al final de cada uno.
// DATOS: {videos: [[titulo, resultado, icono]], actual}   Frases: los videos aparecen en 3 tandas (m0, m1, m2)
ESCENAS.temario = () => {
  const D = DATOS;
  formas(1);
  cabecera("El curso", "list-checks", `${D.videos.length} videos, y en cada uno <span class='acento'>algo funciona</span>`);
  const n = D.videos.length, cols = n <= 4 ? 2 : 3, filas = Math.ceil(n / cols);
  const w = cols === 3 ? 530 : 800, h = Math.min(200, (700 - 30 * (filas - 1)) / filas);
  const cs = D.videos.map(([t, r, i], k) => {
    const actual = D.actual === k + 1;
    return nuevo("div", "panel", `<div style="display:flex;align-items:center;gap:14px">
        <span style="width:46px;height:46px;border-radius:12px;display:grid;place-items:center;flex:none;background:${actual ? C.amarillo : C.celeste + "26"};color:${actual ? "#1b1b1b" : C.celeste};font:800 24px 'Open Sans'">${k + 1}</span>
        <span style="font:800 25px/1.15 'Open Sans'">${t}</span></div>
        <div style="display:flex;align-items:center;gap:10px;margin-top:12px;font:400 20px/1.3 Lato;color:var(--suave)">${ico(i, 26, C.verde)}${r}</div>`,
      esc, `left:${140 + (k % cols) * (w + 30)}px;top:${300 + Math.floor(k / cols) * (h + 30)}px;width:${w}px;height:${h}px;padding:22px 26px;${actual ? `border-color:${C.amarillo}` : ""}`);
  });
  const t1 = Math.ceil(n / 3), t2 = Math.ceil((2 * n) / 3);
  subir(cs.slice(0, t1), m(0) + 0.6, { stagger: 0.12 });
  subir(cs.slice(t1, t2), m(1), { stagger: 0.12 });
  subir(cs.slice(t2), m(2), { stagger: 0.12 });
  salida();
};

// Dónde estamos: las capas de la arquitectura; lo hecho (✓), lo de hoy (amarillo) y lo que falta (apagado).
// DATOS: {capas: [{etiqueta, color, items: [[id, icono, titulo, archivo]]}], contenedor: [icono, texto],
//         hechos: [ids], hoy: [ids], kicker, titulo,
//         explicar: true → recorre las capas (una por frase) y al final muestra "regla" (otra frase)}
ESCENAS.mapa = () => {
  const D = DATOS;
  const hechos = new Set(D.hechos || []), hoy = new Set(D.hoy || []);
  formas(1);
  cabecera(D.kicker || "Dónde estamos", "map", D.titulo || "La <span class='acento'>arquitectura</span>");
  const cel = nuevo("div", "", "", esc, `position:absolute;left:140px;top:300px;width:1400px;height:680px;border:4px solid ${C.borde};border-radius:48px;background:#2b3035`);
  if (D.contenedor) nuevo("div", "pastilla", `${ico(D.contenedor[0], 28, C.celeste)}${D.contenedor[1]}`, cel, "position:absolute;left:40px;top:-28px;background:var(--fondo);font-size:22px;padding:8px 18px");
  aparecer(cel, 0.4);
  const n = D.capas.length, alto = 96;
  const ys = D.capas.map((_, f) => (n === 1 ? 290 : 70 + f * ((680 - 140 - alto) / (n - 1))));
  const cajas = [];
  D.capas.forEach((capa, f) => {
    const y = ys[f];
    const etq = nuevo("div", "etiqueta", capa.etiqueta, cel, `position:absolute;left:40px;top:${y - 34}px`);
    const ancho = (1320 - 24 * (capa.items.length - 1)) / capa.items.length;
    const fila = capa.items.map(([id, i, t, s], k) => {
      const e = nuevo("div", "panel", `${ico(i, 34, capa.color || C.celeste)}<div><div style="font:800 24px 'Open Sans'">${t}</div><div class="mono" style="font-size:16px;color:var(--suave)">${s || ""}</div></div>`,
        cel, `left:${40 + k * (ancho + 24)}px;top:${y}px;width:${ancho}px;height:${alto}px;display:flex;align-items:center;gap:14px;padding:0 20px`);
      e.dataset.id = id;
      return e;
    });
    subir([etq, ...fila], (D.explicar ? m(f) : 0.5 + f * 0.25) + 0.3, { stagger: 0.08 });
    cajas.push(...fila);
    if (f < n - 1) flecha(840, 300 + y + alto + 6, 840, 300 + ys[f + 1] - 40, (D.explicar ? m(f + 1) : 1.0 + f * 0.2) + 0.2, C.suave, 3);
  });
  if (D.explicar) {
    if (D.regla) {
      const regla = nuevo("div", "pastilla", `${ico("shield-check", 26, C.verde)}${D.regla}`, cel, `position:absolute;right:40px;top:${ys[Math.min(1, n - 1)] - 60}px;font-size:22px;color:${C.verde}`);
      pop(regla, m(n));
    }
  } else {
    const tHoy = m(1);
    cajas.forEach((c) => {
      const id = c.dataset.id;
      if (hoy.has(id)) {
        resaltar(c, tHoy, C.amarillo);
        pop(nuevo("div", "", "Hoy", c, `position:absolute;right:-12px;top:-14px;padding:3px 12px;border-radius:99px;background:${C.amarillo};color:#1b1b1b;font:800 16px 'Open Sans'`), tHoy + 0.2);
      } else if (!hechos.has(id)) {
        apagar(c, tHoy, 0.3);
      } else {
        pop(nuevo("div", "", ico("check", 18, "#fff"), c, `position:absolute;right:-10px;top:-12px;width:30px;height:30px;border-radius:50%;background:${C.verde};display:grid;place-items:center`), tHoy + 0.2);
      }
    });
  }
  salida();
};

// Teoría: un concepto con 2 a 4 tarjetas que aparecen una por frase.
// DATOS: {kicker, icono, titulo (html), sub, tarjetas: [[icono, titulo, texto, color]]}
// Frases: 0 introduce el concepto · 1..n una por tarjeta
ESCENAS.concepto = () => {
  const D = DATOS;
  formas(0);
  cabecera(D.kicker || "Concepto", D.icono || "lightbulb", D.titulo, D.sub);
  const n = D.tarjetas.length, cols = n === 4 ? 2 : n;
  const w = cols === 2 ? 790 : (1640 - 30 * (cols - 1)) / cols, h = n === 4 ? 290 : 420;
  const cs = D.tarjetas.map(([i, t, x, c], k) => nuevo("div", "panel", `
      <div class="cuadro-icono" style="width:76px;height:76px;background:${(c || C.celeste)}26;color:${c || C.celeste}">${ico(i, 42)}</div>
      <div style="font:800 32px/1.2 'Open Sans';margin-top:22px">${t}</div>
      <div style="font:400 25px/1.45 Lato;color:var(--suave);margin-top:12px">${x}</div>`,
    esc, `left:${140 + (k % cols) * (w + 30)}px;top:${D.sub ? 380 : 330 + Math.floor(k / cols) * (h + 30)}px;width:${w}px;height:${h}px;padding:34px`));
  cs.forEach((c, k) => { pop(c, m(k + 1)); resaltar(c, m(k + 1) + 0.2, D.tarjetas[k][3] || C.celeste); if (k + 1 < n) normal(c, m(k + 2)); });
  salida();
};

// Pasos numerados (instalación, un proceso, un algoritmo). Cada paso aparece y se resalta en su frase.
// DATOS: {kicker, icono, titulo, pasos: [[icono, titulo, texto]]}   Frases: una por paso
ESCENAS.pasos = () => {
  const D = DATOS;
  formas(1);
  cabecera(D.kicker || "Paso a paso", D.icono || "list-ordered", D.titulo);
  const n = D.pasos.length, h = Math.min(130, (700 - 18 * (n - 1)) / n);
  const ps = D.pasos.map(([i, t, x], k) => nuevo("div", "panel", `
      <span style="width:58px;height:58px;border-radius:50%;display:grid;place-items:center;flex:none;background:${C.celeste}26;color:${C.celeste};font:800 28px 'Open Sans'">${k + 1}</span>
      ${ico(i, 40, C.amarillo)}<div><div style="font:800 29px 'Open Sans'">${t}</div><div style="font:400 23px/1.35 Lato;color:var(--suave);margin-top:4px">${x || ""}</div></div>`,
    esc, `left:140px;top:${300 + k * (h + 18)}px;width:1640px;height:${h}px;display:flex;align-items:center;gap:26px;padding:0 30px`));
  ps.forEach((p, k) => { subir(p, m(k)); resaltar(p, m(k) + 0.3, C.amarillo); if (k + 1 < n) normal(p, m(k + 1)); });
  salida();
};

// Comparación lado a lado (antes/después, nube/local, con/sin...).
// DATOS: {kicker, icono, titulo, izq: {icono, titulo, color, puntos: []}, der: {...}}   Frases: 0 intro · 1 izquierda · 2 derecha
ESCENAS.comparar = () => {
  const D = DATOS;
  formas(0);
  cabecera(D.kicker || "Comparación", D.icono || "columns-2", D.titulo);
  const lado = (L, x) => nuevo("div", "panel", `
      <div style="display:flex;align-items:center;gap:18px">${ico(L.icono, 52, L.color || C.celeste)}<span style="font:800 36px 'Open Sans'">${L.titulo}</span></div>
      <div style="margin-top:24px;display:grid;gap:16px">${L.puntos.map((p) => `<div style="display:flex;gap:14px;font:400 26px/1.4 Lato">${ico(L.marca || "check", 30, L.color || C.celeste)}<span>${p}</span></div>`).join("")}</div>`,
    esc, `left:${x}px;top:330px;width:790px;height:620px;padding:40px;border-color:${L.color || C.borde}`);
  pop(lado(D.izq, 140), m(1));
  pop(lado(D.der, 990), m(2));
  salida();
};

// Cierre de cada video: lo que logramos y lo que sigue. Ningún video termina sin resultado ni de golpe.
// DATOS: {num, logros: [], sig: {num, titulo, sub}}  (sin "sig": último video del curso)
ESCENAS.siguiente = () => {
  const D = DATOS;
  formas(0);
  cabecera("Fin del video " + D.num, "circle-check", D.titulo || "¡Lo <span class='acento'>logramos</span>!");
  const lista = nuevo("div", "", "", esc, "position:absolute;left:140px;top:330px;width:880px;display:grid;gap:18px");
  const ls = D.logros.map((t) => nuevo("div", "panel", `<span class="cuadro-icono" style="width:52px;height:52px;background:${C.verde}26;color:${C.verde}">${ico("check", 30)}</span><span style="font:700 27px/1.3 Lato">${t}</span>`, lista, "position:relative;display:flex;align-items:center;gap:20px;padding:14px 22px"));
  subir(ls, 0.6, { stagger: 0.3 });
  const card = D.sig
    ? nuevo("div", "panel", `<div class="etiqueta" style="position:relative;color:${C.amarillo}">${ico("arrow-right", 22, C.amarillo)} En el próximo video</div>
        <div style="font:800 24px 'Open Sans';color:var(--suave);margin-top:22px">Video ${D.sig.num}</div>
        <div style="font:800 44px/1.15 'Open Sans';margin-top:6px">${D.sig.titulo}</div>
        <div style="font:400 26px/1.4 Lato;color:var(--suave);margin-top:16px">${D.sig.sub}</div>`, esc,
      `left:1100px;top:330px;width:680px;padding:34px 36px;border-color:${C.amarillo}`)
    : nuevo("div", "panel", `${ico("trophy", 96, C.amarillo)}<div style="font:800 44px/1.15 'Open Sans';margin-top:20px">¡Terminaste el curso!</div>
        <div style="font:400 26px/1.4 Lato;color:var(--suave);margin-top:14px">${D.cierre || "Ahora te toca a ti: modifícalo y hazlo tuyo."}</div>`, esc,
      `left:1100px;top:330px;width:680px;padding:40px 36px;border-color:${C.amarillo};text-align:center`);
  pop(card, Math.min(m(1), 3.2));
  salida();
};

// Despedida del canal. DATOS: {repo: "usuario/repositorio", nombre: "Tu nombre"}
ESCENAS.final = () => {
  const D = DATOS;
  const logo = nuevo("img", "", null, esc, "position:absolute;left:0;right:0;margin:auto;top:150px;width:220px;height:220px;object-fit:contain");
  logo.src = "../marca/logo.png";
  pop(logo, 0.1);
  const t = nuevo("div", "", "¡Gracias por ver!", esc, "position:absolute;left:0;right:0;top:420px;text-align:center;font:800 84px 'Open Sans'");
  const sp = new SplitText(t, { type: "chars" });
  tl.from(sp.chars, { yPercent: 80, opacity: 0, duration: 0.6, stagger: 0.03, ease: "back.out(1.7)" }, 0.3);
  if (D.repo) {
    const gh = nuevo("div", "pastilla", `${ico("si_github", 32)}<span>Código en GitHub: <span class="mono" style="color:${C.celeste}">${D.repo}</span></span>`, esc, "position:absolute;left:0;right:0;margin:auto;width:fit-content;top:570px");
    subir(gh, m(0) + 0.4);
  }
  const fila = nuevo("div", "", "", esc, "position:absolute;left:0;right:0;top:700px;display:flex;justify-content:center;gap:30px");
  const bs = [["thumbs-up", "Me gusta", C.azul], ["bell", "Suscríbete", C.rojo], ["message-circle", "Comenta", C.amarillo]].map(([i, x, c]) =>
    nuevo("div", "", `${ico(i, 38, "#fff")}<span>${x}</span>`, fila, `display:flex;gap:14px;align-items:center;padding:22px 40px;border-radius:999px;background:${c};font:800 34px 'Open Sans';color:${c === C.amarillo ? "#1b1b1b" : "#fff"}`));
  pop(bs, m(1), { stagger: 0.2 });
  tl.to(bs[1], { scale: 1.08, duration: 0.35, yoyo: true, repeat: 5, ease: "sine.inOut" }, m(1) + 1.2);
  if (D.nombre) subir(nuevo("div", "", D.nombre, esc, "position:absolute;left:0;right:0;top:870px;text-align:center;font:700 28px Lato;color:var(--suave);letter-spacing:.2em;text-transform:uppercase"), m(1) + 0.8);
  tl.to(esc, { opacity: 0, duration: 0.8 }, DUR - 0.8);
};

// ¿De dónde sale una URL? Pasos en una página y las partes del enlace (útil cuando la página real no se puede capturar).
// DATOS: {nombre, sitio, pasos: [[icono, titulo, texto]], url: [[texto, color, etiqueta]], nota}
ESCENAS.url = () => {
  const D = DATOS;
  formas(0);
  cabecera("¿De dónde sale la URL?", "link", `El enlace de <span class='acento'>${D.nombre}</span>`, D.sitio ? `Lo copiamos de ${D.sitio}` : "");
  const n = D.pasos.length, w = (1640 - 24 * (n - 1)) / n;
  const ps = D.pasos.map(([i, t, x], k) => nuevo("div", "panel", `<div class="cuadro-icono" style="width:60px;height:60px;background:${C.celeste}26;color:${C.celeste}">${ico(i, 32)}</div>
      <div style="font:800 26px 'Open Sans';margin-top:18px">${k + 1} · ${t}</div><div style="font:400 22px/1.35 Lato;color:var(--suave);margin-top:8px">${x}</div>`,
    esc, `left:${140 + k * (w + 24)}px;top:330px;width:${w}px;height:250px;padding:26px`));
  subir(ps, m(1) - 0.2, { stagger: 0.6 });
  const caja = nuevo("div", "panel", `<div class="etiqueta" style="position:relative">Las partes del enlace</div><div id="url-partes" class="mono" style="margin-top:22px;font-size:26px;line-height:2.4;word-break:break-all"></div>`, esc, "left:140px;top:620px;width:1640px;padding:28px 34px");
  const cont = caja.querySelector("#url-partes");
  const piezas = D.url.map(([t, c, e]) => nuevo("span", "", `${t}${e ? `<span style="position:absolute;left:0;top:30px;white-space:nowrap;font:700 18px Lato;color:${c}">${e}</span>` : ""}`, cont, `position:relative;color:${c || C.suave};border-bottom:3px solid ${c || "transparent"}`));
  subir(caja, m(2) - 0.4);
  aparecer(piezas, m(2), { stagger: 0.25 });
  if (D.nota) pop(nuevo("div", "pastilla", `${ico("info", 24, C.amarillo)}${D.nota}`, esc, "position:absolute;left:140px;top:960px;font-size:21px"), m(2) + 2);
  salida();
};

// ------------------------------------------------------------- arranque
document.fonts.ready.then(() => {
  (ESCENAS[ID] || (() => {}))();
  tl.seek(0);
  window.__listo = true;
});
window.seek = (t) => { tl.seek(Math.max(0, Math.min(t, DUR)), false); return 0; };
