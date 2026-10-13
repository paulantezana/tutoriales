"""
Video tutorial: "Crea tu propio Asistente de IA" — simulación de VS Code.

Simula a una persona programando en Visual Studio Code (explorador de archivos,
pestañas, autocompletado, terminal integrada, mouse, atajos de teclado) y
explica cada bloque de código para principiantes.

Uso:
    pip install pillow pygments
    python render.py              # tutorial.mp4 + subtitulos.srt + guion.md
    python render.py --preview    # solo PNGs de muestra en video/preview/

Requiere ffmpeg. El código se lee de ../codigo, así que el video siempre
coincide con el proyecto.
"""
import copy
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
from pygments.lexers import PythonLexer, YamlLexer, IniLexer, TextLexer
from pygments.token import Token

AQUI = Path(__file__).parent
CODIGO = AQUI.parent / "codigo"
W, H, FPS = 1920, 1080, 30

# ============================================================== MARCA DEL CANAL
# Cambia estos valores para adaptar el video al estilo de tu canal.
CANAL = "Paul Antezana"
CURSO = "Curso: Crea tu propio Asistente de IA"
CLASE = "Tu primer asistente con RAG y memoria"
MARCA = (0, 122, 204)        # color principal
MARCA2 = (255, 196, 70)      # color de acento
FONDO_SLIDE = (12, 16, 27)

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
        lectura = max(2.4, len(texto) / 14.0)
        self.say_hasta = self.t + lectura
        self.sub_fin = self.t + lectura + 2.0
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
            fin_lectura = e[0] + max(2.4, len(e[2]) / 14.0) + 2.0
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
        self.set(click=1.0)
        self.wait(0.25)

    def atajo(self, texto, dur=1.3):
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
    def prompt(self):
        venv = (("(.venv) ", BLANCO),) if ".venv" in self.s.carpetas and self.venv_activo else ()
        return venv + (("usuario@pc", G), (":", BLANCO), ("~/asistente", B_), ("$ ", BLANCO))

    venv_activo = False

    def abrir_terminal(self):
        self.atajo("Ctrl + `")
        self.set(term_abierto=True, foco="terminal", term_actual=self.prompt())
        self._ajustar_scroll()
        self.wait(0.6)

    def maximizar_terminal(self, si=True):
        y = H - STATUS_H - self.s.term_alto + 20
        self.clic(BTN_MAX[0], y)
        self.set(term_alto=(H - STATUS_H - TITLE_H - 4) if si else 400)
        self.wait(0.4)

    def comando(self, cmd, cps=13):
        self.set(foco="terminal")
        for c in cmd:
            self.set(term_actual=self.s.term_actual + ((c, BLANCO),))
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
        self.atajo("Ctrl + L", 0.8)
        self.set(term_lineas=(), term_actual=self.prompt())
        self.wait(0.3)

    # ---------- slides
    def slide(self, obj, dur=None, frases=()):
        """Muestra una diapositiva animada mientras se narran las frases."""
        inicio = len(self.frames)
        if frases:
            self.say(frases[0])
        total = dur
        if total is None:
            total = sum(max(2.4, len(f) / 14.0) for f in frases) + 1.5
        n = round(total * FPS)
        cola = list(frases[1:])
        lectura = max(2.4, len(frases[0]) / 14.0) if frases else 0
        siguiente = lectura
        for i in range(n):
            t = i / FPS
            if cola and t >= siguiente:
                f = cola.pop(0)
                self.say(f)
                siguiente = t + max(2.4, len(f) / 14.0)
            fade = min(1.0, t / 0.3, (total - t) / 0.3)
            self.set(slide=(obj, t, total), fundido=max(0.0, fade), ocultar_mouse=True)
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
            for t, col in lineas[i]:
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
        d.text((W - 300, ty + 10), "bash", font=F_UI_S, fill=C_MUTED)
        d.text((W - 240, ty + 7), "+", font=F_UI_B, fill=C_MUTED)
        # maximizar ^ y cerrar ×
        mxx, myy = BTN_MAX[0], ty + 20
        maxim = s.term_alto > 500
        if maxim:
            d.line((mxx - 7, myy - 3, mxx, myy + 4, mxx + 7, myy - 3), fill=C_TEXT, width=2)
        else:
            d.line((mxx - 7, myy + 3, mxx, myy - 4, mxx + 7, myy + 3), fill=C_TEXT, width=2)
        d.text((W - 52, ty + 7), "×", font=F_SYM, fill=C_MUTED)
        # contenido
        ancho_chars = int((W - ED_X - 60) / TCW)
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
        reservado = 120 if s.subtitulo else 20
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
        lang = {"py": "Python", "yml": "YAML", "txt": "Plain Text"}.get(s.activo.rsplit(".", 1)[-1], "Properties")
        partes = [f"Ln {cl + 1}, Col {cc + 1}", "Spaces: 4", "UTF-8", "LF", lang]
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


# ============================================================== DIAPOSITIVAS
def fondo_slide():
    img = Image.new("RGB", (W, H), FONDO_SLIDE)
    d = ImageDraw.Draw(img)
    d.ellipse((W - 280, -140, W + 140, 280), fill=(20, 27, 44))
    d.ellipse((W - 350, -170, W + 50, 230), fill=FONDO_SLIDE)
    d.text((60, H - 60), CANAL, font=F_XS, fill=(110, 120, 145))
    d.text((W - 60, H - 60), CURSO, font=F_XS, fill=(110, 120, 145), anchor="ra")
    return img, d


def aparecer(t, t0, dur=0.5):
    return ease((t - t0) / dur)


class SlidePortada:
    def draw(self, t, dur):
        img, d = fondo_slide()
        a = aparecer(t, 0.1, 0.8)
        d.text((W / 2, 250), CURSO.upper(), font=F_S, fill=mix(FONDO_SLIDE, MARCA2, a), anchor="mm")
        d.text((W / 2, 360), "Crea tu propio", font=F_T2, fill=mix(FONDO_SLIDE, (170, 180, 200), a), anchor="mm")
        d.text((W / 2, 460), "Asistente de IA en Python", font=F_T1, fill=mix(FONDO_SLIDE, (255, 255, 255), a), anchor="mm")
        b = aparecer(t, 1.0, 0.8)
        chips = [("GptLuna", MARCA2), ("LangChain", (126, 211, 140)), ("Qdrant", (255, 120, 120)),
                 ("Ollama", (230, 230, 230)), ("PostgreSQL", (120, 170, 255))]
        anchos = [F_H.getlength(c) + 60 for c, _ in chips]
        x = W / 2 - (sum(anchos) + 22 * (len(chips) - 1)) / 2
        for (c, col), an in zip(chips, anchos):
            yy = 590 + (1 - b) * 20
            d.rounded_rectangle((x, yy, x + an, yy + 68), 34, outline=mix(FONDO_SLIDE, col, b), width=3)
            d.text((x + an / 2, yy + 34), c, font=F_H, fill=mix(FONDO_SLIDE, col, b), anchor="mm")
            x += an + 22
        c = aparecer(t, 1.8, 0.8)
        d.text((W / 2, 760), "Clase 1  ·  " + CLASE, font=F_B, fill=mix(FONDO_SLIDE, (170, 180, 200), c), anchor="mm")
        return img


class SlideConcepto:
    """Título + dibujo animado propio + puntos clave."""

    def __init__(self, num, titulo, puntos, dibujo):
        self.num, self.titulo, self.puntos, self.dibujo = num, titulo, puntos, dibujo

    def draw(self, t, dur):
        img, d = fondo_slide()
        a = aparecer(t, 0.0, 0.6)
        if self.num:
            d.text((120, 120), self.num, font=F_S, fill=mix(FONDO_SLIDE, MARCA2, a))
        d.text((120, 160), self.titulo, font=F_T2, fill=mix(FONDO_SLIDE, (255, 255, 255), a))
        d.rectangle((120, 250, 120 + 120 * a, 256), fill=MARCA)
        paso = max(1.2, (dur - 3) / max(1, len(self.puntos)))
        for i, p in enumerate(self.puntos):
            b = aparecer(t, 0.8 + i * paso, 0.5)
            if b <= 0:
                continue
            y = 320 + i * 110
            d.ellipse((126, y + 12, 146, y + 32), fill=mix(FONDO_SLIDE, MARCA2, b))
            for k, l in enumerate(wrap(p, F_B, 640)):
                d.text((170 + (1 - b) * 20, y + k * 46), l, font=F_B, fill=mix(FONDO_SLIDE, (235, 238, 245), b))
        self.dibujo(d, img, t, dur)
        return img


def caja(d, x, y, w, h, titulo, sub, col, a, fill=(28, 34, 52)):
    d.rounded_rectangle((x - w / 2, y - h / 2, x + w / 2, y + h / 2), 18,
                        fill=mix(FONDO_SLIDE, fill, a), outline=mix(FONDO_SLIDE, col, a), width=3)
    d.text((x, y - (14 if sub else 0)), titulo, font=F_H, fill=mix(FONDO_SLIDE, (255, 255, 255), a), anchor="mm")
    if sub:
        d.text((x, y + 26), sub, font=F_XS, fill=mix(FONDO_SLIDE, (160, 170, 190), a), anchor="mm")


def flecha(d, x0, y0, x1, y1, a, col=(110, 125, 160), w=5):
    if a <= 0:
        return
    xe, ye = x0 + (x1 - x0) * a, y0 + (y1 - y0) * a
    d.line((x0, y0, xe, ye), fill=col, width=w)
    if a >= 0.98:
        ang = math.atan2(y1 - y0, x1 - x0)
        s = 18
        d.polygon([(x1, y1), (x1 - s * math.cos(ang - 0.45), y1 - s * math.sin(ang - 0.45)),
                   (x1 - s * math.cos(ang + 0.45), y1 - s * math.sin(ang + 0.45))], fill=col)


def burbuja(d, x, y, texto, a, derecha=False, col=(40, 48, 70)):
    if a <= 0:
        return
    w = F_S.getlength(texto) + 50
    x0 = x - w if derecha else x
    d.rounded_rectangle((x0, y, x0 + w, y + 62), 22, fill=mix(FONDO_SLIDE, col, a))
    d.text((x0 + 25, y + 31), texto, font=F_S, fill=mix(FONDO_SLIDE, (255, 255, 255), a), anchor="lm")


def dib_llm(d, img, t, dur):
    cx = 1350
    a = aparecer(t, 0.5)
    burbuja(d, 980, 380, "¿Qué es la fotosíntesis?", a)
    flecha(d, cx, 460, cx, 520, aparecer(t, 1.2))
    b = aparecer(t, 1.6)
    d.rounded_rectangle((cx - 170, 530, cx + 170, 650), 26, fill=mix(FONDO_SLIDE, (50, 40, 10), b),
                        outline=mix(FONDO_SLIDE, MARCA2, b), width=4)
    d.text((cx, 572), "LLM", font=F_T2, fill=mix(FONDO_SLIDE, MARCA2, b), anchor="mm")
    d.text((cx, 625), "GptLuna", font=F_XS, fill=mix(FONDO_SLIDE, (220, 210, 180), b), anchor="mm")
    flecha(d, cx, 660, cx, 720, aparecer(t, 2.2))
    burbuja(d, 1720, 735, "Es el proceso por el cual las plantas...", aparecer(t, 2.6), True, (30, 70, 120))
    c = aparecer(t, dur * 0.62)
    if c > 0:
        burbuja(d, 980, 850, "¿A qué hora abre Luna Café?", c)
        d.text((1500, 880), "?  No lo sabe", font=F_H, fill=mix(FONDO_SLIDE, (255, 120, 120), c), anchor="lm")


def dib_embedding(d, img, t, dur):
    ox, oy, w, h = 980, 330, 780, 560
    a = aparecer(t, 0.3)
    d.rounded_rectangle((ox, oy, ox + w, oy + h), 20, outline=mix(FONDO_SLIDE, (60, 70, 100), a), width=2)
    puntos = [
        ("horario de atención", 230, 140, MARCA2, 0.8),
        ("¿a qué hora abren?", 300, 210, MARCA2, 1.3),
        ("lunes a sábado 7 a 21h", 190, 260, MARCA2, 1.8),
        ("Latte de Lúcuma", 560, 380, (126, 211, 140), 2.6),
        ("producto estrella", 610, 450, (126, 211, 140), 3.0),
        ("delivery gratis", 520, 110, (120, 170, 255), 3.4),
    ]
    for txt, px, py, col, t0 in puntos:
        b = aparecer(t, t0)
        if b <= 0:
            continue
        x, y = ox + px, oy + py
        d.ellipse((x - 11, y - 11, x + 11, y + 11), fill=mix(FONDO_SLIDE, col, b))
        d.text((x + 20, y), txt, font=F_XS, fill=mix(FONDO_SLIDE, (230, 230, 230), b), anchor="lm")
    c = aparecer(t, 4.2)
    if c > 0:
        d.ellipse((ox + 140, oy + 80, ox + 470, oy + 320), outline=mix(FONDO_SLIDE, MARCA2, c), width=3)
        d.text((ox + 20, oy + h + 20), "\"horario\" →  [0.12, -0.83, 0.44, 0.07, ... ]  (768 números)",
               font=F_XS, fill=mix(FONDO_SLIDE, (160, 170, 190), c))


def dib_qdrant(d, img, t, dur):
    a = aparecer(t, 0.4)
    burbuja(d, 1000, 340, "¿Hacen delivery?", a)
    flecha(d, 1180, 410, 1180, 470, aparecer(t, 1.0))
    b = aparecer(t, 1.3)
    d.rounded_rectangle((1000, 480, 1760, 820), 22, fill=mix(FONDO_SLIDE, (40, 22, 26), b),
                        outline=mix(FONDO_SLIDE, (255, 120, 120), b), width=3)
    d.text((1030, 500), "Qdrant", font=F_H, fill=mix(FONDO_SLIDE, (255, 140, 140), b))
    filas = [("Delivery gratis para pedidos mayores a 30 soles", 0.94),
             ("Horario: lunes a sábado de 7:00 a 21:00", 0.41),
             ("Producto estrella: el Latte de Lúcuma", 0.33)]
    for i, (txt, sc) in enumerate(filas):
        c = aparecer(t, 2.0 + i * 0.4)
        y = 570 + i * 78
        top = i == 0 and t > 3.6
        d.rounded_rectangle((1030, y, 1730, y + 62), 12,
                            fill=mix(FONDO_SLIDE, (70, 60, 20) if top else (34, 30, 40), c))
        d.text((1050, y + 31), txt, font=F_XS, fill=mix(FONDO_SLIDE, (235, 235, 235), c), anchor="lm")
        d.text((1715, y + 31), f"{sc:.2f}", font=F_S,
               fill=mix(FONDO_SLIDE, MARCA2 if top else (150, 150, 160), c), anchor="rm")


def dib_rag(d, img, t, dur):
    pasos = [("1. Pregunta", "¿Hacen delivery?", (230, 230, 230)),
             ("2. Buscar", "Qdrant encuentra el texto", (255, 120, 120)),
             ("3. Aumentar", "pregunta + contexto", MARCA2),
             ("4. Generar", "GptLuna responde", (126, 211, 140))]
    for i, (tit, sub, col) in enumerate(pasos):
        a = aparecer(t, 0.6 + i * 1.3)
        y = 360 + i * 150
        caja(d, 1360, y, 520, 110, tit, sub, col, a)
        if i:
            flecha(d, 1360, y - 95, 1360, y - 58, aparecer(t, 0.3 + i * 1.3))
    b = aparecer(t, 6.2)
    if b > 0:
        d.text((1660, 360), "R", font=F_T2, fill=mix(FONDO_SLIDE, MARCA2, b), anchor="lm")
        d.text((1660, 660), "A", font=F_T2, fill=mix(FONDO_SLIDE, MARCA2, b), anchor="lm")
        d.text((1660, 810), "G", font=F_T2, fill=mix(FONDO_SLIDE, MARCA2, b), anchor="lm")


def dib_memoria(d, img, t, dur):
    burbuja(d, 1760, 340, "¿Cuál es su producto estrella?", aparecer(t, 0.4), True, (30, 70, 120))
    burbuja(d, 960, 430, "El Latte de Lúcuma.", aparecer(t, 1.2))
    burbuja(d, 1760, 540, "¿Y cuánto cuesta el delivery?", aparecer(t, 2.0), True, (30, 70, 120))
    a = aparecer(t, 3.0)
    burbuja(d, 960, 630, "Gratis en pedidos mayores a 30 soles.", a)
    b = aparecer(t, dur * 0.55)
    if b > 0:
        d.rounded_rectangle((960, 760, 1760, 880), 20, fill=mix(FONDO_SLIDE, (22, 34, 60), b),
                            outline=mix(FONDO_SLIDE, (120, 170, 255), b), width=3)
        d.text((990, 785), "PostgreSQL  ·  tabla chat_history", font=F_S,
               fill=mix(FONDO_SLIDE, (150, 190, 255), b))
        d.text((990, 830), "hilo 7f3c…  →  4 mensajes guardados", font=F_XS,
               fill=mix(FONDO_SLIDE, (210, 215, 225), b))


def dib_arquitectura(d, img, t, dur):
    a = lambda t0: aparecer(t, t0)
    d.text((960, 300), "INGESTA  (una vez)", font=F_XS, fill=mix(FONDO_SLIDE, MARCA2, a(0.3)))
    caja(d, 1060, 390, 200, 100, "docs", "*.txt", (180, 180, 190), a(0.4))
    flecha(d, 1165, 390, 1230, 390, a(0.9))
    caja(d, 1340, 390, 200, 100, "Ollama", "embeddings", (230, 230, 230), a(1.0))
    flecha(d, 1445, 390, 1510, 390, a(1.5))
    caja(d, 1620, 390, 200, 100, "Qdrant", "vectores", (255, 120, 120), a(1.6))
    d.text((960, 520), "CHAT  (cada pregunta)", font=F_XS, fill=mix(FONDO_SLIDE, MARCA2, a(2.5)))
    caja(d, 1060, 620, 200, 100, "Tú", "pregunta", MARCA2, a(2.6))
    flecha(d, 1165, 620, 1230, 620, a(3.0))
    caja(d, 1340, 620, 200, 100, "app.py", "LangChain", (126, 211, 140), a(3.1))
    flecha(d, 1420, 565, 1560, 445, a(3.8))
    caja(d, 1620, 620, 200, 100, "Postgres", "historial", (120, 170, 255), a(4.6))
    flecha(d, 1445, 620, 1510, 620, a(4.5))
    caja(d, 1340, 830, 200, 100, "GptLuna", "LLM", MARCA2, a(5.6))
    flecha(d, 1340, 675, 1340, 775, a(5.4))


class SlideFinal:
    def draw(self, t, dur):
        img, d = fondo_slide()
        a = aparecer(t, 0.1, 0.8)
        d.text((W / 2, 260), "¡Gracias por ver!", font=F_T1, fill=mix(FONDO_SLIDE, (255, 255, 255), a), anchor="mm")
        d.text((W / 2, 380), "Código completo en GitHub", font=F_H, fill=mix(FONDO_SLIDE, (160, 170, 190), a), anchor="mm")
        d.text((W / 2, 440), "github.com/paulantezana/tutoriales", font=F_H, fill=mix(FONDO_SLIDE, MARCA, a), anchor="mm")
        b = aparecer(t, 1.2, 0.8)
        botones = [("Me gusta", MARCA), ("Suscríbete", (230, 60, 60)), ("Comenta", MARCA2)]
        x = W / 2 - (3 * 300 + 2 * 40) / 2
        for txt, col in botones:
            y = 560 + (1 - b) * 30
            d.rounded_rectangle((x, y, x + 300, y + 90), 45, fill=mix(FONDO_SLIDE, col, b))
            d.text((x + 150, y + 45), txt, font=F_H, fill=mix(FONDO_SLIDE, (255, 255, 255), b), anchor="mm")
            x += 340
        c = aparecer(t, 2.4, 0.8)
        d.text((W / 2, 760), "Próxima clase: interfaz web para tu asistente", font=F_B,
               fill=mix(FONDO_SLIDE, MARCA2, c), anchor="mm")
        return img


# ============================================================== RENDER DE UN FOTOGRAMA
def render(s, blink):
    if s.slide:
        obj, t, dur = s.slide
        img = obj.draw(t, dur)
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
    if s.subtitulo:
        capa = capa_subtitulo(s.subtitulo)
        img.paste(capa, (int(W / 2 - capa.width / 2 + (ED_X / 2 if not s.slide else 0)),
                         H - STATUS_H - 18 - capa.height), capa)
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


ID = "7f3c2a10-5b8e-4d21-9a6f-0c1e2b3d4f5a"
CHAT = [
    ("¿Cuál es su producto estrella?",
     "¡Nuestro producto estrella es el Latte de Lúcuma! Te lo recomiendo mucho."),
    ("¿Y hasta qué hora atienden?",
     "Atendemos de lunes a sábado de 7:00 a 21:00. Los domingos estamos cerrados."),
    ("¿Hacen delivery?",
     "¡Sí! El delivery es gratis en pedidos mayores a 30 soles."),
]


def correr_chat(D, preguntas, id_hilo=""):
    D.comando("python app.py")
    D.wait(1.0)
    D.preguntar("ID de hilo (Enter = nuevo): ", BLANCO, id_hilo)
    D.salida(f"Hilo: {ID}  (escribe 'salir' para terminar)\n", BLANCO, 0.2)
    for p, r in preguntas:
        D.preguntar("Tú: ", BLANCO, p)
        D.responder(r)


def guion():
    D = Director()
    archivos_finales = {
        "docker-compose.yml": leer("docker-compose.yml"),
        "requirements.txt": leer("requirements.txt"),
        ".env": leer(".env.example"),
        "docs/empresa.txt": leer("docs/empresa.txt"),
        "ingest.py": leer("ingest.py"),
        "app.py": leer("app.py"),
    }

    # ---------------------------------------------------------- INTRO
    D.capitulo("Introducción")
    D.slide(SlidePortada(), frases=[
        "Hola, ¿qué tal? Bienvenidos a este curso, donde vamos a crear nuestro propio asistente de inteligencia artificial.",
        "No te preocupes si nunca has trabajado con IA: voy a explicar cada concepto y cada línea de código, paso a paso.",
    ])

    # Demo del resultado final
    D.capitulo("Resultado final")
    D.set(files=dict(archivos_finales), carpetas={".venv"}, tabs=("app.py",), activo="app.py",
          cursor=(0, 0), sucios=frozenset(), term_abierto=True,
          term_alto=H - STATUS_H - TITLE_H - 4, foco="terminal", mouse=(1500, 300))
    D.venv_activo = True
    D.set(term_actual=D.prompt())
    D.say("Antes de empezar, mira lo que vamos a tener al terminar este video.")
    correr_chat(D, CHAT[:2])
    D.say("Es un asistente que responde usando la información de NUESTROS documentos, en este caso de una cafetería.", esperar=True)
    D.say("Y además recuerda la conversación: fíjate que en la segunda pregunta no repetí de qué estábamos hablando.", esperar=True)
    D.preguntar("Tú: ", BLANCO, "salir")
    D.fin_comando()
    D.wait(0.8)

    # ---------------------------------------------------------- CONCEPTOS
    D.capitulo("Conceptos básicos")
    D.slide(SlideConcepto("CONCEPTO 1", "¿Qué es un LLM?", [
        "Una IA que entiende y escribe texto",
        "Le envías un mensaje y te responde",
        "Usaremos GptLuna como LLM",
    ], dib_llm), frases=[
        "Primero, unos conceptos rápidos. Un LLM, o modelo de lenguaje, es una inteligencia artificial que entiende y escribe texto, como ChatGPT.",
        "Funciona así: le enviamos un mensaje, y nos responde con otro texto. En este curso usaremos GptLuna como nuestro LLM.",
        "Pero hay un problema: el LLM no conoce la información de TU negocio. No sabe tus horarios, tus precios ni tus productos.",
    ])
    D.slide(SlideConcepto("CONCEPTO 2", "Embeddings", [
        "Convierten un texto en una lista de números",
        "Textos parecidos → números parecidos",
        "Los generamos gratis con Ollama",
    ], dib_embedding), frases=[
        "Para resolverlo usamos embeddings. Un embedding convierte un texto en una lista de números.",
        "Lo interesante es que textos con significado parecido quedan con números parecidos, es decir, quedan 'cerca' en este mapa.",
        "Por ejemplo, 'horario de atención' queda cerca de '¿a qué hora abren?', aunque usen palabras distintas.",
        "Estos números los va a generar Ollama, un programa gratuito que corre en tu propia computadora.",
    ])
    D.slide(SlideConcepto("CONCEPTO 3", "Base de datos vectorial", [
        "Guarda los textos junto a sus vectores",
        "Encuentra los más parecidos a una pregunta",
        "Usaremos Qdrant",
    ], dib_qdrant), frases=[
        "Esos vectores los guardamos en una base de datos vectorial. Nosotros usaremos Qdrant.",
        "Cuando llega una pregunta, Qdrant la compara con todos los textos guardados y nos devuelve los más parecidos, con un puntaje.",
    ])
    D.slide(SlideConcepto("CONCEPTO 4", "RAG", [
        "Retrieval: buscar la información",
        "Augmented: añadirla a la pregunta",
        "Generation: el LLM responde",
    ], dib_rag), frases=[
        "Juntando todo tenemos lo que se conoce como RAG. Suena complicado, pero son solo cuatro pasos.",
        "Llega la pregunta, buscamos la información relevante en Qdrant, la añadimos a la pregunta, y el LLM genera la respuesta.",
        "Así el asistente responde con datos reales de tu negocio, y no se inventa cosas.",
    ])
    D.slide(SlideConcepto("CONCEPTO 5", "Memoria del chat", [
        "Cada conversación es un 'hilo'",
        "Guardamos cada mensaje en PostgreSQL",
        "Así entiende preguntas de seguimiento",
    ], dib_memoria), frases=[
        "El último concepto es la memoria. Si pregunto '¿y cuánto cuesta el delivery?', el asistente necesita recordar de qué hablábamos.",
        "Por eso guardaremos cada conversación, a la que llamaremos 'hilo', en una base de datos PostgreSQL.",
    ])
    D.slide(SlideConcepto("EL PLAN", "Así funcionará", [
        "ingest.py carga tus documentos",
        "app.py es el chat",
        "LangChain une todas las piezas",
    ], dib_arquitectura), frases=[
        "Este es el plan completo. Vamos a escribir dos programas en Python.",
        "El primero, ingest.py, lee nuestros documentos, los convierte en vectores con Ollama y los guarda en Qdrant. Solo se ejecuta una vez.",
        "El segundo, app.py, es el chat: busca el contexto en Qdrant, lee el historial en PostgreSQL y le pregunta a GptLuna.",
        "Y para unir todas estas piezas usaremos LangChain, una librería de Python hecha justamente para esto.",
    ])
    D.slide(SlideConcepto("ANTES DE EMPEZAR", "Lo que necesitas", [
        "Python 3.10 o superior",
        "Docker Desktop",
        "Visual Studio Code",
        "Una API key de GptLuna",
    ], lambda *a: None), frases=[
        "Para seguir el tutorial necesitas tener instalado Python, Docker y Visual Studio Code.",
        "Y una API key de GptLuna, que es la clave que nos permite usar su modelo.",
    ])

    # ---------------------------------------------------------- PASO 1: DOCKER
    D.s = Estado()
    D.venv_activo = False
    D.set(mouse=(1200, 640))
    D.capitulo("Paso 1 · Docker")
    D.say("Bien, ¡manos a la obra! Abrí en Visual Studio Code una carpeta vacía llamada 'asistente'.", esperar=True)
    D.say("Lo primero es levantar los tres servicios que necesitamos: Qdrant, PostgreSQL y Ollama.")
    D.say("Para no instalarlos uno por uno, usaremos Docker. Creamos un archivo llamado docker-compose.yml.")
    D.nuevo_archivo("docker-compose.yml")
    b = piezas("docker-compose.yml", ["  postgres:", "  ollama:", "volumes:"])
    D.escribir(b[0])
    D.resaltar("qdrant:", "qdrant_data:/", titulo="Servicio Qdrant",
               nota="image: el programa a descargar\nports: el puerto para conectarnos (6333)\nvolumes: guarda los datos en tu PC",
               frases=["Dentro de 'services' definimos cada servicio. El primero es Qdrant.",
                       "'image' es el programa que Docker va a descargar, y 'ports' es el puerto por el que nos vamos a conectar: el 6333.",
                       "El volumen sirve para que los datos no se borren cuando apaguemos el contenedor."])
    D.escribir(b[1])
    D.resaltar("postgres:", "pg_data:/", titulo="Servicio PostgreSQL",
               nota="Usuario: luna  ·  Contraseña: luna\nBase de datos: asistente  ·  Puerto: 5432",
               frases=["Ahora PostgreSQL. Con 'environment' le decimos el usuario, la contraseña y el nombre de la base de datos.",
                       "Recuerda estos datos, porque los usaremos más adelante para conectarnos."])
    D.escribir(b[2])
    D.say("Y por último Ollama, en el puerto 11434. Él se encargará de generar los embeddings.", esperar=True)
    D.escribir(b[3])
    D.say("Al final declaramos los tres volúmenes. Guardamos con Control + S.")
    D.guardar()
    D.hold()

    D.say("Ahora abrimos la terminal integrada de VS Code con Control + comilla invertida.")
    D.abrir_terminal()
    D.say("Y escribimos 'docker compose up -d'. La '-d' hace que los servicios corran en segundo plano.")
    D.comando("docker compose up -d")
    D.salida("[+] Running 3/3", BLANCO, 0.3)
    for img_ in ["qdrant", "postgres", "ollama"]:
        D.salida_segs([(" ✔ ", G), (f"{img_} Pulled", BLANCO)], 0.6)
    D.salida_segs([("[+] Running 7/7", BLANCO)], 0.2)
    for linea in ["Network asistente_default         Created",
                  "Volume \"asistente_qdrant_data\"    Created",
                  "Volume \"asistente_pg_data\"        Created",
                  "Volume \"asistente_ollama_data\"    Created",
                  "Container asistente-qdrant-1      Started",
                  "Container asistente-postgres-1    Started",
                  "Container asistente-ollama-1      Started"]:
        D.salida_segs([(" ✔ ", G), (linea, BLANCO)], 0.25)
    D.fin_comando()
    D.say("La primera vez tarda un poco, porque Docker descarga las imágenes. Listo, los tres servicios están corriendo.", esperar=True)
    D.say("Ahora descargamos dentro de Ollama el modelo que genera los embeddings: nomic-embed-text.")
    D.comando("docker compose exec ollama ollama pull nomic-embed-text")
    D.salida("pulling manifest", BLANCO, 0.6)
    D.salida("", BLANCO, 0)
    for pct in range(0, 101, 4):
        llenos = pct * 30 // 100
        barra = "█" * llenos + " " * (30 - llenos)
        mb = 274 * pct // 100
        D.set(term_lineas=D.s.term_lineas[:-1] + (((f"pulling 970aa74c0a90... {pct:3d}% ▕{barra}▏ {mb:3d} MB/274 MB", BLANCO),),))
        D.wait(0.12)
    for linea in ["verifying sha256 digest", "writing manifest", "success"]:
        D.salida(linea, BLANCO, 0.3)
    D.fin_comando()
    D.hold()

    # ---------------------------------------------------------- PASO 2: PYTHON
    D.capitulo("Paso 2 · Entorno Python")
    D.limpiar_terminal()
    D.say("Ahora preparamos Python. Primero creamos un entorno virtual: una carpeta donde se instalan las librerías solo para este proyecto.")
    D.comando("python -m venv .venv")
    D.set(carpetas={".venv"})
    D.fin_comando()
    D.say("Mira, en el explorador apareció la carpeta .venv.", esperar=True)
    D.say("Lo activamos. En Windows el comando es '.venv\\Scripts\\activate'.")
    D.comando("source .venv/bin/activate")
    D.venv_activo = True
    D.fin_comando()
    D.say("Fíjate que ahora la terminal muestra '(.venv)' al inicio: eso significa que el entorno está activo.", esperar=True)

    D.say("Ahora creamos el archivo requirements.txt, con la lista de librerías que vamos a necesitar.")
    D.nuevo_archivo("requirements.txt")
    D.escribir(leer("requirements.txt"))
    D.guardar()
    D.resaltar("langchain", "langchain-postgres", titulo="LangChain y sus integraciones",
               nota="langchain: une todas las piezas\nopenai → GptLuna  ·  ollama → embeddings\nqdrant y postgres → bases de datos",
               frases=["'langchain' es la librería principal que une todas las piezas.",
                       "Cada 'langchain-algo' es una integración: openai para hablar con GptLuna, ollama para los embeddings, y qdrant y postgres para las bases de datos."])
    D.resaltar("langchain-text-splitters", "python-dotenv", titulo="Otras librerías",
               nota="text-splitters: corta textos largos\npsycopg: conecta Python con PostgreSQL\npython-dotenv: lee el archivo .env",
               frases=["text-splitters sirve para cortar textos largos, psycopg conecta Python con PostgreSQL, y python-dotenv lee nuestra configuración."])
    D.say("Las instalamos con 'pip install -r requirements.txt'.")
    D.comando("pip install -r requirements.txt")
    paquetes = ["langchain", "langchain-openai", "langchain-ollama", "langchain-qdrant",
                "langchain-postgres", "langchain-text-splitters", "psycopg[binary]", "python-dotenv"]
    for p in paquetes:
        D.salida(f"Collecting {p}", BLANCO, 0.18)
        D.salida(f"  Downloading {p.split('[')[0].replace('-', '_')}-0.3.x-py3-none-any.whl", GRIS, 0.12)
    for p in ["openai", "qdrant-client", "pydantic", "httpx", "numpy", "sqlalchemy", "tiktoken"]:
        D.salida(f"Collecting {p} (from langchain-openai)", BLANCO, 0.1)
    D.salida("Installing collected packages: ...", BLANCO, 1.2)
    D.salida("Successfully installed langchain langchain-ollama langchain-openai langchain-postgres "
             "langchain-qdrant langchain-text-splitters psycopg python-dotenv qdrant-client openai ...", BLANCO, 0.2)
    D.fin_comando()
    D.say("¡Perfecto! Ya tenemos todo instalado.", esperar=True)

    # ---------------------------------------------------------- PASO 3: .env
    D.capitulo("Paso 3 · Configuración")
    D.say("Ahora la configuración. Creamos un archivo llamado .env: aquí van las claves y direcciones, separadas del código.")
    D.nuevo_archivo(".env")
    b = piezas(".env.example", ["# Ollama", "# Qdrant", "# Postgres"])
    D.escribir(b[0])
    D.resaltar("GPTLUNA_BASE_URL", "GPTLUNA_MODEL", titulo="Datos de GptLuna",
               nota="GptLuna es compatible con la API de OpenAI.\nRevisa en tu cuenta la URL, tu API key y el nombre del modelo.",
               frases=["GptLuna funciona igual que la API de OpenAI, así que solo necesitamos tres datos: la URL, la API key y el nombre del modelo.",
                       "Revisa los valores exactos en el panel de tu cuenta de GptLuna, y reemplaza 'tu_api_key' por tu clave."])
    D.escribir(b[1] + b[2] + b[3])
    D.resaltar("OLLAMA_URL", "PG_URL", titulo="Nuestros servicios de Docker",
               nota="Las direcciones de Ollama, Qdrant y PostgreSQL.\n'documentos' será el nombre de la colección en Qdrant.",
               frases=["Debajo van las direcciones de los servicios que levantamos con Docker, con los mismos puertos.",
                       "Fíjate que en PG_URL aparecen el usuario, la contraseña y la base de datos que definimos en docker-compose."])
    D.guardar()
    D.say("Un consejo importante: este archivo tiene tu clave secreta. ¡Nunca lo subas a GitHub!", esperar=True)

    # ---------------------------------------------------------- PASO 4: DOCUMENTOS
    D.capitulo("Paso 4 · Documentos")
    D.say("Ahora necesitamos los documentos que el asistente va a 'leer'. Creamos una carpeta docs con un archivo empresa.txt.")
    D.nuevo_archivo("docs/empresa.txt")
    D.escribir(leer("docs/empresa.txt"), cps=20, autocompletar=False)
    D.guardar()
    D.say("Como ejemplo, uso la información de una cafetería imaginaria: Luna Café. Su horario, su producto estrella, el delivery y el contacto.", esperar=True)
    D.say("Tú aquí puedes poner la información de tu negocio, tus manuales o tus preguntas frecuentes.", esperar=True)

    # ---------------------------------------------------------- PASO 5: INGESTA
    D.capitulo("Paso 5 · ingest.py")
    D.say("Ahora sí, nuestro primer programa: ingest.py. Su trabajo es leer los documentos, convertirlos en vectores y guardarlos en Qdrant.")
    D.nuevo_archivo("ingest.py")
    b = piezas("ingest.py", ["load_dotenv()", "# 1.", "# 2.", "# 3.", "# 4.", "print("])
    D.escribir(b[0])
    D.resaltar("import os", "from langchain_qdrant", titulo="Importaciones",
               nota="Traemos las herramientas que vamos a usar:\nleer archivos, cortar textos, Ollama y Qdrant.",
               frases=["Empezamos importando lo que vamos a usar. 'os' nos permite leer variables de configuración, y 'Path' trabajar con archivos.",
                       "De LangChain traemos Document, el cortador de textos, los embeddings de Ollama y la conexión con Qdrant."])
    D.escribir(b[1])
    D.say("load_dotenv() lee el archivo .env, para que podamos usar esas variables en el código.", esperar=True)
    D.escribir(b[2])
    D.resaltar("documentos = [", "]", titulo="1. Cargar documentos",
               nota="Por cada archivo .txt de la carpeta docs,\ncreamos un Document = texto + datos extra (metadata).",
               frases=["Aquí recorremos todos los archivos .txt de la carpeta docs.",
                       "Por cada archivo creamos un Document de LangChain: page_content es el texto, y en metadata guardamos el nombre del archivo."])
    D.escribir(b[3])
    D.resaltar("splitter =", "fragmentos =", titulo="2. Dividir en fragmentos",
               nota="chunk_size=500 → trozos de 500 caracteres\nchunk_overlap=50 → se repiten 50 caracteres entre trozos",
               frases=["Los documentos largos se cortan en fragmentos de 500 caracteres. Así, luego buscamos solo el pedazo que importa.",
                       "chunk_overlap repite 50 caracteres entre un fragmento y el siguiente, para no cortar una idea por la mitad."])
    D.escribir(b[4])
    D.resaltar("embeddings =", ")", titulo="3. Embeddings con Ollama",
               nota="os.getenv(\"EMBED_MODEL\") lee el valor del archivo .env\n→ nomic-embed-text",
               frases=["Creamos el generador de embeddings con Ollama. Con os.getenv leemos el modelo y la dirección desde el archivo .env."])
    D.escribir(b[5])
    D.resaltar("QdrantVectorStore.from_documents", ")", titulo="4. Guardar en Qdrant",
               nota="from_documents hace todo el trabajo:\ngenera el vector de cada fragmento y lo guarda.",
               frases=["Y aquí la magia: from_documents toma cada fragmento, le pide a Ollama su vector, y guarda todo en la colección de Qdrant."])
    D.escribir(b[6])
    D.say("Al final mostramos un mensaje con cuántos fragmentos se guardaron. Guardamos el archivo.")
    D.guardar()
    D.hold()
    D.say("Vamos a ejecutarlo en la terminal: python ingest.py.")
    D.limpiar_terminal()
    D.comando("python ingest.py")
    D.wait(1.6)
    D.salida("Listo: 1 fragmentos guardados en Qdrant", BLANCO, 0.4)
    D.fin_comando()
    D.say("¡Funciona! Como nuestro documento es corto, quedó en un solo fragmento. Ya está guardado en Qdrant.", esperar=True)

    # ---------------------------------------------------------- PASO 6: APP
    D.capitulo("Paso 6 · app.py")
    D.say("Ahora la parte principal: el asistente. Creamos el archivo app.py.")
    D.nuevo_archivo("app.py")
    b = piezas("app.py", ["load_dotenv()", "# --- LLM", "# --- Retriever", "vectorstore =",
                          "retriever =", "# --- Memoria", "def obtener_historial", "# --- Prompt",
                          "prompt =", "def buscar_contexto", "cadena =", "asistente =",
                          "# --- Chat", "    while True:"])
    D.escribir(b[0])
    D.resaltar("import os", "import psycopg", titulo="Librerías básicas",
               nota="uuid: crea identificadores únicos para cada hilo\npsycopg: conexión con PostgreSQL",
               frases=["Importamos os, uuid para crear un identificador único para cada conversación, y psycopg para conectarnos a PostgreSQL."])
    D.resaltar("from langchain_openai", "from langchain_postgres", titulo="Una pieza por servicio",
               nota="ChatOpenAI → GptLuna\nOllamaEmbeddings → embeddings\nQdrantVectorStore → búsqueda\nPostgresChatMessageHistory → memoria",
               frases=["Luego, una pieza de LangChain por cada servicio: GptLuna, Ollama, Qdrant y la memoria en PostgreSQL."])
    D.resaltar("from langchain_core.prompts", "from langchain_core.output_parsers", titulo="Herramientas para armar la cadena",
               nota="Las usaremos para construir el 'camino' que sigue\ncada pregunta hasta convertirse en respuesta.",
               frases=["Y estas son herramientas para armar la 'cadena', que es el camino que sigue cada pregunta. Las veremos en un momento."])
    D.escribir(b[1] + b[2])
    D.resaltar("llm = ChatOpenAI(", ")", titulo="El LLM: GptLuna",
               nota="Usamos ChatOpenAI porque GptLuna es compatible con OpenAI.\nEl truco: cambiar base_url por la de GptLuna.\ntemperature baja = respuestas más precisas",
               frases=["Configuramos el LLM. Como GptLuna es compatible con OpenAI, usamos ChatOpenAI y solo cambiamos la base_url por la de GptLuna.",
                       "La temperatura controla la creatividad: con 0.3 las respuestas son más precisas y menos inventadas."])
    D.escribir(b[3] + b[4])
    D.resaltar("embeddings = OllamaEmbeddings(", "url=os.getenv(\"QDRANT_URL\")", titulo="Conectar con Qdrant",
               nota="Usamos la colección que ya creó ingest.py,\ncon el MISMO modelo de embeddings.",
               frases=["Ahora nos conectamos a la colección que ya creamos con ingest.py. Es importante usar el mismo modelo de embeddings."])
    D.escribir(b[5])
    D.resaltar("retriever =", None, titulo="El buscador (retriever)",
               nota="k=3 → devuelve los 3 fragmentos más parecidos a la pregunta",
               frases=["El retriever es nuestro buscador: por cada pregunta nos devolverá los 3 fragmentos más parecidos."])
    D.escribir(b[6])
    D.resaltar("conn = psycopg.connect", "create_tables", titulo="Memoria en PostgreSQL",
               nota="1. Nos conectamos a PostgreSQL\n2. Creamos la tabla chat_history (si no existe)",
               frases=["Ahora la memoria. Nos conectamos a PostgreSQL con la dirección del .env, y creamos la tabla chat_history, donde se guardarán los mensajes."])
    D.escribir(b[7])
    D.resaltar("def obtener_historial", "return PostgresChatMessageHistory", titulo="Historial de un hilo",
               nota="Recibe el id del hilo (session_id)\ny devuelve los mensajes de ESA conversación.",
               frases=["Esta función recibe el identificador de un hilo, el session_id, y devuelve el historial de esa conversación.",
                       "Así, cada conversación tiene su propia memoria, separada de las demás."])
    D.escribir(b[8])
    D.resaltar("SISTEMA =", "{context}", titulo="Instrucciones del asistente",
               nota="Le decimos cómo comportarse.\n{context} se reemplazará por los textos que encuentre Qdrant.",
               frases=["Estas son las instrucciones del asistente: le decimos que sea amable, que responda solo con el contexto, y que si no sabe, lo diga.",
                       "Las llaves con 'context' son un espacio vacío: ahí LangChain pondrá los textos que encuentre Qdrant."])
    D.escribir(b[9])
    D.resaltar("prompt = ChatPromptTemplate", "])", titulo="El prompt: 3 partes",
               nota="system → las instrucciones con el contexto\nhistory → los mensajes anteriores del hilo\nhuman → la pregunta del usuario",
               frases=["El prompt es el mensaje completo que le enviaremos a GptLuna, y tiene tres partes.",
                       "Las instrucciones con el contexto, el historial de la conversación, y la pregunta actual del usuario."])
    D.escribir(b[10])
    D.resaltar("def buscar_contexto", "return", titulo="Buscar contexto",
               nota="1. El retriever busca en Qdrant con la pregunta\n2. Unimos el texto de los fragmentos encontrados",
               frases=["buscar_contexto toma la pregunta, le pide al retriever los fragmentos parecidos, y une sus textos en uno solo."])
    D.escribir(b[11])
    D.resaltar("cadena = (", "StrOutputParser()", titulo="La cadena (el camino de la pregunta)",
               nota="1. Agrega el contexto  →  2. Arma el prompt\n3. Se lo envía a GptLuna  →  4. Devuelve solo el texto\nEl símbolo | significa: \"y luego pásaselo a...\"",
               frases=["Y esta es la cadena. El símbolo de la barra vertical significa 'y luego pásaselo a'.",
                       "Primero agregamos el contexto, luego armamos el prompt, se lo pasamos a GptLuna, y al final nos quedamos solo con el texto de la respuesta."])
    D.escribir(b[12])
    D.resaltar("asistente = RunnableWithMessageHistory", "history_messages_key", titulo="Cadena + memoria",
               nota="Envuelve la cadena para que, en cada mensaje:\n· lea el historial del hilo\n· guarde la pregunta y la respuesta",
               frases=["Finalmente envolvemos la cadena con RunnableWithMessageHistory. Esto le agrega la memoria.",
                       "En cada mensaje lee el historial del hilo, y al terminar guarda automáticamente la pregunta y la respuesta en PostgreSQL."])
    D.escribir(b[13])
    D.resaltar("session_id = input", "print(f\"Hilo", titulo="Elegir el hilo",
               nota="Si presionas Enter, se crea un hilo nuevo con uuid4().\nSi pegas un id anterior, continúas esa conversación.",
               frases=["Ya solo falta el chat en la consola. Primero pedimos el id del hilo: si presionamos Enter, se crea uno nuevo con uuid4."])
    D.escribir(b[14])
    D.resaltar("while True:", "print(f\"Asistente", titulo="El bucle del chat",
               nota="Repite: pide una pregunta → asistente.invoke(...) → muestra la respuesta.\nSi escribes 'salir', termina.",
               frases=["Y este bucle se repite para siempre: pide una pregunta, se la envía al asistente junto con el session_id, y muestra la respuesta.",
                       "Si escribimos 'salir', el programa termina."])
    D.guardar()
    D.say("¡Y listo! Todo el asistente en unas 90 líneas de código. Vamos a probarlo.", esperar=True)

    # ---------------------------------------------------------- PASO 7: PRUEBA
    D.capitulo("Paso 7 · ¡A probar!")
    D.limpiar_terminal()
    D.say("Maximizo la terminal para verlo mejor, y ejecutamos python app.py.")
    D.maximizar_terminal(True)
    D.mover(1200, 500, 0.4)
    correr_chat(D, CHAT[:1])
    D.say("Presioné Enter, así que se creó un hilo nuevo. Le pregunto por el producto estrella... ¡y responde con la información de nuestro documento!", esperar=True)
    D.preguntar("Tú: ", BLANCO, CHAT[1][0])
    D.responder(CHAT[1][1])
    D.say("Ahora pregunto '¿Y hasta qué hora atienden?'. Funciona porque recibe el historial de la conversación.", esperar=True)
    D.preguntar("Tú: ", BLANCO, CHAT[2][0])
    D.responder(CHAT[2][1])
    D.preguntar("Tú: ", BLANCO, "salir")
    D.fin_comando()
    D.say("Ahora la prueba de fuego para la memoria: salimos, y volvemos a entrar con el mismo id de hilo.", esperar=True)
    D.comando("python app.py")
    D.wait(1.0)
    D.preguntar("ID de hilo (Enter = nuevo): ", BLANCO, ID, cps=40)
    D.salida(f"Hilo: {ID}  (escribe 'salir' para terminar)\n", BLANCO, 0.2)
    D.preguntar("Tú: ", BLANCO, "¿Qué te pregunté antes?")
    D.responder("Me preguntaste por nuestro producto estrella, el horario de atención y si hacemos delivery.")
    D.say("¡Lo recuerda todo! Porque cada mensaje quedó guardado en PostgreSQL.", esperar=True)
    D.preguntar("Tú: ", BLANCO, "salir")
    D.fin_comando()
    D.say("Si quieres comprobarlo, podemos ver la tabla chat_history directamente en la base de datos.")
    D.comando("docker compose exec postgres psql -U luna -d asistente -c \"SELECT message->>'type' AS tipo, left(message->'data'->>'content', 40) AS texto FROM chat_history LIMIT 4;\"", cps=30)
    D.salida(" tipo  |                  texto\n"
             "-------+------------------------------------------\n"
             " human | ¿Cuál es su producto estrella?\n"
             " ai    | ¡Nuestro producto estrella es el Latte\n"
             " human | ¿Y hasta qué hora atienden?\n"
             " ai    | Atendemos de lunes a sábado de 7:00 a 2\n"
             "(4 rows)", BLANCO, 0.08)
    D.fin_comando()
    D.say("Ahí están: los mensajes del usuario como 'human' y los del asistente como 'ai'.", esperar=True)

    # ---------------------------------------------------------- CIERRE
    D.capitulo("Resumen")
    D.slide(SlideConcepto("RESUMEN", "¡Ya tienes tu asistente!", [
        "Docker: Qdrant + PostgreSQL + Ollama",
        "ingest.py: documentos → vectores → Qdrant",
        "app.py: RAG con GptLuna y LangChain",
        "Memoria por hilo en PostgreSQL",
    ], dib_arquitectura), frases=[
        "Hagamos un resumen. Levantamos Qdrant, PostgreSQL y Ollama con Docker.",
        "Con ingest.py convertimos nuestros documentos en vectores y los guardamos en Qdrant.",
        "Y con app.py creamos un asistente con RAG y memoria, usando GptLuna y LangChain.",
        "Como reto, prueba agregar tus propios documentos a la carpeta docs, vuelve a ejecutar ingest.py, y hazle preguntas.",
    ])
    D.slide(SlideFinal(), frases=[
        "El código completo está en GitHub, el enlace está en la descripción.",
        "Si te sirvió, dale like, suscríbete y déjame en los comentarios tus dudas. En la próxima clase le crearemos una interfaz web. ¡Nos vemos!",
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
         "Si grabas tu voz, puedes quitar los subtítulos incrustados poniendo `SUBTITULOS = False` en `render.py`.", ""]
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


SUBTITULOS = True
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
            if not SUBTITULOS:
                s = copy.copy(s)
                s.subtitulo = ""
            datos = render(s, blink).tobytes()
            clave_ant = clave
        ff.stdin.write(datos)
    ff.stdin.close()
    ff.wait()
    return idx


def main():
    global FRAMES
    D = guion()
    FRAMES = D.frames
    total = len(FRAMES) / FPS
    escribir_textos(D)
    print(f"Duración: {fmt_min(total)} ({len(FRAMES)} fotogramas)")
    if "--preview" in sys.argv:
        out = AQUI / "preview"
        out.mkdir(exist_ok=True)
        paso = int(sys.argv[sys.argv.index("--preview") + 1]) if len(sys.argv) > 2 else 20
        for k, f in enumerate(range(0, len(FRAMES), paso * FPS)):
            render(FRAMES[f], True).save(out / f"f_{k:03}.png")
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
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lista),
                    "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest",
                    "-movflags", "+faststart", str(AQUI / "tutorial.mp4")], check=True)
    for t in trabajos:
        t[3].unlink()
    lista.unlink()
    tmp.rmdir()
    print("Video:", AQUI / "tutorial.mp4")


if __name__ == "__main__":
    main()
