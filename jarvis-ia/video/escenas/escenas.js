/* Escenas animadas del video. Cada escena es una línea de tiempo de GSAP en pausa:
   el renderizador llama a window.seek(t) para cada fotograma.
   Parámetros de la URL: id (escena), dur (segundos), m (inicio de cada frase, en segundos). */

const P = new URLSearchParams(location.search);
const ID = P.get("id");
const DUR = parseFloat(P.get("dur") || "10");
const M = (P.get("m") || "0").split(",").map(Number);
const LOGO = "../marca/logo.png";

gsap.registerPlugin(SplitText, DrawSVGPlugin, MotionPathPlugin);
const tl = gsap.timeline({ paused: true });
const esc = document.querySelector("#escena");

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
  const k = nuevo("div", "kicker", `${ico(icono, 22)}${kicker}`, c);
  const h = nuevo("h1", "titulo", html, c);
  const s = sub ? nuevo("div", "subtitulo", sub, c) : null;
  const split = new SplitText(h, { type: "lines,words", linesClass: "linea-titulo" });
  tl.from(k, { y: 20, opacity: 0, duration: 0.5, ease: "power3.out" }, 0.1);
  tl.from(split.words, { yPercent: 110, duration: 0.8, stagger: 0.05, ease: "power4.out" }, 0.2);
  if (s) tl.from(s, { y: 20, opacity: 0, duration: 0.6, ease: "power3.out" }, 0.6);
  return c;
}
function salida() {
  tl.to(esc, { opacity: 0, scale: 0.97, duration: 0.45, ease: "power2.in" }, DUR - 0.45);
}
function fondoVivo() {
  tl.to(".m1", { x: 220, y: 120, duration: DUR, ease: "sine.inOut" }, 0);
  tl.to(".m2", { x: -180, y: -90, duration: DUR, ease: "sine.inOut" }, 0);
  tl.to(".m3", { x: -260, y: 60, scale: 1.3, duration: DUR, ease: "sine.inOut" }, 0);
}
function pop(elems, t, extra = {}) {
  tl.from(elems, { scale: 0.6, opacity: 0, duration: 0.6, ease: "back.out(1.8)", stagger: 0.08, ...extra }, t);
}
function subir(elems, t, extra = {}) {
  tl.from(elems, { y: 40, opacity: 0, duration: 0.7, ease: "power3.out", stagger: 0.1, ...extra }, t);
}
function resaltar(elem, t, color = "var(--naranja)") {
  tl.to(elem, { borderColor: color, boxShadow: `0 0 0 3px ${color}, 0 30px 80px rgba(0,0,0,.4)`, scale: 1.04, duration: 0.5, ease: "power2.out" }, t);
}
function apagar(elem, t) {
  tl.to(elem, { opacity: 0.35, scale: 0.98, duration: 0.5 }, t);
}
function svg(w, h, padre, estilo = "") {
  const s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  s.setAttribute("width", w); s.setAttribute("height", h); s.setAttribute("viewBox", `0 0 ${w} ${h}`);
  s.style.cssText = "position:absolute;overflow:visible;" + estilo;
  padre.appendChild(s);
  return s;
}
function trazo(s, d, color = "rgba(255,255,255,.25)", ancho = 3, extra = "") {
  const p = document.createElementNS("http://www.w3.org/2000/svg", "path");
  p.setAttribute("d", d); p.setAttribute("fill", "none"); p.setAttribute("stroke", color);
  p.setAttribute("stroke-width", ancho); p.setAttribute("stroke-linecap", "round");
  if (extra) p.setAttribute("stroke-dasharray", extra);
  s.appendChild(p);
  return p;
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
function nodo(x, y, w, h, icono, titulo, sub, color, padre = esc) {
  const n = nuevo("div", "tarjeta", `
    <div style="display:flex;align-items:center;gap:18px">
      <div style="width:64px;height:64px;border-radius:18px;display:grid;place-items:center;background:${color}22;color:${color}">${ico(icono, 36)}</div>
      <div><div style="font-size:30px;font-weight:700">${titulo}</div><div style="font-size:21px;color:var(--suave);margin-top:4px">${sub}</div></div>
    </div>`, padre, `position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;padding:0 26px;display:flex;align-items:center`);
  return n;
}

// ------------------------------------------------------------- escenas
const ESCENAS = {};

ESCENAS.intro = () => {
  fondoVivo();
  // logo que se arma con sus "píxeles"
  const caja = nuevo("div", "", "", esc, "position:absolute;left:810px;top:250px;width:300px;height:300px");
  const logo = nuevo("img", "", null, caja, "width:300px;height:300px;filter:drop-shadow(0 30px 60px rgba(19,93,188,.6))");
  logo.src = LOGO;
  const brillo = nuevo("div", "anillo-brillo", "", caja, "inset:-24px;border-color:rgba(76,141,246,.6);box-shadow:0 0 60px rgba(76,141,246,.5)");
  tl.from(logo, { scale: 0, rotation: -120, duration: 1.1, ease: "back.out(1.6)" }, 0.15);
  tl.from(brillo, { scale: 0.4, opacity: 0, duration: 0.9, ease: "power3.out" }, 0.5);
  tl.to(brillo, { scale: 1.5, opacity: 0, duration: 1.2, ease: "power2.out" }, 1.4);
  const px = [[-260, -180, 54], [280, -120, 38], [-320, 140, 30], [300, 170, 46], [0, -260, 34]];
  px.forEach(([x, y, s], i) => {
    const c = nuevo("div", "", "", esc, `position:absolute;left:${960 - s / 2}px;top:${400 - s / 2}px;width:${s}px;height:${s}px;background:var(--naranja);border-radius:4px`);
    tl.fromTo(c, { x: 0, y: 0, scale: 0, opacity: 1 }, { x, y, scale: 1, rotation: 90 * (i % 2 ? 1 : -1), duration: 1.2, ease: "power3.out" }, 0.4 + i * 0.05);
    tl.to(c, { y: y - 40, opacity: 0, duration: 0.8, ease: "power2.in" }, 1.9 + i * 0.04);
  });
  // el logo sube y aparece el título
  tl.to(caja, { y: -120, scale: 0.55, duration: 1.0, ease: "power3.inOut" }, 2.0);
  const t1 = nuevo("div", "", "Crea tu propio", esc, "position:absolute;left:0;right:0;top:470px;text-align:center;font:600 46px 'Inter';color:var(--suave)");
  const t2 = nuevo("div", "", "JARVIS con <span style='color:var(--naranja)'>IA</span>", esc, "position:absolute;left:0;right:0;top:530px;text-align:center;font:900 150px 'Inter Display';letter-spacing:-0.03em;line-height:1");
  const sp = new SplitText(t2, { type: "chars" });
  tl.from(t1, { y: 30, opacity: 0, duration: 0.6, ease: "power3.out" }, 2.6);
  tl.from(sp.chars, { yPercent: 80, opacity: 0, rotationX: -90, duration: 0.8, stagger: 0.04, ease: "back.out(1.7)" }, 2.7);
  const fila = nuevo("div", "", "", esc, "position:absolute;left:0;right:0;top:740px;display:flex;justify-content:center;gap:22px");
  const rasgos = [["file-text", "Conoce tus datos"], ["history", "Recuerda las charlas"], ["audio-lines", "Te habla con voz"], ["globe", "Página web"]];
  const ps = rasgos.map(([i, t]) => nuevo("div", "pastilla", `${ico(i, 30, "var(--naranja)")}${t}`, fila));
  pop(ps, Math.max(3.4, m(1)), { stagger: 0.15 });
  const fila2 = nuevo("div", "", "", esc, "position:absolute;left:0;right:0;top:860px;display:flex;justify-content:center;gap:40px;align-items:center;color:#b7c3dc");
  const stack = [["si_python", "Python"], ["si_langchain", "LangChain"], ["si_ollama", "Ollama"], ["si_qdrant", "Qdrant"], ["si_postgresql", "PostgreSQL"], ["si_fastapi", "FastAPI"]];
  const ss = stack.map(([i, t]) => nuevo("div", "", `${ico(i, 34)}<span style="font-size:24px;font-weight:600">${t}</span>`, fila2, "display:flex;gap:12px;align-items:center"));
  const win = nuevo("div", "pastilla", `${ico("laptop", 30, "var(--azul-claro)")}Windows · sin Docker`, esc, "position:absolute;right:120px;top:90px;border-color:rgba(76,141,246,.5)");
  subir(ss, Math.max(4.2, m(2)), { stagger: 0.08 });
  pop(win, Math.max(4.4, m(2) + 0.4));
  salida();
};

ESCENAS.piezas = () => {
  fondoVivo();
  cabecera("El plan", "layers", "Las <span class='acento'>5 piezas</span> de JARVIS");
  const piezas = [
    ["brain", "Cerebro", "LLM · GPT-6 Luna", "#fcb333"],
    ["binary", "Embeddings", "Ollama · bge-m3", "#e5e7eb"],
    ["scan-search", "Búsqueda", "Qdrant", "#f87171"],
    ["history", "Memoria", "PostgreSQL", "#4c8df6"],
    ["app-window", "Página web", "FastAPI + HTML", "#4ade80"],
  ];
  const fila = nuevo("div", "", "", esc, "position:absolute;left:120px;right:120px;top:400px;display:grid;grid-template-columns:repeat(5,1fr);gap:28px");
  const cards = piezas.map(([i, t, s, c], k) => nuevo("div", "tarjeta", `
      <div style="width:110px;height:110px;border-radius:30px;margin:0 auto;display:grid;place-items:center;background:${c}1f;color:${c}">${ico(i, 60)}</div>
      <div style="margin-top:28px;font-size:23px;color:var(--suave);font-weight:600">PIEZA ${k + 1}</div>
      <div style="margin-top:6px;font-size:40px;font-weight:800">${t}</div>
      <div style="margin-top:10px;font-size:25px;color:#c9d4ea">${s}</div>`, fila, "padding:44px 20px;text-align:center"));
  const tiempos = [m(1), m(1) + 2.4, m(2), m(2) + 2.6, m(3)];
  cards.forEach((c, k) => subir(c, tiempos[k]));
  const lc = nuevo("div", "tarjeta", `${ico("si_langchain", 44, "#7ee0b5")}<span style="font-size:32px;font-weight:700">LangChain</span><span style="font-size:26px;color:var(--suave)">el pegamento que une todas las piezas</span>`, esc,
    "position:absolute;left:120px;right:120px;top:830px;height:110px;display:flex;align-items:center;justify-content:center;gap:22px;border-color:rgba(126,224,181,.4)");
  tl.from(lc, { scaleX: 0.2, opacity: 0, duration: 0.8, ease: "power3.out" }, m(3) + 1.8);
  salida();
};

ESCENAS.llm = () => {
  fondoVivo();
  cabecera("Pieza 1 · El cerebro", "brain", "¿Qué es un <span class='acento'>LLM</span>?", "Un modelo de lenguaje: una IA que entiende y escribe texto");
  const pregunta = nuevo("div", "burbuja tu", "¿Qué tengo el miércoles?", esc, "left:120px;top:520px");
  subir(pregunta, m(1));
  // tokens
  const tok = nuevo("div", "", "", esc, "position:absolute;left:120px;top:660px;width:720px");
  const piezas = ["¿Qué", " tengo", " el", " miér", "coles", "?"];
  const ts = piezas.map((p) => nuevo("span", "token", p.replace(" ", "␣"), tok));
  pop(ts, m(1) + 1.6, { stagger: 0.12 });
  const et = nuevo("div", "", "tokens = pedacitos de texto", esc, "position:absolute;left:126px;top:790px;font-size:24px;color:var(--suave)");
  subir(et, m(1) + 2.4);
  // el modelo
  const chip = nuevo("div", "tarjeta", `${ico("brain-circuit", 110, "var(--naranja)")}<div style="font:800 46px 'Inter Display';margin-top:14px">LLM</div><div style="font-size:24px;color:var(--suave)">GPT-6 Luna</div>`, esc,
    "position:absolute;left:880px;top:430px;width:300px;height:330px;display:grid;place-items:center;align-content:center;border-color:rgba(252,179,51,.45);box-shadow:0 0 80px rgba(252,179,51,.25)");
  pop(chip, m(1) + 0.6);
  ts.forEach((t, i) => tl.to(t, { x: 820 - t.offsetLeft, y: -40 + (i % 3) * 30, scale: 0.3, opacity: 0, duration: 0.6, ease: "power2.in" }, m(1) + 3.6 + i * 0.08));
  tl.to(chip, { scale: 1.08, duration: 0.25, yoyo: true, repeat: 3, ease: "sine.inOut" }, m(1) + 4.2);
  // respuesta token a token
  const resp = nuevo("div", "burbuja ia", "", esc, "left:1240px;top:500px;width:560px;min-height:120px");
  const textoResp = "Tienes que entregar el proyecto de la tienda online antes de las 6 p. m.";
  tl.from(resp, { opacity: 0, x: -30, duration: 0.4 }, m(1) + 4.6);
  escribir(resp, textoResp, m(1) + 4.8, 22);
  // proveedores
  const prov = nuevo("div", "", "", esc, "position:absolute;left:120px;right:120px;top:880px;display:flex;justify-content:center;gap:26px");
  const lista = [["sparkles", "ChatGPT", "#e5e7eb"], ["si_claude", "Claude", "#d97757"], ["si_googlegemini", "Gemini", "#8ab4f8"], ["si_deepseek", "DeepSeek", "#6b8bff"], ["si_qwen", "Qwen", "#a78bfa"], ["si_meta", "Llama", "#60a5fa"], ["si_mistralai", "Mistral", "#fb923c"]];
  const pv = lista.map(([i, t, c]) => nuevo("div", "pastilla", `${ico(i, 30, c)}${t}`, prov));
  pop(pv, m(2) + 0.3, { stagger: 0.12 });
  salida();
};

ESCENAS.comparativa = () => {
  fondoVivo();
  cabecera("Artificial Analysis · octubre 2026", "gauge", "Inteligencia <span class='acento'>vs</span> precio");
  const X0 = 300, Y0 = 920, W = 1180, H = 600;               // área del gráfico
  const xmin = Math.log10(0.3), xmax = Math.log10(30), ymin = 30, ymax = 62;
  const px = (p) => X0 + ((Math.log10(p) - xmin) / (xmax - xmin)) * W;
  const py = (v) => Y0 - ((v - ymin) / (ymax - ymin)) * H;
  const s = svg(1920, 1080, esc, "left:0;top:0");
  const ejes = [trazo(s, `M${X0} ${Y0 - H - 20} L${X0} ${Y0} L${X0 + W + 20} ${Y0}`, "rgba(255,255,255,.35)", 3)];
  [0.5, 1, 2, 5, 10, 20].forEach((p) => {
    const g = trazo(s, `M${px(p)} ${Y0} L${px(p)} ${Y0 - H}`, "rgba(255,255,255,.07)", 2, "6 8");
    ejes.push(g);
    nuevo("div", "eje-x", `$${p}`, esc, `position:absolute;left:${px(p) - 40}px;width:80px;top:${Y0 + 14}px;text-align:center;font-size:22px;color:var(--suave)`);
  });
  [35, 40, 45, 50, 55, 60].forEach((v) => {
    ejes.push(trazo(s, `M${X0} ${py(v)} L${X0 + W} ${py(v)}`, "rgba(255,255,255,.07)", 2, "6 8"));
    nuevo("div", "eje-y", `${v}`, esc, `position:absolute;left:${X0 - 70}px;width:50px;top:${py(v) - 14}px;text-align:right;font-size:22px;color:var(--suave)`);
  });
  tl.from(ejes, { drawSVG: 0, duration: 1.0, stagger: 0.03, ease: "power2.inOut" }, m(0) + 0.2);
  tl.from(".eje-x, .eje-y", { opacity: 0, duration: 0.5, stagger: 0.02 }, m(0) + 0.6);
  const lx = nuevo("div", "", `Precio por millón de tokens de salida (USD) →`, esc, `position:absolute;left:${X0}px;width:${W}px;top:${Y0 + 52}px;text-align:center;font-size:24px;font-weight:600;color:#c9d4ea`);
  const ly = nuevo("div", "", `Inteligencia →`, esc, `position:absolute;left:${X0 - 190}px;top:${Y0 - H / 2}px;font-size:24px;font-weight:600;color:#c9d4ea;transform:rotate(-90deg)`);
  subir([ly], m(0) + 1.2); subir([lx], m(0) + 1.8);

  const modelos = [
    // nombre, inteligencia, precio salida, color, lado etiqueta, frase en que aparece
    ["Claude Opus 5.5", 58, 20, "#d97757", "izq", 1],
    ["Claude Sonnet 5.5", 56, 10, "#d97757", "izq", 1],
    ["Gemini 4 Argon*", 53, 10, "#8ab4f8", "der", 1],
    ["GPT-6 Sol", 48, 10, "#e5e7eb", "der", 1],
    ["DeepSeek V4.1 Flash", 39, 1.2, "#6b8bff", "der", 2],
    ["Claude Haiku 5.5", 43, 0.5, "#d97757", "der", 3],
    ["GPT-6 Luna", 38, 0.5, "#fcb333", "abajo", 2],
  ];
  const puntos = {};
  modelos.forEach(([n, v, p, c, lado, f], k) => {
    const x = px(p), y = py(v), luna = n === "GPT-6 Luna";
    const r = luna ? 18 : 13;
    const d = nuevo("div", "", "", esc, `position:absolute;left:${x - r}px;top:${y - r}px;width:${2 * r}px;height:${2 * r}px;border-radius:50%;background:${c};box-shadow:0 0 ${luna ? 40 : 18}px ${c}`);
    const pos = lado === "der" ? `top:${y - 18}px;left:${x + r + 14}px` : lado === "izq" ? `top:${y - 18}px;right:${1920 - x + r + 14}px` : `top:${y + 52}px;left:${x - 110}px;width:220px;text-align:center`;
    const et = nuevo("div", "", `<b${luna ? ' style="color:var(--naranja)"' : ""}>${n}</b> <span style="color:var(--suave)">${v} · $${p}</span>`, esc,
      `position:absolute;${pos};font-size:24px;white-space:nowrap`);
    const t0 = m(f) + (f === 1 ? 0.8 + k * 0.5 : f === 2 ? (luna ? 2.2 : 0.4) : 0.4);
    pop(d, t0); tl.from(et, { opacity: 0, x: lado === "der" ? -14 : 14, duration: 0.5 }, t0 + 0.15);
    puntos[n] = { d, et, x, y };
  });
  // resaltar GPT-6 Luna
  const L = puntos["GPT-6 Luna"];
  const anillo = nuevo("div", "anillo-brillo", "", esc, `left:${L.x - 44}px;top:${L.y - 44}px;width:88px;height:88px`);
  tl.from(anillo, { scale: 0, opacity: 0, duration: 0.6, ease: "back.out(2)" }, m(2) + 2.6);
  tl.to(anillo, { scale: 1.25, duration: 0.7, yoyo: true, repeat: 5, ease: "sine.inOut" }, m(2) + 3.2);
  const veces = nuevo("div", "tarjeta", `<div style="font-size:24px;color:var(--suave)">GPT-6 Luna vs Claude Opus 5.5</div><div style="font:900 84px 'Inter Display';color:var(--naranja);line-height:1.05"><span id="x40">40</span>× más barato</div><div style="font-size:24px;color:var(--suave)">por token de salida ($0.50 vs $20)</div>`, esc,
    "position:absolute;left:1250px;top:690px;width:560px;padding:28px 34px;border-color:rgba(252,179,51,.4)");
  subir(veces, m(2) + 4.2); contador(veces.querySelector("#x40"), m(2) + 4.3, 1, 40, 1.4);
  tl.to(veces, { opacity: 0, y: 20, duration: 0.4 }, m(3) - 0.3);
  // Haiku
  const H5 = puntos["Claude Haiku 5.5"];
  const anH = nuevo("div", "anillo-brillo", "", esc, `left:${H5.x - 36}px;top:${H5.y - 36}px;width:72px;height:72px;border-color:#d97757;box-shadow:0 0 30px rgba(217,119,87,.7)`);
  tl.from(anH, { scale: 0, opacity: 0, duration: 0.6, ease: "back.out(2)" }, m(3) + 0.6);
  tl.to(anH, { opacity: 0, duration: 0.4 }, m(4));
  // tarjeta final de precio
  const fin = nuevo("div", "tarjeta", `
    <div style="display:flex;align-items:center;gap:16px">${ico("coins", 40, "var(--naranja)")}<div style="font:800 40px 'Inter Display'">GPT-6 Luna</div></div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:22px">
      <div><div style="font-size:22px;color:var(--suave)">Entrada</div><div style="font:800 54px 'Inter Display'">$0.10</div></div>
      <div><div style="font-size:22px;color:var(--suave)">Salida</div><div style="font:800 54px 'Inter Display'">$0.50</div></div>
    </div>
    <div style="font-size:22px;color:var(--suave);margin-top:8px">por millón de tokens · modelo: <span class="mono" style="color:#cfe0ff">gpt-6-luna</span></div>`, esc,
    "position:absolute;left:1250px;top:660px;width:560px;padding:30px 34px;border-color:rgba(252,179,51,.5);box-shadow:0 0 60px rgba(252,179,51,.2)");
  subir(fin, m(4) + 0.4);
  nuevo("div", "fuente", "Fuente: artificialanalysis.ai · Intelligence Index v4.3.2 · modo de razonamiento máximo · *precio promocional", esc);
  salida();
};

ESCENAS.embeddings = () => {
  fondoVivo();
  cabecera("Pieza 2 · Embeddings", "binary", "Texto → <span class='acento'>números</span>", "Así la IA entiende el significado de tus documentos");
  // texto -> vector
  const txt = nuevo("div", "burbuja tu", "Miércoles: entregar el proyecto", esc, "left:120px;top:470px");
  subir(txt, m(1));
  const flecha = nuevo("div", "", ico("arrow-right", 56, "var(--naranja)"), esc, "position:absolute;left:720px;top:478px");
  pop(flecha, m(1) + 0.6);
  const vec = nuevo("div", "tarjeta mono", "", esc, "position:absolute;left:810px;top:455px;width:990px;padding:22px 28px;font-size:30px;color:#cfe0ff;white-space:nowrap;overflow:hidden");
  const numeros = "[ 0.12, -0.83, 0.44, 0.07, -0.51, 0.93, 0.28, -0.16, 0.65, ... ]";
  tl.from(vec, { opacity: 0, x: -20, duration: 0.4 }, m(1) + 0.8);
  escribir(vec, numeros, m(1) + 1.0, 40);
  const dims = nuevo("div", "", `<span id="dims" style="font:800 40px 'Inter Display';color:var(--naranja)">0</span> <span style="font-size:26px;color:var(--suave)">números por texto con bge-m3</span>`, esc, "position:absolute;left:830px;top:570px");
  subir(dims, m(1) + 3.0); contador(dims.querySelector("#dims"), m(1) + 3.0, 0, 1024, 1.6);
  // mapa de significado
  const mapa = nuevo("div", "tarjeta", "", esc, "position:absolute;left:120px;top:660px;width:1680px;height:340px;overflow:hidden");
  const pts = [
    ["¿Qué tengo el miércoles?", 380, 120, "#4c8df6", 0], ["Miércoles: entregar el proyecto", 470, 200, "#fcb333", 0],
    ["Lunes: reunión a las 9", 260, 230, "#fcb333", 0.3],
    ["Mi perro se llama Rocky", 1150, 110, "#4ade80", 0.6], ["Sábado: Rocky al veterinario", 1290, 210, "#4ade80", 0.8],
    ["Me gusta el café americano", 820, 260, "#f87171", 1.0],
  ];
  const ptsEl = pts.map(([t, x, y, c, d]) => {
    const p = nuevo("div", "", `<span style="display:inline-block;width:20px;height:20px;border-radius:50%;background:${c};box-shadow:0 0 18px ${c};margin-right:12px;vertical-align:middle"></span>${t}`, mapa, `position:absolute;left:${x}px;top:${y}px;font-size:25px;white-space:nowrap`);
    pop(p, m(2) + d + 0.2);
    return p;
  });
  const grupo = nuevo("div", "", "", mapa, "position:absolute;left:220px;top:85px;width:640px;height:190px;border-radius:50%;border:3px dashed var(--naranja)");
  tl.from(grupo, { scale: 0.3, opacity: 0, duration: 0.7, ease: "back.out(1.6)" }, m(2) + 2.6);
  tl.to([mapa, txt, flecha, vec, dims], { opacity: 0, y: -20, duration: 0.5 }, m(3) - 0.2);
  // comparativa de modelos de embeddings
  const tabla = nuevo("div", "", "", esc, "position:absolute;left:120px;right:120px;top:450px;display:grid;grid-template-columns:repeat(4,1fr);gap:24px");
  const ems = [
    ["si_ollama", "bge-m3", "Ollama · en tu PC", ["Gratis", "1024 dimensiones", "+100 idiomas"], "#fcb333", true],
    ["sparkles", "text-embedding-3-small", "OpenAI · en la nube", ["$0.02 por millón de tokens", "1536 dimensiones", "Requiere internet"], "#e5e7eb"],
    ["sparkles", "text-embedding-3-large", "OpenAI · en la nube", ["Más preciso, más caro", "3072 dimensiones", "Requiere internet"], "#e5e7eb"],
    ["si_ollama", "nomic-embed-text", "Ollama · en tu PC", ["Gratis", "768 dimensiones", "Principalmente inglés"], "#e5e7eb"],
  ];
  const tarj = ems.map(([i, n, s, props, c]) => nuevo("div", "tarjeta", `
      <div style="display:flex;align-items:center;gap:14px">${ico(i, 40, c)}<div style="font-size:21px;color:var(--suave)">${s}</div></div>
      <div class="mono" style="font-size:30px;font-weight:700;margin-top:18px;line-height:1.2;word-break:break-word">${n}</div>
      ${props.map((p) => `<div style="display:flex;gap:10px;align-items:center;margin-top:14px;font-size:24px;color:#c9d4ea">${ico("check", 24, "var(--verde)")}${p}</div>`).join("")}`,
    tabla, "padding:32px 30px;min-height:360px"));
  subir(tarj, m(3) + 0.2, { stagger: 0.25 });
  const elegido = nuevo("div", "pastilla", `${ico("circle-check", 30, "var(--naranja)")}Nuestra elección`, esc, "position:absolute;left:150px;top:850px;border-color:var(--naranja);color:var(--naranja)");
  resaltar(tarj[0], m(4) + 0.2);
  tarj.slice(1).forEach((t) => apagar(t, m(4) + 0.2));
  pop(elegido, m(4) + 0.5);
  salida();
};

ESCENAS.qdrant = () => {
  fondoVivo();
  cabecera("Pieza 3 · Búsqueda", "scan-search", "Qdrant: base de datos <span class='acento'>vectorial</span>");
  const q = nuevo("div", "burbuja tu", "¿Cómo se llama mi perro?", esc, "left:120px;top:420px");
  subir(q, m(1));
  const lib = nuevo("div", "tarjeta", "", esc, "position:absolute;left:120px;top:560px;width:1000px;padding:28px 30px");
  nuevo("div", "", `${ico("si_qdrant", 34, "#f87171")}<span style="font-size:28px;font-weight:700;margin-left:12px">Colección "jarvis"</span>`, lib, "display:flex;align-items:center;margin-bottom:12px");
  const filas = [
    ["Tengo un perro que se llama Rocky.", 0.91],
    ["Sábado: llevar a Rocky al veterinario a las 10:00 a. m.", 0.74],
    ["Me gusta el café americano sin azúcar...", 0.32],
    ["Lunes: reunión con el equipo a las 9:00 a. m.", 0.18],
  ];
  const fs = filas.map(([t, sc], k) => {
    const f = nuevo("div", "", `<span style="flex:1">${t}</span><span class="mono sc" style="font-weight:700">0.00</span>`, lib,
      "display:flex;gap:20px;align-items:center;padding:16px 20px;margin-top:10px;border-radius:16px;background:rgba(255,255,255,.04);font-size:25px");
    return [f, sc];
  });
  subir(lib, m(0) + 1.2);
  subir(fs.map((x) => x[0]), m(0) + 1.6, { stagger: 0.15 });
  // haz de búsqueda + puntajes
  fs.forEach(([f, sc], k) => contador(f.querySelector(".sc"), m(1) + 2.0, 0, sc, 1.2, (v) => v.toFixed(2)));
  tl.to(fs[0][0], { background: "rgba(252,179,51,.18)", boxShadow: "0 0 0 2px var(--naranja)", duration: 0.5 }, m(1) + 3.4);
  tl.to(fs[1][0], { background: "rgba(252,179,51,.10)", duration: 0.5 }, m(1) + 3.6);
  tl.to([fs[2][0], fs[3][0]], { opacity: 0.4, duration: 0.5 }, m(1) + 3.6);
  const top = nuevo("div", "tarjeta", `<div style="font-size:24px;color:var(--suave)">Qdrant devuelve</div><div style="font:800 46px 'Inter Display';margin-top:6px">los más parecidos</div><div style="font-size:24px;color:var(--suave);margin-top:10px">k = 3 fragmentos → contexto para el LLM</div>`, esc,
    "position:absolute;left:1200px;top:560px;width:600px;padding:30px 34px");
  subir(top, m(1) + 4.0);
  const win = nuevo("div", "tarjeta", `<div style="display:flex;gap:18px;align-items:center">${ico("laptop", 52, "var(--azul-claro)")}<div><div style="font-size:30px;font-weight:700">Versión para Windows</div><div class="mono" style="font-size:24px;color:#cfe0ff;margin-top:6px">C:\\qdrant\\qdrant.exe</div></div></div>`, esc,
    "position:absolute;left:1200px;top:820px;width:600px;padding:26px 30px;border-color:rgba(76,141,246,.5)");
  subir(win, m(2) + 0.2);
  salida();
};

ESCENAS.rag = () => {
  fondoVivo();
  cabecera("La técnica", "sparkles", "<span class='acento'>RAG</span>: así responde JARVIS");
  const pasos = [
    ["message-circle", "1. Pregunta", "¿Qué tengo el miércoles?", "#4c8df6", ""],
    ["scan-search", "2. Buscar", "Qdrant encuentra tu agenda", "#f87171", "R"],
    ["layers", "3. Añadir", "pregunta + contexto", "#fcb333", "A"],
    ["brain", "4. Generar", "GPT-6 Luna responde", "#4ade80", "G"],
  ];
  const fila = nuevo("div", "", "", esc, "position:absolute;left:120px;right:120px;top:470px;display:grid;grid-template-columns:repeat(4,1fr);gap:60px");
  const cs = pasos.map(([i, t, s, c, l]) => nuevo("div", "tarjeta", `
      <div style="width:96px;height:96px;border-radius:28px;display:grid;place-items:center;background:${c}22;color:${c}">${ico(i, 54)}</div>
      <div style="font-size:36px;font-weight:800;margin-top:26px">${t}</div>
      <div style="font-size:25px;color:var(--suave);margin-top:10px">${s}</div>
      ${l ? `<div style="position:absolute;right:26px;top:18px;font:900 72px 'Inter Display';color:${c};opacity:.9" class="letra">${l}</div>` : ""}`, fila, "position:relative;padding:36px 32px;min-height:330px"));
  const s = svg(1920, 1080, esc, "left:0;top:0");
  const flechas = [0, 1, 2].map((k) => trazo(s, `M${120 + (k + 1) * 405 - 50} 635 L${120 + (k + 1) * 405 + 5} 635`, "var(--naranja)", 5));
  subir(cs[0], m(1)); subir(cs[1], m(1) + 2.2);
  tl.from(flechas[0], { drawSVG: 0, duration: 0.5 }, m(1) + 2.0);
  subir(cs[2], m(2)); tl.from(flechas[1], { drawSVG: 0, duration: 0.5 }, m(2) - 0.2);
  subir(cs[3], m(2) + 2.6); tl.from(flechas[2], { drawSVG: 0, duration: 0.5 }, m(2) + 2.4);
  tl.from(".letra", { scale: 0, opacity: 0, duration: 0.5, stagger: 0.25, ease: "back.out(2)" }, m(3) - 0.4);
  const fin = nuevo("div", "pastilla", `${ico("shield-check", 32, "var(--verde)")}Responde con TUS datos reales · no se inventa cosas`, esc, "position:absolute;left:0;right:0;margin:auto;width:fit-content;top:880px;font-size:30px;border-color:rgba(74,222,128,.4)");
  pop(fin, m(3) + 0.3);
  salida();
};

ESCENAS.memoria = () => {
  fondoVivo();
  cabecera("Pieza 4 · Memoria", "history", "JARVIS <span class='acento'>recuerda</span>");
  const b1 = nuevo("div", "burbuja tu", "¿Qué tengo el miércoles?", esc, "right:1000px;top:400px");
  const b2 = nuevo("div", "burbuja ia", "Entregar el proyecto de la tienda online.", esc, "left:120px;top:500px");
  const b3 = nuevo("div", "burbuja tu", "¿Y cómo se llama mi perro?", esc, "right:1000px;top:610px");
  const sinMem = nuevo("div", "pastilla", `${ico("ghost", 30, "var(--rojo)")}Sin memoria: cada mensaje empieza de cero`, esc, "position:absolute;left:120px;top:300px;color:var(--rojo);border-color:rgba(248,113,113,.4)");
  pop(sinMem, m(0) + 2.4);
  subir(b1, m(1)); subir(b2, m(1) + 1.0); subir(b3, m(1) + 2.0);
  tl.to(sinMem, { opacity: 0, duration: 0.4 }, m(2) - 0.3);
  // tabla en PostgreSQL
  const tabla = nuevo("div", "tarjeta", `<div style="display:flex;gap:14px;align-items:center">${ico("si_postgresql", 40, "#7fb2ff")}<span style="font-size:28px;font-weight:700">PostgreSQL · tabla <span class="mono">chat_history</span></span></div>`, esc,
    "position:absolute;left:1000px;top:380px;width:800px;padding:28px 30px");
  const filas = [["hilo 7f3c…", "human", "¿Qué tengo el miércoles?"], ["hilo 7f3c…", "ai", "Entregar el proyecto…"], ["hilo 7f3c…", "human", "¿Y cómo se llama mi perro?"], ["hilo 7f3c…", "ai", "Se llama Rocky…"]];
  const fs = filas.map(([h, t, x]) => nuevo("div", "mono", `<span style="color:var(--suave)">${h}</span><span style="color:${t === "ai" ? "var(--verde)" : "var(--azul-claro)"};width:90px">${t}</span><span>${x}</span>`, tabla,
    "display:flex;gap:22px;margin-top:14px;padding:12px 16px;border-radius:12px;background:rgba(255,255,255,.04);font-size:22px;white-space:nowrap;overflow:hidden"));
  subir(tabla, m(2)); subir(fs, m(2) + 0.6, { stagger: 0.3, x: 40, y: 0 });
  const ult = nuevo("div", "pastilla", `${ico("refresh-cw", 28, "var(--naranja)")}En cada pregunta enviamos los últimos 10 mensajes`, esc, "position:absolute;left:1000px;top:770px;font-size:25px");
  pop(ult, m(2) + 3.0);
  const win = nuevo("div", "pastilla", `${ico("laptop", 30, "var(--azul-claro)")}Instalador oficial para Windows`, esc, "position:absolute;left:1000px;top:860px;border-color:rgba(76,141,246,.5)");
  pop(win, m(3) + 0.2);
  salida();
};

ESCENAS.arquitectura = () => {
  fondoVivo();
  cabecera("Arquitectura", "blocks", "Cómo se conecta <span class='acento'>todo</span>");
  const N = {
    web: nodo(120, 520, 340, 130, "app-window", "Página web", "index.html · app.js", "#4ade80"),
    api: nodo(550, 520, 340, 130, "server", "Servidor", "FastAPI · app.py", "#4c8df6"),
    lc: nodo(980, 520, 360, 130, "si_langchain", "asistente.py", "LangChain", "#7ee0b5"),
    qd: nodo(980, 300, 360, 130, "si_qdrant", "Qdrant", "+ Ollama · bge-m3", "#f87171"),
    pg: nodo(980, 760, 360, 130, "si_postgresql", "PostgreSQL", "memoria del hilo", "#7fb2ff"),
    llm: nodo(1430, 520, 370, 130, "brain", "GPT-6 Luna", "el cerebro", "#fcb333"),
  };
  const s = svg(1920, 1080, esc, "left:0;top:0");
  const L = {
    webApi: trazo(s, "M460 585 L550 585", "rgba(255,255,255,.4)", 4),
    apiLc: trazo(s, "M890 585 L980 585", "rgba(255,255,255,.4)", 4),
    lcQd: trazo(s, "M1160 520 L1160 430", "rgba(255,255,255,.4)", 4),
    lcPg: trazo(s, "M1160 650 L1160 760", "rgba(255,255,255,.4)", 4),
    lcLlm: trazo(s, "M1340 585 L1430 585", "rgba(255,255,255,.4)", 4),
  };
  subir(N.web, m(0) + 0.6);
  subir(N.api, m(1)); tl.from(L.webApi, { drawSVG: 0, duration: 0.5 }, m(1) + 0.3);
  subir(N.lc, m(1) + 1.6); tl.from(L.apiLc, { drawSVG: 0, duration: 0.5 }, m(1) + 1.9);
  subir(N.qd, m(2)); tl.from(L.lcQd, { drawSVG: 0, duration: 0.5 }, m(2) + 0.3);
  subir(N.pg, m(2) + 2.4); tl.from(L.lcPg, { drawSVG: 0, duration: 0.5 }, m(2) + 2.7);
  subir(N.llm, m(3)); tl.from(L.lcLlm, { drawSVG: 0, duration: 0.5 }, m(3) + 0.3);
  // paquete que viaja: web → servidor → Qdrant → Postgres → LLM → de vuelta
  const pq = nuevo("div", "", "", esc, "position:absolute;left:0;top:0;width:22px;height:22px;border-radius:50%;background:var(--naranja);box-shadow:0 0 24px var(--naranja)");
  const ruta = [[460, 585], [550, 585], [890, 585], [980, 585], [1160, 520], [1160, 430], [1160, 520], [1160, 650], [1160, 760], [1160, 650], [1340, 585], [1430, 585], [1340, 585], [980, 585], [890, 585], [550, 585], [460, 585]];
  tl.set(pq, { x: 449, y: 574, opacity: 0 }, 0);
  tl.to(pq, { opacity: 1, duration: 0.2 }, m(3) + 1.2);
  ruta.forEach(([x, y], k) => tl.to(pq, { x: x - 11, y: y - 11, duration: 0.32, ease: "none" }, m(3) + 1.2 + k * 0.32));
  const voz = nuevo("div", "pastilla", `${ico("volume-2", 30, "var(--verde)")}La página lee la respuesta en voz alta`, esc, "position:absolute;left:120px;top:720px;font-size:25px");
  pop(voz, m(3) + 1.2 + ruta.length * 0.32);
  salida();
};

ESCENAS.instalacion = () => {
  fondoVivo();
  cabecera("Instalación en Windows", "download", "Todo en <span class='azul'>Windows</span>, sin Docker");
  const pasos = [
    ["si_python", "Python", "python.org", "Marca ✔ “Add python.exe to PATH”", "#ffd43b"],
    ["si_ollama", "Ollama", "ollama.com", "Queda funcionando en segundo plano", "#e5e7eb"],
    ["si_qdrant", "Qdrant", "GitHub · Releases", ".zip para Windows → C:\\qdrant", "#f87171"],
    ["si_postgresql", "PostgreSQL", "postgresql.org", "Anota la contraseña de “postgres”", "#7fb2ff"],
    ["key-round", "API key", "platform.openai.com", "Para usar GPT-6 Luna", "#fcb333"],
  ];
  const fila = nuevo("div", "", "", esc, "position:absolute;left:120px;right:120px;top:420px;display:grid;grid-template-columns:repeat(5,1fr);gap:24px");
  const cs = pasos.map(([i, t, u, d, c], k) => nuevo("div", "tarjeta", `
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div style="width:84px;height:84px;border-radius:24px;display:grid;place-items:center;background:${c}1f;color:${c}">${ico(i, 48)}</div>
        <div style="font:900 56px 'Inter Display';color:rgba(255,255,255,.12)">${k + 1}</div>
      </div>
      <div style="font-size:36px;font-weight:800;margin-top:24px">${t}</div>
      <div class="mono" style="font-size:21px;color:var(--azul-claro);margin-top:8px">${u}</div>
      <div style="font-size:23px;color:#c9d4ea;margin-top:18px;line-height:1.35">${d}</div>
      <div class="ok" style="position:absolute;right:22px;bottom:22px;color:var(--verde)">${ico("circle-check", 40)}</div>`, fila, "position:relative;padding:30px 28px;min-height:400px"));
  cs.forEach((c, k) => {
    subir(c, m(k + 1) - 0.1);
    resaltar(c, m(k + 1) + 0.2, "rgba(76,141,246,.9)");
    tl.to(c, { scale: 1, boxShadow: "0 30px 80px rgba(0,0,0,.35)", borderColor: "rgba(74,222,128,.35)", duration: 0.4 }, (k + 2 < M.length ? m(k + 2) : DUR - 1.5) - 0.3);
    tl.from(c.querySelector(".ok"), { scale: 0, opacity: 0, duration: 0.4, ease: "back.out(2)" }, (k + 2 < M.length ? m(k + 2) : DUR - 1.5) - 0.2);
  });
  const nod = nuevo("div", "pastilla", `${ico("x", 30, "var(--rojo)")}Sin Docker · sin WSL`, esc, "position:absolute;right:120px;top:120px;color:var(--rojo);border-color:rgba(248,113,113,.4)");
  pop(nod, m(0) + 1.4);
  salida();
};

ESCENAS.resumen = () => {
  fondoVivo();
  cabecera("Resumen", "list-checks", "¡Tu JARVIS está <span class='acento'>listo</span>!");
  const items = [
    ["brain", "GPT-6 Luna", "el cerebro, barato e inteligente"],
    ["binary", "Ollama · bge-m3", "embeddings gratis en tu PC"],
    ["scan-search", "Qdrant", "busca en tus documentos"],
    ["history", "PostgreSQL", "recuerda cada conversación"],
    ["app-window", "FastAPI + web", "te responde con voz"],
  ];
  const lista = nuevo("div", "", "", esc, "position:absolute;left:120px;top:380px;width:900px;display:grid;gap:18px");
  const its = items.map(([i, t, s]) => nuevo("div", "tarjeta", `<span style="color:var(--naranja)">${ico(i, 40)}</span><b style="font-size:30px">${t}</b><span style="font-size:25px;color:var(--suave)">${s}</span>`, lista, "display:flex;align-items:center;gap:20px;padding:20px 28px"));
  subir(its, m(1), { stagger: 0.45, x: -40, y: 0 });
  const reto = nuevo("div", "tarjeta", `<div style="display:flex;gap:14px;align-items:center;color:var(--naranja)">${ico("rocket", 40)}<b style="font-size:32px">Tu reto</b></div>
    <div style="font-size:28px;line-height:1.45;margin-top:16px">Agrega tus propios documentos a <span class="mono" style="color:#cfe0ff">docs/</span>, ejecuta <span class="mono" style="color:#cfe0ff">ingest.py</span> y pregúntale lo que quieras.</div>`, esc,
    "position:absolute;left:1100px;top:430px;width:700px;padding:34px 36px;border-color:rgba(252,179,51,.45)");
  subir(reto, m(3));
  const win = nuevo("div", "pastilla", `${ico("laptop", 30, "var(--azul-claro)")}Todo en Windows · sin Docker`, esc, "position:absolute;left:1100px;top:330px");
  pop(win, m(2));
  salida();
};

ESCENAS.final = () => {
  fondoVivo();
  const logo = nuevo("img", "", null, esc, "position:absolute;left:885px;top:150px;width:150px;height:150px");
  logo.src = LOGO;
  tl.from(logo, { scale: 0, rotation: -90, duration: 0.9, ease: "back.out(1.7)" }, 0.1);
  const t = nuevo("div", "", "¡Gracias por ver!", esc, "position:absolute;left:0;right:0;top:340px;text-align:center;font:900 110px 'Inter Display';letter-spacing:-0.03em");
  const sp = new SplitText(t, { type: "chars" });
  tl.from(sp.chars, { yPercent: 60, opacity: 0, duration: 0.6, stagger: 0.03, ease: "back.out(1.7)" }, 0.4);
  const gh = nuevo("div", "pastilla", `${ico("folder", 30, "var(--naranja)")}<span>Código en GitHub: <span class="mono" style="color:#cfe0ff">paulantezana/tutoriales</span></span>`, esc, "position:absolute;left:0;right:0;margin:auto;width:fit-content;top:520px");
  subir(gh, m(0) + 0.3);
  const fila = nuevo("div", "", "", esc, "position:absolute;left:0;right:0;top:660px;display:flex;justify-content:center;gap:34px");
  const bs = [["thumbs-up", "Me gusta", "#4c8df6"], ["bell", "Suscríbete", "#ef4444"], ["message-circle", "Comenta", "#fcb333"]].map(([i, x, c]) =>
    nuevo("div", "", `${ico(i, 40, "#fff")}<span>${x}</span>`, fila, `display:flex;gap:16px;align-items:center;padding:24px 44px;border-radius:999px;background:${c};font-size:36px;font-weight:800;box-shadow:0 20px 50px ${c}55`));
  pop(bs, m(1), { stagger: 0.2 });
  tl.to(bs[1], { scale: 1.08, duration: 0.35, yoyo: true, repeat: 5, ease: "sine.inOut" }, m(1) + 1.2);
  const nombre = nuevo("div", "", "Paul Antezana", esc, "position:absolute;left:0;right:0;top:850px;text-align:center;font-size:30px;font-weight:600;color:var(--suave);letter-spacing:.2em;text-transform:uppercase");
  subir(nombre, m(1) + 0.8);
  tl.to(esc, { opacity: 0, duration: 0.8 }, DUR - 0.8);
};

// Pantalla genérica de "cargando" para el navegador (sin imitar ninguna web real)
ESCENAS.cargando = () => {
  document.querySelector("#fondo").style.display = "none";
  document.body.style.background = "#f5f6f8";
  const barra = nuevo("div", "", "", esc, "position:absolute;left:0;top:0;height:5px;background:#4c8df6;width:0");
  tl.to(barra, { width: "100%", duration: DUR, ease: "power2.out" }, 0);
  const sk = nuevo("div", "", "", esc, "position:absolute;left:160px;right:160px;top:120px;display:grid;gap:26px");
  [500, 1200, 900, 1300, 700].forEach((w) => nuevo("div", "", "", sk, `height:${w === 500 ? 60 : 28}px;width:${w}px;max-width:100%;border-radius:12px;background:#e3e6eb`));
  tl.to(sk.children, { opacity: 0.45, duration: 0.6, yoyo: true, repeat: 7, stagger: 0.1 }, 0);
};

// ------------------------------------------------------------- arranque
document.fonts.ready.then(() => {
  (ESCENAS[ID] || ESCENAS.cargando)();
  tl.seek(0);
  window.__listo = true;
});
window.seek = (t) => { tl.seek(Math.max(0, Math.min(t, DUR)), false); return 0; };
