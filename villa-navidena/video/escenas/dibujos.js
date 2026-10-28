/* Dibujos sencillos (SVG) de herramientas y materiales. Cada función devuelve el
   SVG como texto, en una caja de 96 x 96. */

const SV = (inner, vb = "0 0 96 96") => `<svg viewBox="${vb}" xmlns="http://www.w3.org/2000/svg">${inner}</svg>`;
const CONTORNO = 'stroke="#0d1424" stroke-width="2" stroke-linejoin="round"';

function bloque3d(x, y, w, h, p, frente, arriba, lado) {
  // caja en perspectiva: frente w x h, profundidad p hacia arriba-derecha
  return `<path d="M${x},${y} L${x + p},${y - p * 0.6} L${x + w + p},${y - p * 0.6} L${x + w},${y} Z" fill="${arriba}" ${CONTORNO}/>
    <path d="M${x + w},${y} L${x + w + p},${y - p * 0.6} L${x + w + p},${y + h - p * 0.6} L${x + w},${y + h} Z" fill="${lado}" ${CONTORNO}/>
    <rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${frente}" ${CONTORNO}/>`;
}

const DIB = {
  // ---------------------------------------------------------- herramientas
  cuter: () => SV(`<g transform="rotate(-32 48 48)"><rect x="8" y="38" width="58" height="22" rx="7" fill="#f2c230" ${CONTORNO}/>
      <rect x="16" y="45" width="30" height="8" rx="3" fill="#30343d"/><circle cx="54" cy="49" r="4" fill="#30343d"/>
      <path d="M66,42 L92,45 L92,53 L66,56 Z" fill="#dfe5ef" stroke="#7d8799" stroke-width="1.5"/>
      <line x1="74" y1="43" x2="74" y2="55" stroke="#7d8799" stroke-width="1.5"/><line x1="82" y1="44" x2="82" y2="54" stroke="#7d8799" stroke-width="1.5"/></g>`),
  bisturi: () => SV(`<g transform="rotate(-38 48 48)"><rect x="6" y="44" width="56" height="10" rx="5" fill="#9aa4b8" ${CONTORNO}/>
      <rect x="10" y="46" width="34" height="6" rx="3" fill="#6d7891"/><path d="M62,44 L72,44 L92,50 L72,54 L62,54 Z" fill="#e8edf5" stroke="#7d8799" stroke-width="1.5"/></g>`),
  regla: () => SV(`<g transform="rotate(-30 48 48)"><rect x="2" y="38" width="92" height="20" rx="3" fill="#cfd6e2" ${CONTORNO}/>
      ${Array.from({ length: 11 }, (_, i) => `<line x1="${8 + i * 8}" y1="38" x2="${8 + i * 8}" y2="${i % 5 === 0 ? 50 : 45}" stroke="#4a5368" stroke-width="1.5"/>`).join("")}</g>`),
  escuadra: () => SV(`<path d="M12,86 L12,12 L86,86 Z" fill="rgba(140,200,255,.35)" stroke="#9fd0ff" stroke-width="3" stroke-linejoin="round"/>
      <path d="M26,72 L26,46 L52,72 Z" fill="#0b1528" stroke="#9fd0ff" stroke-width="2"/>
      ${Array.from({ length: 7 }, (_, i) => `<line x1="12" y1="${20 + i * 10}" x2="18" y2="${20 + i * 10}" stroke="#9fd0ff" stroke-width="1.5"/>`).join("")}`),
  compas: () => SV(`<circle cx="48" cy="14" r="7" fill="#cfd6e2" ${CONTORNO}/><rect x="45" y="2" width="6" height="8" rx="2" fill="#9aa4b8"/>
      <path d="M44,20 L22,84" stroke="#cfd6e2" stroke-width="6" stroke-linecap="round"/><path d="M52,20 L72,76" stroke="#cfd6e2" stroke-width="6" stroke-linecap="round"/>
      <path d="M72,76 L76,90" stroke="#30343d" stroke-width="4" stroke-linecap="round"/><path d="M22,84 L20,92" stroke="#7d8799" stroke-width="3" stroke-linecap="round"/>
      <path d="M33,52 L62,52" stroke="#9aa4b8" stroke-width="3"/>`),
  basecorte: () => SV(`<rect x="6" y="18" width="84" height="60" rx="6" fill="#2f8a5b" ${CONTORNO}/>
      ${Array.from({ length: 9 }, (_, i) => `<line x1="${14 + i * 9}" y1="22" x2="${14 + i * 9}" y2="74" stroke="#7fd3a6" stroke-width="1" opacity=".7"/>`).join("")}
      ${Array.from({ length: 6 }, (_, i) => `<line x1="10" y1="${26 + i * 9}" x2="86" y2="${26 + i * 9}" stroke="#7fd3a6" stroke-width="1" opacity=".7"/>`).join("")}`),
  pistola: () => SV(`<path d="M14,30 L70,30 Q80,30 80,40 L80,46 L14,46 Z" fill="#3b82f6" ${CONTORNO}/>
      <path d="M80,36 L92,38 L92,42 L80,44 Z" fill="#cfd6e2" ${CONTORNO}/><path d="M30,46 L46,46 L40,86 L24,86 Z" fill="#2563eb" ${CONTORNO}/>
      <path d="M48,46 Q56,58 48,66" fill="none" stroke="#cfd6e2" stroke-width="4" stroke-linecap="round"/>
      <rect x="2" y="34" width="14" height="8" rx="3" fill="rgba(230,240,255,.8)" stroke="#9fb3d1" stroke-width="1.5"/>`),
  cautin: () => SV(`<g transform="rotate(-30 48 48)"><rect x="6" y="40" width="40" height="16" rx="8" fill="#ef4444" ${CONTORNO}/>
      <rect x="44" y="43" width="12" height="10" rx="2" fill="#30343d"/><rect x="56" y="45" width="26" height="6" fill="#cfd6e2" stroke="#7d8799" stroke-width="1"/>
      <path d="M82,45 L94,48 L82,51 Z" fill="#9aa4b8"/><path d="M6,48 Q-6,48 -4,70" fill="none" stroke="#30343d" stroke-width="4"/></g>
      <path d="M58,22 Q64,14 58,8 M68,24 Q74,16 68,10" fill="none" stroke="#fcb333" stroke-width="2.5" stroke-linecap="round" opacity=".8"/>`),
  multimetro: () => SV(`<rect x="16" y="6" width="52" height="84" rx="10" fill="#f2c230" ${CONTORNO}/><rect x="22" y="12" width="40" height="76" rx="6" fill="#30343d"/>
      <rect x="27" y="17" width="30" height="16" rx="3" fill="#9fe0b3"/><text x="42" y="30" text-anchor="middle" font-family="JetBrains Mono" font-size="11" fill="#0b2a17" font-weight="700">5.02</text>
      <circle cx="42" cy="55" r="12" fill="#4b5263" stroke="#9aa4b8" stroke-width="2"/><line x1="42" y1="55" x2="50" y2="47" stroke="#fff" stroke-width="3" stroke-linecap="round"/>
      <circle cx="32" cy="79" r="3.5" fill="#ef4444"/><circle cx="52" cy="79" r="3.5" fill="#111"/>
      <path d="M32,82 Q30,94 80,92 L88,70" fill="none" stroke="#ef4444" stroke-width="3"/><path d="M52,82 Q58,96 90,86" fill="none" stroke="#9aa4b8" stroke-width="3"/>`),
  pelacables: () => SV(`<path d="M20,90 L40,52 L48,52 L34,90 Z" fill="#ef4444" ${CONTORNO}/><path d="M76,90 L56,52 L48,52 L62,90 Z" fill="#ef4444" ${CONTORNO}/>
      <path d="M40,52 L36,10 L48,10 L48,52 Z" fill="#9aa4b8" ${CONTORNO}/><path d="M56,52 L60,10 L48,10 L48,52 Z" fill="#b8c0cf" ${CONTORNO}/>
      <circle cx="48" cy="22" r="2.5" fill="#0d1424"/><circle cx="48" cy="31" r="2" fill="#0d1424"/><circle cx="48" cy="39" r="1.5" fill="#0d1424"/>`),
  alicate: () => SV(`<path d="M22,90 L42,50 L50,52 L34,90 Z" fill="#f2c230" ${CONTORNO}/><path d="M74,90 L54,50 L46,52 L62,90 Z" fill="#f2c230" ${CONTORNO}/>
      <path d="M42,50 Q34,26 46,10 L50,10 Q46,30 50,52 Z" fill="#9aa4b8" ${CONTORNO}/><path d="M54,50 Q62,26 50,10 L46,10 Q50,30 46,52 Z" fill="#b8c0cf" ${CONTORNO}/>
      <circle cx="48" cy="48" r="4" fill="#30343d"/>`),
  termo: () => SV(`<rect x="10" y="20" width="76" height="12" rx="6" fill="#111827" stroke="#4b5563" stroke-width="2"/>
      <rect x="10" y="42" width="76" height="12" rx="6" fill="#dc2626" stroke="#7f1d1d" stroke-width="2"/>
      <rect x="10" y="64" width="76" height="12" rx="6" fill="#2563eb" stroke="#1e3a8a" stroke-width="2"/>`),
  taladro: () => SV(`<g transform="rotate(-25 48 48)"><rect x="6" y="38" width="58" height="20" rx="10" fill="#6366f1" ${CONTORNO}/>
      <rect x="20" y="42" width="20" height="12" rx="4" fill="#30343d"/><path d="M64,42 L76,44 L76,52 L64,54 Z" fill="#9aa4b8" ${CONTORNO}/>
      <rect x="76" y="46" width="18" height="4" fill="#cfd6e2"/><path d="M6,48 Q-4,50 -2,64" fill="none" stroke="#30343d" stroke-width="4"/></g>`),
  pinceles: () => SV(`<g transform="rotate(-30 48 48)"><rect x="4" y="34" width="54" height="8" rx="4" fill="#b45309" ${CONTORNO}/><rect x="58" y="33" width="12" height="10" fill="#cfd6e2"/>
      <path d="M70,32 Q92,38 70,44 Z" fill="#d6a86b"/><rect x="4" y="56" width="54" height="8" rx="4" fill="#dc2626" ${CONTORNO}/><rect x="58" y="55" width="12" height="10" fill="#cfd6e2"/>
      <path d="M70,54 L90,54 L90,66 L70,66 Z" fill="#c08e52"/></g>`),
  espatula: () => SV(`<g transform="rotate(-35 48 48)"><rect x="4" y="42" width="40" height="12" rx="6" fill="#7c4a2d" ${CONTORNO}/>
      <path d="M44,45 L60,45 L92,38 L92,58 L60,51 L44,51 Z" fill="#cfd6e2" stroke="#7d8799" stroke-width="1.5"/></g>`),
  esponja: () => SV(`<rect x="12" y="24" width="72" height="48" rx="12" fill="#facc15" ${CONTORNO}/>
      ${[[26, 38, 5], [44, 34, 3], [62, 40, 6], [34, 56, 4], [54, 58, 3], [70, 56, 4], [22, 60, 3]].map(([x, y, r]) => `<circle cx="${x}" cy="${y}" r="${r}" fill="#d4a40a"/>`).join("")}`),
  lija: () => SV(`<rect x="14" y="14" width="68" height="68" rx="4" fill="#a16207" ${CONTORNO} transform="rotate(-8 48 48)"/>
      ${Array.from({ length: 40 }, (_, i) => `<circle cx="${22 + (i * 37) % 54}" cy="${22 + (i * 23) % 54}" r="1.3" fill="#fde68a" opacity=".8"/>`).join("")}`),
  secadora: () => SV(`<path d="M10,30 L58,26 Q74,26 74,42 Q74,58 58,58 L10,54 Z" fill="#ec4899" ${CONTORNO}/><rect x="40" y="56" width="16" height="34" rx="6" fill="#db2777" ${CONTORNO}/>
      <circle cx="62" cy="42" r="8" fill="#30343d"/><path d="M4,34 L4,50" stroke="#cfd6e2" stroke-width="3"/>
      <path d="M-6,36 Q-12,42 -6,48" fill="none" stroke="#fcb333" stroke-width="2.5" opacity=".7"/>`),
  balanza: () => SV(`<rect x="10" y="40" width="76" height="40" rx="10" fill="#cfd6e2" ${CONTORNO}/><rect x="16" y="30" width="64" height="10" rx="4" fill="#9aa4b8" ${CONTORNO}/>
      <rect x="30" y="52" width="36" height="16" rx="3" fill="#30343d"/><text x="48" y="64" text-anchor="middle" font-family="JetBrains Mono" font-size="11" fill="#9fe0b3" font-weight="700">100g</text>`),
  vaso: () => SV(`<path d="M24,18 L72,18 L66,84 L30,84 Z" fill="rgba(220,235,255,.25)" stroke="#cfe0ff" stroke-width="3" stroke-linejoin="round"/>
      <path d="M28,48 L68,48 L66,84 L30,84 Z" fill="rgba(252,179,51,.45)"/>
      ${[30, 40, 50, 60, 70].map((y) => `<line x1="27" y1="${y}" x2="35" y2="${y}" stroke="#cfe0ff" stroke-width="1.5"/>`).join("")}`),

  // ---------------------------------------------------------- materiales de estructura
  mdf: () => SV(`${bloque3d(6, 44, 70, 10, 16, "#b07f4f", "#c99a66", "#8f6337")}
      ${[50, 56, 62].map((x) => `<path d="M${x - 30},${40} Q${x},${34} ${x + 26},${38}" stroke="#a5743f" stroke-width="1.2" fill="none"/>`).join("")}`),
  foam: () => SV(`${bloque3d(8, 40, 64, 30, 20, "#f0a3bf", "#f7c2d5", "#d8849f")}`),
  foam2: () => SV(`${bloque3d(8, 52, 64, 14, 20, "#f0a3bf", "#f7c2d5", "#d8849f")}`),
  cartonpluma: () => SV(`${bloque3d(6, 50, 72, 6, 18, "#f4f6fa", "#ffffff", "#e3e7ee")}<rect x="6" y="52" width="72" height="2" fill="#f0a3bf" opacity=".0"/>
      <line x1="6" y1="53" x2="78" y2="53" stroke="#cbd2de" stroke-width="2"/>`),
  cartulina: () => SV(`<rect x="18" y="16" width="62" height="64" rx="3" fill="#8b94a7" ${CONTORNO} transform="rotate(8 48 48)"/>
      <rect x="12" y="20" width="62" height="64" rx="3" fill="#a3abbc" ${CONTORNO}/>`),
  masilla: () => SV(`<rect x="16" y="22" width="22" height="60" rx="11" fill="#f4f6fa" ${CONTORNO}/><rect x="46" y="22" width="22" height="60" rx="11" fill="#9aa4b8" ${CONTORNO}/>
      <path d="M70,64 Q82,54 88,66 Q84,80 72,76 Z" fill="#cfd6e2" ${CONTORNO}/>`),
  conos: () => SV(`<path d="M24,86 L36,20 L48,86 Z" fill="#f4f6fa" ${CONTORNO}/><path d="M50,86 L64,36 L78,86 Z" fill="#e3e7ee" ${CONTORNO}/>
      <ellipse cx="36" cy="86" rx="12" ry="3" fill="#cfd6e2"/><ellipse cx="64" cy="86" rx="14" ry="3" fill="#cfd6e2"/>`),
  brochetas: () => SV(`${[0, 1, 2, 3].map((i) => `<line x1="${14 + i * 6}" y1="88" x2="${70 + i * 6}" y2="${10 + i * 2}" stroke="#d6a86b" stroke-width="4" stroke-linecap="round"/>`).join("")}
      <rect x="54" y="52" width="38" height="10" rx="3" fill="#e9c27f" ${CONTORNO} transform="rotate(-12 70 58)"/>`),
  alambre: () => SV(`<circle cx="48" cy="48" r="30" fill="none" stroke="#b8c0cf" stroke-width="3"/><circle cx="48" cy="48" r="24" fill="none" stroke="#9aa4b8" stroke-width="3"/>
      <circle cx="48" cy="48" r="18" fill="none" stroke="#b8c0cf" stroke-width="3"/><path d="M78,48 Q88,60 80,80" fill="none" stroke="#b8c0cf" stroke-width="3"/>`),
  pvc: () => SV(`${bloque3d(6, 50, 72, 5, 18, "#f8fafc", "#ffffff", "#e2e8f0")}<circle cx="48" cy="40" r="0" />`),

  // ---------------------------------------------------------- acabado
  balde: () => SV(`<path d="M18,26 L78,26 L72,86 L24,86 Z" fill="#e5e7eb" ${CONTORNO}/><ellipse cx="48" cy="26" rx="30" ry="7" fill="#f8fafc" ${CONTORNO}/>
      <path d="M18,26 Q48,-6 78,26" fill="none" stroke="#9aa4b8" stroke-width="3"/><rect x="28" y="46" width="40" height="20" rx="3" fill="#3b82f6"/>`),
  cola: () => SV(`<path d="M30,34 L66,34 L66,86 Q66,90 62,90 L34,90 Q30,90 30,86 Z" fill="#f8fafc" ${CONTORNO}/><path d="M38,34 L42,16 L54,16 L58,34 Z" fill="#f97316" ${CONTORNO}/>
      <rect x="45" y="6" width="6" height="10" fill="#f97316"/><rect x="34" y="50" width="28" height="22" rx="3" fill="#2563eb"/><text x="48" y="65" text-anchor="middle" font-size="11" font-weight="800" fill="#fff" font-family="Inter">COLA</text>`),
  mica: () => SV(`<rect x="10" y="16" width="62" height="62" rx="3" fill="rgba(200,230,255,.22)" stroke="#cfe0ff" stroke-width="2"/>
      <rect x="22" y="24" width="62" height="62" rx="3" fill="rgba(250,204,21,.55)" stroke="#facc15" stroke-width="2"/>
      <rect x="34" y="32" width="54" height="54" rx="3" fill="rgba(255,255,255,.75)" stroke="#e5e7eb" stroke-width="2"/>
      <path d="M14,22 L30,22" stroke="#fff" stroke-width="2" opacity=".7"/>`),
  imprimante: () => SV(`<rect x="22" y="28" width="52" height="58" rx="8" fill="#f8fafc" ${CONTORNO}/><rect x="20" y="18" width="56" height="14" rx="4" fill="#cbd5e1" ${CONTORNO}/>
      <rect x="28" y="46" width="40" height="22" rx="3" fill="#94a3b8"/><text x="48" y="61" text-anchor="middle" font-size="10" font-weight="800" fill="#fff" font-family="Inter">BASE</text>`),
  pinturas: () => SV(`${[["#f8fafc", 8], ["#111827", 30], ["#8a3b2a", 52], ["#2f7d4f", 74]].map(([c, x]) => `<rect x="${x}" y="30" width="18" height="52" rx="4" fill="${c}" ${CONTORNO}/><rect x="${x + 3}" y="20" width="12" height="10" rx="2" fill="#cbd5e1"/>`).join("")}`),
  barniz: () => SV(`<rect x="28" y="30" width="40" height="56" rx="8" fill="rgba(220,235,255,.35)" stroke="#cfe0ff" stroke-width="3"/><rect x="34" y="18" width="28" height="14" rx="3" fill="#475569"/>
      <path d="M36,40 L40,74" stroke="#fff" stroke-width="4" stroke-linecap="round" opacity=".8"/><path d="M76,20 l4,8 8,4 -8,4 -4,8 -4,-8 -8,-4 8,-4 z" fill="#fff"/>`),
  bicarbonato: () => SV(`${bloque3d(16, 30, 46, 56, 14, "#f97316", "#fb923c", "#c2410c")}<rect x="22" y="44" width="34" height="24" rx="3" fill="#fff"/>
      <text x="39" y="60" text-anchor="middle" font-size="10" font-weight="800" fill="#c2410c" font-family="Inter">BICARB.</text>`),
  escarcha: () => SV(`<rect x="24" y="34" width="48" height="52" rx="10" fill="rgba(220,235,255,.25)" stroke="#cfe0ff" stroke-width="3"/><rect x="22" y="22" width="52" height="14" rx="5" fill="#a78bfa" ${CONTORNO}/>
      ${[[34, 50, "#fff"], [48, 60, "#bfe6ff"], [60, 48, "#f0abfc"], [40, 72, "#fde68a"], [58, 74, "#fff"], [50, 44, "#a7f3d0"]].map(([x, y, c]) => `<path d="M${x},${y - 5} l1.6,3.4 3.4,1.6 -3.4,1.6 -1.6,3.4 -1.6,-3.4 -3.4,-1.6 3.4,-1.6 z" fill="${c}"/>`).join("")}`),
  barrasilicona: () => SV(`${[0, 1, 2].map((i) => `<rect x="${12 + i * 4}" y="${28 + i * 16}" width="70" height="12" rx="6" fill="rgba(230,240,255,.55)" stroke="#cfe0ff" stroke-width="2"/>`).join("")}`),

  // ---------------------------------------------------------- electrónica
  led: (c = "#fff4c2", brillo = "#fcd34d") => SV(`<circle cx="48" cy="30" r="26" fill="${brillo}" opacity=".18"/>
      <path d="M32,52 L32,30 Q32,12 48,12 Q64,12 64,30 L64,52 Z" fill="${c}" ${CONTORNO}/><rect x="28" y="52" width="40" height="7" rx="2" fill="${c}" ${CONTORNO}/>
      <line x1="40" y1="59" x2="40" y2="92" stroke="#9aa4b8" stroke-width="3"/><line x1="56" y1="59" x2="56" y2="82" stroke="#9aa4b8" stroke-width="3"/>`),
  ledrgb: () => SV(`<circle cx="48" cy="30" r="26" fill="#a78bfa" opacity=".2"/>
      <defs><linearGradient id="arcoiris" x1="0" x2="1"><stop offset="0" stop-color="#f87171"/><stop offset=".5" stop-color="#4ade80"/><stop offset="1" stop-color="#60a5fa"/></linearGradient></defs>
      <path d="M32,52 L32,30 Q32,12 48,12 Q64,12 64,30 L64,52 Z" fill="url(#arcoiris)" ${CONTORNO}/><rect x="28" y="52" width="40" height="7" rx="2" fill="#e9d5ff" ${CONTORNO}/>
      <line x1="40" y1="59" x2="40" y2="92" stroke="#9aa4b8" stroke-width="3"/><line x1="56" y1="59" x2="56" y2="82" stroke="#9aa4b8" stroke-width="3"/>`),
  resistencia: (bandas = ["#dc2626", "#dc2626", "#7c2d12", "#d4a017"]) => SV(`<line x1="2" y1="48" x2="94" y2="48" stroke="#9aa4b8" stroke-width="3"/>
      <rect x="24" y="36" width="48" height="24" rx="11" fill="#e8d3a6" ${CONTORNO}/>
      ${bandas.map((c, i) => `<rect x="${32 + i * 9 + (i === 3 ? 4 : 0)}" y="36" width="5" height="24" fill="${c}"/>`).join("")}`),
  usb: () => SV(`<rect x="8" y="38" width="34" height="20" rx="3" fill="#cfd6e2" ${CONTORNO}/><rect x="12" y="43" width="24" height="10" fill="#475569"/>
      <rect x="42" y="36" width="18" height="24" rx="4" fill="#111827" ${CONTORNO}/><path d="M60,48 Q76,48 78,64 Q80,84 94,86" fill="none" stroke="#111827" stroke-width="6" stroke-linecap="round"/>`),
  interruptor: () => SV(`<rect x="18" y="30" width="60" height="40" rx="6" fill="#111827" ${CONTORNO}/><path d="M30,40 L66,34 L66,62 L30,58 Z" fill="#ef4444" ${CONTORNO}/>
      <text x="40" y="54" font-size="12" font-weight="800" fill="#fff" font-family="Inter">I</text><circle cx="58" cy="48" r="5" fill="none" stroke="#fff" stroke-width="2"/>`),
  placa: () => SV(`<rect x="10" y="20" width="76" height="56" rx="4" fill="#3f7d4a" ${CONTORNO}/>
      ${Array.from({ length: 48 }, (_, i) => `<circle cx="${18 + (i % 8) * 9}" cy="${28 + Math.floor(i / 8) * 8}" r="2" fill="#d6b36a"/>`).join("")}`),
  cable: () => SV(`<circle cx="34" cy="48" r="24" fill="#7f1d1d" ${CONTORNO}/><circle cx="34" cy="48" r="16" fill="#dc2626"/><circle cx="34" cy="48" r="6" fill="#0b1528"/>
      <circle cx="66" cy="54" r="22" fill="#111827" ${CONTORNO}/><circle cx="66" cy="54" r="14" fill="#374151"/><circle cx="66" cy="54" r="5" fill="#0b1528"/>`),
  estano: () => SV(`<circle cx="44" cy="48" r="30" fill="#cbd5e1" ${CONTORNO}/><circle cx="44" cy="48" r="20" fill="#94a3b8"/><circle cx="44" cy="48" r="8" fill="#0b1528"/>
      <path d="M74,48 Q90,50 86,76" fill="none" stroke="#cbd5e1" stroke-width="3"/>`),
  motor: () => SV(`<rect x="10" y="30" width="34" height="36" rx="8" fill="#cbd5e1" ${CONTORNO}/><rect x="44" y="32" width="26" height="32" rx="2" fill="#d6b36a" ${CONTORNO}/>
      <rect x="70" y="44" width="22" height="8" fill="#e5e7eb" stroke="#7d8799" stroke-width="1.5"/><rect x="2" y="40" width="8" height="5" fill="#d6b36a"/><rect x="2" y="51" width="8" height="5" fill="#d6b36a"/>
      ${[48, 54, 60, 66].map((x) => `<line x1="${x}" y1="32" x2="${x}" y2="64" stroke="#a8843d" stroke-width="1.2"/>`).join("")}`),
  soporte: () => SV(`<path d="M14,70 L14,34 Q14,22 26,22 L70,22 Q82,22 82,34 L82,70" fill="none" stroke="#cbd5e1" stroke-width="6"/>
      <rect x="4" y="66" width="24" height="8" rx="2" fill="#cbd5e1"/><rect x="68" y="66" width="24" height="8" rx="2" fill="#cbd5e1"/>
      <circle cx="12" cy="70" r="2.5" fill="#0b1528"/><circle cx="84" cy="70" r="2.5" fill="#0b1528"/>`),
  rueda: () => SV(`<circle cx="48" cy="48" r="38" fill="#111827" ${CONTORNO}/><circle cx="48" cy="48" r="28" fill="#facc15" ${CONTORNO}/>
      <circle cx="48" cy="48" r="9" fill="#eab308" ${CONTORNO}/><path d="M45,45 L51,45 L51,49 L45,51 Z" fill="#0b1528"/>
      ${[0, 60, 120, 180, 240, 300].map((a) => `<circle cx="${48 + Math.cos(a * Math.PI / 180) * 19}" cy="${48 + Math.sin(a * Math.PI / 180) * 19}" r="4" fill="#eab308"/>`).join("")}`),
  cargador: () => SV(`${bloque3d(14, 30, 48, 52, 16, "#f8fafc", "#ffffff", "#d7dde7")}<rect x="26" y="44" width="22" height="8" rx="2" fill="#475569"/>
      <line x1="30" y1="30" x2="30" y2="16" stroke="#9aa4b8" stroke-width="4"/><line x1="46" y1="30" x2="46" y2="16" stroke="#9aa4b8" stroke-width="4"/>`),
  fusible: () => SV(`<line x1="4" y1="48" x2="30" y2="48" stroke="#9aa4b8" stroke-width="3"/><line x1="66" y1="48" x2="92" y2="48" stroke="#9aa4b8" stroke-width="3"/>
      <rect x="26" y="30" width="44" height="36" rx="16" fill="#eab308" ${CONTORNO}/><text x="48" y="54" text-anchor="middle" font-size="12" font-weight="800" fill="#1d1405" font-family="Inter">0.5A</text>`),
  fieltro: () => SV(`<rect x="10" y="26" width="76" height="44" rx="6" fill="#4b5563" ${CONTORNO}/>${Array.from({ length: 30 }, (_, i) => `<circle cx="${16 + (i * 29) % 66}" cy="${32 + (i * 17) % 34}" r="1" fill="#9ca3af"/>`).join("")}`),
};
