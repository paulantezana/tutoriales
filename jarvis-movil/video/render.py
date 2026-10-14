"""
Video tutorial: "Crea tu propio YARBYS 100% en tu celular" — simulación de VS Code.

Simula a una persona programando en Visual Studio Code (explorador de archivos,
pestañas, autocompletado, terminal integrada, mouse, atajos de teclado) y
explica cada bloque de código para principiantes.

La narración se genera con la voz neuronal Kokoro (sin internet, en tu PC).

Uso:
    pip install pillow pygments kokoro-onnx soundfile playwright
    python render.py              # tutorial.mp4 + narracion.wav + subtitulos.srt + guion.md
    python render.py --preview 15 # una captura cada 15 s en video/preview/

Requiere ffmpeg, Chromium (para las escenas animadas y la página web) y los archivos
del modelo Kokoro en video/modelos/ (ver README).
El código se lee de ../yarbys, así que el video siempre coincide con el proyecto.
Las demos del celular usan escenas/app.html: una réplica visual de la app manejada por eventos.
"""
import copy
import json
import math
import multiprocessing as mp
import random
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pygments import lex
from pygments.lexers import (PythonLexer, YamlLexer, IniLexer, TextLexer, HtmlLexer, CssLexer, JavascriptLexer,
                             DartLexer, XmlLexer, KotlinLexer)
from pygments.token import Token

AQUI = Path(__file__).parent
CODIGO = AQUI.parent / "yarbys"
PLANTILLA = AQUI / "plantilla"     # archivos tal como los deja "flutter create"
W, H, FPS = 1920, 1080, 30

# ============================================================== MARCA DEL CANAL
# Cambia estos valores para adaptar el video al estilo de tu canal.
CANAL = "Paul Antezana"
LOGO = AQUI / "marca" / "logo.png"   # logo que aparece siempre en una esquina
MARCA = (19, 93, 188)        # azul del logo
MARCA2 = (252, 179, 51)      # naranja del logo
ESCENAS_HTML = AQUI / "escenas" / "escena.html"
APP_HTML = AQUI / "escenas" / "celular.html"
DEMOS = AQUI / "escenas" / "_demos"

# ============================================================== VOZ
VOZ = "em_alex"          # narrador. Voces en español de Kokoro: em_alex, ef_dora, em_santa
VOZ_YARBYS = "em_santa"  # la voz con la que YARBYS lee sus respuestas
VELOCIDAD = 1.0          # 1.1 = un poco más rápido
NARRACION = True         # False = video sin voz (solo subtítulos)
TECLADO = False          # True = sonido suave de teclado y clics del mouse
PAUSA_ENTRE_FRASES = 0.45

# ============================================================== FUENTES
INTER = "/usr/share/fonts/opentype/inter/"
DEJAVU = "/usr/share/fonts/truetype/dejavu/"


def fnt(path, size):
    return ImageFont.truetype(path, size)


F_UI = fnt(INTER + "Inter-Regular.otf", 18)
F_UI_B = fnt(INTER + "Inter-SemiBold.otf", 18)
F_UI_S = fnt(INTER + "Inter-Regular.otf", 16)
F_SYM = fnt(DEJAVU + "DejaVuSans.ttf", 17)
F_CODE = fnt(DEJAVU + "DejaVuSansMono.ttf", 24)
F_TERM = fnt(DEJAVU + "DejaVuSansMono.ttf", 22)
F_SUB = fnt(INTER + "Inter-Medium.otf", 34)
F_NOTE = fnt(INTER + "Inter-Medium.otf", 26)
F_NOTE_B = fnt(INTER + "Inter-Bold.otf", 26)
F_KEY = fnt(INTER + "Inter-SemiBold.otf", 30)
F_FICHA = fnt(INTER + "Inter-Medium.otf", 21)
F_FICHA_B = fnt(INTER + "Inter-Bold.otf", 25)
F_FICHA_T = fnt(INTER + "Inter-Bold.otf", 16)
F_FICHA_M = fnt(DEJAVU + "DejaVuSansMono-Bold.ttf", 21)
F_T1 = fnt(INTER + "InterDisplay-Bold.otf", 88)
F_T2 = fnt(INTER + "InterDisplay-Bold.otf", 62)
F_H = fnt(INTER + "Inter-SemiBold.otf", 38)
F_B = fnt(INTER + "Inter-Medium.otf", 36)
F_S = fnt(INTER + "Inter-Medium.otf", 28)
F_XS = fnt(INTER + "Inter-Regular.otf", 23)

CW = F_CODE.getlength("M")
LH = 35
TCW = F_TERM.getlength("M")
TLH = 31

# ============================================================== COLORES VS CODE (Dark Modern)
C_BG = (31, 31, 31)
C_SIDE = (24, 24, 24)
C_BORDER = (43, 43, 43)
C_TEXT = (204, 204, 204)
C_MUTED = (157, 157, 157)
C_LINENO = (110, 118, 129)
C_SEL = (38, 79, 120)
C_CURLINE = (40, 40, 40)
C_BLUE = (0, 120, 212)
C_TERM_BG = (24, 24, 24)

SYN_DEF = (212, 212, 212)
SYN = {
    "kw_ctrl": (197, 134, 192),
    "kw": (86, 156, 214),
    "str": (206, 145, 120),
    "fn": (220, 220, 170),
    "cls": (78, 201, 176),
    "var": (156, 220, 254),
    "num": (181, 206, 168),
    "com": (106, 153, 85),
    "op": (212, 212, 212),
    "esc": (215, 186, 125),
}
BRACKETS = [(255, 215, 0), (218, 112, 214), (23, 159, 255)]

# Atajos del terminal
G = (35, 209, 139)     # verde de bash
B_ = (59, 142, 234)    # azul de bash
Y = (229, 229, 16)
GRIS = (140, 140, 140)
BLANCO = (229, 229, 229)
CIAN = (41, 184, 219)
ROJO = (241, 76, 76)


DUR_VOZ = {}  # (voz, frase) -> segundos de audio generado


def duracion_frase(texto, voz=None):
    voz = voz or VOZ
    if (voz, texto) in DUR_VOZ:
        return DUR_VOZ[(voz, texto)] + PAUSA_ENTRE_FRASES
    return max(2.4, len(texto) / 14.0)


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = max(0.0, min(1.0, x))
    return 3 * x * x - 2 * x * x * x


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def wrap(texto, font, ancho):
    out = []
    for parrafo in texto.split("\n"):
        linea = ""
        for p in parrafo.split(" "):
            prueba = (linea + " " + p).strip() if linea else p
            if font.getlength(prueba) <= ancho:
                linea = prueba
            else:
                if linea:
                    out.append(linea)
                linea = p
        out.append(linea)
    return out


# ============================================================== RESALTADO DE SINTAXIS
PY_CTRL = {"import", "from", "return", "if", "else", "elif", "while", "for", "in",
           "break", "continue", "try", "except", "with", "as", "not", "and", "or"}
DART_CTRL = {"import", "export", "return", "if", "else", "for", "in", "while", "switch", "case", "try", "catch",
             "finally", "await", "async", "yield", "throw", "break", "continue", "as", "is"}
DART_TIPOS = {"String", "int", "double", "bool", "void", "dynamic", "List", "Map", "Set", "Future", "Stream",
              "Duration", "Object", "num"}


@lru_cache(maxsize=64)
def colorear(nombre, texto):
    """Devuelve una lista de líneas; cada línea es lista de (texto, color)."""
    ext = nombre.rsplit(".", 1)[-1] if "." in nombre else ""
    if nombre.endswith(".py"):
        lexer = PythonLexer(stripnl=False)
    elif ext in ("yml", "yaml"):
        lexer = YamlLexer(stripnl=False)
    elif nombre.endswith(".env"):
        lexer = IniLexer(stripnl=False)
    elif ext == "html":
        lexer = HtmlLexer(stripnl=False)
    elif ext == "css":
        lexer = CssLexer(stripnl=False)
    elif ext == "js":
        lexer = JavascriptLexer(stripnl=False)
    elif ext == "dart":
        lexer = DartLexer(stripnl=False)
    elif ext == "xml":
        lexer = XmlLexer(stripnl=False)
    elif ext == "kts":
        lexer = KotlinLexer(stripnl=False)
    else:
        lexer = TextLexer(stripnl=False)
    toks = list(lex(texto, lexer))
    if toks and toks[-1][1] == "\n" and not texto.endswith("\n"):
        toks.pop()
    salida, profundidad = [], 0
    for i, (tok, val) in enumerate(toks):
        col = SYN_DEF
        if nombre.endswith(".py"):
            if tok in Token.Keyword:
                col = SYN["kw_ctrl"] if val in PY_CTRL else SYN["kw"]
            elif tok in Token.Name.Builtin.Pseudo:
                col = SYN["kw"]
            elif tok in Token.Literal.String.Affix or tok in Token.Literal.String.Interpol:
                col = SYN["kw"]
            elif tok in Token.Literal.String.Escape:
                col = SYN["esc"]
            elif tok in Token.Literal.String:
                col = SYN["str"]
            elif tok in Token.Comment:
                col = SYN["com"]
            elif tok in Token.Literal.Number:
                col = SYN["num"]
            elif tok in Token.Name.Namespace or tok in Token.Name.Class:
                col = SYN["cls"]
            elif tok in Token.Name.Function or tok in Token.Name.Builtin:
                col = SYN["fn"]
            elif tok in Token.Name:
                sig = next((v for _, v in toks[i + 1:i + 3] if v.strip()), "")
                if sig.startswith("("):
                    col = SYN["cls"] if val[:1].isupper() else SYN["fn"]
                elif val[:1].isupper() and not val.isupper():
                    col = SYN["cls"]
                else:
                    col = SYN["var"]
            elif tok in Token.Punctuation and val in "()[]{}":
                if val in "([{":
                    col = BRACKETS[profundidad % 3]
                    profundidad += 1
                else:
                    profundidad = max(0, profundidad - 1)
                    col = BRACKETS[profundidad % 3]
        elif ext in ("yml", "yaml"):
            if tok in Token.Name.Tag:
                col = SYN["kw"]
            elif tok in Token.Literal.String or tok in Token.Literal.Scalar:
                col = SYN["str"]
            elif tok in Token.Comment:
                col = SYN["com"]
            elif tok in Token.Literal.Number:
                col = SYN["num"]
            elif tok in Token.Punctuation:
                col = SYN_DEF
            else:
                col = SYN["str"]
        elif ext == "html":
            if tok in Token.Comment:
                col = SYN["com"]
            elif tok in Token.Name.Tag:
                col = SYN["kw"]
            elif tok in Token.Name.Attribute:
                col = SYN["var"]
            elif tok in Token.Literal.String:
                col = SYN["str"]
            elif tok in Token.Punctuation or val in ("<", ">", "</", "/>"):
                col = (128, 128, 128)
        elif ext == "css":
            if tok in Token.Comment:
                col = SYN["com"]
            elif tok in Token.Keyword or (tok in Token.Name.Variable):
                col = SYN["var"]
            elif tok in Token.Name.Class or tok in Token.Name.Tag or tok in Token.Name.Decorator or tok in Token.Name.Function and val.startswith("."):
                col = (215, 186, 125)
            elif tok in Token.Literal.Number:
                col = SYN["num"]
            elif tok in Token.Literal.String or tok in Token.Keyword.Constant:
                col = SYN["str"]
            elif tok in Token.Name.Builtin or tok in Token.Name.Function:
                col = SYN["fn"]
            elif tok in Token.Name.Constant or tok in Token.Name:
                col = SYN["str"]
        elif ext == "js":
            if tok in Token.Comment:
                col = SYN["com"]
            elif tok in Token.Keyword:
                col = SYN["kw_ctrl"] if val in ("if", "else", "return", "await", "try", "catch", "for", "while") else SYN["kw"]
            elif tok in Token.Literal.String:
                col = SYN["str"]
            elif tok in Token.Literal.Number:
                col = SYN["num"]
            elif tok in Token.Name.Builtin or tok in Token.Name.Other or tok in Token.Name:
                sig = next((v for _, v in toks[i + 1:i + 3] if v.strip()), "")
                col = SYN["fn"] if sig.startswith("(") else (SYN["cls"] if val[:1].isupper() else SYN["var"])
            elif tok in Token.Punctuation and val in "()[]{}":
                if val in "([{":
                    col = BRACKETS[profundidad % 3]
                    profundidad += 1
                else:
                    profundidad = max(0, profundidad - 1)
                    col = BRACKETS[profundidad % 3]
        elif ext in ("dart", "kts"):
            if tok in Token.Comment:
                col = SYN["com"]
            elif tok in Token.Literal.String.Interpol:
                col = SYN["kw"]
            elif tok in Token.Literal.String.Escape:
                col = SYN["esc"]
            elif tok in Token.Literal.String:
                col = SYN["str"]
            elif tok in Token.Literal.Number:
                col = SYN["num"]
            elif tok in Token.Keyword.Type or (tok in Token.Name and val in DART_TIPOS):
                col = SYN["cls"]
            elif tok in Token.Keyword:
                col = SYN["kw_ctrl"] if val in DART_CTRL else SYN["kw"]
            elif tok in Token.Name.Builtin.Pseudo or val in ("this", "super", "null", "true", "false"):
                col = SYN["kw"]
            elif tok in Token.Name:
                sig = next((v for _, v in toks[i + 1:i + 3] if v.strip()), "")
                if val[:1].isupper() and not val.isupper():
                    col = SYN["cls"]
                elif sig.startswith("(") or sig.startswith("<"):
                    col = SYN["fn"]
                else:
                    col = SYN["var"]
            elif tok in Token.Punctuation and val in "()[]{}":
                if val in "([{":
                    col = BRACKETS[profundidad % 3]
                    profundidad += 1
                else:
                    profundidad = max(0, profundidad - 1)
                    col = BRACKETS[profundidad % 3]
        elif ext == "xml":
            if tok in Token.Comment:
                col = SYN["com"]
            elif tok in Token.Name.Tag:
                col = SYN["kw"]
            elif tok in Token.Name.Attribute:
                col = SYN["var"]
            elif tok in Token.Literal.String:
                col = SYN["str"]
            elif tok in Token.Punctuation:
                col = (128, 128, 128)
        elif nombre.endswith(".env"):
            if tok in Token.Comment:
                col = SYN["com"]
            elif tok in Token.Name.Attribute or tok in Token.Name:
                col = SYN["var"]
            elif tok in Token.Literal.String:
                col = SYN["str"]
            elif tok in Token.Operator:
                col = SYN_DEF
        salida.append((val, col))
    lineas, actual = [], []
    for val, col in salida:
        partes = val.split("\n")
        for j, p in enumerate(partes):
            if p:
                if actual and actual[-1][1] == col:
                    actual[-1] = (actual[-1][0] + p, col)
                else:
                    actual.append((p, col))
            if j < len(partes) - 1:
                lineas.append(actual)
                actual = []
    lineas.append(actual)
    return lineas


# ============================================================== ESTADO
class Estado:
    def __init__(self):
        self.files = {}            # ruta -> texto
        self.carpetas = set()      # carpetas sin archivos visibles (p.ej. android, ios)
        self.abiertas = frozenset()  # carpetas desplegadas en el explorador
        self.raiz = "PROYECTOS"    # carpeta abierta en VS Code
        self.tabs = ()
        self.activo = None
        self.sucios = frozenset()  # archivos sin guardar
        self.cursor = (0, 0)
        self.scroll = {}           # ruta -> primera línea visible
        self.sel = None            # (l1, l2) 0-based
        self.nota = None           # (titulo, texto)
        self.input_explorer = None
        self.foco = "editor"
        self.popup = None          # (items, palabra, linea, col)
        self.term_abierto = False
        self.term_alto = 400
        self.term_lineas = ()      # tuplas de segmentos
        self.term_actual = ()      # segmentos de la línea en curso
        self.term_tabs = ()        # nombres de las terminales abiertas
        self.term_activa = 0
        self.navegador = None      # (url, contenido) ; contenido = ("demo", seg, k) | ("cargando", t)
        self.tecla = None
        self.subtitulo = ""
        self.slide = None          # (objeto, t, dur)
        self.mouse = (1200, 600)
        self.click = 0.0
        self.fundido = 1.0
        self.capitulo = ""
        self.ocultar_mouse = False
        self.ficha = None          # (titulo, descripcion, elementos, activo, hechos): el mapa del archivo
        self.rapido = None         # "x4" mientras el tecleo va acelerado
        self.panel = "terminal"    # pestaña del panel de abajo: "terminal" o "debug"
        self.consola = ()          # líneas de la DEBUG CONSOLE: (texto, color)
        self.depurando = False     # la app corre con F5 (barra de estado naranja)
        self.punto = None          # (ruta, línea) del punto de parada (círculo rojo)
        self.pausa = None          # (ruta, línea) donde está detenida la app
        self.hover = None          # (línea, columna, nombre, valor) del globo con el valor


# ============================================================== ESCENARIO / DIRECTOR
# Posiciones fijas de la interfaz
TITLE_H, TABS_H, BREAD_H, STATUS_H = 38, 46, 30, 30
ACT_W, SIDE_W = 56, 330
ED_X = ACT_W + SIDE_W
ED_Y = TITLE_H + TABS_H + BREAD_H
GUTTER = 74
MINIMAP = 110
BTN_NUEVO = (ED_X - 112, TITLE_H + 52)      # icono "New File" del explorador
BTN_MAX = (W - 98, None)                     # maximizar panel (y depende del panel)


def editor_bottom(s):
    return H - STATUS_H - (s.term_alto if s.term_abierto else 0)


def lineas_visibles(s):
    return max(0, int((editor_bottom(s) - ED_Y - 10) // LH))


class Director:
    def __init__(self, seed=7):
        self.s = Estado()
        self.frames = []
        self.cambio = True
        self.snap = None
        self.rnd = random.Random(seed)
        self.say_hasta = 0.0
        self.sub_fin = None
        self.log = []          # (inicio, fin, texto, capitulo)
        self.capitulos = []
        self.tecla_hasta = -1
        self.sonidos = []      # (segundo, "tecla" | "clic")
        self.estado_terminales = {}
        self.log_yarbys = []   # (segundo, texto) que YARBYS dice en voz alta
        self.pos = None        # dónde se escribe (índice en el texto); None = al final
        self.acel = None       # aceleración del tecleo en curso (None = no hay tecleo)
        self._deuda = 0.0      # fracción de fotograma pendiente al teclear acelerado
        self.demos_app = []    # demos del celular (escenas/app.html)
        self.log_usuario = []  # (segundo, texto) que la persona le dice a YARBYS

    # ---------- tiempo
    @property
    def t(self):
        return len(self.frames) / FPS

    def set(self, **kw):
        for k, v in kw.items():
            setattr(self.s, k, v)
        self.cambio = True

    def emit(self, n=1):
        for _ in range(max(0, int(n))):
            ahora = self.t
            if self.s.subtitulo and self.sub_fin is not None and ahora >= self.sub_fin:
                self.set(subtitulo="")
            if self.s.tecla and len(self.frames) >= self.tecla_hasta:
                self.set(tecla=None)
            if self.s.click > 0:
                self.set(click=max(0.0, self.s.click - 0.12))
            if self.cambio or self.snap is None:
                self.snap = copy.copy(self.s)
                self.cambio = False
            self.frames.append(self.snap)

    def wait(self, seg):
        self.emit(round(seg * FPS))

    # ---------- narración
    def say(self, texto, esperar=False):
        self.hold()
        if self.log and self.log[-1][1] is None:
            self.log[-1][1] = self.t
        lectura = duracion_frase(texto)
        self.say_hasta = self.t + lectura
        self.sub_fin = self.t + lectura + 1.2
        self.log.append([self.t, None, texto, self.s.capitulo])
        self.set(subtitulo=texto)
        if esperar:
            self.hold()

    def hold(self):
        if self.t < self.say_hasta:
            self.wait(self.say_hasta - self.t)

    def explicar(self, *frases):
        for f in frases:
            self.say(f, esperar=True)

    def capitulo(self, nombre):
        self.set(capitulo=nombre)
        self.capitulos.append((self.t, nombre))

    def cerrar_log(self):
        for e in self.log:
            if e[1] is None:
                e[1] = self.t
        for i, e in enumerate(self.log):
            fin_lectura = e[0] + duracion_frase(e[2]) + 1.2
            e[1] = min(e[1], fin_lectura)

    # ---------- mouse y teclado
    def mover(self, x, y, dur=None):
        x0, y0 = self.s.mouse
        dist = math.hypot(x - x0, y - y0)
        dur = dur or min(0.9, 0.25 + dist / 2200)
        n = max(1, round(dur * FPS))
        for i in range(1, n + 1):
            a = ease_io(i / n)
            self.set(mouse=(x0 + (x - x0) * a, y0 + (y - y0) * a))
            self.emit()

    def clic(self, x=None, y=None):
        if x is not None:
            self.mover(x, y)
        self.wait(0.08)
        self.sonidos.append((self.t, "clic"))
        self.set(click=1.0)
        self.wait(0.25)

    def atajo(self, texto, dur=1.3):
        self.sonidos.append((self.t, "tecla"))
        self.set(tecla=texto)
        self.tecla_hasta = len(self.frames) + round(dur * FPS)

    # ---------- editor
    def texto(self):
        return self.s.files[self.s.activo]

    def _poner_texto(self, nuevo, cursor):
        f = dict(self.s.files)
        f[self.s.activo] = nuevo
        self.set(files=f, cursor=cursor, sucios=self.s.sucios | {self.s.activo})
        self._ajustar_scroll()

    def _ajustar_scroll(self):
        vis = lineas_visibles(self.s)
        top = self.s.scroll.get(self.s.activo, 0)
        lin = self.s.cursor[0]
        if lin > top + vis - 4:
            top = lin - vis + 4
        if lin < top + 1:
            top = max(0, lin - 1)
        if top != self.s.scroll.get(self.s.activo, 0):
            sc = dict(self.s.scroll)
            sc[self.s.activo] = top
            self.set(scroll=sc)

    @staticmethod
    def _cursor_de(txt, pos):
        antes = txt[:pos].split("\n")
        return (len(antes) - 1, len(antes[-1]))

    def _linea_actual(self):
        txt = self.texto()
        pos = len(txt) if self.pos is None else self.pos
        return txt[:pos].split("\n")[-1]

    def _insertar(self, ch):
        self.sonidos.append((self.t, "tecla"))
        txt = self.texto()
        pos = len(txt) if self.pos is None else self.pos   # None = al final del archivo
        nuevo = txt[:pos] + ch + txt[pos:]
        if self.pos is not None:
            self.pos += len(ch)
        self._poner_texto(nuevo, self._cursor_de(nuevo, pos + len(ch)))

    def _borrar(self):
        txt = self.texto()
        pos = len(txt) if self.pos is None else self.pos
        nuevo = txt[:pos - 1] + txt[pos:]
        if self.pos is not None:
            self.pos -= 1
        self._poner_texto(nuevo, self._cursor_de(nuevo, pos - 1))

    LIMITE_TECLEO = 8.0   # segundos de tecleo sin voz; si un bloque tarda más, se acelera (⏩)

    def _empezar_tecleo(self, texto, cps):
        """Calcula cuánto acelerar el tecleo para no dejar más de LIMITE_TECLEO segundos sin voz."""
        estimado = len(texto) * 1.05 / cps + texto.count("\n") * 0.24
        voz = max(0.0, self.say_hasta - self.t)
        self.acel = max(1.0, estimado / (voz + self.LIMITE_TECLEO))
        self._deuda = 0.0
        if self.acel >= 1.5:
            self.set(rapido=f"x{round(self.acel)}")

    def _terminar_tecleo(self):
        if self._deuda >= 0.5:
            self.emit(1)
        self.acel = None
        self._deuda = 0.0
        self.set(rapido=None)

    def _avanzar(self, fotogramas):
        """Emite fotogramas del tecleo; acelerado puede juntar varias teclas en un solo fotograma."""
        self._deuda += fotogramas / (self.acel or 1.0)
        n = int(self._deuda)
        self._deuda -= n
        self.emit(n)

    def escribir(self, texto, cps=17, errores=True, autocompletar=True):
        """Teclea como una persona: velocidad variable, sangría automática,
        algún error corregido y autocompletado en palabras largas."""
        propio = self.acel is None
        if propio:
            self._empezar_tecleo(texto, cps)
        if self.acel > 2:          # a toda velocidad no hay tiempo para errores ni sugerencias
            errores = autocompletar = False
        r = self.rnd
        i = 0
        palabras_vistas = set(re.findall(r"[A-Za-z_]\w{6,}", self.texto()))
        while i < len(texto):
            ch = texto[i]
            linea_actual = self._linea_actual()
            # sangría automática: los espacios del inicio aparecen de golpe
            if ch == " " and linea_actual.strip() == "":
                j = i
                while j < len(texto) and texto[j] == " ":
                    j += 1
                for c in texto[i:j]:
                    self._insertar(c)
                self._avanzar(1)
                i = j
                continue
            # autocompletado en identificadores largos
            m = re.match(r"[A-Za-z_]\w*", texto[i:])
            if (autocompletar and m and len(m.group()) >= 9
                    and (i == 0 or not (texto[i - 1].isalnum() or texto[i - 1] == "_"))
                    and r.random() < 0.7):
                palabra = m.group()
                k = 3 if palabra in palabras_vistas else 4
                for c in palabra[:k]:
                    self._insertar(c)
                    self._avanzar(max(1, round(FPS / cps * r.uniform(0.7, 1.4))))
                lin, col = self.s.cursor
                otras = sorted({p for p in palabras_vistas | SUGERENCIAS
                                if p.startswith(palabra[:k]) and p != palabra})[:4]
                self.set(popup=((palabra,) + tuple(otras), palabra, lin, col - k))
                self._avanzar(FPS * r.uniform(0.35, 0.6))
                for c in palabra[k:]:
                    self._insertar(c)
                self.set(popup=None)
                self._avanzar(2)
                palabras_vistas.add(palabra)
                i += len(palabra)
                continue
            # pequeño error de tipeo que se corrige
            if errores and ch.isalpha() and r.random() < 1 / 140:
                self._insertar(r.choice("asdfjklqwertyuio"))
                self.wait(0.12)
                self.wait(r.uniform(0.25, 0.45))
                self._borrar()
                self.wait(0.12)
            self._insertar(ch)
            if m:
                palabras_vistas.add(m.group())
            espera = FPS / cps * r.uniform(0.6, 1.5)
            if ch == "\n":
                espera += FPS * r.uniform(0.12, 0.35)
            elif ch in ",:)":
                espera += FPS * 0.05
            self._avanzar(max(1, round(espera)))
            i += 1
        if propio:
            self._terminar_tecleo()

    def pegar(self, texto):
        """Pega un bloque de código de una vez (Ctrl + V)."""
        self.atajo("Ctrl + V")
        self.wait(0.2)
        txt = self.texto()
        pos = len(txt) if self.pos is None else self.pos
        nuevo = txt[:pos] + texto + txt[pos:]
        if self.pos is not None:
            self.pos += len(texto)
        self.sonidos.append((self.t, "tecla"))
        self._poner_texto(nuevo, self._cursor_de(nuevo, pos + len(texto)))
        self.wait(0.6)

    def guardar(self):
        self.atajo("Ctrl + S")
        self.wait(0.3)
        self.set(sucios=self.s.sucios - {self.s.activo})
        self.wait(0.5)

    def nuevo_archivo(self, ruta):
        self.set(foco="explorer")
        self.mover(ED_X - 160, TITLE_H + 52, 0.5)
        self.clic(*BTN_NUEVO)
        self.set(input_explorer="")
        self.wait(0.3)
        for c in ruta:
            self.sonidos.append((self.t, "tecla"))
            self.set(input_explorer=self.s.input_explorer + c)
            self.emit(max(1, round(FPS / 11 * self.rnd.uniform(0.6, 1.4))))
        self.wait(0.3)
        self.atajo("Enter", 0.8)
        f = dict(self.s.files)
        f[ruta] = ""
        partes = ruta.split("/")
        self.set(abiertas=self.s.abiertas | {"/".join(partes[:k]) for k in range(1, len(partes))})
        tabs = self.s.tabs + (ruta,)
        if len(tabs) > 6:            # cierra las pestañas más viejas, como haría una persona
            tabs = tabs[-6:]
        self.set(files=f, input_explorer=None, tabs=tabs, activo=ruta,
                 cursor=(0, 0), foco="editor", sel=None)
        self.mover(ED_X + 500, ED_Y + 200, 0.5)
        self.wait(0.4)

    def abrir(self, ruta):
        self.set(activo=ruta, foco="editor", sel=None)
        lineas = self.texto().split("\n")
        self.set(cursor=(len(lineas) - 1, len(lineas[-1])))

    def buscar_lineas(self, desde, hasta=None):
        lineas = self.texto().split("\n")
        a = next(i for i, l in enumerate(lineas) if desde in l)
        if hasta is None:
            return a, a
        b = next(i for i, l in enumerate(lineas) if i >= a and hasta in l)
        return a, b

    def resaltar(self, desde, hasta=None, nota=None, titulo=None, frases=()):
        """Selecciona líneas con el mouse, muestra una nota y explica."""
        a, b = self.buscar_lineas(desde, hasta)
        top = self.s.scroll.get(self.s.activo, 0)
        vis = lineas_visibles(self.s)
        if a < top or b >= top + vis - 3:
            sc = dict(self.s.scroll)
            sc[self.s.activo] = max(0, min(a - 2, len(self.texto().split("\n")) - vis + 3))
            self.set(scroll=sc)
            top = sc[self.s.activo]
        y = ED_Y + (a - top) * LH + LH / 2
        self.mover(ED_X + GUTTER + 30, y, 0.5)
        self.wait(0.15)
        n = b - a + 1
        pasos = max(1, min(n, 10))
        for k in range(1, pasos + 1):
            fin = a + round((n - 1) * k / pasos)
            self.set(sel=(a, fin),
                     mouse=(ED_X + GUTTER + 30 + 260, ED_Y + (fin - top) * LH + LH / 2))
            self.emit(2)
        if nota or titulo:
            self.set(nota=(titulo, nota or ""))
        for f in frases:
            self.say(f, esperar=True)
        self.wait(0.4)
        self.set(sel=None, nota=None)
        txt = self.texto()
        self.set(cursor=self._cursor_de(txt, len(txt) if self.pos is None else self.pos))
        self._ajustar_scroll()
        self.mover(ED_X + 700, editor_bottom(self.s) - 140, 0.5)

    # ---------- edición en medio del archivo
    def _mostrar_linea(self, lin):
        top = self.s.scroll.get(self.s.activo, 0)
        vis = lineas_visibles(self.s)
        if lin < top + 1 or lin > top + vis - 4:
            sc = dict(self.s.scroll)
            sc[self.s.activo] = max(0, lin - vis // 2)
            self.set(scroll=sc)
        return self.s.scroll.get(self.s.activo, 0)

    def ir_a(self, ancla):
        """Hace clic al final de la línea que contiene 'ancla' (ahí se seguirá escribiendo)."""
        txt = self.texto()
        i = txt.index(ancla)
        fin = txt.find("\n", i)
        fin = len(txt) if fin < 0 else fin
        lin, col = self._cursor_de(txt, fin)
        top = self._mostrar_linea(lin)
        self.clic(ED_X + GUTTER + col * CW + 12, ED_Y + (lin - top) * LH + LH / 2)
        self.pos = fin
        self.set(cursor=(lin, col), foco="editor", sel=None)
        self.wait(0.2)

    def insertar_debajo(self, ancla, texto, cps=17):
        """Agrega líneas nuevas debajo de la línea que contiene 'ancla'."""
        self.ir_a(ancla)
        self.atajo("End", 0.6)
        self.escribir("\n" + texto, cps)
        self.pos = None

    def reemplazar(self, viejo, nuevo, cps=17):
        """Selecciona un texto con el mouse, lo borra y escribe el nuevo en su lugar."""
        txt = self.texto()
        i = txt.index(viejo)
        la, ca = self._cursor_de(txt, i)
        lb, _ = self._cursor_de(txt, i + len(viejo))
        top = self._mostrar_linea(la)
        self.mover(ED_X + GUTTER + ca * CW + 6, ED_Y + (la - top) * LH + LH / 2, 0.5)
        self.set(sel=(la, lb))
        self.wait(0.6)
        self.atajo("Delete", 0.6)
        nuevo_txt = txt[:i] + txt[i + len(viejo):]
        self.pos = i
        self.set(sel=None)
        self._poner_texto(nuevo_txt, (la, ca))
        self.wait(0.3)
        self.escribir(nuevo, cps)
        self.pos = None

    def borrar_todo(self):
        """Ctrl + A y Suprimir: deja el archivo vacío."""
        n = len(self.texto().split("\n"))
        self.atajo("Ctrl + A", 0.8)
        self.set(sel=(0, n - 1))
        self.wait(0.6)
        self.atajo("Delete", 0.6)
        self.set(sel=None, scroll={**self.s.scroll, self.s.activo: 0})
        self._poner_texto("", (0, 0))
        self.wait(0.4)

    def abrir_desde_explorador(self, ruta):
        """Despliega las carpetas, hace clic en el archivo y lo abre en una pestaña."""
        partes = ruta.split("/")
        self.set(abiertas=self.s.abiertas | {"/".join(partes[:k]) for k in range(1, len(partes))}, foco="explorer")
        items = arbol(self.s)
        idx = next(k for k, it in enumerate(items) if it[2] == ruta)
        y = TITLE_H + 70 + idx * 28 + 12
        self.clic(ACT_W + 110 + len(partes) * 18, y)
        tabs = self.s.tabs if ruta in self.s.tabs else (self.s.tabs + (ruta,))[-6:]
        self.set(tabs=tabs, activo=ruta, foco="editor", sel=None, cursor=(0, 0))
        self.wait(0.4)

    def verificar(self, ruta):
        """El video debe terminar con el mismo archivo que hay en el proyecto."""
        esperado = leer(ruta)
        assert self.s.files[ruta] == esperado, f"{ruta} no coincide con el proyecto"

    # ---------- el mapa del archivo (ficha a la derecha del editor)
    def ficha(self, titulo, descripcion, elementos):
        """Muestra qué hay dentro del archivo: elementos = [(tipo, nombre, explicación), ...]."""
        self.ficha_datos = (titulo, descripcion, tuple(elementos))
        self.ficha_hechos = frozenset()
        self.set(ficha=(titulo, descripcion, tuple(elementos), None, self.ficha_hechos))

    def ficha_ver(self, activo=None):
        t, d, e = self.ficha_datos
        self.set(ficha=(t, d, e, activo, self.ficha_hechos))

    def ficha_hecho(self, k):
        self.ficha_hechos = self.ficha_hechos | {k}
        if self.s.ficha:
            self.ficha_ver(self.s.ficha[3])

    def ficha_ocultar(self):
        self.set(ficha=None)

    def ficha_explicar(self, k, frase, firma=None):
        """Resalta el elemento k de la ficha (y su línea en el código) mientras se explica."""
        self.ficha_ver(k)
        if firma:
            a, b = self.buscar_lineas(firma)
            top = self._mostrar_linea(a)
            self.mover(ED_X + GUTTER + 30, ED_Y + (a - top) * LH + LH / 2, 0.45)
            self.set(sel=(a, b))
        self.say(frase, esperar=True)
        self.set(sel=None)

    # ---------- escribir un archivo por partes: primero el esqueleto, luego cada método
    def escribir_codigo(self, texto, cps=19):
        """Teclea código; las direcciones web no se teclean: se pegan (Ctrl + V)."""
        trozos = re.split(r"(https?://[^'\"\s]+)", texto)
        self._empezar_tecleo("".join(trozos[0::2]), cps)
        for k, trozo in enumerate(trozos):
            if not trozo:
                continue
            if k % 2:
                acel, self.acel = self.acel, None
                self.set(rapido=None)
                self.wait(0.3)
                self.pegar(trozo)
                self.acel = acel
                if acel >= 1.5:
                    self.set(rapido=f"x{round(acel)}")
            else:
                self.escribir(trozo, cps)
        self._terminar_tecleo()

    # ---------- navegador (páginas reales capturadas con Chromium)
    def navegador_abrir(self):
        self.atajo("Alt + Tab", 0.8)
        self.set(navegador=("", ("vacia",)), foco="url", ocultar_mouse=False)
        self.wait(0.6)

    def _pagina(self, url_texto, pagina, scroll=0, extra=None):
        self.set(navegador=(url_texto, ("pagina", pagina, scroll, extra)))

    def _cargar(self, url_texto, pagina, seg=0.9):
        n = round(seg * FPS)
        for i in range(n):
            self.set(navegador=(url_texto, ("cargando", i / max(1, n - 1))))
            self.emit()
        self._pagina(url_texto, pagina)
        self.wait(0.3)

    def navegador_ir(self, url_texto, pagina):
        """Escribe la dirección en la barra y abre la página."""
        self.mover(700, 62, 0.4)
        self.clic()
        self.set(navegador=("", self.s.navegador[1]), foco="url")
        for c in url_texto:
            self.set(navegador=(self.s.navegador[0] + c, self.s.navegador[1]))
            self.emit(max(1, round(FPS / 15 * self.rnd.uniform(0.6, 1.4))))
        self.wait(0.3)
        self.atajo("Enter", 0.8)
        self.set(foco="pagina")
        self._cargar(url_texto, pagina)

    def _centro(self, pagina, clave):
        x, y, w, h = PAGINAS_CAJAS[pagina][clave]
        scroll = self.s.navegador[1][2] if self.s.navegador[1][0] == "pagina" else 0
        return x + w / 2, NAV_TOP + y + h / 2 - scroll

    def navegador_escribir(self, clave, texto):
        """Hace clic en un campo de la página y escribe en él."""
        url, (tipo, pagina, scroll, _) = self.s.navegador
        self.clic(*self._centro(pagina, clave))
        for i in range(1, len(texto) + 1):
            self._pagina(url, pagina, scroll, (clave, texto[:i]))
            self.emit(max(1, round(FPS / 13 * self.rnd.uniform(0.6, 1.4))))
        self.wait(0.3)

    def navegador_clic(self, clave, url_nueva=None, pagina_nueva=None, mover=0.6):
        url, (tipo, pagina, scroll, extra) = self.s.navegador
        self.mover(*self._centro(pagina, clave), mover)
        self.wait(0.2)
        self.clic()
        if pagina_nueva:
            self._cargar(url_nueva, pagina_nueva)

    def navegador_enter(self, url_nueva, pagina_nueva):
        self.atajo("Enter", 0.8)
        self._cargar(url_nueva, pagina_nueva)

    def navegador_desplazar(self, hasta, dur=1.2):
        """Desplaza la página (rueda del mouse) hasta que 'hasta' (px o clave) quede arriba."""
        url, (tipo, pagina, scroll, extra) = self.s.navegador
        if isinstance(hasta, str):
            hasta = max(0, PAGINAS_CAJAS[pagina][hasta][1] - 140)
        alto = PAGINAS_CAJAS[pagina]["_alto"]
        hasta = max(0, min(hasta, alto - (H - NAV_TOP)))
        n = max(1, round(dur * FPS))
        for i in range(1, n + 1):
            self._pagina(url, pagina, round(scroll + (hasta - scroll) * ease_io(i / n)), extra)
            self.emit()

    def navegador_marcar(self, clave, seg=1.5):
        """Recuadro amarillo alrededor de un elemento de la página."""
        url, (tipo, pagina, scroll, extra) = self.s.navegador
        self._pagina(url, pagina, scroll, ("marco", clave))
        self.wait(seg)

    def navegador_cerrar(self):
        self.atajo("Alt + Tab", 0.8)
        self.set(navegador=None, foco="editor")
        self.wait(0.4)

    # ---------- terminal
    venv_activo = False
    cwd = "C:\\proyectos"

    def prompt(self):
        venv = (("(.venv) ", G),) if self.venv_activo else ()
        return venv + ((f"PS {self.cwd}> ", BLANCO),)

    def abrir_terminal(self):
        self.atajo("Ctrl + `")
        self.set(term_abierto=True, foco="terminal", term_actual=self.prompt(),
                 term_tabs=("powershell",), term_activa=0)
        self._ajustar_scroll()
        self.wait(0.6)

    def nueva_terminal(self, nombre="powershell"):
        """Abre otra terminal (Ctrl + Shift + `) y la deja activa."""
        self.atajo("Ctrl + Shift + `")
        self._guardar_terminal()
        idx = len(self.s.term_tabs)
        self.estado_terminales[idx] = ((), None, False, self.cwd)
        self.set(term_tabs=self.s.term_tabs + (nombre,))
        self._cargar_terminal(idx)
        self.wait(0.5)

    def _guardar_terminal(self):
        self.estado_terminales[self.s.term_activa] = (self.s.term_lineas, self.s.term_actual,
                                                      self.venv_activo, self.cwd)

    def _cargar_terminal(self, idx):
        lineas, actual, venv, cwd = self.estado_terminales.get(idx, ((), None, False, self.cwd))
        self.venv_activo, self.cwd = venv, cwd
        self.set(term_lineas=lineas, term_actual=actual if actual is not None else self.prompt(),
                 term_activa=idx, foco="terminal")

    def cambiar_terminal(self, idx):
        y = H - STATUS_H - self.s.term_alto + 56 + idx * 30
        self.clic(W - 110, y)
        self._guardar_terminal()
        self._cargar_terminal(idx)
        self.wait(0.3)

    def maximizar_terminal(self, si=True):
        y = H - STATUS_H - self.s.term_alto + 20
        self.clic(BTN_MAX[0], y)
        self.set(term_alto=(H - STATUS_H - TITLE_H - 4) if si else 400)
        self.wait(0.4)

    def comando(self, cmd, cps=13):
        """Teclea un comando en PowerShell, con sus colores (comando amarillo, opciones grises)."""
        self.set(foco="terminal")
        colores, palabra = [], 0
        en_texto = False
        for i, c in enumerate(cmd):
            if c == '"':
                en_texto = not en_texto
            if c == " " and not en_texto:
                palabra += 1
            inicio = cmd.rfind(" ", 0, i + 1) + 1
            if en_texto or c == '"':
                colores.append(CIAN)
            elif palabra == 0:
                colores.append(Y)
            elif cmd[inicio:inicio + 1] == "-":
                colores.append(GRIS)
            else:
                colores.append(BLANCO)
        for c, col in zip(cmd, colores):
            self.sonidos.append((self.t, "tecla"))
            self.set(term_actual=self.s.term_actual + ((c, col),))
            self.emit(max(1, round(FPS / cps * self.rnd.uniform(0.6, 1.4))))
        self.wait(0.25)
        self.atajo("Enter", 0.8)
        self.nueva_linea()

    def nueva_linea(self):
        self.set(term_lineas=self.s.term_lineas + (self.s.term_actual,), term_actual=())

    def salida(self, texto, color=BLANCO, pausa=0.06):
        for linea in texto.split("\n"):
            segs = linea if isinstance(linea, tuple) else ((linea, color),)
            self.set(term_lineas=self.s.term_lineas + (segs,))
            self.wait(pausa)

    def salida_segs(self, segs, pausa=0.06):
        self.set(term_lineas=self.s.term_lineas + (tuple(segs),))
        self.wait(pausa)

    def fin_comando(self):
        self.set(term_actual=self.prompt())

    def preguntar(self, etiqueta, color, texto, cps=12):
        """El programa muestra una etiqueta (input) y la persona escribe."""
        self.set(term_actual=((etiqueta, color),))
        self.wait(0.5)
        for c in texto:
            self.sonidos.append((self.t, "tecla"))
            self.set(term_actual=self.s.term_actual + ((c, BLANCO),))
            self.emit(max(1, round(FPS / cps * self.rnd.uniform(0.6, 1.4))))
        self.wait(0.3)
        self.atajo("Enter", 0.8)
        self.nueva_linea()

    def responder(self, texto, cps=45, pensar=1.4):
        self.wait(pensar)
        self.set(term_actual=(("Asistente: ", BLANCO),))
        for c in texto:
            self.set(term_actual=self.s.term_actual + ((c, BLANCO),))
            self.emit(1 if self.rnd.random() < 0.6 else 2)
        self.nueva_linea()
        self.salida("")

    def limpiar_terminal(self):
        self.atajo("cls", 0.8)
        self.set(term_lineas=(), term_actual=self.prompt())
        self.wait(0.3)

    # ---------- el celular (réplica de la app, en tiempo virtual)
    # Coordenadas de la pantalla del celular (468 x 968) que se tocan en las demos
    T_CAMPO, T_BOTON = (200, 916), (424, 916)
    T_MENU, T_DOCS, T_AJUSTES, T_ATRAS = (28, 85), (392, 85), (436, 85), (28, 85)

    def demo_app(self, id_, titulo, pasos, inicial=()):
        """Muestra la app en el celular mientras se narran y ejecutan los pasos.
        titulo: (icono, kicker, html del título). inicial: eventos en t = 0.
        Pasos: ("decir", frase) · ("esperar", s) · ("ev", tipo, *args) · ("toque", x, y) · ("nota", icono, texto, color)
               ("escribir", texto) · ("preguntar", texto, respuesta, fuentes, por_voz)"""
        obj = DemoApp(id_)
        self.demos_app.append(obj)
        t0 = self.t
        vt = lambda: round(self.t - t0, 3)
        ev = lambda *a: obj.eventos.append([vt(), *a])
        ev("titulo", [titulo[0], titulo[1]], titulo[2])
        for e in inicial:
            ev(*e)

        def avanzar(seg):
            for _ in range(max(0, round(seg * FPS))):
                self.set(slide=(obj, self.t - t0, None), ocultar_mouse=True)
                self.emit()

        def hasta_fin_de_frase():
            while self.t < self.say_hasta:
                avanzar(1 / FPS)

        def tocar(x, y):
            ev("toque", x, y)
            self.sonidos.append((self.t, "clic"))
            avanzar(0.3)

        def teclear(texto, cps=13):
            for i in range(1, len(texto) + 1):
                self.sonidos.append((self.t, "tecla"))
                ev("campo", texto[:i])
                avanzar(1 / FPS * max(1, round(FPS / cps * self.rnd.uniform(0.6, 1.4))))

        avanzar(0.5)
        for p in pasos:
            tipo = p[0]
            if tipo == "decir":
                hasta_fin_de_frase()
                self.say(p[1])
                avanzar(0.3)
            elif tipo == "esperar":
                avanzar(p[1])
            elif tipo == "hasta_fin":
                hasta_fin_de_frase()
            elif tipo == "ev":
                ev(*p[1:])
            elif tipo == "toque":
                tocar(p[1], p[2])
            elif tipo == "nota":
                ev("nota", *p[1:])
                avanzar(0.4)
            elif tipo == "escribir":
                tocar(*self.T_CAMPO)
                teclear(p[1])
            elif tipo == "preguntar":
                _, pregunta, respuesta, fuentes, por_voz = (list(p) + [False])[:5]
                if por_voz:
                    hasta_fin_de_frase()
                    tocar(*self.T_BOTON)
                    ev("estado", "escuchando")
                    avanzar(0.5)
                    self.log_usuario.append((self.t, pregunta))   # la persona habla
                    palabras = pregunta.split(" ")
                    paso = duracion_frase(pregunta) / (len(palabras) + 1)
                    for k in range(1, len(palabras) + 1):
                        avanzar(paso)
                        ev("campo", " ".join(palabras[:k]))
                    avanzar(0.9)
                    ev("estado", "reposo")
                else:
                    tocar(*self.T_CAMPO)
                    teclear(pregunta)
                    avanzar(0.3)
                    tocar(*self.T_BOTON)
                ev("campo", "")
                ev("msg", "u", pregunta)
                ev("estado", "pensando")
                avanzar(0.2)
                ev("pendiente", fuentes)
                avanzar(1.4)                                   # busca en Qdrant y Gemma empieza
                dur = max(1.2, len(respuesta) / 38)            # token por token
                ev("stream", respuesta, dur, fuentes)
                avanzar(dur + 0.2)
                hasta_fin_de_frase()                           # nunca encima del narrador
                ev("estado", "hablando")
                self.log_yarbys.append((self.t, respuesta))    # YARBYS habla
                avanzar(duracion_frase(respuesta, VOZ_YARBYS))
                ev("estado", "reposo")
                avanzar(0.4)
        hasta_fin_de_frase()
        avanzar(0.6)
        self.set(slide=None, ocultar_mouse=False)

    # ---------- slides
    def slide(self, obj, dur=None, frases=()):
        """Muestra una escena animada mientras se narran las frases."""
        inicio = len(self.frames)
        self.hold()
        marcas, acc = [], 0.0
        for f in frases:
            marcas.append(round(acc, 3))
            acc += duracion_frase(f)
        total = dur if dur is not None else acc + 1.5
        if hasattr(obj, "configurar"):
            obj.configurar(total, marcas)
        if frases:
            self.say(frases[0])
        n = round(total * FPS)
        cola = list(frases[1:])
        lectura = duracion_frase(frases[0]) if frases else 0
        siguiente = lectura
        for i in range(n):
            t = i / FPS
            if cola and t >= siguiente:
                f = cola.pop(0)
                self.say(f)
                siguiente = t + duracion_frase(f)
            self.set(slide=(obj, t, total), fundido=1.0, ocultar_mouse=True)
            self.emit()
        while cola:  # por si faltó tiempo
            self.say(cola.pop(0), esperar=True)
        self.hold()
        self.set(slide=None, fundido=1.0, ocultar_mouse=False)
        return inicio


SUGERENCIAS = {"FlutterEdgeAi", "FlutterEdgeAiRag", "FlutterEdgeAiActiveEmbedder", "InferenceModel",
               "ModelType", "ModelFileType", "LiteRtLmEngine", "LiteRtEmbeddingBackend", "VectorStoreSpec",
               "QdrantVectorStoreProvider", "EmbeddingInput", "RetrievalResult", "RagIndex", "TextResponse",
               "StatelessWidget", "StatefulWidget", "BuildContext", "MaterialApp", "Scaffold", "Database",
               "WidgetsFlutterBinding", "ensureInitialized", "initialize", "installModel", "installEmbedder",
               "fromNetwork", "modelFromNetwork", "withProgress", "withModelProgress", "getActiveModel",
               "createChat", "systemInstruction", "maxOutputTokens", "addQueryChunk", "generateChatResponseAsync",
               "getApplicationDocumentsDirectory", "getDatabasesPath", "openDatabase", "hasActiveModel",
               "hasActiveEmbedder", "StringBuffer", "writeln", "jsonEncode", "jsonDecode", "fragmentar",
               "fragmentos", "documentos", "armarPrompt", "historial", "contexto", "Conocimiento", "Memoria",
               "Cerebro", "Modelos", "Ajustes", "inferenceEngines", "embeddingBackends", "guardarDocumento"}


# ============================================================== DIBUJO VS CODE
def icono_archivo(d, x, y, nombre):
    ext = nombre.rsplit(".", 1)[-1] if "." in nombre else nombre
    if nombre.endswith(".dart"):
        d.polygon([(x + 1, y + 10), (x + 8, y + 3), (x + 17, y + 3), (x + 17, y + 20), (x + 8, y + 20)], fill=(1, 117, 194))
        d.polygon([(x + 8, y + 3), (x + 17, y + 3), (x + 17, y + 12)], fill=(64, 196, 255))
    elif ext in ("yml", "yaml"):
        d.text((x + 1, y), "!", font=F_UI_B, fill=(166, 120, 226))
        d.text((x + 8, y), "!", font=F_UI_B, fill=(166, 120, 226))
    elif ext == "xml":
        d.text((x - 2, y - 1), "<>", font=F_UI_B, fill=(241, 142, 51))
    elif ext == "kts":
        d.polygon([(x + 2, y + 3), (x + 18, y + 3), (x + 10, y + 11), (x + 18, y + 20), (x + 2, y + 20)], fill=(160, 100, 230))
    elif ext == "md":
        d.text((x + 1, y), "i", font=F_UI_B, fill=(66, 165, 245))
        d.text((x + 8, y), "↓", font=F_SYM, fill=(66, 165, 245))
    elif ext in ("lock", "metadata", "gitignore"):
        d.rectangle((x + 3, y + 9, x + 15, y + 19), outline=C_MUTED, width=2)
        d.arc((x + 5, y + 2, x + 13, y + 14), 180, 360, fill=C_MUTED, width=2)
    elif ext == "txt":
        for k in range(4):
            d.line((x + 2, y + 6 + k * 4, x + 16 - (k % 2) * 4, y + 6 + k * 4), fill=(140, 170, 200), width=2)
    else:
        d.rectangle((x + 3, y + 3, x + 15, y + 19), outline=C_MUTED, width=2)


def chevron(d, x, y, abierto, col=C_TEXT):
    if abierto:
        d.line((x, y + 7, x + 5, y + 12, x + 10, y + 7), fill=col, width=2)
    else:
        d.line((x + 3, y + 4, x + 8, y + 9, x + 3, y + 14), fill=col, width=2)


def arbol(s):
    """Lista de (nivel, nombre, ruta, es_carpeta, abierta), con carpetas anidadas como en VS Code."""
    rutas = list(s.files)
    carpetas = set(s.carpetas)
    for r in rutas:
        partes = r.split("/")
        for k in range(1, len(partes)):
            carpetas.add("/".join(partes[:k]))
    items = []

    def nivel(base, prof):
        pref = base + "/" if base else ""
        hijas = sorted((c for c in carpetas if c.startswith(pref) and "/" not in c[len(pref):]), key=str.lower)
        for c in hijas:
            abierta = c in s.abiertas
            items.append((prof, c.split("/")[-1], c, True, abierta))
            if abierta:
                nivel(c, prof + 1)
        for r in sorted((r for r in rutas if r.startswith(pref) and "/" not in r[len(pref):]), key=str.lower):
            items.append((prof, r.split("/")[-1], r, False, False))

    nivel("", 0)
    return items


def dibujar_vscode(img, d, s, blink):
    # barra de título
    d.rectangle((0, 0, W, TITLE_H), fill=C_SIDE)
    d.line((0, TITLE_H - 1, W, TITLE_H - 1), fill=C_BORDER)
    # logo VS Code simplificado
    d.polygon([(16, 12), (30, 6), (30, 32), (16, 26)], fill=(36, 142, 230))
    d.polygon([(10, 14), (16, 19), (10, 24)], fill=(26, 112, 200))
    x = 52
    for m in ["File", "Edit", "Selection", "View", "Go", "Run", "Terminal", "Help"]:
        d.text((x, 9), m, font=F_UI, fill=C_TEXT)
        x += F_UI.getlength(m) + 22
    cw = 560
    d.rounded_rectangle((W / 2 - cw / 2, 6, W / 2 + cw / 2, TITLE_H - 7), 6,
                        fill=(36, 36, 36), outline=(60, 60, 60))
    d.text((W / 2, TITLE_H / 2), s.raiz.lower(), font=F_UI_S, fill=C_MUTED, anchor="mm")
    for i, c in enumerate([(200, 200, 200)] * 3):
        bx = W - 140 + i * 46
        if i == 0:
            d.line((bx, 19, bx + 12, 19), fill=c, width=1)
        elif i == 1:
            d.rectangle((bx, 13, bx + 11, 24), outline=c)
        else:
            d.line((bx, 13, bx + 11, 24), fill=c)
            d.line((bx, 24, bx + 11, 13), fill=c)

    # barra de actividades
    d.rectangle((0, TITLE_H, ACT_W, H - STATUS_H), fill=C_SIDE)
    d.line((ACT_W, TITLE_H, ACT_W, H - STATUS_H), fill=C_BORDER)
    y = TITLE_H + 14
    d.rectangle((0, y - 6, 2, y + 34), fill=C_BLUE)
    d.rectangle((17, y, 35, y + 24), outline=(230, 230, 230), width=2)
    d.rectangle((22, y + 4, 39, y + 28), outline=(230, 230, 230), width=2)
    y += 56
    d.ellipse((16, y, 34, y + 18), outline=C_MUTED, width=2)
    d.line((31, y + 15, 39, y + 23), fill=C_MUTED, width=3)
    y += 56
    for cx, cy in [(20, y), (20, y + 24), (36, y + 8)]:
        d.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), outline=C_MUTED, width=2)
    d.line((20, y + 4, 20, y + 20), fill=C_MUTED, width=2)
    y += 56
    d.polygon([(19, y), (37, y + 12), (19, y + 24)], outline=C_MUTED)
    y += 56
    for dx, dy in [(0, 0), (12, 0), (0, 12), (14, 14)]:
        d.rectangle((17 + dx, y + dy, 27 + dx, y + 10 + dy), outline=C_MUTED, width=2)

    # barra lateral: explorador
    d.rectangle((ACT_W + 1, TITLE_H, ED_X, H - STATUS_H), fill=C_SIDE)
    d.line((ED_X, TITLE_H, ED_X, H - STATUS_H), fill=C_BORDER)
    d.text((ACT_W + 20, TITLE_H + 12), "EXPLORER", font=F_UI_S, fill=C_MUTED)
    ry = TITLE_H + 40
    chevron(d, ACT_W + 10, ry + 2, True)
    d.text((ACT_W + 28, ry), s.raiz, font=fnt(INTER + "Inter-Bold.otf", 16), fill=C_TEXT)
    # iconos (nuevo archivo, nueva carpeta, refrescar, colapsar)
    bx, by = BTN_NUEVO
    hover = abs(s.mouse[0] - bx) < 16 and abs(s.mouse[1] - by) < 16
    if hover:
        d.rounded_rectangle((bx - 13, by - 12, bx + 13, by + 12), 4, fill=(55, 55, 55))
    d.rectangle((bx - 6, by - 8, bx + 4, by + 8), outline=C_TEXT, width=2)
    d.line((bx + 2, by - 2, bx + 10, by - 2), fill=C_TEXT, width=2)
    d.line((bx + 6, by - 6, bx + 6, by + 2), fill=C_TEXT, width=2)
    for k in range(1, 4):
        ix = bx + k * 30
        d.rectangle((ix - 7, by - 6, ix + 7, by + 6), outline=C_MUTED, width=1)
    y = ry + 30
    items = arbol(s)
    if s.input_explorer is not None:
        # caja de nombre del nuevo archivo, arriba del todo
        d.rectangle((ACT_W + 1, y - 2, ED_X - 1, y + 26), fill=(4, 57, 94))
        nombre = s.input_explorer.split("/")[-1] or " "
        icono_archivo(d, ACT_W + 38, y + 1, nombre)
        d.rectangle((ACT_W + 64, y, ED_X - 10, y + 24), fill=(49, 49, 49), outline=C_BLUE)
        d.text((ACT_W + 70, y + 2), s.input_explorer, font=F_UI, fill=C_TEXT)
        cx = ACT_W + 70 + F_UI.getlength(s.input_explorer)
        if blink:
            d.line((cx + 1, y + 4, cx + 1, y + 21), fill=C_TEXT, width=1)
        y += 28
    for nivel, nombre, ruta, carpeta, abierta in items:
        x = ACT_W + 22 + nivel * 18
        if ruta == s.activo and not carpeta and s.input_explorer is None:
            d.rectangle((ACT_W + 1, y - 2, ED_X - 1, y + 26),
                        fill=(4, 57, 94) if s.foco == "explorer" else (55, 55, 61))
        if carpeta:
            chevron(d, x, y + 3, abierta, C_MUTED)
            d.text((x + 18, y + 1), nombre, font=F_UI, fill=C_TEXT)
        else:
            icono_archivo(d, x + 16, y + 1, nombre)
            col = (226, 192, 141) if ruta in s.sucios else C_TEXT
            d.text((x + 42, y + 1), nombre, font=F_UI, fill=col)
            if ruta in s.sucios:
                d.text((ED_X - 30, y + 1), "●", font=F_SYM, fill=(226, 192, 141))
        y += 28
    # sección inferior
    d.line((ACT_W + 1, H - STATUS_H - 70, ED_X, H - STATUS_H - 70), fill=C_BORDER)
    for i, t in enumerate(["OUTLINE", "TIMELINE"]):
        yy = H - STATUS_H - 62 + i * 30
        chevron(d, ACT_W + 10, yy + 3, False, C_MUTED)
        d.text((ACT_W + 28, yy), t, font=fnt(INTER + "Inter-Bold.otf", 15), fill=C_MUTED)

    # área del editor
    eb = editor_bottom(s)
    d.rectangle((ED_X + 1, TITLE_H, W, eb), fill=C_BG)
    # pestañas
    d.rectangle((ED_X + 1, TITLE_H, W, TITLE_H + TABS_H), fill=C_SIDE)
    tabs_visibles = eb > ED_Y
    d.line((ED_X + 1, TITLE_H + TABS_H - 1, W, TITLE_H + TABS_H - 1), fill=C_BORDER)
    x = ED_X + 1
    for ruta in (s.tabs if tabs_visibles else ()):
        nombre = ruta.split("/")[-1]
        tw = F_UI.getlength(nombre) + 80
        activo = ruta == s.activo
        if activo:
            d.rectangle((x, TITLE_H, x + tw, TITLE_H + TABS_H), fill=C_BG)
            d.line((x, TITLE_H, x + tw, TITLE_H), fill=C_BLUE, width=2)
        d.line((x + tw, TITLE_H, x + tw, TITLE_H + TABS_H), fill=C_BORDER)
        icono_archivo(d, x + 14, TITLE_H + 12, nombre)
        d.text((x + 40, TITLE_H + 13), nombre, font=F_UI,
               fill=(255, 255, 255) if activo else C_MUTED)
        if ruta in s.sucios:
            d.ellipse((x + tw - 26, TITLE_H + 19, x + tw - 16, TITLE_H + 29), fill=C_TEXT)
        elif activo:
            d.text((x + tw - 26, TITLE_H + 12), "×", font=F_SYM, fill=C_TEXT)
        x += tw
    if eb <= ED_Y:
        pass  # terminal maximizada: el editor no se ve
    elif s.activo is None:
        # pantalla de bienvenida vacía
        d.polygon([(W / 2 + 180 - 60, 430), (W / 2 + 180 + 40, 390), (W / 2 + 180 + 40, 590),
                   (W / 2 + 180 - 60, 550)], fill=(40, 40, 40))
        d.text((W / 2 + 180, 650), "Show All Commands   Ctrl + Shift + P", font=F_UI,
               fill=(110, 110, 110), anchor="mm")
        d.text((W / 2 + 180, 685), "Go to File   Ctrl + P", font=F_UI, fill=(110, 110, 110),
               anchor="mm")
    else:
        ruta = s.activo
        partes = ruta.split("/")
        bc = s.raiz.lower() + "  ›  " + "  ›  ".join(partes)
        d.text((ED_X + 20, TITLE_H + TABS_H + 5), bc, font=F_UI_S, fill=C_MUTED)
        texto = s.files[ruta]
        lineas = colorear(ruta.split("/")[-1], texto)
        top = s.scroll.get(ruta, 0)
        vis = lineas_visibles(s)
        cl, cc = s.cursor
        x0 = ED_X + GUTTER
        for i in range(top, min(len(lineas), top + vis + 1)):
            yy = ED_Y + (i - top) * LH
            if yy + LH > eb:
                break
            if s.pausa == (ruta, i):
                d.rectangle((ED_X + GUTTER - 6, yy, W - MINIMAP - 14, yy + LH - 1), fill=(75, 70, 28))
            elif i == cl and s.foco == "editor" and not s.sel:
                d.rectangle((ED_X + GUTTER - 6, yy, W - MINIMAP - 14, yy + LH - 1), outline=C_CURLINE, width=2)
            if s.punto == (ruta, i):
                d.ellipse((ED_X + 8, yy + 10, ED_X + 24, yy + 26), fill=(229, 20, 0))
            if s.pausa == (ruta, i):
                d.polygon([(ED_X + 6, yy + 8), (ED_X + 22, yy + 8), (ED_X + 30, yy + 18), (ED_X + 22, yy + 28),
                           (ED_X + 6, yy + 28)], outline=(255, 204, 0), width=2)
            if s.sel and s.sel[0] <= i <= s.sel[1]:
                crudo = "".join(t for t, _ in lineas[i])
                ini = len(crudo) - len(crudo.lstrip())
                fin = max(len(crudo), ini + 1)
                d.rectangle((x0 + ini * CW, yy, x0 + fin * CW + 6, yy + LH - 1), fill=C_SEL)
            d.text((ED_X + GUTTER - 22, yy + 4), str(i + 1), font=F_CODE,
                   fill=(204, 204, 204) if i == cl else C_LINENO, anchor="ra")
            crudo = "".join(t for t, _ in lineas[i])
            sangria = len(crudo) - len(crudo.lstrip(" "))
            paso = 2 if ruta.endswith((".dart", ".yaml")) else 4
            for g in range(0, sangria, paso):
                if g:
                    d.line((x0 + g * CW, yy, x0 + g * CW, yy + LH), fill=(64, 64, 64))
            xx = x0
            limite_x = W - MINIMAP - 24
            for t, col in lineas[i]:
                if xx >= limite_x:
                    break
                if xx + CW * len(t) > limite_x:
                    t = t[:max(0, int((limite_x - xx) / CW))]
                d.text((xx, yy + 4), t, font=F_CODE, fill=col)
                xx += CW * len(t)
        # cursor
        if s.foco == "editor" and (blink or s.popup) and top <= cl < top + vis:
            cy = ED_Y + (cl - top) * LH
            cx = x0 + cc * CW
            d.rectangle((cx, cy + 4, cx + 2, cy + LH - 4), fill=(174, 175, 173))
        # globo del depurador con el valor de una variable
        if s.hover and top <= s.hover[0] < top + vis:
            hl, hc, nombre, valor = s.hover
            lineas_v = wrap(f"{nombre}: {valor}", F_CODE, 760)
            hx = x0 + hc * CW
            hy = ED_Y + (hl - top + 1) * LH + 4
            hw = max(F_CODE.getlength(l) for l in lineas_v) + 30
            hh = len(lineas_v) * 32 + 18
            if hx + hw > W - 30:
                hx = W - 30 - hw
            d.rectangle((hx, hy, hx + hw, hy + hh), fill=(37, 37, 38), outline=(69, 69, 69))
            for k, l in enumerate(lineas_v):
                nm = l.split(":")[0] if k == 0 else ""
                d.text((hx + 14, hy + 9 + k * 32), l, font=F_CODE, fill=(206, 145, 120))
                if nm:
                    d.text((hx + 14, hy + 9), nm + ":", font=F_CODE, fill=(156, 220, 254))
        # minimapa
        mx = W - MINIMAP - 8
        for i, segs in enumerate(lineas[:300]):
            yy = ED_Y + 4 + i * 3
            xx = mx + 6
            for t, col in segs:
                ln = len(t.rstrip()) * 1.1
                if t.strip():
                    off = (len(t) - len(t.lstrip())) * 1.1
                    d.line((xx + off, yy, xx + ln, yy), fill=mix(C_BG, col, 0.55), width=2)
                xx += len(t) * 1.1
        vy0 = ED_Y + 4 + top * 3
        if vis > 0:
            capa = Image.new("RGBA", (MINIMAP, vis * 3 + 2), (121, 121, 121, 40))
            img.paste(capa, (mx, int(vy0)), capa)
        # popup de autocompletado
        if s.popup and top <= s.popup[2] < top + vis:
            items, palabra, pl, pc = s.popup
            px = x0 + pc * CW
            py = ED_Y + (pl - top + 1) * LH
            pw = max(F_CODE.getlength(it) for it in items) + 90
            ph = len(items) * 32 + 8
            d.rectangle((px, py, px + pw, py + ph), fill=(37, 37, 38), outline=(69, 69, 69))
            for k, it in enumerate(items):
                iy = py + 4 + k * 32
                if k == 0:
                    d.rectangle((px + 1, iy, px + pw - 1, iy + 32), fill=(4, 57, 94))
                es_clase = it[:1].isupper()
                d.rectangle((px + 10, iy + 9, px + 24, iy + 23),
                            outline=(238, 157, 40) if es_clase else (183, 128, 235), width=2)
                d.text((px + 36, iy + 3), it, font=F_CODE, fill=(255, 255, 255) if k == 0 else C_TEXT)
                n = len(s.files[s.activo].split("\n")[pl]) - pc
                d.text((px + 36, iy + 3), it[:max(0, n)], font=F_CODE, fill=(24, 163, 255))

    # panel de terminal
    if s.term_abierto:
        ty = editor_bottom(s)
        d.rectangle((ED_X + 1, ty, W, H - STATUS_H), fill=C_TERM_BG)
        d.line((ED_X + 1, ty, W, ty), fill=C_BORDER)
        x = ED_X + 20
        activa = "DEBUG CONSOLE" if s.panel == "debug" else "TERMINAL"
        for nombre in ["PROBLEMS", "OUTPUT", "DEBUG CONSOLE", "TERMINAL", "PORTS"]:
            col = C_TEXT if nombre == activa else C_MUTED
            d.text((x, ty + 10), nombre, font=F_UI_S, fill=col)
            if nombre == activa:
                d.line((x, ty + 34, x + F_UI_S.getlength(nombre), ty + 34), fill=C_BLUE, width=1)
            x += F_UI_S.getlength(nombre) + 28
        if s.panel == "debug":
            d.rounded_rectangle((W - 520, ty + 6, W - 260, ty + 32), 3, fill=(49, 49, 49), outline=(69, 69, 69))
            d.text((W - 510, ty + 9), "Filter (e.g. text, !exclude)", font=F_UI_S, fill=(120, 120, 120))
        else:
            d.text((W - 330, ty + 10), "powershell", font=F_UI_S, fill=C_MUTED)
            d.text((W - 240, ty + 7), "+", font=F_UI_B, fill=C_MUTED)
        # maximizar ^ y cerrar ×
        mxx, myy = BTN_MAX[0], ty + 20
        maxim = s.term_alto > 500
        if maxim:
            d.line((mxx - 7, myy - 3, mxx, myy + 4, mxx + 7, myy - 3), fill=C_TEXT, width=2)
        else:
            d.line((mxx - 7, myy + 3, mxx, myy - 4, mxx + 7, myy + 3), fill=C_TEXT, width=2)
        d.text((W - 52, ty + 7), "×", font=F_SYM, fill=C_MUTED)
        # lista de terminales (cuando hay más de una)
        lista_w = 0
        if len(s.term_tabs) > 1:
            lista_w = 200
            lx = W - lista_w
            d.line((lx, ty + 40, lx, H - STATUS_H), fill=C_BORDER)
            for i, nombre in enumerate(s.term_tabs):
                yy = ty + 46 + i * 30
                if i == s.term_activa:
                    d.rectangle((lx + 1, yy - 2, W, yy + 26), fill=(55, 55, 61))
                d.text((lx + 16, yy + 1), ">_", font=F_UI_B, fill=C_MUTED)
                d.text((lx + 48, yy + 2), nombre, font=F_UI_S, fill=C_TEXT if i == s.term_activa else C_MUTED)
        # contenido
        ancho_chars = int((W - ED_X - 60 - lista_w) / TCW)
        filas = []
        if s.panel == "debug":
            todas = [((t, c),) for t, c in s.consola] + [()]
        else:
            todas = list(s.term_lineas) + [s.term_actual]
        for segs in todas:
            fila, largo = [], 0
            for t, col in segs:
                while largo + len(t) > ancho_chars:
                    corte = ancho_chars - largo
                    fila.append((t[:corte], col))
                    filas.append(fila)
                    fila, largo, t = [], 0, t[corte:]
                if t:
                    fila.append((t, col))
                    largo += len(t)
            filas.append(fila)
        reservado = 20
        disponibles = int((H - STATUS_H - ty - 50 - reservado) // TLH)
        filas = filas[-disponibles:] if disponibles > 0 else []
        for k, fila in enumerate(filas):
            xx = ED_X + 24
            yy = ty + 48 + k * TLH
            for t, col in fila:
                d.text((xx, yy), t, font=F_TERM, fill=col)
                xx += TCW * len(t)
        if filas and s.foco == "terminal" and s.panel != "debug":
            ult = filas[-1]
            cx = ED_X + 24 + TCW * sum(len(t) for t, _ in ult)
            cy = ty + 48 + (len(filas) - 1) * TLH
            d.rectangle((cx, cy + 2, cx + TCW - 2, cy + TLH - 4), fill=(200, 200, 200))

    # barra de estado
    d.rectangle((0, H - STATUS_H, W, H), fill=(204, 102, 51) if s.depurando else C_SIDE)
    d.line((0, H - STATUS_H, W, H - STATUS_H), fill=C_BORDER)
    d.rectangle((0, H - STATUS_H, 44, H), fill=C_BLUE)
    d.text((22, H - STATUS_H / 2), "><", font=F_UI_B, fill=(255, 255, 255), anchor="mm")
    d.text((60, H - STATUS_H + 5), "⎇ main", font=F_SYM, fill=C_TEXT)
    d.text((150, H - STATUS_H + 5), "⊗ 0  ⚠ 0", font=F_SYM, fill=C_TEXT)
    if s.activo:
        cl, cc = s.cursor
        ext = s.activo.rsplit(".", 1)[-1]
        lang = {"py": "Python", "yml": "YAML", "yaml": "YAML", "txt": "Plain Text", "dart": "Dart", "xml": "XML",
                "kts": "Kotlin", "md": "Markdown"}.get(ext, "Plain Text")
        partes = [f"Ln {cl + 1}, Col {cc + 1}", f"Spaces: {2 if ext in ('dart', 'yaml') else 4}", "UTF-8", "CRLF", lang]
        if s.raiz == "YARBYS":
            partes.append("Pixel 8 (android-arm64)")
        x = W - 30
        for p in reversed(partes):
            x -= F_UI_S.getlength(p)
            d.text((x, H - STATUS_H + 6), p, font=F_UI_S, fill=C_TEXT)
            x -= 30


def dibujar_mouse(d, x, y, click):
    if click > 0:
        r = 10 + (1 - click) * 26
        d.ellipse((x - r, y - r, x + r, y + r), outline=(255, 210, 80), width=3)
    pts = [(0, 0), (0, 27), (7, 21), (12, 32), (17, 30), (12, 19), (21, 19)]
    d.polygon([(x + px, y + py) for px, py in pts], fill=(255, 255, 255), outline=(0, 0, 0))


# ---------- capas superpuestas
_cache_sub = {}


def capa_subtitulo(texto):
    if texto in _cache_sub:
        return _cache_sub[texto]
    lineas = wrap(texto, F_SUB, 1500)
    alto = 26 + len(lineas) * 46
    ancho = max(F_SUB.getlength(l) for l in lineas) + 64
    capa = Image.new("RGBA", (int(ancho), int(alto)), (0, 0, 0, 0))
    dc = ImageDraw.Draw(capa)
    dc.rounded_rectangle((0, 0, ancho - 1, alto - 1), 16, fill=(0, 0, 0, 205))
    for i, l in enumerate(lineas):
        dc.text((ancho / 2, 13 + i * 46), l, font=F_SUB, fill=(255, 255, 255), anchor="ma")
    if len(_cache_sub) > 50:
        _cache_sub.clear()
    _cache_sub[texto] = capa
    return capa


def dibujar_nota(img, d, s):
    titulo, texto = s.nota
    top = s.scroll.get(s.activo, 0)
    a, b = s.sel if s.sel else (s.cursor[0], s.cursor[0])
    ancho = 900
    lineas = wrap(texto, F_NOTE, ancho - 70) if texto else []
    alto = 30 + (40 if titulo else 0) + len(lineas) * 36 + 14
    if not lineas:
        ancho = int(F_NOTE_B.getlength(titulo)) + 110
    x0 = ED_X + GUTTER + 40
    y_debajo = ED_Y + (b - top + 1) * LH + 16
    limite = editor_bottom(s) - 130
    if y_debajo + alto > limite:
        y0 = ED_Y + (a - top) * LH - alto - 16
        flecha_arriba = False
        if y0 < ED_Y:
            y0 = max(ED_Y + 10, limite - alto)
            x0 = W - MINIMAP - ancho - 30
    else:
        y0 = y_debajo
        flecha_arriba = True
    capa = Image.new("RGBA", (ancho + 20, alto + 20), (0, 0, 0, 0))
    dc = ImageDraw.Draw(capa)
    dc.rounded_rectangle((6, 8, ancho + 6, alto + 8), 14, fill=(0, 0, 0, 120))
    dc.rounded_rectangle((0, 0, ancho, alto), 14, fill=(38, 34, 22, 250), outline=MARCA2 + (255,), width=3)
    dc.ellipse((22, 20, 54, 52), fill=MARCA2 + (255,))
    dc.text((38, 36), "i", font=F_NOTE_B, fill=(30, 25, 10, 255), anchor="mm")
    y = 18
    if titulo:
        dc.text((70, y), titulo, font=F_NOTE_B, fill=MARCA2 + (255,))
        y += 40
    for l in lineas:
        dc.text((70, y), l, font=F_NOTE, fill=(245, 240, 225, 255))
        y += 36
    img.paste(capa, (int(x0), int(y0)), capa)
    if flecha_arriba:
        d.polygon([(x0 + 60, y0 - 14), (x0 + 46, y0 + 1), (x0 + 74, y0 + 1)], fill=MARCA2)


def dibujar_tecla(img, s):
    texto = s.tecla
    w = F_KEY.getlength(texto) + 50
    capa = Image.new("RGBA", (int(w), 64), (0, 0, 0, 0))
    dc = ImageDraw.Draw(capa)
    dc.rounded_rectangle((0, 0, w - 1, 63), 14, fill=(20, 20, 20, 230), outline=(120, 120, 120, 255), width=2)
    dc.text((w / 2, 32), texto, font=F_KEY, fill=(255, 255, 255), anchor="mm")
    img.paste(capa, (int(W - 40 - w), TITLE_H + TABS_H + 24), capa)


def dibujar_capitulo(img, s):
    """Etiqueta del paso actual, a la derecha de la barra de pestañas."""
    if not s.capitulo:
        return
    w = F_UI_B.getlength(s.capitulo) + 36
    capa = Image.new("RGBA", (int(w), 32), (0, 0, 0, 0))
    dc = ImageDraw.Draw(capa)
    dc.rounded_rectangle((0, 0, w - 1, 31), 16, fill=MARCA + (255,))
    dc.text((w / 2, 16), s.capitulo, font=F_UI_B, fill=(255, 255, 255), anchor="mm")
    img.paste(capa, (int(W - 24 - w), TITLE_H + 7), capa)


def dibujar_barra_depuracion(d, s):
    """La barra flotante de depuración de VS Code (con los botones de Flutter)."""
    x0, y0, w, h = W / 2 - 200, TITLE_H + 6, 400, 34
    d.rounded_rectangle((x0, y0, x0 + w, y0 + h), 5, fill=(51, 51, 51), outline=(69, 69, 69))
    x = x0 + 14
    for k in range(3):
        d.ellipse((x + (k % 2) * 6, y0 + 9 + k * 6, x + 3 + (k % 2) * 6, y0 + 12 + k * 6), fill=(140, 140, 140))
    x += 30
    cy = y0 + h / 2
    if s.pausa:
        d.polygon([(x, cy - 9), (x, cy + 9), (x + 14, cy)], fill=(117, 190, 255))            # continuar
    else:
        d.rectangle((x, cy - 8, x + 4, cy + 8), fill=(117, 190, 255))                         # pausa
        d.rectangle((x + 9, cy - 8, x + 13, cy + 8), fill=(117, 190, 255))
    x += 40
    d.arc((x, cy - 9, x + 18, cy + 7), 180, 360, fill=(117, 190, 255), width=2)              # paso por encima
    d.ellipse((x + 6, cy + 4, x + 12, cy + 10), fill=(117, 190, 255))
    x += 40
    d.line((x + 8, cy - 10, x + 8, cy + 4), fill=(117, 190, 255), width=2)                    # entrar
    d.polygon([(x + 2, cy - 1), (x + 14, cy - 1), (x + 8, cy + 6)], fill=(117, 190, 255))
    x += 40
    d.line((x + 8, cy + 10, x + 8, cy - 4), fill=(117, 190, 255), width=2)                    # salir
    d.polygon([(x + 2, cy + 1), (x + 14, cy + 1), (x + 8, cy - 6)], fill=(117, 190, 255))
    x += 40
    d.polygon([(x + 9, cy - 11), (x + 2, cy + 2), (x + 8, cy + 2), (x + 5, cy + 11), (x + 14, cy - 3),
               (x + 8, cy - 3)], fill=(255, 204, 0))                                          # hot reload
    x += 40
    d.arc((x, cy - 9, x + 18, cy + 9), 40, 330, fill=(137, 209, 133), width=2)                # reiniciar
    x += 40
    d.rectangle((x + 1, cy - 8, x + 17, cy + 8), outline=(241, 76, 76), width=2)              # detener


def dibujar_rapido(img, s):
    """Etiqueta ⏩ x4 mientras el tecleo va acelerado (como un video adelantado)."""
    w = F_UI_B.getlength(s.rapido) + 74
    capa = Image.new("RGBA", (int(w), 44), (0, 0, 0, 0))
    dc = ImageDraw.Draw(capa)
    dc.rounded_rectangle((0, 0, w - 1, 43), 22, fill=(20, 22, 26, 235), outline=MARCA + (255,), width=2)
    for k in range(2):
        x = 20 + k * 15
        dc.polygon([(x, 12), (x + 15, 22), (x, 32)], fill=(255, 255, 255))
    dc.text((58, 22), s.rapido, font=F_UI_B, fill=(255, 255, 255), anchor="lm")
    img.paste(capa, (int(W - MINIMAP - 30 - w), int(editor_bottom(s) - 64)), capa)


# ============================================================== ESCENAS HTML (motion graphics)
class SlideHTML:
    """Escena animada hecha con HTML + GSAP (escenas/escenas.js), renderizada con Chromium."""

    def __init__(self, id_, datos=None):
        self.id = id_
        self.datos = datos
        self.dur, self.marcas = 10.0, [0.0]

    def configurar(self, dur, marcas):
        self.dur, self.marcas = dur, marcas

    def url(self):
        from urllib.parse import quote
        m = ",".join(f"{x:.3f}" for x in self.marcas)
        d = f"&d={quote(json.dumps(self.datos, ensure_ascii=False))}" if self.datos else ""
        return f"file://{ESCENAS_HTML}?id={self.id}&dur={self.dur:.3f}&m={m}{d}"


class DemoApp:
    """La app en el celular (escenas/app.html) manejada por eventos en tiempo virtual."""

    def __init__(self, id_):
        self.id = id_
        self.eventos = []
        self.html = APP_HTML

    def url(self):
        return f"file://{self.html}?id={self.id}&v={len(self.eventos)}"

    def guardar(self):
        DEMOS.mkdir(exist_ok=True)
        datos = json.dumps({"eventos": self.eventos}, ensure_ascii=False)
        (DEMOS / f"{self.id}.js").write_text(f"window.DEMO = {datos};\n", encoding="utf-8")


class Chromium:
    """Un navegador por proceso, para capturar las escenas HTML cuadro a cuadro."""

    def __init__(self):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.launch()
        self.page = self.browser.new_page(viewport={"width": W, "height": H})
        self.cdp = self.page.context.new_cdp_session(self.page)
        self.url = None

    def captura(self, obj, t):
        import base64
        import io
        url = obj.url()
        if url != self.url:
            self.page.goto(url)
            self.page.wait_for_function("window.__listo === true", polling=50, timeout=30000)
            self.url = url
        self.page.evaluate(f"seek({t:.4f})")
        datos = self.cdp.send("Page.captureScreenshot", {"format": "jpeg", "quality": 93, "optimizeForSpeed": True})["data"]
        return Image.open(io.BytesIO(base64.b64decode(datos))).convert("RGB")


_chromium = None


def chromium():
    global _chromium
    if _chromium is None:
        _chromium = Chromium()
    return _chromium


_logo = None


def pegar_logo(img):
    """Logo del canal, siempre en la esquina inferior derecha."""
    global _logo
    if _logo is None:
        _logo = Image.open(LOGO).convert("RGBA").resize((84, 84), Image.LANCZOS)
        alfa = _logo.getchannel("A").point(lambda v: int(v * 0.92))
        _logo.putalpha(alfa)
    img.paste(_logo, (W - 84 - 28, H - 84 - STATUS_H - 22), _logo)


# ============================================================== FICHA DEL ARCHIVO
COLOR_TIPO = {"clase": (78, 201, 176), "widget": (78, 201, 176), "estado": (197, 134, 192),
              "método": (220, 220, 170), "función": (220, 220, 170), "getter": (220, 220, 170),
              "campo": (156, 220, 254), "constante": (156, 220, 254), "enum": (78, 201, 176),
              "carpeta": (220, 180, 90), "archivo": (64, 196, 255)}
_cache_ficha = {}


def dibujar_ficha(img, s):
    """El mapa del archivo: para qué sirve y qué clases y métodos tiene."""
    clave = s.ficha
    if clave not in _cache_ficha:
        titulo, desc, elementos, activo, hechos = s.ficha
        ancho = 540
        lin_desc = wrap(desc, F_FICHA, ancho - 48)
        filas = []
        for k, (tipo, nombre, expl) in enumerate(elementos):
            sangria = 24 if tipo in ("método", "campo", "getter", "constante") else 0
            bw = F_FICHA_T.getlength(tipo.upper()) + 16
            libre = ancho - 24 - sangria - bw - 12 - 50
            nombres = [""]
            for parte in nombre.split(" · "):
                prueba = parte if not nombres[-1] else nombres[-1] + " · " + parte
                if nombres[-1] and F_FICHA_M.getlength(prueba) > libre:
                    nombres[-1] += " ·"
                    nombres.append(parte)
                else:
                    nombres[-1] = prueba
            filas.append((k, tipo, nombres, wrap(expl, F_FICHA, ancho - 64 - sangria) if expl else [], sangria))
        alto = 22 + 34 + len(lin_desc) * 29 + 20 + sum(44 + (len(n) - 1) * 28 + len(ex) * 26 for _, _, n, ex, _ in filas) + 14
        capa = Image.new("RGBA", (ancho + 12, alto + 12), (0, 0, 0, 0))
        dc = ImageDraw.Draw(capa)
        dc.rounded_rectangle((6, 8, ancho + 6, alto + 8), 16, fill=(0, 0, 0, 110))
        dc.rounded_rectangle((0, 0, ancho, alto), 16, fill=(30, 33, 38, 248), outline=MARCA + (255,), width=3)
        icono_archivo(dc, 22, 22, titulo)
        dc.text((52, 18), titulo, font=F_FICHA_B, fill=(255, 255, 255))
        y = 22 + 34
        for l in lin_desc:
            dc.text((24, y), l, font=F_FICHA, fill=(200, 205, 212))
            y += 29
        y += 12
        dc.line((24, y, ancho - 24, y), fill=(60, 66, 74), width=2)
        y += 8
        for k, tipo, nombres, ex, sang in filas:
            extra = (len(nombres) - 1) * 28
            h = 44 + extra + len(ex) * 26
            if k == activo:
                dc.rounded_rectangle((10, y - 2, ancho - 10, y + h - 6), 10, fill=(4, 57, 94, 255))
            col = COLOR_TIPO.get(tipo, (200, 200, 200))
            bw = F_FICHA_T.getlength(tipo.upper()) + 16
            dc.rounded_rectangle((24 + sang, y + 8, 24 + sang + bw, y + 32), 6, outline=col, width=2)
            dc.text((24 + sang + 8, y + 11), tipo.upper(), font=F_FICHA_T, fill=col)
            for j, nombre in enumerate(nombres):
                dc.text((24 + sang + bw + 12, y + 7 + j * 28), nombre, font=F_FICHA_M, fill=(255, 255, 255))
            if k in hechos:
                dc.text((ancho - 44, y + 6), "✓", font=F_SYM, fill=(35, 209, 139))
            yy = y + 38 + extra
            for l in ex:
                dc.text((24 + sang + 4, yy), l, font=F_FICHA, fill=(170, 176, 184))
                yy += 26
            y += h
        if len(_cache_ficha) > 40:
            _cache_ficha.clear()
        _cache_ficha[clave] = capa
    capa = _cache_ficha[clave]
    img.paste(capa, (W - capa.width - 26, ED_Y + 12), capa)


# ============================================================== NAVEGADOR (páginas reales)
NAV_TOP = 84                      # alto de la barra de pestañas + barra de direcciones
CACHE_WEB = AQUI / "_cache_web"   # capturas de las páginas (ver capturar_paginas)
PAGINAS = {                       # id -> (url, {clave: selector})
    "pub_inicio": ("https://pub.dev", {"busqueda": "input[name=q]"}),
    "pub_busqueda": ("https://pub.dev/packages?q=flutter_edge_ai",
                     {"resultado": ".packages-item:first-child .packages-title a"}),
    "pub_paquete": ("https://pub.dev/packages/flutter_edge_ai",
                    {"titulo": "h1", "instalar": "a[href='/packages/flutter_edge_ai/install']"}),
    "pub_instalar": ("https://pub.dev/packages/flutter_edge_ai/install",
                     {"comando": "pre:has-text('flutter pub add')"}),
    "pub_litertlm": ("https://pub.dev/packages/flutter_edge_ai_litertlm",
                     {"eg2": "#embeddinggemma-2", "codigo_eg2": "pre:has-text('9be6e8b9')"}),
}
PAGINAS_CAJAS = {}                # id -> {clave: (x, y, w, h), "_alto": alto, "_titulo": título}
ZOOM_WEB = 1.25                   # las páginas se ven al 125% para que se lean bien


def capturar_paginas():
    """Abre cada página real con Chromium y guarda una captura completa y la posición de sus elementos."""
    import os
    CACHE_WEB.mkdir(exist_ok=True)
    pendientes = []
    for pid, (url, sel) in PAGINAS.items():
        meta = CACHE_WEB / f"{pid}.json"
        if meta.exists():
            datos = json.loads(meta.read_text(encoding="utf-8"))
            if datos.get("url") == url and datos.get("selectores") == sel:
                PAGINAS_CAJAS[pid] = datos["cajas"]
                continue
        pendientes.append(pid)
    if not pendientes:
        return
    from playwright.sync_api import sync_playwright
    print(f"Capturando {len(pendientes)} páginas web...", flush=True)
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    with sync_playwright() as p:
        b = p.chromium.launch(proxy={"server": proxy} if proxy else None)
        ctx = b.new_context(viewport={"width": round(W / ZOOM_WEB), "height": round((H - NAV_TOP) / ZOOM_WEB)},
                            device_scale_factor=ZOOM_WEB, locale="es-ES")
        for pid in pendientes:
            url, sel = PAGINAS[pid]
            pg = ctx.new_page()
            pg.goto(url, wait_until="networkidle", timeout=90000)
            pg.wait_for_timeout(1200)
            cajas = {}
            for clave, selector in sel.items():
                loc = pg.locator(selector).first
                caja = loc.bounding_box()
                if caja:
                    cajas[clave] = [round(caja["x"] * ZOOM_WEB), round(caja["y"] * ZOOM_WEB),
                                    round(caja["width"] * ZOOM_WEB), round(caja["height"] * ZOOM_WEB)]
                else:
                    print(f"  aviso: '{clave}' no está en {pid}", flush=True)
            alto = min(pg.evaluate("document.documentElement.scrollHeight"), 9000)
            pg.screenshot(path=str(CACHE_WEB / f"{pid}.png"), full_page=True,
                          clip={"x": 0, "y": 0, "width": round(W / ZOOM_WEB), "height": alto})
            cajas["_alto"] = round(alto * ZOOM_WEB)
            cajas["_titulo"] = pg.title()
            PAGINAS_CAJAS[pid] = cajas
            (CACHE_WEB / f"{pid}.json").write_text(json.dumps({"url": url, "selectores": sel, "cajas": cajas},
                                                             ensure_ascii=False), encoding="utf-8")
            pg.close()
            print(f"  {pid} lista", flush=True)
        b.close()


_cache_paginas = {}


def imagen_pagina(pid):
    if pid not in _cache_paginas:
        _cache_paginas[pid] = Image.open(CACHE_WEB / f"{pid}.png").convert("RGB")
    return _cache_paginas[pid]


def dibujar_navegador(img, d, s, blink):
    url, contenido = s.navegador
    d.rectangle((0, 0, W, NAV_TOP), fill=(32, 32, 32))
    titulo = "Nueva pestaña"
    if contenido[0] == "pagina":
        titulo = PAGINAS_CAJAS.get(contenido[1], {}).get("_titulo", url)
    titulo = titulo if len(titulo) < 30 else titulo[:28] + "…"
    d.rounded_rectangle((8, 6, 330, 44), 10, fill=(56, 56, 56))
    d.rectangle((8, 30, 330, 44), fill=(56, 56, 56))
    d.ellipse((22, 16, 40, 34), fill=(66, 133, 244))
    d.text((52, 15), titulo, font=F_UI, fill=(235, 235, 235))
    d.text((302, 13), "×", font=F_SYM, fill=(200, 200, 200))
    d.text((348, 10), "+", font=F_UI_B, fill=(200, 200, 200))
    for i in range(3):   # controles de ventana de Windows
        bx = W - 140 + i * 46
        c = (210, 210, 210)
        if i == 0:
            d.line((bx, 22, bx + 12, 22), fill=c)
        elif i == 1:
            d.rectangle((bx, 16, bx + 11, 27), outline=c)
        else:
            d.line((bx, 16, bx + 11, 27), fill=c)
            d.line((bx, 27, bx + 11, 16), fill=c)
    d.rectangle((0, 44, W, NAV_TOP), fill=(56, 56, 56))
    for i, x in enumerate([22, 62, 102]):
        col = (220, 220, 220) if i != 1 else (120, 120, 120)
        if i == 0:
            d.line((x + 12, 64, x, 64), fill=col, width=2); d.line((x, 64, x + 6, 58), fill=col, width=2); d.line((x, 64, x + 6, 70), fill=col, width=2)
        elif i == 1:
            d.line((x, 64, x + 12, 64), fill=col, width=2); d.line((x + 12, 64, x + 6, 58), fill=col, width=2); d.line((x + 12, 64, x + 6, 70), fill=col, width=2)
        else:
            d.arc((x, 57, x + 14, 71), 40, 330, fill=col, width=2)
    d.rounded_rectangle((150, 50, W - 150, 78), 14, fill=(36, 36, 36))
    d.ellipse((166, 57, 180, 71), outline=(170, 170, 170), width=2)
    d.text((194, 54), url, font=F_UI, fill=(235, 235, 235))
    if s.foco == "url" and blink:
        cx = 194 + F_UI.getlength(url) + 2
        d.line((cx, 55, cx, 74), fill=(235, 235, 235))
    d.ellipse((W - 112, 52, W - 88, 76), fill=MARCA)
    d.text((W - 60, 52), "···", font=F_UI_B, fill=(220, 220, 220))
    if contenido[0] == "pagina":
        _, pid, scroll, extra = contenido
        pag = imagen_pagina(pid)
        alto = H - NAV_TOP
        recorte = pag.crop((0, scroll, W, scroll + alto))
        img.paste(recorte, (0, NAV_TOP))
        if extra and extra[0] == "marco":
            x, y, w, h = PAGINAS_CAJAS[pid][extra[1]]
            y = y + NAV_TOP - scroll
            d.rounded_rectangle((x - 10, y - 8, x + w + 10, y + h + 8), 10, outline=MARCA2, width=5)
        elif extra:
            clave, texto = extra
            x, y, w, h = PAGINAS_CAJAS[pid][clave]
            y = y + NAV_TOP - scroll
            fondo = pag.getpixel((min(W - 1, x + w - 12), min(pag.height - 1, PAGINAS_CAJAS[pid][clave][1] + h // 2)))
            d.rectangle((x + 40, y + 6, x + w - 14, y + h - 6), fill=fondo)
            claro = sum(fondo) / 3 > 140
            fuente = fnt(INTER + "Inter-Regular.otf", max(18, int(h * 0.42)))
            d.text((x + 46, y + h / 2), texto, font=fuente, fill=(30, 30, 30) if claro else (240, 240, 240), anchor="lm")
            if blink:
                cx = x + 46 + fuente.getlength(texto) + 2
                d.line((cx, y + h * 0.25, cx, y + h * 0.75), fill=(30, 30, 30) if claro else (240, 240, 240), width=2)
    elif contenido[0] == "cargando":
        t = contenido[1]
        d.rectangle((0, NAV_TOP, W, H), fill=(246, 247, 249))
        d.rectangle((0, NAV_TOP, int(W * min(1.0, 0.15 + t * 0.85)), NAV_TOP + 3), fill=(0, 120, 212))
    else:
        d.rectangle((0, NAV_TOP, W, H), fill=(32, 33, 36))
        d.text((W / 2, H / 2), "Nueva pestaña", font=F_H, fill=(150, 150, 150), anchor="mm")


# ============================================================== RENDER DE UN FOTOGRAMA
def render(s, blink):
    if s.slide:
        obj, t, dur = s.slide
        img = chromium().captura(obj, t)
        d = ImageDraw.Draw(img)
    elif s.navegador:
        img = Image.new("RGB", (W, H), (32, 32, 32))
        d = ImageDraw.Draw(img)
        dibujar_navegador(img, d, s, blink)
        if s.tecla:
            dibujar_tecla(img, s)
        if not s.ocultar_mouse:
            dibujar_mouse(d, *s.mouse, s.click)
    else:
        img = Image.new("RGB", (W, H), C_BG)
        d = ImageDraw.Draw(img)
        dibujar_vscode(img, d, s, blink)
        if s.depurando:
            dibujar_barra_depuracion(d, s)
        if s.ficha:
            dibujar_ficha(img, s)
        if s.nota:
            dibujar_nota(img, d, s)
        if s.rapido:
            dibujar_rapido(img, s)
        dibujar_capitulo(img, s)
        if s.tecla:
            dibujar_tecla(img, s)
        if not s.ocultar_mouse:
            dibujar_mouse(d, *s.mouse, s.click)
    if SUBTITULOS and s.subtitulo:
        capa = capa_subtitulo(s.subtitulo)
        img.paste(capa, (int(W / 2 - capa.width / 2), H - STATUS_H - 18 - capa.height), capa)
    pegar_logo(img)
    if s.fundido < 1.0:
        img = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), img, s.fundido)
    return img


# ============================================================== GUION DEL VIDEO
def leer(archivo):
    return (CODIGO / archivo).read_text(encoding="utf-8")


R_MIERCOLES = "El miércoles tienes que entregar el proyecto de la tienda online antes de las 6 de la tarde."
R_PERRO = "Se llama Rocky. Y recuerda que el sábado a las 10 de la mañana lo llevas al veterinario."
R_MUSICA = "Te gusta el rock de los 80, ideal para programar con tu café americano sin azúcar."
R_SABADO = "El sábado a las 10 de la mañana llevas a Rocky al veterinario."
R_ANTES = "Hablamos de tu música favorita, el rock de los 80, y de la cita de Rocky con el veterinario el sábado."

VERDE, AMARILLO, CELESTE = "#4ade80", "#fba905", "#00cbff"
F_GEMMA = ("brain", "Gemma 4 corre dentro del celular", CELESTE)


def archivos_plantilla():
    """El proyecto tal como lo deja 'flutter create' (solo lo que se ve en el explorador)."""
    f = {
        "lib/main.dart": (PLANTILLA / "main.dart").read_text(encoding="utf-8"),
        "pubspec.yaml": (PLANTILLA / "pubspec.yaml").read_text(encoding="utf-8"),
        "android/app/build.gradle.kts": (PLANTILLA / "build.gradle.kts").read_text(encoding="utf-8"),
        "android/app/src/main/AndroidManifest.xml": (PLANTILLA / "AndroidManifest.xml").read_text(encoding="utf-8"),
        "test/widget_test.dart": "", "analysis_options.yaml": "", "pubspec.lock": "", "README.md": "",
        ".gitignore": "", ".metadata": "", "android/build.gradle.kts": "", "android/settings.gradle.kts": "",
        "android/gradle.properties": "",
    }
    carpetas = {".dart_tool", "ios", "android/gradle", "android/app/src/debug", "android/app/src/profile",
                "android/app/src/main/kotlin", "android/app/src/main/res"}
    return f, carpetas


def fmt_srt(s):
    ms = int(round(s * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    sec, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{sec:02},{ms:03}"


def fmt_min(s):
    return f"{int(s // 60)}:{int(s % 60):02}"


def escribir_textos(D, base=None):
    """Escribe el guion (.md) y los subtítulos (.srt) junto al video."""
    base = base or AQUI / "tutorial"
    srt = [f"{i}\n{fmt_srt(a)} --> {fmt_srt(b)}\n{t}\n" for i, (a, b, t, _) in enumerate(D.log, 1)]
    base.with_suffix(".srt").write_text("\n".join(srt), encoding="utf-8")
    g = [f"# Guion de narración · {base.name}", "",
         f"Lee cada frase en voz alta en el momento indicado. Los tiempos coinciden con `{base.name}.mp4`.",
         "El video ya trae esta narración con voz generada (Kokoro). Si prefieres grabar tu propia voz, "
         "pon `NARRACION = False` en `render.py` y graba siguiendo estos tiempos.", ""]
    actual = None
    for a, b, t, cap in D.log:
        if cap != actual:
            g += ["", f"## {cap}", ""]
            actual = cap
        g.append(f"- **{fmt_min(a)}** — {t}")
    vistos, caps = set(), []
    for t, c in D.capitulos:
        if c not in vistos:
            vistos.add(c)
            caps.append(f"{fmt_min(t)} {c}")
    g += ["", "## Capítulos para la descripción de YouTube", "", "```"] + caps + ["```", ""]
    base.with_suffix(".md").write_text("\n".join(g), encoding="utf-8")


# ============================================================== NARRACIÓN (voz)
# Cómo debe "sonar" cada término técnico. Solo afecta al audio (el guion y los
# subtítulos muestran el texto original). Se aplica en orden: lo más largo primero.
PRONUNCIACION = sorted([
    ("flutter create --org com.paulantezana --platforms android,ios yarbys", "flóter criéit"),
    ("flutter build apk --release --target-platform android-arm64", "flóter bild a pe ka"),
    ("--target-platform android-arm64", "guión guión tárguet plátform, ándroid arm sesenta y cuatro"),
    ("flutter run --release", "flóter ran, guión guión rilís"),
    ("flutter build apk", "flóter bild a pe ka"),
    ("flutter pub add", "flóter pab ad"),
    ("flutter devices", "flóter diváisis"),
    ("flutter doctor", "flóter dóctor"),
    ("flutter create", "flóter criéit"),
    ("--platforms", "guión guión plátforms"),
    ("--org", "guión guión org"),
    ("--release", "guión guión rilís"),
    ("build.gradle.kts", "build punto greidl punto ka te ese"),
    ("AndroidManifest.xml", "ándroid mánifest punto equis eme ele"),
    ("pubspec.yaml", "pab spec punto yámel"),
    ("yarbys.db", "yárbis punto de be"),
    ("C:\\flutter", "ce dos puntos, flóter"),
    ("C:\\proyectos", "ce dos puntos, proyectos"),
    ("File, Open Folder", "fail, óupen fólder"),
    ("Control + comilla invertida", "control, comilla invertida"),
    ("Control +", "control"),
    ("flutter.dev", "flóter punto dev"),
    ("pub.dev", "pab punto dev"),
    (".litertlm", "punto lait er te ele eme"),
    (".dart", " punto dart"),
    ("LiteRtLmEngine", "lait er te ele eme énllin"),
    ("LiteRtEmbeddingBackend", "lait er te embéding bákend"),
    ("LiteRT-LM", "lait er te, ele eme"),
    ("FlutterEdgeAiRag", "flóter ech ei ai rag"),
    ("flutter_edge_ai", "flóter ech ei ai"),
    ("FlutterSecureStorage", "flóter sekiúr stórich"),
    ("flutter_secure_storage", "flóter sekiúr stórich"),
    ("speech_to_text", "spich tu text"),
    ("SpeechToText", "spich tu text"),
    ("flutter_tts", "flóter te te ese"),
    ("FlutterTts", "flóter te te ese"),
    ("file_picker", "fail píker"),
    ("path_provider", "path provaider"),
    ("sqflite", "ese cu eflait"),
    ("http", "hache te te pe"),
    ("getActiveModel", "guet áctiv módel"),
    ("installEmbedder", "instól embéder"),
    ("installModel", "instól módel"),
    ("withModelProgress", "uiz módel prógres"),
    ("createChat", "criéit chat"),
    ("maxTokens", "max tókens"),
    ("modelType", "módel taip"),
    ("fileType", "fail taip"),
    ("openDatabase", "open déita beis"),
    ("onCreate", "on criéit"),
    ("armarPrompt", "armar prómt"),
    ("usarNube", "usar nube"),
    ("esPro", "es pro"),
    ("MaterialApp", "matírial app"),
    ("CustomPainter", "cástom péinter"),
    ("setState", "set stéit"),
    ("await for", "auéit for"),
    ("Ticker", "tíker"),
    ("Stream", "strim"),
    ("yield", "yild"),
    ("flush", "flash"),
    ("search", "serch"),
    ("threshold", "zréshold"),
    ("listen", "lísen"),
    ("false", "fols"),
    ("minSdk", "min es de ka"),
    ("queries", "cuíris"),
    ("src", "ese erre ce"),
    ("Keystore", "kístor"),
    ("Keychain", "kíchein"),
    ("EmbeddingGemma", "embéding yéma"),
    ("Gemma 4 E2B", "yéma cuatro, e dos be"),
    ("Gemma", "yéma"),
    ("Qdrant Edge", "cudrant ech"),
    ("Qdrant", "cudrant"),
    ("SQLite", "ese cu ele lait"),
    ("SQL", "ese cu ele"),
    ("YARBYS", "yárbis"),
    ("JARVIS", "yárvis"),
    ("Flutter", "flóter"),
    ("Hugging Face", "jáguin feis"),
    ("GPT-6 Luna", "ge pe te seis luna"),
    ("Claude Haiku", "clod jáiku"),
    ("ChatGPT", "chat ge pe te"),
    ("Anthropic", "ánzropic"),
    ("OpenAI", "open ei ai"),
    ("GitHub Actions", "guit jab ácshons"),
    ("GitHub", "guit jab"),
    ("workflow", "uórk flou"),
    ("README", "rid mi"),
    ("Xcode", "équis coud"),
    ("Wi-Fi", "uai fai"),
    ("iPhone", "áifon"),
    ("Google", "gúgol"),
    ("Pixel 8", "píxel ocho"),
    ("Android Studio", "ándroid estudio"),
    ("Visual Studio Code", "visual estudio coud"),
    ("VS Code", "ve ese coud"),
    ("Windows", "uíndous"),
    ("PATH", "pat"),
    ("APK", "a pe ka"),
    ("USB", "u ese be"),
    ("API key", "a pi kei"),
    ("API", "a pi"),
    ("framework", "fréimuork"),
    ("widgets", "uíyets"),
    ("widget", "uíyet"),
    ("embeddings", "embédings"),
    ("embedding", "embéding"),
    ("tokens", "tókens"),
    ("token", "tóken"),
    ("prompt", "prómt"),
    ("LLMs", "ele ele emes"),
    ("LLM", "ele ele eme"),
    ("RAG", "rag"),
    ("IA", "i a"),
    ("2.6", "dos punto seis"),
    ("2.8", "dos punto ocho"),
    ("like", "láik"),
    # código de Flutter y Dart
    ("flutter_edge_ai_litertlm", "flóter ech ei ai, lait er te ele eme"),
    ("flutter_edge_ai_qdrant", "flóter ech ei ai cudrant"),
    ("flutter_edge_ai_rag", "flóter ech ei ai rag"),
    ("Future<void>", "fiúcher void"),
    ("Future", "fiúcher"),
    ("async", "eisínc"),
    ("await", "auéit"),
    ("static", "estátic"),
    ("late", "léit"),
    ("enum", "ínum"),
    ("main", "méin"),
    ("build", "bild"),
    ("dispose", "dispóus"),
    ("catch", "cach"),
    ("finally", "fáinali"),
    ("initialize", "inishaláis"),
    ("insert", "insért"),
    ("install", "instól"),
    ("limit", "límit"),
    ("query", "cuíri"),
    ("reversed", "rivérsd"),
    ("speak", "spik"),
    ("paint", "péint"),
    ("drawer", "dróer"),
    ("markdown", "márkdaun"),
    ("resolve", "risólv"),
    ("commit", "cómit"),
    ("State", "stéit"),
    ("Row", "rou"),
    ("Scaffold", "scáfold"),
    ("Container", "contéiner"),
    ("Navigator", "návigueitor"),
    ("Installing", "instóling"),
    ("Pildora", "píldora"),
    ("Nucleo", "núcleo"),
    (".txt", " punto te equis te"),
    (".md", " punto eme de"),
    ("Debug Console", "debag cónsol"),
    ("debugPrint", "debag print"),
    ("hot reload", "jot rilóud"),
    ("hot restart", "jot ristárt"),
    ("F5", "efe cinco"),
    ("Shift", "shift"),
    ("runApp", "ran ap"),
    ("Message", "méseich"),
    ("isUser", "is iúser"),
    ("join", "yóin"),
    ("Center", "sénter"),
    ("Column", "cólum"),
    ("const", "const"),
    ("bool", "bul"),
    ("void", "void"),
    ("String", "string"),
    ("import", "ímport"),
    ("material", "matírial"),
    ("close", "clóus"),
    ("try", "trai"),
    ("finally", "fáinali"),
    ("initialize", "inishaláis"),
    ("main", "méin"),
    ("android:label", "ándroid léibel"),
    ("uses-permission", "iúses permíshon"),
    ("INTERNET", "internet"),
    ("dependencies", "dipéndensis"),
    ("pub.dev", "pab punto dev"),
    ("Installing", "instóling"),
    ("widget_test.dart", "uíyet test punto dart"),
    ("test", "test"),
    ("Mira la consola", "mira la consola"),
    # la página de Hugging Face
    ("huggingface.co", "jáguin feis punto co"),
    ("litert-community", "lait er te comiúniti"),
    ("Files and versions", "fails and vérshons"),
    ("gemma-4-E2B-it-litert-lm", "yéma cuatro, e dos be, it, lait er te ele eme"),
    ("gemma-4-E2B-it.litertlm", "yéma cuatro, e dos be, it, punto lait er te ele eme"),
    ("embeddinggemma-2-text-270m-litert-lm", "embéding yéma dos, text, doscientos setenta eme, lait er te ele eme"),
], key=lambda par: -len(par[0]))
_CLAVES = {k.lower() for k, _ in PRONUNCIACION}

# Partes en inglés de los nombres del código (hasActiveModel → "jas áctiv módel")
INGLES = {"has": "jas", "active": "áctiv", "model": "módel", "embedder": "embéder", "from": "from",
          "network": "nétuork", "init": "init", "state": "stéit", "stateful": "stéitful", "stateless": "stéitles",
          "list": "list", "view": "viu", "safe": "séif", "area": "érea", "app": "ap", "bar": "bar",
          "custom": "cástom", "paint": "péint", "segmented": "ségmented", "button": "báton", "string": "string",
          "buffer": "báfer", "should": "shud", "repaint": "ripéint", "pick": "pik", "files": "fails",
          "push": "push", "replacement": "ripléisment", "read": "rid", "all": "ol", "run": "ran", "db": "de be",
          "url": "u erre ele", "nucleo": "núcleo", "oir": "oír", "microfono": "micrófono", "indice": "índice",
          "oido": "oído", "menu": "menú", "with": "uiz", "progress": "prógres", "generate": "yénereit",
          "response": "rispóns", "async": "eisínc", "query": "cuíri", "chunk": "chank", "system": "sístem",
          "instruction": "instrúcshon", "output": "áutput", "tokens": "tókens", "max": "max", "my": "mai",
          "home": "jóum", "page": "péich", "counter": "cáunter", "increment": "íncrement", "ensure": "enshúr",
          "initialized": "inishalaisd", "widgets": "uíyets", "flutter": "flóter", "binding": "báinding",
          "floating": "flóuting", "action": "ácshon", "inference": "ínferens", "engines": "énllins",
          "engine": "énllin", "litert": "lait er te", "lm": "ele eme", "text": "text", "chat": "chat",
          "model": "módel", "file": "fail", "type": "taip", "personalidad": "personalidad", "deep": "dip",
          "purple": "pérpel", "color": "cólor", "scheme": "squim", "theme": "zim", "data": "déita"}


def _decir_identificador(m):
    """Separa los nombres del código en palabras: _cargarHilos → "cargar Hilos"."""
    w = m.group()
    if w.lower() in _CLAVES:
        return w
    trozos = []
    for t in w.split("."):
        if t.startswith("_") or re.search(r"[a-z][A-Z]", t):
            partes = re.findall(r"[A-Z]?[a-záéíóúñ]+|[A-Z]+(?![a-z])|\d+", t)
            t = " ".join(INGLES.get(p.lower(), p) for p in partes)
        trozos.append(t)
    return ".".join(trozos)


def texto_hablado(texto):
    """Convierte el texto del guion en el texto que pronuncia la voz."""
    t = re.sub(r"(?<![\w-])_*[A-Za-z][\w-]*(?:\.[A-Za-z_][\w-]*)*", _decir_identificador, texto)
    for original, dicho in PRONUNCIACION:
        patron = re.escape(original)
        if original[0].isalnum() or original[0] == "_":
            patron = r"(?<![\w.])" + patron
        if original[-1].isalnum() or original[-1] == "_":
            patron += r"(?![\w])"
        flags = 0 if original in ("IA", "API", "RAG", "LLM", "LLMs", "SQL", "PATH", "APK", "USB", "add") else re.IGNORECASE
        t = re.sub(patron, dicho, t, flags=flags)
    t = re.sub(r"(?<=[A-Za-z])\.(?=[a-z_])", " punto ", t)          # Modelos.descargarGemma
    t = re.sub(r"\b[A-ZÁÉÍÓÚÑ]{2,}\b", lambda m: m.group().lower(), t)   # énfasis en MAYÚSCULAS
    return t.replace("'", "").replace("\"", "")


def rutas_modelo():
    carpeta = AQUI / "modelos"
    modelo = next((carpeta / n for n in ["kokoro-v1.0.onnx", "kokoro-v1.0.int8.onnx",
                                          "kokoro-quantized.onnx", "kokoro.onnx"]
                   if (carpeta / n).exists()), None)
    voces = next((carpeta / n for n in ["voices-v1.0.bin", "voices.npz", "voices.bin"]
                  if (carpeta / n).exists()), None)
    return modelo, voces


_kokoro = None


def _sintetizar(args):
    global _kokoro
    voz, texto, destino = args
    import soundfile as sf
    if _kokoro is None:
        import onnxruntime as ort
        from kokoro_onnx import Kokoro
        modelo, voces = rutas_modelo()
        # un hilo por proceso: varios procesos en paralelo sin pelear por la CPU
        op = ort.SessionOptions()
        op.intra_op_num_threads = 1
        op.inter_op_num_threads = 1
        sesion = ort.InferenceSession(str(modelo), op, providers=["CPUExecutionProvider"])
        _kokoro = Kokoro.from_session(sesion, str(voces))
    audio, sr = _kokoro.create(texto_hablado(texto), voice=voz, speed=VELOCIDAD, lang="es")
    sf.write(str(destino), audio, sr)
    return texto


def preparar_voz(pares):
    """Genera (o reutiliza de la caché) el audio de cada (voz, frase) y guarda su duración."""
    import hashlib
    import soundfile as sf
    cache = AQUI / "_voz"
    cache.mkdir(exist_ok=True)
    archivos, pendientes = {}, []
    for voz, f in dict.fromkeys(pares):
        clave = hashlib.sha1(f"{voz}|{VELOCIDAD}|{texto_hablado(f)}".encode()).hexdigest()[:16]
        archivos[(voz, f)] = cache / f"{clave}.wav"
        if not archivos[(voz, f)].exists():
            pendientes.append((voz, f, archivos[(voz, f)]))
    if pendientes:
        modelo, voces = rutas_modelo()
        if not modelo or not voces:
            raise SystemExit("Faltan los archivos del modelo Kokoro en video/modelos/ (ver README).")
        print(f"Generando voz para {len(pendientes)} frases...", flush=True)
        with mp.get_context("fork").Pool(max(1, mp.cpu_count())) as pool:
            for i, _ in enumerate(pool.imap_unordered(_sintetizar, pendientes), 1):
                if i % 20 == 0 or i == len(pendientes):
                    print(f"  {i}/{len(pendientes)}", flush=True)
    for clave, ruta in archivos.items():
        DUR_VOZ[clave] = sf.info(str(ruta)).duration
    return archivos


def mezclar_audio(D, archivos, destino):
    """Pista de audio: narración + voz de YARBYS + teclado y clics, en los tiempos del video."""
    import numpy as np
    import soundfile as sf
    sr = 24000
    total = int(len(D.frames) / FPS * sr) + sr
    pista = np.zeros(total, dtype=np.float32)

    def poner(inicio, clave, vol=1.0):
        if clave not in archivos:
            return
        audio, _sr = sf.read(str(archivos[clave]), dtype="float32")
        a = int(inicio * sr)
        pista[a:a + len(audio)] += vol * audio[:max(0, total - a)]

    for inicio, _, texto, _ in D.log:
        poner(inicio, (VOZ, texto))
    for inicio, texto in D.log_yarbys:
        poner(inicio, (VOZ_YARBYS, texto), 0.95)
    for inicio, texto in D.log_usuario:
        poner(inicio, (VOZ, texto), 0.9)
    if TECLADO:
        rnd = np.random.default_rng(3)
        vistos = set()
        for t, tipo in D.sonidos:
            cuadro = round(t * FPS)
            if (cuadro, tipo) in vistos:
                continue   # varias letras en el mismo instante (autocompletado, pegar) = un solo golpe
            vistos.add((cuadro, tipo))
            n = int(0.012 * sr) if tipo == "tecla" else int(0.02 * sr)
            ruido = np.diff(rnd.standard_normal(n).astype(np.float32), prepend=0)
            env = np.exp(-np.linspace(0, 9, n)).astype(np.float32)
            vol = rnd.uniform(0.018, 0.032) if tipo == "tecla" else 0.05
            a = int(t * sr)
            pista[a:a + n] += (ruido * env * vol)[:max(0, total - a)]
    pico = float(np.abs(pista).max()) or 1.0
    pista *= min(1.0, 0.9 / pico)
    sf.write(str(destino), pista, sr)


# ============================================================== RENDER EN PARALELO
SUBTITULOS = False   # el video va sin subtítulos (subtitulos.srt queda para YouTube)
FRAMES = None


def trabajador(args):
    idx, ini, fin, salida = args
    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
        "-crf", "23", "-pix_fmt", "yuv420p", str(salida)], stdin=subprocess.PIPE)
    clave_ant, datos = None, None
    for f in range(ini, fin):
        s = FRAMES[f]
        blink = (f // 16) % 2 == 0
        clave = (id(s), blink)
        if clave != clave_ant:
            datos = render(s, blink).tobytes()
            clave_ant = clave
        ff.stdin.write(datos)
    ff.stdin.close()
    ff.wait()
    return idx


import curso                               # noqa: E402  (herramientas del curso en 9 videos)
curso.instalar(Director, sys.modules[__name__])


VIDEOS = AQUI / "videos"        # un .mp4 (con su .md y .srt) por video del curso


def guion_video(n):
    """Arma el video n del curso con el guion de guiones/videoNN.py."""
    import importlib
    capturar_paginas()
    modulo = importlib.import_module(f"guiones.video{n:02d}")
    D = Director()
    modulo.guion(D, sys.modules[__name__])
    D.cerrar_log()
    D.nombre = modulo.NOMBRE
    return D


def main():
    global FRAMES
    n = int(sys.argv[sys.argv.index("--video") + 1])
    archivos = {}
    if NARRACION:
        # 1ª pasada: obtener las frases; 2ª pasada: usar la duración real de cada audio
        D0 = guion_video(n)
        pares = ([(VOZ, e[2]) for e in D0.log] + [(VOZ_YARBYS, t) for _, t in D0.log_yarbys]
                 + [(VOZ, t) for _, t in D0.log_usuario])
        archivos = preparar_voz(pares)
    D = guion_video(n)
    for demo in D.demos_app:
        demo.guardar()
    FRAMES = D.frames
    total = len(FRAMES) / FPS
    VIDEOS.mkdir(exist_ok=True)
    base = VIDEOS / D.nombre
    escribir_textos(D, base)
    print(f"Video {n}: {fmt_min(total)} ({len(FRAMES)} fotogramas)")
    if "--preview" in sys.argv:
        out = AQUI / "preview"
        out.mkdir(exist_ok=True)
        for f in out.glob("f_*.jpg"):
            f.unlink()
        paso = int(sys.argv[sys.argv.index("--preview") + 1])
        for k, f in enumerate(range(0, len(FRAMES), paso * FPS)):
            render(FRAMES[f], True).save(out / f"f_{k:03}.jpg", quality=90)
        print("Previews en", out)
        return
    nproc = max(1, mp.cpu_count())
    tmp = AQUI / "_partes"
    tmp.mkdir(exist_ok=True)
    tam = math.ceil(len(FRAMES) / nproc)
    trabajos = [(i, i * tam, min(len(FRAMES), (i + 1) * tam), tmp / f"parte_{i}.mp4") for i in range(nproc)]
    with mp.get_context("fork").Pool(nproc) as pool:
        for i in pool.imap_unordered(trabajador, trabajos):
            print(f"  parte {i + 1}/{nproc} lista", flush=True)
    lista = tmp / "lista.txt"
    lista.write_text("".join(f"file '{t[3].name}'\n" for t in trabajos))
    wav = AQUI / "narracion.wav"
    mezclar_audio(D, archivos, wav)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lista),
                    "-i", str(wav), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", "-ac", "1",
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "96k",
                    "-shortest", "-movflags", "+faststart", str(base.with_suffix(".mp4"))], check=True)
    for t in trabajos:
        t[3].unlink()
    lista.unlink()
    tmp.rmdir()
    print("Video:", base.with_suffix(".mp4"))


if __name__ == "__main__":
    main()
