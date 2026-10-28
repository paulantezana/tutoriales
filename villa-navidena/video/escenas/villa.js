/* La villa ilustrada (vista de frente), basada en el modelo de la tienda:
   casa tudor con tienda, iglesia con torre, casa del arco, río con puente,
   pista de patinaje que gira, árbol de Navidad, panadería y muñeco de nieve.
   villa(padre, x, y, ancho, opciones) devuelve las partes para animarlas. */

const COL = {
  nieve: "#eef3fb", nieveSombra: "#c9d6ea", roca: "#59606e", rocaClara: "#7d8595", rocaOscura: "#3a404c",
  pino: "#1f5c3c", pinoSombra: "#174a30", pinoClaro: "#2f7a50",
  teja: "#7a3a2b", tejaOscura: "#55261b", ladrillo: "#8a4636", ladrilloOscuro: "#5c2b20",
  crema: "#ead9b4", viga: "#3d261b", verdePuerta: "#1f5a3d", rojo: "#c53b32", pizarra: "#4a566e",
  amarillo: "#f1d48a", hielo: "#bfe6ff", agua: "#2f6fd1", ventanaOff: "#2f3546",
};

function villa(padre, x, y, ancho, op = {}) {
  const o = { luces: 0, motor: 0, apagada: false, ...op };
  const esc_ = ancho / 1000;
  const s = svg(x, y, ancho, ancho * 0.8, padre, "0 0 1000 800");
  const D = defs(s);
  const r = azar(op.semilla || 11);
  const P = {};   // partes

  // ---------- patrones de textura
  const pat = (id, w, h, inner) => {
    const p = el("pattern", { id, width: w, height: h, patternUnits: "userSpaceOnUse" }, D);
    p.innerHTML = inner;
    return `url(#${id})`;
  };
  const sid = uid("v");
  const LAD = pat(sid + "lad", 24, 12, `<rect width="24" height="12" fill="${COL.ladrillo}"/><path d="M0,11.5 H24 M0,5.5 H24 M6,0 V5.5 M18,5.5 V11.5" stroke="${COL.ladrilloOscuro}" stroke-width="1.6"/>`);
  const TEJ = pat(sid + "tej", 18, 12, `<rect width="18" height="12" fill="${COL.teja}"/><path d="M0,11 Q4.5,5 9,11 Q13.5,5 18,11" fill="none" stroke="${COL.tejaOscura}" stroke-width="1.8"/>`);
  const PIZ = pat(sid + "piz", 16, 10, `<rect width="16" height="10" fill="${COL.pizarra}"/><path d="M0,9.5 H16 M8,0 V9.5" stroke="#36405a" stroke-width="1.5"/>`);
  const ROC = pat(sid + "roc", 60, 34, `<rect width="60" height="34" fill="${COL.roca}"/><path d="M0,16 L14,12 L30,18 L44,10 L60,15 M10,34 L16,20 M38,34 L34,22 M50,10 L54,0 M22,12 L20,0" stroke="${COL.rocaOscura}" stroke-width="2" fill="none"/><path d="M4,9 L14,6 M32,27 L44,24" stroke="${COL.rocaClara}" stroke-width="2"/>`);
  const LUZ = gradRadial(s, [[0, "#fff6d6"], [0.55, "#ffd27a"], [1, "#f59e0b"]]);
  const NIEVE = gradLineal(s, [[0, "#ffffff"], [1, "#dfe8f6"]]);
  const BRILLO = filtroBrillo(s, 5);
  const HIELO = gradRadial(s, [[0, "#e9f7ff"], [0.7, "#bfe6ff"], [1, "#8cc8ee"]]);
  const AGUA = gradLineal(s, [[0, "#1d4fa8"], [0.5, "#3b82f6"], [1, "#1d4fa8"]], 0, 0, 1, 0);

  const ventanas = [];
  const ventana = (gr, x, y, w, h, arco = false, barras = true) => {
    const d = arco ? `M${x},${y + h} L${x},${y + w / 2} A${w / 2},${w / 2} 0 0 1 ${x + w},${y + w / 2} L${x + w},${y + h} Z` : `M${x},${y} H${x + w} V${y + h} H${x} Z`;
    const marco = camino(gr, d, "#f3efe6", 4, COL.ventanaOff);
    const luz = camino(gr, d, "none", 0, LUZ, { opacity: 0 });
    if (barras) {
      linea(gr, x + w / 2, y + (arco ? 2 : 0), x + w / 2, y + h, "#f3efe6", 2.5);
      linea(gr, x, y + h * 0.55, x + w, y + h * 0.55, "#f3efe6", 2.5);
    }
    ventanas.push(luz);
    return marco;
  };
  const nieveTecho = (gr, puntos, grosor = 14, gotas = true) => {
    // capa de nieve sobre los bordes superiores de un techo: lista de puntos (x,y)
    let d = `M${puntos[0][0]},${puntos[0][1]}`;
    puntos.slice(1).forEach(([px, py]) => (d += ` L${px},${py}`));
    const vuelta = [...puntos].reverse().map(([px, py]) => [px, py + grosor]);
    vuelta.forEach(([px, py], i) => {
      if (gotas && i > 0) {
        const [qx, qy] = vuelta[i - 1];
        const mx = (qx + px) / 2, my = (qy + py) / 2;
        d += ` Q${mx},${my + 6 + r() * 8} ${px},${py}`;
      } else d += ` L${px},${py}`;
    });
    d += " Z";
    camino(gr, d, "#c9d6ea", 1.5, NIEVE);
  };
  const pino = (gr, cx, base, h, w, sombra = true) => {
    const p = g(gr);
    el("rect", { x: cx - w * 0.06, y: base - h * 0.12, width: w * 0.12, height: h * 0.12, fill: "#5b3a24" }, p);
    [[0.0, 0.42, 1.0], [0.28, 0.72, 0.78], [0.55, 1.0, 0.52]].forEach(([a, b, k]) => {
      const yb = base - h * 0.1 - a * h * 0.85, yt = base - h * 0.1 - b * h * 0.9;
      const hw = (w / 2) * k;
      camino(p, `M${cx - hw},${yb} Q${cx},${yb - 10} ${cx + hw},${yb} L${cx},${yt} Z`, COL.pinoSombra, 1.5, COL.pino);
      if (sombra) camino(p, `M${cx},${yb - 5} Q${cx + hw * 0.5},${yb - 6} ${cx + hw},${yb} L${cx},${yt} Z`, "none", 0, COL.pinoSombra, { opacity: 0.8 });
      camino(p, `M${cx - hw * 0.95},${yb - 2} Q${cx - hw * 0.5},${yb - 14} ${cx - hw * 0.3},${yb - 6} Q${cx - hw * 0.1},${yb - 16} ${cx},${yt + 6}`, "none", 0, "none");
      camino(p, `M${cx - hw * 0.92},${yb - 1} L${cx - hw * 0.25},${yt + (yb - yt) * 0.35} L${cx},${yt + 4}`, "#ffffff", 5, "none", { opacity: 0.92 });
      camino(p, `M${cx + hw * 0.15},${yt + (yb - yt) * 0.6} L${cx + hw * 0.6},${yb - 3}`, "#ffffff", 4, "none", { opacity: 0.7 });
    });
    return p;
  };
  const persona = (gr, cx, base, h, abrigo, gorro, patina = false) => {
    const p = g(gr);
    const k = h / 40;
    linea(p, cx - 4 * k, base - 12 * k, cx - 6 * k, base - 1 * k, "#2b2f3a", 3 * k);
    linea(p, cx + 4 * k, base - 12 * k, cx + 7 * k, base - 2 * k, "#2b2f3a", 3 * k);
    if (patina) {
      linea(p, cx - 10 * k, base, cx - 2 * k, base, "#e5e7eb", 2 * k);
      linea(p, cx + 3 * k, base - 1 * k, cx + 11 * k, base - 1 * k, "#e5e7eb", 2 * k);
    }
    camino(p, `M${cx - 9 * k},${base - 10 * k} L${cx - 6 * k},${base - 28 * k} L${cx + 6 * k},${base - 28 * k} L${cx + 9 * k},${base - 10 * k} Z`, "#0d1424", 1, abrigo);
    linea(p, cx - 6 * k, base - 26 * k, cx - 13 * k, base - 18 * k, abrigo, 3.5 * k);
    linea(p, cx + 6 * k, base - 26 * k, cx + 13 * k, base - 20 * k, abrigo, 3.5 * k);
    el("circle", { cx, cy: base - 33 * k, r: 6 * k, fill: "#f2c9a8" }, p);
    camino(p, `M${cx - 6.5 * k},${base - 34 * k} Q${cx},${base - 46 * k} ${cx + 6.5 * k},${base - 34 * k} Z`, "none", 0, gorro);
    el("rect", { x: cx - 7 * k, y: base - 29 * k, width: 14 * k, height: 3 * k, rx: 1.5 * k, fill: "#f3efe6" }, p);
    return p;
  };

  // ---------- sombra, base y terreno
  el("ellipse", { cx: 500, cy: 735, rx: 470, ry: 26, fill: "#000", opacity: 0.35 }, s);
  P.base = g(s);
  camino(P.base, "M58,640 L942,640 L930,722 Q500,734 70,722 Z", COL.rocaOscura, 2, ROC);
  P.terreno = g(s);
  camino(P.terreno, "M58,642 L942,642 L882,470 L118,470 Z", "#c9d6ea", 2, NIEVE);
  // labio de nieve con gotas en el borde delantero
  let lab = "M50,626 L950,626 L950,650";
  for (let xx = 950; xx > 50;) {
    const paso = 26 + r() * 22, x2 = Math.max(50, xx - paso), largo = 8 + r() * 28;
    lab += ` C${xx},${652 + largo} ${x2},${652 + largo} ${x2},650`;
    xx = x2;
  }
  camino(P.base, lab + " Z", "#c9d6ea", 1.5, NIEVE);

  // ---------- nivel de atrás (meseta)
  P.meseta = g(s);
  camino(P.meseta, "M122,470 L878,470 L878,500 L122,500 Z", COL.rocaOscura, 2, "#4a3b33");
  camino(P.meseta, "M128,470 L872,470 L860,438 L140,438 Z", "#c9d6ea", 1.5, NIEVE);
  let lm = "M118,464 L882,464 L882,476";
  for (let xx = 882; xx > 118;) {
    const x2 = Math.max(118, xx - (20 + r() * 20));
    lm += ` C${xx},${480 + r() * 12} ${x2},${480 + r() * 12} ${x2},476`;
    xx = x2;
  }
  camino(P.meseta, lm + " Z", "none", 0, NIEVE);

  // ---------- pinos de atrás (derecha)
  P.pinosAtras = g(s);
  pino(P.pinosAtras, 712, 468, 225, 92);
  pino(P.pinosAtras, 852, 470, 205, 92);
  pino(P.pinosAtras, 785, 472, 262, 112);

  // ---------- casa tudor (izquierda)
  P.tudor = g(s);
  camino(P.tudor, "M150,345 L320,345 L320,462 L150,462 Z", "#0d1424", 2, COL.crema);
  camino(P.tudor, "M138,352 L235,262 L332,352 Z", COL.tejaOscura, 2, TEJ);
  camino(P.tudor, "M158,345 L235,276 L312,345 Z", "#0d1424", 2, COL.crema);
  [[150, 345, 150, 462], [205, 345, 205, 462], [265, 345, 265, 462], [320, 345, 320, 462], [150, 400, 320, 400], [150, 345, 320, 345],
   [205, 345, 265, 400], [265, 345, 205, 400], [190, 345, 235, 300], [280, 345, 235, 300], [235, 276, 235, 300]]
    .forEach(([a, b, c, d]) => linea(P.tudor, a, b, c, d, COL.viga, 6));
  ventana(P.tudor, 218, 296, 34, 40, false);
  // buhardilla
  camino(P.tudor, "M162,318 L186,296 L210,318 L210,340 L162,340 Z", "#0d1424", 2, COL.crema);
  camino(P.tudor, "M156,322 L186,292 L216,322", COL.tejaOscura, 6, "none");
  ventana(P.tudor, 175, 312, 22, 24, false, false);
  // vitrina con toldo rojo
  el("rect", { x: 210, y: 398, width: 96, height: 60, fill: "#7a1f1f", stroke: "#0d1424", "stroke-width": 2 }, P.tudor);
  ventana(P.tudor, 216, 410, 84, 44, false);
  linea(P.tudor, 244, 410, 244, 454, "#f3efe6", 2.5); linea(P.tudor, 272, 410, 272, 454, "#f3efe6", 2.5);
  let toldo = "M204,388 L312,388 L312,402";
  for (let xx = 312; xx > 204; xx -= 18) toldo += ` Q${xx - 9},${412} ${xx - 18},402`;
  camino(P.tudor, toldo + " Z", "#7a1f1f", 2, COL.rojo);
  for (let xx = 204; xx < 312; xx += 18) el("rect", { x: xx + 6, y: 388, width: 6, height: 14, fill: "#f6d77b", opacity: 0.85 }, P.tudor);
  // puerta verde
  camino(P.tudor, "M160,462 L160,418 Q176,404 192,418 L192,462 Z", "#0d1424", 2, COL.verdePuerta);
  nieveTecho(P.tudor, [[132, 354], [235, 258], [338, 354]], 13);

  // ---------- pino entre la casa tudor y la iglesia
  P.pinoMedio = g(s);
  pino(P.pinoMedio, 330, 468, 232, 78);

  // ---------- iglesia
  P.iglesia = g(s);
  camino(P.iglesia, "M345,335 L530,335 L530,462 L345,462 Z", "#0d1424", 2, LAD);
  camino(P.iglesia, "M398,340 L462,252 L540,340 Z", COL.tejaOscura, 2, TEJ);
  camino(P.iglesia, "M412,335 L462,268 L520,335 Z", "#0d1424", 2, LAD);
  ventana(P.iglesia, 448, 286, 28, 38, true);
  ventana(P.iglesia, 425, 356, 56, 56, true);
  camino(P.iglesia, "M488,462 L488,420 Q506,398 524,420 L524,462 Z", "#0d1424", 2, COL.verdePuerta);
  el("circle", { cx: 506, cy: 428, r: 8, fill: "none", stroke: "#2f8a4f", "stroke-width": 4 }, P.iglesia);
  el("circle", { cx: 506, cy: 422, r: 2.5, fill: COL.rojo }, P.iglesia);
  // torre grande
  camino(P.iglesia, "M345,335 L345,160 L408,160 L408,335 Z", "#0d1424", 2, LAD);
  ventana(P.iglesia, 361, 182, 32, 46, true);
  ventana(P.iglesia, 364, 262, 26, 34, false);
  el("rect", { x: 340, y: 150, width: 73, height: 12, fill: "#f3efe6", stroke: "#0d1424", "stroke-width": 2 }, P.iglesia);
  camino(P.iglesia, "M336,152 L376,64 L417,152 Z", COL.tejaOscura, 2, TEJ);
  nieveTecho(P.iglesia, [[332, 156], [376, 60], [421, 156]], 12);
  // torre pequeña
  camino(P.iglesia, "M496,335 L496,236 L528,236 L528,335 Z", "#0d1424", 2, LAD);
  ventana(P.iglesia, 503, 250, 18, 26, true, false);
  camino(P.iglesia, "M490,238 L512,192 L534,238 Z", COL.tejaOscura, 2, TEJ);
  nieveTecho(P.iglesia, [[487, 241], [512, 188], [537, 241]], 9);
  nieveTecho(P.iglesia, [[392, 344], [462, 248], [546, 344]], 12);
  nieveTecho(P.iglesia, [[341, 339], [534, 339]], 9);

  // ---------- casa del arco
  P.arco = g(s);
  camino(P.arco, "M540,360 L662,360 L662,462 L540,462 Z", "#0d1424", 2, LAD);
  camino(P.arco, "M528,366 L601,292 L674,366 Z", COL.tejaOscura, 2, TEJ);
  camino(P.arco, "M548,360 L601,306 L654,360 Z", "#0d1424", 2, COL.crema);
  ventana(P.arco, 588, 318, 26, 32, false);
  camino(P.arco, "M576,462 L576,414 Q601,388 626,414 L626,462 Z", "#0d1424", 2, COL.verdePuerta);
  el("circle", { cx: 601, cy: 420, r: 9, fill: "none", stroke: "#2f8a4f", "stroke-width": 4 }, P.arco);
  ventana(P.arco, 548, 392, 20, 30, false, false);
  ventana(P.arco, 636, 392, 20, 30, false, false);
  nieveTecho(P.arco, [[522, 369], [601, 288], [680, 369]], 13);
  // guirnalda
  P.guirnalda = camino(P.arco, "M352,344 Q440,372 530,346 Q600,382 662,364", "#2f8a4f", 6, "none");
  [[372, 352, "#ef4444"], [410, 360, "#facc15"], [450, 360, "#60a5fa"], [490, 354, "#ef4444"], [560, 360, "#facc15"], [600, 370, "#60a5fa"], [635, 368, "#ef4444"]]
    .forEach(([cx, cy, c]) => el("circle", { cx, cy, r: 3.5, fill: c }, P.arco));

  // ---------- puente y río
  P.rio = g(s);
  const rio = camino(P.rio, "M455,500 L505,500 Q520,560 540,640 L418,640 Q440,560 455,500 Z", "#173c7d", 2, AGUA);
  camino(P.rio, "M470,510 Q462,570 448,632 M492,512 Q500,575 512,632", "#bfe6ff", 2.5, "none", { opacity: 0.7, "stroke-dasharray": "14 18" });
  P.espuma = camino(P.rio, "M480,520 Q476,580 470,632", "#ffffff", 3, "none", { opacity: 0.85, "stroke-dasharray": "8 22" });
  camino(P.rio, "M432,500 L528,500 L528,476 L432,476 Z", COL.rocaOscura, 2, ROC);
  camino(P.rio, "M446,500 Q480,470 514,500 Z", "#0b1222", 0, "#0b1222");
  camino(P.rio, "M428,476 L532,476", "#ffffff", 8, "none");

  // ---------- pista de patinaje
  P.pista = g(s);
  el("ellipse", { cx: 285, cy: 572, rx: 152, ry: 54, fill: COL.roca, stroke: COL.rocaOscura, "stroke-width": 2 }, P.pista);
  el("ellipse", { cx: 285, cy: 566, rx: 152, ry: 50, fill: "none", stroke: "#ffffff", "stroke-width": 9, opacity: 0.95 }, P.pista);
  el("ellipse", { cx: 285, cy: 574, rx: 132, ry: 42, fill: "#1a2233" }, P.pista);
  P.hielo = el("ellipse", { cx: 285, cy: 576, rx: 126, ry: 39, fill: HIELO }, P.pista);
  P.marcas = [0, 1, 2, 3].map(() => camino(P.pista, "", "#ffffff", 2.5, "none", { opacity: 0.75 }));
  P.patinadores = [persona(P.pista, 0, 0, 40, "#c53b32", "#1f5a3d", true), persona(P.pista, 0, 0, 38, "#2563eb", "#c53b32", true)];

  // ---------- pino pequeño a la izquierda y niño en la meseta
  P.pinosAdelante = g(s);
  pino(P.pinosAdelante, 96, 628, 128, 58);
  P.figuras = g(s);
  persona(P.figuras, 256, 470, 34, "#9d3a6b", "#ef4444");

  // ---------- árbol de Navidad
  P.arbol = g(s);
  el("rect", { x: 576, y: 600, width: 18, height: 18, fill: "#5b3a24" }, P.arbol);
  const arb = [[0, 0.36, 1], [0.24, 0.64, 0.8], [0.5, 0.92, 0.58]];
  arb.forEach(([a, b, k]) => {
    const yb = 606 - a * 160, yt = 606 - b * 168, hw = 58 * k;
    camino(P.arbol, `M${585 - hw},${yb} Q585,${yb - 12} ${585 + hw},${yb} L585,${yt} Z`, "#155c34", 1.5, "#1f7a43");
  });
  for (let i = 0; i < 60; i++) {
    const t = r(), yy = 606 - t * 160, hw = 54 * (1 - t * 0.9) * (r() * 2 - 1);
    el("circle", { cx: 585 + hw, cy: yy - r() * 8, r: 1.4 + r() * 1.6, fill: r() > 0.5 ? "#a7f3d0" : "#fef3c7", opacity: 0.85 }, P.arbol);
  }
  [[560, 584], [604, 560], [575, 530], [598, 506], [590, 594], [566, 548]].forEach(([cx, cy]) => el("circle", { cx, cy, r: 5, fill: "#dc2626", stroke: "#7f1d1d", "stroke-width": 1 }, P.arbol));
  P.estrella = camino(P.arbol, estrellaD(585, 434, 17, 7), "#e5e7eb", 2, "#f8fafc");

  // ---------- panadería
  P.panaderia = g(s);
  camino(P.panaderia, "M655,540 L905,540 L905,640 L655,640 Z", "#0d1424", 2, COL.amarillo);
  camino(P.panaderia, "M640,548 L780,404 L920,548 Z", "#2c3446", 2, PIZ);
  camino(P.panaderia, "M682,540 L780,440 L878,540 Z", "#0d1424", 2, COL.amarillo);
  ventana(P.panaderia, 764, 466, 32, 40, true);
  el("rect", { x: 722, y: 548, width: 116, height: 26, rx: 4, fill: "#fbfbf7", stroke: "#7a1f1f", "stroke-width": 2 }, P.panaderia);
  texto(P.panaderia, 780, 568, "BAKERY", "", "middle", { style: "font:800 19px Inter;fill:#b91c1c;letter-spacing:1px" });
  [[664, 760], [800, 896]].forEach(([a, b]) => {
    ventana(P.panaderia, a + 8, 604, b - a - 16, 30, false);
    let d = `M${a},582 L${b},582 L${b},598`;
    for (let xx = b; xx > a; xx -= 16) d += ` Q${xx - 8},606 ${xx - 16},598`;
    camino(P.panaderia, d + " Z", "#7a1f1f", 2, "#fbfbf7");
    for (let xx = a; xx < b; xx += 16) el("rect", { x: xx, y: 582, width: 8, height: 16, fill: COL.rojo }, P.panaderia);
  });
  camino(P.panaderia, "M766,640 L766,598 Q780,586 794,598 L794,640 Z", "#0d1424", 2, COL.verdePuerta);
  nieveTecho(P.panaderia, [[632, 552], [780, 398], [928, 552]], 16);

  // ---------- muñeco de nieve
  P.muneco = g(s);
  const mn = [[930, 652, 22], [930, 618, 16], [930, 592, 11]];
  mn.forEach(([cx, cy, rr]) => el("circle", { cx, cy, r: rr, fill: "#f8fafc", stroke: "#c9d6ea", "stroke-width": 1.5 }, P.muneco));
  el("rect", { x: 918, y: 566, width: 24, height: 18, fill: "#111827" }, P.muneco);
  el("rect", { x: 912, y: 582, width: 36, height: 5, rx: 2, fill: "#111827" }, P.muneco);
  camino(P.muneco, "M916,604 Q930,612 944,604 L948,626 L940,626 L938,610", "none", 0, "#dc2626");
  camino(P.muneco, "M930,594 L944,597 L930,598 Z", "none", 0, "#f97316");
  el("circle", { cx: 926, cy: 589, r: 1.6, fill: "#111827" }, P.muneco);
  el("circle", { cx: 934, cy: 589, r: 1.6, fill: "#111827" }, P.muneco);

  // ---------- LEDs
  const LED = [];
  const led = (cx, cy, tipo, fase = 0) => {
    const halo = el("circle", { cx, cy, r: 26, fill: gradRadial(s, [[0, "#ffffff", 0.9], [0.25, "#ffd27a", 0.55], [1, "#ffd27a", 0]]), opacity: 0 }, s);
    const nucleo = el("circle", { cx, cy, r: 6, fill: "#5b6070", stroke: "#0d1424", "stroke-width": 1.2 }, s);
    LED.push({ halo, nucleo, tipo, fase, stop: halo.firstChild });
    return nucleo;
  };
  // blanco cálido (foquitos de fachada)
  [[176, 402], [235, 290], [376, 342], [601, 300], [700, 524], [860, 524], [152, 594], [420, 598]].forEach(([a, b], i) => led(a, b, "w", i * 0.7));
  // RGB de cambio lento: 4 en el árbol, la estrella y la guirnalda
  [[560, 562], [610, 528], [572, 496], [604, 594], [585, 434], [652, 366]].forEach(([a, b], i) => led(a, b, "rgb", i * 1.3));
  // azul bajo el puente
  led(480, 506, "b");
  P.leds = LED;

  // gradientes de cada halo (para poder cambiar su color)
  LED.forEach((l) => {
    const id = l.halo.getAttribute("fill").slice(5, -1);
    l.grad = document.getElementById(id);
  });

  // ---------- animación continua: luces y pista
  const RGB = ["#ff4d4d", "#ffd84d", "#4dff88", "#4dc3ff", "#b44dff", "#ff4dd2"];
  const mezcla = (a, b, t) => {
    const pa = parseInt(a.slice(1), 16), pb = parseInt(b.slice(1), 16);
    const c = [16, 8, 0].map((sh) => Math.round(((pa >> sh) & 255) * (1 - t) + ((pb >> sh) & 255) * t));
    return "#" + c.map((v) => v.toString(16).padStart(2, "0")).join("");
  };
  P.encendida = (t) => !o.apagada && t >= o.luces;
  CUADRO.push((t) => {
    const on = P.encendida(t);
    const k = on ? Math.min(1, (t - o.luces) / 0.6) : 0;
    ventanas.forEach((v) => v.setAttribute("opacity", k));
    LED.forEach((l) => {
      let c = "#ffd27a", brillo = 1;
      if (l.tipo === "w") brillo = 0.88 + 0.12 * Math.sin(t * 7 + l.fase * 5);
      if (l.tipo === "b") { c = "#4d8dff"; brillo = 0.85 + 0.15 * Math.sin(t * 1.5); }
      if (l.tipo === "rgb") {
        const f = (t * 0.45 + l.fase) % RGB.length, i = Math.floor(f);
        c = mezcla(RGB[i], RGB[(i + 1) % RGB.length], f - i);
      }
      l.nucleo.setAttribute("fill", on ? mezcla(c, "#ffffff", l.tipo === "w" ? 0.55 : 0.35) : "#5b6070");
      l.halo.setAttribute("opacity", on ? k * brillo : 0);
      const st = l.grad.children;
      st[1].setAttribute("stop-color", c); st[2].setAttribute("stop-color", c);
    });
    P.estrella.setAttribute("fill", on ? "#fff8dc" : "#e5e7eb");
    // pista que gira (8 vueltas por minuto)
    const ang = Math.max(0, t - o.motor) * (Math.PI * 2 / 7.5);
    P.patinadores.forEach((p, i) => {
      const a = ang + i * Math.PI;
      const px = 285 + Math.cos(a) * 72, py = 578 + Math.sin(a) * 22;
      const esc2 = 0.85 + 0.15 * (Math.sin(a) + 1) / 2;
      p.setAttribute("transform", `translate(${px},${py}) scale(${esc2})`);
    });
    P.marcas.forEach((mk, i) => {
      const a = ang + i * (Math.PI / 2) + 0.5;
      const pts = [0, 0.35, 0.7].map((d) => [285 + Math.cos(a + d) * 100, 576 + Math.sin(a + d) * 30]);
      mk.setAttribute("d", `M${pts[0][0]},${pts[0][1]} Q${pts[1][0]},${pts[1][1]} ${pts[2][0]},${pts[2][1]}`);
    });
    const izq = P.patinadores.map((p, i) => Math.sin(ang + i * Math.PI));
    if (izq[0] < izq[1]) P.pista.appendChild(P.patinadores[1]); else P.pista.appendChild(P.patinadores[0]);
    P.espuma.setAttribute("stroke-dashoffset", -t * 30);
  });

  // punto de la villa (coordenadas del dibujo) -> píxeles de la pantalla
  P.punto = (px, py) => [x + px * esc_, y + py * esc_];
  P.svg = s;
  P.esc = esc_;
  P.ANCLAS = {
    tudor: [235, 380], iglesia: [376, 120], arco: [601, 330], rio: [470, 590], pista: [285, 572], arbol: [585, 520],
    panaderia: [780, 590], muneco: [930, 610], pinos: [785, 330], meseta: [180, 485], base: [700, 690], torre: [376, 200],
  };
  return P;
}

function estrellaD(cx, cy, R, r) {
  let d = "";
  for (let i = 0; i < 10; i++) {
    const a = -Math.PI / 2 + (i * Math.PI) / 5, rr = i % 2 ? r : R;
    d += `${i ? "L" : "M"}${cx + Math.cos(a) * rr},${cy + Math.sin(a) * rr} `;
  }
  return d + "Z";
}
