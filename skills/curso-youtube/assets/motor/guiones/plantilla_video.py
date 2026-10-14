"""Plantilla de un video del curso. Cópiala como guiones/videoNN.py y llénala.

Estructura que siempre se respeta (ver references/pedagogia.md):
  1. Portada: saludo, qué vamos a hacer hoy y qué vas a tener al final.
  2. Dónde estamos: el mapa de la arquitectura con lo hecho, lo de hoy y lo que falta.
  3. Teoría: solo lo que se usa en este video (escenas concepto / pasos / comparar / propias).
  4. Código: crear archivos (para qué sirve cada uno) → por archivo: ficha → clase → firmas de métodos
     → implementación LÍNEA POR LÍNEA mientras se escribe.
  5. Resultado: ejecutar y mostrarlo (consola / depurador / app). Ningún video termina sin resultado.
  6. Cierre: lo que logramos + qué viene en el próximo video.
"""
NOMBRE = "01-nombre-del-video"   # nombre del .mp4 en videos/
ETAPA = 1                        # el código termina igual que curso/01-*/


def guion(D, R):
    SlideHTML, CELESTE, VERDE, AMARILLO = R.SlideHTML, R.CELESTE, R.VERDE, R.AMARILLO
    D.set(mouse=(1500, 700))

    # ---------------------------------------------------------- 1. PORTADA
    D.capitulo("Introducción")
    D.slide(SlideHTML("portada", {
        "curso": R.CFG.CURSO, "num": ETAPA, "total": len(R.CFG.VIDEOS),
        "titulo": "Título del <span class='acento'>video</span>",
        "sub": "Una línea que dice de qué trata",
        "puntos": [["code", "Lo primero que haremos"], ["terminal", "Lo segundo"]],
        "resultado": "Lo que vas a ver funcionando al final", "icono": "terminal"}), frases=[
        "Hola, ¿qué tal? Bienvenidos al video uno del curso.",
        "Hoy vamos a ...",
        "Y al final de este video vas a tener ...",
    ])

    # ---------------------------------------------------------- 2. DÓNDE ESTAMOS
    # D.slide(SlideHTML("mapa", {"capas": CAPAS, "hechos": [...], "hoy": [...]}), frases=[...])

    # ---------------------------------------------------------- 3. TEORÍA
    # D.slide(SlideHTML("concepto", {"titulo": "...", "tarjetas": [[icono, titulo, texto, color]]}), frases=[...])

    # ---------------------------------------------------------- 4. CÓDIGO (línea por línea)
    D.abrir_proyecto(ETAPA - 1)                    # VS Code con el código del video anterior
    # D.nuevo_archivo("src/archivo.py")            # crear archivos diciendo para qué sirve cada uno
    # c = D.codigo("src/archivo.py", ETAPA)        # de cómo estaba a cómo queda en esta etapa
    # D.poner(c, c.rango("import", "import"), "Frase que explica estas líneas.", titulo="...", nota="...")
    # D.guardar(); D.terminar(c)                   # verifica que quedó igual a curso/NN-*/

    # ---------------------------------------------------------- 5. RESULTADO
    # D.depurar(); D.consola("lo que imprime el programa", app=True)

    # ---------------------------------------------------------- 6. CIERRE
    D.capitulo("Lo que sigue")
    D.slide(SlideHTML("siguiente", {
        "num": ETAPA, "logros": ["Lo que logramos 1", "Lo que logramos 2"],
        "sig": {"num": ETAPA + 1, "titulo": "Título del próximo video", "sub": "Qué vamos a hacer."}}), frases=[
        "Y listo. Hoy ...",
        "En el próximo video ... ¡Nos vemos!",
    ])
