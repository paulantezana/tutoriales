"""Configuración de UN curso. El motor (render.py y curso.py) lee todo lo propio del curso desde aquí.

Estructura de la carpeta del curso (la crea scripts/nuevo_curso.py):

    mi-curso/
      codigo/          el proyecto terminado (compila y pasa sus pruebas)
      curso/           el código al final de cada video: 01-nombre/, 02-nombre/ ...
      video/           este motor: render.py, curso.py, proyecto.py, escenas/, guiones/, plantilla/, marca/
"""

# ------------------------------------------------------------------ el curso
CURSO = "Curso de ejemplo"            # aparece en la portada: "<CURSO> · Video 2 de 9"
NOMBRE = "miapp"                      # carpeta del proyecto (en VS Code se ve en MAYÚSCULAS)
CODIGO_FINAL = "../codigo"            # el proyecto terminado, relativo a video/
CARPETA_ETAPAS = "../curso"           # curso/NN-nombre/ con el código al final de cada video

# Los videos del curso: (título, lo que se ve funcionando al final, ícono de Lucide)
VIDEOS = [
    ("Qué vamos a construir", "El proyecto corriendo", "monitor"),
    ("Primer paso", "El resultado en la consola", "terminal"),
]

# ------------------------------------------------------------------ el canal
CANAL = "Tu canal"
LOGO = "marca/logo.png"               # logo en la esquina (PNG con fondo transparente, cuadrado)
COLOR_MARCA = (19, 93, 188)           # color principal: etiquetas, bordes y la ficha del archivo
COLOR_ENFASIS = (252, 179, 51)        # color de las notas amarillas que explican el código

# ------------------------------------------------------------------ voz (Kokoro)
VOZ = "em_alex"                       # narrador. En español: em_alex, em_santa, ef_dora
VOZ_APP = "em_santa"                  # si la app habla (un asistente, por ejemplo)
VELOCIDAD = 1.0

# Pronunciación de los términos de ESTE curso (además de la base genérica de render.py).
# Se escriben como se leerían en español. Lo más largo se aplica primero.
PRONUNCIACION = [
    # ("mi_paquete", "mi paquete"),
    # ("Next.js", "next yei ese"),
]
PRONUNCIACION_EXACTA = set()          # términos que solo se reemplazan si coinciden mayúsculas y minúsculas
INGLES = {}                           # partes de nombres camelCase: {"todo": "tu du"}

# ------------------------------------------------------------------ VS Code y la terminal
RUTA_TERMINAL = "C:\\proyectos\\miapp"   # carpeta que muestra el prompt de PowerShell
DISPOSITIVO = None                    # texto de la barra de estado al depurar, ej. "Pixel 8 (android-arm64)"
CARPETAS_ABIERTAS = ["src"]           # carpetas desplegadas en el explorador al abrir el proyecto
SUGERENCIAS = []                      # palabras que ofrece el autocompletado (clases y funciones del curso)

# El proyecto recién creado (antes del video 1). Archivos con contenido real: ruta → archivo en plantilla/
ARCHIVOS_PLANTILLA = {
    # "src/main.py": "main.py",
}
ARCHIVOS_EXTRA = ["README.md", ".gitignore"]   # solo se ven en el explorador (vacíos)
CARPETAS = []                                  # carpetas sin archivos visibles (ej. "android", "node_modules")

# True: cada carpeta curso/NN-*/ trae TODOS los archivos que difieren de la plantilla.
# False: cada carpeta trae solo lo que cambió en ese video.
ETAPAS_COMPLETAS = True
QUITAR = {}                           # {ruta: video} archivos de la plantilla que se borran en ese video

# ------------------------------------------------------------------ ejecutar y depurar (F5)
# Mensajes de arranque en la Debug Console: (texto, segundos de pausa)
LANZAR = [
    ("Launching src\\main.py...", 0.8),
]
PREFIJO_APP = ""                      # lo que antepone la consola a cada print (Flutter: "I/flutter (24816): ")
RECARGA = None                        # línea del hot reload al guardar (None si el lenguaje no tiene)
REINICIO = "Restarted application."
FIN = "Process finished."

# ------------------------------------------------------------------ resultado de la app
REPLICA = "app.html"                  # réplica de la app en escenas/ (celular o web), manejada por eventos
# Páginas web REALES que se muestran en el navegador (se capturan con Chromium):
# id → (url, {clave: selector CSS})   La clave se usa en el guion: D.navegador_clic("instalar", ...)
PAGINAS = {
    # "npm_paquete": ("https://www.npmjs.com/package/express", {"titulo": "h1", "instalar": "code"}),
}
