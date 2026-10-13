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
TECLADO = True           # sonido suave de teclado y clics del mouse
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
        if nota:
            self.set(nota=(titulo, nota))
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
    lineas = wrap(texto, F_NOTE, ancho - 70)
    alto = 30 + (40 if titulo else 0) + len(lineas) * 36 + 14
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

    def __init__(self, id_):
        self.id = id_
        self.dur, self.marcas = 10.0, [0.0]

    def configurar(self, dur, marcas):
        self.dur, self.marcas = dur, marcas

    def url(self):
        m = ",".join(f"{x:.3f}" for x in self.marcas)
        return f"file://{ESCENAS_HTML}?id={self.id}&dur={self.dur:.3f}&m={m}"


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


# ============================================================== RENDER DE UN FOTOGRAMA
def render(s, blink):
    if s.slide:
        obj, t, dur = s.slide
        img = chromium().captura(obj, t)
        d = ImageDraw.Draw(img)
    else:
        img = Image.new("RGB", (W, H), C_BG)
        d = ImageDraw.Draw(img)
        dibujar_vscode(img, d, s, blink)
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


def guion():
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
    D.say("Agregamos los paquetes de inteligencia artificial con flutter pub add.")
    ia = ["flutter_edge_ai", "flutter_edge_ai_litertlm", "flutter_edge_ai_rag", "flutter_edge_ai_qdrant"]
    D.comando("flutter pub add " + " ".join(ia))
    D.salida("Resolving dependencies...", BLANCO, 1.2)
    D.salida("Downloading packages...", BLANCO, 1.0)
    for p, v in [("flutter_edge_ai", "2.3.2"), ("flutter_edge_ai_litertlm", "1.13.2"), ("flutter_edge_ai_qdrant", "2.1.0"),
                 ("flutter_edge_ai_rag", "1.1.0"), ("qdrant_edge", "0.8.0-dev.5")]:
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

    # ---------------------------------------------------------- PASO 4: MODELOS
    D.capitulo("Paso 4 · Los modelos")
    D.say("Ahora sí, a programar. En lib creamos la carpeta servicios, y dentro, el archivo modelos.dart. Aquí descargamos los dos modelos de inteligencia artificial.")
    D.nuevo_archivo("lib/servicios/modelos.dart")
    b = piezas("lib/servicios/modelos.dart", ["  /// ¿Ya están", "  static Future<void> descargarEmbeddings", "  static Future<void> descargarGemma"])
    D.escribir(b[0], cps=22)
    D.resaltar("static const urlGemma", "embeddinggemma-2-text-270m.litertlm';", titulo="Los modelos están en Hugging Face",
               nota="Gemma 4 E2B: el cerebro · 2.6 GB\nEmbeddingGemma 2: los embeddings · 165 MB\nNo necesitan cuenta ni token",
               frases=["Guardamos las direcciones de los dos modelos. Están en Hugging Face, la plataforma donde se publican los modelos abiertos, y no necesitan cuenta ni token."])
    D.escribir(b[1])
    D.resaltar("static bool get listos", None, titulo="¿Ya están descargados?",
               frases=["listos nos dice si los dos modelos ya están en el celular, para no descargarlos otra vez."])
    D.escribir(b[2] + b[3], cps=19)
    D.guardar()
    D.resaltar("await FlutterEdgeAi.installEmbedder()", ".install();", titulo="Descargar e instalar",
               nota="installEmbedder(): el modelo de embeddings\nwithModelProgress: avisa el porcentaje",
               frases=["installEmbedder descarga EmbeddingGemma, y withModelProgress nos va avisando el porcentaje, para mostrar una barra de progreso."])
    D.resaltar("await FlutterEdgeAi.installModel(", ").fromNetwork(urlGemma)", titulo="Gemma 4",
               nota="modelType: gemma4 → cómo habla el modelo\nfileType: litertlm → el motor LiteRT-LM",
               frases=["Con installModel descargamos Gemma. modelType le dice a la librería que es Gemma 4, y fileType, que es un archivo .litertlm, el formato del motor LiteRT-LM."])

    # ---------------------------------------------------------- PASO 5: MEMORIA
    D.capitulo("Paso 5 · Memoria con SQLite")
    D.say("Ahora la memoria. Creamos servicios, memoria.dart.")
    D.nuevo_archivo("lib/servicios/memoria.dart")
    b = piezas("lib/servicios/memoria.dart", ["class Hilo {", "/// La memoria de YARBYS", "        // Los documentos que YARBYS aprendió", "  static int get _ahora"])
    D.escribir(b[0])
    D.resaltar("class Mensaje {", "bool get esUsuario", titulo="Un mensaje",
               nota="rol: 'usuario' o 'yarbys'\ntexto: lo que se dijo\nfuentes: documentos que usó",
               frases=["Una clase en Dart es como un molde. Mensaje tiene un rol, que dice quién habló, el texto, y las fuentes: los documentos que YARBYS usó para responder."])
    D.say("Las clases Hilo y Documento son parecidas; las pego para avanzar más rápido.")
    D.pegar(b[1])
    D.hold()
    D.escribir(b[2], cps=21)
    D.resaltar("final ruta = p.join", "_db = await openDatabase(", titulo="El archivo de la base de datos",
               nota="getDatabasesPath(): la carpeta de bases de datos de la app\nyarbys.db: un solo archivo",
               frases=["openDatabase abre el archivo yarbys.db, dentro de la carpeta de la app. Si no existe, lo crea."])
    D.resaltar("onCreate: (db, version) async {", "fuentes TEXT NOT NULL DEFAULT", titulo="Las tablas (SQL)",
               nota="onCreate solo corre la primera vez\nhilos: cada conversación\nmensajes: cada mensaje, con el id de su hilo",
               frases=["onCreate se ejecuta solo la primera vez. Con SQL creamos dos tablas: hilos, con cada conversación, y mensajes, donde cada mensaje guarda el id del hilo al que pertenece."])
    D.pegar(b[3])
    D.hold()
    D.say("Y pego también la tabla de documentos y las funciones para leer y guardar; son consultas sencillas.")
    D.pegar(b[4])
    D.guardar()
    D.verificar("lib/servicios/memoria.dart")
    D.resaltar("static Future<void> guardar(int hilo", "});", titulo="Guardar un mensaje",
               nota="insert: agrega una fila a la tabla mensajes",
               frases=["guardar inserta una fila nueva en la tabla mensajes."])
    D.resaltar("static Future<List<Mensaje>> mensajes(", "limit: ultimos,", titulo="Los últimos mensajes",
               nota="orderBy id DESC + limit: los más recientes\nLuego los volteamos (reversed) para leerlos en orden",
               frases=["Y mensajes trae los mensajes de un hilo. Con limit pedimos solo los últimos, y luego los volteamos para tenerlos en orden. Así le daremos memoria a YARBYS."])

    # ---------------------------------------------------------- PASO 6: CONOCIMIENTO
    D.capitulo("Paso 6 · RAG con Qdrant Edge")
    D.say("Sigue el conocimiento: tus documentos en Qdrant. Creamos servicios, conocimiento.dart.")
    D.nuevo_archivo("lib/servicios/conocimiento.dart")
    b = piezas("lib/servicios/conocimiento.dart", ["  /// Corta un texto largo", "  /// Aprende un documento", "  static Future<void> olvidar",
                                                   "  /// Búsqueda semántica", "  /// El nombre del documento"])
    D.escribir(b[0], cps=21)
    D.resaltar("final rag = FlutterEdgeAiRag(", "providers: const [QdrantVectorStoreProvider()]", titulo="Qdrant Edge",
               nota="FlutterEdgeAiRag: el sistema de RAG\nQdrantVectorStoreProvider: guarda los vectores con Qdrant Edge",
               frases=["FlutterEdgeAiRag es el sistema de RAG, y le decimos que guarde los vectores con Qdrant Edge."])
    D.resaltar("_indice = await rag.open(", "embedder: FlutterEdgeAiActiveEmbedder", titulo="Abrir el índice",
               nota="location: una carpeta dentro de la app\nembedder: EmbeddingGemma crea los vectores",
               frases=["Abrimos el índice en una carpeta de la app, y le indicamos que EmbeddingGemma será quien convierta los textos en vectores."])
    D.say("Ahora la función que corta los documentos en fragmentos. La pego y la explico.")
    D.pegar(b[1])
    D.resaltar("for (final parrafo in texto.split", "fragmentos.add(actual);", titulo="Fragmentar",
               nota="Separa por párrafos (líneas en blanco)\nVa juntando párrafos hasta unos 800 caracteres",
               frases=["Separamos el texto por párrafos, y los vamos juntando hasta llegar a unos 800 caracteres. Cuando no cabe uno más, guardamos el fragmento y empezamos otro."])
    D.escribir(b[2], cps=20)
    D.resaltar("final partes = fragmentar(texto);", "metadata: jsonEncode", titulo="Aprender un documento",
               nota="1. Fragmenta el texto\n2. Guarda el documento en SQLite\n3. add(): crea el vector y lo guarda en Qdrant",
               frases=["aprender fragmenta el texto y anota el documento en SQLite. Luego, por cada fragmento, add crea su vector con EmbeddingGemma y lo guarda en Qdrant, junto con el nombre del documento."])
    D.resaltar("await _indice.flush();", None, frases=["Y flush guarda los cambios en el disco."])
    D.pegar(b[3])
    D.hold()
    D.escribir(b[4], cps=20)
    D.resaltar("return _indice.search(", "threshold: 0.3,", titulo="Búsqueda semántica",
               nota="topK: 3 → los 3 fragmentos más parecidos\nthreshold: descarta los poco parecidos",
               frases=["Y la búsqueda: search convierte la pregunta en vector y nos devuelve los tres fragmentos más parecidos. threshold descarta los que se parecen muy poco."])
    D.pegar(b[5])
    D.guardar()
    D.verificar("lib/servicios/conocimiento.dart")
    D.hold()

    # ---------------------------------------------------------- PASO 7: CEREBRO
    D.capitulo("Paso 7 · El cerebro")
    D.say("Llegamos al cerebro. Creamos servicios, cerebro.dart.")
    D.nuevo_archivo("lib/servicios/cerebro.dart")
    b = piezas("lib/servicios/cerebro.dart", ["  /// Arma el prompt", "  /// Devuelve la respuesta", "  // --- 2. LLM externo"])
    D.escribir(b[0], cps=21)
    D.resaltar("static const sistema = '''", "Si no sabes algo", titulo="La personalidad",
               nota="Las instrucciones de sistema: quién es y cómo responde\nMáximo 3 oraciones y sin markdown: se leen en voz alta",
               frases=["Primero, la personalidad de YARBYS. Son las instrucciones de sistema: le decimos quién es, que responda en español, en máximo tres oraciones y sin formato, porque se leen en voz alta."])
    D.escribir(b[1], cps=21)
    D.resaltar("final b = StringBuffer();", "b.write('Pregunta del usuario: $pregunta');", titulo="Armar el prompt",
               nota="1. Los fragmentos de tus documentos\n2. La conversación hasta ahora\n3. Tu pregunta",
               frases=["armarPrompt construye el mensaje que verá Gemma: primero los fragmentos de tus documentos, luego la conversación reciente y al final tu pregunta. Exactamente lo que vimos en la parte de RAG."])
    D.escribir(b[2], cps=20)
    D.guardar()
    D.resaltar("static Stream<String> responder", "return Ajustes.usarNube", titulo="¿Local o externo?",
               nota="Stream: la respuesta llega en pedacitos\nPor defecto: Gemma 4 en el celular",
               frases=["responder devuelve un Stream: un flujo de datos que llega en pedacitos, token por token. Si el usuario no activó la nube, usamos Gemma en el celular."])
    D.resaltar("final modelo = await FlutterEdgeAi.getActiveModel", "maxOutputTokens: 512,", titulo="Gemma 4",
               nota="maxTokens: 4096 → el contexto (lo que puede leer)\nmaxOutputTokens: 512 → largo máximo de la respuesta",
               frases=["getActiveModel carga Gemma en la memoria. maxTokens es cuánto texto puede leer a la vez, el contexto. Y createChat crea la conversación con la personalidad y un máximo de 512 tokens de respuesta."])
    D.resaltar("await chat.addQueryChunk", "if (respuesta is TextResponse) yield", titulo="Token por token",
               nota="isUser: true → lo escribió el usuario\nyield: entrega cada token apenas llega",
               frases=["Le enviamos el prompt, y con yield vamos entregando cada token apenas Gemma lo genera. Al final, cerramos el chat."])
    D.say("La parte del LLM externo es opcional. La pego y te explico lo importante.")
    D.pegar(b[3])
    D.guardar()
    D.verificar("lib/servicios/cerebro.dart")
    D.resaltar("final clave = await Ajustes.leerClave();", "throw Exception", titulo="Tu propia API key",
               nota="El usuario pega su API key en Ajustes\nNunca va escrita en el código",
               frases=["La API key la escribe cada usuario en la app; nunca va escrita en el código."])
    D.resaltar("Uri.parse('https://api.anthropic.com/v1/messages')", "'max_tokens': 512,", titulo="Anthropic o OpenAI",
               nota="Claude Haiku con la API de Anthropic\nGPT-6 Luna con la API de OpenAI\nMismo prompt, mismo sistema",
               frases=["Con el paquete http enviamos el mismo prompt a Anthropic, para Claude Haiku, o a OpenAI, para GPT-6 Luna. El resto de la app no cambia nada."])

    # ---------------------------------------------------------- PASO 8: VOZ Y AJUSTES
    D.capitulo("Paso 8 · Voz y ajustes")
    D.say("Ahora la voz. Creamos servicios, voz.dart, y pego el código.")
    D.nuevo_archivo("lib/servicios/voz.dart")
    D.pegar(leer("lib/servicios/voz.dart"))
    D.guardar()
    D.resaltar("static final _oido = SpeechToText();", "static final _boca = FlutterTts();", titulo="Oídos y boca",
               nota="SpeechToText: tu voz → texto\nFlutterTts: texto → voz",
               frases=["Tenemos dos piezas: el oído, SpeechToText, que convierte tu voz en texto, y la boca, FlutterTts, que lee en voz alta."])
    D.resaltar("await _oido.listen(", "pauseFor: const Duration(seconds: 3),", titulo="Escuchar",
               nota="partialResults: muestra el texto mientras hablas\npauseFor: 3 segundos de silencio y termina",
               frases=["listen escucha en español, nos va mostrando el texto mientras hablas, y termina cuando te quedas en silencio tres segundos."])
    D.resaltar("static Future<void> hablar(String texto)", "await _boca.speak(texto);", titulo="Hablar",
               frases=["Y hablar lee la respuesta en voz alta, y espera a que termine."])
    D.say("Y servicios, ajustes.dart: aquí se guardan las preferencias.")
    D.nuevo_archivo("lib/servicios/ajustes.dart")
    D.pegar(leer("lib/servicios/ajustes.dart"))
    D.guardar()
    D.resaltar("static const _cofre = FlutterSecureStorage();", None, titulo="Guardado cifrado",
               nota="Keystore en Android, Keychain en iPhone",
               frases=["Usamos FlutterSecureStorage, que guarda los datos cifrados: en Android con Keystore y en iPhone con Keychain. Ideal para la API key."])
    D.resaltar("static bool usarNube = false;", "static bool hablar = true;", titulo="Por defecto: 100% local",
               frases=["usarNube empieza en false: por defecto, YARBYS es cien por ciento local."])
    D.resaltar("// Versión Pro:", "static bool esPro = true;", titulo="La versión Pro",
               nota="Aquí conectarías una compra única\n(paquete in_app_purchase)",
               frases=["Y esPro es el interruptor de la versión Pro. Aquí conectarías una compra dentro de la app; en este proyecto viene desbloqueada."])

    # ---------------------------------------------------------- PASO 9: INTERFAZ
    D.capitulo("Paso 9 · El núcleo de YARBYS")
    D.say("Pasemos a la interfaz. Primero tema.dart, con los colores de la app: fondos oscuros y planos. Lo pego.")
    D.nuevo_archivo("lib/tema.dart")
    D.pegar(leer("lib/tema.dart"))
    D.guardar()
    D.resaltar("class Colores {", "static const suave", titulo="La paleta",
               frases=["Todos los colores están en un solo lugar, para cambiarlos fácilmente."])
    D.say("Y ahora, lo más vistoso: el núcleo circular, inspirado en el JARVIS de las películas. Creamos widgets, nucleo.dart.")
    D.nuevo_archivo("lib/widgets/nucleo.dart")
    D.pegar(leer("lib/widgets/nucleo.dart"))
    D.guardar()
    D.resaltar("enum EstadoYarbys", None, titulo="Cuatro estados",
               frases=["YARBYS tiene cuatro estados: en reposo, escuchando, pensando y hablando."])
    D.resaltar("double _velocidad(EstadoYarbys estado)", "EstadoYarbys.hablando => 1.4,", titulo="Gira según el estado",
               nota="Un Ticker avisa 60 veces por segundo\nPensando: gira 4 veces más rápido",
               frases=["Un Ticker nos avisa sesenta veces por segundo, y en cada cuadro los anillos giran un poco. Al pensar, giran cuatro veces más rápido."])
    D.resaltar("class _PintorNucleo extends CustomPainter", None, titulo="CustomPainter",
               nota="Dibujamos con código: círculos, arcos y líneas\ncomo en un lienzo",
               frases=["Y el dibujo lo hacemos con un CustomPainter: un lienzo donde dibujamos con código, con círculos, arcos y líneas."])
    D.resaltar("// 4. Ecualizador circular", "(0.5 + 0.5 * sin(t * 3.7 + i * 0.31));", titulo="El ecualizador",
               frases=["Por ejemplo, estas barras forman un ecualizador circular que baila cuando YARBYS escucha o habla."])

    D.capitulo("Paso 10 · Las pantallas")
    D.say("Ahora las pantallas. En lib creamos la carpeta pantallas. Empezamos por inicio.dart, la pantalla que descarga los modelos.")
    D.nuevo_archivo("lib/pantallas/inicio.dart")
    D.pegar(leer("lib/pantallas/inicio.dart"))
    D.guardar()
    D.resaltar("if (Modelos.listos) _entrar();", None, titulo="Solo la primera vez",
               frases=["Si los modelos ya están descargados, vamos directo al chat."])
    D.resaltar("await Modelos.descargarEmbeddings(", "await _entrar();", titulo="Descargar con progreso",
               nota="setState: actualiza la pantalla con el nuevo %",
               frases=["Si no, el botón descarga los dos modelos. Cada vez que llega un porcentaje nuevo, setState redibuja la pantalla con la barra de progreso."])
    D.say("La pantalla principal es chat.dart. La pego, y vamos a ver su corazón paso a paso.")
    D.nuevo_archivo("lib/pantallas/chat.dart")
    D.pegar(leer("lib/pantallas/chat.dart"))
    D.guardar()
    D.resaltar("// 1. Memoria:", "await Memoria.guardar(hilo, pregunta);", titulo="1 · Memoria",
               nota="Crea el hilo si es nuevo\nLee los últimos 6 mensajes\nGuarda tu pregunta",
               frases=["La función enviar hace todo el trabajo. Paso uno, la memoria: si la conversación es nueva, creamos el hilo. Leemos los últimos seis mensajes y guardamos tu pregunta."])
    D.resaltar("// 2. RAG:", "fuentes = {", titulo="2 · RAG",
               frases=["Paso dos, RAG: buscamos en Qdrant los fragmentos más parecidos a la pregunta, y anotamos de qué documentos salieron."])
    D.resaltar("// 3. El LLM responde", "respuesta.write(token);", titulo="3 · El LLM",
               nota="armarPrompt: documentos + historial + pregunta\nawait for: recibe cada token y actualiza la burbuja",
               frases=["Paso tres: armamos el prompt, y con await for recibimos cada token y actualizamos la burbuja en la pantalla. Por eso la respuesta aparece poco a poco."])
    D.resaltar("// 4. Guardamos la respuesta", "await Memoria.guardar(hilo, respuestaFinal);", titulo="4 · Guardar",
               frases=["Paso cuatro: guardamos la respuesta en la memoria."])
    D.resaltar("// 5. Y la decimos en voz alta", "await Voz.hablar(respuestaFinal.texto);", titulo="5 · Hablar",
               frases=["Y paso cinco: YARBYS la lee en voz alta, y el núcleo cambia al estado hablando."])
    D.resaltar("Future<void> _microfono() async {", "_enviar(texto);", titulo="El micrófono",
               frases=["Con el micrófono es igual: cuando terminas de hablar, el texto reconocido se envía con la misma función."])
    D.say("Siguen documentos.dart, para agregar tus archivos, y ajustes.dart. Los pego.")
    D.nuevo_archivo("lib/pantallas/documentos.dart")
    D.pegar(leer("lib/pantallas/documentos.dart"))
    D.guardar()
    D.resaltar("final archivos = await FilePicker.pickFiles(", "await _aprender(archivo.name, texto);", titulo="Agregar archivos",
               nota="Elige archivos .txt o .md\nlos lee y los manda a Conocimiento.aprender",
               frases=["Aquí elegimos archivos de texto del celular, los leemos y se los damos a Conocimiento para que los aprenda. También puedes escribir una nota rápida."])
    D.nuevo_archivo("lib/pantallas/ajustes.dart")
    D.pegar(leer("lib/pantallas/ajustes.dart"))
    D.guardar()
    D.resaltar("if (nube && !Ajustes.esPro) {", "return;", titulo="Solo con Pro",
               frases=["Y en ajustes, si alguien que no es Pro intenta activar el LLM externo, le mostramos la versión Pro."])
    D.resaltar("'Con un LLM externo, tu pregunta", "'siguen guardados en el celular.',", titulo="Transparencia",
               frases=["Además le explicamos al usuario qué datos salen del celular cuando usa un LLM externo. Es importante ser transparentes."])

    D.capitulo("Paso 11 · main.dart")
    D.say("Por último, main.dart: el punto de entrada de la app. Lo abrimos: trae el ejemplo del contador de Flutter. Lo borramos todo.")
    D.abrir_desde_explorador("lib/main.dart")
    D.wait(1.0)
    D.borrar_todo()
    D.hold()
    b = piezas("lib/main.dart", ["Future<void> main() async {", "class YarbysApp"])
    D.escribir(b[0] + b[1], cps=20)
    D.resaltar("await FlutterEdgeAi.initialize(", "embeddingBackends:", titulo="Encender el motor de IA",
               nota="LiteRtLmEngine: ejecuta Gemma 4\nLiteRtEmbeddingBackend: ejecuta EmbeddingGemma",
               frases=["Al arrancar, encendemos el motor de inteligencia artificial: LiteRtLmEngine para Gemma, y LiteRtEmbeddingBackend para EmbeddingGemma."])
    D.resaltar("await Memoria.abrir();", "await Ajustes.cargar();", frases=["Abrimos la memoria y cargamos los ajustes."])
    D.escribir(b[2], cps=21)
    D.guardar()
    D.verificar("lib/main.dart")
    D.resaltar("return MaterialApp(", "home: const PantallaInicio(),", titulo="La app",
               frases=["Y la app: MaterialApp con nuestro tema oscuro, y la pantalla de inicio como primera pantalla."])
    D.set(abiertas=frozenset({"lib", "lib/pantallas", "lib/servicios", "lib/widgets"}))
    D.say("Y listo. Así queda el proyecto: los servicios con la inteligencia artificial, el núcleo y las pantallas.", esperar=True)

    # ---------------------------------------------------------- PASO 12: EJECUTAR
    D.capitulo("Paso 12 · Probar en el celular")
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
], key=lambda par: -len(par[0]))


def texto_hablado(texto):
    """Convierte el texto del guion en el texto que pronuncia la voz."""
    t = texto
    for original, dicho in PRONUNCIACION:
        patron = re.escape(original)
        if original[0].isalnum() or original[0] == "_":
            patron = r"(?<![\w.])" + patron
        if original[-1].isalnum() or original[-1] == "_":
            patron += r"(?![\w])"
        flags = 0 if original in ("IA", "API", "RAG", "LLM", "LLMs", "SQL", "PATH", "APK", "USB", "add") else re.IGNORECASE
        t = re.sub(patron, dicho, t, flags=flags)
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
