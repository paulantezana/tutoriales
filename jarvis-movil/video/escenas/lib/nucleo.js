/* Núcleo de YARBYS: interfaz circular inspirada en el JARVIS de las películas.
   Todo es geometría simple (círculos, arcos, líneas y rectángulos), así que se puede
   portar tal cual a Flutter con CustomPainter. Cada anillo es un <g> con su id para
   poder girarlo en las animaciones. */
(function () {
  const NS = "http://www.w3.org/2000/svg";

  function el(padre, tag, attrs) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    padre.appendChild(e);
    return e;
  }
  const rad = (g) => ((g - 90) * Math.PI) / 180;
  const punto = (r, g) => [r * Math.cos(rad(g)), r * Math.sin(rad(g))];
  function arco(r, a0, a1) {
    const [x0, y0] = punto(r, a0), [x1, y1] = punto(r, a1);
    return `M${x0.toFixed(2)} ${y0.toFixed(2)} A${r} ${r} 0 ${a1 - a0 > 180 ? 1 : 0} 1 ${x1.toFixed(2)} ${y1.toFixed(2)}`;
  }

  // R = radio total. Devuelve el <g> raíz centrado en (0,0).
  window.dibujarNucleo = function (svg, R, op = {}) {
    const C = op.color || "#00cbff";          // celeste holográfico
    const A = op.acento || "#fba905";         // acento dorado (detalles mínimos)
    const nombre = op.nombre || "YARBYS";
    const estado = op.estado || "EN LÍNEA";
    const brillo = op.brillo !== false;
    const raiz = el(svg, "g", { id: "nucleo" });
    if (brillo) {
      const f = el(svg, "defs", {});
      const filtro = el(f, "filter", { id: "brillo", x: "-30%", y: "-30%", width: "160%", height: "160%" });
      el(filtro, "feGaussianBlur", { stdDeviation: R * 0.012, result: "b" });
      const m = el(filtro, "feMerge", {});
      el(m, "feMergeNode", { in: "b" });
      el(m, "feMergeNode", { in: "SourceGraphic" });
      raiz.setAttribute("filter", "url(#brillo)");
    }
    const g = (id) => el(raiz, "g", { id });

    // 1. anillo exterior fino + marcas de medición
    const g1 = g("anillo-marcas");
    el(g1, "circle", { r: R, fill: "none", stroke: C, "stroke-opacity": 0.35, "stroke-width": R * 0.006 });
    for (let i = 0; i < 120; i++) {
      const largo = i % 10 === 0 ? 0.06 : i % 5 === 0 ? 0.04 : 0.022;
      const [x0, y0] = punto(R * 0.975, i * 3), [x1, y1] = punto(R * (0.975 - largo), i * 3);
      el(g1, "line", { x1: x0, y1: y0, x2: x1, y2: y1, stroke: C, "stroke-opacity": i % 10 === 0 ? 0.95 : 0.55, "stroke-width": R * (i % 10 === 0 ? 0.008 : 0.005) });
    }
    // grados
    [["000", 0], ["090", 90], ["180", 180], ["270", 270]].forEach(([t, a]) => {
      const [x, y] = punto(R * 1.07, a);
      const e = el(raiz, "text", { x, y: y + R * 0.017, fill: C, "fill-opacity": 0.8, "font-family": "JetBrains Mono", "font-size": R * 0.05, "text-anchor": "middle" });
      e.textContent = t;
    });

    // 2. anillo segmentado grueso (bloques como en la película)
    const g2 = g("anillo-segmentos");
    const segmentos = [[4, 52], [56, 60], [64, 118], [124, 128], [132, 196], [202, 206], [210, 262], [268, 272], [276, 356]];
    segmentos.forEach(([a0, a1], i) => el(g2, "path", { d: arco(R * 0.86, a0, a1), fill: "none", stroke: i % 2 ? C : C,
      "stroke-opacity": i % 2 ? 1 : 0.85, "stroke-width": R * 0.05 }));
    [[96, 100], [300, 304]].forEach(([a0, a1]) => el(g2, "path", { d: arco(R * 0.86, a0, a1), fill: "none", stroke: A, "stroke-width": R * 0.05 }));

    // 3. anillo punteado fino
    const g3 = g("anillo-puntos");
    el(g3, "circle", { r: R * 0.795, fill: "none", stroke: C, "stroke-opacity": 0.7, "stroke-width": R * 0.006, "stroke-dasharray": `${R * 0.006} ${R * 0.03}` });

    // 4. barras radiales tipo espectro (el "ecualizador" circular de JARVIS)
    const g4 = g("anillo-espectro");
    let s = 3;
    const azar = () => (s = (s * 16807) % 2147483647) / 2147483647;
    for (let i = 0; i < 90; i++) {
      const a = i * 4, h = 0.025 + Math.pow(azar(), 1.6) * 0.075;
      const [x0, y0] = punto(R * 0.70, a), [x1, y1] = punto(R * (0.70 + h), a);
      el(g4, "line", { x1: x0, y1: y0, x2: x1, y2: y1, stroke: C, "stroke-opacity": 0.85, "stroke-width": R * 0.016 });
    }

    // 5. arcos con remates (dos arcos opuestos)
    const g5 = g("anillo-arcos");
    [[20, 150], [200, 330]].forEach(([a0, a1]) => {
      el(g5, "path", { d: arco(R * 0.62, a0, a1), fill: "none", stroke: C, "stroke-width": R * 0.012 });
      [a0, a1].forEach((a) => {
        const [x0, y0] = punto(R * 0.585, a), [x1, y1] = punto(R * 0.655, a);
        el(g5, "line", { x1: x0, y1: y0, x2: x1, y2: y1, stroke: C, "stroke-width": R * 0.012 });
      });
    });
    [85, 265].forEach((a) => {
      const [x, y] = punto(R * 0.62, a);
      el(g5, "circle", { cx: x, cy: y, r: R * 0.018, fill: A });
    });

    // 6. media luna gruesa y tenue
    const g6 = g("anillo-luna");
    el(g6, "path", { d: arco(R * 0.53, 210, 500), fill: "none", stroke: C, "stroke-opacity": 0.35, "stroke-width": R * 0.06 });

    // 7. anillo interior con muescas en cruz
    const g7 = g("anillo-interior");
    el(g7, "circle", { r: R * 0.45, fill: "none", stroke: C, "stroke-opacity": 0.9, "stroke-width": R * 0.008 });
    [0, 90, 180, 270].forEach((a) => {
      const [x0, y0] = punto(R * 0.41, a), [x1, y1] = punto(R * 0.49, a);
      el(g7, "line", { x1: x0, y1: y0, x2: x1, y2: y1, stroke: C, "stroke-width": R * 0.014 });
    });
    for (let i = 0; i < 36; i++) {
      const [x0, y0] = punto(R * 0.425, i * 10 + 5), [x1, y1] = punto(R * 0.44, i * 10 + 5);
      el(g7, "line", { x1: x0, y1: y0, x2: x1, y2: y1, stroke: C, "stroke-opacity": 0.6, "stroke-width": R * 0.005 });
    }

    // 8. centro: nombre y estado
    el(raiz, "circle", { r: R * 0.38, fill: "#06131a", "fill-opacity": 0.85 });
    const t = el(raiz, "text", { x: 0, y: R * 0.03, fill: "#e9fbff", "font-family": "Open Sans", "font-weight": 800,
      "font-size": R * 0.13, "letter-spacing": R * 0.02, "text-anchor": "middle" });
    t.textContent = nombre;
    const e2 = el(raiz, "text", { x: 0, y: R * 0.14, fill: C, "font-family": "JetBrains Mono", "font-weight": 700,
      "font-size": R * 0.048, "letter-spacing": R * 0.012, "text-anchor": "middle" });
    e2.textContent = estado;
    el(raiz, "line", { x1: -R * 0.2, y1: -R * 0.1, x2: R * 0.2, y2: -R * 0.1, stroke: C, "stroke-opacity": 0.6, "stroke-width": R * 0.005 });
    return raiz;
  };
})();
