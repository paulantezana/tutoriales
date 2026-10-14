---
name: curso-youtube
description: >-
  Crea cursos y tutoriales de programación para YouTube en estilo "línea por línea": planifica el curso en varios videos donde cada uno termina con algo funcionando, escribe y verifica el código de cada etapa, y genera los videos con un motor incluido (VS Code simulado que escribe y explica cada línea, Debug Console y depurador, la app en un celular o navegador, escenas animadas HTML+GSAP y narración en español con voz Kokoro). Úsalo siempre que alguien pida hacer un curso, una serie de videos, un tutorial en video, clases grabadas, contenido educativo de programación para YouTube o explicar un proyecto de código paso a paso en video, aunque no diga "skill" ni "línea por línea", y también para continuar o corregir un curso ya empezado con este motor.
---

# Cursos de programación para YouTube, línea por línea

El objetivo es **educar**: que una persona que nunca hizo el proyecto pueda seguir el curso y entender cada línea. Todo lo demás (la arquitectura, la división en videos, el ritmo, el motor de video) está al servicio de eso. Este estilo nació de un curso real y de las correcciones de su autor; las reglas de abajo existen porque cada una arregló un problema que se vio en los videos.

## Antes de empezar: lee las guías

- `references/pedagogia.md`: cómo se diseña el curso y cómo se explica (la parte más importante). Léela completa antes de planificar.
- `references/motor.md`: cómo se usa el motor (comandos, API del guion, verificación). Léela antes de escribir guiones.
- `references/escenas.md`: escenas animadas incluidas y cómo escribir otras.
- `references/ejemplo-guion-video02.py`: un guion real completo (video 2 del curso YARBYS, Flutter). Úsalo como modelo de tono y de detalle.
- `references/celular.html` / `celular.js` y `references/escenas-ejemplo-yarbys.js`: ejemplos a la medida (réplica de una app y escenas de teoría).

## El flujo de trabajo

### 1. Entender el tema y proponer el plan (y esperar el visto bueno)

Pregunta lo que falte: tema, público (¿principiantes?), stack, qué app o resultado se construye, cuántos videos aproximadamente, voz y canal. Luego propón, **en el chat y antes de producir nada**:

- **El resultado final**: qué se construye y cómo se verá funcionando.
- **La arquitectura**: la más simple que sea correcta y enseñable (capas con una tarea cada una; la interfaz nunca llama directo a la base de datos o a la API, sino a una clase coordinadora). Menos código = se puede explicar línea por línea. Di cuántas líneas tendrá aproximadamente y qué recortaste para lograrlo.
- **Los videos** (tabla): título · qué se programa · qué se ve funcionando al final · qué anuncia del siguiente. La progresión típica: consola/depurador → interfaz básica → interfaz bonita → prueba final y entrega.
- **Un ejemplo de explicación** de un fragmento (2–3 líneas de código con su narración) para que la persona apruebe el tono.

No sigas hasta que la persona apruebe el plan: rehacer 9 videos cuesta horas.

### 2. Escribir el proyecto final y sus etapas

1. Escribe el proyecto terminado en `codigo/` y verifícalo de verdad (compila, `analyze`/lint, pruebas). Formatea con el formateador oficial del lenguaje: el video escribe el archivo exactamente como está.
2. Crea `curso/NN-nombre/` con el código **tal como queda al final de cada video**. Lo más práctico es derivar las etapas hacia atrás desde el final (quitando lo que aún no se programó) con un script propio. Cada etapa debe compilar sola: verifícalo con `scripts/verificar_etapas.py`.
3. Diseña las etapas para que cada cambio entre videos sea explicable: introduce un concepto por vez (por ejemplo, un `bool` que en un video posterior se convierte en `enum` es una buena lección; renombrar cosas sin motivo no lo es).

### 3. Preparar el motor

```bash
python <skill>/scripts/nuevo_curso.py ~/cursos/mi-curso --nombre miapp --curso "Curso de X" --canal "Mi canal" --logo logo.png
bash <skill>/scripts/instalar.sh ~/cursos/mi-curso/video     # pip, Chromium, ffmpeg y la voz Kokoro (~340 MB)
```

Edita `video/proyecto.py` (todo lo propio del curso está documentado ahí) y pon en `video/plantilla/` los archivos del proyecto recién creado (lo que deja `flutter create`, `npm create vite`, etc.).

### 4. Piloto: los videos 1 y 2

Escribe los guiones en `video/guiones/videoNN.py` (parte de `guiones/plantilla_video.py`). Para cada video:

```bash
cd ~/cursos/mi-curso/video
python -c "import render; render.guion_video(2)"     # prueba en seco: corre el guion y verifica el código
python render.py --video 2 --preview 20              # capturas en preview/ para revisar
python render.py --video 2                           # el video: videos/02-nombre.mp4 + .md + .srt
python <skill>/scripts/revisar_video.py videos/02-nombre.mp4   # duración, volumen, silencios, hoja de capturas
```

Mira las capturas antes de entregar (notas que tapan código, textos que se montan, escenas vacías). Entrega los dos primeros videos y pide opinión sobre el ritmo y el detalle de la explicación **antes** de producir el resto.

### 5. El resto del curso

Con el formato aprobado, produce los demás videos del mismo modo. Al terminar cada uno, revisa con `revisar_video.py`. Los `.mp4` no van a git (pesan mucho y cada versión queda para siempre en el historial): entrégalos directamente o súbelos a un almacenamiento; en el repositorio quedan el código, los guiones, los `.md` y los `.srt`.

## Reglas del estilo (resumen; el detalle y el porqué están en `references/pedagogia.md`)

- **Línea por línea mientras se escribe**: cada grupo de 1 a 5 líneas se escribe mientras la voz explica qué hace y por qué; luego se resalta con una nota corta. Las llaves y los imports triviales se agrupan.
- **De arriba hacia abajo**: archivos (para qué sirve cada uno) → ficha del archivo → clase → firmas de métodos → implementación.
- **Avance visible**: cada video termina mostrando algo que funciona (consola, depurador, app). Ningún video termina de golpe: cierra con lo logrado y lo que viene.
- **Primero la lógica, después la interfaz**: se prueba en la consola o con el depurador; luego interfaz básica; al final la bonita.
- **Las URL no se teclean**: se pegan, y se muestra de dónde salen (navegando la página real o con la escena `url`).
- **Nada de silencios largos**: sin sonido de teclado; el tecleo largo se acelera solo (etiqueta ⏩ x4); nunca más de ~10 s sin voz.
- **Estilo visual**: oscuro y plano (sin degradados), logo del canal en una esquina, sin subtítulos incrustados (el `.srt` va aparte).
- **Honestidad**: si el resultado de la app es una réplica con respuestas de ejemplo, dilo en la descripción y en el README. Cuando se pueda, muestra salidas reales: ejecuta el programa de verdad y copia su salida a la consola, o captura la página web real con `PAGINAS`.

## Si algo no está disponible

- **Sin GitHub** para descargar la voz: busca `kokoro-onnx` en otro espejo permitido o pide a la persona los archivos `kokoro-v1.0.onnx` y `voices-v1.0.bin`. El motor también acepta `kokoro-quantized.onnx` + `voices.npz`.
- **Una página web bloqueada** (no se puede capturar): usa la escena `url` para mostrar los pasos y las partes del enlace, y dilo.
- **Una plataforma que no puedes ejecutar** (por ejemplo, un celular): construye una réplica por etapas en `escenas/app_pantallas.js` (ver `references/celular.js`) y aclara que es una recreación.
