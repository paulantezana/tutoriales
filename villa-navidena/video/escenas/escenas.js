/* Escenas del video, en el orden del guion (render.py).
   m(i) = segundo en que empieza la frase i de la escena. */

// ------------------------------------------------------------- utilidades de dibujo técnico
const FOAM = "#f0a3bf", FOAM_TOP = "#f7c2d5", FOAM_LADO = "#d8849f";
const MDF = "#b07f4f", MDF_TOP = "#c99a66", MDF_LADO = "#8f6337";

function iso(ox, oy, k) {
  const c = Math.cos(Math.PI / 6) * k, s = 0.5 * k;
  return (x, y, z = 0) => [ox + (x - y) * c, oy + (x + y) * s - z * k];
}
function poli(padre, pts, relleno, borde = "#0d1424", ancho = 2, extra = {}) {
  return el("path", { d: "M" + pts.map((p) => p.join(",")).join(" L") + " Z", fill: relleno, stroke: borde, "stroke-width": ancho, "stroke-linejoin": "round", ...extra }, padre);
}
function cajaIso(padre, P, x, y, z, w, d, h, arriba, izq, der) {
  const gr = g(padre);
  poli(gr, [P(x, y + d, z), P(x + w, y + d, z), P(x + w, y + d, z + h), P(x, y + d, z + h)], izq);
  poli(gr, [P(x + w, y, z), P(x + w, y + d, z), P(x + w, y + d, z + h), P(x + w, y, z + h)], der);
  poli(gr, [P(x, y, z + h), P(x + w, y, z + h), P(x + w, y + d, z + h), P(x, y + d, z + h)], arriba);
  return gr;
}
function tarjetaPanel(x, y, w, h, titulo, detalle = "", padre = esc) {
  const p = nuevo("div", "tarjeta panel", `<div class="pt">${titulo}</div>${detalle ? `<div class="pd">${detalle}</div>` : ""}`, padre, `left:${x}px;top:${y}px;width:${w}px;height:${h}px`);
  return p;
}
// puntitos que recorren un camino SVG (corriente eléctrica)
function corriente(padre, d, n, color, vel, desde = 0, radio = 5) {
  const p = el("path", { d, fill: "none", stroke: "none" }, padre);
  const pts = Array.from({ length: n }, () => el("circle", { r: radio, fill: color, opacity: 0 }, padre));
  const L = () => p.getTotalLength();
  CUADRO.push((t) => {
    const on = t >= desde;
    pts.forEach((c, i) => {
      if (!on) { c.setAttribute("opacity", 0); return; }
      const len = L();
      const pos = (((t - desde) * vel + (i / n) * len) % len + len) % len;
      const q = p.getPointAtLength(pos);
      c.setAttribute("cx", q.x); c.setAttribute("cy", q.y);
      c.setAttribute("opacity", Math.min(1, (t - desde) * 2));
    });
  });
  return pts;
}
// símbolo de LED en un esquema (vertical, ánodo arriba)
function ledSimbolo(padre, x, y, color = "#ffd27a", tam = 1) {
  const gr = g(padre, { transform: `translate(${x},${y}) scale(${tam})` });
  poli(gr, [[-16, -12], [16, -12], [0, 12]], color, "#0d1424", 2);
  linea(gr, -16, 12, 16, 12, "#e8eeff", 3);
  camino(gr, "M20,-6 L32,-16 M26,-16 L32,-16 L32,-10 M22,4 L34,-6 M28,-6 L34,-6 L34,0", color, 2.5);
  return gr;
}
function resistenciaSimbolo(padre, x, y, vertical = true) {
  const gr = g(padre, { transform: `translate(${x},${y}) rotate(${vertical ? 90 : 0})` });
  el("rect", { x: -22, y: -9, width: 44, height: 18, rx: 4, fill: "#e8d3a6", stroke: "#0d1424", "stroke-width": 2 }, gr);
  [["#dc2626", -12], ["#dc2626", -5], ["#7c2d12", 2], ["#d4a017", 12]].forEach(([c, bx]) => el("rect", { x: bx, y: -9, width: 4, height: 18, fill: c }, gr));
  return gr;
}
function ledDibujo(padre, x, y, color, escala = 1, encendido = false) {
  const gr = g(padre, { transform: `translate(${x},${y}) scale(${escala})` });
  if (encendido) el("circle", { cx: 0, cy: -10, r: 46, fill: gradRadial(padre.ownerSVGElement || padre, [[0, color, 0.8], [1, color, 0]]) }, gr);
  camino(gr, "M-16,14 L-16,-10 Q-16,-30 0,-30 Q16,-30 16,-10 L16,14 Z", "#0d1424", 2, color);
  el("rect", { x: -20, y: 14, width: 40, height: 7, rx: 2, fill: color, stroke: "#0d1424", "stroke-width": 2 }, gr);
  return gr;
}
function reloj(padre, x, y, texto_, emoji = "⏱️") {
  return nuevo("div", "pastilla", `${emo(emoji, 30)}${texto_}`, padre, `position:absolute;left:${x}px;top:${y}px`);
}

// ============================================================== INTRODUCCIÓN
ESCENAS.portada = () => {
  const v = villa(esc, 860, 150, 1000, { luces: m(1) - 0.3, motor: m(2) });
  tl.from(v.svg, { y: 60, opacity: 0, duration: 1.1, ease: "power3.out" }, 0.2);
  const c = nuevo("div", "cabecera", "", esc, "top:180px");
  const k = nuevo("div", "kicker", "Tutorial completo · paso a paso", c);
  const h = nuevo("h1", "titulo", "Villa navideña<br><span class='acento'>animada</span>", c, "font-size:104px");
  const s = nuevo("div", "subtitulo", "Con luces LED, río que brilla y una pista de patinaje que gira", c, "max-width:700px;line-height:1.35");
  const sp = new SplitText(h, { type: "lines,words", linesClass: "linea-titulo" });
  tl.from(k, { y: 20, opacity: 0, duration: 0.5 }, 0.2);
  tl.from(sp.words, { yPercent: 110, duration: 0.9, stagger: 0.08, ease: "power4.out" }, 0.3);
  tl.from(s, { y: 20, opacity: 0, duration: 0.6 }, 0.9);
  const sv = svg(0, 0, 1920, 1080);
  const partes = [["iglesia", "Iglesia con torre", 70, -40], ["tudor", "Casa con tienda", -40, 90], ["rio", "Río con luz azul", 20, 120],
    ["arbol", "Árbol con luces", 120, -60], ["panaderia", "Panadería", 90, 60]];
  const etis = partes.map(([a, t, dx, dy]) => {
    const [px, py] = v.punto(...v.ANCLAS[a]);
    return etiqueta(sv, px, py, px + dx, py + dy, t);
  });
  pop(etis, m(1) + 0.4, { stagger: 0.35 });
  tl.to(etis, { opacity: 0, duration: 0.4 }, m(2) - 0.2);
  const [px, py] = v.punto(...v.ANCLAS.pista);
  const ep = etiqueta(sv, px, py, px - 90, py + 160, "Pista que gira", "motor de 5 V");
  pop(ep, m(2) + 0.2);
  tl.to(ep, { opacity: 0, duration: 0.4 }, m(3) - 0.2);
  const fila = nuevo("div", "", "", esc, "position:absolute;left:110px;top:640px;width:700px;display:flex;flex-wrap:wrap;gap:14px");
  const temas = [["🧰", "Herramientas"], ["📦", "Materiales"], ["📐", "Medidas"], ["🎨", "Pintura"], ["💡", "Circuito"], ["⚙️", "Motor"], ["❄️", "Nieve"]]
    .map(([e, t]) => nuevo("div", "pastilla", `${emo(e, 28)}${t}`, fila));
  pop(temas, m(3) + 0.3, { stagger: 0.18 });
  const bonus = nuevo("div", "tip", `${emo("🏭", 34)}<span>Bonus: copias en <b>polirresina</b>, como la fábrica</span>`, esc, "left:110px;top:856px");
  subir(bonus, m(4) + 0.2);
  salida();
};

ESCENAS.original = () => {
  cabecera("Cómo está hecha", "La villa de la <span class='acento'>tienda</span>");
  const s = svg(900, 250, 940, 650);
  // base hueca
  const base = g(s);
  poli(base, [[30, 430], [900, 430], [900, 452], [30, 452]], "#d9c7a3");
  poli(base, [[30, 452], [50, 452], [50, 590], [30, 590]], "#d9c7a3");
  poli(base, [[880, 452], [900, 452], [900, 590], [880, 590]], "#d9c7a3");
  camino(base, "M24,428 L906,428", "#ffffff", 10);
  linea(base, 30, 596, 900, 596, "#4b5563", 6);
  // casa hueca de polirresina
  const casa = g(s);
  el("path", { d: "M430,428 L430,250 L575,140 L720,250 L720,428 Z M448,428 L702,428 L702,258 L575,162 L448,258 Z", fill: "#d9c7a3", "fill-rule": "evenodd", stroke: "#0d1424", "stroke-width": 2 }, casa);
  el("rect", { x: 702, y: 300, width: 18, height: 56, fill: "#ffd27a" }, casa);
  camino(casa, "M418,256 L575,128 L732,256", "#ffffff", 12);
  const luz = el("circle", { cx: 600, cy: 330, r: 70, fill: gradRadial(s, [[0, "#ffd27a", 0.8], [1, "#ffd27a", 0]]) }, casa);
  ledDibujo(casa, 600, 345, "#fff4c2", 0.8);
  camino(casa, "M592,362 L592,500 L700,520 M608,362 L608,490 L700,512", "#ef4444", 3);
  // pista con motor
  const pista = g(s);
  el("rect", { x: 120, y: 410, width: 230, height: 10, rx: 3, fill: "#bfe6ff", stroke: "#0d1424", "stroke-width": 2 }, pista);
  poli(pista, [[110, 430], [360, 430], [360, 452], [110, 452]], "#0b1222", "none");
  el("rect", { x: 229, y: 420, width: 12, height: 60, fill: "#cfd6e2" }, pista);
  el("rect", { x: 208, y: 480, width: 54, height: 34, rx: 4, fill: "#d6b36a", stroke: "#0d1424", "stroke-width": 2 }, pista);
  el("rect", { x: 212, y: 514, width: 46, height: 54, rx: 8, fill: "#cbd5e1", stroke: "#0d1424", "stroke-width": 2 }, pista);
  [[180, 470, 16], [290, 475, 22]].forEach(([cx, cy, r]) => el("circle", { cx, cy, r, fill: "none", stroke: "#9aa4b8", "stroke-width": 4, "stroke-dasharray": "4 3" }, pista));
  camino(pista, "M170,398 A70,14 0 1 0 300,398", "#fcb333", 3);
  // placa y USB
  const elec = g(s);
  el("rect", { x: 690, y: 495, width: 90, height: 40, rx: 4, fill: "#3f7d4a", stroke: "#0d1424", "stroke-width": 2 }, elec);
  camino(elec, "M780,515 L940,520", "#111827", 8);
  el("rect", { x: 930, y: 506, width: 30, height: 26, rx: 4, fill: "#cfd6e2", stroke: "#0d1424", "stroke-width": 2 }, elec);
  camino(elec, "M258,540 L690,525", "#ef4444", 3);
  // etiquetas
  const e1 = etiqueta(s, 440, 330, 300, 240, "Polirresina", "pieza hueca");
  const e2 = etiqueta(s, 575, 150, 760, 90, "Pintura a mano", "+ escarcha");
  const e3 = etiqueta(s, 600, 330, 800, 300, "LED");
  const e4 = etiqueta(s, 235, 520, 120, 620, "Motorreductor");
  const e5 = etiqueta(s, 945, 520, 900, 630, "USB 5 V", "o 3 pilas AA");
  aparecer([base, casa], 0.3, 0.8);
  aparecer(pista, 0.5, 0.8);
  aparecer(elec, 0.6, 0.8);
  tl.from(luz, { opacity: 0, duration: 0.8 }, m(3));
  pop(e1, m(1) + 0.3); pop(e3, m(3) + 0.2); pop(e4, m(3) + 1.2); pop(e5, m(4) + 0.2); pop(e2, m(5) + 0.2);
  // tarjetas de la izquierda
  const cs = [
    ["🧪", "Polirresina", "resina poliéster + <b>carbonato de calcio</b>"],
    ["🧱", "Molde de silicona", "por eso las casas salen <b>huecas</b>"],
    ["💡", "LEDs + motorreductor", "luces dentro, motor debajo de la pista"],
    ["🔌", "USB de 5 V", "o 3 pilas AA (4.5 V)"],
    ["🖌️", "Pintada a mano", "nieve blanca + <b>escarcha</b>"],
  ].map(([e, t, d], i) => tarjetaPanel(110, 300 + i * 118, 720, 104, `${emo(e, 34)}${t}`, d));
  cs.forEach((c, i) => { subir(c, m(i + 1), { x: -40, y: 0 }); resaltar(c, m(i + 1) + 0.1); if (i) normal(cs[i - 1], m(i + 1)); });
  cs.forEach((c) => { c.style.height = "auto"; c.style.padding = "16px 24px"; });
  salida();
};

ESCENAS.plan = () => {
  cabecera("El plan", "Dos <span class='acento'>etapas</span>");
  const a = tarjetaPanel(110, 290, 820, 460, `${emo("✋", 40)}<span>Etapa A · <span style="color:var(--oro)">pieza a mano</span></span>`);
  const b = tarjetaPanel(990, 290, 820, 460, `${emo("🏭", 40)}<span>Etapa B · <span style="color:var(--oro)">copias</span> <span style="color:var(--suave);font-weight:600">(opcional)</span></span>`);
  const filaA = nuevo("div", "", "", a, "display:flex;gap:16px;margin-top:26px");
  [[DIB.foam(), "Foam"], [DIB.cartonpluma(), "Cartón pluma"], [DIB.masilla(), "Masilla epóxica"]].forEach(([d, t]) =>
    nuevo("div", "", `<div style="width:120px;height:110px">${d}</div><div style="font-size:22px;font-weight:700;margin-top:6px">${t}</div>`, filaA, "flex:1;text-align:center;padding:16px;border-radius:18px;background:rgba(255,255,255,.05)"));
  const resA = nuevo("div", "tip", `${emo("✅", 32)}<span>Tu villa terminada, con luces y movimiento</span>`, a, "position:relative;margin-top:28px");
  const filaB = nuevo("div", "", "", b, "display:flex;align-items:center;gap:14px;margin-top:26px");
  [["🏠", "Tu pieza"], ["➜", ""], ["🧱", "Molde de silicona"], ["➜", ""], ["🧪", "Polirresina"], ["➜", ""], ["🏘️", "Copias"]].forEach(([e, t]) =>
    nuevo("div", "", t ? `${emo(e, 50)}<div style="font-size:20px;font-weight:700;margin-top:8px">${t}</div>` : `<span style="font-size:40px;color:var(--oro)">${e}</span>`, filaB, t ? "flex:1;text-align:center;padding:16px 6px;border-radius:18px;background:rgba(255,255,255,.05)" : ""));
  const resB = nuevo("div", "", `<div class="pastilla">${emo("1️⃣", 28)} 1 villa → solo la <b style="color:var(--oro)">etapa A</b></div><div class="pastilla" style="margin-top:14px">${emo("🔢", 28)} varias o para vender → <b style="color:var(--oro)">A + B</b></div>`, b, "margin-top:28px");
  subir(a, m(1)); subir(filaA.children, m(1) + 0.4, { stagger: 0.15 });
  pop(resA, m(2) + 0.2);
  subir(b, m(3)); subir(filaB.children, m(3) + 0.4, { stagger: 0.12 });
  subir(resB.children, m(4) + 0.2, { stagger: 0.6 });
  const tiempo = nuevo("div", "pastilla", `${emo("🗓️", 32)}<span>Unos <b style="color:var(--oro)">3 o 4 fines de semana</b> · con secados de una noche</span>`, esc, "position:absolute;left:0;right:0;margin:auto;width:fit-content;top:790px");
  pop(tiempo, m(5) + 0.2);
  salida();
};

ESCENAS.seguridad = () => {
  cabecera("Antes de empezar", "Seguridad <span class='rojo'>primero</span>");
  const datos = [
    ["🔪", "Cúter", "Hoja nueva · sobre base de corte · la otra mano lejos del filo"],
    ["🔥", "Cautín: +300 °C", "Siempre en su soporte · nunca encendido solo"],
    ["🌡️", "Silicona caliente", "Ten un vaso con agua fría cerca"],
    ["⚡", "Solo 5 V", "Nunca conectes nada al enchufe de 220 V"],
    ["😷", "Resina (etapa B)", "Respirador con filtros · guantes · lentes · ventilación"],
  ];
  const cs = datos.map(([e, t, d], i) => {
    const c = tarjetaPanel(110 + (i % 3) * 570, 300 + Math.floor(i / 3) * 290, 540, 260, `${emo(e, 56)}`, `<div style="font-size:32px;font-weight:800;color:#fff;margin:14px 0 8px">${t}</div>${d}`);
    return c;
  });
  cs.forEach((c, i) => { pop(c, m(i + 1)); resaltar(c, m(i + 1) + 0.2, i === 3 ? "var(--rojo)" : "var(--oro)"); if (i) normal(cs[i - 1], m(i + 1)); });
  salida();
};

// ============================================================== HERRAMIENTAS Y MATERIALES
ESCENAS.herramientas = () => {
  cabecera("Lo que necesitas", "Herramientas");
  const grupos = [
    ["Cortar y medir", [["cuter", "Cúter grande"], ["bisturi", "Cúter de precisión"], ["regla", "Regla metálica"], ["escuadra", "Escuadra"], ["compas", "Compás"], ["basecorte", "Base de corte"]]],
    ["Pegar", [["pistola", "Pistola de silicona", "baja temperatura"]]],
    ["Electrónica", [["cautin", "Cautín 30–40 W"], ["estano", "Estaño"], ["multimetro", "Multímetro"], ["pelacables", "Pelacables"], ["alicate", "Alicate de corte"], ["termo", "Termocontraíble"]]],
    ["Perforar", [["taladro", "Minitaladro", "brocas 3 y 5 mm"]]],
    ["Pintar", [["pinceles", "Pinceles"], ["espatula", "Espátula"], ["esponja", "Esponja"], ["lija", "Lija al agua"]]],
    ["Secar", [["secadora", "Secadora de pelo"]]],
  ];
  const caja = nuevo("div", "", "", esc, "position:absolute;left:86px;top:270px;width:1748px;display:grid;grid-template-columns:repeat(7,1fr);gap:14px");
  const porGrupo = grupos.map(([nombre, its]) => its.map(([d, t, det]) =>
    nuevo("div", "tarjeta", `<div style="width:92px;height:92px;margin:0 auto">${DIB[d]()}</div><div style="font-size:22px;font-weight:700;margin-top:10px">${t}</div><div style="font-size:17px;color:var(--suave);margin-top:4px;min-height:20px">${det || nombre}</div>`,
      caja, "padding:16px 10px;text-align:center;height:196px")));
  porGrupo.forEach((tarjs, i) => {
    pop(tarjs, m(i + 1), { stagger: 0.12 });
    tarjs.forEach((t) => resaltar(t, m(i + 1) + 0.3));
    if (i) porGrupo[i - 1].forEach((t) => normal(t, m(i + 1)));
  });
  salida();
};

function materiales(kicker, titulo, lista, marcasDe) {
  cabecera(kicker, titulo);
  const caja = nuevo("div", "rejilla", "", esc, "left:110px;top:280px;width:1700px;grid-template-columns:1fr 1fr");
  const its = lista.map(([d, n, det, cant]) => item(caja, d, n, det, cant));
  its.forEach((it, i) => { subir(it, marcasDe[i], { x: -30, y: 0 }); resaltar(it, marcasDe[i] + 0.2); });
  its.forEach((it, i) => { const sig = marcasDe.find((t) => t > marcasDe[i]); if (sig) normal(it, sig); });
  return its;
}

ESCENAS.mat_estructura = () => {
  const its = materiales("Materiales · 1", "La <span class='acento'>estructura</span>", [
    [DIB.mdf(), "MDF de 5 mm", "Base de <b>32 × 24 cm</b>", "1"],
    [DIB.foam(), "Foam de poliestireno extruido", "Una plancha de <b>5 cm</b> y otra de <b>2.5 cm</b> · o tecnopor de alta densidad", ""],
    [DIB.cartonpluma(), "Cartón pluma (foam board) 5 mm", "Paredes de las casas · 1 pliego", ""],
    [DIB.cartulina(), "Cartulina gruesa / cartón gris 2 mm", "Techos, agujas, marcos y tejas", ""],
    [DIB.masilla(), "Masilla epóxica (tipo Poxilina)", "Figuras, chimeneas y adornos", ""],
    [DIB.conos(), "Conos de tecnopor", "6, 9 y 12 cm (pinos) · 9 cm (árbol)", ""],
    [DIB.brochetas(), "Brochetas, mondadientes, alambre 1 mm", "Troncos, clavos y armazón de figuras", ""],
    [DIB.pvc(), "PVC espumado (sintra) 3 mm", "Disco de la pista: Ø 9.5 cm", ""],
  ], [m(1), m(2), m(4), m(5), m(6), m(7), m(7) + 0.6, m(7) + 1.2]);
  its.forEach((it) => (it.style.padding = "12px 20px"));
  const nota = nuevo("div", "pastilla", `${emo("💡", 26)}Sin foam extruido: tecnopor de alta densidad`, its[1].querySelector(".det").parentNode, "margin-top:8px;font-size:20px;padding:8px 16px");
  pop(nota, m(3));
  salida();
};

ESCENAS.mat_acabado = () => {
  const its = materiales("Materiales · 2", "El <span class='acento'>acabado</span>", [
    [DIB.balde(), "Masilla drywall (pasta muro) + cola", "Sellar el foam, nieve gruesa y uniones", ""],
    [DIB.mica(), "Mica · celofán amarillo · albanene", "Las 3 capas de cada ventana", ""],
    [DIB.imprimante(), "Imprimante blanco + acrílicos", "Base para pintar todo", ""],
    [DIB.barniz(), "Barniz acrílico brillante", "Hielo de la pista y agua del río", ""],
    [DIB.escarcha(), "Bicarbonato + escarcha iridiscente", "La nieve y su brillo", ""],
    [DIB.barrasilicona(), "Barras de silicona transparentes", "Carámbanos y el agua del río", ""],
  ], [m(1), m(2), m(3), m(4), m(5), m(6)]);
  const colores = [["#f8fafc", "Blanco"], ["#111827", "Negro"], ["#8a4b2a", "Siena tostada"], ["#8e3b2c", "Rojo óxido"], ["#e0412f", "Rojo bermellón"],
    ["#c8932f", "Ocre"], ["#f2c94c", "Amarillo"], ["#3e8e41", "Verde hoja"], ["#2f4fb5", "Azul ultramar"]];
  const pal = nuevo("div", "tarjeta", "", esc, "position:absolute;left:110px;top:760px;width:1700px;padding:16px 24px;display:flex;justify-content:space-between");
  const sw = colores.map(([c, n]) => nuevo("div", "", `<div style="width:54px;height:54px;border-radius:50%;background:${c};border:2px solid rgba(255,255,255,.3);margin:0 auto"></div><div style="font-size:18px;font-weight:600;margin-top:8px">${n}</div>`, pal, "text-align:center;width:170px"));
  subir(pal, m(3) + 0.4);
  pop(sw, m(3) + 0.7, { stagger: 0.12 });
  salida();
};

ESCENAS.mat_electronica = () => {
  const its = materiales("Materiales · 3", "La <span class='acento'>electrónica</span>", [
    [DIB.led(), "LEDs blanco cálido", "8 de 5 mm difusos (adentro) + 8 de 3 mm transparentes (foquitos)", "16"],
    [DIB.ledrgb(), "LEDs RGB de cambio lento", "De 2 patas · cambian de color solos", "6"],
    [DIB.led("#93c5fd", "#3b82f6"), "LED azul de 5 mm", "La luz del río", "1"],
    [DIB.resistencia(), "Resistencias de ¼ W", "<b>20 × 220 Ω</b> · <b>10 × 100 Ω</b>", ""],
    [DIB.usb(), "Cable USB + interruptor pequeño", "La entrada de energía", ""],
    [DIB.placa(), "Placa perforada + cable rojo y negro", "Más termocontraíble y estaño", ""],
    [DIB.motor(), "Motorreductor N20 · 6 V · 10 RPM", "Con su soporte y rueda para eje de 3 mm", "1"],
    [DIB.cargador(), "Cargador de celular 5 V · 1 A", "Alimenta todo por USB", "1"],
  ], [m(1), m(2), m(3), m(4), m(5), m(5) + 0.8, m(6), m(7)]);
  its.forEach((it) => (it.style.padding = "12px 20px"));
  its.forEach((it) => it.querySelectorAll(".det b").forEach((b) => (b.style.color = "var(--oro)")));
  salida();
};

// ============================================================== MEDIDAS
function plano(padre, x, y, k, op = {}) {
  // planta de la villa vista desde arriba; k = píxeles por cm
  const s = svg(x, y, 32 * k + 2, 24 * k + 2, padre);
  const R = (cx, cy, w, h, attrs) => el("rect", { x: cx * k, y: cy * k, width: w * k, height: h * k, ...attrs }, s);
  const C = (cx, cy, r, attrs) => el("circle", { cx: cx * k, cy: cy * k, r: r * k, ...attrs }, s);
  const P = {};
  P.base = R(0, 0, 32, 24, { fill: "rgba(240,246,255,.07)", stroke: "#cfe0ff", "stroke-width": 3, rx: 6 });
  P.meseta = g(s);
  el("rect", { x: 0, y: 0, width: 32 * k, height: 9 * k, fill: "rgba(240,163,191,.16)", stroke: "#f0a3bf", "stroke-width": 2, "stroke-dasharray": "10 8" }, P.meseta);
  P.casas = g(s);
  const casa = (cx, cy, w, h, nombre, col = "rgba(252,179,51,.22)") => {
    el("rect", { x: cx * k, y: cy * k, width: w * k, height: h * k, fill: col, stroke: "#fcb333", "stroke-width": 2, rx: 3 }, P.casas);
    texto(P.casas, (cx + w / 2) * k, (cy + h / 2) * k + 7, nombre, "lbl-s", "middle", { style: "font-weight:700;fill:#ffe2a8" });
  };
  casa(2.5, 2, 8, 5, "Tudor");
  casa(11, 1.5, 9, 6, "Iglesia");
  el("rect", { x: 11.3 * k, y: 1.8 * k, width: 3.5 * k, height: 3.5 * k, fill: "rgba(252,179,51,.25)", stroke: "#fcb333", "stroke-width": 1.5, "stroke-dasharray": "5 4" }, P.casas);
  casa(20.5, 2, 6, 5, "Arco");
  P.pinos = g(s);
  [[10.8, 7.8, 1.2], [27.8, 3, 1.7], [30.2, 6.2, 1.5], [28.6, 8.2, 1.1], [1.6, 21, 1.2]].forEach(([a, b, r]) =>
    el("circle", { cx: a * k, cy: b * k, r: r * k, fill: "rgba(67,196,122,.35)", stroke: "#43c47a", "stroke-width": 2 }, P.pinos));
  P.pista = g(s);
  el("circle", { cx: 9 * k, cy: 16.5 * k, r: 5 * k, fill: "rgba(191,230,255,.25)", stroke: "#bfe6ff", "stroke-width": 3 }, P.pista);
  texto(P.pista, 9 * k, 16.5 * k + 8, "Pista", "lbl", "middle");
  P.rio = g(s);
  camino(P.rio, `M${15 * k},${9 * k} L${17.5 * k},${9 * k} Q${17 * k},${16 * k} ${18 * k},${24 * k} L${15 * k},${24 * k} Q${15.4 * k},${16 * k} ${15 * k},${9 * k} Z`, "#60a5fa", 2, "rgba(59,130,246,.35)");
  el("rect", { x: 14.2 * k, y: 8.2 * k, width: 4.1 * k, height: 1.6 * k, fill: "rgba(160,170,190,.5)", stroke: "#cfd6e2", "stroke-width": 2, rx: 3 }, P.rio);
  texto(P.rio, 16.4 * k, 9.4 * k, "puente", "lbl-s", "middle", { style: "font-size:15px" });
  P.frente = g(s);
  el("circle", { cx: 19.4 * k, cy: 19.4 * k, r: 2.2 * k, fill: "rgba(67,196,122,.4)", stroke: "#43c47a", "stroke-width": 2.5 }, P.frente);
  texto(P.frente, 19.4 * k, 19.4 * k + 7, "Árbol", "lbl-s", "middle", { style: "font-weight:700;fill:#c9ffe0" });
  el("rect", { x: 22 * k, y: 16.5 * k, width: 9.8 * k, height: 6 * k, fill: "rgba(252,179,51,.22)", stroke: "#fcb333", "stroke-width": 2, rx: 3 }, P.frente);
  texto(P.frente, 26.9 * k, 19.5 * k + 7, "Panadería", "lbl-s", "middle", { style: "font-weight:700;fill:#ffe2a8" });
  el("circle", { cx: 31 * k, cy: 23.2 * k, r: 0.7 * k, fill: "#f8fafc" }, P.frente);
  P.s = s; P.k = k;
  return P;
}

ESCENAS.planta = () => {
  cabecera("Medidas", "Vista desde <span class='acento'>arriba</span>");
  const k = 25;
  const P = plano(esc, 1000, 270, k);
  const s = P.s;
  const c1 = cota(s, 0, 0, 32 * k, 0, "32 cm", -26);
  const c2 = cota(s, 0, 0, 0, 24 * k, "24 cm", 30);
  const c3 = cota(s, 32 * k, 0, 32 * k, 9 * k, "9 cm", -34);
  const c4 = cota(s, 4 * k, 16.5 * k, 14 * k, 16.5 * k, "Ø 10 cm", 0);
  const c5 = cota(s, 15 * k, 24 * k, 18 * k, 24 * k, "2.5 cm", 26);
  tl.from([P.base, c1, c2], { opacity: 0, duration: 0.6, stagger: 0.2 }, m(0) + 0.3);
  aparecer([P.meseta, P.casas, c3], m(2), 0.7);
  aparecer(P.pinos, m(2) + 0.6);
  aparecer([P.pista], m(3), 0.6); aparecer(c4, m(3) + 0.5);
  aparecer([P.rio], m(4), 0.6); aparecer(c5, m(4) + 0.5);
  aparecer(P.frente, m(5), 0.7);
  const med = nuevo("div", "tarjeta panel", `<div class="grande">32 × 24 cm</div><div class="pd" style="font-size:26px">y unos <b>28 cm</b> de alto hasta la punta de la torre</div>`, esc, "left:110px;top:300px;width:780px");
  subir(med, m(0) + 0.4);
  const tip = nuevo("div", "tip", `${emo("🖨️", 40)}<span>Imprime tu foto a <b>32 cm</b> de ancho y mide cada casa con la regla</span>`, esc, "left:110px;top:480px;width:780px");
  subir(tip, m(1) + 0.3);
  const ley = nuevo("div", "", "", esc, "position:absolute;left:110px;top:640px;width:780px;display:grid;gap:12px");
  const ls = [["#f0a3bf", "Atrás, nivel alto de 9 cm: tudor, iglesia y casa del arco", 2], ["#bfe6ff", "Adelante izquierda: pista de Ø 10 cm", 3],
    ["#60a5fa", "Centro: el río y el puente", 4], ["#fcb333", "Adelante derecha: panadería, árbol y muñeco", 5]]
    .map(([c, t, i]) => { const e = nuevo("div", "", `<span style="width:18px;height:18px;border-radius:5px;background:${c};display:inline-block"></span>${t}`, ley, "display:flex;gap:14px;align-items:center;font-size:23px;font-weight:600"); subir(e, m(i) + 0.2); return e; });
  salida();
};

ESCENAS.alzado = () => {
  cabecera("Medidas", "Vista de <span class='acento'>frente</span>");
  const v = villa(esc, 860, 210, 960, { luces: 0.3, motor: 0 });
  const s = svg(0, 0, 1920, 1080);
  const P = (x, y) => v.punto(x, y);
  const vc = (x, y1, y2, t, d) => { const a = P(x, y1), b = P(x, y2); return cota(s, a[0], a[1], b[0], b[1], t, d); };
  const cBase = vc(950, 642, 722, "5.5 cm", -40);
  const cMes = vc(110, 500, 470, "+2.5", 40);
  const pill = (x, y, t) => { const [px, py] = P(x, y); const gr = g(s); const w = t.length * 12 + 26; el("rect", { x: px - w / 2, y: py - 18, width: w, height: 36, rx: 18, fill: "#0b1528", stroke: "#fcb333", "stroke-width": 2 }, gr); texto(gr, px, py + 8, t, "cota-t", "middle"); return gr; };
  const pT = pill(235, 236, "11 cm"), pI = pill(470, 230, "12 cm"), pTo = pill(376, 40, "torre 20 cm");
  const pP = pill(780, 375, "10 cm"), pA = pill(585, 402, "9 cm"), pPi = pill(785, 190, "6–12 cm");
  const pF = pill(256, 420, "3.5 cm"), pM = pill(930, 548, "4.5 cm");
  pop([cBase], m(1) + 0.2); pop(cMes, m(1) + 2.0);
  pop([pT, pI, pTo], m(2) + 0.3, { stagger: 0.9 });
  pop([pP, pA, pPi], m(3) + 0.2, { stagger: 0.8 });
  pop([pF, pM], m(4) + 0.2, { stagger: 0.8 });
  const filas = [["Base adelante", "5.5 cm", 1], ["Nivel de atrás", "+ 2.5 cm", 1], ["Casa tudor", "11 cm", 2], ["Iglesia", "12 cm", 2], ["Torre", "20 cm", 2],
    ["Panadería", "10 cm", 3], ["Árbol de Navidad", "9 cm", 3], ["Pinos", "6 a 12 cm", 3], ["Figuras", "3.5 cm", 4], ["Muñeco de nieve", "4.5 cm", 4]];
  const tb = nuevo("div", "tarjeta", `<table class="tabla" style="width:100%"><tr><th>Pieza</th><th>Alto</th></tr>${filas.map(([a, b]) => `<tr><td>${a}</td><td class="num">${b}</td></tr>`).join("")}</table>`, esc, "position:absolute;left:110px;top:290px;width:640px;padding:12px 16px");
  tb.querySelectorAll("td").forEach((td) => (td.style.padding = "7px 16px"));
  subir(tb, m(0) + 0.3);
  const trs = [...tb.querySelectorAll("tr")].slice(1);
  trs.forEach((tr, i) => tl.from(tr, { opacity: 0.25, duration: 0.4 }, m(filas[i][2]) + 0.1));
  salida();
};

// ============================================================== PASO 1 · BASE
ESCENAS.paso1 = () => {
  cabecera("Paso 1", "La <span class='acento'>base</span>");
  pasos(["Corta el MDF de <b>32 × 24 cm</b> y lija los bordes",
    "Foam de <b>5 cm</b> del mismo tamaño · varias pasadas, hoja nueva",
    "Foam de <b>2.5 cm</b>: franja de <b>32 × 9 cm</b> (nivel de atrás)",
    "<b>No pegues todavía:</b> primero se talla"], 110, 300, 760, [m(1), m(2), m(3), m(4)]);
  const s = svg(900, 260, 940, 640);
  const P = iso(390, 210, 13);
  const mdf = cajaIso(s, P, 0, 0, 0, 32, 24, 0.5, MDF_TOP, MDF, MDF_LADO);
  const foam = cajaIso(s, P, 0, 0, 3.5, 32, 24, 5, FOAM_TOP, FOAM, FOAM_LADO);
  const franja = cajaIso(s, P, 0, 0, 12, 32, 9, 2.5, "#f9d3e1", "#f2b2c9", "#dc93ad");
  const lab = (gr, pts, t) => { const [x, y] = pts; return etiqueta(s, x, y, x + 120, y + 50, t); };
  const e1 = etiqueta(s, ...P(32, 24, 0.25), 760, 560, "MDF 5 mm", "32 × 24 cm");
  const e2 = etiqueta(s, ...P(32, 12, 6), 830, 380, "Foam 5 cm", "32 × 24 cm");
  const e3 = etiqueta(s, ...P(32, 4.5, 13.25), 820, 150, "Foam 2.5 cm", "franja 32 × 9 cm");
  tl.from(mdf, { y: -80, opacity: 0, duration: 0.8, ease: "bounce.out" }, m(1));
  pop(e1, m(1) + 0.6);
  tl.from(foam, { y: -120, opacity: 0, duration: 0.9, ease: "bounce.out" }, m(2));
  pop(e2, m(2) + 0.7);
  tl.from(franja, { y: -120, opacity: 0, duration: 0.9, ease: "bounce.out" }, m(3));
  pop(e3, m(3) + 0.7);
  const cut = nuevo("div", "pastilla", `${DIB.cuter().replace("<svg", "<svg width='40' height='40'")}Varias pasadas suaves`, esc, "position:absolute;left:960px;top:860px");
  pop(cut, m(2) + 1.4);
  salida();
};

// ============================================================== PASO 2 · TALLAR
ESCENAS.paso2 = () => {
  cabecera("Paso 2", "Tallar el <span class='acento'>terreno</span>");
  pasos(["Pista: círculo de <b>Ø 10 cm</b> que atraviesa todo el foam",
    "Río: canaleta de <b>2.5 cm</b> de ancho y <b>8 mm</b> de hondo",
    "Borde de roca: cortes irregulares + <b>papel aluminio</b> arrugado",
    "Por debajo: canales de <b>1 cm</b> hasta el hueco de la pista",
    "Atrás: ranura del <b>interruptor</b> y agujero del <b>USB</b>",
    "Pega con <b>cola + mondadientes</b>, peso encima, <b>1 noche</b>"], 110, 280, 780, [m(1), m(2), m(3), m(4), m(5), m(6)]).forEach((p) => p.parentNode.classList.add("compacto"));
  const k = 24;
  // vista de arriba
  const arriba = g(svg(1000, 300, 32 * k, 24 * k));
  const sA = arriba.ownerSVGElement;
  el("rect", { x: 0, y: 0, width: 32 * k, height: 24 * k, fill: FOAM, stroke: "#0d1424", "stroke-width": 2, rx: 4 }, arriba);
  el("rect", { x: 0, y: 0, width: 32 * k, height: 9 * k, fill: FOAM_TOP, opacity: 0.6 }, arriba);
  const plumon = g(arriba);
  [[2.5, 2, 8, 5], [11, 1.5, 9, 6], [20.5, 2, 6, 5], [22, 16.5, 9.8, 6]].forEach(([a, b, w, h]) => el("rect", { x: a * k, y: b * k, width: w * k, height: h * k, fill: "none", stroke: "#1f2937", "stroke-width": 2, "stroke-dasharray": "6 5" }, plumon));
  el("circle", { cx: 19.4 * k, cy: 19.4 * k, r: 2.2 * k, fill: "none", stroke: "#1f2937", "stroke-width": 2, "stroke-dasharray": "6 5" }, plumon);
  const hueco = el("circle", { cx: 9 * k, cy: 16.5 * k, r: 5 * k, fill: "#0b1222", stroke: "#ef4444", "stroke-width": 4, "stroke-dasharray": "12 8" }, arriba);
  const rio = camino(arriba, `M${15 * k},${9 * k} L${17.5 * k},${9 * k} Q${17 * k},${16 * k} ${18 * k},${24 * k} L${15 * k},${24 * k} Q${15.4 * k},${16 * k} ${15 * k},${9 * k} Z`, "#ef4444", 3, "#c0688a", { "stroke-dasharray": "10 7" });
  let roca = `M0,${24 * k}`;
  const rr = azar(5);
  for (let xx = 0; xx <= 32 * k; xx += 22) roca += ` L${xx},${24 * k - 6 - rr() * 16}`;
  const rocas = camino(arriba, roca + ` L${32 * k},${24 * k} Z`, "#59606e", 2, "#7d8595");
  const cT = cota(sA, 4 * k, 16.5 * k, 14 * k, 16.5 * k, "Ø 10 cm");
  const cR = cota(sA, 15 * k, 12 * k, 17.3 * k, 12 * k, "2.5", -30);
  const tit1 = texto(sA, 0, -14, "Vista de arriba", "lbl-oro");
  // vista de abajo (volteada)
  const abajo = g(svg(1000, 300, 32 * k, 24 * k));
  const sB = abajo.ownerSVGElement;
  el("rect", { x: 0, y: 0, width: 32 * k, height: 24 * k, fill: FOAM_LADO, stroke: "#0d1424", "stroke-width": 2, rx: 4 }, abajo);
  const X = (x) => (32 - x) * k;
  el("circle", { cx: X(9), cy: 16.5 * k, r: 5 * k, fill: "#0b1222", stroke: "#0d1424", "stroke-width": 2 }, abajo);
  const canales = g(abajo);
  [[[6.5, 4.5], [8, 12]], [[15.5, 4.5], [11, 12.5]], [[23.5, 4.5], [12.5, 14]], [[26.9, 19.5], [14, 17]], [[19.4, 19.4], [14, 17.5]], [[16.4, 9.2], [13, 13.5]], [[26, 0.6], [13.4, 14.4]]]
    .forEach(([[a, b], [c, d]]) => camino(canales, `M${X(a)},${b * k} L${X(c)},${d * k}`, "#7a2e4b", 1 * k, "none", { "stroke-linecap": "round", opacity: 0.9 }));
  const marcasCasas = g(abajo);
  [[6.5, 4.5, "tudor"], [15.5, 4.5, "iglesia"], [23.5, 4.5, "arco"], [26.9, 19.5, "panadería"], [19.4, 19.4, "árbol"], [16.4, 9.2, "puente"]]
    .forEach(([a, b, t]) => { el("circle", { cx: X(a), cy: b * k, r: 9, fill: "#fcb333" }, marcasCasas); texto(marcasCasas, X(a), b * k - 16, t, "lbl-s", "middle", { style: "font-weight:700;fill:#fff" }); });
  const salidaUSB = g(abajo);
  el("rect", { x: X(27.5), y: -4, width: 3 * k, height: 1.2 * k, fill: "#111827", stroke: "#fcb333", "stroke-width": 2, rx: 3 }, salidaUSB);
  texto(salidaUSB, X(26), -18, "interruptor + USB", "lbl-oro", "middle");
  const tit2 = texto(sB, 32 * k, 24 * k + 34, "Vista de abajo (volteado)", "lbl-oro", "end");
  const cC = cota(sB, X(19.4) - 0.5 * k, 19.4 * k + 26, X(19.4) + 0.5 * k, 19.4 * k + 26, "1 cm", 0);
  // secuencia
  aparecer(arriba, m(0) + 0.3);
  tl.from(plumon.children, { opacity: 0, duration: 0.4, stagger: 0.25 }, m(0) + 0.6);
  tl.from(hueco, { scale: 0, transformOrigin: `${9 * k}px ${16.5 * k}px`, duration: 0.6, ease: "back.out(1.6)" }, m(1) + 0.3);
  pop(cT, m(1) + 1.0);
  tl.from(rio, { opacity: 0, duration: 0.6 }, m(2) + 0.2); pop(cR, m(2) + 0.8);
  tl.from(rocas, { opacity: 0, y: 20, duration: 0.6 }, m(3) + 0.2);
  tl.to(arriba.ownerSVGElement, { rotationY: 90, duration: 0.5, ease: "power2.in" }, m(4));
  tl.set(arriba.ownerSVGElement, { opacity: 0 }, m(4) + 0.5);
  tl.from(abajo.ownerSVGElement, { rotationY: -90, opacity: 0, duration: 0.5, ease: "power2.out" }, m(4) + 0.5);
  trazar(canales.children, m(4) + 1.0, 1.4);
  pop(marcasCasas.children, m(4) + 1.2, { stagger: 0.1 });
  pop(cC, m(4) + 2.4);
  pop(salidaUSB, m(5) + 0.2);
  const pega = nuevo("div", "", `<div class="pastilla">${DIB.cola().replace("<svg", "<svg width='40' height='40'")}Cola sintética</div><div class="pastilla">${emo("📚", 30)}Peso encima</div><div class="pastilla">${emo("🌙", 30)}1 noche</div>`, esc, "position:absolute;left:1040px;top:560px;width:700px;display:flex;flex-wrap:wrap;justify-content:center;gap:14px");
  pop(pega.children, m(6) + 0.3, { stagger: 0.3 });
  tl.to(sB, { opacity: 0.35, duration: 0.5 }, m(6));
  salida();
};

// ============================================================== PASO 3 · CASAS
ESCENAS.paso3 = () => {
  cabecera("Paso 3", "Las <span class='acento'>casas</span>", "Cartón pluma de 5 mm");
  const lista = pasos(["4 paredes: <b>2 frentes</b> (pentágono) + <b>2 laterales</b>",
    "Tudor: frente de <b>8 cm</b> de ancho, <b>7 cm</b> de pared, <b>11 cm</b> de punta · laterales <b>4 × 7</b>",
    "Lateral = fondo − <b>1 cm</b> (2 cartones de 5 mm)",
    "Corta ventanas y puertas <b>antes</b> de armar",
    "Silicona + alfileres · escuadra a <b>90°</b>",
    "Abiertas por abajo · todas las medidas en la tabla"], 110, 300, 760, [m(1), m(2), m(3), m(4), m(5), m(6)]);
  lista[0].parentNode.classList.add("compacto");
  const k = 27;
  const s = svg(930, 300, 900, 560);
  const plant = g(s);
  const frente = (ox) => {
    const gr = g(plant);
    poli(gr, [[ox, 11 * k], [ox, 4 * k], [ox + 4 * k, 0], [ox + 8 * k, 4 * k], [ox + 8 * k, 11 * k]].map(([a, b]) => [a, b + 20]), "#f4f6fa", "#0d1424", 2.5);
    return gr;
  };
  const f1 = frente(0), f2 = frente(9 * k);
  const lat1 = poli(g(plant), [[18 * k, 4 * k + 20], [22 * k, 4 * k + 20], [22 * k, 11 * k + 20], [18 * k, 11 * k + 20]], "#e3e7ee", "#0d1424", 2.5);
  const lat2 = poli(g(plant), [[23 * k, 4 * k + 20], [27 * k, 4 * k + 20], [27 * k, 11 * k + 20], [23 * k, 11 * k + 20]], "#e3e7ee", "#0d1424", 2.5);
  const vent = g(plant);
  [[2.2, 7.5, 3.6, 2.6], [11.2, 7.5, 3.6, 2.6], [3.4, 4.2, 1.2, 1.6], [12.4, 4.2, 1.2, 1.6]].forEach(([a, b, w, h]) => el("rect", { x: a * k, y: b * k + 20, width: w * k, height: h * k, fill: "rgba(239,68,68,.12)", stroke: "#ef4444", "stroke-width": 2.5, "stroke-dasharray": "8 6" }, vent));
  el("rect", { x: 0.5 * k, y: 8.2 * k + 20, width: 1.3 * k, height: 2.8 * k, fill: "rgba(239,68,68,.12)", stroke: "#ef4444", "stroke-width": 2.5, "stroke-dasharray": "8 6" }, vent);
  const cotas = g(s);
  cota(cotas, 0, 11 * k + 20, 8 * k, 11 * k + 20, "8 cm", 30);
  cota(cotas, 0, 4 * k + 20, 0, 11 * k + 20, "7 cm", 34);
  cota(cotas, 8 * k, 20, 8 * k, 11 * k + 20, "11 cm", -40);
  cota(cotas, 18 * k, 11 * k + 20, 22 * k, 11 * k + 20, "4 cm", 30);
  cota(cotas, 27 * k, 4 * k + 20, 27 * k, 11 * k + 20, "7 cm", -34);
  const formula = nuevo("div", "tarjeta panel", `<div class="pt">${emo("🧮", 32)}Fondo 5 cm − 2 × 0.5 cm = <span style="color:var(--oro)">4 cm</span></div>`, esc, "left:1180px;top:820px;width:600px;padding:14px 22px");
  formula.style.display = "none";
  tl.set(formula, { display: "block" }, m(3));
  // casa armada (isométrica)
  const arm = g(s, { transform: "translate(250,40)" });
  const P = iso(170, 160, 26);
  cajaIso(arm, P, 0, 0, 0, 8, 5, 7, "rgba(0,0,0,0)", "#f4f6fa", "#e3e7ee");
  poli(arm, [P(0, 5, 7), P(4, 5, 11), P(8, 5, 7)], "#f4f6fa");
  poli(arm, [P(2.2, 5, 1.2), P(5.8, 5, 1.2), P(5.8, 5, 3.8), P(2.2, 5, 3.8)], "#2f3546");
  poli(arm, [P(3.4, 5, 4.6), P(4.6, 5, 4.6), P(4.6, 5, 6.2), P(3.4, 5, 6.2)], "#2f3546");
  const esq = P(8, 5, 0);
  camino(arm, `M${esq[0] - 30},${esq[1] - 12} L${esq[0] - 30},${esq[1] - 52} M${esq[0] - 30},${esq[1] - 12} L${esq[0] + 4},${esq[1] - 32}`, "#fcb333", 4);
  texto(arm, esq[0] + 18, esq[1] - 40, "90°", "lbl-oro");
  [P(0.3, 5, 6.5), P(7.7, 5, 6.5), P(8, 2.5, 6.6)].forEach(([a, b]) => { el("circle", { cx: a, cy: b - 8, r: 6, fill: "#ef4444" }, arm); linea(arm, a, b - 2, a, b + 10, "#cfd6e2", 2); });
  texto(arm, 170, 430, "Abierta por abajo", "lbl-s", "middle");
  arm.style.opacity = 0;
  // tabla de todas las casas
  const tabla = nuevo("div", "tarjeta", `<table class="tabla"><tr><th>Casa</th><th>Frente: ancho × pared × punta</th><th>Laterales</th></tr>
    <tr><td>Tudor</td><td class="num">8 × 7 × 11 cm</td><td class="num">4 × 7</td></tr>
    <tr><td>Iglesia</td><td class="num">9 × 8 × 12 cm</td><td class="num">5 × 8</td></tr>
    <tr><td>Torre grande</td><td class="num">caja 3.5 × 3.5 × 14 cm</td><td class="num">—</td></tr>
    <tr><td>Casa del arco</td><td class="num">6 × 7 × 10 cm</td><td class="num">4 × 7</td></tr>
    <tr><td>Panadería</td><td class="num">10 × 6 × 10 cm</td><td class="num">5 × 6</td></tr></table>`, esc, "position:absolute;left:930px;top:330px;padding:14px 18px;width:880px");
  tabla.style.opacity = 0;
  pop([f1, f2, lat1.parentNode, lat2.parentNode], m(1), { stagger: 0.15 });
  aparecer(cotas, m(2) + 0.3);
  tl.from([lat1, lat2], { fill: "#fcb333", duration: 0.8, repeat: 1, yoyo: true }, m(3) + 0.3);
  tl.from(vent.children, { opacity: 0, scale: 0.8, transformOrigin: "50% 50%", duration: 0.4, stagger: 0.25 }, m(4) + 0.3);
  tl.to([plant, cotas], { opacity: 0, duration: 0.5 }, m(5));
  tl.to(arm, { opacity: 1, duration: 0.6 }, m(5) + 0.3);
  tl.set(formula, { display: "none" }, m(5));
  tl.to(arm, { opacity: 0, duration: 0.4 }, m(6));
  tl.to(tabla, { opacity: 1, duration: 0.6 }, m(6) + 0.3);
  salida();
};

// ============================================================== PASO 4 · TECHOS Y TORRES
ESCENAS.paso4 = () => {
  cabecera("Paso 4", "Techos y <span class='acento'>torres</span>");
  pasos(["Techo: 2 rectángulos de cartulina con <b>0.5 cm</b> de alero",
    "Torre grande: caja de <b>3.5 × 3.5 × 14 cm</b>",
    "Aguja: 4 triángulos de <b>3.8 cm</b> de base y <b>6.3 cm</b> de alto",
    "Cinta por dentro · punta afinada con <b>masilla epóxica</b>",
    "Torre pequeña de <b>2.5 cm</b> (aguja de 3 cm) · chimeneas de <b>1 cm</b>"], 110, 300, 760, [m(1), m(2), m(3), m(4), m(5)]);
  const s = svg(920, 290, 920, 600);
  // techo con alero (vista de frente)
  const techo = g(s);
  poli(techo, [[40, 300], [40, 170], [150, 90], [260, 170], [260, 300]], "#f4f6fa");
  poli(techo, [[18, 186], [150, 74], [158, 82], [26, 194]], "#a3abbc");
  poli(techo, [[282, 186], [150, 74], [142, 82], [274, 194]], "#8b94a7");
  cota(techo, 18, 186, 40, 186, "0.5", 34);
  texto(techo, 150, 340, "alero de 0.5 cm por lado", "lbl-s", "middle");
  // torre isométrica
  const torre = g(s, { transform: "translate(330,0)" });
  const P = iso(110, 410, 22);
  cajaIso(torre, P, 0, 0, 0, 3.5, 3.5, 14, "#e3e7ee", "#f4f6fa", "#d7dde7");
  const cT = cota(torre, ...P(3.5, 3.5, 0), ...P(3.5, 3.5, 14), "14 cm", -46);
  const aguja = g(torre);
  const tope = P(1.75, 1.75, 20);
  poli(aguja, [P(-0.15, 3.65, 14), P(3.65, 3.65, 14), tope], "#a3abbc");
  poli(aguja, [P(3.65, 3.65, 14), P(3.65, -0.15, 14), tope], "#8b94a7");
  el("circle", { cx: tope[0], cy: tope[1] + 4, r: 7, fill: "#9aa4b8", stroke: "#0d1424", "stroke-width": 1.5 }, aguja);
  const masillaE = etiqueta(torre, tope[0], tope[1] + 4, tope[0] + 110, tope[1] - 10, "Masilla", "punta fina");
  // desarrollo de la aguja: 4 triángulos
  const red = g(s, { transform: "translate(640,150)" });
  const kk = 26, b = 3.8 * kk, h = 6.3 * kk;
  [0, 1, 2, 3].forEach((i) => poli(red, [[i * b * 0.5, h], [i * b * 0.5 + b / 2, 0], [i * b * 0.5 + b, h]].map(([a, c]) => [a - (i % 2 ? 0 : 0), i % 2 ? h - c : c]), i % 2 ? "#a3abbc" : "#b8c0cf"));
  cota(red, 0, h, b, h, "3.8 cm", 30);
  cota(red, b * 2.5 + 10, 0, b * 2.5 + 10, h, "6.3 cm", -2);
  const cinta = nuevo("div", "pastilla", `${emo("🩹", 28)}Cinta por dentro`, esc, "position:absolute;left:1560px;top:640px");
  // torre pequeña y chimeneas
  const extras = g(s, { transform: "translate(560,430)" });
  const P2 = iso(60, 40, 16);
  cajaIso(extras, P2, 0, 0, 0, 2.5, 2.5, 6, "#e3e7ee", "#f4f6fa", "#d7dde7");
  const t2 = P2(1.25, 1.25, 9);
  poli(extras, [P2(-0.1, 2.6, 6), P2(2.6, 2.6, 6), t2], "#a3abbc");
  poli(extras, [P2(2.6, 2.6, 6), P2(2.6, -0.1, 6), t2], "#8b94a7");
  texto(extras, 60, 150, "Torre 2.5 cm", "lbl-s", "middle");
  const P3 = iso(220, 80, 30);
  [0, 2].forEach((d) => cajaIso(extras, P3, d, 0, 0, 1, 1, 1, FOAM_TOP, FOAM, FOAM_LADO));
  texto(extras, 300, 150, "Chimeneas 1 cm", "lbl-s", "middle");
  aparecer(techo, m(1));
  aparecer(torre.children[0], m(2)); pop(cT, m(2) + 0.6);
  aparecer(red, m(3)); tl.from(red.children, { opacity: 0, y: 20, stagger: 0.2, duration: 0.4 }, m(3) + 0.2);
  aparecer(aguja, m(4)); pop(masillaE, m(4) + 0.8); pop(cinta, m(4) + 0.3);
  aparecer(extras, m(5));
  salida();
};

// ============================================================== PASO 5 · TEXTURAS
ESCENAS.paso5 = () => {
  cabecera("Paso 5", "Las <span class='acento'>texturas</span>", "Lo que hace que se vea de fábrica");
  const W = 540, H = 290;
  const pos = [[110, 300], [690, 300], [1270, 300], [400, 620], [980, 620]];
  const titulos = [["🧱", "Ladrillos", "Despega el papel del cartón pluma y raya con lapicero sin tinta: filas de <b>4 mm</b>, cortes cada <b>8 mm</b>"],
    ["🪵", "Vigas tudor", "Tiras de cartulina de <b>2 mm</b>, en cruz y en diagonal"],
    ["🏠", "Tejas", "Tiras de <b>1 cm</b> con cortes cada <b>7 mm</b>, de abajo hacia arriba"],
    ["🪟", "Marcos y barritas", "Tiras finas de cartulina · barritas de <b>1 mm</b>"],
    ["🥖", "Toldos y letrero", "Cartulina doblada en ondas · letrero de <b>4 × 1 cm</b>"]];
  const paneles = titulos.map(([e, t, d], i) => tarjetaPanel(pos[i][0], pos[i][1], W, H, `${emo(e, 30)}${t}`, d));
  const dib = paneles.map((p) => svg(0, 0, W - 52, 140, p, `0 0 ${W - 52} 140`));
  dib.forEach((s) => { s.style.position = "relative"; s.style.marginTop = "12px"; s.style.left = "0"; s.style.top = "0"; });
  // ladrillos con lapicero
  const l = dib[0];
  el("rect", { x: 0, y: 0, width: 300, height: 130, fill: "#f0a3bf", rx: 6 }, l);
  for (let f = 0; f < 6; f++) {
    linea(l, 0, f * 22, 300, f * 22, "#9c4b67", 2);
    for (let c = 0; c < 8; c++) linea(l, c * 44 + (f % 2) * 22, f * 22, c * 44 + (f % 2) * 22, f * 22 + 22, "#9c4b67", 2);
  }
  const lap = g(l);
  el("rect", { x: 300, y: 40, width: 120, height: 14, rx: 6, fill: "#2563eb", transform: "rotate(-25 300 47)" }, lap);
  el("path", { d: "M300,47 L285,52 L300,56 Z", fill: "#cfd6e2", transform: "rotate(-25 300 47)" }, lap);
  cota(l, 330, 66, 330, 88, "4 mm", -40);
  tl.fromTo(lap, { x: -40 }, { x: 0, duration: 1.2, repeat: 3, yoyo: true, ease: "sine.inOut" }, m(1) + 0.5);
  // vigas
  const v = dib[1];
  el("rect", { x: 0, y: 0, width: 420, height: 130, fill: "#ead9b4", rx: 6 }, v);
  [[0, 0, 0, 130], [140, 0, 140, 130], [280, 0, 280, 130], [420, 0, 420, 130], [0, 65, 420, 65], [0, 0, 140, 65], [140, 0, 0, 65], [280, 65, 420, 130], [420, 65, 280, 130]]
    .forEach(([a, b, c, d]) => linea(v, a, b, c, d, "#3d261b", 9));
  // tejas que se pegan por filas
  const tj = dib[2];
  const filasT = [];
  for (let f = 0; f < 5; f++) {
    const gr = g(tj);
    const y = 110 - f * 22;
    for (let c = 0; c < 12; c++) el("path", { d: `M${c * 36 + (f % 2) * 18},${y} q18,26 36,0 v-22 h-36 Z`, fill: f % 2 ? "#8a4b2a" : "#7a3a2b", stroke: "#3b1810", "stroke-width": 1.5 }, gr);
    filasT.push(gr);
  }
  filasT.forEach((gr, i) => tl.from(gr, { y: 20, opacity: 0, duration: 0.4 }, m(3) + 0.4 + i * 0.5));
  // ventana con marco
  const vm = dib[3];
  el("rect", { x: 160, y: 4, width: 130, height: 126, fill: "#2f3546", stroke: "#f3efe6", "stroke-width": 10 }, vm);
  linea(vm, 225, 4, 225, 130, "#f3efe6", 4); linea(vm, 160, 64, 290, 64, "#f3efe6", 4);
  el("rect", { x: 150, y: 128, width: 150, height: 10, fill: "#f3efe6" }, vm);
  // toldo y letrero
  const tt = dib[4];
  let d = "M20,60";
  for (let i = 0; i < 10; i++) d += ` q15,24 30,0`;
  camino(tt, `M20,20 L320,20 L320,60 ${d.replace("M20,60", "")}`.replace("L320,60", "L320,60"), "none", 0, "none");
  for (let i = 0; i < 10; i++) {
    el("path", { d: `M${20 + i * 30},20 L${50 + i * 30},20 L${50 + i * 30},60 q-15,24 -30,0 Z`, fill: i % 2 ? "#fbfbf7" : "#c53b32", stroke: "#7a1f1f", "stroke-width": 1.5 }, tt);
  }
  el("rect", { x: 350, y: 30, width: 120, height: 34, rx: 4, fill: "#fbfbf7", stroke: "#7a1f1f", "stroke-width": 2 }, tt);
  texto(tt, 410, 54, "BAKERY", "", "middle", { style: "font:800 20px Inter;fill:#b91c1c" });
  cota(tt, 350, 74, 470, 74, "4 cm", 22);
  paneles.forEach((p, i) => { subir(p, m(i + 1)); resaltar(p, m(i + 1) + 0.2); if (i) normal(paneles[i - 1], m(i + 1)); });
  salida();
};

// ============================================================== PASO 6 · ÁRBOLES
ESCENAS.paso6 = () => {
  cabecera("Paso 6", "Los <span class='acento'>árboles</span>");
  pasos(["Conos de tecnopor de <b>6, 9 y 12 cm</b>",
    "Brocheta como tronco · <b>1 cm</b> afuera",
    "Masilla en capas, <b>de abajo hacia arriba</b>",
    "Árbol de Navidad: cono de <b>9 cm</b> + <b>4 agujeros</b> de 5 mm",
    "Túnel por el centro para los <b>cables</b>",
    "Estrella de <b>silicona transparente</b> de 2 cm"], 110, 300, 760, [m(1), m(2), m(3), m(4), m(5), m(6)])[0].parentNode.classList.add("compacto");
  const s = svg(920, 270, 920, 620);
  const k = 30;
  const conos = g(s);
  [[60, 6], [190, 9], [330, 12]].forEach(([x, h]) => {
    poli(conos, [[x - 1.6 * k * h / 12 - 10, 520], [x, 520 - h * k], [x + 1.6 * k * h / 12 + 10, 520]], "#f4f6fa");
    texto(conos, x, 590, `${h} cm`, "lbl-oro", "middle");
  });
  const tronco = g(s);
  [[60], [190], [330]].forEach(([x]) => { el("rect", { x: x - 4, y: 520, width: 8, height: 34, fill: "#d6a86b" }, tronco); });
  const cTr = cota(s, 360, 520, 360, 550, "1 cm", -50);
  // pino terminado con masilla
  const pinoG = g(s);
  const pino = (cx, base, h, w) => {
    [[0, 0.42, 1], [0.28, 0.72, 0.78], [0.55, 1, 0.52]].forEach(([a, b, kk]) => {
      const yb = base - a * h * 0.9, yt = base - b * h;
      camino(pinoG, `M${cx - w * kk / 2},${yb} Q${cx},${yb - 12} ${cx + w * kk / 2},${yb} L${cx},${yt} Z`, "#174a30", 2, "#1f5c3c");
      camino(pinoG, `M${cx - w * kk / 2 * 0.9},${yb - 2} L${cx},${yt + 4}`, "#ffffff", 5, "none");
    });
  };
  pino(330, 520, 360, 120);
  const espat = nuevo("div", "pastilla", `${DIB.espatula().replace("<svg", "<svg width='40' height='40'")}Jala hacia abajo, en capas`, esc, "position:absolute;left:1000px;top:320px");
  // árbol de Navidad en corte
  const arb = g(s, { transform: "translate(470,0)" });
  const cono = poli(arb, [[90, 520], [220, 250], [350, 520]], "#f4f6fa");
  const tunel = camino(arb, "M220,262 L220,520", "#ef4444", 5, "none", { "stroke-dasharray": "10 8" });
  const hoyosG = g(arb), canalesA = g(arb);
  [[170, 440], [262, 400], [190, 350], [248, 470]].forEach(([x, y]) => {
    el("circle", { cx: x, cy: y, r: 10, fill: "#0b1222", stroke: "#fcb333", "stroke-width": 2 }, hoyosG);
    camino(canalesA, `M${x},${y} L220,${y + 30}`, "#ef4444", 2.5);
  });
  const lblCono = texto(arb, 220, 556, "Cono de 9 cm", "lbl-oro", "middle");
  const tun = etiqueta(arb, 220, 500, 380, 420, "Túnel", "para los cables");
  const est = g(arb);
  el("circle", { cx: 220, cy: 232, r: 40, fill: gradRadial(s, [[0, "#fff6d6", 0.9], [1, "#fff6d6", 0]]) }, est);
  camino(est, estrellaD(220, 232, 34, 14), "#e5e7eb", 2, "rgba(240,248,255,.8)");
  const eEst = etiqueta(arb, 250, 220, 370, 160, "Estrella", "sobre el LED");
  aparecer(conos, m(1));
  aparecer(tronco, m(2)); pop(cTr, m(2) + 0.4);
  tl.to(conos.children[4], { opacity: 0, duration: 0.6 }, m(3) + 0.2);
  tl.from(pinoG.children, { opacity: 0, y: 30, stagger: 0.25, duration: 0.5 }, m(3) + 0.2);
  pop(espat, m(3) + 0.6);
  aparecer([cono, lblCono], m(4));
  tl.from(hoyosG.children, { scale: 0, transformOrigin: "50% 50%", stagger: 0.2, duration: 0.4 }, m(4) + 0.6);
  aparecer(tunel, m(5) + 0.2);
  tl.from(canalesA.children, { drawSVG: "0%", duration: 0.8, stagger: 0.1 }, m(5) + 0.8);
  pop(tun, m(5) + 1.0);
  tl.from(est, { scale: 0, transformOrigin: "220px 232px", duration: 0.6, ease: "back.out(2)" }, m(6) + 0.3); pop(eEst, m(6) + 0.9);
  salida();
};

// ============================================================== PASO 7 · FIGURAS
ESCENAS.paso7 = () => {
  cabecera("Paso 7", "Las <span class='acento'>figuras</span>", "Compradas o de masilla epóxica");
  pasos(["Mezcla <b>partes iguales</b> · ~<b>15 min</b> para modelar",
    "Alambre de <b>3.5 cm</b> + cuerpo, cabeza, gorro y bufanda",
    "Patines: <b>2 trocitos de clip</b> en los pies",
    "Muñeco: bolitas de <b>22, 16 y 11 mm</b>",
    "Endurecer <b>1 noche</b> antes de pintar"], 110, 300, 760, [m(1), m(2), m(3), m(4), m(5)]);
  const s = svg(920, 270, 920, 620);
  // masilla
  const mas = g(s);
  el("rect", { x: 20, y: 40, width: 30, height: 110, rx: 15, fill: "#f4f6fa", stroke: "#0d1424", "stroke-width": 2 }, mas);
  el("rect", { x: 60, y: 40, width: 30, height: 110, rx: 15, fill: "#9aa4b8", stroke: "#0d1424", "stroke-width": 2 }, mas);
  texto(mas, 120, 100, "+", "grande", "middle", { style: "font:800 50px Inter;fill:#fcb333" });
  el("circle", { cx: 190, cy: 95, r: 42, fill: "#c6ccd6", stroke: "#0d1424", "stroke-width": 2 }, mas);
  texto(mas, 110, 190, "1 : 1 · un solo color", "lbl-s", "middle");
  // armazón y figura
  const fig = g(s, { transform: "translate(300,0)" });
  const alambre = camino(fig, "M100,90 L100,190 M100,120 L70,160 M100,120 L130,160 M100,190 L80,260 M100,190 L120,260 M100,90 m0,-24 a12,12 0 1 0 0.1,0", "#b8c0cf", 4);
  const cuerpo = g(fig);
  camino(cuerpo, "M78,190 L86,110 L114,110 L122,190 Z", "#0d1424", 2, "#c53b32");
  el("circle", { cx: 100, cy: 80, r: 18, fill: "#f2c9a8", stroke: "#0d1424", "stroke-width": 2 }, cuerpo);
  camino(cuerpo, "M82,76 Q100,40 118,76 Z", "#0d1424", 2, "#1f5a3d");
  el("rect", { x: 80, y: 102, width: 40, height: 10, rx: 4, fill: "#f3efe6" }, cuerpo);
  linea(cuerpo, 86, 120, 66, 160, "#c53b32", 9); linea(cuerpo, 114, 120, 134, 160, "#c53b32", 9);
  linea(cuerpo, 90, 190, 80, 258, "#2b2f3a", 9); linea(cuerpo, 110, 190, 120, 258, "#2b2f3a", 9);
  const pat = g(fig);
  linea(pat, 62, 266, 94, 266, "#e5e7eb", 4); linea(pat, 106, 266, 138, 266, "#e5e7eb", 4);
  const ePat = etiqueta(fig, 70, 266, 10, 320, "Clip", "cuchilla del patín");
  const cFig = cota(fig, 30, 56, 30, 266, "3.5 cm", 30);
  // muñeco de nieve a escala
  const mun = g(s, { transform: "translate(560,0)" });
  const px = 5;
  const bolas = [[22, 470], [16, 470 - 11 * px - 8 * px], [11, 0]];
  bolas[2][1] = bolas[1][1] - 8 * px - 5.5 * px;
  bolas.forEach(([dmm, cy]) => el("circle", { cx: 120, cy, r: dmm * px / 2, fill: "#f8fafc", stroke: "#c9d6ea", "stroke-width": 2 }, mun));
  bolas.forEach(([dmm, cy]) => cota(mun, 205, cy - dmm * px / 2, 205, cy + dmm * px / 2, `${dmm} mm`, 0));
  const deta = g(mun);
  el("rect", { x: 98, y: bolas[2][1] - 52, width: 44, height: 30, fill: "#111827" }, deta);
  el("rect", { x: 88, y: bolas[2][1] - 26, width: 64, height: 8, rx: 3, fill: "#111827" }, deta);
  camino(deta, `M92,${bolas[1][1] - 34} Q120,${bolas[1][1] - 20} 148,${bolas[1][1] - 34} L156,${bolas[1][1] + 6} L144,${bolas[1][1] + 6} L140,${bolas[1][1] - 22}`, "none", 0, "#dc2626");
  camino(deta, `M120,${bolas[2][1] + 4} L150,${bolas[2][1] + 10} L120,${bolas[2][1] + 12} Z`, "none", 0, "#f97316");
  const noche = reloj(esc, 1200, 820, "1 noche", "🌙");
  aparecer(mas, m(1));
  tl.from(alambre, { drawSVG: "0%", duration: 1.2 }, m(2) + 0.2);
  tl.from(cuerpo.children, { opacity: 0, scale: 0.8, transformOrigin: "50% 50%", stagger: 0.25, duration: 0.4 }, m(2) + 1.4);
  pop(cFig, m(2) + 0.8);
  aparecer(pat, m(3)); pop(ePat, m(3) + 0.4);
  tl.from(mun.querySelectorAll("circle"), { scale: 0, transformOrigin: "50% 50%", stagger: 0.4, duration: 0.5, ease: "back.out(2)" }, m(4) + 0.2);
  aparecer([...mun.children].slice(3, 6), m(4) + 1.6);
  aparecer(deta, m(4) + 2.4);
  pop(noche, m(5) + 0.2);
  salida();
};

// ============================================================== PASO 8 · SELLAR
ESCENAS.paso8 = () => {
  cabecera("Paso 8", "Sellar <span class='acento'>todo</span>");
  const no = nuevo("div", "aviso", `${emo("🚫", 40)}<span><b>Nunca spray</b> sobre el foam: lo derrite</span>`, esc, "left:110px;top:300px;width:760px");
  subir(no, m(0) + 0.6);
  pasos(["Masilla <b>3</b> + cola <b>1</b>, con brocha en terreno y rocas",
    "Uniones de las casas: masilla con el <b>dedo húmedo</b>",
    "Lija suave + <b>imprimante blanco</b> a todo",
    "Etapa B: <b>haz los moldes ahora</b>, antes de pintar"], 110, 420, 760, [m(1), m(2), m(3), m(4)]);
  const s = svg(940, 290, 880, 600);
  // receta 3:1
  const rec = g(s);
  [0, 1, 2].forEach((i) => { el("path", { d: `M${20 + i * 90},40 L${90 + i * 90},40 L${84 + i * 90},130 L${26 + i * 90},130 Z`, fill: "#e5e7eb", stroke: "#0d1424", "stroke-width": 2 }, rec); texto(rec, 55 + i * 90, 160, "masilla", "lbl-s", "middle"); });
  texto(rec, 310, 100, "+", "", "middle", { style: "font:800 50px Inter;fill:#fcb333" });
  el("path", { d: "M350,40 L420,40 L414,130 L356,130 Z", fill: "#f8fafc", stroke: "#2563eb", "stroke-width": 3 }, rec);
  texto(rec, 385, 160, "cola", "lbl-s", "middle");
  texto(rec, 470, 100, "=", "", "middle", { style: "font:800 50px Inter;fill:#fcb333" });
  el("ellipse", { cx: 570, cy: 100, rx: 70, ry: 36, fill: "#d7dbe2", stroke: "#0d1424", "stroke-width": 2 }, rec);
  texto(rec, 570, 160, "capa dura", "lbl-s", "middle");
  // superficie antes / después
  const sup = g(s, { transform: "translate(0,220)" });
  const r = azar(4);
  let dd = "M0,80";
  for (let x = 0; x <= 380; x += 12) dd += ` L${x},${70 + r() * 18}`;
  camino(sup, dd + " L380,160 L0,160 Z", "#0d1424", 2, FOAM);
  texto(sup, 190, 190, "foam crudo", "lbl-s", "middle");
  const sel = g(s, { transform: "translate(430,220)" });
  camino(sel, "M0,80 Q190,62 380,80 L380,160 L0,160 Z", "#0d1424", 2, "#e5e7eb");
  texto(sel, 190, 190, "sellado: duro y liso", "lbl-s", "middle");
  // unión con el dedo
  const union = g(s, { transform: "translate(140,440)" });
  el("rect", { x: 0, y: 0, width: 140, height: 110, fill: "#f4f6fa", stroke: "#0d1424", "stroke-width": 2 }, union);
  el("rect", { x: 140, y: 0, width: 140, height: 110, fill: "#f4f6fa", stroke: "#0d1424", "stroke-width": 2 }, union);
  const grieta = linea(union, 140, 0, 140, 110, "#9aa4b8", 6);
  const dedo = nuevo("div", "", emo("👆", 60), esc, "position:absolute;left:1180px;top:690px");
  const lij = nuevo("div", "", `<div class="pastilla">${DIB.lija().replace("<svg", "<svg width='40' height='40'")}Lija suave</div><div class="pastilla">${DIB.imprimante().replace("<svg", "<svg width='40' height='40'")}Imprimante blanco</div>`, esc, "position:absolute;left:1440px;top:730px;display:grid;gap:12px");
  const molde = nuevo("div", "tip", `${emo("🧱", 34)}<span>Etapa B: el molde se saca <b>ahora</b></span>`, esc, "left:1240px;top:220px");
  aparecer(rec, m(1)); aparecer(sup, m(1) + 0.4); aparecer(sel, m(1) + 1.6);
  aparecer(union, m(2)); pop(dedo, m(2) + 0.3);
  tl.fromTo(dedo, { y: -30 }, { y: 60, duration: 1.4, ease: "sine.inOut" }, m(2) + 0.8);
  tl.to(grieta, { opacity: 0, duration: 1.2 }, m(2) + 1.0);
  subir(lij.children, m(3) + 0.2, { stagger: 0.4 });
  pop(molde, m(4) + 0.2);
  salida();
};

// ============================================================== PASO 9 · PINTURA
function paredLadrillo(padre, etapa, w = 440, h = 240) {
  const s = svg(0, 0, w, h, padre);
  s.style.position = "relative"; s.style.left = "0"; s.style.top = "0";
  const r = azar(9);
  el("rect", { x: 0, y: 0, width: w, height: h, rx: 8, fill: etapa >= 2 ? "#3b1810" : "#8e3b2c" }, s);
  for (let f = 0; f < 8; f++) {
    for (let c = -1; c < 8; c++) {
      const x = c * 60 + (f % 2) * 30 + 3, y = f * 30 + 3;
      const tono = ["#8e3b2c", "#94412f", "#86372a"][Math.floor(r() * 3)];
      el("rect", { x, y, width: 54, height: 24, rx: 2, fill: etapa >= 1 ? tono : "#8e3b2c" }, s);
      if (etapa >= 2) el("rect", { x, y: y + 18, width: 54, height: 6, fill: "#5e2a1f", opacity: 0.6 }, s);
      if (etapa >= 3) {
        linea(s, x + 2, y + 2, x + 52, y + 2, "#d98a6c", 2.5, { opacity: 0.85 });
        if (r() > 0.5) linea(s, x + 8 + r() * 20, y + 6, x + 30 + r() * 20, y + 6 + r() * 4, "#c9765a", 2, { opacity: 0.6 });
      }
    }
  }
  return s;
}
ESCENAS.paso9 = () => {
  cabecera("Paso 9", "La <span class='acento'>pintura</span>", "3 técnicas, siempre en este orden");
  const datos = [["1", "Capa base", "Color principal, <b>2 manos finas</b>"],
    ["2", "Aguada", "<b>1 parte</b> de pintura oscura + <b>5 de agua</b> + 1 gota de lavavajilla · se mete en las ranuras"],
    ["3", "Pincel seco", "Pincel casi sin pintura, color claro, <b>pasadas rápidas</b>: solo pinta los relieves"]];
  const ps = datos.map(([n, t, d], i) => {
    const p = tarjetaPanel(110 + i * 575, 300, 545, 560, `<span style="width:46px;height:46px;border-radius:50%;background:var(--oro);color:#1d1405;display:grid;place-items:center;font-size:24px">${n}</span>${t}`, "");
    const cont = nuevo("div", "", "", p, "margin-top:16px;border-radius:10px;overflow:hidden;width:490px;height:240px");
    paredLadrillo(cont, i + 1, 490, 240);
    nuevo("div", "pd", d, p, "font-size:23px;margin-top:16px");
    return p;
  });
  ps.forEach((p, i) => { subir(p, m(i + 1)); resaltar(p, m(i + 1) + 0.2); if (i) normal(ps[i - 1], m(i + 1)); });
  const fin = nuevo("div", "tip", `${emo("🏭", 34)}<span>Ladrillos, tejas y rocas: igual que la pieza de fábrica</span>`, esc, "left:1000px;top:150px");
  pop(fin, m(4) + 0.2);
  tl.to(ps.map((p) => p), { y: 20, duration: 0.5 }, m(4));
  normal(ps[2], m(4));
  salida();
};

ESCENAS.colores = () => {
  cabecera("Paso 9", "Los <span class='acento'>colores</span>");
  const v = villa(esc, 1060, 250, 780, { luces: 0.3, motor: 0 });
  const filas = [
    ["Tejas", ["#8a4b2a", "#8e3b2c", "#c8734f"], "Siena tostada + rojo óxido · pincel seco terracota", ["tudor", "iglesia", "arco"]],
    ["Iglesia", ["#8e3b2c", "#4a2418", "#f5f1e6"], "Ladrillo rojo óxido · aguada marrón · marcos blancos", ["iglesia"]],
    ["Casa tudor", ["#ead9b4", "#3d261b", "#b0302a"], "Paredes crema · vigas marrón oscuro · vitrina roja", ["tudor"]],
    ["Panadería", ["#f1d48a", "#e0412f", "#fbfbf7"], "Amarillo crema · toldos rojo y blanco · letrero", ["panaderia"]],
    ["Rocas y puertas", ["#4b525e", "#9aa1ad", "#1f5a3d"], "Gris oscuro + pincel seco gris claro · verde oscuro", ["base", "meseta"]],
    ["Pinos y árbol", ["#1f5c3c", "#3e8e41", "#a7f3d0", "#dc2626"], "Verde oscuro + verde hoja · escarcha verde · bolitas", ["pinosAtras", "pinoMedio", "pinosAdelante", "arbol"]],
  ];
  const caja = nuevo("div", "", "", esc, "position:absolute;left:110px;top:270px;width:900px;display:grid;gap:12px");
  const todas = ["tudor", "iglesia", "arco", "panaderia", "base", "meseta", "terreno", "pinosAtras", "pinoMedio", "pinosAdelante", "arbol", "rio", "pista", "muneco", "figuras"];
  const rs = filas.map(([n, cols, d]) => nuevo("div", "tarjeta", `<div style="display:flex;gap:8px">${cols.map((c) => `<span style="width:44px;height:44px;border-radius:50%;background:${c};border:2px solid rgba(255,255,255,.3)"></span>`).join("")}</div>
    <div><div style="font-size:26px;font-weight:800">${n}</div><div style="font-size:21px;color:var(--suave);margin-top:2px">${d}</div></div>`, caja, "display:flex;gap:22px;align-items:center;padding:13px 20px"));
  rs.forEach((r_, i) => {
    const t = m(i + 1);
    subir(r_, t, { x: -30, y: 0 }); resaltar(r_, t + 0.2); if (i) normal(rs[i - 1], t);
    todas.forEach((p) => v[p] && tl.to(v[p], { opacity: filas[i][3].includes(p) ? 1 : 0.25, duration: 0.4 }, t));
  });
  todas.forEach((p) => v[p] && tl.to(v[p], { opacity: 1, duration: 0.4 }, m(7)));
  normal(rs[5], m(7));
  const tip = nuevo("div", "tip", `${emo("🩹", 32)}<span>Rayas de los toldos: cinta de pintor en tiras de <b>4 mm</b></span>`, esc, "left:1060px;top:860px");
  pop(tip, m(7) + 0.2);
  salida();
};

// ============================================================== PASO 10 · MECANISMO
ESCENAS.paso10 = () => {
  cabecera("Paso 10", "La pista que <span class='acento'>gira</span>");
  const lista = pasos(["Capas: MDF · taco · motor · rueda · disco",
    "Disco de PVC 3 mm de <b>Ø 9.5 cm</b> (hueco de 10)",
    "El eje del motor, en el <b>centro exacto</b>",
    "Rueda <b>sin llanta</b> + disco pegado con epóxico",
    "Disco <b>8 mm</b> bajo el borde: ajusta antes de apretar",
    "La rueda entra <b>a presión</b>: se saca para revisar",
    "~<b>8 vueltas/min</b> · más lento: resistencia de <b>22–47 Ω</b>"], 110, 280, 740, [m(1), m(2), m(3), m(4), m(5), m(6), m(7)]);
  lista[0].parentNode.classList.add("compacto");
  const s = svg(890, 250, 940, 660);
  const k = 7; // px por mm
  const X0 = 10, Y0 = 70;   // origen
  const fTop = Y0 + 120, fBot = fTop + 50 * k, mdfB = fBot + 5 * k;
  const cx = X0 + 460;
  const capas = {};
  capas.mdf = el("rect", { x: X0, y: fBot, width: 920, height: 5 * k, fill: MDF, stroke: "#0d1424", "stroke-width": 2 }, s);
  capas.foam = g(s);
  el("rect", { x: X0, y: fTop, width: cx - 50 * k - X0, height: 50 * k, fill: FOAM, stroke: "#0d1424", "stroke-width": 2 }, capas.foam);
  el("rect", { x: cx + 50 * k, y: fTop, width: X0 + 920 - (cx + 50 * k), height: 50 * k, fill: FOAM, stroke: "#0d1424", "stroke-width": 2 }, capas.foam);
  el("rect", { x: cx - 50 * k, y: fTop, width: 100 * k, height: 50 * k, fill: "#0b1222" }, capas.foam);
  camino(capas.foam, `M${X0},${fTop} L${cx - 50 * k},${fTop} M${cx + 50 * k},${fTop} L${X0 + 920},${fTop}`, "#ffffff", 8);
  [cx - 50 * k - 22, cx + 50 * k].forEach((xx) => el("rect", { x: xx, y: fTop - 10 * k, width: 22, height: 10 * k, rx: 6, fill: "#7d8595", stroke: "#0d1424", "stroke-width": 2 }, capas.foam));
  // taco + soporte + motor
  const motTop = fTop + 8 * k + 3 * k + 12 * k + 1 * k;  // disco 8 mm abajo + disco 3 + rueda 12 + 1 de luz
  capas.taco = el("rect", { x: cx - 6 * k - 20 * k, y: fBot - 26 * k, width: 20 * k, height: 26 * k, fill: "#c99a66", stroke: "#0d1424", "stroke-width": 2 }, s);
  capas.motor = g(s);
  el("rect", { x: cx - 6 * k, y: motTop, width: 12 * k, height: 9 * k, fill: "#d6b36a", stroke: "#0d1424", "stroke-width": 2 }, capas.motor);
  el("rect", { x: cx - 6 * k, y: motTop + 9 * k, width: 12 * k, height: 15 * k, rx: 6, fill: "#cbd5e1", stroke: "#0d1424", "stroke-width": 2 }, capas.motor);
  el("rect", { x: cx - 1.5 * k, y: motTop - 10 * k, width: 3 * k, height: 10 * k, fill: "#e5e7eb", stroke: "#7d8799", "stroke-width": 1.5 }, capas.motor);
  camino(capas.motor, `M${cx - 6 * k - 3},${motTop + 12 * k} L${cx + 6 * k + 6},${motTop + 12 * k} L${cx + 6 * k + 6},${motTop + 18 * k} L${cx - 6 * k - 3},${motTop + 18 * k}`, "#cfd6e2", 5);
  el("circle", { cx: cx - 6 * k - 10, cy: motTop + 15 * k, r: 5, fill: "#30343d" }, capas.motor);
  camino(capas.motor, `M${cx - 3 * k},${motTop + 24 * k} q0,${1.5 * k} ${-6 * k},${1.5 * k} M${cx + 3 * k},${motTop + 24 * k} q0,${1.5 * k} ${24 * k},${1.5 * k} L${cx + 46 * k},${motTop + 25.5 * k}`, "#ef4444", 3);
  // placa parada contra la pared
  capas.placa = el("rect", { x: cx + 46 * k, y: fBot - 25 * k, width: 2.5 * k, height: 25 * k, fill: "#3f7d4a", stroke: "#0d1424", "stroke-width": 2 }, s);
  // rueda y disco (giran)
  capas.giro = g(s);
  const rueda = el("rect", { x: cx - 17 * k, y: motTop - 1 * k - 12 * k, width: 34 * k, height: 12 * k, rx: 4, fill: "#facc15", stroke: "#0d1424", "stroke-width": 2 }, capas.giro);
  const disco = el("rect", { x: cx - 47.5 * k, y: fTop + 8 * k, width: 95 * k, height: 3 * k, fill: "#bfe6ff", stroke: "#0d1424", "stroke-width": 2 }, capas.giro);
  const flechaGiro = camino(s, `M${cx - 200},${fTop - 20} A200,26 0 1 0 ${cx + 200},${fTop - 20}`, "#fcb333", 4);
  const puntaGiro = el("path", { d: `M${cx + 200},${fTop - 20} l-6,-20 l20,8 z`, fill: "#fcb333" }, s);
  // etiquetas
  const E = [];
  E.push(etiqueta(s, X0 + 30, fBot + 17, X0 + 50, fBot + 84, "MDF 5 mm"));
  E.push(etiqueta(s, X0 + 80, fTop + 200, X0 + 30, fTop - 64, "Foam 5 cm"));
  E.push(etiqueta(s, cx - 16 * k, fBot - 6 * k, cx - 40 * k, fBot - 2 * k, "Taco de madera", "pegado al MDF"));
  E.push(etiqueta(s, cx - 6 * k, motTop + 16 * k, cx - 40 * k, motTop + 6 * k, "Motor N20", "en su soporte"));
  E.push(etiqueta(s, cx + 1.5 * k, motTop - 6 * k, cx + 40 * k, motTop + 4 * k, "Eje 3 mm"));
  E.push(etiqueta(s, cx + 14 * k, motTop - 7 * k, cx + 41 * k, fTop + 6, "Rueda sin llanta", "entra a presión"));
  E.push(etiqueta(s, cx + 20 * k, fTop + 9.5 * k, cx + 4 * k, fTop - 74, "Disco PVC 3 mm", "Ø 9.5 cm"));
  E.push(etiqueta(s, cx + 47 * k, fBot - 12 * k, X0 + 880, fBot + 84, "Placa"));
  const c8 = cota(s, cx - 49 * k, fTop, cx - 49 * k, fTop + 8 * k, "8 mm", 0);
  const cHueco = cota(s, cx - 50 * k, mdfB + 26, cx + 50 * k, mdfB + 26, "hueco Ø 10 cm", 0);
  const cLuz = cota(s, cx + 47.5 * k, fTop + 20 * k, cx + 50 * k, fTop + 20 * k, "2.5", -24);
  const centro = camino(s, `M${cx},${fTop - 40} L${cx},${fBot}`, "#43c47a", 2, "none", { "stroke-dasharray": "10 8" });
  // secuencia
  aparecer([capas.mdf, capas.foam], m(0) + 0.2);
  pop([E[0], E[1]], m(0) + 0.8, { stagger: 0.3 });
  aparecer(capas.taco, m(1) + 0.3); pop(E[2], m(1) + 0.6);
  aparecer(capas.motor, m(1) + 2.0); pop([E[3], E[4]], m(1) + 2.4, { stagger: 0.4 });
  tl.from(rueda, { y: -60, opacity: 0, duration: 0.6 }, m(1) + 4.0); pop(E[5], m(1) + 4.4);
  tl.from(disco, { y: -80, opacity: 0, duration: 0.6 }, m(1) + 5.6); pop(E[6], m(1) + 6.0);
  pop([cHueco, cLuz], m(2) + 0.6, { stagger: 0.5 });
  aparecer(capas.placa, m(2)); pop(E[7], m(2) + 0.2);
  tl.from(centro, { opacity: 0, duration: 0.6 }, m(3) + 0.2);
  tl.from(rueda, { fill: "#fcb333", duration: 0.5, repeat: 3, yoyo: true }, m(4) + 0.3);
  pop(c8, m(5) + 0.4);
  tl.to(capas.motor, { y: -10, duration: 0.6, repeat: 3, yoyo: true, ease: "sine.inOut" }, m(5) + 2.0);
  tl.to(capas.giro, { y: -60, duration: 0.7, yoyo: true, repeat: 1, ease: "power2.inOut" }, m(6) + 0.5);
  tl.from(flechaGiro, { drawSVG: "0%", duration: 1.2 }, m(7) + 0.2);
  tl.from(puntaGiro, { opacity: 0, duration: 0.3 }, m(7) + 1.3);
  const res = nuevo("div", "pastilla", `${DIB.resistencia(["#dc2626", "#dc2626", "#111827", "#d4a017"]).replace("<svg", "<svg width='52' height='52'")}22–47 Ω en serie = más lento`, esc, "position:absolute;left:1180px;top:250px");
  pop(res, m(7) + 1.0);
  salida();
};

ESCENAS.pista = () => {
  cabecera("Paso 10", "El <span class='acento'>hielo</span> de la pista");
  pasos(["Celeste muy claro + curvas blancas", "<b>3 manos</b> de barniz brillante", "Patinadores a <b>3 cm</b> del centro", "Murito de masilla de <b>1 cm</b>, como piedra"],
    110, 300, 740, [m(0), m(1), m(2), m(3)]);
  const s = svg(960, 270, 860, 640);
  const cx = 380, cy = 320, R = 237;   // 9.5 cm a 50 px/cm
  const muro = el("circle", { cx, cy, r: R + 38, fill: "none", stroke: "#7d8595", "stroke-width": 44 }, s);
  const nieveM = el("circle", { cx, cy, r: R + 44, fill: "none", stroke: "#ffffff", "stroke-width": 16, "stroke-dasharray": "40 14" }, s);
  const giro = g(s);
  const disco = el("circle", { cx, cy, r: R, fill: gradRadial(s, [[0, "#f0faff"], [0.8, "#cdeeff"], [1, "#a9dcf7"]]), stroke: "#0d1424", "stroke-width": 2 }, giro);
  const curvas = g(giro);
  [[0, 160], [1.6, 120], [3.2, 180], [4.6, 90]].forEach(([a, r]) => camino(curvas, `M${cx + Math.cos(a) * r},${cy + Math.sin(a) * r} A${r},${r} 0 0 1 ${cx + Math.cos(a + 1.1) * r},${cy + Math.sin(a + 1.1) * r}`, "#ffffff", 4, "none", { opacity: 0.9 }));
  const brillo = el("ellipse", { cx: cx - 90, cy: cy - 110, rx: 90, ry: 30, fill: "#fff", opacity: 0.0, transform: `rotate(-25 ${cx - 90} ${cy - 110})` }, giro);
  const pats = g(giro);
  [[0, "#c53b32"], [Math.PI, "#2563eb"]].forEach(([a, c]) => {
    const px = cx + Math.cos(a) * 150, py = cy + Math.sin(a) * 150;
    const fg = g(pats, { transform: `translate(${px},${py}) rotate(${a * 180 / Math.PI + 90})` });
    el("ellipse", { cx: 0, cy: 0, rx: 22, ry: 14, fill: c, stroke: "#0d1424", "stroke-width": 2 }, fg);
    el("circle", { cx: 0, cy: 0, r: 9, fill: "#f2c9a8", stroke: "#0d1424", "stroke-width": 1.5 }, fg);
    el("path", { d: "M-6,-20 L0,-34 L6,-20 Z", fill: "#fcb333" }, fg);
  });
  const c3 = cota(s, cx, cy, cx + 150, cy, "3 cm", -24);
  const manos = nuevo("div", "", ["1ª", "2ª", "3ª"].map((t) => `<div class="pastilla">${emo("✨", 26)}${t} mano</div>`).join(""), esc, "position:absolute;left:1650px;top:300px;display:grid;gap:12px");
  aparecer(giro, m(0) + 0.2);
  tl.from(curvas.children, { drawSVG: "0%", duration: 0.8, stagger: 0.3 }, m(0) + 0.8);
  pop(manos.children, m(1) + 0.4, { stagger: 0.6 });
  tl.to(brillo, { opacity: 0.5, duration: 0.8 }, m(1) + 0.5);
  tl.from(pats.children, { scale: 0, transformOrigin: "50% 50%", stagger: 0.3, duration: 0.5, ease: "back.out(2)" }, m(2) + 0.2);
  pop(c3, m(2) + 0.6);
  tl.to(c3, { opacity: 0, duration: 0.3 }, m(3));
  aparecer([muro, nieveM], m(3) + 0.2);
  CUADRO.push((t) => { const a = Math.max(0, t - m(2) - 1.2) * 48; giro.setAttribute("transform", `rotate(${a} ${cx} ${cy})`); });
  salida();
};

// ============================================================== PASO 11 · ELECTRÓNICA
ESCENAS.circuito = () => {
  cabecera("Paso 11", "El <span class='acento'>circuito</span>", "Todo en paralelo, a 5 V");
  const s = svg(70, 290, 1780, 600);
  const yP = 140, yN = 470;
  const usb = g(s);
  el("rect", { x: 0, y: 270, width: 70, height: 60, rx: 8, fill: "#cfd6e2", stroke: "#0d1424", "stroke-width": 2 }, usb);
  el("rect", { x: 70, y: 262, width: 40, height: 76, rx: 8, fill: "#111827", stroke: "#0d1424", "stroke-width": 2 }, usb);
  texto(usb, 55, 370, "USB 5 V", "lbl-oro", "middle");
  const rojo = camino(s, `M110,285 L160,285 L160,${yP} L270,${yP}`, "#ef4444", 6);
  const negro = camino(s, `M110,315 L160,315 L160,${yN} L420,${yN}`, "#9aa4b8", 6);
  const sw = g(s);
  el("circle", { cx: 280, cy: yP, r: 9, fill: "#e8eeff" }, sw);
  el("circle", { cx: 360, cy: yP, r: 9, fill: "#e8eeff" }, sw);
  const palanca = linea(sw, 280, yP, 354, yP - 36, "#e8eeff", 6);
  texto(sw, 320, yP - 60, "Interruptor", "lbl", "middle");
  const rojo2 = camino(s, `M360,${yP} L420,${yP}`, "#ef4444", 6);
  const rails = g(s);
  linea(rails, 420, yP, 1760, yP, "#ef4444", 8);
  linea(rails, 420, yN, 1760, yN, "#9aa4b8", 8);
  texto(rails, 430, yP - 20, "+ 5 V", "lbl", "start", { style: "font:800 26px Inter;fill:#ff8a87" });
  texto(rails, 430, yN + 44, "− (negativo)", "lbl", "start", { style: "font:800 26px Inter;fill:#cfd6e2" });
  const ramas = [["Tudor", 4, "#ffd27a"], ["Iglesia", 4, "#ffd27a"], ["Arco", 3, "#ffd27a"], ["Panadería", 4, "#ffd27a"], ["Pista", 2, "#ffd27a"], ["Árbol", 5, "rgb"], ["Río", 1, "#60a5fa"], ["Motor", 0, ""]];
  const gramas = ramas.map(([n, cnt, col], i) => {
    const x = 560 + i * 165;
    const gr = g(s);
    linea(gr, x, yP, x, yN, "#cfe0ff", 3);
    if (cnt) {
      resistenciaSimbolo(gr, x, yP + 90);
      const c = col === "rgb" ? "#c084fc" : col;
      ledSimbolo(gr, x, yP + 220, c);
      el("rect", { x: x - 52, y: yN + 66, width: 104, height: 34, rx: 17, fill: "#0b1528", stroke: "#fcb333", "stroke-width": 1.5 }, gr);
      texto(gr, x, yN + 90, `${n} ×${cnt}`, "lbl-s", "middle", { style: "font-weight:700;fill:#fff" });
    } else {
      el("circle", { cx: x, cy: (yP + yN) / 2, r: 40, fill: "#cbd5e1", stroke: "#0d1424", "stroke-width": 2 }, gr);
      texto(gr, x, (yP + yN) / 2 + 12, "M", "", "middle", { style: "font:800 34px Inter;fill:#0d1424" });
      el("rect", { x: x - 52, y: yN + 66, width: 104, height: 34, rx: 17, fill: "#0b1528", stroke: "#fcb333", "stroke-width": 1.5 }, gr);
      texto(gr, x, yN + 90, "Motor", "lbl-s", "middle", { style: "font-weight:700;fill:#fff" });
    }
    return gr;
  });
  const placaR = el("rect", { x: 400, y: yP - 70, width: 1380, height: yN - yP + 120, rx: 22, fill: "none", stroke: "#43c47a", "stroke-width": 2, "stroke-dasharray": "12 10" }, s);
  const placaT = texto(s, 1770, yP - 84, "Placa de distribución", "lbl", "end", { style: "font:700 22px Inter;fill:#7ee2a8" });
  // corriente
  const flujo = g(s);
  corriente(flujo, `M110,285 L160,285 L160,${yP} L1760,${yP}`, 26, "#ffb4b4", 120, m(2) + 1.0, 4);
  corriente(flujo, `M1760,${yN} L160,${yN} L160,315 L110,315`, 26, "#e5e7eb", 120, m(2) + 1.0, 4);
  // falla de un LED
  const falla = g(s);
  const xF = 560 + 1 * 165;
  el("circle", { cx: xF, cy: yP + 220, r: 34, fill: "rgba(239,68,68,.25)", stroke: "#ef4444", "stroke-width": 3 }, falla);
  camino(falla, `M${xF - 22},${yP + 198} L${xF + 22},${yP + 242} M${xF + 22},${yP + 198} L${xF - 22},${yP + 242}`, "#ef4444", 6);
  const ok = nuevo("div", "tip", `${emo("✅", 32)}<span>Si un LED falla, <b>los demás siguen prendidos</b></span>`, esc, "left:1190px;top:250px");
  // brillo de los LEDs cuando hay corriente
  const halos = gramas.slice(0, 7).map((gr, i) => {
    const x = 560 + i * 165;
    const c = i === 5 ? "#c084fc" : i === 6 ? "#60a5fa" : "#ffd27a";
    return el("circle", { cx: x, cy: yP + 220, r: 46, fill: gradRadial(s, [[0, c, 0.75], [1, c, 0]]), opacity: 0 }, s);
  });
  aparecer(usb, m(1)); tl.from([rojo, negro], { drawSVG: "0%", duration: 1.0, stagger: 0.3 }, m(1) + 0.4);
  aparecer(sw, m(2)); tl.from(rojo2, { drawSVG: "0%", duration: 0.4 }, m(2) + 0.3);
  tl.to(palanca, { attr: { x2: 360, y2: yP }, duration: 0.3 }, m(2) + 0.8);
  aparecer([rails, placaR, placaT], m(2) + 0.6);
  tl.from(gramas, { opacity: 0, y: 30, stagger: 0.18, duration: 0.5 }, m(3) + 0.2);
  tl.to(halos, { opacity: 1, duration: 0.5, stagger: 0.1 }, m(3) + 1.6);
  aparecer(falla, m(4) + 0.3); tl.to(halos[1], { opacity: 0, duration: 0.3 }, m(4) + 0.3);
  pop(ok, m(4) + 0.8);
  tl.to(falla, { opacity: 0, duration: 0.4 }, m(5)); tl.to(halos[1], { opacity: 1, duration: 0.4 }, m(5));
  const fab = nuevo("div", "pastilla", `${emo("🏭", 28)}La de fábrica: lo mismo, en una placa impresa`, esc, "position:absolute;left:1190px;top:250px");
  tl.to(ok, { opacity: 0, duration: 0.3 }, m(5));
  pop(fab, m(5) + 0.3);
  salida();
};

ESCENAS.leds = () => {
  cabecera("Paso 11", "LED + <span class='acento'>resistencia</span>");
  const f = tarjetaPanel(110, 290, 860, 150, `${emo("🧮", 34)}R = (V fuente − V LED) ÷ corriente`, "");
  const ej = tarjetaPanel(110, 460, 860, 130, `${emo("⚪", 30)}Blanco o azul: (5 − 3) ÷ 0.009 ≈ <span style="color:var(--oro)">220 Ω</span>`, "");
  const rgb = tarjetaPanel(110, 610, 860, 130, `${emo("🌈", 30)}RGB lento: <span style="color:var(--oro)">100 Ω</span>, una por cada LED`, "");
  const pil = tarjetaPanel(110, 760, 860, 120, `${emo("🔋", 30)}Con 3 pilas AA: <span style="color:var(--oro)">150 Ω</span> y <span style="color:var(--oro)">68 Ω</span>`, "");
  [f, ej, rgb, pil].forEach((p) => (p.style.height = "auto"));
  nuevo("div", "pd", "Ejemplo: 5 V del USB · el LED blanco usa ~3 V · 9 mA", f);
  const s = svg(1010, 270, 820, 640);
  // LED grande
  const led = g(s, { transform: "translate(170,250) scale(2.6)" });
  camino(led, "M-16,14 L-16,-10 Q-16,-30 0,-30 Q16,-30 16,-10 L16,14 Z", "#0d1424", 1, "rgba(255,244,194,.9)");
  el("rect", { x: -20, y: 14, width: 40, height: 7, rx: 2, fill: "#fff4c2", stroke: "#0d1424", "stroke-width": 1 }, led);
  el("rect", { x: 14, y: 12, width: 8, height: 11, fill: "#0b1528" }, led);
  linea(led, -7, 21, -7, 95, "#9aa4b8", 2.4);
  linea(led, 7, 21, 7, 72, "#9aa4b8", 2.4);
  const eMas = etiqueta(s, 152, 490, 40, 560, "Larga = +", "ánodo");
  const eMenos = etiqueta(s, 188, 430, 300, 520, "Corta = −", "cátodo");
  const ePlano = etiqueta(s, 222, 302, 330, 250, "Lado plano = −");
  // resistencias
  const r220 = g(s, { transform: "translate(420,90)" });
  r220.innerHTML = DIB.resistencia(["#dc2626", "#dc2626", "#7c2d12", "#d4a017"]).replace("<svg", "<svg width='300' height='300' x='0' y='-110'");
  texto(r220, 150, 120, "220 Ω · rojo rojo marrón", "lbl", "middle");
  const r100 = g(s, { transform: "translate(420,290)" });
  r100.innerHTML = DIB.resistencia(["#7c2d12", "#111827", "#7c2d12", "#d4a017"]).replace("<svg", "<svg width='300' height='300' x='0' y='-110'");
  texto(r100, 150, 120, "100 Ω · marrón negro marrón", "lbl", "middle");
  const mal = nuevo("div", "aviso", `${emo("⚠️", 30)}Dos RGB con una sola resistencia = parpadean mal`, esc, "left:1010px;top:820px;font-size:22px");
  subir(f, m(0) + 0.3);
  subir(f.querySelector(".pd"), m(1) + 0.2);
  subir(ej, m(2) + 0.2);
  subir(rgb, m(3) + 0.2); pop(mal, m(3) + 2.0);
  pop(r220, m(4) + 0.2); pop(r100, m(4) + 2.2);
  tl.to(mal, { opacity: 0, duration: 0.3 }, m(5));
  aparecer(led, m(5)); pop([eMas, eMenos, ePlano], m(5) + 0.5, { stagger: 0.6 });
  subir(pil, m(6) + 0.2);
  salida();
};

ESCENAS.soldar = () => {
  cabecera("Paso 11", "A <span class='acento'>soldar</span>");
  pasos(["Cautín caliente · punta limpia en la esponja húmeda",
    "Pata + corta a <b>1 cm</b>, torcida con la resistencia",
    "<b>2 s</b> de calor · el estaño a la unión, no a la punta",
    "Rojo al final de la resistencia · negro a la pata −",
    "Termocontraíble en cada unión, con calor",
    "Cola de <b>30 cm</b> · ×23 · etiqueta de cinta"], 110, 290, 760, [m(0), m(1), m(2), m(3), m(4), m(5)])[0].parentNode.classList.add("compacto");
  const s = svg(900, 270, 940, 640);
  const yA = 420, yC = 500;
  const led = g(s);
  camino(led, "M40,400 L80,400 Q110,400 110,430 L110,490 Q110,520 80,520 L40,520 Z", "#0d1424", 2, "#fff4c2");
  el("rect", { x: 30, y: 390, width: 10, height: 140, rx: 2, fill: "#fff4c2", stroke: "#0d1424", "stroke-width": 2 }, led);
  const pataA = linea(led, 110, yA, 230, yA, "#9aa4b8", 4);
  const pataC = linea(led, 110, yC, 200, yC, "#9aa4b8", 4);
  texto(led, 150, yA - 16, "+", "", "middle", { style: "font:800 30px Inter;fill:#ff8a87" });
  texto(led, 150, yC + 40, "−", "", "middle", { style: "font:800 30px Inter;fill:#cfd6e2" });
  const cor = cota(s, 110, yA - 50, 180, yA - 50, "1 cm", 0);
  const res = g(s);
  linea(res, 180, yA, 290, yA, "#9aa4b8", 4);
  res.innerHTML += DIB.resistencia().replace("<svg", `<svg x="250" y="${yA - 60}" width="120" height="120"`);
  linea(res, 350, yA, 420, yA, "#9aa4b8", 4);
  const cables = g(s);
  camino(cables, `M410,${yA} L900,${yA}`, "#ef4444", 9);
  camino(cables, `M190,${yC} L900,${yC}`, "#5b6475", 9);
  camino(cables, `M190,${yC} L900,${yC}`, "#6b7280", 2.5, "none", { opacity: 0.8 });
  const soldaduras = [[200, yA], [415, yA], [195, yC]].map(([x, y]) => el("ellipse", { cx: x, cy: y, rx: 16, ry: 11, fill: "#e5e7eb", stroke: "#94a3b8", "stroke-width": 1.5 }, s));
  const termos = [[175, yA], [390, yA], [170, yC]].map(([x, y]) => el("rect", { x, y: y - 14, width: 52, height: 28, rx: 8, fill: "#111827", opacity: 0.88 }, s));
  const cautin = g(s);
  cautin.innerHTML = DIB.cautin().replace("<svg", `<svg x="120" y="200" width="200" height="200"`);
  const lupa = g(s);
  el("circle", { cx: 620, cy: 190, r: 110, fill: "#0b1528", stroke: "#fcb333", "stroke-width": 3 }, lupa);
  linea(lupa, 530, 220, 710, 220, "#9aa4b8", 6);
  camino(lupa, "M560,220 Q620,120 680,220 Z", "#94a3b8", 2, "#e5e7eb");
  camino(lupa, "M590,190 Q610,160 630,170", "#ffffff", 4, "none", { opacity: 0.9 });
  texto(lupa, 620, 270, "bien: brillante, como gota", "lbl-s", "middle");
  const etiq = g(s);
  el("path", { d: `M800,${yA - 6} L900,${yA - 6} L900,${yA - 64} L800,${yA - 64} Z`, fill: "#fde68a", stroke: "#a16207", "stroke-width": 2 }, etiq);
  texto(etiq, 850, yA - 28, "TUDOR 1", "", "middle", { style: "font:800 20px Inter;fill:#713f12" });
  const c30 = cota(s, 420, yC + 60, 900, yC + 60, "30 cm", 0);
  const x23 = nuevo("div", "pastilla", `${emo("✖️", 26)}23 LEDs así`, esc, "position:absolute;left:1600px;top:860px");
  aparecer(cautin, m(0) + 0.3);
  aparecer(led, m(1)); pop(cor, m(1) + 0.4); aparecer(res, m(1) + 1.4);
  tl.to(cautin, { x: 70, y: 150, duration: 0.8 }, m(2) + 0.2);
  tl.from(soldaduras[0], { scale: 0, transformOrigin: "200px 420px", duration: 0.4 }, m(2) + 1.2);
  pop(lupa, m(2) + 1.8);
  tl.to(lupa, { opacity: 0, duration: 0.4 }, m(3));
  tl.to(cautin, { opacity: 0, duration: 0.4 }, m(3));
  tl.from(cables.children, { drawSVG: "0%", duration: 0.9, stagger: 0.3 }, m(3) + 0.2);
  tl.from([soldaduras[1], soldaduras[2]], { scale: 0, transformOrigin: "50% 50%", duration: 0.4, stagger: 0.3 }, m(3) + 1.6);
  tl.from(termos, { x: 160, opacity: 0, duration: 0.6, stagger: 0.25 }, m(4) + 0.3);
  pop([etiq, c30], m(5) + 0.4, { stagger: 0.5 }); pop(x23, m(5) + 1.4);
  salida();
};

ESCENAS.probar = () => {
  cabecera("Paso 11", "Prueba cada <span class='acento'>LED</span>");
  const s = svg(110, 280, 1700, 600);
  const carg = g(s);
  carg.innerHTML = DIB.cargador().replace("<svg", `<svg x="0" y="140" width="190" height="190"`);
  camino(carg, "M150,250 Q260,250 300,200 L420,200", "#ef4444", 7);
  camino(carg, "M150,268 Q270,268 310,290 L420,290", "#111827", 7);
  const led = g(s);
  const brillo = el("circle", { cx: 640, cy: 170, r: 120, fill: gradRadial(s, [[0, "#fff4c2", 0.9], [1, "#ffd27a", 0]]), opacity: 0 }, s);
  ledDibujo(led, 640, 200, "#fff4c2", 2.0);
  camino(led, "M620,245 L620,290 L460,290 M660,245 L660,200 L560,200", "none", 0, "none");
  camino(led, "M540,200 L460,200", "#ef4444", 7); camino(led, "M540,290 L460,290", "#111827", 7);
  linea(led, 625, 245, 625, 290, "#9aa4b8", 5); linea(led, 655, 245, 655, 260, "#9aa4b8", 5);
  camino(led, "M625,290 L540,290 M655,260 Q600,230 540,200", "#9aa4b8", 4);
  const toque = nuevo("div", "pastilla", `${emo("🔴", 22)}rojo con rojo · ${emo("⚫", 22)} negro con negro`, esc, "position:absolute;left:330px;top:640px");
  const mul = g(s, { transform: "translate(900,40)" });
  mul.innerHTML = DIB.multimetro().replace("<svg", `<svg x="0" y="0" width="360" height="360"`);
  texto(mul, 180, 400, "Modo diodo: prende suave si está al derecho", "lbl", "middle");
  const mot = g(s, { transform: "translate(1360,120)" });
  mot.innerHTML = DIB.motor().replace("<svg", `<svg x="0" y="0" width="300" height="300"`);
  const giro = camino(mot, "M290,90 A40,40 0 1 1 290,190", "#fcb333", 5);
  texto(mot, 150, 320, "Gira suave, sin ruidos", "lbl", "middle");
  aparecer([carg, led], m(1) + 0.2);
  tl.to(brillo, { opacity: 1, duration: 0.4 }, m(1) + 2.6);
  pop(toque, m(1) + 1.0);
  aparecer(mul, m(2) + 0.3);
  aparecer(mot, m(3) + 0.2);
  tl.from(giro, { drawSVG: "0%", duration: 0.8, repeat: 2 }, m(3) + 0.6);
  salida();
};

ESCENAS.placa = () => {
  cabecera("Paso 11", "La placa de <span class='acento'>distribución</span>");
  pasos(["Corta la placa a <b>2.5 × 6 cm</b>", "2 alambres de punta a punta: <b>+</b> y <b>−</b>", "Negro → línea −, rojo → interruptor → línea +",
    "Continuidad entre + y −: <b>no debe sonar</b>", "Opcional: fusible reseteable de <b>500 mA</b>", "<b>Nudo</b> en el cable USB, por dentro"], 110, 290, 740, [m(0), m(1), m(2), m(3), m(4), m(5)])[0].parentNode.classList.add("compacto");
  const s = svg(900, 270, 940, 640);
  const k = 100;
  const grande = g(s);
  el("rect", { x: 160, y: 40, width: 7 * 60, height: 5 * 60, rx: 6, fill: "#3f7d4a", stroke: "#0d1424", "stroke-width": 2 }, grande);
  for (let i = 0; i < 18; i++) for (let j = 0; j < 13; j++) el("circle", { cx: 172 + i * 22.5, cy: 52 + j * 22.5, r: 3, fill: "#d6b36a" }, grande);
  const corte = camino(grande, "M160,190 L580,190", "#ef4444", 4, "none", { "stroke-dasharray": "12 8" });
  texto(grande, 370, 380, "5 × 7 cm → corta 2.5 × 6", "lbl-s", "middle");
  const placa = g(s, { transform: "translate(260,120)" });
  el("rect", { x: 0, y: 0, width: 6 * k, height: 2.5 * k, rx: 6, fill: "#3f7d4a", stroke: "#0d1424", "stroke-width": 2 }, placa);
  for (let i = 0; i < 24; i++) for (let j = 0; j < 10; j++) el("circle", { cx: 12 + i * 24.5, cy: 14 + j * 24.5, r: 3.5, fill: "#d6b36a" }, placa);
  const rP = linea(placa, 10, 60, 590, 60, "#e5e7eb", 7);
  const rN = linea(placa, 10, 190, 590, 190, "#e5e7eb", 7);
  texto(placa, 600, 68, "+", "", "start", { style: "font:800 34px Inter;fill:#ff8a87" });
  texto(placa, 600, 200, "−", "", "start", { style: "font:800 34px Inter;fill:#cfd6e2" });
  const usb = g(s);
  camino(usb, "M-60,455 L0,455", "#111827", 14);
  const crojo = camino(usb, "M0,440 L40,440 L40,173 L100,173 M170,173 L270,180", "#ef4444", 6);
  const sw = g(s);
  el("rect", { x: 100, y: 150, width: 70, height: 46, rx: 8, fill: "#111827", stroke: "#0d1424", "stroke-width": 2 }, sw);
  texto(sw, 135, 180, "I/O", "", "middle", { style: "font:800 16px Inter;fill:#fff" });
  const negroRail = camino(s, "M0,470 L200,470 L200,310 L270,310", "#111827", 6);
  const fus = g(s);
  fus.innerHTML = DIB.fusible().replace("<svg", `<svg x="0" y="260" width="90" height="90"`);
  const cont = g(s);
  cont.innerHTML = DIB.multimetro().replace("<svg", `<svg x="740" y="380" width="200" height="200"`);
  const noSuena = texto(cont, 840, 610, "¡no debe sonar!", "lbl-oro", "middle");
  const nudo = g(s, { transform: "translate(400,410) scale(1.2)" });
  el("rect", { x: 0, y: 0, width: 26, height: 140, fill: FOAM_LADO, stroke: "#0d1424", "stroke-width": 2 }, nudo);
  camino(nudo, "M-120,70 L0,70", "#111827", 10); camino(nudo, "M26,70 L60,70 Q90,70 90,50 Q90,30 70,40 Q50,50 70,70 L110,70", "#111827", 10);
  texto(nudo, 40, 170, "nudo antitirón", "lbl-s", "middle");
  aparecer(grande, m(0) + 0.3); tl.from(corte, { drawSVG: "0%", duration: 0.8 }, m(0) + 2.0);
  tl.to(grande, { opacity: 0, duration: 0.5 }, m(1) - 0.3);
  aparecer(placa, m(1) - 0.2);
  tl.from([rP, rN], { drawSVG: "0%", duration: 0.9, stagger: 0.3 }, m(1) + 0.4);
  aparecer(usb, m(2)); tl.from(negroRail, { drawSVG: "0%", duration: 0.8 }, m(2) + 0.3); aparecer(sw, m(2) + 1.6);
  aparecer(cont, m(3) + 0.2);
  pop(fus, m(4) + 0.2);
  tl.to(cont, { opacity: 0, duration: 0.3 }, m(5));
  aparecer(nudo, m(5) + 0.2);
  salida();
};

// ============================================================== PASO 12 · INSTALAR LUCES
ESCENAS.paso12 = () => {
  cabecera("Paso 12", "Instalar las <span class='acento'>luces</span>");
  pasos(["Ventanas por dentro, en <b>3 capas</b>", "Mica · celofán amarillo · albanene", "Interior blanco · LED de 5 mm a <b>1 cm</b> de la ventana",
    "Foquitos: agujero de <b>3 mm</b>, LED desde adentro", "Piso perforado hasta el canal · casa pegada con silicona",
    "Azul bajo el puente · RGB en el árbol", "Todo llega al hueco: rojo a +, negro a −", "Prueba · placa parada, lejos del motor"], 110, 280, 740,
  [m(0), m(1), m(2), m(3), m(4), m(5), m(6), m(7)])[0].parentNode.classList.add("compacto");
  // A: corte de la pared con ventana
  const sA = svg(900, 270, 940, 640);
  const A = g(sA);
  el("rect", { x: 120, y: 60, width: 36, height: 520, fill: "#f4f6fa", stroke: "#0d1424", "stroke-width": 2 }, A);
  el("rect", { x: 120, y: 250, width: 36, height: 140, fill: "#0b1528" }, A);
  const capas = [["#bfe6ff", "Mica", 0.5], ["#facc15", "Celofán amarillo", 0.75], ["#f8fafc", "Albanene", 0.85]].map(([c, n, op], i) => {
    const gr = g(A);
    el("rect", { x: 170 + i * 70, y: 236, width: 10, height: 168, fill: c, opacity: op, stroke: "#0d1424", "stroke-width": 1 }, gr);
    el("circle", { cx: 240 + i * 50, cy: 482 + i * 36, r: 7, fill: c }, gr);
    texto(gr, 256 + i * 50, 489 + i * 36, `${i + 1}. ${n}`, "lbl-s", "start", { style: "font-weight:700;fill:#fff" });
    return gr;
  });
  const interior = el("rect", { x: 156, y: 60, width: 560, height: 520, fill: "rgba(255,255,255,.06)" }, A);
  const ledA = g(A);
  ledDibujo(ledA, 420, 330, "#fff4c2", 1.2);
  const rayos = g(A);
  [[-40], [0], [40]].forEach(([d]) => flecha(rayos, 390, 320 + d * 0.3, 60, 320 + d * 1.6, "#ffd27a", 4));
  const c1 = cota(A, 222, 440, 400, 440, "1 cm", 0);
  const foquito = g(A);
  el("rect", { x: 120, y: 130, width: 36, height: 16, fill: "#0b1528" }, foquito);
  camino(foquito, "M100,128 L120,128 L120,148 L100,148 Q90,138 100,128 Z", "#0d1424", 1.5, "#ffd27a");
  camino(foquito, "M156,132 L230,132 M156,144 L230,144", "#9aa4b8", 3);
  const brilloF = el("circle", { cx: 100, cy: 138, r: 36, fill: gradRadial(sA, [[0, "#ffd27a", 0.9], [1, "#ffd27a", 0]]), opacity: 0 }, A);
  texto(A, 40, 110, "Foquito", "lbl-s", "middle", { style: "font-weight:700" });
  texto(A, 138, 620, "Pared", "lbl-s", "middle");
  // B: corte del terreno con cables
  const B = g(sA);
  B.style.opacity = 0;
  el("rect", { x: 0, y: 460, width: 940, height: 26, fill: MDF, stroke: "#0d1424", "stroke-width": 2 }, B);
  el("rect", { x: 0, y: 260, width: 600, height: 200, fill: FOAM, stroke: "#0d1424", "stroke-width": 2 }, B);
  el("rect", { x: 600, y: 260, width: 300, height: 200, fill: "#0b1222" }, B);
  el("rect", { x: 900, y: 260, width: 40, height: 200, fill: FOAM, stroke: "#0d1424", "stroke-width": 2 }, B);
  el("rect", { x: 60, y: 430, width: 540, height: 30, fill: "#7a2e4b" }, B);
  texto(B, 330, 452, "canal de 1 cm", "lbl-s", "middle", { style: "fill:#ffd6e7;font-weight:700" });
  camino(B, "M0,260 L600,260 M900,260 L940,260", "#ffffff", 8);
  const casaB = g(B);
  poli(casaB, [[120, 258], [120, 120], [210, 60], [300, 120], [300, 258]], "#ead9b4");
  el("rect", { x: 150, y: 150, width: 40, height: 50, fill: "#ffd27a" }, casaB);
  ledDibujo(casaB, 240, 210, "#fff4c2", 0.7);
  el("rect", { x: 232, y: 258, width: 16, height: 172, fill: "#0b1222" }, B);
  const cablesB = g(B);
  camino(cablesB, "M236,226 L236,445 L700,445 L740,420", "#ef4444", 4);
  camino(cablesB, "M244,226 L244,452 L700,452 L740,430", "#111827", 4);
  camino(cablesB, "M500,445 L500,445", "#ef4444", 4);
  const placaB = el("rect", { x: 860, y: 300, width: 18, height: 160, fill: "#3f7d4a", stroke: "#0d1424", "stroke-width": 2 }, B);
  camino(cablesB, "M740,420 L860,380 M740,430 L860,410", "#9aa4b8", 3);
  texto(B, 870, 290, "placa", "lbl-s", "middle", { style: "font-weight:700" });
  texto(B, 750, 240, "hueco de la pista", "lbl-s", "middle");
  const otros = g(B);
  [["árbol", 560, 300], ["río", 520, 360]].forEach(([n, x, y]) => { camino(otros, `M${x},${y} L${x},445`, "#c084fc", 3, "none", { "stroke-dasharray": "8 6" }); texto(otros, x, y - 10, n, "lbl-s", "middle"); });
  const brilloB = el("circle", { cx: 170, cy: 175, r: 70, fill: gradRadial(sA, [[0, "#ffd27a", 0.8], [1, "#ffd27a", 0]]), opacity: 0 }, B);
  // secuencia
  aparecer(A, m(0) + 0.2);
  capas.forEach((c, i) => tl.from(c, { x: 200, opacity: 0, duration: 0.6 }, m(1) + i * 1.6));
  tl.to(capas, { x: (i) => -i * 50, duration: 0.6 }, m(2));
  aparecer(ledA, m(2) + 0.4); tl.from(rayos.children, { opacity: 0, duration: 0.5, stagger: 0.2 }, m(2) + 1.0); pop(c1, m(2) + 1.8);
  aparecer(foquito, m(3) + 0.3); tl.to(brilloF, { opacity: 1, duration: 0.4 }, m(3) + 1.2);
  tl.to(A, { opacity: 0, duration: 0.5 }, m(4));
  tl.to(B, { opacity: 1, duration: 0.6 }, m(4) + 0.3);
  tl.from(cablesB.children, { drawSVG: "0%", duration: 1.2, stagger: 0.2 }, m(4) + 1.4);
  aparecer(otros, m(5) + 0.3);
  tl.from(placaB, { opacity: 0, duration: 0.5 }, m(6) + 0.2);
  tl.to(brilloB, { opacity: 1, duration: 0.5 }, m(7) + 0.4);
  const sw = nuevo("div", "pastilla", `${emo("💡", 28)}¡Prende!`, esc, "position:absolute;left:1640px;top:300px");
  pop(sw, m(7) + 0.4);
  salida();
};

// ============================================================== PASO 13 · NIEVE
ESCENAS.paso13 = () => {
  cabecera("Paso 13", "La <span class='acento'>nieve</span>");
  const rec = nuevo("div", "tarjeta panel", `<div class="pt">${emo("🥣", 34)}La receta</div>
    <div style="display:flex;gap:18px;margin-top:18px;align-items:center;font-size:24px;font-weight:700">
      <div style="text-align:center">${emo("🥄", 42)}${emo("🥄", 42)}<div>2 cdas<br><span style="color:var(--suave);font-weight:500">bicarbonato</span></div></div>
      <div style="color:var(--oro);font-size:40px">+</div>
      <div style="text-align:center">${emo("🥄", 42)}<div>1 cda<br><span style="color:var(--suave);font-weight:500">cola</span></div></div>
      <div style="color:var(--oro);font-size:40px">+</div>
      <div style="text-align:center">${emo("🥄", 30)}<div>1 cdta<br><span style="color:var(--suave);font-weight:500">pintura blanca</span></div></div>
    </div><div class="pd" style="margin-top:14px">Como <b>pasta dental espesa</b></div>`, esc, "left:110px;top:290px;width:760px");
  subir(rec, m(1) + 0.2);
  const s = svg(930, 270, 900, 640);
  // techo con nieve
  const techo = g(s);
  poli(techo, [[40, 260], [210, 110], [380, 260]], "#7a3a2b");
  el("rect", { x: 70, y: 260, width: 280, height: 110, fill: "#ead9b4", stroke: "#0d1424", "stroke-width": 2 }, techo);
  const nieveT = camino(techo, "M26,264 L210,94 L394,264 Q382,280 366,270 L210,128 L54,270 Q38,280 26,264 Z", "#c9d6ea", 2, "#f8fafc");
  const gotas = g(techo);
  [[60, 280, 22], [110, 276, 14], [300, 278, 26], [350, 280, 16]].forEach(([x, y, l]) => camino(gotas, `M${x - 7},${y - 4} Q${x},${y + l} ${x + 7},${y - 4} Z`, "none", 0, "#f8fafc"));
  const esp = nuevo("div", "", DIB.espatula().replace("<svg", "<svg width='90' height='90'"), esc, "position:absolute;left:1340px;top:330px");
  // borde de la base
  const borde = g(s, { transform: "translate(0,400)" });
  el("rect", { x: 20, y: 40, width: 820, height: 120, fill: "#59606e", stroke: "#0d1424", "stroke-width": 2 }, borde);
  const franja = el("rect", { x: 14, y: 26, width: 832, height: 30, rx: 10, fill: "#f8fafc" }, borde);
  const gotasB = [];
  for (let i = 0; i < 16; i++) {
    const x = 40 + i * 52, l = 20 + ((i * 37) % 30);
    gotasB.push(camino(borde, `M${x - 16},52 C${x - 16},${56 + l} ${x + 16},${56 + l} ${x + 16},52 Z`, "none", 0, "#f8fafc"));
  }
  const dedo = nuevo("div", "", emo("👇", 54), esc, "position:absolute;left:960px;top:650px");
  const cB = cota(borde, 846, 26, 846, 56, "1 cm", -40);
  const brillos = g(s);
  const r = azar(3);
  for (let i = 0; i < 40; i++) {
    const x = 40 + r() * 800, y = 120 + r() * 420;
    camino(brillos, `M${x},${y - 7} l2,5 5,2 -5,2 -2,5 -2,-5 -5,-2 5,-2 z`, "none", 0, ["#ffffff", "#bfe6ff", "#f0abfc", "#fde68a"][i % 4]);
  }
  const t24 = reloj(esc, 110, 640, "Secado: 24 horas", "⏳");
  const ic = nuevo("div", "tip", `${emo("🧊", 32)}<span>Carámbanos: gotas de silicona, jalando la pistola hacia abajo</span>`, esc, "left:110px;top:740px;width:760px");
  aparecer(techo.children[0], m(2)); aparecer(techo.children[1], m(2));
  tl.from(nieveT, { opacity: 0, y: -20, duration: 0.7 }, m(2) + 0.4); pop(esp, m(2) + 0.2);
  tl.from(gotas.children, { scaleY: 0, transformOrigin: "50% 0%", stagger: 0.2, duration: 0.5 }, m(3) + 0.4);
  aparecer(borde, m(4)); tl.from(franja, { scaleX: 0, transformOrigin: "0% 50%", duration: 1 }, m(4) + 0.5); pop(cB, m(4) + 1.4);
  tl.from(gotasB, { scaleY: 0, transformOrigin: "50% 0%", stagger: 0.25, duration: 0.4 }, m(4) + 2.2);
  pop(dedo, m(4) + 2.0); tl.to(dedo, { x: 760, duration: 4.5, ease: "none" }, m(4) + 2.2);
  tl.to(dedo, { opacity: 0, duration: 0.3 }, m(5));
  tl.from(brillos.children, { scale: 0, opacity: 0, transformOrigin: "50% 50%", stagger: 0.04, duration: 0.3 }, m(5) + 0.3);
  pop(t24, m(5) + 1.2);
  subir(ic, m(6) + 0.2);
  salida();
};

// ============================================================== PASO 14 · RÍO
ESCENAS.paso14 = () => {
  cabecera("Paso 14", "El agua del <span class='acento'>río</span>");
  pasos(["Azul oscuro en los bordes, azul claro al centro, líneas blancas", "Tiras de silicona transparente + <b>secadora</b>", "<b>2 manos</b> de barniz brillante · LED azul bajo el puente"],
    110, 300, 740, [m(1), m(2), m(3)]);
  const s = svg(930, 270, 900, 620);
  // vista desde arriba del río
  const rio = g(s);
  const grad = gradLineal(s, [[0, "#1d3f8f"], [0.5, "#4b8df0"], [1, "#1d3f8f"]], 0, 0, 1, 0);
  el("rect", { x: 0, y: 40, width: 900, height: 80, fill: "#cfd6e2" }, rio);
  const fondo = camino(rio, "M380,40 L520,40 Q560,300 620,580 L280,580 Q330,300 380,40 Z", "#0d1424", 2, grad);
  const espuma = g(rio);
  [[420, 120, 400, 300], [470, 160, 460, 420], [500, 90, 540, 360], [440, 320, 420, 540], [520, 400, 560, 560]].forEach(([a, b, c, d]) => camino(espuma, `M${a},${b} Q${(a + c) / 2 + 12},${(b + d) / 2} ${c},${d}`, "#ffffff", 4, "none", { opacity: 0.85 }));
  const sil = g(rio);
  [[400, 80, 360, 560], [450, 60, 440, 570], [500, 70, 540, 565]].forEach(([a, b, c, d]) => camino(sil, `M${a},${b} Q${(a + c) / 2 - 16},${(b + d) / 2} ${c},${d}`, "rgba(230,245,255,.55)", 14, "none"));
  const barniz = el("path", { d: "M380,40 L520,40 Q560,300 620,580 L280,580 Q330,300 380,40 Z", fill: gradLineal(s, [[0, "#ffffff", 0.35], [0.5, "#ffffff", 0], [1, "#ffffff", 0.2]], 0, 0, 1, 1), opacity: 0 }, rio);
  const puente = g(rio);
  el("rect", { x: 340, y: 20, width: 220, height: 50, rx: 8, fill: "#7d8595", stroke: "#0d1424", "stroke-width": 2 }, puente);
  texto(puente, 450, 52, "puente", "lbl", "middle");
  const azul = el("ellipse", { cx: 450, cy: 120, rx: 150, ry: 120, fill: gradRadial(s, [[0, "#60a5fa", 0.85], [1, "#60a5fa", 0]]), opacity: 0 }, rio);
  const sec = nuevo("div", "", DIB.secadora().replace("<svg", "<svg width='110' height='110'"), esc, "position:absolute;left:1660px;top:520px");
  aparecer([rio.children[0], fondo], m(0) + 0.3);
  tl.from(espuma.children, { drawSVG: "0%", duration: 0.7, stagger: 0.2 }, m(1) + 0.6);
  tl.from(sil.children, { drawSVG: "0%", duration: 0.8, stagger: 0.3 }, m(2) + 0.4); pop(sec, m(2) + 1.4);
  tl.to(barniz, { opacity: 1, duration: 0.6 }, m(3) + 0.3);
  aparecer(puente, m(0) + 0.6);
  tl.to(azul, { opacity: 1, duration: 0.8 }, m(3) + 1.6);
  salida();
};

// ============================================================== PASO 15 · MONTAJE FINAL
ESCENAS.paso15 = () => {
  cabecera("Paso 15", "El <span class='acento'>montaje</span> final");
  pasos(["Pinos con su palito + gota de silicona", "Árbol, muñeco de nieve y el niño", "Pista: la rueda a presión, gírala con la mano", "Abajo: <b>fieltro</b> + <b>4 patitas</b> de goma", "Retoca uniones con nieve y escarcha"],
    110, 300, 740, [m(1), m(2), m(3), m(4), m(5)]);
  const v = villa(esc, 900, 240, 920, { luces: m(5), motor: m(3) + 0.8 });
  [v.pinosAtras, v.pinoMedio, v.pinosAdelante].forEach((p, i) => tl.from(p, { y: -200, opacity: 0, duration: 0.7, ease: "bounce.out" }, m(1) + 0.3 + i * 0.4));
  [v.arbol, v.muneco, v.figuras].forEach((p, i) => tl.from(p, { y: -200, opacity: 0, duration: 0.7, ease: "bounce.out" }, m(2) + 0.3 + i * 0.6));
  tl.from([...v.pista.children].slice(3), { y: -120, opacity: 0, duration: 0.7, ease: "power2.out" }, m(3) + 0.2);
  const abajo = nuevo("div", "tarjeta panel", `<div class="pt">${emo("🔄", 30)}Por debajo</div><div style="display:flex;gap:16px;margin-top:10px;align-items:center"><div style="width:90px;height:90px">${DIB.fieltro()}</div><span style="font-size:22px">Fieltro + 4 patitas de goma</span></div>`, esc, "left:110px;top:806px;width:740px;padding:12px 20px");
  subir(abajo, m(4) + 0.2);
  const brillos = svg(900, 240, 920, 736);
  const r = azar(8);
  for (let i = 0; i < 26; i++) {
    const x = 80 + r() * 760, y = 300 + r() * 380;
    camino(brillos, `M${x},${y - 8} l2,6 6,2 -6,2 -2,6 -2,-6 -6,-2 6,-2 z`, "none", 0, i % 2 ? "#ffffff" : "#bfe6ff");
  }
  tl.from(brillos.children, { scale: 0, opacity: 0, transformOrigin: "50% 50%", stagger: 0.06, duration: 0.3 }, m(5) + 0.4);
  salida();
};

// ============================================================== PASO 16 · PRUEBAS
ESCENAS.problemas = () => {
  cabecera("Paso 16", "Pruebas y <span class='acento'>soluciones</span>");
  const h = reloj(esc, 1440, 150, "Funcionando 1 hora", "⏱️");
  pop(h, m(0) + 0.6);
  const filas = [["💡", "Un solo LED no prende", "Revisa su polaridad y su soldadura"],
    ["🔌", "No prende ninguno", "Mide si llegan 5 V a la placa: interruptor o cable"],
    ["🪟", "Se ve el puntito del LED", "Otra capa de albanene, o aleja el LED"],
    ["⛸️", "La pista se traba o hace ruido", "Está rozando: centra el disco o lija el borde"],
    ["🔥", "El cargador se calienta", "Desconéctalo: hay un corto. Revisa con el multímetro"]];
  const caja = nuevo("div", "", "", esc, "position:absolute;left:110px;top:290px;width:1700px;display:grid;gap:14px");
  const rs = filas.map(([e, p, sol]) => nuevo("div", "tarjeta", `<div style="display:flex;gap:16px;align-items:center;font-size:27px;font-weight:700">${emo(e, 40)}${p}</div><div style="font-size:30px;color:var(--oro)">→</div><div style="font-size:26px;font-weight:500">${sol}</div>`,
    caja, "display:grid;grid-template-columns:680px 60px 1fr;align-items:center;padding:18px 28px"));
  rs.forEach((r_, i) => { subir(r_, m(i + 1), { x: -30, y: 0 }); resaltar(r_, m(i + 1) + 0.2, i === 4 ? "var(--rojo)" : "var(--oro)"); if (i) normal(rs[i - 1], m(i + 1)); });
  salida();
};

// ============================================================== ETAPA B · POLIRRESINA
ESCENAS.etapa_b = () => {
  cabecera("Etapa B · opcional", "Copias en <span class='acento'>polirresina</span>");
  const fila = nuevo("div", "", "", esc, "position:absolute;left:110px;top:330px;width:1700px;display:flex;align-items:center;justify-content:space-between");
  const paso_ = (e, t, d) => nuevo("div", "tarjeta", `${emo(e, 70)}<div style="font-size:28px;font-weight:800;margin-top:12px">${t}</div><div style="font-size:21px;color:var(--suave);margin-top:6px">${d}</div>`, fila, "width:330px;padding:26px;text-align:center");
  const fl = () => nuevo("div", "", "➜", fila, "font-size:56px;color:var(--oro)");
  const a = paso_("🏠", "Tu pieza sellada", "el modelo original"); const f1 = fl();
  const b = paso_("🧱", "Molde de silicona", "se hace una vez"); const f2 = fl();
  const c = paso_("🧪", "Polirresina", "se vacía en el molde"); const f3 = fl();
  const d = paso_("🏘️", "Copias", "todas las que quieras");
  subir([a, f1, b, f2, c, f3, d], m(1) + 0.2, { stagger: 0.35 });
  const partes = nuevo("div", "", "", esc, "position:absolute;left:110px;top:640px;width:1700px;display:flex;gap:16px;justify-content:center");
  const ps = [["🟫", "Base"], ["🏘️", "Bloque de casas"], ["🥖", "Panadería"], ["🌲", "Árboles"], ["⛄", "Figuras"]].map(([e, t]) => nuevo("div", "pastilla", `${emo(e, 30)}${t}`, partes));
  const tit = nuevo("div", "", "Un molde por cada parte:", esc, "position:absolute;left:0;right:0;text-align:center;top:590px;font-size:24px;font-weight:700;color:var(--oro)");
  aparecer(tit, m(2)); pop(ps, m(2) + 0.4, { stagger: 0.3 });
  const toldos = nuevo("div", "tip", `${emo("✂️", 32)}<span>Los salientes (como los <b>toldos</b>) se cuelan aparte y se pegan después</span>`, esc, "left:0;right:0;margin:auto;width:fit-content;top:760px");
  pop(toldos, m(3) + 0.2);
  salida();
};

ESCENAS.molde = () => {
  cabecera("Etapa B", "El molde de <span class='acento'>silicona</span>");
  const mats = nuevo("div", "", "", esc, "position:absolute;left:110px;top:270px;width:760px;display:flex;gap:12px;flex-wrap:wrap");
  [["🧴", "Caucho de silicona + catalizador"], ["⚖️", "Balanza"], ["🥤", "Vasos y palitos"], ["🟩", "Plastilina"]].forEach(([e, t]) => nuevo("div", "pastilla", `${emo(e, 26)}${t}`, mats, "font-size:22px;padding:10px 18px"));
  pop(mats.children, m(0) + 0.3, { stagger: 0.25 });
  pasos(["Pieza pegada con <b>plastilina</b> · caja con <b>1 cm</b> de espacio", "Catalizador según el envase (<b>2–5 %</b>) · mezcla <b>2 min</b>",
    "Primera capa <b>con pincel</b>: sin burbujas", "Vierte en <b>hilo delgado</b>, desde <b>30 cm</b>, en una esquina", "<b>24 h</b> · desarma y saca la pieza"], 110, 420, 760, [m(1), m(2), m(3), m(4), m(5)])[0].parentNode.classList.add("compacto");
  const s = svg(930, 260, 900, 650);
  const tabla = el("rect", { x: 60, y: 560, width: 760, height: 30, fill: MDF, stroke: "#0d1424", "stroke-width": 2 }, s);
  const plast = el("rect", { x: 230, y: 548, width: 420, height: 14, rx: 6, fill: "#43c47a" }, s);
  const pieza = poli(s, [[250, 548], [250, 380], [440, 260], [630, 380], [630, 548]], "#e5e7eb");
  const caja = g(s);
  el("rect", { x: 170, y: 200, width: 24, height: 360, fill: "#f4f6fa", stroke: "#0d1424", "stroke-width": 2 }, caja);
  el("rect", { x: 686, y: 200, width: 24, height: 360, fill: "#f4f6fa", stroke: "#0d1424", "stroke-width": 2 }, caja);
  const c1 = cota(s, 194, 450, 250, 450, "1 cm", 0);
  const clipId = uid("clip");
  const clip = el("clipPath", { id: clipId }, defs(s));
  const nivel = el("rect", { x: 190, y: 548, width: 500, height: 0 }, clip);
  const sil = el("path", { d: "M194,548 L194,230 L686,230 L686,548 L630,548 L630,380 L440,260 L250,380 L250,548 Z", fill: "rgba(244,114,182,.55)", "clip-path": `url(#${clipId})` }, s);
  const capa = camino(s, "M250,548 L250,380 L440,260 L630,380 L630,548", "#f472b6", 10, "none");
  const vaso = g(s);
  vaso.innerHTML = DIB.vaso().replace("<svg", `<svg x="560" y="-60" width="140" height="140"`).replace("rgba(252,179,51,.45)", "rgba(244,114,182,.75)");
  const hilo = camino(s, "M660,60 Q664,150 668,226", "#f472b6", 5, "none");
  const c30 = cota(s, 740, 60, 740, 226, "30 cm", -40);
  const rec = nuevo("div", "tarjeta panel", `<div class="pt">${DIB.balanza().replace("<svg", "<svg width='60' height='60'")}100 g silicona + <span style="color:var(--oro)">2–5 g</span> catalizador</div>`, esc, "left:110px;top:818px;width:760px;padding:10px 20px;display:none");
  const t24 = reloj(esc, 1620, 270, "24 h", "⏳");
  aparecer([tabla], m(1)); aparecer([plast, pieza], m(1) + 0.4); aparecer(caja, m(1) + 1.2); pop(c1, m(1) + 1.8);
  tl.set(rec, { display: "block" }, m(2)); subir(rec, m(2) + 0.1);
  tl.from(capa, { drawSVG: "0%", duration: 1.6 }, m(3) + 0.4);
  aparecer(vaso, m(4) + 0.2); tl.from(hilo, { drawSVG: "0%", duration: 0.8 }, m(4) + 0.8); pop(c30, m(4) + 1.4);
  tl.to(nivel, { attr: { y: 226, height: 322 }, duration: 3.5, ease: "none" }, m(4) + 1.2);
  tl.to([vaso, hilo, c30], { opacity: 0, duration: 0.4 }, m(5));
  tl.set(rec, { display: "none" }, m(5));
  pop(t24, m(5) + 0.2);
  tl.to([sil, caja], { y: -180, duration: 1.0, ease: "power2.inOut" }, m(5) + 1.6);
  salida();
};

ESCENAS.colado = () => {
  cabecera("Etapa B", "Colar la <span class='acento'>polirresina</span>");
  const rec = nuevo("div", "tarjeta panel", `<div class="pt">${emo("🧪", 34)}La mezcla</div>
    <table class="tabla" style="margin-top:10px;width:100%"><tr><td>Resina poliéster preacelerada</td><td class="num">100 g</td></tr>
    <tr><td>Carbonato de calcio (mismo peso)</td><td class="num">100 g</td></tr>
    <tr><td>Catalizador MEKP (1–2 % de la resina)</td><td class="num">1–2 ml</td></tr></table>`, esc, "left:110px;top:290px;width:780px");
  const trs = rec.querySelectorAll("tr");
  subir(rec, m(0) + 0.2);
  tl.from(trs[0], { opacity: 0.2, duration: 0.3 }, m(0) + 0.6);
  tl.from(trs[1], { opacity: 0.2, duration: 0.3 }, m(1) + 0.2);
  tl.from(trs[2], { opacity: 0.2, duration: 0.3 }, m(2) + 0.2);
  const t = reloj(esc, 110, 590, "10 a 15 min para trabajar · menos con calor", "⏱️");
  pop(t, m(3) + 0.2);
  pasos(["Casas huecas: llena <b>⅓</b>, gira en todas direcciones", "Bota el sobrante · repite hasta <b>3–4 mm</b>", "Desmolda en <b>1–2 h</b> · lija · abre ventanas"], 110, 680, 780, [m(4), m(5), m(6)])[0].parentNode.classList.add("compacto");
  const s = svg(960, 260, 860, 660);
  const cx = 430, cy = 330;
  const molde = g(s);
  el("rect", { x: cx - 230, y: cy - 230, width: 460, height: 460, rx: 30, fill: "rgba(244,114,182,.55)", stroke: "#0d1424", "stroke-width": 2 }, molde);
  const cav = poli(molde, [[cx - 140, cy + 160], [cx - 140, cy - 40], [cx, cy - 150], [cx + 140, cy - 40], [cx + 140, cy + 160]], "#0b1222");
  const capa = el("path", { d: `M${cx - 140},${cy + 160} L${cx - 140},${cy - 40} L${cx},${cy - 150} L${cx + 140},${cy - 40} L${cx + 140},${cy + 160} L${cx + 112},${cy + 160} L${cx + 112},${cy - 26} L${cx},${cy - 116} L${cx - 112},${cy - 26} L${cx - 112},${cy + 160} Z`, fill: "#d9c7a3", opacity: 0 }, molde);
  const liquido = el("rect", { x: cx - 140, y: cy + 60, width: 280, height: 100, fill: "#d9c7a3", opacity: 0 }, molde);
  const flechas = camino(s, `M${cx + 280},${cy - 120} A300,300 0 0 1 ${cx + 280},${cy + 160}`, "#fcb333", 5);
  const puntaF = el("path", { d: `M${cx + 280},${cy + 160} l-16,-14 l22,-4 z`, fill: "#fcb333" }, s);
  const cGros = cota(s, cx - 140, cy + 200, cx - 112, cy + 200, "3–4 mm", 26);
  const casaF = poli(s, [[cx - 140, cy + 160], [cx - 140, cy - 40], [cx, cy - 150], [cx + 140, cy - 40], [cx + 140, cy + 160]], "#d9c7a3");
  casaF.style.opacity = 0;
  el("rect", { x: cx - 50, y: cy, width: 100, height: 80, fill: "#0b1222", class: "vent" }, s).style.opacity = 0;
  aparecer(molde, m(0) + 0.4);
  tl.to(liquido, { opacity: 1, duration: 0.5 }, m(4) + 0.3);
  tl.to(molde, { rotation: 25, transformOrigin: `${cx}px ${cy}px`, duration: 1.0, yoyo: true, repeat: 3, ease: "sine.inOut" }, m(4) + 1.0);
  tl.to(liquido, { opacity: 0, duration: 0.8 }, m(5) + 0.2);
  tl.to(capa, { opacity: 1, duration: 1.2 }, m(4) + 2.0);
  tl.from(flechas, { drawSVG: "0%", duration: 1 }, m(4) + 1.0);
  pop(cGros, m(5) + 0.8);
  tl.to([molde, flechas, puntaF, cGros], { opacity: 0, duration: 0.5 }, m(6));
  tl.to(casaF, { opacity: 1, duration: 0.6 }, m(6) + 0.3);
  tl.to(s.querySelector(".vent"), { opacity: 1, duration: 0.4 }, m(6) + 2.4);
  const fin = nuevo("div", "tip", `${emo("🎨", 32)}<span>Y desde aquí: igual que la etapa A</span>`, esc, "left:1180px;top:860px");
  pop(fin, m(6) + 3.0);
  salida();
};

ESCENAS.seguridad_resina = () => {
  cabecera("Etapa B", "Cuidado con la <span class='rojo'>resina</span>");
  const datos = [["😷", "Vapores tóxicos", "Al aire libre o con mucha ventilación · respirador con filtros para vapores orgánicos"],
    ["🥽", "Catalizador corrosivo", "Sobre todo para los ojos: lentes y guantes de nitrilo, siempre"],
    ["⚠️", "Nunca MEKP + cobalto directo", "Reaccionan con violencia: compra la resina ya preacelerada"],
    ["🗑️", "No botes resina líquida", "Deja que endurezca en el vaso y luego a la basura"]];
  const cs = datos.map(([e, t, d], i) => tarjetaPanel(110 + (i % 2) * 860, 300 + Math.floor(i / 2) * 290, 830, 260, `${emo(e, 56)}`, `<div style="font-size:32px;font-weight:800;color:#fff;margin:14px 0 8px">${t}</div>${d}`));
  cs.forEach((c, i) => { pop(c, m(i + 1)); resaltar(c, m(i + 1) + 0.2, "var(--rojo)"); if (i) normal(cs[i - 1], m(i + 1)); });
  salida();
};

// ============================================================== FINAL
ESCENAS.final = () => {
  const v = villa(esc, 980, 200, 860, { luces: 0, motor: 0 });
  const c = nuevo("div", "cabecera", "", esc, "top:150px");
  nuevo("div", "kicker", "Resumen", c);
  const h = nuevo("h1", "titulo", "¡Tu villa está <span class='acento'>lista</span>!", c);
  const sp = new SplitText(h, { type: "lines,words", linesClass: "linea-titulo" });
  tl.from(sp.words, { yPercent: 110, duration: 0.8, stagger: 0.06, ease: "power4.out" }, 0.2);
  const fila = nuevo("div", "", "", esc, "position:absolute;left:110px;top:340px;width:780px;display:flex;flex-wrap:wrap;gap:12px");
  const ps = ["Base y terreno", "Casas y texturas", "Árboles y figuras", "Sellado", "Pintura", "Motor", "Luces", "Nieve", "Montaje"].map((t, i) => nuevo("div", "pastilla", `${emo("✅", 24)}${t}`, fila, "font-size:23px"));
  pop(ps, m(0) + 0.6, { stagger: 0.45 });
  const guia = nuevo("div", "tarjeta panel", `<div class="pt">${emo("📘", 34)}Guía escrita completa</div><div class="pd" style="font-size:23px">Materiales, medidas y circuito en<br><span class="mono" style="color:#cfe0ff">github.com/paulantezana/tutoriales</span><br><span class="mono" style="color:#cfe0ff">villa-navidena/README.md</span></div>`, esc, "left:110px;top:560px;width:780px");
  subir(guia, m(1) + 0.2);
  const fn = nuevo("div", "", "¡Feliz Navidad!", esc, "position:absolute;left:110px;top:780px;font:900 84px 'Inter Display';letter-spacing:-0.03em;color:#fff");
  const sp2 = new SplitText(fn, { type: "chars" });
  tl.from(sp2.chars, { yPercent: 60, opacity: 0, duration: 0.6, stagger: 0.04, ease: "back.out(1.7)" }, m(2) + 0.8);
  tl.to(esc, { opacity: 0, duration: 0.8 }, DUR - 0.8);
};

iniciar();
