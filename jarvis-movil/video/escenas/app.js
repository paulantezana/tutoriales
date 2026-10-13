/* Réplica de la app YARBYS (misma interfaz que lib/pantallas) manejada por eventos
   en tiempo virtual. render.py escribe los eventos en _demos/<id>.js y llama a seek(t)
   en cada fotograma, igual que con las escenas animadas. */
const P = new URLSearchParams(location.search);
const ID = P.get("id");
const W_S = 468, H_S = 968;
const C = { azul: "#007bdf", celeste: "#00cbff", rojo: "#ff3c32", amarillo: "#fba905", verde: "#4ade80",
            sup: "#1f272e", borde: "#2c3a45", suave: "#8a9aa8", fondo: "#0f1418" };
const I = (n, tam = 24, color = "currentColor") => `<span class="i" style="width:${tam}px;height:${tam}px;color:${color}">${ICONOS[n] || ""}</span>`;
const ease = (x) => 1 - Math.pow(1 - Math.max(0, Math.min(1, x)), 3);
let EV = [];

// ------------------------------------------------------------------ estado
function estadoEn(t) {
  const s = {
    pantalla: "chat", anterior: null, pantallaT0: -99, dir: 1, avion: false, sombra: false, sombraT0: -99,
    estado: "reposo", campo: "", msgs: [], msgsT0: -99, drawer: false, drawerT0: -99, hilos: [], hiloActivo: 0,
    docs: [], aprendiendo: null, picker: false, pickerT0: -99, pickerSel: [], snack: null, snackT0: -99, snackDur: 2.8,
    nube: false, proveedor: "openai", modelo: "gpt-6-luna", clave: 0, hablar: true,
    prog: { emb: 0, gemma: 0 }, descargando: false, toque: null, toqueT0: -99,
    notas: [], kicker: ["smartphone", ""], titulo: "",
  };
  const conMsgs = () => s.msgs.length > 0;
  for (const ev of EV) {
    const [te, tipo, ...a] = ev;
    if (te > t) break;
    const antes = conMsgs();
    switch (tipo) {
      case "pantalla": s.anterior = s.pantalla; s.pantalla = a[0]; s.dir = a[1] || 1; s.pantallaT0 = te; break;
      case "estado": s.estado = a[0]; break;
      case "campo": s.campo = a[0]; break;
      case "msg": s.msgs.push({ rol: a[0], texto: a[1], fuentes: a[2] || [], t0: te }); break;
      case "pendiente": s.msgs.push({ rol: "y", texto: "", fuentes: a[0] || [], t0: te, pendiente: true }); break;
      case "stream": {
        const [texto, dur, fuentes] = a;
        const k = Math.min(1, (t - te) / dur);
        let n = Math.round(texto.length * k);
        if (n < texto.length) { const sp = texto.indexOf(" ", n); n = sp < 0 ? texto.length : sp; }
        const ult = s.msgs[s.msgs.length - 1];
        const m = { rol: "y", texto: texto.slice(0, n), fuentes: fuentes || [], t0: ult && ult.pendiente ? ult.t0 : te, pendiente: n === 0 };
        if (ult && ult.pendiente) s.msgs[s.msgs.length - 1] = m; else s.msgs.push(m);
        break;
      }
      case "limpiar_chat": s.msgs = []; break;
      case "cargar_chat": s.msgs = a[0].map(([rol, texto, fuentes]) => ({ rol, texto, fuentes: fuentes || [], t0: -99 })); break;
      case "drawer": s.drawer = a[0]; s.drawerT0 = te; break;
      case "hilos": s.hilos = a[0]; s.hiloActivo = a[1] ?? -1; break;
      case "docs": s.docs = a[0]; break;
      case "aprendiendo": s.aprendiendo = a[0]; break;
      case "picker": s.picker = a[0]; s.pickerT0 = te; if (a[0]) s.pickerSel = []; break;
      case "picker_sel": s.pickerSel = a[0]; break;
      case "snack": s.snack = a[0]; s.snackT0 = te; s.snackDur = a[1] || 2.8; break;
      case "sombra": s.sombra = a[0]; s.sombraT0 = te; break;
      case "avion": s.avion = a[0]; break;
      case "nube": s.nube = a[0]; break;
      case "proveedor": s.proveedor = a[0]; s.modelo = a[1]; break;
      case "clave": s.clave = a[0]; break;
      case "progreso": {
        const [cual, desde, hasta, dur] = a;
        s.prog[cual] = desde + (hasta - desde) * Math.min(1, Math.max(0, (t - te) / dur));
        break;
      }
      case "descargando": s.descargando = a[0]; break;
      case "toque": s.toque = [a[0], a[1]]; s.toqueT0 = te; break;
      case "titulo": s.kicker = a[0]; s.titulo = a[1]; break;
      case "nota": s.notas.push({ icono: a[0], texto: a[1], color: a[2] || C.celeste, t0: te }); break;
      case "notas_limpiar": s.notas = []; break;
    }
    if (antes !== conMsgs()) s.msgsT0 = te;
  }
  return s;
}

// Giro acumulado del núcleo: cada estado gira a otra velocidad (igual que en Dart)
const VEL = { reposo: 1.0, escuchando: 1.8, pensando: 4.0, hablando: 1.4 };
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
let BARRAS = (() => {
  let s = 3; const azar = () => (s = (s * 16807) % 2147483647) / 2147483647;
  return Array.from({ length: 90 }, () => 0.025 + Math.pow(azar(), 1.6) * 0.075);
})();
function pintarNucleo(ctx, S, t, giro, estado) {
  const c = C.celeste, a = C.amarillo;
  ctx.clearRect(0, 0, S, S);
  ctx.save();
  ctx.translate(S / 2, S / 2);
  const r = S / 2 / 1.14;
  const rad = (gr) => ((gr - 90) * Math.PI) / 180;
  const punto = (rr, gr) => [rr * Math.cos(rad(gr)), rr * Math.sin(rad(gr))];
  const linea = (p0, p1, color, ancho, op = 1) => { ctx.globalAlpha = op; ctx.strokeStyle = color; ctx.lineWidth = ancho; ctx.beginPath(); ctx.moveTo(...p0); ctx.lineTo(...p1); ctx.stroke(); ctx.globalAlpha = 1; };
  const arco = (rr, a0, a1, color, ancho, op = 1) => { ctx.globalAlpha = op; ctx.strokeStyle = color; ctx.lineWidth = ancho; ctx.beginPath(); ctx.arc(0, 0, rr, rad(a0), rad(a1)); ctx.stroke(); ctx.globalAlpha = 1; };
  const girado = (gr, f) => { ctx.save(); ctx.rotate((gr * Math.PI) / 180); f(); ctx.restore(); };
  const texto = (txt, x, y, fuente, color, esp = 0) => { ctx.font = fuente; ctx.fillStyle = color; ctx.letterSpacing = `${esp}px`; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(txt, x, y); ctx.letterSpacing = "0px"; };
  const g = giro;
  const activo = estado !== "reposo";
  const pulso = 0.5 + 0.5 * Math.sin(t * (activo ? 6 : 2));
  // halo
  ctx.save();
  ctx.shadowColor = c; ctx.shadowBlur = r * 0.3;
  ctx.fillStyle = `rgba(0,203,255,${0.08 + (activo ? 0.10 : 0.04) * pulso})`;
  ctx.beginPath(); ctx.arc(0, 0, r * 0.5, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
  ctx.lineCap = "butt";
  // 1. marcas
  girado(g * 2, () => {
    ctx.globalAlpha = 0.35; ctx.strokeStyle = c; ctx.lineWidth = r * 0.006; ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.stroke(); ctx.globalAlpha = 1;
    for (let i = 0; i < 120; i++) {
      const largo = i % 10 === 0 ? 0.06 : i % 5 === 0 ? 0.04 : 0.022;
      linea(punto(r * 0.975, i * 3), punto(r * (0.975 - largo), i * 3), c, r * (i % 10 === 0 ? 0.008 : 0.005), i % 10 === 0 ? 0.95 : 0.55);
    }
  });
  [["000", 0], ["090", 90], ["180", 180], ["270", 270]].forEach(([tx, an]) => {
    const [x, y] = punto(r * 1.08, an);
    texto(tx, x, y, `400 ${r * 0.05}px 'JetBrains Mono'`, "rgba(0,203,255,.8)");
  });
  // 2. bloques
  girado(-g * 6, () => {
    [[4, 52], [56, 60], [64, 118], [124, 128], [132, 196], [202, 206], [210, 262], [268, 272], [276, 356]]
      .forEach(([a0, a1], i) => arco(r * 0.86, a0, a1, c, r * 0.05, i % 2 ? 1 : 0.85));
    [[96, 100], [300, 304]].forEach(([a0, a1]) => arco(r * 0.86, a0, a1, a, r * 0.05));
  });
  // 3. puntos
  girado(g * 10, () => {
    ctx.fillStyle = "rgba(0,203,255,.7)";
    for (let i = 0; i < 160; i++) { const [x, y] = punto(r * 0.795, i * 2.25); ctx.beginPath(); ctx.arc(x, y, r * 0.004, 0, Math.PI * 2); ctx.fill(); }
  });
  // 4. ecualizador
  girado(g * 1.5, () => {
    for (let i = 0; i < 90; i++) {
      let h = BARRAS[i];
      if (estado === "escuchando" || estado === "hablando") {
        h *= 0.6 + 1.4 * (0.5 + 0.5 * Math.sin(t * 9 + i * 0.9)) * (0.5 + 0.5 * Math.sin(t * 3.7 + i * 0.31));
      }
      linea(punto(r * 0.7, i * 4), punto(r * (0.7 + h), i * 4), c, r * 0.016, 0.85);
    }
  });
  // 5. arcos con remates
  girado(-g * 12, () => {
    [[20, 150], [200, 330]].forEach(([a0, a1]) => {
      arco(r * 0.62, a0, a1, c, r * 0.012);
      [a0, a1].forEach((an) => linea(punto(r * 0.585, an), punto(r * 0.655, an), c, r * 0.012));
    });
    ctx.fillStyle = a;
    [85, 265].forEach((an) => { const [x, y] = punto(r * 0.62, an); ctx.beginPath(); ctx.arc(x, y, r * 0.018, 0, Math.PI * 2); ctx.fill(); });
  });
  // 6. media luna
  girado(g * 20, () => arco(r * 0.53, 210, 500, c, r * 0.06, 0.35));
  // 7. interior
  girado(-g * 4, () => {
    ctx.globalAlpha = 0.9; ctx.strokeStyle = c; ctx.lineWidth = r * 0.008; ctx.beginPath(); ctx.arc(0, 0, r * 0.45, 0, Math.PI * 2); ctx.stroke(); ctx.globalAlpha = 1;
    [0, 90, 180, 270].forEach((an) => linea(punto(r * 0.41, an), punto(r * 0.49, an), c, r * 0.014));
    for (let i = 0; i < 36; i++) linea(punto(r * 0.425, i * 10 + 5), punto(r * 0.44, i * 10 + 5), c, r * 0.005, 0.6);
  });
  // 8. centro
  ctx.fillStyle = "rgba(6,19,26,.85)"; ctx.beginPath(); ctx.arc(0, 0, r * 0.38, 0, Math.PI * 2); ctx.fill();
  linea([-r * 0.2, -r * 0.1], [r * 0.2, -r * 0.1], c, r * 0.005, 0.6);
  texto("YARBYS", 0, -r * 0.01, `800 ${r * 0.13}px 'Open Sans'`, "#e9fbff", r * 0.02);
  const et = { reposo: "EN LÍNEA", escuchando: "ESCUCHANDO", pensando: "PENSANDO", hablando: "HABLANDO" }[estado];
  texto(et, 0, r * 0.13, `700 ${r * 0.048}px 'JetBrains Mono'`, estado === "pensando" ? a : c, r * 0.012);
  ctx.restore();
}

// ------------------------------------------------------------------ pantallas (HTML)
function pildora(texto, color, icono) {
  const rgb = color === C.verde ? "74,222,128" : "251,169,5";
  return `<span class="pildora" style="background:rgba(${rgb},.16);color:${color}">${I(icono, 16)}${texto}</span>`;
}
function barraApp(s) {
  return `<div class="barra">${I("menu", 28, "#e8eef3")}<span class="tit">YARBYS</span>
    ${s.nube ? pildora("Nube", C.amarillo, "cloud") : pildora("Sin internet", C.verde, "plane")}
    <span class="btn-i">${I("file-text", 25)}</span><span class="btn-i">${I("sliders-horizontal", 25)}</span></div>`;
}
function barraAtras(titulo) {
  return `<div class="barra">${I("arrow-left", 28, "#e8eef3")}<span class="tit2">${titulo}</span></div>`;
}
function geomChat(s, t) {
  const k = ease((t - s.msgsT0) / 0.4);
  const con = s.msgs.length > 0;
  const h = con ? 300 + (170 - 300) * k : 170 + (300 - 170) * k;
  return { h, top: 118 };
}
function htmlChat(s, t) {
  const { h, top } = geomChat(s, t);
  const etiquetaY = top + h + 2;
  const listaTop = etiquetaY + 26, listaBot = H_S - 22 - 60 - 8;
  const msgs = s.msgs.map((m) => {
    const k = ease((t - m.t0) / 0.3);
    const cuerpo = m.pendiente ? `<div class="spin" style="transform:rotate(${t * 400}deg)"></div>` : m.texto;
    const fuentes = m.fuentes.map((f) => `<div class="fuente">${I("file-text", 15)}${f}</div>`).join("");
    return `<div class="msg ${m.rol === "u" ? "u" : "y"}" style="opacity:${k};transform:translateY(${(1 - k) * 16}px)">${cuerpo}${fuentes}</div>`;
  }).join("");
  const escuchando = s.estado === "escuchando";
  const escribiendo = s.campo.trim() && !escuchando;
  const ocupado = s.estado === "pensando";
  return `${barraApp(s)}
    <div id="etiqueta-modelo" style="top:${etiquetaY}px">${s.nube ? s.modelo.toUpperCase() : "GEMMA 4 · LOCAL"}</div>
    ${s.msgs.length ? `<div id="lista" style="top:${listaTop}px;height:${listaBot - listaTop}px"><div id="lista-int">${msgs}</div></div>`
      : `<div id="vacio" style="top:${listaTop + 120}px">Pregúntame algo o toca el micrófono.<br>Agrega tus documentos para que te conozca mejor.</div>`}
    <div id="entrada"><div id="campo" class="${s.campo ? "" : "vacio"}" style="opacity:${ocupado ? 0.5 : 1}">${s.campo || "Habla con YARBYS..."}</div>
      <div id="boton" style="background:${escuchando ? C.rojo : C.azul};opacity:${ocupado ? 0.45 : 1}">${I(escribiendo ? "send" : "mic", 27, "#fff")}</div></div>`;
}
function tarjetaDescarga(icono, titulo, detalle, p) {
  const listo = p >= 100;
  return `<div class="tarjeta-d" style="margin-top:12px"><div style="display:flex;align-items:center;gap:14px">${I(icono, 26, C.celeste)}
    <div style="flex:1"><div style="font:700 18px Lato">${titulo}</div><div style="font:400 16px Lato;color:${C.suave}">${detalle}</div></div>
    <span style="font:700 17px Lato;color:${listo ? C.verde : C.celeste}">${listo ? "Listo" : Math.floor(p) + "%"}</span></div>
    <div class="barra-p"><span style="width:${p}%;background:${listo ? C.verde : C.celeste}"></span></div></div>`;
}
function htmlInicio(s) {
  return `<div style="position:absolute;left:24px;right:24px;top:350px">
    <div style="font:800 31px 'Open Sans'">Hola, soy YARBYS</div>
    <div style="font:400 18px/1.45 Lato;color:${C.suave};margin-top:8px">Para funcionar sin internet necesito descargar mi cerebro una sola vez. Usa Wi-Fi: son unos 2.8 GB.</div>
    <div style="margin-top:14px">${tarjetaDescarga("network", "EmbeddingGemma 2", "Convierte texto en vectores · 165 MB", s.prog.emb)}
    ${tarjetaDescarga("brain", "Gemma 4 E2B", "El cerebro (LLM) · 2.6 GB", s.prog.gemma)}</div>
    <div class="boton-g" style="margin-top:22px;background:${s.descargando ? C.borde : C.azul};color:${s.descargando ? C.suave : "#fff"}">${I("download", 24)}${s.descargando ? "Descargando..." : "Descargar modelos"}</div></div>`;
}
function htmlDocumentos(s, t) {
  const docs = s.docs.map(([n, k]) => `<div class="doc">${I("file-text", 26, C.amarillo)}<div style="flex:1"><div style="font:700 18px Lato">${n}</div><div style="font:400 15px Lato;color:${C.suave}">${k} ${k === 1 ? "fragmento" : "fragmentos"}</div></div>${I("trash-2", 22, C.suave)}</div>`).join("");
  const aprendiendo = s.aprendiendo ? `<div class="doc"><div class="spin" style="transform:rotate(${t * 400}deg)"></div><div><div style="font:700 18px Lato">Aprendiendo ${s.aprendiendo}...</div><div style="font:400 15px Lato;color:${C.suave}">Creando los embeddings</div></div></div>` : "";
  const vacio = !s.docs.length && !s.aprendiendo ? `<div style="text-align:center;color:${C.suave};font:400 17px/1.5 Lato;margin-top:60px">Todavía no hay documentos.<br>Agrega tu agenda, notas o lo que quieras que YARBYS sepa.</div>` : "";
  return `${barraAtras("Mis documentos")}
    <div style="position:absolute;left:18px;right:18px;top:126px">
      <div style="font:400 17px/1.45 Lato;color:${C.suave}">YARBYS lee estos documentos, los convierte en vectores con EmbeddingGemma y los guarda en Qdrant, dentro de tu celular.</div>
      ${aprendiendo}${vacio}${docs}</div>
    <div class="fab" style="bottom:104px;background:${C.sup};border:1px solid ${C.borde}">${I("pencil", 22)}Escribir nota</div>
    <div class="fab" style="bottom:30px;background:${C.azul}">${I("upload", 22)}Agregar archivo</div>`;
}
function htmlAjustes(s) {
  const seg = (ops, sel) => `<div class="seg">${ops.map(([v, txt, ic]) => `<span class="${v === sel ? "on" : ""}">${v === sel ? I("check", 18) : ic ? I(ic, 18) : ""}${txt}</span>`).join("")}</div>`;
  const nube = s.nube ? `<div style="display:flex;align-items:center;gap:10px;margin-top:14px">${pildora("PRO", C.amarillo, "award")}<span style="color:${C.suave};font:400 16px Lato">Usa tu propia API key.</span></div>
      <div style="margin-top:12px">${seg([["openai", "OpenAI"], ["anthropic", "Anthropic"]], s.proveedor)}</div>
      <div class="campo-a"><small>Modelo</small><span style="font:400 18px Lato">${s.modelo}</span></div>
      <div class="campo-a"><small>API key</small><span style="font:400 18px Lato;letter-spacing:3px">${"•".repeat(s.clave)}</span></div>
      <div style="margin-top:12px;color:${C.amarillo};font:400 15px/1.4 Lato">Con un LLM externo, tu pregunta y los fragmentos encontrados se envían a ese proveedor. Tus documentos, tus vectores y tu memoria siguen guardados en el celular.</div>`
    : `<div style="margin-top:14px;color:${C.suave};font:400 16px/1.45 Lato">Gemma 4 responde dentro de tu celular. Nada sale del teléfono y funciona en modo avión.</div>`;
  return `${barraAtras("Ajustes")}
    <div style="position:absolute;left:18px;right:18px;top:132px">
      <div class="titulo-a">CEREBRO</div>${seg([[false, "En el celular", "smartphone"], [true, "LLM externo", "cloud"]], s.nube)}${nube}
      <div class="titulo-a" style="margin-top:30px">VOZ</div>
      <div style="display:flex;align-items:center;font:400 18px Lato">Leer las respuestas en voz alta<span style="margin-left:auto;width:56px;height:32px;border-radius:16px;background:${C.celeste};position:relative"><span style="position:absolute;right:4px;top:4px;width:24px;height:24px;border-radius:50%;background:#0f1418"></span></span></div>
    </div>`;
}
function htmlSplash() { return ""; }
const PANTALLAS = { chat: htmlChat, inicio: htmlInicio, documentos: htmlDocumentos, ajustes: htmlAjustes, splash: htmlSplash };

// Dónde va el núcleo en cada pantalla
function geomNucleo(nombre, s, t) {
  if (nombre === "chat") { const { h, top } = geomChat(s, t); return { size: h, cx: W_S / 2, cy: top + h / 2 }; }
  if (nombre === "inicio") return { size: 250, cx: W_S / 2, cy: 92 + 125 };
  if (nombre === "splash") return { size: 280, cx: W_S / 2, cy: H_S / 2 };
  return null;
}

// ------------------------------------------------------------------ overlays
function htmlOverlays(s, t) {
  let h = "";
  const kd = ease((t - s.drawerT0) / 0.3);
  const vis = s.drawer ? kd : 1 - kd;
  if (vis > 0.001) {
    const hilos = s.hilos.map((x, i) => `<div class="item-d" style="${i === s.hiloActivo ? `color:${C.celeste}` : ""}">${I("message-circle", 22)}<span style="flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${x}</span>${I("trash-2", 20, C.suave)}</div>`).join("");
    h += `<div id="drawer-fondo" style="opacity:${vis}"></div><div id="drawer" style="transform:translateX(${(vis - 1) * 360}px)">
      <div style="font:800 23px 'Open Sans';padding:0 22px 10px">Conversaciones</div>
      <div class="item-d">${I("plus", 24, C.celeste)}Nueva conversación</div><div style="height:1px;background:${C.borde};margin:4px 0"></div>${hilos}</div>`;
  }
  const kp = ease((t - s.pickerT0) / 0.3);
  const vp = s.picker ? kp : 1 - kp;
  if (vp > 0.001) {
    const archivos = [["agenda.txt", "2 KB"], ["perfil.txt", "1 KB"], ["receta_pan.txt", "3 KB"]];
    h += `<div id="picker-fondo" style="opacity:${vp}"></div><div id="picker" style="transform:translateY(${(1 - vp) * 470}px)">
      <div style="font:800 21px 'Open Sans'">Elige archivos</div><div style="font:400 15px Lato;color:${C.suave};margin:4px 0 10px">Descargas · .txt y .md</div>
      ${archivos.map(([n, k], i) => `<div class="archivo">${I(s.pickerSel.includes(i) ? "square-check" : "square", 26, s.pickerSel.includes(i) ? C.celeste : C.suave)}${I("file-text", 24, C.amarillo)}<span style="flex:1">${n}</span><span style="color:${C.suave};font-size:15px">${k}</span></div>`).join("")}
      <div class="boton-g" style="margin-top:22px;background:${s.pickerSel.length ? C.azul : C.borde}">Seleccionar (${s.pickerSel.length})</div></div>`;
  }
  const ks = ease((t - s.sombraT0) / 0.35);
  const vs = s.sombra ? ks : 1 - ks;
  if (vs > 0.001) {
    const tile = (ic, txt, sub, on) => `<span class="mosaico" style="background:${on ? C.celeste : "#2b3238"};color:${on ? "#08202a" : "#e8eef3"}">${I(ic, 24)}<span>${txt}</span><span style="font:400 14px Lato;opacity:.8">${sub}</span></span>`;
    h += `<div id="sombra" style="transform:translateY(${(vs - 1) * 420}px)">
      ${tile("wifi", "Wi-Fi", s.avion ? "Desactivado" : "Conectado", !s.avion)}${tile("signal", "Datos", s.avion ? "Desactivados" : "Activados", !s.avion)}
      ${tile("plane", "Modo avión", s.avion ? "Activado" : "Desactivado", s.avion)}${tile("flashlight", "Linterna", "Desactivada", false)}</div>`;
  }
  if (s.snack && t - s.snackT0 < s.snackDur) {
    const k = Math.min(ease((t - s.snackT0) / 0.25), 1 - ease((t - s.snackT0 - s.snackDur + 0.3) / 0.3));
    h += `<div id="snack" style="opacity:${k};transform:translateY(${(1 - k) * 20}px)">${s.snack}</div>`;
  }
  return h;
}

// ------------------------------------------------------------------ pintar
const capas = document.querySelector("#capas");
const over = document.querySelector("#overlays");
const canvas = document.querySelector("#canvas-nucleo");
const ctx = canvas.getContext("2d");
const toque = document.querySelector("#toque");
let notasPintadas = "";

function pintar(t) {
  const s = estadoEn(t);
  document.querySelector("#iconos-estado").innerHTML =
    (s.avion ? I("plane", 20) : I("signal", 19) + I("wifi", 20)) + I("battery-full", 24);
  // transición entre pantallas
  const k = ease((t - s.pantallaT0) / 0.35);
  const enTransicion = s.anterior && k < 1 && s.anterior !== s.pantalla;
  let html = "";
  let offAct = 0, offAnt = 0;
  if (enTransicion) {
    if (s.dir > 0) { offAct = (1 - k) * W_S; offAnt = -k * W_S * 0.3; }
    else { offAct = -(1 - k) * W_S * 0.3; offAnt = k * W_S; }
    const capaAnt = `<div class="capa" style="transform:translateX(${offAnt}px);z-index:${s.dir > 0 ? 1 : 3}">${PANTALLAS[s.anterior](s, t)}</div>`;
    const capaAct = `<div class="capa" style="transform:translateX(${offAct}px);z-index:${s.dir > 0 ? 3 : 1}">${PANTALLAS[s.pantalla](s, t)}</div>`;
    html = capaAnt + capaAct;
  } else {
    html = `<div class="capa">${PANTALLAS[s.pantalla](s, t)}</div>`;
  }
  capas.innerHTML = html;
  // la lista de mensajes siempre muestra el final
  capas.querySelectorAll("#lista").forEach((l) => {
    const int = l.firstElementChild;
    const exceso = int.offsetHeight - l.offsetHeight;
    if (exceso > 0) int.style.transform = `translateY(${-exceso}px)`;
  });
  // núcleo (canvas encima de la pantalla que lo contiene)
  let geo = null, off = 0;
  const geoAct = geomNucleo(s.pantalla, s, t);
  if (enTransicion) {
    const geoAnt = geomNucleo(s.anterior, s, t);
    // se dibuja el de la pantalla que está arriba en la transición, o el que exista
    if (geoAct && (s.dir > 0 || !geoAnt)) { geo = geoAct; off = offAct; }
    else if (geoAnt) { geo = geoAnt; off = offAnt; }
  } else { geo = geoAct; }
  if (geo) {
    canvas.style.display = "block";
    pintarNucleo(ctx, 600, t, giroEn(t), s.estado);
    const esc = geo.size / 600;
    canvas.style.transform = `translate(${geo.cx - geo.size / 2 + off}px, ${geo.cy - geo.size / 2}px) scale(${esc})`;
    // si su pantalla está debajo durante la transición, el núcleo también va debajo
    const deAbajo = enTransicion && ((s.dir > 0 && geo !== geoAct) || (s.dir < 0 && geo === geoAct));
    canvas.style.zIndex = deAbajo ? 2 : 4;
  } else canvas.style.display = "none";
  capas.style.position = "absolute"; capas.style.inset = "0";
  over.innerHTML = htmlOverlays(s, t);
  over.style.position = "absolute"; over.style.inset = "0"; over.style.zIndex = 10;
  // toque del dedo
  const kt = (t - s.toqueT0) / 0.45;
  if (s.toque && kt >= 0 && kt < 1) {
    toque.style.display = "block";
    toque.style.left = s.toque[0] + "px"; toque.style.top = s.toque[1] + "px";
    toque.style.opacity = 1 - kt; toque.style.transform = `scale(${0.6 + kt * 0.7})`;
  } else toque.style.display = "none";
  // panel derecho
  document.querySelector("#kicker").innerHTML = `${I(s.kicker[0], 24)}${s.kicker[1]}`;
  document.querySelector("#titulo").innerHTML = s.titulo;
  const notas = s.notas.map((n, i) => {
    const kn = ease((t - n.t0) / 0.5);
    return `<div class="nota" style="opacity:${kn};transform:translateY(${(1 - kn) * 30}px)"><span class="cuadro" style="background:${n.color}26;color:${n.color}">${I(n.icono, 36)}</span><span>${n.texto}</span></div>`;
  }).join("");
  document.querySelector("#notas").innerHTML = notas;
}

window.seek = (t) => { pintar(t); return 0; };
const sc = document.createElement("script");
sc.src = `_demos/${ID}.js?v=${P.get("v") || 0}`;
sc.onload = () => {
  EV = (window.DEMO.eventos || []).slice().sort((a, b) => a[0] - b[0]);
  document.fonts.ready.then(() => { pintar(0); window.__listo = true; });
};
document.body.appendChild(sc);
