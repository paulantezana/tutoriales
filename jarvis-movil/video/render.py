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
APP_HTML = AQUI / "escenas" / "app.html"
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

    def escribir(self, texto, cps=17, errores=True, autocompletar=True):
        """Teclea como una persona: velocidad variable, sangría automática,
        algún error corregido y autocompletado en palabras largas."""
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
                self.emit(1)
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
                    self.emit(max(1, round(FPS / cps * r.uniform(0.7, 1.4))))
                lin, col = self.s.cursor
                otras = sorted({p for p in palabras_vistas | SUGERENCIAS
                                if p.startswith(palabra[:k]) and p != palabra})[:4]
                self.set(popup=((palabra,) + tuple(otras), palabra, lin, col - k))
                self.wait(r.uniform(0.35, 0.6))
                for c in palabra[k:]:
                    self._insertar(c)
                self.set(popup=None)
                self.emit(2)
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
            self.emit(max(1, round(espera)))
            i += 1

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
        for k, trozo in enumerate(re.split(r"(https?://[^'\"\s]+)", texto)):
            if not trozo:
                continue
            if k % 2:
                self.wait(0.3)
                self.pegar(trozo)
            else:
                self.escribir(trozo, cps)

    def esqueleto(self, plan, quitar=(), modo="escribir", cps=20):
        """Escribe el archivo sin los bloques de 'quitar' (los cuerpos de los métodos)."""
        quitados = set()
        for a, b in quitar:
            quitados.update(range(a, b + 1))
        plan.presentes = [i not in quitados for i in range(len(plan.lineas))]
        texto = plan.texto()
        self.pos = None
        if modo == "pegar":
            self.pegar(texto)
        else:
            self.escribir_codigo(texto, cps)
        assert self.texto() == texto, f"esqueleto de {plan.ruta} desfasado"

    def completar(self, plan, rango, modo="escribir", cps=20):
        """Escribe un bloque (por ejemplo el cuerpo de un método) en su lugar exacto."""
        a, b = rango
        assert not any(plan.presentes[a:b + 1]), f"{plan.ruta}: bloque {a}-{b} ya escrito"
        previos = [k for k in range(a) if plan.presentes[k]]
        actual = self.texto()
        assert actual == plan.texto(), f"{plan.ruta} desfasado antes de completar"
        if previos:
            pos = sum(len(plan.lineas[k]) + 1 for k in previos) - 1   # final de la línea anterior
            bloque = "\n" + "\n".join(plan.lineas[a:b + 1])
        else:
            pos = 0
            bloque = "\n".join(plan.lineas[a:b + 1]) + "\n"
        lin, col = self._cursor_de(actual, pos)
        top = self._mostrar_linea(lin)
        self.clic(ED_X + GUTTER + col * CW + 12, ED_Y + (lin - top) * LH + LH / 2)
        self.set(cursor=(lin, col), foco="editor", sel=None)
        self.atajo("End", 0.5)
        self.pos = pos
        if modo == "pegar":
            self.pegar(bloque)
        else:
            self.escribir_codigo(bloque, cps)
        self.pos = None
        for k in range(a, b + 1):
            plan.presentes[k] = True
        assert self.texto() == plan.texto(), f"{plan.ruta}: el bloque {a}-{b} no quedó igual"

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
            if i == cl and s.foco == "editor" and not s.sel:
                d.rectangle((ED_X + GUTTER - 6, yy, W - MINIMAP - 14, yy + LH - 1), outline=C_CURLINE, width=2)
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
        for nombre in ["PROBLEMS", "OUTPUT", "DEBUG CONSOLE", "TERMINAL", "PORTS"]:
            col = C_TEXT if nombre == "TERMINAL" else C_MUTED
            d.text((x, ty + 10), nombre, font=F_UI_S, fill=col)
            if nombre == "TERMINAL":
                d.line((x, ty + 34, x + F_UI_S.getlength(nombre), ty + 34), fill=C_BLUE, width=1)
            x += F_UI_S.getlength(nombre) + 28
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
        if filas and s.foco == "terminal":
            ult = filas[-1]
            cx = ED_X + 24 + TCW * sum(len(t) for t, _ in ult)
            cy = ty + 48 + (len(filas) - 1) * TLH
            d.rectangle((cx, cy + 2, cx + TCW - 2, cy + TLH - 4), fill=(200, 200, 200))

    # barra de estado
    d.rectangle((0, H - STATUS_H, W, H), fill=C_SIDE)
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

    def url(self):
        return f"file://{APP_HTML}?id={self.id}&v={len(self.eventos)}"

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


class Plan:
    """Un archivo del proyecto que se escribe por partes: primero el esqueleto y luego cada bloque."""

    def __init__(self, ruta):
        self.ruta = ruta
        self.lineas = leer(ruta).split("\n")
        self.presentes = [False] * len(self.lineas)

    def buscar(self, texto, desde=0):
        return next(i for i in range(desde, len(self.lineas)) if texto in self.lineas[i])

    def bloque(self, desde, hasta=None, despues_de=0):
        a = self.buscar(desde, despues_de)
        return (a, a if hasta is None else self.buscar(hasta, a))

    def cuerpo(self, firma, desde=0):
        """Las líneas entre la llave que abre un método y la llave que lo cierra."""
        i = self.buscar(firma, desde)
        k = i
        while not self.lineas[k].rstrip().endswith("{"):
            k += 1
        sangria = len(self.lineas[i]) - len(self.lineas[i].lstrip())
        j = next(m for m in range(k + 1, len(self.lineas))
                 if self.lineas[m].strip().startswith("}")
                 and len(self.lineas[m]) - len(self.lineas[m].lstrip()) == sangria)
        return (k + 1, j - 1)

    def texto(self):
        return "\n".join(l for l, p in zip(self.lineas, self.presentes) if p)

    def completo(self):
        return all(self.presentes)


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
        if s.ficha:
            dibujar_ficha(img, s)
        if s.nota:
            dibujar_nota(img, d, s)
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


def piezas(archivo, marcadores):
    """Divide un archivo en bloques; cada marcador es el inicio (línea exacta) de un bloque."""
    texto = leer(archivo)
    lineas = texto.split("\n")
    cortes, desde = [0], 0
    for m in marcadores:
        idx = next(i for i in range(desde, len(lineas)) if lineas[i].startswith(m))
        cortes.append(idx)
        desde = idx + 1
    cortes.append(len(lineas))
    out = []
    for a, b in zip(cortes, cortes[1:]):
        bloque = "\n".join(lineas[a:b])
        if b < len(lineas):
            bloque += "\n"
        out.append(bloque)
    assert "".join(out) == texto, archivo
    return out


# Respuestas de YARBYS en las demos (de ejemplo, basadas en documentos-ejemplo/)
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


def pubspec_con(paquetes):
    """pubspec.yaml de la plantilla con los paquetes que agrega 'flutter pub add'."""
    final = leer("pubspec.yaml").split("\n")
    texto = (PLANTILLA / "pubspec.yaml").read_text(encoding="utf-8")
    lineas = [l for l in final if any(l.strip().startswith(p + ":") for p in paquetes)]
    return texto.replace("  cupertino_icons: ^1.0.8\n", "  cupertino_icons: ^1.0.8\n" + "".join(l + "\n" for l in lineas))


def paso(D, P, k, rango, antes, modo="escribir", cps=20, despues=()):
    """Implementa un bloque del archivo: lo señala en la ficha, lo escribe y explica sus partes.
    despues = [(desde, hasta, titulo, nota, frase), ...]"""
    D.ficha_ver(k)
    D.say(antes)
    D.wait(1.4)
    D.ficha_ocultar()
    D.completar(P, rango, modo, cps)
    D.hold()
    for desde, hasta, titulo, nota, frase in despues:
        D.resaltar(desde, hasta, nota=nota, titulo=titulo, frases=[frase])
    D.ficha_hecho(k)


def fin_archivo(D, frase):
    """Vuelve a mostrar la ficha con todo marcado y cierra el archivo."""
    D.ficha_hechos = frozenset(range(len(D.ficha_datos[2])))
    D.ficha_ver(None)
    D.say(frase, esperar=True)
    D.wait(0.4)
    D.ficha_ocultar()


def guion():
    capturar_paginas()
    D = Director()
    D.set(mouse=(1500, 700))

    # ---------------------------------------------------------- INTRO
    D.capitulo("Introducción")
    D.slide(SlideHTML("intro"), frases=[
        "Hola, ¿qué tal? Bienvenidos. Hoy vamos a crear YARBYS: nuestro propio asistente de inteligencia artificial que vive cien por ciento dentro del celular.",
        "Lee tus documentos, recuerda tus conversaciones y te habla. Y lo mejor: funciona sin internet, incluso en modo avión.",
        "Lo haremos con Flutter, paso a paso y explicando cada concepto desde cero. Si nunca programaste con inteligencia artificial, este video es para ti.",
    ])

    # ---------------------------------------------------------- DEMO
    D.capitulo("Resultado final")
    D.demo_app("resultado", ("smartphone", "Resultado final", "YARBYS <span class='acento'>en acción</span>"), [
        ("decir", "Antes de empezar, mira el resultado final. Este es YARBYS en mi celular. Y fíjate en algo: está en modo avión, no hay internet."),
        ("nota", "plane", "Modo avión: sin internet", VERDE),
        ("decir", "Le pregunto qué tengo el miércoles."),
        ("preguntar", "¿Qué tengo el miércoles?", R_MIERCOLES, ["agenda.txt"]),
        ("nota", "file-text", "Respondió con mi agenda.txt", AMARILLO),
        ("decir", "Respondió con mi agenda, que guardé en la app, y además me dice de qué documento sacó la información. Ahora le hablo con el micrófono."),
        ("preguntar", "¿Y cómo se llama mi perro?", R_PERRO, ["perfil.txt"], True),
        ("nota", "mic", "Me entendió por voz", CELESTE),
        ("decir", "Me entendió por voz y me respondió hablando. Y todo esto ocurre dentro del teléfono: el modelo de inteligencia artificial, la base de datos y la memoria."),
        ("nota", *F_GEMMA),
    ], inicial=[("pantalla", "chat"), ("avion", True), ("docs", [["perfil.txt", 1], ["agenda.txt", 1]])])

    # ---------------------------------------------------------- TEORÍA
    D.capitulo("¿IA en el celular?")
    D.slide(SlideHTML("ia_celular"), frases=[
        "Primero, un poco de teoría. Cuando usas ChatGPT, tu pregunta viaja por internet hasta un centro de datos lleno de computadoras gigantes. Allí se genera la respuesta, y vuelve a tu teléfono.",
        "En YARBYS es distinto. El modelo de inteligencia artificial es un archivo que descargamos una sola vez, y que vive dentro del celular. El procesador del teléfono hace todo el trabajo.",
        "Eso tiene grandes ventajas: tus datos nunca salen del teléfono, funciona sin internet, no pagas por cada pregunta y no esperas a ningún servidor.",
        "¿Las desventajas? El modelo es más pequeño que los de la nube, ocupa espacio, y usa la memoria RAM y la batería. Por eso elegiremos un modelo pensado para celulares.",
    ])
    D.capitulo("Las 5 piezas")
    D.slide(SlideHTML("piezas"), frases=[
        "Para construir a YARBYS necesitamos cinco piezas, y todas viven dentro del celular.",
        "Un cerebro, que es el modelo de lenguaje: Gemma 4. Y un traductor de textos a números: EmbeddingGemma.",
        "Un buscador de información, que es la base de datos vectorial Qdrant Edge. Y una memoria para las conversaciones: SQLite.",
        "Y la voz, para escuchar y hablar. Flutter será el cuerpo: la app que une todas las piezas, y que funciona en Android y en iPhone.",
    ])
    D.capitulo("¿Qué es un LLM?")
    D.slide(SlideHTML("llm"), frases=[
        "Empecemos por el cerebro: el LLM, o modelo de lenguaje grande. Es una inteligencia artificial que aprendió a escribir leyendo muchísimo texto: libros, páginas web y conversaciones.",
        "Funciona como el autocompletado del teclado de tu celular, pero mucho más inteligente. Divide el texto en pedacitos llamados tokens, y calcula cuál es el siguiente token más probable.",
        "Así, token por token, va escribiendo la respuesta. Por eso, en la app, verás que la respuesta aparece poco a poco.",
        "Todo lo que el modelo aprendió se guarda en miles de millones de números, llamados parámetros. Más parámetros suele significar más inteligencia, pero también un archivo más pesado.",
    ])
    D.capitulo("Modelos para celular")
    D.slide(SlideHTML("tamanos"), frases=[
        "Los modelos de la nube tienen cientos de miles de millones de parámetros. Necesitan centros de datos enormes: no caben en un teléfono.",
        "Pero existen modelos pequeños, diseñados para celulares. Y además se comprimen con una técnica llamada cuantización: cada número se guarda con menos bits, como cuando comprimes una foto.",
        "Nosotros usaremos Gemma 4 E2B, de Google. Es gratuito, entiende muy bien el español, y su archivo pesa 2.6 gigas. Lo ejecutaremos con LiteRT-LM, el motor de Google para correr modelos en celulares.",
        "Para usarlo, tu celular necesita Android 11 o superior y, de preferencia, 8 gigas de RAM. Con 6 también funciona, pero más lento. Y unos 3 gigas libres.",
    ])
    D.capitulo("Embeddings")
    D.slide(SlideHTML("embeddings"), frases=[
        "Ahora, ¿cómo encuentra YARBYS la información correcta dentro de tus documentos? Con embeddings.",
        "Un embedding convierte un texto en una lista de números, llamada vector. EmbeddingGemma 2, que también es de Google y pesa solo 165 megas, genera 768 números por cada texto.",
        "Lo genial es que los textos con significado parecido quedan cerca, como en un mapa: la agenda por un lado, tu mascota por otro, tus gustos por otro.",
        "Entonces, la pregunta '¿Qué tengo el miércoles?' queda justo al lado de 'Miércoles: entregar el proyecto', aunque usen palabras distintas.",
    ])
    D.capitulo("Fragmentos")
    D.slide(SlideHTML("fragmentos"), frases=[
        "Pero antes de crear los embeddings, cortamos cada documento en fragmentos. ¿Por qué? Porque un solo vector para un documento enorme mezclaría demasiadas ideas.",
        "Lo cortamos en pedazos de unos 800 caracteres, sin partir los párrafos. Y cada fragmento tendrá su propio vector.",
    ])
    D.capitulo("Qdrant Edge")
    D.slide(SlideHTML("qdrant"), frases=[
        "Esos vectores los guardamos en una base de datos vectorial. Es como una biblioteca que ordena los textos por su significado, y no por orden alfabético.",
        "Usaremos Qdrant Edge: la misma tecnología de Qdrant, una de las bases vectoriales más usadas, pero en una versión que corre dentro de la app, sin servidor.",
        "Cuando haces una pregunta, Qdrant la compara con todos los fragmentos y te devuelve los más parecidos, cada uno con un puntaje de similitud.",
    ])
    D.capitulo("RAG")
    D.slide(SlideHTML("rag"), frases=[
        "Juntando estas piezas tenemos la técnica más usada para crear asistentes con inteligencia artificial: RAG, que en español significa generación aumentada por recuperación.",
        "Primero llega tu pregunta. La convertimos en vector con EmbeddingGemma, y buscamos en Qdrant los tres fragmentos más parecidos.",
        "Luego armamos un mensaje para Gemma con esos fragmentos, la conversación reciente y tu pregunta. A ese mensaje lo llamamos prompt.",
        "Y Gemma responde usando tus propios datos. Así no se inventa las cosas.",
    ])
    D.capitulo("Memoria")
    D.slide(SlideHTML("memoria"), frases=[
        "La siguiente pieza es la memoria. Un LLM, por sí solo, no recuerda nada. Cada pregunta es como hablar con alguien que te acaba de conocer.",
        "Por eso guardamos cada conversación, a la que llamamos hilo, en SQLite: una base de datos que es un solo archivo dentro de la app. Tendremos una tabla de hilos y otra de mensajes.",
        "Y en cada pregunta le enviamos a Gemma los últimos seis mensajes. Así puede seguir la conversación.",
    ])
    D.capitulo("La voz")
    D.slide(SlideHTML("voz"), frases=[
        "Para la voz usamos los motores que ya trae el celular. Uno convierte tu voz en texto, y otro lee el texto en voz alta. En Flutter los usamos con dos paquetes: speech_to_text y flutter_tts.",
        "En la mayoría de celulares también funcionan sin internet, si tienes descargado el idioma español.",
    ])
    D.capitulo("Flutter")
    D.slide(SlideHTML("flutter"), frases=[
        "Y el cuerpo de YARBYS es Flutter, el framework de Google para crear apps. Con un solo código, en lenguaje Dart, tienes tu app para Android y para iPhone.",
        "En Flutter todo es un widget: un texto, un botón, una lista. Y los combinamos como bloques de Lego para armar cada pantalla.",
        "Las piezas de inteligencia artificial las agregamos con paquetes de pub.dev, la tienda de librerías de Flutter. El principal será flutter_edge_ai, que ejecuta Gemma dentro del celular.",
    ])
    D.capitulo("Arquitectura")
    D.slide(SlideHTML("arquitectura"), frases=[
        "Este es el plan completo, y todo ocurre dentro del celular.",
        "Las pantallas, hechas con Flutter, le pasan tu pregunta a nuestros servicios: memoria, conocimiento, voz y cerebro.",
        "Conocimiento busca en Qdrant con EmbeddingGemma, memoria lee el historial en SQLite, y cerebro le pregunta a Gemma 4.",
        "Internet solo se usa una vez, para descargar los modelos desde Hugging Face. Y, si el usuario quiere, para conectarse a un LLM externo como GPT-6 Luna o Claude Haiku. Pero eso es opcional.",
    ])
    D.capitulo("Instalación")
    D.slide(SlideHTML("instalacion"), frases=[
        "Pasemos a la instalación en Windows. Primero, Flutter: lo descargas desde flutter.dev, lo descomprimes, por ejemplo, en C:\\flutter, y agregas la carpeta bin al PATH.",
        "Segundo, Android Studio. Trae el Android SDK, que es lo que necesitamos para compilar apps de Android.",
        "Tercero, Visual Studio Code con la extensión de Flutter. Y cuarto, tu celular Android con la depuración USB activada.",
        "Para activarla: en Ajustes, Acerca del teléfono, toca siete veces Número de compilación. Luego, en Opciones de desarrollador, activa Depuración USB, y conecta el celular a la computadora con el cable.",
    ])

    # ---------------------------------------------------------- PASO 1: PROYECTO
    D.s = Estado()
    D.set(mouse=(1200, 640), raiz="PROYECTOS")
    D.capitulo("Paso 1 · Crear el proyecto")
    D.say("Con todo instalado, abrimos Visual Studio Code. Yo abrí la carpeta C:\\proyectos con File, Open Folder. Y abrimos la terminal con Control + comilla invertida.")
    D.wait(2.5)
    D.abrir_terminal()
    D.hold()
    D.say("Primero revisamos que todo esté bien instalado con flutter doctor.")
    D.comando("flutter doctor")
    D.salida("Doctor summary (to see all details, run flutter doctor -v):", BLANCO, 0.6)
    for item in ["Flutter (Channel stable, 3.47.7, on Microsoft Windows, locale es-PE)",
                 "Windows Version (Windows 11 or higher)",
                 "Android toolchain - develop for Android devices (Android SDK version 36.1.0)",
                 "Chrome - develop for the web", "Android Studio (version 2025.2)", "VS Code (version 1.105)",
                 "Connected device (3 available)", "Network resources"]:
        D.salida_segs([("[√] ", G), (item, BLANCO)], 0.35)
    D.salida("", BLANCO, 0.1)
    D.salida_segs([("• No issues found!", G)], 0.3)
    D.fin_comando()
    D.hold()
    D.say("Si todo sale con un check verde, estamos listos. Ahora creamos el proyecto con flutter create.", esperar=True)
    D.say("Con --org ponemos el identificador de nuestra empresa, y con --platforms indicamos que la app será para Android y para iPhone.")
    D.comando("flutter create --org com.paulantezana --platforms android,ios yarbys")
    for linea, p in [("Creating project yarbys...", 0.8), ("Resolving dependencies in `yarbys`...", 0.9),
                     ("Downloading packages...", 1.0), ("Got dependencies in `yarbys`.", 0.3), ("Wrote 75 files.", 0.3),
                     ("", 0.1), ("All done!", 0.2), ("In order to run your application, type:", 0.1), ("", 0.05),
                     ("  $ cd yarbys", 0.05), ("  $ flutter run", 0.05), ("", 0.05),
                     ("Your application code is in yarbys\\lib\\main.dart.", 0.2)]:
        D.salida(linea, BLANCO, p)
    D.set(carpetas={"yarbys"})
    D.fin_comando()
    D.hold()
    D.say("Listo. Ahora abrimos la carpeta yarbys con File, Open Folder.", esperar=True)
    archivos, carpetas = archivos_plantilla()
    D.s = Estado()
    D.cwd = "C:\\proyectos\\yarbys"
    D.estado_terminales = {}
    D.set(raiz="YARBYS", files=archivos, carpetas=carpetas, abiertas=frozenset({"lib", "test"}), mouse=(1000, 500))
    D.abrir_terminal()
    D.say("Este es un proyecto de Flutter. Las carpetas android e ios tienen la configuración de cada sistema. En lib va nuestro código en Dart, y pubspec.yaml es como la lista de compras del proyecto: ahí van los paquetes que usamos.", esperar=True)

    # ---------------------------------------------------------- PASO 2: PAQUETES
    D.capitulo("Paso 2 · Paquetes")
    D.say("Ahora los paquetes. Los paquetes de Flutter se buscan en pub.dev, así que abrimos el navegador.")
    D.wait(1.5)
    D.navegador_abrir()
    D.navegador_ir("pub.dev", "pub_inicio")
    D.hold()
    D.say("En el buscador escribimos flutter_edge_ai.")
    D.navegador_escribir("busqueda", "flutter_edge_ai")
    D.navegador_enter("pub.dev/packages?q=flutter_edge_ai", "pub_busqueda")
    D.hold()
    D.say("Y abrimos el primer resultado.")
    D.navegador_clic("resultado", "pub.dev/packages/flutter_edge_ai", "pub_paquete")
    D.hold()
    D.navegador_marcar("titulo", 0.4)
    D.say("Esta es la página del paquete. Aquí dice qué hace, en qué plataformas funciona y cómo se usa. flutter_edge_ai es el que ejecuta Gemma dentro del celular. Vamos a la pestaña Installing.", esperar=True)
    D.navegador_clic("instalar", "pub.dev/packages/flutter_edge_ai/install", "pub_instalar")
    D.navegador_marcar("comando", 0.4)
    D.say("Aquí está el comando para instalarlo: flutter pub add flutter_edge_ai.", esperar=True)
    D.say("Junto con él usaremos tres complementos de la misma familia: flutter_edge_ai_litertlm, el motor que ejecuta los modelos, y flutter_edge_ai_rag y flutter_edge_ai_qdrant, para la búsqueda con Qdrant Edge. Cada uno tiene su página en pub.dev y se instala igual.", esperar=True)
    D.navegador_cerrar()
    D.say("Volvemos a VS Code y, en la terminal, agregamos los cuatro juntos con flutter pub add.")
    ia = ["flutter_edge_ai", "flutter_edge_ai_litertlm", "flutter_edge_ai_rag", "flutter_edge_ai_qdrant"]
    D.comando("flutter pub add " + " ".join(ia))
    D.salida("Resolving dependencies...", BLANCO, 1.2)
    D.salida("Downloading packages...", BLANCO, 1.0)
    for p, v in [("flutter_edge_ai", "2.3.3"), ("flutter_edge_ai_litertlm", "1.13.3"), ("flutter_edge_ai_qdrant", "2.1.0"),
                 ("flutter_edge_ai_rag", "1.1.1"), ("qdrant_edge", "0.8.0-dev.5")]:
        D.salida_segs([("+ ", G), (f"{p} {v}", BLANCO)], 0.12)
    D.salida("Changed 41 dependencies!", BLANCO, 0.2)
    D.set(files={**D.s.files, "pubspec.yaml": pubspec_con(ia)})
    D.fin_comando()
    D.hold()
    otros = ["sqflite", "path_provider", "path", "file_picker", "flutter_secure_storage", "http", "speech_to_text", "flutter_tts"]
    D.say("Y después el resto: sqflite para SQLite, path_provider para las carpetas, file_picker para elegir archivos, flutter_secure_storage para guardar la API key, http, y los dos paquetes de voz.")
    D.comando("flutter pub add " + " ".join(otros), cps=16)
    D.salida("Resolving dependencies...", BLANCO, 1.0)
    D.salida("Downloading packages...", BLANCO, 0.8)
    for p in otros:
        D.salida_segs([("+ ", G), (p, BLANCO)], 0.1)
    D.salida("Changed 46 dependencies!", BLANCO, 0.2)
    D.set(files={**D.s.files, "pubspec.yaml": pubspec_con(ia + otros)})
    D.fin_comando()
    D.hold()
    D.abrir_desde_explorador("pubspec.yaml")
    D.resaltar("flutter_edge_ai:", "flutter_edge_ai_qdrant:", titulo="Paquetes de IA",
               nota="flutter_edge_ai + litertlm: ejecutan Gemma en el celular\nrag + qdrant: búsqueda con Qdrant Edge",
               frases=["Fíjate que flutter pub add los anotó en pubspec.yaml. flutter_edge_ai y su motor LiteRT-LM ejecutan Gemma en el celular, y los paquetes rag y qdrant nos dan la búsqueda con Qdrant Edge."])

    # ---------------------------------------------------------- PASO 3: ANDROID
    D.capitulo("Paso 3 · Configurar Android")
    D.say("Ahora configuramos Android. Abrimos android, app, build.gradle.kts.")
    D.abrir_desde_explorador("android/app/build.gradle.kts")
    D.hold()
    D.say("Gemma necesita Android 11 o superior, que es la versión 30 de la API. Cambiamos minSdk por 30.")
    D.reemplazar("minSdk = flutter.minSdkVersion", "// Gemma 4 y EmbeddingGemma (.litertlm) necesitan Android 11 o superior\n        minSdk = 30")
    D.guardar()
    D.verificar("android/app/build.gradle.kts")
    D.hold()
    D.say("Y en android, app, src, main, abrimos AndroidManifest.xml: ahí van los permisos de la app.")
    D.abrir_desde_explorador("android/app/src/main/AndroidManifest.xml")
    D.hold()
    D.say("Agregamos el permiso de internet, para descargar los modelos, y el del micrófono, para hablar con YARBYS.")
    D.insertar_debajo('<manifest xmlns:android="http://schemas.android.com/apk/res/android">',
                      '    <!-- Internet solo para descargar los modelos (y para el LLM externo opcional) -->\n'
                      '    <uses-permission android:name="android.permission.INTERNET"/>\n'
                      '    <!-- Micrófono para hablar con YARBYS -->\n'
                      '    <uses-permission android:name="android.permission.RECORD_AUDIO"/>')
    D.hold()
    D.say("Cambiamos el nombre visible de la app a YARBYS, en mayúsculas.")
    D.reemplazar('android:label="yarbys"', 'android:label="YARBYS"')
    D.hold()
    D.say("Y en la sección queries avisamos que usaremos el reconocimiento de voz y la lectura en voz alta del sistema.")
    D.insertar_debajo("</intent>",
                      "        <!-- Reconocimiento de voz (speech_to_text) y lectura en voz alta (flutter_tts) -->\n"
                      "        <intent>\n"
                      '            <action android:name="android.speech.RecognitionService"/>\n'
                      "        </intent>\n"
                      "        <intent>\n"
                      '            <action android:name="android.intent.action.TTS_SERVICE"/>\n'
                      "        </intent>")
    D.guardar()
    D.verificar("android/app/src/main/AndroidManifest.xml")
    D.hold()
    D.say("Para iPhone necesitas una Mac con Xcode; te dejo los pasos en el README del repositorio.", esperar=True)
    D.set(abiertas=frozenset({"lib"}), term_abierto=False)
    D.atajo("Ctrl + `")
    D.wait(0.4)

    # ---------------------------------------------------------- PASO 4: ESTRUCTURA
    D.capitulo("Paso 4 · Los archivos")
    D.say("Antes de escribir código, vamos a crear todos los archivos del proyecto, y te explico para qué sirve cada uno. Así tendrás el mapa completo en la cabeza.", esperar=True)
    for ruta, frase in [
        ("lib/servicios/modelos.dart", "En lib creamos la carpeta servicios, que es la lógica de YARBYS: no se ve en la pantalla, pero hace todo el trabajo. El primero es modelos.dart, que descarga los dos modelos de inteligencia artificial."),
        ("lib/servicios/memoria.dart", "memoria.dart guarda las conversaciones en SQLite."),
        ("lib/servicios/conocimiento.dart", "conocimiento.dart aprende tus documentos y busca en ellos con Qdrant."),
        ("lib/servicios/cerebro.dart", "cerebro.dart arma el prompt y le pregunta a Gemma."),
        ("lib/servicios/voz.dart", "voz.dart escucha tu voz y lee las respuestas en voz alta."),
        ("lib/servicios/ajustes.dart", "Y ajustes.dart guarda las preferencias del usuario y su API key."),
        ("lib/widgets/nucleo.dart", "En la carpeta widgets va nucleo.dart, el círculo animado de YARBYS. Un widget es una pieza visual que podemos reutilizar."),
        ("lib/tema.dart", "tema.dart tiene los colores de la app."),
        ("lib/pantallas/inicio.dart", "Y en la carpeta pantallas, lo que ve el usuario: inicio, que descarga los modelos,"),
        ("lib/pantallas/chat.dart", "chat, la pantalla principal,"),
        ("lib/pantallas/documentos.dart", "documentos, para agregar tus archivos,"),
        ("lib/pantallas/ajustes.dart", "y ajustes."),
    ]:
        D.say(frase)
        D.nuevo_archivo(ruta)
        D.hold()
    D.ficha("lib/", "El mapa del proyecto. main.dart ya existía: es el punto de partida, y lo dejamos para el final.", [
        ("carpeta", "servicios/", "La lógica: modelos · memoria · conocimiento · cerebro · voz · ajustes"),
        ("carpeta", "widgets/", "nucleo: el círculo animado"),
        ("carpeta", "pantallas/", "Lo que ve el usuario: inicio · chat · documentos · ajustes"),
        ("archivo", "tema.dart", "Los colores"),
        ("archivo", "main.dart", "El punto de partida"),
    ])
    D.say("Este es el mapa del proyecto. main.dart ya existía: es el punto de partida, y lo dejaremos para el final.", esperar=True)
    D.say("Y cada archivo lo escribiremos siempre en el mismo orden: primero para qué sirve, luego sus clases, luego sus métodos, y al final lo que hace cada método por dentro.", esperar=True)
    D.ficha_ocultar()

    # ---------------------------------------------------------- MODELOS
    D.capitulo("Paso 5 · modelos.dart")
    P = Plan("lib/servicios/modelos.dart")
    D.abrir_desde_explorador(P.ruta)
    D.ficha("modelos.dart", "Descarga los dos modelos de IA una sola vez. Después, todo funciona sin internet.", [
        ("clase", "Modelos", "Todo lo de los modelos, en un solo lugar"),
        ("constante", "urlGemma", "Dónde descargar Gemma 4"),
        ("constante", "urlEmbeddings", "Dónde descargar EmbeddingGemma"),
        ("getter", "listos", "¿Ya están en el celular?"),
        ("método", "descargarEmbeddings()", "Descarga EmbeddingGemma"),
        ("método", "descargarGemma()", "Descarga Gemma 4"),
    ])
    D.say("Empezamos por modelos.dart. A la derecha tienes el mapa de este archivo: una clase, Modelos, con dos direcciones web, una propiedad para saber si los modelos ya están descargados, y dos métodos para descargarlos.", esperar=True)
    url_g = P.bloque("// El cerebro (LLM)", "gemma-4-E2B-it.litertlm';")
    url_g = (url_g[0], url_g[1] + 1)
    url_e = P.bloque("// Los embeddings:", "embeddinggemma-2-text-270m.litertlm';")
    listos = P.bloque("/// ¿Ya están descargados", "FlutterEdgeAi.hasActiveModel()")
    listos = (listos[0], listos[1] + 1)
    c_emb, c_gem = P.cuerpo("static Future<void> descargarEmbeddings"), P.cuerpo("static Future<void> descargarGemma")
    D.say("Primero escribimos la estructura: la clase y los métodos, todavía vacíos.")
    D.esqueleto(P, [url_g, url_e, listos, c_emb, c_gem], cps=19)
    D.hold()
    D.ficha_explicar(0, "Una clase es como un molde que agrupa datos y funciones. Modelos solo agrupa funciones; por eso todo será static: lo usamos sin crear objetos, por ejemplo Modelos.descargarGemma.", "class Modelos {")
    D.ficha_explicar(4, "descargarEmbeddings recibe una función, progreso, a la que le avisaremos el porcentaje de la descarga. Es async porque descargar toma tiempo, y así la app no se congela mientras espera.", "static Future<void> descargarEmbeddings")
    D.ficha_explicar(5, "descargarGemma es igual, pero para Gemma 4. Future<void> significa que el método termina más tarde y no devuelve ningún valor.", "static Future<void> descargarGemma")
    D.ficha_ver(1)
    D.say("Ahora necesitamos las direcciones de los modelos. ¿De dónde las sacamos?", esperar=True)
    D.ficha_ocultar()
    D.slide(SlideHTML("hf", {"nombre": "Gemma 4 E2B", "busqueda": "gemma-4-E2B-it-litert-lm", "cuenta": "litert-community",
                             "repo": "gemma-4-E2B-it-litert-lm", "version": "main", "version_txt": "la versión más reciente",
                             "archivo": "gemma-4-E2B-it.litertlm", "peso": "2.6 GB",
                             "nota": "Si el enlace copiado termina en ?download=true, puedes quitar esa parte"}), frases=[
        "Los modelos abiertos se publican en Hugging Face, la plataforma donde Google y otras empresas comparten sus modelos.",
        "Entras a huggingface.co, buscas gemma-4-E2B-it-litert-lm y abres el modelo de la cuenta litert-community. En la pestaña Files and versions está el archivo gemma-4-E2B-it.litertlm, de 2.6 gigas. Haces clic derecho en su botón de descarga y copias la dirección del enlace.",
        "Fíjate en las partes del enlace: el sitio, quién lo publica, el nombre del modelo, la palabra resolve, que significa descargar, la versión, que aquí es main, la más reciente, y el nombre del archivo.",
    ])
    paso(D, P, 1, url_g, "Volvemos a VS Code y creamos la constante urlGemma. La dirección no la escribimos a mano: la pegamos.")
    D.slide(SlideHTML("hf", {"nombre": "EmbeddingGemma 2", "busqueda": "embeddinggemma-2-text-270m-litert-lm", "cuenta": "litert-community",
                             "repo": "embeddinggemma-2-text-270m-litert-lm", "version": "9be6e8b9...dbac7",
                             "version_txt": "una versión exacta (commit)", "archivo": "embeddinggemma-2-text-270m.litertlm", "peso": "165 MB"}), frases=[
        "Para EmbeddingGemma es igual: buscas embeddinggemma-2-text-270m-litert-lm y copias el enlace del archivo .litertlm, de 165 megas.",
        "Pero hay un detalle. En vez de main, usamos un código de versión exacta, llamado commit. Así, si algún día publican otro archivo con el mismo nombre, YARBYS sigue usando exactamente el mismo modelo.",
        "¿Y qué código usamos? El que recomienda la documentación del paquete. Vamos a verla.",
    ])
    D.set(mouse=(900, 500))
    D.navegador_abrir()
    D.navegador_ir("pub.dev/packages/flutter_edge_ai_litertlm", "pub_litertlm")
    D.say("En la página de flutter_edge_ai_litertlm, en la sección EmbeddingGemma 2...")
    D.navegador_desplazar("eg2", 1.4)
    D.hold()
    D.navegador_marcar("codigo_eg2", 0.6)
    D.say("...está el código de versión, en la constante revision, y debajo el enlace del modelo, escrito en tres partes.", esperar=True)
    D.say("Para tener la dirección completa, juntamos las tres partes y cambiamos signo de dólar revision por ese código. O, más fácil: en Hugging Face, en el historial de versiones del modelo, abres esa versión y copias el enlace de descarga del archivo, igual que con Gemma.", esperar=True)
    D.navegador_cerrar()
    paso(D, P, 2, url_e, "Y lo pegamos en la constante urlEmbeddings.")
    paso(D, P, 3, listos, "Ahora listos: nos dice si los dos modelos ya están en el celular, para no descargarlos otra vez.",
         despues=[("FlutterEdgeAi.hasActiveModel()", None, "Una línea", "=> devuelve el resultado directamente\n&& : los dos tienen que estar listos",
                   "La flecha devuelve el resultado directamente. hasActiveModel revisa Gemma, hasActiveEmbedder revisa EmbeddingGemma, y con el doble ampersand, los dos tienen que estar listos.")])
    paso(D, P, 4, c_emb, "Implementamos descargarEmbeddings.", cps=20,
         despues=[("await FlutterEdgeAi.installEmbedder()", ".install();", "Descargar e instalar",
                   "installEmbedder(): el modelo de embeddings\nmodelFromNetwork: desde la URL\nwithModelProgress: avisa el %",
                   "installEmbedder prepara la instalación del modelo de embeddings, modelFromNetwork le dice que lo baje de nuestra URL, withModelProgress nos avisa el porcentaje, e install lo descarga. Con await esperamos a que termine.")])
    paso(D, P, 5, c_gem, "Y descargarGemma.", cps=20,
         despues=[("await FlutterEdgeAi.installModel(", ").fromNetwork(urlGemma)", "Gemma 4",
                   "modelType: gemma4 → cómo habla el modelo\nfileType: litertlm → el motor LiteRT-LM",
                   "installModel es lo mismo para el LLM. modelType le dice a la librería que es Gemma 4, y fileType, que es un archivo .litertlm, el formato del motor LiteRT-LM.")])
    D.guardar()
    D.verificar(P.ruta)
    fin_archivo(D, "Y modelos.dart está completo.")

    # ---------------------------------------------------------- MEMORIA
    D.capitulo("Paso 6 · memoria.dart")
    P = Plan("lib/servicios/memoria.dart")
    D.abrir_desde_explorador(P.ruta)
    D.ficha("memoria.dart", "La memoria de YARBYS: guarda y lee las conversaciones en una base de datos SQLite.", [
        ("clase", "Mensaje", "Un mensaje: quién habló, qué dijo y qué documentos usó"),
        ("clase", "Hilo", "Una conversación"),
        ("clase", "Documento", "Un documento que YARBYS aprendió"),
        ("clase", "Memoria", "La base de datos"),
        ("método", "abrir()", "Abre el archivo y crea las tablas"),
        ("método", "nuevoHilo() · hilos() · borrarHilo() · borrarTodo()", "Crear, listar y borrar conversaciones"),
        ("método", "guardar() · mensajes()", "Guardar y leer mensajes"),
        ("método", "guardarDocumento() · documentos()", "Anotar los documentos aprendidos"),
    ])
    D.say("Seguimos con memoria.dart. Tendrá cuatro clases: tres pequeñas que representan los datos —un mensaje, un hilo o conversación, y un documento—, y la clase Memoria, que los guarda y los lee de SQLite.", esperar=True)
    c_abrir = P.cuerpo("static Future<void> abrir()")
    m_nuevo = P.bloque("static Future<int> nuevoHilo", "_db.insert('hilos'")
    m_nuevo = (m_nuevo[0], m_nuevo[1] + 1)
    c_hilos = P.cuerpo("static Future<List<Hilo>> hilos()")
    c_bhilo = P.cuerpo("static Future<void> borrarHilo")
    c_btodo = P.cuerpo("static Future<void> borrarTodo")
    m_guardar = P.bloque("static Future<void> guardar(int hilo", "});")
    m_guardar = (m_guardar[0], m_guardar[1] + 1)
    c_mensajes = P.cuerpo("static Future<List<Mensaje>> mensajes(")
    m_gdoc = P.bloque("static Future<int> guardarDocumento", "});")
    m_gdoc = (m_gdoc[0], m_gdoc[1] + 1)
    c_docs = P.cuerpo("static Future<List<Documento>> documentos()")
    m_bdoc = P.bloque("static Future<void> borrarDocumento", "_db.delete('documentos'")
    m_bdoc = (m_bdoc[0] - 1, m_bdoc[1])   # con la línea en blanco de arriba
    D.say("Escribimos la estructura. Las tres clases de datos son cortas: solo tienen sus campos y un constructor.")
    D.esqueleto(P, [c_abrir, m_nuevo, c_hilos, c_bhilo, c_btodo, m_guardar, c_mensajes, m_gdoc, c_docs, m_bdoc], cps=22)
    D.hold()
    D.ficha_explicar(0, "Mensaje tiene tres campos: el rol, que dice quién habló, el texto, y las fuentes. final significa que no cambian después de crearse. La línea de arriba es el constructor: la forma de crear un mensaje.", "class Mensaje {")
    D.ficha_explicar(0, "Y esUsuario es un getter: una propiedad calculada que nos dice si el mensaje lo escribió el usuario.", "bool get esUsuario")
    D.ficha_explicar(1, "Hilo es una conversación, con su id y un título.", "class Hilo {")
    D.ficha_explicar(2, "Y Documento guarda el nombre del archivo y en cuántos fragmentos lo cortamos.", "class Documento {")
    D.ficha_explicar(3, "La clase Memoria guarda la conexión con la base de datos en _db. El guion bajo la hace privada: solo se usa dentro de este archivo.", "static late Database _db;")
    D.ficha_explicar(4, "abrir abre la base de datos al arrancar la app.", "static Future<void> abrir()")
    D.ficha_explicar(5, "Y estos métodos trabajan con los hilos: listarlos, borrar uno o borrarlos todos.", "static Future<List<Hilo>> hilos()")
    D.ficha_explicar(6, "mensajes lee los mensajes de un hilo.", "static Future<List<Mensaje>> mensajes(")
    paso(D, P, 4, c_abrir, "Implementamos abrir.", cps=22,
         despues=[("final ruta = p.join", "_db = await openDatabase(", "El archivo de la base de datos",
                   "getDatabasesPath(): la carpeta de bases de datos de la app\nyarbys.db: un solo archivo",
                   "Armamos la ruta del archivo yarbys.db, dentro de la carpeta de la app, y openDatabase lo abre. Si no existe, lo crea."),
                  ("onCreate: (db, version) async {", "fuentes TEXT NOT NULL DEFAULT", "Las tablas (SQL)",
                   "onCreate solo corre la primera vez\nhilos: cada conversación\nmensajes: cada mensaje, con el id de su hilo",
                   "onCreate se ejecuta solo la primera vez. Con el lenguaje SQL creamos las tablas: hilos, con cada conversación, y mensajes, donde cada mensaje guarda el id del hilo al que pertenece. La tabla documentos es igual.")])
    paso(D, P, 5, m_nuevo, "Ahora los hilos. nuevoHilo crea una conversación con insert, que agrega una fila a la tabla, y devuelve su id.", cps=22)
    paso(D, P, 5, c_hilos, "hilos los lee todos con query, del más nuevo al más viejo, y convierte cada fila en un Hilo.", cps=22)
    paso(D, P, 5, c_bhilo, "borrarHilo borra sus mensajes y luego el hilo.", modo="pegar")
    paso(D, P, 5, c_btodo, "Y borrarTodo vacía las dos tablas.", modo="pegar")
    paso(D, P, 6, m_guardar, "guardar inserta un mensaje en la tabla mensajes. Las fuentes las unimos con una barra vertical, porque SQLite guarda texto.", cps=22)
    paso(D, P, 6, c_mensajes, "Y mensajes es el que le da memoria a YARBYS.", cps=22,
         despues=[("orderBy: 'id DESC',", "limit: ultimos,", "Los últimos mensajes",
                   "orderBy id DESC + limit: los más recientes\nreversed: los ponemos en orden",
                   "Pide los mensajes del hilo del más nuevo al más viejo, y con limit solo los últimos. Luego los volteamos con reversed para leerlos en orden, y convertimos cada fila en un Mensaje.")])
    paso(D, P, 7, m_gdoc, "Los métodos de documentos son iguales a los de hilos; los pego.", modo="pegar")
    D.completar(P, c_docs, modo="pegar")
    D.completar(P, m_bdoc, modo="pegar")
    D.guardar()
    D.verificar(P.ruta)
    fin_archivo(D, "Memoria lista.")

    # ---------------------------------------------------------- CONOCIMIENTO
    D.capitulo("Paso 7 · conocimiento.dart")
    P = Plan("lib/servicios/conocimiento.dart")
    D.abrir_desde_explorador(P.ruta)
    D.ficha("conocimiento.dart", "Lo que YARBYS sabe de ti: tus documentos convertidos en vectores y guardados en Qdrant Edge.", [
        ("clase", "Conocimiento", "El RAG de YARBYS"),
        ("campo", "_indice", "El índice de Qdrant"),
        ("constante", "_perfil", "El tipo de vectores de EmbeddingGemma 2"),
        ("método", "abrir()", "Abre Qdrant con EmbeddingGemma"),
        ("método", "fragmentar()", "Corta un texto en pedazos"),
        ("método", "aprender()", "Guarda un documento como vectores"),
        ("método", "olvidar()", "Borra un documento"),
        ("método", "buscar()", "Búsqueda semántica"),
        ("método", "origen()", "De qué documento salió un fragmento"),
    ])
    D.say("Sigue conocimiento.dart: aquí vive el RAG. La clase Conocimiento guarda tus documentos en Qdrant y busca en ellos.", esperar=True)
    cs = {n: P.cuerpo(f) for n, f in [("abrir", "static Future<void> abrir()"), ("fragmentar", "static List<String> fragmentar("),
                                       ("aprender", "static Future<int> aprender("), ("olvidar", "static Future<void> olvidar("),
                                       ("buscar", "static Future<List<RetrievalResult>> buscar("), ("origen", "static String origen(")]}
    D.esqueleto(P, list(cs.values()), cps=22)
    D.hold()
    D.ficha_explicar(1, "_indice es el índice de Qdrant, donde están los vectores. late significa que le daremos valor más tarde, en abrir.", "static late RagIndex _indice;")
    D.ficha_explicar(2, "_perfil identifica el tipo de vectores que crea EmbeddingGemma 2. Qdrant lo guarda para no mezclar vectores de modelos distintos.", "static const _perfil")
    D.ficha_explicar(4, "fragmentar recibe un texto y devuelve una lista de fragmentos.", "static List<String> fragmentar(")
    D.ficha_explicar(5, "aprender recibe el nombre y el texto de un documento, y devuelve cuántos fragmentos guardó.", "static Future<int> aprender(")
    D.ficha_explicar(7, "Y buscar recibe la pregunta y devuelve los fragmentos más parecidos.", "static Future<List<RetrievalResult>> buscar(")
    paso(D, P, 3, cs["abrir"], "Implementamos abrir.", cps=22,
         despues=[("final rag = FlutterEdgeAiRag(", "providers: const [QdrantVectorStoreProvider()]", "Qdrant Edge",
                   "FlutterEdgeAiRag: el sistema de RAG\nQdrantVectorStoreProvider: los vectores van en Qdrant Edge",
                   "FlutterEdgeAiRag es el sistema de RAG, y le decimos que guarde los vectores con Qdrant Edge."),
                  ("_indice = await rag.open(", "embedder: FlutterEdgeAiActiveEmbedder", "Abrir el índice",
                   "location: una carpeta dentro de la app\nembedder: EmbeddingGemma crea los vectores",
                   "Abrimos el índice en una carpeta de la app, y le indicamos que EmbeddingGemma será quien convierta los textos en vectores.")])
    paso(D, P, 4, cs["fragmentar"], "fragmentar es un poco más largo; lo pego y lo explicamos.", modo="pegar",
         despues=[("for (final parrafo in texto.split", "fragmentos.add(actual);", "Fragmentar",
                   "Separa por párrafos (líneas en blanco)\nVa juntando párrafos hasta unos 800 caracteres",
                   "Separamos el texto por párrafos y los vamos juntando hasta llegar a unos 800 caracteres. Cuando no cabe uno más, guardamos el fragmento y empezamos otro."),
                  ("while (limpio.length > maximo) {", "limpio = limpio.substring(corte).trim();", "Párrafos gigantes",
                   None, "Y si un párrafo solo ya es muy largo, lo cortamos en el último espacio antes del límite, para no partir una palabra.")])
    paso(D, P, 5, cs["aprender"], "Ahora aprender.", cps=21,
         despues=[("final partes = fragmentar(texto);", "metadata: jsonEncode", "Aprender un documento",
                   "1. Fragmenta el texto\n2. Lo anota en SQLite\n3. add(): crea el vector y lo guarda en Qdrant",
                   "Fragmentamos el texto y anotamos el documento en SQLite. Luego, por cada fragmento, add crea su vector con EmbeddingGemma y lo guarda en Qdrant, junto con el nombre del documento."),
                  ("await _indice.flush();", None, None, None, "Y flush guarda los cambios en el disco.")])
    paso(D, P, 6, cs["olvidar"], "olvidar hace lo contrario: borra los fragmentos del documento. Lo pego.", modo="pegar")
    paso(D, P, 7, cs["buscar"], "Y buscar.", cps=21,
         despues=[("return _indice.search(", "threshold: 0.3,", "Búsqueda semántica",
                   "topK: 3 → los 3 fragmentos más parecidos\nthreshold: descarta los poco parecidos",
                   "search convierte la pregunta en vector y nos devuelve los tres fragmentos más parecidos. threshold descarta los que se parecen muy poco.")])
    paso(D, P, 8, cs["origen"], "origen lee el nombre del documento desde los datos que guardamos con el fragmento.", modo="pegar")
    D.guardar()
    D.verificar(P.ruta)
    fin_archivo(D, "Conocimiento listo.")

    # ---------------------------------------------------------- CEREBRO
    D.capitulo("Paso 8 · cerebro.dart")
    P = Plan("lib/servicios/cerebro.dart")
    D.abrir_desde_explorador(P.ruta)
    D.ficha("cerebro.dart", "El cerebro: arma el prompt y responde con Gemma 4 en el celular, o con un LLM externo si el usuario lo activa.", [
        ("clase", "Cerebro", ""),
        ("constante", "sistema", "La personalidad de YARBYS"),
        ("método", "armarPrompt()", "Documentos + historial + pregunta"),
        ("método", "responder()", "Elige: local o externo"),
        ("método", "_local()", "Gemma 4 dentro del celular"),
        ("método", "_externo()", "OpenAI o Anthropic (opcional)"),
        ("método", "_leer()", "Lee la respuesta de la API"),
    ])
    D.say("Llegamos al cerebro. La clase Cerebro tiene la personalidad de YARBYS y los métodos para armar el prompt y responder.", esperar=True)
    sis = P.bloque("// La personalidad de YARBYS", "Si no sabes algo")
    sis = (sis[0], sis[1] + 1)
    cs = {n: P.cuerpo(f) for n, f in [("armar", "static String armarPrompt("), ("responder", "static Stream<String> responder("),
                                       ("local", "static Stream<String> _local("), ("externo", "static Stream<String> _externo("),
                                       ("leer", "static Map<String, dynamic> _leer(")]}
    D.esqueleto(P, [sis] + list(cs.values()), cps=22)
    D.hold()
    D.ficha_explicar(2, "armarPrompt recibe la pregunta, los fragmentos encontrados, y el historial de la conversación, y devuelve el texto completo que leerá Gemma.", "static String armarPrompt(")
    D.ficha_explicar(3, "responder devuelve un Stream: un flujo de datos que llega en pedacitos. Así recibimos la respuesta token por token.", "static Stream<String> responder(")
    D.ficha_explicar(4, "_local responde con Gemma, dentro del celular. async con asterisco significa que va entregando valores poco a poco.", "static Stream<String> _local(")
    D.ficha_explicar(5, "Y _externo usa un LLM de internet. Es opcional.", "static Stream<String> _externo(")
    paso(D, P, 1, sis, "Primero la personalidad: las instrucciones de sistema.", cps=24,
         despues=[("static const sistema = '''", "Si no sabes algo", "La personalidad",
                   "Quién es y cómo responde\nMáximo 3 oraciones y sin markdown: se leen en voz alta",
                   "Le decimos quién es, que responda en español, en máximo tres oraciones y sin formato, porque las respuestas se leen en voz alta.")])
    paso(D, P, 2, cs["armar"], "Ahora armarPrompt.", cps=22,
         despues=[("final b = StringBuffer();", "b.write('Pregunta del usuario: $pregunta');", "Armar el prompt",
                   "1. Los fragmentos de tus documentos\n2. La conversación hasta ahora\n3. Tu pregunta",
                   "StringBuffer va juntando texto. Primero escribimos los fragmentos de tus documentos, luego la conversación reciente, y al final la pregunta. Exactamente lo que vimos en la parte de RAG.")])
    paso(D, P, 3, cs["responder"], "responder elige el cerebro.", cps=20,
         despues=[("return Ajustes.usarNube", None, "¿Local o externo?", None,
                   "Si el usuario activó la nube, usa el LLM externo; si no, Gemma en el celular. Ese signo de pregunta es un if en una sola línea.")])
    paso(D, P, 4, cs["local"], "Y _local, la parte más importante.", cps=21,
         despues=[("final modelo = await FlutterEdgeAi.getActiveModel", "maxOutputTokens: 512,", "Gemma 4",
                   "maxTokens: 4096 → el contexto (lo que puede leer)\nmaxOutputTokens: 512 → largo máximo de la respuesta",
                   "getActiveModel carga Gemma en la memoria. maxTokens es cuánto texto puede leer a la vez: el contexto. Y createChat crea la conversación con la personalidad y un máximo de 512 tokens de respuesta."),
                  ("await chat.addQueryChunk", "if (respuesta is TextResponse) yield", "Token por token",
                   "isUser: true → lo escribió el usuario\nyield: entrega cada token apenas llega",
                   "Le enviamos el prompt, y con yield entregamos cada token apenas Gemma lo genera. Al final, en finally, cerramos el chat.")])
    paso(D, P, 5, cs["externo"], "La parte del LLM externo es opcional. La pego y te explico lo importante.", modo="pegar",
         despues=[("final clave = await Ajustes.leerClave();", "throw Exception", "Tu propia API key",
                   "El usuario pega su API key en Ajustes\nNunca va escrita en el código",
                   "La API key la escribe cada usuario en la app; nunca va escrita en el código."),
                  ("Uri.parse('https://api.anthropic.com/v1/messages')", "'max_tokens': 512,", "Anthropic u OpenAI",
                   "Claude Haiku con la API de Anthropic\nGPT-6 Luna con la API de OpenAI",
                   "Con el paquete http enviamos el mismo prompt a Anthropic, para Claude Haiku, o a OpenAI, para GPT-6 Luna. El resto de la app no cambia.")])
    paso(D, P, 6, cs["leer"], "Y _leer convierte la respuesta en datos, o lanza un error si algo falló.", modo="pegar")
    D.guardar()
    D.verificar(P.ruta)
    fin_archivo(D, "El cerebro está completo.")

    # ---------------------------------------------------------- VOZ
    D.capitulo("Paso 9 · voz.dart y ajustes.dart")
    P = Plan("lib/servicios/voz.dart")
    D.abrir_desde_explorador(P.ruta)
    D.ficha("voz.dart", "Los oídos y la boca de YARBYS, con los motores de voz del propio celular.", [
        ("clase", "Voz", ""),
        ("campo", "_oido · _boca", "SpeechToText (voz → texto) y FlutterTts (texto → voz)"),
        ("campo", "alDejarDeEscuchar", "Aviso cuando se apaga el micrófono"),
        ("método", "escuchar()", "Escucha y devuelve el texto en vivo"),
        ("método", "dejarDeEscuchar()", ""),
        ("método", "hablar()", "Lee un texto en voz alta"),
        ("método", "callar()", ""),
    ])
    D.say("Ahora la voz. La clase Voz tiene un oído, que convierte tu voz en texto, y una boca, que lee en voz alta.", esperar=True)
    c_esc = P.cuerpo("static Future<bool> escuchar(")
    m_dejar = P.bloque("static Future<void> dejarDeEscuchar()")
    m_dejar = (m_dejar[0], m_dejar[1] + 1)
    c_hablar = P.cuerpo("static Future<void> hablar(")
    m_callar = P.bloque("static Future<void> callar()")
    m_callar = (m_callar[0] - 1, m_callar[1])
    D.esqueleto(P, [c_esc, m_dejar, c_hablar, m_callar], cps=23)
    D.hold()
    D.ficha_explicar(1, "_oido es un SpeechToText y _boca un FlutterTts: vienen de los dos paquetes de voz que instalamos.", "static final _oido = SpeechToText();")
    D.ficha_explicar(2, "alDejarDeEscuchar es una función que la pantalla del chat nos dará, para avisarle cuando el micrófono se apague.", "static void Function()? alDejarDeEscuchar;")
    D.ficha_explicar(3, "escuchar recibe la función alOir, a la que le pasaremos el texto mientras hablas, y devuelve false si no hay permiso de micrófono.", "static Future<bool> escuchar(")
    paso(D, P, 3, c_esc, "Implementamos escuchar; lo pego y lo vemos por partes.", modo="pegar",
         despues=[("if (!_oidoListo) {", "_idioma = delSistema.localeId;", "La primera vez",
                   "initialize: pide el permiso del micrófono\nsystemLocale: usa el español del celular",
                   "La primera vez, initialize prepara el reconocimiento de voz y pide el permiso del micrófono. Y si el celular está en español, usamos su idioma."),
                  ("await _oido.listen(", "pauseFor: const Duration(seconds: 3),", "Escuchar",
                   "partialResults: muestra el texto mientras hablas\npauseFor: 3 segundos de silencio y termina",
                   "listen escucha, nos va pasando el texto mientras hablas, y termina cuando te quedas en silencio tres segundos.")])
    paso(D, P, 4, m_dejar, "dejarDeEscuchar apaga el micrófono.", cps=22)
    paso(D, P, 5, c_hablar, "Y hablar.", cps=21,
         despues=[("if (!_bocaLista) {", "await _boca.speak(texto);", "Hablar",
                   "setLanguage: en español\nawaitSpeakCompletion: esperar a que termine",
                   "La primera vez configuramos la boca en español, y le pedimos que espere a terminar de hablar. Luego speak lee el texto.")])
    paso(D, P, 6, m_callar, "Y callar la detiene.", cps=22)
    D.guardar()
    D.verificar(P.ruta)
    D.ficha_ocultar()

    P = Plan("lib/servicios/ajustes.dart")
    D.abrir_desde_explorador(P.ruta)
    D.ficha("ajustes.dart", "Las preferencias del usuario, guardadas cifradas en el celular.", [
        ("clase", "Ajustes", ""),
        ("constante", "_cofre", "FlutterSecureStorage: guardado cifrado"),
        ("campo", "usarNube · proveedor · modeloNube · hablar", "Las preferencias"),
        ("campo", "esPro", "El interruptor de la versión Pro"),
        ("método", "cargar() · guardar()", "Leer y escribir el cofre"),
        ("método", "leerClave() · guardarClave()", "La API key"),
        ("getter", "nombreCerebro", "Qué cerebro está respondiendo"),
    ])
    D.say("Y ajustes.dart guarda las preferencias.", esperar=True)
    c_cargar, c_guardar = P.cuerpo("static Future<void> cargar()"), P.cuerpo("static Future<void> guardar()")
    claves = P.bloque("// La API key nunca", "value: clave.trim());")
    claves = (claves[0], claves[1] + 1)
    nombre = P.bloque("/// Texto corto para mostrar", "usarNube ? modeloNube.toUpperCase()")
    D.esqueleto(P, [c_cargar, c_guardar, claves, nombre], cps=24)
    D.hold()
    D.ficha_explicar(1, "_cofre es un FlutterSecureStorage: guarda los datos cifrados, en Android con Keystore y en iPhone con Keychain. Ideal para la API key.", "static const _cofre")
    D.ficha_explicar(2, "Estas son las preferencias. usarNube empieza en false: por defecto, YARBYS es cien por ciento local.", "static bool usarNube = false;")
    D.ficha_explicar(3, "Y esPro es el interruptor de la versión Pro. Aquí conectarías una compra dentro de la app; en este proyecto viene desbloqueada.", "static bool esPro = true;")
    paso(D, P, 4, c_cargar, "cargar lee el cofre al arrancar la app.", cps=23,
         despues=[("final datos = await _cofre.readAll();", "hablar = datos['hablar'] != 'no';", "Cargar",
                   "readAll: lee todo el cofre\n??: valor por defecto si no existe",
                   "readAll lee todo el cofre, y cada preferencia toma su valor. El doble signo de pregunta pone un valor por defecto si todavía no se guardó nada.")])
    paso(D, P, 4, c_guardar, "guardar escribe cada valor; lo pego.", modo="pegar")
    paso(D, P, 5, claves, "Y estas dos funciones leen y guardan la API key, una por proveedor.", cps=23)
    paso(D, P, 6, nombre, "nombreCerebro es el texto que mostramos debajo del núcleo.", cps=23)
    D.guardar()
    D.verificar(P.ruta)
    fin_archivo(D, "Los servicios están listos. Ahora, la parte visual.")

    # ---------------------------------------------------------- TEMA Y NÚCLEO
    D.capitulo("Paso 10 · tema.dart y el núcleo")
    P = Plan("lib/tema.dart")
    D.abrir_desde_explorador(P.ruta)
    D.ficha("tema.dart", "Los colores y el estilo de la app: fondos oscuros y planos.", [
        ("clase", "Colores", "La paleta"),
        ("función", "temaYarbys()", "El tema oscuro de la app"),
        ("widget", "Pildora", "La etiqueta 'Sin internet'"),
        ("método", "build()", "Lo que dibuja la píldora"),
    ])
    D.say("tema.dart tiene los colores, el tema y un pequeño widget: la píldora que dice Sin internet.", esperar=True)
    c_tema = P.cuerpo("ThemeData temaYarbys()")
    c_build = P.cuerpo("Widget build(BuildContext context)")
    D.esqueleto(P, [c_tema, c_build], modo="pegar")
    D.hold()
    D.ficha_explicar(0, "Colores agrupa la paleta: así cambiamos un color en un solo lugar.", "class Colores {")
    D.ficha_explicar(2, "Pildora es un StatelessWidget: un widget sin estado, que siempre se dibuja igual con los datos que recibe. Recibe un texto, un color y un ícono.", "class Pildora extends StatelessWidget")
    D.ficha_explicar(3, "Todo widget tiene un método build, que devuelve lo que se dibuja en la pantalla.", "Widget build(BuildContext context)")
    paso(D, P, 1, c_tema, "temaYarbys devuelve el tema oscuro de Material; lo pego.", modo="pegar",
         despues=[("brightness: Brightness.dark,", "error: Colores.rojo,", "El tema", None,
                   "Le decimos que es oscuro y le damos nuestros colores. Todos los botones, campos y barras los usarán.")])
    paso(D, P, 3, c_build, "Y el build de la píldora.", modo="pegar",
         despues=[("return Container(", "children: [", "Bloques de Lego",
                   "Container: la caja con fondo\nRow: pone el ícono y el texto en fila",
                   "Aquí se ve la idea de los bloques: un Container con fondo redondeado, que adentro tiene una fila, Row, con el ícono y el texto.")])
    D.guardar()
    D.verificar(P.ruta)
    D.ficha_ocultar()

    P = Plan("lib/widgets/nucleo.dart")
    D.abrir_desde_explorador(P.ruta)
    D.ficha("widgets/nucleo.dart", "El núcleo circular de YARBYS, inspirado en el JARVIS de las películas.", [
        ("enum", "EstadoYarbys", "reposo · escuchando · pensando · hablando"),
        ("widget", "Nucleo", "StatefulWidget: el que usamos en las pantallas"),
        ("estado", "_NucleoState", "Lleva la cuenta del tiempo y del giro"),
        ("método", "initState() · dispose()", "Arranca y apaga el reloj"),
        ("método", "_velocidad()", "Qué tan rápido gira cada estado"),
        ("método", "build()", "Dibuja con CustomPaint"),
        ("clase", "_PintorNucleo", "CustomPainter: el lienzo"),
        ("método", "paint()", "Dibuja los 8 anillos"),
    ])
    D.say("Y ahora lo más vistoso: el núcleo. Aquí aparece un concepto clave de Flutter: el StatefulWidget.", esperar=True)
    c_init = P.cuerpo("void initState()")
    m_vel = P.bloque("// Cada estado hace girar", "};")
    m_vel = (m_vel[0], m_vel[1] + 1)
    c_disp = P.cuerpo("void dispose()")
    c_build = P.cuerpo("Widget build(BuildContext context)")
    ayudas = P.bloque("// Alturas fijas de las barras", "tp.paint(canvas")
    ayudas = (ayudas[0], ayudas[1] + 2)
    c_paint = P.cuerpo("void paint(Canvas canvas, Size size)")
    p2 = P.buscar("    // 2. Anillo de bloques")
    p5 = P.buscar("    // 5. Dos arcos opuestos")
    m_repaint = P.bloque("bool shouldRepaint(", "old.segundos != segundos")
    m_repaint = (m_repaint[0] - 2, m_repaint[1])
    D.esqueleto(P, [c_init, m_vel, c_disp, c_build, ayudas, c_paint, m_repaint], modo="pegar")
    D.hold()
    D.ficha_explicar(0, "Un enum es una lista de opciones fijas: los cuatro estados de YARBYS.", "enum EstadoYarbys")
    D.ficha_explicar(1, "Un StatefulWidget tiene dos partes. El widget, Nucleo, recibe la configuración: el estado y el tamaño...", "class Nucleo extends StatefulWidget")
    D.ficha_explicar(2, "...y su State, _NucleoState, guarda los datos que cambian con el tiempo: los segundos y el giro. Cada vez que cambian, llamamos a setState y Flutter vuelve a dibujar.", "class _NucleoState extends State<Nucleo>")
    D.ficha_explicar(6, "Y _PintorNucleo es un CustomPainter: un lienzo donde dibujamos con código.", "class _PintorNucleo extends CustomPainter")
    paso(D, P, 3, c_init, "initState se ejecuta una vez, cuando el widget aparece.", modo="pegar",
         despues=[("_reloj = createTicker((transcurrido) {", "_giro += dt * _velocidad(widget.estado);", "Un reloj de cuadros",
                   "Ticker: avisa en cada cuadro (60 veces por segundo)\nsetState: actualiza los datos y redibuja",
                   "Creamos un Ticker, que nos avisa en cada cuadro de la pantalla, sesenta veces por segundo. En cada aviso, setState suma el tiempo y el giro, y Flutter redibuja el núcleo.")])
    paso(D, P, 4, m_vel, "_velocidad dice qué tan rápido gira cada estado: al pensar, cuatro veces más rápido.", modo="pegar")
    paso(D, P, 3, c_disp, "dispose apaga el reloj cuando el widget desaparece, para no gastar batería.", cps=22)
    paso(D, P, 5, c_build, "build entrega el lienzo: CustomPaint con nuestro pintor.", modo="pegar")
    D.say("Estas son funciones de ayuda para dibujar: un punto en el círculo, un trazo, un arco, girar y escribir texto. Las pego.")
    D.completar(P, ayudas, modo="pegar")
    D.hold()
    paso(D, P, 7, (c_paint[0], p2 - 1), "Y paint dibuja el núcleo, anillo por anillo. Pego la primera parte.", modo="pegar",
         despues=[("final r = size.width / 2 / 1.14;", "final pulso", "Medidas", None,
                   "Calculamos el radio según el tamaño, y nos movemos al centro del lienzo."),
                  ("// 1. Anillo exterior", "_trazo(c, r * 0.006, 0.35)", "Anillo 1", None,
                   "El primer anillo es un círculo fino con 120 marcas, como un reloj, que gira despacio.")])
    D.completar(P, (p2, p5 - 1), modo="pegar")
    D.resaltar("// 4. Ecualizador circular", "(0.5 + 0.5 * sin(t * 3.7 + i * 0.31));", titulo="El ecualizador",
               frases=["Luego vienen los bloques gruesos, los puntos, y este ecualizador: noventa barras que bailan cuando YARBYS escucha o habla."])
    D.completar(P, (p5, c_paint[1]), modo="pegar")
    D.resaltar("// 8. Centro: nombre y estado", "EstadoYarbys.hablando => 'HABLANDO',", titulo="El centro",
               frases=["Y al final, el centro, con el nombre y el estado actual."])
    paso(D, P, 7, m_repaint, "shouldRepaint le dice a Flutter cuándo volver a pintar: cuando cambia el tiempo o el estado.", cps=22)
    D.guardar()
    D.verificar(P.ruta)
    fin_archivo(D, "El núcleo está listo.")

    # ---------------------------------------------------------- PANTALLAS
    D.capitulo("Paso 11 · Las pantallas")
    P = Plan("lib/pantallas/inicio.dart")
    D.abrir_desde_explorador(P.ruta)
    D.ficha("pantallas/inicio.dart", "La primera pantalla: descarga los modelos una sola vez y abre el chat.", [
        ("widget", "PantallaInicio", "StatefulWidget"),
        ("estado", "_PantallaInicioState", "Progreso de las descargas y errores"),
        ("método", "initState()", "Si ya hay modelos, entra directo"),
        ("método", "_descargar()", "Descarga los dos modelos"),
        ("método", "_entrar()", "Abre Qdrant y va al chat"),
        ("método", "build()", "La pantalla"),
        ("widget", "_Descarga", "La tarjeta con la barra de progreso"),
    ])
    D.say("Ahora las pantallas. Empezamos por inicio: la que descarga los modelos la primera vez.", esperar=True)
    cs = [P.cuerpo("void initState()"), P.cuerpo("Future<void> _descargar()"), P.cuerpo("Future<void> _entrar()"),
          P.cuerpo("Widget build(BuildContext context)"), P.cuerpo("Widget build(BuildContext context)", P.buscar("class _Descarga"))]
    D.esqueleto(P, cs, modo="pegar")
    D.hold()
    D.ficha_explicar(1, "Su estado guarda el progreso de cada descarga, si está descargando, y el error, si lo hay.", "int _progresoEmbeddings = 0;")
    paso(D, P, 2, cs[0], "initState: si los modelos ya están en el celular, entramos directo.", cps=22)
    paso(D, P, 3, cs[1], "_descargar baja los dos modelos.", modo="pegar",
         despues=[("await Modelos.descargarEmbeddings(", "await _entrar();", "Descargar con progreso",
                   "setState: cambia los datos y redibuja la pantalla",
                   "Usa los métodos de Modelos. Cada vez que llega un porcentaje nuevo, setState lo guarda y Flutter redibuja la barra de progreso. Si algo falla, catch muestra el error.")])
    paso(D, P, 4, cs[2], "_entrar abre Qdrant y cambia a la pantalla del chat.", modo="pegar",
         despues=[("Navigator.of(", "pushReplacement(MaterialPageRoute(builder: (_) => const PantallaChat()));", "Navegar",
                   "Navigator: cambia de pantalla\npushReplacement: no se puede volver atrás",
                   "Navigator cambia de pantalla. Con pushReplacement, la pantalla de inicio se reemplaza y no se puede volver a ella.")])
    paso(D, P, 5, cs[3], "Y build arma la pantalla.", modo="pegar",
         despues=[("return Scaffold(", "child: ListView(", "La estructura",
                   "Scaffold: la página\nSafeArea: evita la cámara y los bordes\nListView: una lista que se desplaza",
                   "Scaffold es la página, SafeArea evita la cámara y los bordes del celular, y ListView pone todo en una lista que se puede desplazar: el núcleo, los textos, las dos tarjetas y el botón."),
                  ("onPressed: _descargando ? null : _descargar,", None, None, None,
                   "El botón llama a _descargar, y se desactiva mientras descarga.")])
    paso(D, P, 6, cs[4], "_Descarga es la tarjeta de cada modelo; la pego.", modo="pegar")
    D.guardar()
    D.verificar(P.ruta)
    D.ficha_ocultar()

    P = Plan("lib/pantallas/chat.dart")
    D.abrir_desde_explorador(P.ruta)
    D.ficha("pantallas/chat.dart", "La pantalla principal: el núcleo, los mensajes y el campo para hablar con YARBYS.", [
        ("widget", "PantallaChat", "StatefulWidget"),
        ("estado", "_PantallaChatState", "Mensajes, hilo actual y estado del núcleo"),
        ("método", "initState()", "Carga los hilos"),
        ("método", "_cargarHilos() · _abrirHilo()", "Conversaciones"),
        ("método", "_enviar()", "El corazón: buscar → pensar → responder → hablar"),
        ("método", "_microfono()", "Hablar en vez de escribir"),
        ("método", "_limpiar() · _avisar() · _bajar() · _ir()", "Ayudas"),
        ("método", "build() · _menuHilos()", "La pantalla y el menú"),
        ("widget", "_Burbuja", "Una burbuja del chat"),
    ])
    D.say("La pantalla del chat es la principal. Su método más importante es enviar: el corazón de toda la app.", esperar=True)
    c = {n: P.cuerpo(f) for n, f in [("init", "void initState()"), ("cargar", "Future<void> _cargarHilos()"),
                                      ("abrir", "Future<void> _abrirHilo("), ("enviar", "Future<void> _enviar("),
                                      ("micro", "Future<void> _microfono()"), ("avisar", "void _avisar("),
                                      ("bajar", "void _bajar()"), ("ir", "Future<void> _ir("),
                                      ("build", "Widget build(BuildContext context)"), ("menu", "Widget _menuHilos()")]}
    c["burbuja"] = P.cuerpo("Widget build(BuildContext context)", P.buscar("class _Burbuja"))
    limpiar = P.bloque("// Quita asteriscos", "texto.replaceAll(RegExp")
    limpiar = (limpiar[0], limpiar[1] + 1)
    D.esqueleto(P, list(c.values()) + [limpiar], modo="pegar")
    D.hold()
    D.ficha_explicar(1, "Su estado guarda el controlador del campo de texto, la lista de mensajes en pantalla, los hilos, el hilo actual y el estado del núcleo.", "final _campo = TextEditingController();")
    D.ficha_explicar(4, "Y aquí está enviar, todavía vacío. Lo escribiremos paso a paso.", "Future<void> _enviar(")
    paso(D, P, 2, c["init"], "initState carga los hilos y le da a la voz el aviso para cuando se apague el micrófono.", modo="pegar")
    paso(D, P, 3, c["cargar"], "_cargarHilos lee las conversaciones de la memoria...", modo="pegar")
    paso(D, P, 3, c["abrir"], "...y _abrirHilo muestra los mensajes de una conversación.", modo="pegar")
    i1 = P.buscar("    // 2. RAG:", c["enviar"][0]) - 4
    i2 = P.buscar("    // 4. Guardamos la respuesta", c["enviar"][0])
    i3 = P.buscar("    // 5. Y la decimos en voz alta", c["enviar"][0])
    paso(D, P, 4, (c["enviar"][0], P.buscar("    _bajar();", c["enviar"][0])), "Ahora sí, enviar. Paso uno, la memoria.", cps=24,
         despues=[("// 1. Memoria:", "await Memoria.guardar(hilo, pregunta);", "1 · Memoria",
                   "Crea el hilo si es nuevo\nLee los últimos 6 mensajes\nGuarda tu pregunta",
                   "Si la conversación es nueva, creamos el hilo. Leemos los últimos seis mensajes y guardamos tu pregunta. Luego, setState la muestra en pantalla y pone el núcleo en pensando.")])
    paso(D, P, 4, (P.buscar("    _bajar();", c["enviar"][0]) + 1, i2 - 2), "Pasos dos y tres: buscar y responder.", cps=24,
         despues=[("// 2. RAG:", "fuentes = {", "2 · RAG", None,
                   "Buscamos en Qdrant los fragmentos más parecidos a la pregunta, y anotamos de qué documentos salieron."),
                  ("// 3. El LLM responde", "respuesta.write(token);", "3 · El LLM",
                   "armarPrompt: documentos + historial + pregunta\nawait for: recibe cada token y actualiza la burbuja",
                   "Armamos el prompt, y con await for recibimos cada token y actualizamos la burbuja. Por eso la respuesta aparece poco a poco.")])
    paso(D, P, 4, (i2 - 1, c["enviar"][1]), "Y los pasos cuatro y cinco: guardar y hablar.", cps=24,
         despues=[("// 4. Guardamos la respuesta", "await Memoria.guardar(hilo, respuestaFinal);", "4 · Guardar", None,
                   "Guardamos la respuesta en la memoria..."),
                  ("// 5. Y la decimos en voz alta", "await Voz.hablar(respuestaFinal.texto);", "5 · Hablar", None,
                   "...y YARBYS la lee en voz alta, con el núcleo en el estado hablando.")])
    paso(D, P, 5, c["micro"], "_microfono hace lo mismo, pero con tu voz: cuando terminas de hablar, envía el texto reconocido.", modo="pegar")
    D.say("Estas son funciones de ayuda: limpiar el markdown, mostrar avisos, bajar la lista y cambiar de pantalla. Las pego.")
    D.ficha_ver(6)
    D.completar(P, limpiar, modo="pegar")
    for k in ("avisar", "bajar", "ir"):
        D.completar(P, c[k], modo="pegar")
    D.ficha_hecho(6)
    D.hold()
    paso(D, P, 7, c["build"], "Y build, la pantalla. La pego y vemos sus bloques.", modo="pegar",
         despues=[("appBar: AppBar(", "drawer: _menuHilos(),", "La barra de arriba", None,
                   "Arriba, una AppBar con el nombre, la píldora y los botones de documentos y ajustes. Y drawer es el menú lateral de conversaciones."),
                  ("AnimatedContainer(", "child: FittedBox(child: Nucleo(", "El núcleo", None,
                   "Luego el núcleo, que se achica con una animación cuando ya hay mensajes."),
                  ("? ListView.builder(", "itemBuilder: (_, i) => _Burbuja(_mensajes[i]),", "Los mensajes", None,
                   "La lista de mensajes, una burbuja por mensaje..."),
                  ("child: TextField(", "onSubmitted: _enviar,", "El campo", None,
                   "...y abajo el campo de texto, que al enviar llama a nuestra función enviar.")])
    paso(D, P, 7, c["menu"], "_menuHilos es el menú de conversaciones; lo pego.", modo="pegar")
    paso(D, P, 8, c["burbuja"], "Y _Burbuja dibuja cada mensaje: azul a la derecha si es tuyo, gris a la izquierda si es de YARBYS, con sus fuentes debajo.", modo="pegar")
    D.guardar()
    D.verificar(P.ruta)
    D.ficha_ocultar()

    P = Plan("lib/pantallas/documentos.dart")
    D.abrir_desde_explorador(P.ruta)
    D.ficha("pantallas/documentos.dart", "Tus documentos: agregar archivos o notas, y borrarlos.", [
        ("widget", "PantallaDocumentos", "StatefulWidget"),
        ("estado", "_PantallaDocumentosState", "La lista y el documento que se está aprendiendo"),
        ("método", "_cargar() · _aprender()", "Leer la lista y aprender un documento"),
        ("método", "_elegirArchivos()", "Elegir archivos .txt o .md"),
        ("método", "_escribirNota()", "Escribir una nota rápida"),
        ("método", "_olvidar() · build()", "Borrar y la pantalla"),
    ])
    D.say("La pantalla de documentos es parecida, así que la armamos más rápido.", esperar=True)
    c = [P.cuerpo("void initState()"), P.cuerpo("Future<void> _cargar()"), P.cuerpo("Future<void> _aprender("),
         P.cuerpo("Future<void> _elegirArchivos()"), P.cuerpo("Future<void> _escribirNota()"),
         P.cuerpo("Future<void> _olvidar("), P.cuerpo("void _avisar("), P.cuerpo("Widget build(BuildContext context)")]
    D.esqueleto(P, c, modo="pegar")
    D.hold()
    D.ficha_ver(2)
    D.completar(P, c[0], modo="pegar")
    D.completar(P, c[1], modo="pegar")
    paso(D, P, 2, c[2], "_aprender le pasa el texto a Conocimiento y muestra un aviso con cuántos fragmentos guardó.", modo="pegar")
    paso(D, P, 3, c[3], "_elegirArchivos usa file_picker.", modo="pegar",
         despues=[("final archivos = await FilePicker.pickFiles(", "await _aprender(archivo.name, texto);", "Agregar archivos",
                   "pickFiles: abre el selector de archivos\nutf8.decode: convierte los bytes en texto",
                   "pickFiles abre el selector de archivos del celular, solo para .txt y .md. Leemos cada archivo, lo convertimos en texto y se lo damos a _aprender.")])
    paso(D, P, 4, c[4], "_escribirNota abre un diálogo para escribir o pegar una nota.", modo="pegar")
    paso(D, P, 5, c[5], "Y el resto: borrar, avisar y la pantalla.", modo="pegar")
    D.completar(P, c[6], modo="pegar")
    D.completar(P, c[7], modo="pegar")
    D.ficha_hecho(5)
    D.guardar()
    D.verificar(P.ruta)
    D.ficha_ocultar()

    P = Plan("lib/pantallas/ajustes.dart")
    D.abrir_desde_explorador(P.ruta)
    D.ficha("pantallas/ajustes.dart", "Elegir el cerebro, la voz y borrar la memoria.", [
        ("widget", "PantallaAjustes", "StatefulWidget"),
        ("método", "initState() · _guardar() · dispose()", "Leer y guardar al salir"),
        ("método", "_cambiarModo()", "Local o LLM externo (Pro)"),
        ("método", "_cambiarProveedor()", "OpenAI o Anthropic"),
        ("método", "build()", "La pantalla"),
    ])
    D.say("Y la última pantalla, ajustes.", esperar=True)
    c = [P.cuerpo("void initState()"), P.cuerpo("Future<void> _leerClave()"), P.cuerpo("Future<void> _guardar()"),
         P.cuerpo("void dispose()"), P.cuerpo("void _cambiarModo("), P.cuerpo("Future<void> _cambiarProveedor("),
         P.cuerpo("Widget build(BuildContext context)"), P.cuerpo("Widget build(BuildContext context)", P.buscar("class _Titulo"))]
    D.esqueleto(P, c, modo="pegar")
    D.hold()
    D.ficha_ver(1)
    for r in c[:4]:
        D.completar(P, r, modo="pegar")
    D.ficha_hecho(1)
    paso(D, P, 2, c[4], "_cambiarModo activa el LLM externo.", modo="pegar",
         despues=[("if (nube && !Ajustes.esPro) {", "return;", "Solo con Pro", None,
                   "Si alguien que no es Pro intenta activarlo, le mostramos la versión Pro.")])
    paso(D, P, 3, c[5], "_cambiarProveedor cambia entre OpenAI y Anthropic.", modo="pegar")
    paso(D, P, 4, c[6], "Y build arma la pantalla.", modo="pegar",
         despues=[("SegmentedButton<bool>(", "onSelectionChanged: (s) => _cambiarModo(s.first),", "Elegir el cerebro", None,
                   "Con SegmentedButton se elige el cerebro: en el celular o externo."),
                  ("'Con un LLM externo, tu pregunta", "'siguen guardados en el celular.',", "Transparencia", None,
                   "Y le explicamos al usuario qué datos salen del celular cuando usa un LLM externo. Es importante ser transparentes.")])
    D.completar(P, c[7], modo="pegar")
    D.guardar()
    D.verificar(P.ruta)
    fin_archivo(D, "Las cuatro pantallas están listas.")

    # ---------------------------------------------------------- MAIN
    D.capitulo("Paso 12 · main.dart")
    P = Plan("lib/main.dart")
    D.say("Por último, main.dart: el punto de partida. Lo abrimos: trae el ejemplo del contador de Flutter. Lo borramos todo.")
    D.abrir_desde_explorador(P.ruta)
    D.wait(1.0)
    D.borrar_todo()
    D.hold()
    D.ficha("main.dart", "El punto de partida: prepara el motor de IA, la memoria y abre la app.", [
        ("función", "main()", "Lo primero que se ejecuta"),
        ("widget", "YarbysApp", "La app: tema y primera pantalla"),
        ("método", "build()", ""),
    ])
    c_main = P.cuerpo("Future<void> main() async")
    c_build = P.cuerpo("Widget build(BuildContext context)")
    D.esqueleto(P, [c_main, c_build], cps=22)
    D.hold()
    D.ficha_explicar(0, "main es lo primero que se ejecuta al abrir la app.", "Future<void> main() async")
    D.ficha_explicar(1, "Y YarbysApp es el widget raíz de toda la app.", "class YarbysApp extends StatelessWidget")
    paso(D, P, 0, c_main, "Implementamos main.", cps=22,
         despues=[("await FlutterEdgeAi.initialize(", "embeddingBackends:", "Encender el motor de IA",
                   "LiteRtLmEngine: ejecuta Gemma 4\nLiteRtEmbeddingBackend: ejecuta EmbeddingGemma",
                   "Encendemos el motor de inteligencia artificial: LiteRtLmEngine para Gemma, y LiteRtEmbeddingBackend para EmbeddingGemma."),
                  ("await Memoria.abrir();", "runApp(const YarbysApp());", None, None,
                   "Abrimos la memoria, cargamos los ajustes, y runApp arranca la app.")])
    paso(D, P, 2, c_build, "Y build devuelve la app.", cps=22,
         despues=[("return MaterialApp(", "home: const PantallaInicio(),", "La app", None,
                   "MaterialApp con nuestro tema oscuro, y la pantalla de inicio como primera pantalla.")])
    D.guardar()
    D.verificar(P.ruta)
    fin_archivo(D, "Y main.dart está listo.")
    D.set(abiertas=frozenset({"lib", "lib/pantallas", "lib/servicios", "lib/widgets"}))
    D.say("Así queda el proyecto completo: los servicios con la inteligencia artificial, el núcleo y las pantallas.", esperar=True)

    # ---------------------------------------------------------- PASO 13: EJECUTAR
    D.capitulo("Paso 13 · Probar en el celular")
    D.set(term_abierto=False, term_lineas=())
    D.abrir_terminal()
    D.say("Conectamos el celular por USB y revisamos que Flutter lo vea con flutter devices.")
    D.comando("flutter devices")
    D.salida("Found 3 connected devices:", BLANCO, 0.6)
    for linea in ["  Pixel 8 (mobile)  • 38021FDH2004ZT • android-arm64  • Android 16 (API 36)",
                  "  Windows (desktop) • windows        • windows-x64    • Microsoft Windows",
                  "  Chrome (web)      • chrome         • web-javascript • Google Chrome"]:
        D.salida(linea, BLANCO, 0.25)
    D.fin_comando()
    D.hold()
    D.say("Ahí está mi Pixel 8. Ejecutamos la app con flutter run --release. En modo release, Gemma corre mucho más rápido.")
    D.comando("flutter run --release")
    D.salida("Launching lib\\main.dart on Pixel 8 in release mode...", BLANCO, 1.0)
    D.salida("qdrant_edge: downloading qdrant-edge-ffi-android_arm64.tar.gz …", GRIS, 0.8)
    D.salida("flutter_edge_ai: Downloading litertlm native libs ...", GRIS, 0.6)
    D.salida("flutter_edge_ai: Checksum verified (litertlm-android_arm64.tar.gz)", GRIS, 0.6)
    D.say("La primera compilación tarda unos minutos, porque descarga las librerías nativas de LiteRT-LM y de Qdrant Edge.")
    D.salida("Running Gradle task 'assembleRelease'...", BLANCO, 2.5)
    D.salida_segs([("√ ", G), ("Built build\\app\\outputs\\flutter-apk\\app-release.apk (84.8MB)", BLANCO)], 0.6)
    D.salida("Installing build\\app\\outputs\\flutter-apk\\app-release.apk...", BLANCO, 1.2)
    D.salida("", BLANCO, 0.1)
    D.salida("Flutter run key commands.", BLANCO, 0.1)
    D.salida("h List all available interactive commands.", BLANCO, 0.05)
    D.salida("c Clear the screen", BLANCO, 0.05)
    D.salida("q Quit (terminate the application on the device).", BLANCO, 0.05)
    D.set(term_actual=())
    D.hold()
    D.demo_app("prueba", ("smartphone", "Probando en el celular", "YARBYS <span class='acento'>en tu celular</span>"), [
        ("decir", "Y se abre en el celular. La primera vez, YARBYS nos pide descargar los modelos. Usa Wi-Fi: son unos 2.8 gigas."),
        ("toque", 234, 752),
        ("ev", "descargando", True), ("ev", "progreso", "emb", 0, 100, 2.0),
        ("nota", "download", "Descarga única: unos 2.8 GB", CELESTE),
        ("esperar", 2.0), ("ev", "progreso", "gemma", 0, 100, 6.0),
        ("decir", "Aquí aceleré el video. Según tu internet, la descarga puede tardar varios minutos, pero se hace una sola vez."),
        ("esperar", 6.2), ("ev", "pantalla", "splash"), ("ev", "descargando", False), ("ev", "estado", "pensando"),
        ("esperar", 1.5), ("ev", "estado", "reposo"), ("ev", "pantalla", "chat"),
        ("decir", "Ya tenemos el chat. Primero le enseñamos nuestros documentos: toco el ícono de documentos, y Agregar archivo."),
        ("toque", 392, 85), ("ev", "pantalla", "documentos"), ("esperar", 0.8),
        ("toque", 350, 909), ("ev", "picker", True), ("esperar", 0.8),
        ("toque", 60, 611), ("ev", "picker_sel", [0]), ("toque", 60, 665), ("ev", "picker_sel", [0, 1]), ("esperar", 0.3),
        ("toque", 234, 798), ("ev", "picker", False),
        ("ev", "aprendiendo", "agenda.txt"), ("esperar", 1.2), ("ev", "aprendiendo", None), ("ev", "docs", [["agenda.txt", 1]]),
        ("ev", "aprendiendo", "perfil.txt"), ("esperar", 1.0), ("ev", "aprendiendo", None),
        ("ev", "docs", [["perfil.txt", 1], ["agenda.txt", 1]]), ("ev", "snack", 'Aprendí "perfil.txt" en 1 fragmentos'),
        ("nota", "binary", "Fragmentos → vectores → Qdrant Edge", CELESTE),
        ("decir", "YARBYS lee cada archivo, lo corta en fragmentos, crea los embeddings y los guarda en Qdrant. Todo dentro del celular."),
        ("toque", 28, 85), ("ev", "pantalla", "chat", -1),
        ("decir", "Ahora activo el modo avión, para comprobar que todo funciona sin internet."),
        ("toque", 234, 12), ("ev", "sombra", True), ("esperar", 0.8), ("toque", 122, 210), ("ev", "avion", True),
        ("esperar", 0.8), ("ev", "sombra", False), ("nota", "plane", "Modo avión activado", VERDE),
        ("decir", "Y le pregunto."),
        ("preguntar", "¿Qué música me gusta?", R_MUSICA, ["perfil.txt"]),
        ("preguntar", "¿Y qué tengo el sábado?", R_SABADO, ["agenda.txt"], True),
        ("nota", *F_GEMMA),
        ("decir", "Perfecto. Ahora, la prueba de la memoria: cierro la app y la vuelvo a abrir."),
        ("esperar", 1.0), ("ev", "pantalla", "splash"), ("ev", "limpiar_chat"), ("ev", "estado", "pensando"), ("esperar", 1.5),
        ("ev", "estado", "reposo"), ("ev", "pantalla", "chat"),
        ("decir", "Abro el menú, entro a la conversación de antes, y le pregunto de qué hablamos."),
        ("toque", 28, 85), ("ev", "hilos", ["¿Qué música me gusta?"], -1), ("ev", "drawer", True), ("esperar", 0.9),
        ("toque", 160, 202), ("ev", "drawer", False), ("ev", "hilos", ["¿Qué música me gusta?"], 0),
        ("ev", "cargar_chat", [["u", "¿Qué música me gusta?"], ["y", R_MUSICA, ["perfil.txt"]], ["u", "¿Y qué tengo el sábado?"], ["y", R_SABADO, ["agenda.txt"]]]),
        ("esperar", 0.8),
        ("preguntar", "¿De qué hablamos antes?", R_ANTES, []),
        ("nota", "history", "Recuerda gracias a SQLite", CELESTE),
        ("decir", "¡Lo recuerda todo! Porque cada mensaje quedó guardado en SQLite, en el mismo hilo."),
        ("decir", "Y si quieres, en Ajustes puedes activar un LLM externo con tu propia API key. Es opcional: por defecto, YARBYS es cien por ciento local."),
        ("toque", 436, 85), ("ev", "pantalla", "ajustes"), ("esperar", 1.0), ("toque", 342, 182), ("ev", "nube", True),
        ("esperar", 0.6), ("toque", 234, 382), ("ev", "clave", 8), ("esperar", 0.3), ("ev", "clave", 20), ("esperar", 0.3), ("ev", "clave", 28),
        ("nota", "cloud", "LLM externo opcional · versión Pro", AMARILLO),
    ], inicial=[("pantalla", "inicio"), ("avion", False)])

    # ---------------------------------------------------------- APK
    D.capitulo("Generar el APK")
    D.atajo("q", 0.8)
    D.salida("Application finished.", BLANCO, 0.4)
    D.fin_comando()
    D.say("Para compartir la app sin cable, generamos el APK con flutter build apk. Con --target-platform android-arm64 compilamos solo para los celulares modernos.")
    D.comando("flutter build apk --release --target-platform android-arm64", cps=16)
    D.salida("Running Gradle task 'assembleRelease'...", BLANCO, 2.0)
    D.salida_segs([("√ ", G), ("Built build\\app\\outputs\\flutter-apk\\app-release.apk (84.8MB)", BLANCO)], 0.5)
    D.fin_comando()
    D.hold()
    D.say("Y en el repositorio de GitHub dejé un workflow de GitHub Actions que compila el APK automáticamente. Así puedes descargarlo y probarlo sin instalar nada.", esperar=True)

    # ---------------------------------------------------------- NEGOCIO Y CIERRE
    D.capitulo("Bonus · Ganar dinero")
    D.slide(SlideHTML("negocio"), frases=[
        "Bonus: ¿cómo podrías ganar dinero con una app como YARBYS?",
        "Una idea: la versión gratuita es cien por ciento local, sin límites. Eso atrae a muchos usuarios, porque sus datos nunca salen del celular.",
        "Luego, una versión Pro de pago único, con funciones extra como el LLM externo. Como cada usuario pone su propia API key, tú no pagas los tokens.",
        "Y para empresas: clínicas, estudios de abogados o colegios valoran mucho la privacidad. Puedes ofrecerles una versión a medida.",
        "Y más adelante, si quieres, una suscripción con tu propio servidor. Pero empieza simple.",
    ])
    D.capitulo("Resumen")
    D.slide(SlideHTML("resumen"), frases=[
        "¡Y listo! Hagamos un resumen de lo que construimos.",
        "Un asistente que usa Gemma 4 como cerebro dentro del celular, EmbeddingGemma y Qdrant Edge para buscar en tus documentos, SQLite para recordar las conversaciones, y los motores de voz del teléfono.",
        "Además, un LLM externo opcional para la versión Pro, y el APK listo con GitHub Actions. Como reto, agrégale tus propios documentos y pregúntale lo que quieras.",
    ])
    D.slide(SlideHTML("final"), frases=[
        "El código completo está en GitHub; te dejo el enlace en la descripción.",
        "Si te gustó, dale like, suscríbete, y cuéntame en los comentarios qué le agregarías a tu YARBYS. ¡Nos vemos en el próximo video!",
    ])
    D.cerrar_log()
    return D


# ============================================================== SALIDA
def fmt_srt(s):
    ms = int(round(s * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    sec, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{sec:02},{ms:03}"


def fmt_min(s):
    return f"{int(s // 60)}:{int(s % 60):02}"


def escribir_textos(D):
    srt = [f"{i}\n{fmt_srt(a)} --> {fmt_srt(b)}\n{t}\n" for i, (a, b, t, _) in enumerate(D.log, 1)]
    (AQUI / "subtitulos.srt").write_text("\n".join(srt), encoding="utf-8")
    g = ["# Guion de narración", "",
         "Lee cada frase en voz alta en el momento indicado. Los tiempos coinciden con `tutorial.mp4`.",
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
    (AQUI / "guion.md").write_text("\n".join(g), encoding="utf-8")


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
          "oido": "oído", "menu": "menú"}


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


def main():
    global FRAMES
    archivos = {}
    if NARRACION:
        # 1ª pasada: obtener las frases; 2ª pasada: usar la duración real de cada audio
        D0 = guion()
        pares = ([(VOZ, e[2]) for e in D0.log] + [(VOZ_YARBYS, t) for _, t in D0.log_yarbys]
                 + [(VOZ, t) for _, t in D0.log_usuario])
        archivos = preparar_voz(pares)
    D = guion()
    for demo in D.demos_app:
        demo.guardar()
    FRAMES = D.frames
    total = len(FRAMES) / FPS
    escribir_textos(D)
    print(f"Duración: {fmt_min(total)} ({len(FRAMES)} fotogramas)")
    if "--preview" in sys.argv:
        out = AQUI / "preview"
        out.mkdir(exist_ok=True)
        paso = int(sys.argv[sys.argv.index("--preview") + 1]) if len(sys.argv) > 2 else 20
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
                    "-i", str(wav), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", "-ac", "2",
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", str(AQUI / "tutorial.mp4")], check=True)
    for t in trabajos:
        t[3].unlink()
    lista.unlink()
    tmp.rmdir()
    print("Video:", AQUI / "tutorial.mp4")


if __name__ == "__main__":
    main()
