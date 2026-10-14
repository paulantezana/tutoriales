/* Pantallas de la app de ESTE curso (ejemplo: una lista de tareas). Cada pantalla es una función
   (s, T, t) → HTML: s es el estado (ver app.js), T el tema y t el segundo actual.
   Escribe una versión por etapa del curso cuando cambie el diseño (por ejemplo "basico" y "final"),
   y usa ids en los elementos que se tocan: el guion hace ("toque", "agregar"). */
const TEMAS = {
  basico: { bg: "#fef7ff", on: "#1d1b20", var: "#49454f", primary: "#6750a4", oscuro: false },
  final: { bg: "#0f1418", on: "#ffffff", var: "#9aa5ae", primary: "#007bdf", sup: "#1f272e", oscuro: true },
};
window.ESTADO_INICIAL = { tareas: [] };

const PANTALLAS = {
  lista: (s, T) => {
    const tareas = (s.tareas || []).map((x, i) => `<div style="display:flex;align-items:center;gap:16px;padding:14px 22px;font:400 19px Roboto;color:${T.on}">
        ${I(x.hecha ? "circle-check" : "circle", 26, x.hecha ? T.primary : T.var)}<span style="${x.hecha ? "text-decoration:line-through;opacity:.6" : ""}">${esc(x.texto)}</span></div>`).join("");
    return `<div style="position:absolute;left:0;right:0;top:52px;height:72px;display:flex;align-items:center;padding:0 20px;font:400 25px Roboto;color:${T.on}">Mis tareas</div>
      <div style="position:absolute;left:0;right:0;top:124px;bottom:100px;overflow:hidden">${tareas}</div>
      <div style="position:absolute;left:16px;right:16px;bottom:24px;display:flex;gap:10px;align-items:center">
        <div id="campo" style="flex:1;height:56px;border-bottom:1.5px solid ${T.var};display:flex;align-items:center;font:400 18px Roboto;color:${s.campo ? T.on : T.var}">${s.campo ? esc(s.campo) : "Nueva tarea"}</div>
        <div id="agregar" style="width:52px;height:52px;border-radius:50%;background:${T.primary};display:grid;place-items:center;color:#fff">${I("plus", 26)}</div></div>`;
  },
};
