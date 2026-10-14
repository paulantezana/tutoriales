# Escenas animadas (HTML + GSAP)

Cada escena es una línea de tiempo de GSAP en pausa que el motor recorre fotograma a fotograma (`window.seek(t)`). Se usan con:

```python
D.slide(R.SlideHTML("concepto", datos), frases=["frase 0", "frase 1", ...])
```

Dentro de la escena, `m(i)` es el segundo en que empieza la frase `i`: así cada parte aparece justo cuando la voz habla de ella. `DATOS` son los datos que le pasas desde el guion. Los íconos son de Lucide por su nombre (`"brain"`, `"database"`, `"rocket"`...; más de 2 000 en `escenas/lib/iconos.js`) y algunas marcas con prefijo `si_` (`si_github`, `si_flutter`, `si_python`...).

## Escenas incluidas

### portada
`{"curso", "num", "total", "titulo" (html; usa <span class='acento'>…</span> para el color), "sub", "puntos": [[icono, texto]], "resultado", "icono"}`
Frases: 0 saludo · 1 "hoy vamos a…" (aparecen los puntos) · 2 "al final del video…" (aparece el resultado).

### temario
`{"videos": [[título, resultado, icono]], "actual": n}` — todos los videos del curso (usa `R.CFG.VIDEOS`). Aparecen en tres tandas: frases 0, 1 y 2.

### mapa
`{"capas": [{"etiqueta", "color", "items": [[id, icono, título, archivo]]}], "contenedor": [icono, texto], "hechos": [ids], "hoy": [ids], "kicker", "titulo"}`
- Normal (inicio de cada video): frase 0 recuerda; en la frase 1 se resaltan las piezas de hoy, las hechas llevan ✓ y las que faltan se apagan.
- `"explicar": true` (video 1, para presentar la arquitectura): aparece una capa por frase y, si hay `"regla"`, se muestra en la frase siguiente (por ejemplo "Las pantallas solo hablan con Yarbys").
Define las capas una sola vez en un módulo del curso y reúsalas en todos los guiones.

### concepto
`{"kicker", "icono", "titulo", "sub", "tarjetas": [[icono, título, texto, color]]}` (2 a 4 tarjetas)
Frases: 0 presenta el concepto · 1..n una por tarjeta (se resalta la actual).

### pasos
`{"kicker", "icono", "titulo", "pasos": [[icono, título, texto]]}` — pasos numerados; una frase por paso.

### comparar
`{"kicker", "icono", "titulo", "izq": {"icono", "titulo", "color", "puntos": [], "marca": "check"}, "der": {...}}`
Frases: 0 intro · 1 izquierda · 2 derecha. Para "nube vs local", "antes vs después", "con vs sin".

### url
`{"nombre", "sitio", "pasos": [[icono, título, texto]], "url": [[texto, color, etiqueta]], "nota"}` — de dónde sale un enlace cuando la página real no se puede capturar: los pasos para encontrarlo y el enlace coloreado por partes (sitio, autor, nombre, versión, archivo).
Frases: 0 intro · 1 los pasos · 2 las partes del enlace.

### siguiente
`{"num", "logros": [texto], "sig": {"num", "titulo", "sub"}}` — cierre de cada video. Sin `"sig"` es el cierre del curso (`"cierre"` opcional). Frases: 0 los logros · 1 el próximo video.

### final
`{"repo": "usuario/repositorio", "nombre": "Tu nombre"}` — despedida del canal con el logo (`marca/logo.png`) y los botones de me gusta, suscríbete y comenta.

## Escribir una escena nueva

Agrega en `escenas/escenas.js`:

```js
ESCENAS.mi_escena = () => {
  const D = DATOS;
  formas(0);                                            // formas decorativas planas
  cabecera("Kicker", "icono", "Título con <span class='acento'>acento</span>", "subtítulo");
  const a = tarjeta(140, 330, 780, 200, "database", "Título", "Texto", C.celeste);
  pop(a, m(1));                                         // aparece en la frase 1
  const b = nuevo("div", "panel", "html", esc, "left:1000px;top:330px;width:780px;height:200px;padding:30px");
  subir(b, m(2));
  flecha(920, 430, 1000, 430, m(2) + 0.5);
  resaltar(a, m(3), C.amarillo); normal(a, m(4));
  salida();                                             // fundido al final
};
```

Utilidades: `nuevo(tag, clase, html, padre, estilo)`, `ico(nombre, tamaño, color)`, `cabecera`, `formas`, `tarjeta`, `pop`, `subir`, `aparecer`, `resaltar`, `normal`, `apagar`, `flecha`, `contador`, `escribir` (texto que se escribe solo), `svg`/`trazo` + `dibujarAnillos` (dibujar trazos), `telefono(padre, x, y, w, h)`. Colores en `C` (`azul`, `celeste`, `rojo`, `amarillo`, `verde`, `suave`, `borde`...). Clases CSS útiles: `panel`, `pastilla`, `etiqueta`, `kicker`, `titulo`, `subtitulo`, `mono`, `cuadro-icono`, `acento`.

Estilo: 1920×1080, fondo oscuro plano, sin degradados, textos grandes (mínimo ~20 px), una idea por frase. Revisa la escena antes de renderizar el video: abre `escenas/escena.html?id=mi_escena&dur=20&m=0,5,10&d=<json url-encoded>` en Chromium y mira varios tiempos (o crea un script con Playwright que haga `seek(t)` y capture).

`references/escenas-ejemplo-yarbys.js` tiene escenas de teoría completas de otro curso (LLM, tokens, embeddings, base vectorial, RAG, memoria, instalación...) para inspirarte.
