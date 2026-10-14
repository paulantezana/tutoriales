# Pedagogía del curso: cómo se diseña y cómo se explica

Es un curso, no una demostración. Quien lo mira quiere **aprender a hacerlo**, así que cada decisión se toma pensando en alguien que escribe el código junto al video y necesita entender cada línea.

## Índice
1. Diseñar el proyecto para poder explicarlo
2. Dividir en videos con avance visible
3. La estructura de cada video
4. Explicar línea por línea
5. Mostrar resultados
6. Ritmo, voz y estilo visual
7. Errores que ya se cometieron (y cómo se arreglaron)

---

## 1. Diseñar el proyecto para poder explicarlo

**Menos código.** Explicar línea por línea cuesta unos 4–8 segundos por línea. Un proyecto de 2 000 líneas da más de 4 horas solo de código; uno de 800–900 líneas cabe en 8–10 videos de 15–25 minutos. Antes de escribir, recorta todo lo que no enseña algo nuevo: funciones repetidas, opciones avanzadas, pantallas de configuración, variantes. Si algo es valioso pero largo, va a un video "bonus" opcional o se quita.

**Arquitectura simple y correcta.** Por ejemplo, en tres capas:
```
PANTALLAS (lo que ves)  →  solo hablan con  →  COORDINADOR (una clase que une todo)  →  usa  →  SERVICIOS (una tarea cada uno)
```
- Una tarea por clase (`Memoria` guarda y lee; `Cerebro` habla con el modelo).
- La interfaz nunca llama directo a la base de datos o a la API externa: así cada pieza se prueba primero en la consola y luego se conecta a la pantalla sin cambiar la lógica. Esa regla se explica en el video 1 y se recuerda en el mapa de cada video.
- Sin librerías de arquitectura que agreguen conceptos (Bloc, Redux, inyección de dependencias...) si el tamaño del proyecto no lo justifica; dilo como decisión consciente.
- Buenas prácticas visibles: nombres claros en el idioma del curso, métodos cortos (≤ 20 líneas), `try/finally` donde se liberan recursos, sin claves ni secretos en el código, una prueba automática de la lógica pura (y se ejecuta en un video).

**Código formateado con la herramienta oficial** (`dart format`, `black`, `prettier`...). El video lo escribe tal cual: si el formateador lo cambia después, el código del video y el del repositorio ya no coinciden.

## 2. Dividir en videos con avance visible

Cada video agrega una pieza y **termina mostrando algo que funciona**. La progresión que mejor funciona:

1. **Qué vamos a construir**: el resultado final, la teoría general, la arquitectura, crear el proyecto y ejecutarlo (aunque sea la app de ejemplo) con hot reload o equivalente.
2. **La lógica central en la consola**: sin pantalla. El resultado se ve en la Debug Console, y se muestra el depurador (punto de parada, valor de una variable).
3. **Interfaz básica**: la pantalla más simple posible (widgets/componentes por defecto, sin diseño) conectada a la lógica.
4. … una pieza por video, siempre probada primero en la consola cuando sea lógica nueva, y después conectada a la interfaz.
5. **Interfaz bonita**: tema, colores, componentes propios, animaciones. Aquí el cambio visual es grande y motiva.
6. **Prueba final y entrega**: todo funcionando de punta a punta, compilar el instalable o publicar, resumen del curso.

Instala cada paquete en el video donde se usa por primera vez (buscándolo en su página, como pub.dev o npmjs), no todos al principio: así cada instalación tiene un porqué.

Videos de 10–25 minutos. Si un tema pasa de 25 minutos, divídelo en dos videos, cada uno con su resultado (por ejemplo, "buscar en la consola" y "usarlo en la pantalla").

## 3. La estructura de cada video

1. **Portada** (escena `portada`): saludo, "hoy vamos a…" (2–4 puntos) y "al final del video vas a tener…".
2. **Dónde estamos** (escena `mapa`): la arquitectura con lo hecho (✓), lo de hoy (resaltado) y lo que falta (apagado). Un recordatorio de una frase de lo que se hizo en el video anterior.
3. **Teoría justa**: solo los conceptos que se usan hoy, con escenas animadas (`concepto`, `pasos`, `comparar` o una propia). La teoría se reparte entre los videos, no se acumula toda en el primero.
4. **Código** (en VS Code):
   - Crear los archivos del día diciendo para qué sirve cada uno.
   - Por archivo: la **ficha** (mapa del archivo: clases, métodos y campos con una línea de qué hace cada uno).
   - De arriba hacia abajo: imports → clase → firmas de los métodos (todavía vacíos) → implementación de cada método.
   - Cada grupo de líneas, explicado mientras se escribe (ver la sección 4).
5. **Resultado**: ejecutar (F5) y mostrarlo (consola, depurador, la app en el celular o navegador). Si hay varias formas de probar, de la más simple a la más vistosa.
6. **Cierre** (escena `siguiente`): 2–4 logros del día y qué se hará en el próximo video, con una frase que dé ganas de verlo. El último video cierra el curso ("¡Terminaste el curso!") y luego la despedida del canal (escena `final`).

## 4. Explicar línea por línea

Para cada grupo de 1 a 5 líneas: **mientras se escribe**, la voz dice qué hace y por qué; al terminar de escribirlo se resalta con una nota corta (título + 1–2 líneas). Las notas resumen, la voz explica.

- Explica **el porqué**, no solo el qué: "await espera a que cargue, porque tarda unos segundos" enseña más que "await espera".
- Cada palabra nueva del lenguaje se explica la primera vez (`static`, `async*`, `yield`, `final`, `=>`, comprensión de listas…) y después ya no.
- Agrupa lo trivial: imports, llaves de cierre, líneas en blanco. Nunca expliques una llave.
- Las firmas de clases y métodos se escriben y explican antes que sus cuerpos ("recibe X, devuelve Y, es async porque…").
- En un archivo que ya existe, se borran o cambian líneas concretas con su explicación ("cambiamos el bool por un enum porque ahora hay cuatro estados"). Nunca reescribas un archivo entero si solo cambian unas líneas.
- Las URL, claves de ejemplo o textos largos no se teclean: se pegan (el motor lo hace solo) y se muestra de dónde salen.
- Tono: tutor cercano, de "tú", frases cortas y naturales, sin relleno. Ejemplo:

> 🎙 "Primero cargamos Gemma en la memoria del celular. getActiveModel nos da el modelo que descargamos. maxTokens, 4096, es el contexto: cuánto texto puede leer de una vez, sumando la pregunta y la respuesta. Y await espera a que cargue, porque tarda unos segundos."
> Nota: **getActiveModel** · maxTokens: 4096 → el contexto · await: espera a que cargue

## 5. Mostrar resultados

- **Consola primero**: `print`/`debugPrint`/`console.log` con la salida en la Debug Console. Si el programa se puede ejecutar de verdad, **ejecútalo y usa su salida real**.
- **Depurador**: un punto de parada en una línea clave, la línea pausada en amarillo y el valor de una variable al pasar el mouse. Enseña a investigar, no solo a ejecutar.
- **La app**: en un celular o navegador. Para web, captura la página real (`PAGINAS` con la URL local mientras corre el servidor). Si no se puede ejecutar la plataforma, una réplica por etapas (con la interfaz básica en los primeros videos y la final al final) y se aclara que es una recreación con datos de ejemplo.
- Prueba los casos que demuestran la pieza del día (por ejemplo, para memoria: cerrar la app, abrirla y que recuerde).

## 6. Ritmo, voz y estilo visual

- Nunca más de ~10 segundos sin voz. Si un bloque tarda en teclearse, se acelera (lo hace el motor y muestra ⏩ x4); si aun así queda silencio, agrega una frase que explique lo que se escribe.
- Sin sonido de teclado ni clics (molesta).
- Pronunciación: los términos técnicos en inglés se escriben como se leen en español en `PRONUNCIACION` (por ejemplo, `("await", "auéit")`). Revisa las frases nuevas de cada video: cualquier nombre raro necesita su entrada. Los nombres en camelCase se separan solos ("hasActiveModel" → "jas áctiv módel").
- Estilo visual: fondo oscuro y plano, sin degradados; un color de marca; logo del canal en una esquina en todo el video; sin subtítulos incrustados (el `.srt` se sube aparte a YouTube); 1080p a 30 fps; volumen normalizado a −16 LUFS.

## 7. Errores que ya se cometieron (y cómo se arreglaron)

| Problema que se vio | Arreglo |
|---|---|
| Se escribía todo el código y recién al final se explicaba | Explicar cada grupo de líneas mientras se escribe |
| El código aparecía en el orden del archivo, sin contexto | Archivos → ficha → clase → firmas → cuerpos |
| Las URL se tecleaban letra por letra y no se sabía de dónde salían | Se pegan y se muestra la página de origen |
| Ruido de teclado constante | Sin sonido de teclado |
| Tramos de hasta 80 s tecleando en silencio | Tecleo acelerado con etiqueta ⏩ y límite de ~8 s |
| Todo se probaba recién al final del curso | Resultado visible al final de cada video |
| Videos que terminaban de golpe | Escena de cierre con lo logrado y el próximo video |
| La nota amarilla tapaba el código de arriba | El editor se desplaza para dejar la nota debajo |
| Un proyecto de 2 000 líneas imposible de explicar entero | Simplificar la arquitectura y recortar funciones hasta ~900 líneas |
| Un título largo de portada se montaba sobre el subtítulo | Las escenas usan columnas que fluyen; revisar capturas antes de entregar |
