"""
Video tutorial: "Crea tu propio Asistente de IA" — simulación de VS Code.

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
El código se lee de ../codigo, así que el video siempre coincide con el proyecto.
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
from pygments.lexers import PythonLexer, YamlLexer, IniLexer, TextLexer, HtmlLexer, CssLexer, JavascriptLexer
from pygments.token import Token

AQUI = Path(__file__).parent
CODIGO = AQUI.parent / "codigo"
W, H, FPS = 1920, 1080, 30

# ============================================================== MARCA DEL CANAL
# Cambia estos valores para adaptar el video al estilo de tu canal.
CANAL = "Paul Antezana"
LOGO = AQUI / "marca" / "logo.png"   # logo que aparece siempre en una esquina
MARCA = (19, 93, 188)        # azul del logo
MARCA2 = (252, 179, 51)      # naranja del logo
ESCENAS_HTML = AQUI / "escenas" / "escena.html"

# ============================================================== VOZ
VOZ = "em_alex"          # narrador. Voces en español de Kokoro: em_alex, ef_dora, em_santa
VOZ_JARVIS = "em_santa"  # la voz con la que JARVIS lee sus respuestas
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
        self.carpetas = set()      # carpetas extra (p.ej. .venv)
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
        self.log_jarvis = []   # (segundo, texto) que JARVIS dice en voz alta
        self.demos = {}        # segmento -> lista de eventos de la página web (tiempo virtual)

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

    def _insertar(self, ch):
        self.sonidos.append((self.t, "tecla"))
        txt = self.texto()
        pos = len(txt)  # siempre escribimos al final del archivo
        nuevo = txt[:pos] + ch + txt[pos:]
        lineas = nuevo.split("\n")
        self._poner_texto(nuevo, (len(lineas) - 1, len(lineas[-1])))

    def _borrar(self):
        txt = self.texto()[:-1]
        lineas = txt.split("\n")
        self._poner_texto(txt, (len(lineas) - 1, len(lineas[-1])))

    def escribir(self, texto, cps=17, errores=True, autocompletar=True):
        """Teclea como una persona: velocidad variable, sangría automática,
        algún error corregido y autocompletado en palabras largas."""
        r = self.rnd
        i = 0
        palabras_vistas = set(re.findall(r"[A-Za-z_]\w{6,}", self.texto()))
        while i < len(texto):
            ch = texto[i]
            linea_actual = self.texto().split("\n")[-1]
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
        nuevo = self.texto() + texto
        lineas = nuevo.split("\n")
        self.sonidos.append((self.t, "tecla"))
        self._poner_texto(nuevo, (len(lineas) - 1, len(lineas[-1])))
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
        self.set(files=f, input_explorer=None, tabs=self.s.tabs + (ruta,), activo=ruta,
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
        lineas = self.texto().split("\n")
        self.set(cursor=(len(lineas) - 1, len(lineas[-1])))
        self._ajustar_scroll()
        self.mover(ED_X + 700, editor_bottom(self.s) - 140, 0.5)

    # ---------- terminal
    venv_activo = False
    cwd = "C:\\proyectos\\jarvis"

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
        self.estado_terminales[idx] = ((), None, False, "C:\\proyectos\\jarvis")
        self.set(term_tabs=self.s.term_tabs + (nombre,))
        self._cargar_terminal(idx)
        self.wait(0.5)

    def _guardar_terminal(self):
        self.estado_terminales[self.s.term_activa] = (self.s.term_lineas, self.s.term_actual,
                                                      self.venv_activo, self.cwd)

    def _cargar_terminal(self, idx):
        lineas, actual, venv, cwd = self.estado_terminales.get(idx, ((), None, False, "C:\\proyectos\\jarvis"))
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

    # ---------- navegador (Microsoft Edge en Windows)
    def abrir_navegador(self, url=""):
        self.set(navegador=(url, ("cargando", 0.0)), ocultar_mouse=False, foco="pagina")
        self.wait(0.4)

    def escribir_url(self, url):
        self.mover(700, 62, 0.4)
        self.clic()
        self.set(navegador=("", self.s.navegador[1]), foco="url")
        for c in url:
            self.sonidos.append((self.t, "tecla"))
            self.set(navegador=(self.s.navegador[0] + c, self.s.navegador[1]))
            self.emit(max(1, round(FPS / 14 * self.rnd.uniform(0.6, 1.4))))
        self.wait(0.3)
        self.atajo("Enter", 0.8)
        self.set(foco="pagina")

    def cargando(self, seg):
        n = round(seg * FPS)
        for i in range(n):
            self.set(navegador=(self.s.navegador[0], ("cargando", i / FPS)))
            self.emit()

    def cerrar_navegador(self):
        self.set(navegador=None)
        self.wait(0.3)

    def demo_web(self, seg, pasos, recargar_al_inicio=False):
        """Usa la página de JARVIS en el navegador, en 'tiempo virtual'.
        pasos: lista de ("preguntar", texto, respuesta) | ("decir", frase) | ("recargar",) | ("esperar", s)
        Los fotogramas de la página se generan después con Chromium (ver grabar_demos)."""
        eventos = self.demos.setdefault(seg, [])
        t0 = self.t
        vt = lambda: self.t - t0
        n0 = len(self.frames)

        def avanzar(segundos):
            for _ in range(round(segundos * FPS)):
                k = len(self.frames) - n0
                self.set(navegador=(self.s.navegador[0], ("demo", seg, k)))
                self.emit()

        def avanzar_hasta_hold():
            while self.t < self.say_hasta:
                avanzar(1 / FPS)

        if recargar_al_inicio:
            eventos.append((vt(), "recargar"))
        avanzar(0.6)
        for p in pasos:
            if p[0] == "decir":
                avanzar_hasta_hold()
                self.say(p[1])
                avanzar_hasta_hold()
            elif p[0] == "esperar":
                avanzar(p[1])
            elif p[0] == "recargar":
                self.atajo("F5", 0.8)
                eventos.append((vt(), "recargar"))
                avanzar(1.0)
            elif p[0] == "preguntar":
                _, pregunta, respuesta = p
                eventos.append((vt(), "foco"))
                avanzar(0.3)
                for i in range(1, len(pregunta) + 1):
                    self.sonidos.append((self.t, "tecla"))
                    eventos.append((vt(), "texto", pregunta[:i]))
                    avanzar(1 / FPS * max(1, round(FPS / 13 * self.rnd.uniform(0.6, 1.4))))
                avanzar(0.3)
                self.atajo("Enter", 0.8)
                self.sonidos.append((self.t, "tecla"))
                eventos.append((vt(), "enviar"))
                avanzar(1.6)                                   # JARVIS "pensando"
                eventos.append((vt(), "responder", respuesta))
                avanzar(0.25)
                self.log_jarvis.append((self.t, respuesta))   # JARVIS habla
                eventos.append((vt(), "hablando"))
                avanzar(duracion_frase(respuesta, VOZ_JARVIS))
                eventos.append((vt(), "fin_voz"))
                avanzar(0.6)
        avanzar_hasta_hold()
        avanzar(0.5)

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


SUGERENCIAS = {"ChatOpenAI", "ChatPromptTemplate", "ChatMessageHistory", "OllamaEmbeddings",
               "OllamaLLM", "QdrantVectorStore", "QdrantClient", "PostgresChatMessageHistory",
               "RunnablePassthrough", "RunnableLambda", "RunnableWithMessageHistory",
               "RecursiveCharacterTextSplitter", "CharacterTextSplitter", "StrOutputParser",
               "MessagesPlaceholder", "from_documents", "from_existing_collection",
               "from_messages", "from_template", "as_retriever", "split_documents",
               "split_text", "load_dotenv", "page_content", "collection_name", "create_tables",
               "sync_connection", "search_kwargs", "search_type", "temperature",
               "input_messages_key", "history_messages_key", "output_messages_key",
               "obtener_historial", "buscar_contexto", "documentos", "fragmentos"}


# ============================================================== DIBUJO VS CODE
def icono_archivo(d, x, y, nombre):
    ext = nombre.rsplit(".", 1)[-1] if "." in nombre else nombre
    if nombre.endswith(".py"):
        d.rounded_rectangle((x, y + 3, x + 16, y + 19), 3, fill=(55, 118, 171))
        d.rounded_rectangle((x + 6, y + 9, x + 18, y + 21), 3, fill=(255, 211, 67))
    elif ext in ("yml", "yaml"):
        d.text((x + 1, y), "!", font=F_UI_B, fill=(203, 56, 55))
        d.text((x + 8, y), "!", font=F_UI_B, fill=(203, 56, 55))
    elif nombre.startswith(".env"):
        d.ellipse((x + 2, y + 4, x + 16, y + 18), outline=(226, 192, 141), width=3)
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
    """Lista de (nivel, nombre, ruta, es_carpeta, abierta)."""
    rutas = list(s.files)
    carpetas = set(s.carpetas)
    for r in rutas:
        if "/" in r:
            carpetas.add(r.split("/")[0])
    items = []
    for c in sorted(carpetas, key=str.lower):
        abierta = c != ".venv"
        items.append((0, c, c, True, abierta))
        if abierta:
            for r in sorted((r for r in rutas if r.startswith(c + "/")), key=str.lower):
                items.append((1, r.split("/", 1)[1], r, False, False))
    for r in sorted((r for r in rutas if "/" not in r), key=str.lower):
        items.append((0, r, r, False, False))
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
    d.text((W / 2, TITLE_H / 2), "asistente", font=F_UI_S, fill=C_MUTED, anchor="mm")
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
    d.text((ACT_W + 28, ry), "ASISTENTE", font=fnt(INTER + "Inter-Bold.otf", 16), fill=C_TEXT)
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
        bc = "asistente  ›  " + "  ›  ".join(partes)
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
            for g in range(0, sangria, 4):
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
        lang = {"py": "Python", "yml": "YAML", "txt": "Plain Text", "html": "HTML", "css": "CSS",
                "js": "JavaScript"}.get(s.activo.rsplit(".", 1)[-1], "Properties")
        partes = [f"Ln {cl + 1}, Col {cc + 1}", "Spaces: 4", "UTF-8", "CRLF", lang]
        if s.activo.endswith(".py"):
            partes.append("3.12.3 ('.venv': venv)")
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


# ============================================================== NAVEGADOR (Edge)
NAV_TOP = 84                      # alto de la barra de pestañas + barra de direcciones
CACHE_WEB = AQUI / "_cache_web"   # fotogramas de la página de JARVIS (ver grabar_demos)


def dibujar_navegador(img, d, s, blink):
    url, contenido = s.navegador
    d.rectangle((0, 0, W, NAV_TOP), fill=(32, 32, 32))
    # pestaña
    titulo = "JARVIS" if "127.0.0.1" in url or not url else url.split("/")[0]
    d.rounded_rectangle((8, 6, 300, 44), 10, fill=(56, 56, 56))
    d.rectangle((8, 30, 300, 44), fill=(56, 56, 56))
    d.ellipse((22, 16, 40, 34), fill=(79, 209, 255) if titulo == "JARVIS" else (140, 150, 170))
    d.text((52, 15), titulo, font=F_UI, fill=(235, 235, 235))
    d.text((272, 13), "×", font=F_SYM, fill=(200, 200, 200))
    d.text((318, 10), "+", font=F_UI_B, fill=(200, 200, 200))
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
    # barra de direcciones
    d.rectangle((0, 44, W, NAV_TOP), fill=(56, 56, 56))
    for i, x in enumerate([22, 62, 102]):
        if i == 0:
            d.line((x + 12, 64, x, 64), fill=(220, 220, 220), width=2); d.line((x, 64, x + 6, 58), fill=(220, 220, 220), width=2); d.line((x, 64, x + 6, 70), fill=(220, 220, 220), width=2)
        elif i == 1:
            d.line((x, 64, x + 12, 64), fill=(120, 120, 120), width=2); d.line((x + 12, 64, x + 6, 58), fill=(120, 120, 120), width=2); d.line((x + 12, 64, x + 6, 70), fill=(120, 120, 120), width=2)
        else:
            d.arc((x, 57, x + 14, 71), 40, 330, fill=(220, 220, 220), width=2)
    d.rounded_rectangle((150, 50, W - 150, 78), 14, fill=(36, 36, 36))
    d.ellipse((166, 57, 180, 71), outline=(170, 170, 170), width=2)
    d.text((194, 54), url, font=F_UI, fill=(235, 235, 235))
    if s.foco == "url" and blink:
        cx = 194 + F_UI.getlength(url) + 2
        d.line((cx, 55, cx, 74), fill=(235, 235, 235))
    d.ellipse((W - 112, 52, W - 88, 76), fill=(19, 93, 188))
    d.text((W - 60, 52), "···", font=F_UI_B, fill=(220, 220, 220))
    # contenido
    if contenido[0] == "demo":
        _, seg, k = contenido
        ruta = CACHE_WEB / seg / f"{k:05d}.jpg"
        if ruta.exists():
            foto = Image.open(ruta)
            if foto.size != (W, H - NAV_TOP):
                foto = foto.resize((W, H - NAV_TOP), Image.LANCZOS)
            img.paste(foto, (0, NAV_TOP))
        else:
            d.rectangle((0, NAV_TOP, W, H), fill=(5, 9, 19))
    else:
        t = contenido[1]
        d.rectangle((0, NAV_TOP, W, H), fill=(246, 247, 249))
        d.rectangle((0, NAV_TOP, int(W * min(1.0, 0.15 + t * 0.5)), NAV_TOP + 3), fill=(0, 120, 212))
        cx, cy, r = W / 2, (NAV_TOP + H) / 2, 34
        a0 = (t * 360 * 1.4) % 360
        d.arc((cx - r, cy - r, cx + r, cy + r), a0, a0 + 270, fill=(0, 120, 212), width=6)


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


# Respuestas de JARVIS en las demos (ilustrativas, basadas en docs/perfil.txt y docs/agenda.txt)
R_MIERCOLES = "El miércoles tienes que entregar el proyecto de la tienda online antes de las 6 de la tarde. ¡Tú puedes, Alex!"
R_PERRO = "Se llama Rocky. Y recuerda que el sábado a las 10 de la mañana lo llevas al veterinario."
R_MUSICA = "Te gusta el rock de los 80. Ideal para programar con un café americano sin azúcar."
R_SABADO = "El sábado a las 10 de la mañana llevas a Rocky al veterinario."
R_ANTES = "Hablamos de tu música favorita, el rock de los 80, y de la cita de Rocky con el veterinario el sábado."


def guion():
    D = Director()
    D.set(mouse=(1500, 700))

    # ---------------------------------------------------------- INTRO
    D.capitulo("Introducción")
    D.slide(SlideHTML("intro"), frases=[
        "Hola, ¿qué tal? Bienvenidos. Hoy vamos a crear nuestro propio JARVIS: un asistente personal con inteligencia artificial.",
        "Conoce tu información, recuerda lo que conversan y te responde con voz, desde una página web.",
        "Y lo haremos en Windows, sin Docker, paso a paso y explicando cada línea de código.",
    ])

    # ---------------------------------------------------------- DEMO
    D.capitulo("Resultado final")
    D.set(mouse=(1500, 640))
    D.abrir_navegador("127.0.0.1:8000")
    D.demo_web("inicio", [
        ("decir", "Antes de empezar, mira el resultado final. Le pregunto a JARVIS qué tengo el miércoles."),
        ("preguntar", "¿Qué tengo el miércoles?", R_MIERCOLES),
        ("decir", "Sabe lo que tengo en mi agenda porque lee mis documentos, y me responde con voz."),
        ("preguntar", "¿Y cómo se llama mi perro?", R_PERRO),
        ("decir", "Y recuerda la conversación: en la segunda pregunta no tuve que explicarle nada más."),
    ])
    D.cerrar_navegador()

    # ---------------------------------------------------------- CONCEPTOS
    D.capitulo("Las 5 piezas")
    D.slide(SlideHTML("piezas"), frases=[
        "Para construir a JARVIS necesitamos cinco piezas, y te voy a explicar cada una con calma.",
        "Un cerebro, que es el modelo de lenguaje, y un traductor de textos a números, que son los embeddings.",
        "Una base de datos vectorial para buscar información, y una memoria para recordar las conversaciones.",
        "Y una página web para hablar con él. LangChain será el pegamento que une todas las piezas.",
    ])
    D.capitulo("¿Qué es un LLM?")
    D.slide(SlideHTML("llm"), frases=[
        "Empecemos por el cerebro: el LLM, o modelo de lenguaje. Es una inteligencia artificial que entiende y escribe texto.",
        "Funciona así: le envías un mensaje, lo divide en pequeños pedazos llamados tokens, y genera la respuesta token por token.",
        "ChatGPT, Claude, Gemini o DeepSeek usan LLMs. Pero hay decenas de modelos, cada uno con distinta inteligencia y precio.",
    ])
    D.capitulo("Comparativa de LLMs")
    D.set(mouse=(1300, 500))
    D.abrir_navegador("")
    D.say("¿Y cómo elegimos uno? Yo uso Artificial Analysis, una página independiente que compara los modelos de IA por inteligencia, velocidad y precio.")
    D.escribir_url("artificialanalysis.ai")
    D.cargando(max(1.5, D.say_hasta - D.t))
    D.cerrar_navegador()
    D.slide(SlideHTML("comparativa"), frases=[
        "En este gráfico, más arriba significa más inteligente, y más a la derecha, más caro. El precio es en dólares por millón de tokens de salida.",
        "Arriba están los más potentes, como Claude Opus 5.5, Claude Sonnet 5.5 o Gemini 4 Argon. Son muy inteligentes, pero cuestan entre 10 y 20 dólares por millón de tokens.",
        "Y aquí abajo, a la izquierda, está GPT-6 Luna, al que llamamos GptLuna: tiene 38 puntos y cuesta solo 50 centavos. ¡Unas 40 veces más barato que Opus!",
        "En la misma zona está Claude Haiku 5.5, con el mismo precio y algo más de inteligencia. También sería una gran opción.",
        "Para un asistente personal que responde preguntas del día a día no necesitamos el modelo más caro. GptLuna nos da una excelente relación entre precio e inteligencia.",
    ])
    D.capitulo("Embeddings")
    D.slide(SlideHTML("embeddings"), frases=[
        "Ahora, ¿cómo encuentra JARVIS la información correcta dentro de tus documentos? Con embeddings.",
        "Un embedding convierte un texto en una lista de números, llamada vector. bge-m3, por ejemplo, genera 1024 números por cada texto.",
        "Lo genial es que los textos con significado parecido quedan cerca. '¿Qué tengo el miércoles?' queda junto a 'Miércoles: entregar el proyecto', aunque usen palabras distintas.",
        "Hay varios modelos de embeddings. OpenAI tiene text-embedding-3-small, que cuesta 2 centavos por millón de tokens, y uno más grande y preciso. También está nomic-embed-text, que corre en tu PC.",
        "Nosotros usaremos bge-m3 con Ollama: es gratis, funciona sin internet en tu computadora y entiende más de 100 idiomas, incluido el español.",
    ])
    D.capitulo("Qdrant")
    D.slide(SlideHTML("qdrant"), frases=[
        "Esos vectores los guardamos en Qdrant, una base de datos vectorial. Es como una biblioteca que ordena los textos por su significado.",
        "Cuando haces una pregunta, Qdrant la compara con todos los fragmentos guardados y te devuelve los más parecidos, con un puntaje.",
        "Y lo mejor: Qdrant tiene una versión para Windows. Solo descargas un archivo y lo ejecutas.",
    ])
    D.capitulo("RAG")
    D.slide(SlideHTML("rag"), frases=[
        "Juntando estas piezas tenemos la técnica más usada para crear asistentes con IA: RAG.",
        "Primero llega tu pregunta. Luego buscamos en Qdrant la información relevante.",
        "Después la añadimos al mensaje, junto con tu pregunta. Y finalmente el LLM genera la respuesta.",
        "Así JARVIS responde con TUS datos reales, y no se inventa cosas.",
    ])
    D.capitulo("Memoria")
    D.slide(SlideHTML("memoria"), frases=[
        "La última pieza es la memoria. Un LLM, por sí solo, no recuerda nada: cada mensaje es como hablar con alguien que te acaba de conocer.",
        "Si le pregunto '¿y cómo se llama mi perro?' después de hablar de mi agenda, necesita saber de qué estábamos hablando.",
        "Por eso guardamos cada conversación, a la que llamamos 'hilo', en PostgreSQL. Y en cada pregunta le enviamos los últimos mensajes.",
        "PostgreSQL también tiene instalador oficial para Windows, así que tampoco necesitamos Docker.",
    ])
    D.capitulo("Arquitectura")
    D.slide(SlideHTML("arquitectura"), frases=[
        "Este es el plan completo. Tú hablas con JARVIS desde una página web, en tu navegador.",
        "La página le envía tu mensaje a nuestro servidor en Python, hecho con FastAPI, que se lo pasa a asistente.py.",
        "Ahí buscamos el contexto en Qdrant, con la ayuda de Ollama, y leemos el historial en PostgreSQL.",
        "Luego le preguntamos a GptLuna, guardamos la respuesta en la memoria, y la página la lee en voz alta.",
    ])
    D.capitulo("Instalación en Windows")
    D.slide(SlideHTML("instalacion"), frases=[
        "Pasemos a la instalación. Todo funciona directamente en Windows, sin Docker y sin WSL.",
        "Primero, Python, desde python.org. Muy importante: en el instalador marca la casilla 'Add python.exe to PATH'.",
        "Segundo, Ollama, desde ollama.com. Se instala como cualquier programa y queda funcionando en segundo plano.",
        "Tercero, Qdrant. En su página de GitHub, en la sección Releases, descarga el archivo .zip para Windows y descomprímelo, por ejemplo, en C:\\qdrant.",
        "Cuarto, PostgreSQL, con el instalador para Windows de su página oficial. Te pedirá una contraseña para el usuario postgres: anótala, la usaremos después.",
        "Y por último, tu API key de OpenAI, desde platform.openai.com, para poder usar GptLuna.",
    ])

    # ---------------------------------------------------------- PASO 1: SERVICIOS
    D.s = Estado()
    D.venv_activo = False
    D.set(mouse=(1200, 640))
    D.capitulo("Paso 1 · Servicios")
    D.say("Con todo instalado, abrimos Visual Studio Code. Creé una carpeta llamada jarvis en C:\\proyectos, y la abrí con File, Open Folder.", esperar=True)
    D.say("Abrimos la terminal con Control + comilla invertida. En Windows, VS Code usa PowerShell.")
    D.abrir_terminal()
    D.hold()
    D.say("Primero descargamos el modelo de embeddings con Ollama: ollama pull bge-m3.")
    D.comando("ollama pull bge-m3")
    D.salida("pulling manifest", BLANCO, 0.6)
    D.salida("", BLANCO, 0)
    for pct in range(0, 101, 4):
        llenos = pct * 30 // 100
        barra = "█" * llenos + " " * (30 - llenos)
        gb = 1.2 * pct / 100
        D.set(term_lineas=D.s.term_lineas[:-1] + (((f"pulling model... {pct:3d}% ▕{barra}▏ {gb:.1f} GB/1.2 GB", BLANCO),),))
        D.wait(0.13)
    for linea in ["verifying sha256 digest", "writing manifest", "success"]:
        D.salida(linea, BLANCO, 0.3)
    D.fin_comando()
    D.hold()
    D.say("Ahora encendemos Qdrant. Abro una segunda terminal con Control + Shift + comilla invertida, y ejecuto el programa que descomprimimos en C:\\qdrant.")
    D.nueva_terminal("qdrant")
    D.comando("C:\\qdrant\\qdrant.exe")
    banner = ["           _                 _    ",
              "  __ _  __| |_ __ __ _ _ __ | |_  ",
              " / _` |/ _` | '__/ _` | '_ \\| __| ",
              "| (_| | (_| | | | (_| | | | | |_  ",
              " \\__, |\\__,_|_|  \\__,_|_| |_|\\__| ",
              "    |_|                           "]
    for l in banner:
        D.salida(l, (220, 70, 90), 0.05)
    D.salida("", BLANCO, 0.1)
    D.salida("Access web UI at http://localhost:6333/dashboard", BLANCO, 0.4)
    D.salida_segs([("INFO ", G), ("qdrant::actix: Qdrant HTTP listening on 6333", BLANCO)], 0.2)
    D.salida_segs([("INFO ", G), ("qdrant::tonic: Qdrant gRPC listening on 6334", BLANCO)], 0.2)
    D.set(term_actual=())
    D.hold()
    D.say("Qdrant ya está funcionando en el puerto 6333. Deja esta terminal abierta mientras trabajas.", esperar=True)

    # ---------------------------------------------------------- PASO 2: PYTHON
    D.capitulo("Paso 2 · Entorno Python")
    D.say("Volvemos a la primera terminal y creamos un entorno virtual: una carpeta donde se instalan las librerías solo para este proyecto.")
    D.cambiar_terminal(0)
    D.limpiar_terminal()
    D.comando("python -m venv .venv")
    D.wait(1.0)
    D.set(carpetas={".venv"})
    D.fin_comando()
    D.hold()
    D.say("Lo activamos con .venv\\Scripts\\activate.")
    D.comando(".venv\\Scripts\\activate")
    D.venv_activo = True
    D.fin_comando()
    D.hold()
    D.say("Fíjate que ahora aparece '(.venv)' en verde al inicio. Eso significa que el entorno está activo.", esperar=True)
    D.say("Si Windows te muestra un error de permisos al activarlo, ejecuta una sola vez: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned.", esperar=True)

    D.say("Ahora creamos el archivo requirements.txt, con las librerías que vamos a necesitar.")
    D.nuevo_archivo("requirements.txt")
    D.escribir(leer("requirements.txt"))
    D.guardar()
    D.resaltar("langchain", "langchain-text-splitters", titulo="LangChain y sus integraciones",
               nota="langchain: une todas las piezas\nopenai → GptLuna · ollama → embeddings\nqdrant y postgres → bases de datos",
               frases=["langchain es la librería principal. Cada 'langchain-algo' es una integración: openai para GptLuna, ollama para los embeddings, y qdrant y postgres para las bases de datos."])
    D.resaltar("psycopg", "uvicorn", titulo="Otras librerías",
               nota="psycopg: conecta Python con PostgreSQL\npython-dotenv: lee el archivo .env\nfastapi + uvicorn: nuestro servidor web",
               frases=["psycopg conecta Python con PostgreSQL, python-dotenv lee nuestra configuración, y fastapi con uvicorn nos permiten crear el servidor web."])
    D.say("Las instalamos con pip install -r requirements.txt.")
    D.comando("pip install -r requirements.txt")
    paquetes = ["langchain", "langchain-openai", "langchain-ollama", "langchain-qdrant", "langchain-postgres",
                "langchain-text-splitters", "psycopg[binary]", "python-dotenv", "fastapi", "uvicorn"]
    for p in paquetes:
        D.salida(f"Collecting {p}", BLANCO, 0.16)
        D.salida(f"  Downloading {p.split('[')[0].replace('-', '_')}-...-py3-none-any.whl", GRIS, 0.1)
    D.salida("Installing collected packages: ...", BLANCO, 1.0)
    D.salida("Successfully installed fastapi langchain langchain-ollama langchain-openai langchain-postgres "
             "langchain-qdrant langchain-text-splitters psycopg python-dotenv uvicorn ...", BLANCO, 0.2)
    D.fin_comando()
    D.hold()

    # ---------------------------------------------------------- PASO 3: .env
    D.capitulo("Paso 3 · Configuración")
    D.say("Ahora la configuración. Creamos un archivo llamado .env, donde van las claves y direcciones, separadas del código.")
    D.nuevo_archivo(".env")
    b = piezas(".env.example", ["# Ollama", "# Qdrant", "# PostgreSQL"])
    D.escribir(b[0])
    D.resaltar("OPENAI_API_KEY", "LLM_MODEL", titulo="GptLuna (OpenAI)",
               nota="Tu API key de platform.openai.com\nEl modelo: gpt-6-luna",
               frases=["Primero, tu API key de OpenAI y el nombre del modelo: gpt-6-luna. Reemplaza el texto de ejemplo por tu clave real."])
    D.escribir(b[1] + b[2])
    D.resaltar("OLLAMA_URL", "COLLECTION", titulo="Ollama y Qdrant",
               nota="Ollama escucha en el puerto 11434\nQdrant en el 6333 · colección: jarvis",
               frases=["Después las direcciones de Ollama y de Qdrant, con el modelo bge-m3 y el nombre de nuestra colección: jarvis."])
    D.escribir(b[3])
    D.resaltar("PG_URL", None, titulo="PostgreSQL",
               nota="usuario: postgres · contraseña: la que elegiste\nbase de datos: postgres (viene por defecto)",
               frases=["Y la conexión a PostgreSQL. Aquí va la contraseña que elegiste al instalarlo. Usamos la base de datos que viene por defecto, llamada postgres, así no tenemos que crear nada."])
    D.guardar()
    D.say("Un consejo importante: este archivo tiene tu clave secreta. ¡Nunca lo subas a GitHub!", esperar=True)

    # ---------------------------------------------------------- PASO 4: DOCUMENTOS
    D.capitulo("Paso 4 · Tus documentos")
    D.say("Ahora, la información que JARVIS va a conocer. Creamos la carpeta docs con un archivo perfil.txt.")
    D.nuevo_archivo("docs/perfil.txt")
    D.escribir(leer("docs/perfil.txt"), cps=24, autocompletar=False)
    D.guardar()
    D.say("Y otro archivo con mi agenda de la semana. Este lo pego para ir más rápido.")
    D.nuevo_archivo("docs/agenda.txt")
    D.pegar(leer("docs/agenda.txt"))
    D.guardar()
    D.say("Tú puedes poner aquí lo que quieras: tus notas, tus proyectos, tus contactos. Mientras más información, más útil será JARVIS.", esperar=True)

    # ---------------------------------------------------------- PASO 5: INGESTA
    D.capitulo("Paso 5 · ingest.py")
    D.say("Nuestro primer programa es ingest.py. Su trabajo es leer los documentos, convertirlos en vectores y guardarlos en Qdrant.")
    D.nuevo_archivo("ingest.py")
    b = piezas("ingest.py", ["load_dotenv()", "# 1.", "# 2.", "# 3.", "# 4.", "print("])
    D.escribir(b[0])
    D.resaltar("import os", "from langchain_qdrant", titulo="Importaciones",
               nota="os → leer la configuración · Path → buscar archivos\nY las piezas de LangChain que vamos a usar",
               frases=["Empezamos importando lo que vamos a usar: os para leer la configuración, Path para buscar archivos, y las piezas de LangChain."])
    D.escribir(b[1])
    D.say("load_dotenv lee el archivo .env, para poder usar esas variables en el código.", esperar=True)
    D.escribir(b[2])
    D.resaltar("documentos = [", "]", titulo="1. Leer tus documentos",
               nota="Por cada .txt de la carpeta docs creamos un Document:\nel texto + el nombre del archivo",
               frases=["Recorremos todos los archivos .txt de la carpeta docs, y por cada uno creamos un Document de LangChain, con su texto y el nombre del archivo."])
    D.escribir(b[3])
    D.resaltar("splitter =", "fragmentos =", titulo="2. Dividir en fragmentos",
               nota="chunk_size=500 → trozos de 500 caracteres\nchunk_overlap=50 → se repiten 50 entre trozos",
               frases=["Los documentos largos se cortan en fragmentos de 500 caracteres, repitiendo 50 entre uno y otro para no cortar una idea por la mitad."])
    D.escribir(b[4])
    D.resaltar("embeddings =", ")", titulo="3. Embeddings con Ollama",
               nota="os.getenv(\"EMBED_MODEL\") → bge-m3\nos.getenv(\"OLLAMA_URL\") → http://localhost:11434",
               frases=["Creamos el generador de embeddings con Ollama. Con os.getenv leemos el modelo, bge-m3, y la dirección desde el archivo .env."])
    D.escribir(b[5])
    D.resaltar("QdrantVectorStore.from_documents", ")", titulo="4. Guardar en Qdrant",
               nota="from_documents: calcula el vector de cada fragmento\ny lo guarda en la colección \"jarvis\"",
               frases=["Y from_documents hace la magia: le pide a Ollama el vector de cada fragmento y guarda todo en la colección de Qdrant."])
    D.escribir(b[6])
    D.guardar()
    D.say("Lo ejecutamos: python ingest.py.")
    D.limpiar_terminal()
    D.comando("python ingest.py")
    D.wait(1.8)
    D.salida("Listo: 2 fragmentos guardados en Qdrant", BLANCO, 0.4)
    D.fin_comando()
    D.hold()
    D.say("¡Funciona! Se guardaron dos fragmentos, uno por cada archivo. Cada vez que cambies tus documentos, vuelve a ejecutarlo.", esperar=True)

    # ---------------------------------------------------------- PASO 6: ASISTENTE
    D.capitulo("Paso 6 · El cerebro")
    D.say("Ahora el corazón del proyecto: asistente.py. Aquí juntamos el cerebro, la búsqueda y la memoria.")
    D.nuevo_archivo("asistente.py")
    b = piezas("asistente.py", ["load_dotenv()", "# --- 1.", "# --- 2.", "vectorstore =", "retriever =",
                                "# --- 3.", "def obtener_historial", "# --- 4.", "prompt =",
                                "def buscar_contexto", "cadena =", "# --- 5."])
    D.escribir(b[0] + b[1])
    D.resaltar("from langchain_openai", "from langchain_postgres", titulo="Una pieza por servicio",
               nota="ChatOpenAI → GptLuna · OllamaEmbeddings → embeddings\nQdrantVectorStore → búsqueda\nPostgresChatMessageHistory → memoria",
               frases=["Importamos una pieza de LangChain por cada servicio: GptLuna, Ollama, Qdrant y la memoria en PostgreSQL."])
    D.escribir(b[2])
    D.resaltar("llm = ChatOpenAI(", ")", titulo="1. El cerebro: GPT-6 Luna",
               nota="model → gpt-6-luna (desde el .env)\nuse_responses_api → la API más moderna de OpenAI",
               frases=["Primero el cerebro. ChatOpenAI se conecta con OpenAI usando tu API key, y el modelo gpt-6-luna. Activamos la API de respuestas, que es la más moderna de OpenAI."])
    D.escribir(b[3] + b[4] + b[5])
    D.resaltar("embeddings = OllamaEmbeddings(", "retriever =", titulo="2. La búsqueda",
               nota="Usamos la colección que creó ingest.py, con el MISMO modelo.\nk=3 → los 3 fragmentos más parecidos",
               frases=["Luego nos conectamos a la colección que creamos con ingest.py, usando el mismo modelo de embeddings.",
                       "Y el retriever es nuestro buscador: por cada pregunta nos devuelve los 3 fragmentos más parecidos."])
    D.escribir(b[6] + b[7])
    D.resaltar("conn = psycopg.connect", "def obtener_historial", titulo="3. La memoria",
               nota="autocommit=True → cada mensaje se guarda al instante\nobtener_historial(hilo) → los mensajes de ESA conversación",
               frases=["Ahora la memoria. Nos conectamos a PostgreSQL y creamos la tabla chat_history, donde se guardan los mensajes.",
                       "La función obtener_historial devuelve los mensajes de un hilo, así cada conversación tiene su propia memoria."])
    D.escribir(b[8])
    D.resaltar("SISTEMA =", "{context}", titulo="4. La personalidad de JARVIS",
               nota="Respuestas cortas, porque se leen en voz alta.\n{context} → ahí van los textos que encuentre Qdrant",
               frases=["Esta es la personalidad de JARVIS. Le pedimos respuestas cortas, de máximo tres oraciones, porque se van a leer en voz alta.",
                       "Las llaves con context son un espacio vacío: ahí pondremos los textos que encuentre Qdrant."])
    D.escribir(b[9] + b[10])
    D.resaltar("prompt = ChatPromptTemplate", "def buscar_contexto", titulo="El mensaje para GptLuna",
               nota="system → personalidad + contexto\nhistory → los mensajes anteriores\nhuman → tu pregunta",
               frases=["El prompt es el mensaje completo que recibe GptLuna: la personalidad con el contexto, el historial de la conversación y tu pregunta."])
    D.resaltar("def buscar_contexto", "return", titulo="Buscar contexto",
               nota="Busca en Qdrant con tu pregunta\ny une el texto de los fragmentos encontrados",
               frases=["buscar_contexto le pasa tu pregunta al retriever y une el texto de los fragmentos que encuentra."])
    D.escribir(b[11])
    D.resaltar("cadena = (", "StrOutputParser()", titulo="La cadena",
               nota="| significa: \"y luego pásaselo a...\"\ncontexto → prompt → GptLuna → texto",
               frases=["Y esta es la cadena. La barra vertical significa 'y luego pásaselo a': agregamos el contexto, armamos el prompt, se lo enviamos a GptLuna y nos quedamos con el texto."])
    D.escribir(b[12])
    D.resaltar("def preguntar_a_jarvis", "return respuesta", titulo="5. Preguntar a JARVIS",
               nota="1. Lee el historial del hilo (últimos 10 mensajes)\n2. Ejecuta la cadena\n3. Guarda la pregunta y la respuesta",
               frases=["Por último, preguntar_a_jarvis. Lee el historial del hilo, ejecuta la cadena con los últimos 10 mensajes, y guarda tu pregunta y su respuesta en PostgreSQL."])
    D.guardar()
    D.hold()

    # ---------------------------------------------------------- PASO 7: SERVIDOR
    D.capitulo("Paso 7 · El servidor")
    D.say("Ahora el servidor web: app.py. Es muy cortito, gracias a FastAPI.")
    D.nuevo_archivo("app.py")
    b = piezas("app.py", ["app = FastAPI", "class Mensaje", "@app.post", "# La página web"])
    D.escribir(b[0] + b[1] + b[2])
    D.resaltar("class Mensaje", "hilo: str", titulo="Lo que envía la página",
               nota="texto → tu pregunta\nhilo → el id de tu conversación",
               frases=["Mensaje describe lo que nos envía la página: el texto de tu pregunta y el id del hilo."])
    D.escribir(b[3])
    D.resaltar("@app.post", "return", titulo="La ruta /api/chat",
               nota="Recibe el mensaje → pregunta a JARVIS\n→ devuelve la respuesta en JSON",
               frases=["Esta ruta, /api/chat, recibe el mensaje, se lo pregunta a JARVIS y devuelve la respuesta."])
    D.escribir(b[4])
    D.resaltar("app.mount", None, titulo="La página web",
               nota="Sirve los archivos de la carpeta web/\n(index.html, estilo.css y app.js)",
               frases=["Y con app.mount servimos la página web, que va en la carpeta web."])
    D.guardar()
    D.hold()

    # ---------------------------------------------------------- PASO 8: PÁGINA WEB
    D.capitulo("Paso 8 · La página web")
    D.say("Ahora la página. Creamos la carpeta web con el archivo index.html. El HTML lo pego para ir más rápido.")
    D.nuevo_archivo("web/index.html")
    D.pegar(leer("web/index.html"))
    D.guardar()
    D.resaltar('<div id="orbe"', "</div>", titulo="El núcleo de JARVIS",
               nota="Tres anillos y un centro que se animan con CSS",
               frases=["Tiene tres partes. El núcleo animado de JARVIS: tres anillos y un centro brillante."])
    D.resaltar('<div id="chat"', "</div>", titulo="El chat",
               nota="Aquí aparecen los mensajes",
               frases=["El chat, donde aparecen los mensajes."])
    D.resaltar('<form id="form"', "</form>", titulo="La entrada",
               nota="Botón de micrófono · cuadro de texto · botón enviar",
               frases=["Y la entrada: un botón de micrófono para hablarle, el cuadro de texto y el botón de enviar."])
    D.say("Los estilos también los pego: estilo.css.")
    D.nuevo_archivo("web/estilo.css")
    D.pegar(leer("web/estilo.css"))
    D.guardar()
    D.resaltar(".a1 {", ".centro {", titulo="Animación con CSS",
               nota="Cada anillo gira a distinta velocidad\n@keyframes girar → rotate(360deg)",
               frases=["Lo más interesante es la animación: cada anillo gira a una velocidad distinta, y el centro late como un corazón."])
    D.resaltar('.orbe[data-estado="pensando"] .anillo', '.orbe[data-estado="escuchando"]', titulo="Estados de JARVIS",
               nota="pensando → gira rápido y se pone naranja\nhablando → late más rápido",
               frases=["Y cambia según el estado: cuando piensa, gira rápido y se pone naranja; cuando habla, late más rápido."])
    D.say("Y el último archivo, app.js, que le da vida a la página. Este sí lo escribimos y lo explico.")
    D.nuevo_archivo("web/app.js")
    b = piezas("web/app.js", ["const chat", "function cambiarEstado", "function agregarMensaje", "// JARVIS lee",
                              "async function preguntar", "form.addEventListener", "// Hablarle a JARVIS"])
    D.escribir(b[0])
    D.resaltar("const hilo", "localStorage.setItem", titulo="Tu hilo de conversación",
               nota="Se crea un id único y se guarda en el navegador.\nSi recargas la página, JARVIS sigue recordando.",
               frases=["Primero el hilo: creamos un identificador único y lo guardamos en el navegador. Así, aunque recargues la página, JARVIS sigue recordando la conversación."])
    D.escribir(b[1] + b[2] + b[3])
    D.resaltar("function agregarMensaje", "chat.scrollTop", titulo="Mostrar mensajes",
               nota="textContent → muestra el texto de forma segura",
               frases=["cambiarEstado actualiza el núcleo y el texto de estado, y agregarMensaje pone cada mensaje en el chat."])
    D.escribir(b[4])
    D.resaltar("function hablar", "speechSynthesis.speak", titulo="JARVIS habla",
               nota="SpeechSynthesis: la voz del navegador, gratis\nlang = \"es-ES\" → en español",
               frases=["Con SpeechSynthesis, el navegador lee la respuesta en voz alta, en español y gratis."])
    D.escribir(b[5])
    D.resaltar("async function preguntar", "catch", titulo="Preguntar al servidor",
               nota="fetch → envía tu pregunta a /api/chat\ny espera la respuesta de JARVIS",
               frases=["preguntar envía tu mensaje a nuestro servidor con fetch, muestra la respuesta, y la lee en voz alta. Si algo falla, te avisa."])
    D.escribir(b[6] + b[7])
    D.resaltar("const Reconocimiento", "mic.hidden", titulo="Hablarle con tu voz",
               nota="SpeechRecognition convierte tu voz en texto\n(funciona en Chrome y Edge)",
               frases=["Y al final, el reconocimiento de voz: al presionar el micrófono, el navegador escucha, convierte tu voz en texto y se lo pregunta a JARVIS."])
    D.guardar()
    D.hold()

    # ---------------------------------------------------------- PASO 9: PRUEBA
    D.capitulo("Paso 9 · ¡Probamos JARVIS!")
    D.say("¡Llegó el momento! Encendemos el servidor con uvicorn app:app --reload.")
    D.limpiar_terminal()
    D.comando("uvicorn app:app --reload")
    D.wait(0.8)
    for linea in ["INFO:     Will watch for changes in these directories: ['C:\\\\proyectos\\\\jarvis']",
                  "INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)",
                  "INFO:     Started reloader process [10452] using WatchFiles",
                  "INFO:     Started server process [8816]",
                  "INFO:     Waiting for application startup.",
                  "INFO:     Application startup complete."]:
        D.salida_segs([("INFO", G), (linea[4:], BLANCO)], 0.25)
    D.set(term_actual=())
    D.hold()
    D.say("Hacemos Control + clic en la dirección, y se abre JARVIS en el navegador.")
    fila = len(D.s.term_lineas) - 5
    D.mover(ED_X + 420, H - STATUS_H - D.s.term_alto + 48 + fila * TLH + 14, 0.6)
    D.wait(0.3)
    D.atajo("Ctrl + clic", 0.9)
    D.clic()
    D.hold()
    D.abrir_navegador("127.0.0.1:8000")
    D.demo_web("prueba", [
        ("decir", "Probemos con otra pregunta."),
        ("preguntar", "¿Qué música me gusta?", R_MUSICA),
        ("preguntar", "¿Y qué tengo el sábado?", R_SABADO),
        ("decir", "Ahora la prueba de fuego para la memoria: recargo la página..."),
        ("recargar",),
        ("decir", "...y le pregunto de qué hablamos antes."),
        ("preguntar", "¿De qué hablamos antes?", R_ANTES),
        ("decir", "¡Lo recuerda todo! Porque cada mensaje quedó guardado en PostgreSQL, en el mismo hilo."),
    ])
    D.cerrar_navegador()
    D.say("Y en la terminal puedes ver cada mensaje que llegó al servidor.")
    for _ in range(3):
        D.salida_segs([("INFO", G), (':     127.0.0.1:52418 - "POST /api/chat HTTP/1.1" 200 OK', BLANCO)], 0.3)
    D.hold()

    # ---------------------------------------------------------- CIERRE
    D.capitulo("Resumen")
    D.slide(SlideHTML("resumen"), frases=[
        "¡Y listo! Hagamos un resumen de lo que construimos.",
        "Un JARVIS que usa GptLuna como cerebro, bge-m3 y Qdrant para buscar en tus documentos, y PostgreSQL para recordar las conversaciones.",
        "Todo en Windows, sin Docker, y con una página web que te responde con voz.",
        "Como reto, agrega tus propios documentos a la carpeta docs, vuelve a ejecutar ingest.py, y pregúntale lo que quieras.",
    ])
    D.slide(SlideHTML("final"), frases=[
        "El código completo está en GitHub; te dejo el enlace en la descripción.",
        "Si te gustó, dale like, suscríbete y cuéntame en los comentarios qué le agregarías a tu JARVIS. ¡Nos vemos en el próximo video!",
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
PRONUNCIACION = [
    ("Set-ExecutionPolicy -Scope CurrentUser RemoteSigned", "set execiúshon pólisi, guión scoup, cárent iúser, rimóut sáind"),
    ("uvicorn app:app --reload", "iuvicorn, app dos puntos app, guión guión rilóud"),
    ("pip install -r requirements.txt", "pip instól guión erre ricuáirments punto te equis te"),
    ("ollama pull bge-m3", "olama pul, be ge e eme tres"),
    ("Add python.exe to PATH", "ad páiton punto exe tu pat"),
    (".venv\\Scripts\\activate", "punto venv, barra, scripts, barra, áctiveit"),
    ("'(.venv)'", "punto venv entre paréntesis"),
    ("C:\\proyectos", "ce dos puntos, proyectos"),
    ("C:\\qdrant", "ce dos puntos, cudrant"),
    ("File, Open Folder", "fail, óupen fólder"),
    ("text-embedding-3-small", "text embéding tres smol"),
    ("nomic-embed-text", "nómic embéd text"),
    ("platform.openai.com", "plátform punto open ei ai punto com"),
    ("requirements.txt", "ricuáirments punto te equis te"),
    ("perfil.txt", "perfil punto te equis te"),
    ("asistente.py", "asistente punto pai"),
    ("ingest.py", "ínyest punto pai"),
    ("app.py", "app punto pai"),
    ("app.js", "app punto yei es"),
    ("index.html", "índex punto hache te eme ele"),
    ("estilo.css", "estilo punto ce ese ese"),
    ("python.org", "páiton punto org"),
    ("ollama.com", "olama punto com"),
    ("/api/chat", "barra a pi barra chat"),
    ("app.mount", "app punto maunt"),
    ("python-dotenv", "páiton dot env"),
    ("langchain-algo", "lang chéin guión algo"),
    ("gpt-6-luna", "ge pe te seis luna"),
    ("GPT-6 Luna", "ge pe te seis luna"),
    ("GPT-6 Sol", "ge pe te seis sol"),
    ("Claude Opus 5.5", "clod ópus cinco punto cinco"),
    ("Claude Sonnet 5.5", "clod sónet cinco punto cinco"),
    ("Claude Haiku 5.5", "clod jáiku cinco punto cinco"),
    ("Gemini 4 Argon", "yémini cuatro árgon"),
    ("Artificial Analysis", "artifishal análisis"),
    (".venv", "punto venv"),
    (".env", "punto env"),
    (".txt", "punto te equis te"),
    (".zip", "punto zip"),
    ("os.getenv", "o ese punto guet env"),
    ("load_dotenv", "lóud dot env"),
    ("from_documents", "from dócuments"),
    ("chat_history", "chat jístori"),
    ("obtener_historial", "obtener historial"),
    ("buscar_contexto", "buscar contexto"),
    ("preguntar_a_jarvis", "preguntar a yarvis"),
    ("cambiarEstado", "cambiar estado"),
    ("agregarMensaje", "agregar mensaje"),
    ("SpeechSynthesis", "spich síntesis"),
    ("ChatOpenAI", "chat open ei ai"),
    ("OpenAI", "open ei ai"),
    ("ChatGPT", "chat ge pe te"),
    ("GptLuna", "ge pe te luna"),
    ("LangChain", "lang chéin"),
    ("langchain", "lang chéin"),
    ("FastAPI", "fast a pi i"),
    ("fastapi", "fast a pi i"),
    ("uvicorn", "iuvicorn"),
    ("Qdrant", "cudrant"),
    ("Ollama", "olama"),
    ("PostgreSQL", "póstgres"),
    ("postgres", "póstgres"),
    ("DeepSeek", "dip sik"),
    ("Gemini", "yémini"),
    ("Claude", "clod"),
    ("JARVIS", "yarvis"),
    ("Docker", "dóker"),
    ("WSL", "doble ve ese ele"),
    ("Python", "páiton"),
    ("python", "páiton"),
    ("PowerShell", "páuer shel"),
    ("Visual Studio Code", "visual estudio coud"),
    ("VS Code", "ve ese coud"),
    ("Windows", "uíndous"),
    ("embeddings", "embédings"),
    ("embedding", "embéding"),
    ("bge-m3", "be ge e eme tres"),
    ("GitHub", "guit jab"),
    ("Releases", "rilíses"),
    ("Enter", "énter"),
    ("Control + clic", "control clic"),
    ("Control + Shift +", "control shift"),
    ("Control + S", "control ese"),
    ("Control +", "control"),
    ("API key", "a pi kei"),
    ("API", "a pi"),
    ("psycopg", "sáico pe ge"),
    ("pip install", "pip instól"),
    ("prompt", "prómt"),
    ("retriever", "ritríver"),
    ("context", "cóntext"),
    ("fetch", "fech"),
    ("HTML", "hache te eme ele"),
    ("PC", "pe ce"),
    ("LLMs", "ele ele emes"),
    ("LLM", "ele ele eme"),
    ("RAG", "rag"),
    ("os", "o ese"),
    ("IA", "i a"),
    ("hilo", "hilo"),
    ("like", "láik"),
    ("id", "ai di"),
]


def texto_hablado(texto):
    """Convierte el texto del guion en el texto que pronuncia la voz."""
    t = texto
    for original, dicho in PRONUNCIACION:
        patron = re.escape(original)
        if original[0].isalnum() or original[0] == "_":
            patron = r"(?<![\w.])" + patron
        if original[-1].isalnum() or original[-1] == "_":
            patron += r"(?![\w])"
        flags = 0 if original in ("id", "os", "IA", "PC", "API", "RAG", "LLM", "LLMs") else re.IGNORECASE
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
        from kokoro_onnx import Kokoro
        modelo, voces = rutas_modelo()
        _kokoro = Kokoro(str(modelo), str(voces))
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
    """Pista de audio: narración + voz de JARVIS + teclado y clics, en los tiempos del video."""
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
    for inicio, texto in D.log_jarvis:
        poner(inicio, (VOZ_JARVIS, texto), 0.95)
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


# ============================================================== DEMOS DE LA PÁGINA WEB
# La página real de JARVIS (codigo/web) se abre en Chromium en "tiempo virtual":
# las animaciones CSS, la red (fetch) y la voz del navegador se controlan cuadro a cuadro,
# así el video muestra exactamente la página del proyecto.
INIT_DEMO = r"""
(() => {
  window.__pend = [];
  window.fetch = (url, opts) => new Promise((res) => window.__pend.push(res));
  window.__responder = (texto) => {
    const r = window.__pend.shift();
    if (r) r({ json: async () => ({ respuesta: texto }) });
  };
  const voz = { speak(u) { window.__u = u; }, cancel() {} };
  Object.defineProperty(window, "speechSynthesis", { value: voz, configurable: true });
  window.__finVoz = () => { const u = window.__u; window.__u = null; if (u && u.onend) u.onend(); };
  window.__anim = (vt) => {
    document.getAnimations().forEach((a) => {
      if (a.__t0 === undefined) a.__t0 = vt;
      a.pause();
      a.currentTime = Math.max(0, (vt - a.__t0) * 1000);
    });
  };
})();
"""


def _grabar_demo(args):
    import base64
    import io
    from playwright.sync_api import sync_playwright
    seg, eventos, n, firma = args
    carpeta = CACHE_WEB / seg
    carpeta.mkdir(parents=True, exist_ok=True)
    pagina = CODIGO / "web" / "index.html"
    with sync_playwright() as p:
        b = p.chromium.launch()
        # zoom de 125% para que el texto se lea bien en el video
        ctx = b.new_context(viewport={"width": round(W / 1.25), "height": round((H - NAV_TOP) / 1.25)},
                            device_scale_factor=1.25)
        ctx.add_init_script(INIT_DEMO)
        pg = ctx.new_page()
        cdp = ctx.new_cdp_session(pg)
        pg.goto(pagina.as_uri())
        pg.wait_for_timeout(300)
        pendientes = sorted(eventos, key=lambda e: e[0])
        i = 0
        for k in range(n):
            vt = k / FPS
            while i < len(pendientes) and pendientes[i][0] <= vt + 1e-6:
                ev = pendientes[i]
                tipo = ev[1]
                if tipo == "recargar":
                    pg.reload()
                    pg.wait_for_timeout(200)
                elif tipo == "foco":
                    pg.focus("#texto")
                elif tipo == "texto":
                    pg.evaluate("v => { document.querySelector('#texto').value = v; }", ev[2])
                elif tipo == "enviar":
                    pg.evaluate("document.querySelector('#form').requestSubmit()")
                elif tipo == "responder":
                    pg.evaluate("t => window.__responder(t)", ev[2])
                    pg.evaluate("new Promise(r => setTimeout(r, 30))")
                elif tipo == "fin_voz":
                    pg.evaluate("window.__finVoz()")
                i += 1
            pg.evaluate(f"window.__anim({vt:.4f})")
            datos = cdp.send("Page.captureScreenshot", {"format": "jpeg", "quality": 92, "optimizeForSpeed": True})["data"]
            (carpeta / f"{k:05d}.jpg").write_bytes(base64.b64decode(datos))
        b.close()
    (carpeta / "firma.json").write_text(firma, encoding="utf-8")
    return seg


def grabar_demos(D):
    """Genera los fotogramas de cada demo de la página web (uno por proceso)."""
    import shutil
    trabajos = []
    for seg, eventos in D.demos.items():
        n = 1 + max(s.navegador[1][2] for s in D.frames
                    if s.navegador and s.navegador[1][0] == "demo" and s.navegador[1][1] == seg)
        firma = json.dumps({"n": n, "eventos": eventos, "pagina": [
            (CODIGO / "web" / f).read_text(encoding="utf-8") for f in ("index.html", "estilo.css", "app.js")]})
        marca = CACHE_WEB / seg / "firma.json"
        if marca.exists() and marca.read_text(encoding="utf-8") == firma:
            continue   # ya está grabada y no cambió
        shutil.rmtree(CACHE_WEB / seg, ignore_errors=True)
        trabajos.append((seg, eventos, n, firma))
    if not trabajos:
        return
    print(f"Grabando {len(trabajos)} demos de la página web...", flush=True)
    with mp.get_context("spawn").Pool(len(trabajos)) as pool:
        for seg in pool.imap_unordered(_grabar_demo, trabajos):
            print(f"  demo '{seg}' lista", flush=True)


# ============================================================== RENDER EN PARALELO
SUBTITULOS = False   # el video va sin subtítulos (subtitulos.srt queda para YouTube)
FRAMES = None


def trabajador(args):
    idx, ini, fin, salida = args
    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
        "-crf", "20", "-pix_fmt", "yuv420p", str(salida)], stdin=subprocess.PIPE)
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
        pares = [(VOZ, e[2]) for e in D0.log] + [(VOZ_JARVIS, t) for _, t in D0.log_jarvis]
        archivos = preparar_voz(pares)
    D = guion()
    FRAMES = D.frames
    total = len(FRAMES) / FPS
    escribir_textos(D)
    print(f"Duración: {fmt_min(total)} ({len(FRAMES)} fotogramas)")
    if "--preview" in sys.argv:
        out = AQUI / "preview"
        out.mkdir(exist_ok=True)
        paso = int(sys.argv[sys.argv.index("--preview") + 1]) if len(sys.argv) > 2 else 20
        if "--sin-demos" not in sys.argv:
            grabar_demos(D)
        for k, f in enumerate(range(0, len(FRAMES), paso * FPS)):
            render(FRAMES[f], True).save(out / f"f_{k:03}.jpg", quality=90)
        print("Previews en", out)
        return
    grabar_demos(D)
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
