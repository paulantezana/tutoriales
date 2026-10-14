# El motor de video: cómo se usa

El motor está en `assets/motor/` y `scripts/nuevo_curso.py` lo copia a `<curso>/video/`. Un video es un archivo Python (`guiones/videoNN.py`) que **dirige** una simulación: el `Director` (variable `D`) avanza el tiempo fotograma a fotograma mientras narra, mueve el mouse, escribe en VS Code, ejecuta en la consola o muestra escenas. Luego `render.py` dibuja cada fotograma (Pillow para VS Code, Chromium para las escenas HTML), genera la voz con Kokoro y une todo con ffmpeg.

## Índice
1. Carpetas y comandos
2. proyecto.py
3. Estructura de un guion
4. Narración
5. Código línea por línea (`Codigo`)
6. VS Code: archivos, terminal, ficha, notas
7. Ejecutar y depurar
8. Escenas animadas
9. La app (celular o navegador)
10. Navegador con páginas reales
11. Verificar y revisar
12. Problemas comunes

---

## 1. Carpetas y comandos

```
mi-curso/
  codigo/                 el proyecto terminado
  curso/01-nombre/ ...    el código al final de cada video
  video/
    render.py  curso.py  proyecto.py
    guiones/videoNN.py    un guion por video (NOMBRE, ETAPA y guion(D, R))
    plantilla/            archivos del proyecto recién creado (ARCHIVOS_PLANTILLA)
    escenas/              escenas HTML+GSAP, réplica de la app (app.html + app_pantallas.js)
    marca/logo.png        logo del canal
    modelos/              voz Kokoro (kokoro-v1.0.onnx + voices-v1.0.bin)
    videos/               salida: NN-nombre.mp4, .md (guion con tiempos y capítulos) y .srt
```

```bash
python -c "import render; render.guion_video(2)"   # prueba en seco (rápida, sin audio ni imágenes)
python render.py --video 2 --preview 20            # capturas cada 20 s en preview/
python render.py --video 2                         # video completo (usa todos los núcleos)
```

La prueba en seco ya detecta casi todos los errores: líneas que no existen, código que no coincide con la etapa, escenas sin datos. Úsala después de cada cambio del guion.

## 2. proyecto.py

Todo lo propio del curso: nombre, lista de videos (para el temario), logo y colores, voces, pronunciación extra, la plantilla del proyecto (`ARCHIVOS_PLANTILLA`), cómo se guardan las etapas (`ETAPAS_COMPLETAS`, `QUITAR`), los mensajes de arranque de F5 (`LANZAR`, `PREFIJO_APP`, `RECARGA`), la réplica de la app (`REPLICA`) y las páginas web reales (`PAGINAS`). Cada opción está comentada en el archivo.

Ejemplos de `LANZAR` y `PREFIJO_APP`:
- Flutter (Android): `[("Launching lib\\main.dart on Pixel 8 in debug mode...", 0.9), ("Running Gradle task 'assembleDebug'...", 2.4), ("√ Built build\\app\\outputs\\flutter-apk\\app-debug.apk", 0.4)]`, `PREFIJO_APP = "I/flutter (24816): "`, `RECARGA = "Reloaded 1 of 1042 libraries in 389ms."`
- Python: `[("Launching src\\main.py...", 0.6)]`, `PREFIJO_APP = ""`, `RECARGA = None`
- Node: `[("C:\\Program Files\\nodejs\\node.exe .\\src\\index.js", 0.6)]`

## 3. Estructura de un guion

```python
NOMBRE = "02-gemma-en-consola"      # nombre del archivo de salida
ETAPA = 2                           # el código termina igual que curso/02-*/

def guion(D, R):                    # R = el módulo render (constantes, SlideHTML, CFG...)
    D.capitulo("Introducción")      # capítulos: van a la descripción de YouTube y a la etiqueta de arriba
    D.slide(R.SlideHTML("portada", {...}), frases=[...])
    D.abrir_proyecto(ETAPA - 1)     # VS Code con el código del video anterior
    ...
```

Parte de `guiones/plantilla_video.py` y mira `references/ejemplo-guion-video02.py` (un video real completo).

## 4. Narración

- `D.say(frase)`: empieza a hablar y **no espera**: lo que sigue (escribir, mover el mouse) ocurre mientras habla. `D.say(frase, esperar=True)` espera a que termine. `D.hold()` espera a que termine la frase en curso.
- `D.wait(segundos)`: pasa el tiempo.
- `D.slide(escena, frases=[...])`: muestra una escena y la narra; cada frase marca un tiempo `m(i)` que la escena usa para animar.
- La duración real de cada frase viene del audio (primera pasada); el guion se ejecuta dos veces.

## 5. Código línea por línea (`Codigo`)

`c = D.codigo(ruta, ETAPA)` compara lo que hay ahora en el editor con `curso/NN-*/ruta` y deja listas las líneas nuevas (`c.nuevas`) y las viejas que sobran (`c.viejas`). Después, en el orden pedagógico que quieras:

| Método | Qué hace |
|---|---|
| `D.poner(c, lineas, frase, titulo=None, nota=None, modo="escribir")` | Escribe esas líneas nuevas en su lugar exacto mientras narra la frase; luego las resalta con la nota. `modo="pegar"` las pega de una vez |
| `D.cambiar(c, viejas, nuevas, frase, titulo, nota)` | Selecciona líneas viejas, las borra y escribe las nuevas en su lugar |
| `D.quitar(c, viejas, frase)` | Selecciona y borra líneas viejas |
| `D.vaciar(c, frase)` | Ctrl + A y Suprimir (reemplazar un archivo entero) |
| `D.terminar(c)` | Verifica que el archivo quedó **idéntico** al de la etapa (si no, el guion falla) |

Para elegir líneas (índices en `c.nuevas`):

| Ayuda | Devuelve |
|---|---|
| `c.rango("desde", "hasta")` | De la línea que contiene "desde" a la que contiene "hasta" |
| `c.j("texto")` | El índice de la primera línea que contiene el texto |
| `c.firma("def agregar")` | La firma (hasta `{` o `:`) y, si hay llaves, la llave de cierre: la estructura sin el cuerpo |
| `c.cuerpo("def agregar")` | Las líneas de adentro |
| `c.bloque("class Tareas")` | Todo el bloque |
| `c.viejas_rango("desde", "hasta")`, `c.viejas_vivas()` | Líneas viejas (para `cambiar`/`quitar`) |

Reglas útiles:
- Las líneas que se escriben juntas deben quedar juntas en el archivo (no puede haber líneas ya escritas entre ellas). Por eso se escribe primero la firma con su llave de cierre y después el cuerpo.
- Incluye las líneas en blanco en algún paso (por ejemplo, `[c.j("def agregar") - 1] + c.rango(...)`). `D.terminar(c)` avisa si faltó alguna.
- La velocidad de tecleo se ajusta sola a la duración de la frase; si un bloque es largo, se acelera con la etiqueta ⏩.

## 6. VS Code: archivos, terminal, ficha, notas

- `D.abrir_proyecto(etapa)`: VS Code con el proyecto tal como quedó en esa etapa.
- `D.nuevo_archivo("src/x.py")`: crea el archivo desde el explorador (la carpeta se crea sola).
- `D.abrir_desde_explorador(ruta)`, `D.borrar_archivo(ruta, frase)`, `D.guardar()` (Ctrl + S).
- `D.ficha(titulo, descripcion, [(tipo, nombre, explicación), ...])`: el mapa del archivo a la derecha (tipos: clase, widget, estado, método, función, getter, campo, constante, enum, carpeta, archivo). `D.ficha_explicar(k, frase, firma)` resalta el elemento k (y su línea en el código) mientras se explica; `D.ficha_hecho(k)` le pone ✓; `D.ficha_ocultar()`.
- `D.resaltar(desde, hasta, titulo=, nota=, frases=[...])`: selecciona líneas que ya existen (buscadas por texto) y las explica.
- Terminal: `D.abrir_terminal()`, `D.comando("npm install x")`, `D.salida(texto, color, pausa)`, `D.salida_segs([(texto, color), ...])`, `D.fin_comando()`. Colores en `R`: `R.G` (verde), `R.GRIS`, `R.BLANCO`.
- `D.atajo("Ctrl + S")`: muestra la tecla en pantalla.
- `D.set(term_abierto=False)`: cierra el panel de abajo.

## 7. Ejecutar y depurar

- `D.depurar()`: F5, barra de estado naranja, barra de depuración y los mensajes de `CFG.LANZAR` en la Debug Console.
- `D.consola(texto, app=True)`: una línea que imprime el programa (con `CFG.PREFIJO_APP`). Sin `app`, una línea del sistema.
- `D.recargar()` (hot reload al guardar), `D.reiniciar()` (Ctrl + Shift + F5), `D.detener()` (Shift + F5).
- Depurador: `lin = D.punto_de_parada("texto de la línea")` (punto rojo), `D.pausar_en(lin)` (línea amarilla), `D.mostrar_valor("variable", "valor")` (globo con el valor), `D.continuar()`.

Si el programa se puede ejecutar de verdad, ejecútalo en el guion con `subprocess` y muestra su salida real con `D.consola`.

## 8. Escenas animadas

`D.slide(R.SlideHTML("id", datos), frases=[...])`. Escenas incluidas y sus datos en `references/escenas.md`: `portada`, `temario`, `mapa`, `concepto`, `pasos`, `comparar`, `url`, `siguiente`, `final`. Para un concepto que merece su propia animación, escribe una escena nueva en `escenas/escenas.js` (ver `references/escenas-ejemplo-yarbys.js`).

## 9. La app (celular o navegador)

`D.app(id, (icono, kicker, titulo_html), pasos, inicial=[...])` muestra la réplica (`escenas/app.html` + tus pantallas en `escenas/app_pantallas.js`) a la izquierda y un título con notas a la derecha, mientras narra.

- `inicial`: eventos en t = 0, por ejemplo `("marco", "navegador")` o `("marco", "celular")`, `("tema", "basico")`, `("pantalla", "lista")`, `("url", "localhost:3000")`, `("debug", True)`, `("set", "tareas", [...])`.
- Pasos: `("decir", frase)`, `("esperar", s)`, `("toque", "id-del-elemento")`, `("escribir", texto[, id_campo])`, `("enviar"[, id_boton])`, `("nota", icono, texto, color)`, `("ev", tipo, ...)` (cualquier evento), y para chats `("preguntar", pregunta, respuesta, fuentes, {"voz": bool, "habla": bool})`.
- Escribe en `app_pantallas.js` una función por pantalla `(s, T, t) => html` y un tema por etapa visual (por ejemplo `basico` en los primeros videos y `final` en el de diseño). Pon `id` a los elementos que se tocan. `references/celular.js` es una réplica completa de una app de chat con tres temas.

## 10. Navegador con páginas reales

Declara las páginas en `CFG.PAGINAS` (`id: (url, {clave: selector CSS})`). El motor las captura con Chromium la primera vez (caché en `_cache_web/`) y guarda la posición de cada elemento. En el guion:

```python
D.navegador_abrir()
D.navegador_ir("pub.dev", "pub_inicio")
D.navegador_escribir("busqueda", "flutter_edge_ai")
D.navegador_enter("pub.dev/packages?q=flutter_edge_ai", "pub_busqueda")
D.navegador_clic("resultado", "pub.dev/packages/flutter_edge_ai", "pub_paquete")
D.navegador_desplazar("seccion")          # desplaza hasta un elemento (o px)
D.navegador_marcar("comando", 0.4)        # recuadro alrededor de un elemento
D.navegador_cerrar()
```

Para una app web propia, levanta el servidor local antes de renderizar y declara `http://localhost:PUERTO/...` en `PAGINAS`: se ve la app real.

## 11. Verificar y revisar

- `scripts/verificar_etapas.py`: compila y prueba cada etapa en una copia limpia del proyecto.
- `D.terminar(c)` en el guion: el archivo escrito en el video es idéntico al de la etapa.
- `scripts/revisar_video.py video.mp4`: duración, volumen, silencios largos y una hoja de capturas para mirar.
- Antes de entregar, mira la hoja de capturas: notas que tapan código, textos encimados, escenas vacías, nombres mal pronunciados (escucha un tramo).

## 12. Problemas comunes

| Error | Causa y solución |
|---|---|
| `no encuentro 'texto'` | El marcador no existe en el archivo de la etapa (quizá el formateador partió la línea): usa otro trozo de la línea |
| `lo escrito no coincide` / `desfasado` | El editor no tenía el contenido de la etapa anterior: revisa que el video anterior termine con `D.terminar` y que `abrir_proyecto(ETAPA - 1)` corresponda |
| `hay líneas escritas entre X e Y` | Esas líneas no quedan juntas: escribe primero las de afuera (firma + cierre) o divide el paso |
| `faltan líneas [...]` | Alguna línea (a menudo en blanco) no se escribió en ningún paso |
| Escena vacía o en negro | Revisa la consola del navegador con una vista previa de la escena; casi siempre es un dato que falta o un ícono que no existe en `escenas/lib/iconos.js` |
| Palabra mal pronunciada | Agrégala a `PRONUNCIACION` en proyecto.py (cambiar el texto cambia el audio en caché) |
| "Faltan los archivos del modelo Kokoro" | Corre `scripts/instalar.sh` o copia los archivos a `video/modelos/` |
