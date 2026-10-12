"""
Genera el video tutorial "Crea tu propio Asistente IA" (1920x1080, 30 fps).

Uso:
    pip install pillow pygments
    python render.py            # crea tutorial.mp4, subtitulos.srt y guion.md

Requiere ffmpeg en el PATH. El código que aparece en el video se lee
directamente de ../codigo, así el video y el proyecto siempre coinciden.
"""
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pygments import lex
from pygments.lexers import get_lexer_for_filename, TextLexer
from pygments.token import Token

AQUI = Path(__file__).parent
CODIGO = AQUI.parent / "codigo"
W, H, FPS = 1920, 1080, 30
PREVIEW = "--preview" in sys.argv  # renderiza un fotograma por escena en PNG

# ---------------------------------------------------------------- estilo
BG = (13, 17, 28)
PANEL = (22, 27, 41)
PANEL_HEAD = (30, 36, 54)
TEXT = (230, 234, 242)
MUTED = (140, 150, 172)
ACCENT = (138, 180, 255)   # azul "luna"
ACCENT2 = (255, 196, 92)   # dorado
GREEN = (126, 211, 140)
RED = (255, 120, 120)

F = "/usr/share/fonts/opentype/inter/"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def font(name, size):
    return ImageFont.truetype(name, size)


f_title = font(F + "InterDisplay-Bold.otf", 96)
f_h1 = font(F + "InterDisplay-Bold.otf", 64)
f_h2 = font(F + "Inter-SemiBold.otf", 40)
f_body = font(F + "Inter-Medium.otf", 40)
f_small = font(F + "Inter-Medium.otf", 28)
f_sub = font(F + "Inter-Medium.otf", 36)
f_code = font(MONO, 27)
f_code_b = font(MONO_B, 27)
f_box = font(F + "Inter-SemiBold.otf", 30)
f_box_s = font(F + "Inter-Regular.otf", 22)

CW = f_code.getlength("M")  # ancho de un carácter monoespaciado
LH = 39                     # alto de línea de código

# Colores de sintaxis (estilo One Dark)
SYNTAX = [
    (Token.Comment, (110, 120, 140)),
    (Token.Keyword, (198, 120, 221)),
    (Token.Name.Builtin, (229, 192, 123)),
    (Token.Name.Function, (97, 175, 239)),
    (Token.Name.Class, (229, 192, 123)),
    (Token.Name.Namespace, (229, 192, 123)),
    (Token.Name.Tag, (224, 108, 117)),
    (Token.Literal.String, (152, 195, 121)),
    (Token.Literal.Number, (209, 154, 102)),
    (Token.Name.Attribute, (224, 108, 117)),
    (Token.Name.Variable, (224, 108, 117)),
    (Token.Operator, (86, 182, 194)),
    (Token.Literal, (209, 154, 102)),
]


def color_de(tok):
    for t, c in SYNTAX:
        if tok in t:
            return c
    return (220, 223, 228)


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def mezclar(c1, c2, a):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * a) for i in range(3))


# ---------------------------------------------------------------- base
def fondo():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # Una "luna" decorativa arriba a la derecha
    d.ellipse((W - 260, -120, W + 120, 260), fill=(20, 26, 42))
    d.ellipse((W - 330, -150, W + 30, 210), fill=BG)
    return img, d


def cabecera(d, paso):
    d.text((60, 36), paso, font=f_small, fill=ACCENT)
    txt = "Asistente IA  ·  GptLuna + LangChain"
    d.text((W - 60 - f_small.getlength(txt), 36), txt, font=f_small, fill=MUTED)


def envolver(texto, fnt, ancho):
    palabras, lineas, actual = texto.split(), [], ""
    for p in palabras:
        prueba = (actual + " " + p).strip()
        if fnt.getlength(prueba) <= ancho:
            actual = prueba
        else:
            lineas.append(actual)
            actual = p
    if actual:
        lineas.append(actual)
    return lineas


def subtitulo(img, texto):
    if not texto:
        return
    lineas = envolver(texto, f_sub, 1600)
    alto = 30 + len(lineas) * 48
    y0 = H - 40 - alto
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dc = ImageDraw.Draw(capa)
    ancho = max(f_sub.getlength(l) for l in lineas) + 70
    x0 = (W - ancho) / 2
    dc.rounded_rectangle((x0, y0, x0 + ancho, y0 + alto), 18, fill=(0, 0, 0, 200))
    for i, l in enumerate(lineas):
        dc.text((W / 2 - f_sub.getlength(l) / 2, y0 + 14 + i * 48), l,
                font=f_sub, fill=(255, 255, 255, 255))
    img.paste(capa, (0, 0), capa)


def ventana(d, caja, titulo, terminal=False):
    x0, y0, x1, y1 = caja
    d.rounded_rectangle(caja, 16, fill=PANEL if not terminal else (10, 12, 18))
    d.rounded_rectangle((x0, y0, x1, y0 + 52), 16, fill=PANEL_HEAD)
    d.rectangle((x0, y0 + 36, x1, y0 + 52), fill=PANEL_HEAD)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse((x0 + 24 + i * 30, y0 + 18, x0 + 40 + i * 30, y0 + 34), fill=c)
    d.text((x0 + 140, y0 + 12), titulo, font=f_small, fill=MUTED)


# ---------------------------------------------------------------- escenas
class Escena:
    paso = ""
    narracion = []  # lista de frases (se reparten en el tiempo de la escena)

    def duracion(self):
        raise NotImplementedError

    def dibujar(self, t):
        raise NotImplementedError

    def frase(self, t):
        if not self.narracion:
            return ""
        i = min(int(t / self.duracion() * len(self.narracion)), len(self.narracion) - 1)
        return self.narracion[i]

    def frame(self, t):
        img = self.dibujar(t)
        subtitulo(img, self.frase(t))
        return img


class Titulo(Escena):
    def __init__(self, narracion, dur=8):
        self.narracion, self.dur = narracion, dur

    def duracion(self):
        return self.dur

    def dibujar(self, t):
        img, d = fondo()
        a = ease(t / 1.2)
        y = 300 + (1 - a) * 40
        d.text((W / 2, y), "Crea tu propio", font=f_h1, fill=mezclar(BG, MUTED, a), anchor="mm")
        d.text((W / 2, y + 110), "Asistente de IA en Python", font=f_title,
               fill=mezclar(BG, TEXT, a), anchor="mm")
        b = ease((t - 1.0) / 1.0)
        chips = ["GptLuna", "LangChain", "Qdrant", "Ollama", "PostgreSQL"]
        colores = [ACCENT2, GREEN, RED, TEXT, ACCENT]
        anchos = [f_h2.getlength(c) + 60 for c in chips]
        x = W / 2 - (sum(anchos) + 24 * (len(chips) - 1)) / 2
        for c, col, an in zip(chips, colores, anchos):
            d.rounded_rectangle((x, 520, x + an, 590), 35,
                                outline=mezclar(BG, col, b), width=3)
            d.text((x + an / 2, 555), c, font=f_h2, fill=mezclar(BG, col, b), anchor="mm")
            x += an + 24
        c = ease((t - 2.0) / 1.0)
        d.text((W / 2, 680), "RAG  +  memoria de conversación  ·  paso a paso",
               font=f_body, fill=mezclar(BG, MUTED, c), anchor="mm")
        return img


class Lista(Escena):
    def __init__(self, paso, titulo, items, narracion, dur):
        self.paso, self.titulo, self.items = paso, titulo, items
        self.narracion, self.dur = narracion, dur

    def duracion(self):
        return self.dur

    def dibujar(self, t):
        img, d = fondo()
        cabecera(d, self.paso)
        d.text((140, 150), self.titulo, font=f_h1, fill=TEXT)
        d.rectangle((140, 240, 260, 246), fill=ACCENT)
        paso_t = min(1.2, (self.dur - 3) / max(1, len(self.items)))
        for i, (txt, col) in enumerate(self.items):
            a = ease((t - 0.6 - i * paso_t) / 0.5)
            if a <= 0:
                continue
            y = 300 + i * 88
            x = 160 + (1 - a) * 30
            d.ellipse((x, y + 14, x + 20, y + 34), fill=mezclar(BG, col, a))
            d.text((x + 50, y), txt, font=f_body, fill=mezclar(BG, TEXT, a))
        return img


class Diagrama(Escena):
    paso = "Arquitectura"

    def __init__(self, narracion, dur):
        self.narracion, self.dur = narracion, dur
        # nombre: (x, y, título, subtítulo, color)
        self.nodos = {
            "docs": (260, 330, "Documentos", "docs/*.txt", MUTED),
            "ingest": (260, 560, "ingest.py", "carga y divide", TEXT),
            "ollama": (760, 560, "Ollama", "nomic-embed-text", TEXT),
            "qdrant": (1260, 560, "Qdrant", "base vectorial", RED),
            "user": (260, 790, "Usuario", "chat en consola", ACCENT2),
            "app": (760, 790, "app.py", "LangChain", GREEN),
            "pg": (1260, 790, "PostgreSQL", "memoria del hilo", ACCENT),
            "luna": (1660, 790, "GptLuna", "LLM", ACCENT2),
        }
        # (desde, hasta, etiqueta, momento de aparición en segundos)
        self.flechas = [
            ("docs", "ingest", "", 1.0),
            ("ingest", "ollama", "texto", 2.0),
            ("ollama", "qdrant", "vectores", 3.0),
            ("user", "app", "pregunta", 7.0),
            ("app", "qdrant", "busca contexto", 8.5),
            ("app", "pg", "historial", 10.0),
        ]
        self.aparicion = {"docs": 0.3, "ingest": 0.8, "ollama": 1.8, "qdrant": 2.8,
                          "user": 6.5, "app": 6.8, "pg": 9.8, "luna": 12.3}

    def duracion(self):
        return self.dur

    def flecha(self, d, p0, p1, col, etiqueta, a):
        (cx0, cy0), (cx1, cy1) = p0, p1
        dx, dy = cx1 - cx0, cy1 - cy0
        largo = math.hypot(dx, dy)
        ux, uy = dx / largo, dy / largo
        # distancia del centro al borde de la caja (220x112) en esa dirección, + margen
        borde = min(118 / abs(ux) if ux else 1e9, 64 / abs(uy) if uy else 1e9)
        x0, y0 = cx0 + ux * borde, cy0 + uy * borde
        x1, y1 = cx1 - ux * borde, cy1 - uy * borde
        xe, ye = x0 + (x1 - x0) * a, y0 + (y1 - y0) * a
        d.line((x0, y0, xe, ye), fill=col, width=5)
        if a > 0.95:
            s, ang = 18, math.atan2(dy, dx)
            d.polygon([(x1, y1),
                       (x1 - s * math.cos(ang - 0.45), y1 - s * math.sin(ang - 0.45)),
                       (x1 - s * math.cos(ang + 0.45), y1 - s * math.sin(ang + 0.45))], fill=col)
            if etiqueta:
                mx, my = (x0 + x1) / 2, (y0 + y1) / 2
                # etiqueta desplazada en perpendicular a la flecha
                px, py = uy, -ux
                if py > 0 or (py == 0 and px < 0):
                    px, py = -px, -py
                ancla = "mm" if abs(px) < 0.3 else ("rm" if px < 0 else "lm")
                d.text((mx + px * 30, my + py * 30), etiqueta, font=f_box_s, fill=MUTED,
                       anchor=ancla)

    def dibujar(self, t):
        img, d = fondo()
        cabecera(d, self.paso)
        d.text((140, 130), "¿Cómo funciona?", font=f_h1, fill=TEXT)
        a1 = ease((t - 0.2) / 0.6)
        d.text((80, 455), "1 · INGESTA", font=f_small, fill=mezclar(BG, ACCENT2, a1))
        a2 = ease((t - 6.3) / 0.6)
        d.text((80, 685), "2 · CHAT", font=f_small, fill=mezclar(BG, ACCENT2, a2))
        for desde, hasta, et, t0 in self.flechas:
            a = ease((t - t0) / 0.7)
            if a > 0:
                n0, n1 = self.nodos[desde], self.nodos[hasta]
                self.flecha(d, n0[:2], n1[:2], mezclar(BG, (90, 104, 135), 1), et, a)
        # app -> luna: curva por debajo (prompt + contexto + historial)
        a = ease((t - 13.0) / 0.8)
        if a > 0:
            col = (90, 104, 135)
            pts = [(760, 852), (760, 930), (1660, 930), (1660, 852)]
            largo = [80, 900, 78]
            total = sum(largo) * a
            for (p, q), L in zip(zip(pts, pts[1:]), largo):
                if total <= 0:
                    break
                f = min(1, total / L)
                d.line((p[0], p[1], p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f),
                       fill=col, width=5)
                total -= L
            if a > 0.95:
                d.polygon([(1660, 852), (1648, 872), (1672, 872)], fill=col)
                d.text((1210, 905), "prompt = contexto + historial + pregunta",
                       font=f_box_s, fill=MUTED, anchor="mm")
        for k, (x, y, tit, sub, col) in self.nodos.items():
            a = ease((t - self.aparicion[k]) / 0.5)
            if a <= 0:
                continue
            w, h = 220, 112
            d.rounded_rectangle((x - w / 2, y - h / 2, x + w / 2, y + h / 2), 18,
                                fill=mezclar(BG, PANEL_HEAD, a), outline=mezclar(BG, col, a), width=3)
            d.text((x, y - 16), tit, font=f_box, fill=mezclar(BG, TEXT, a), anchor="mm")
            d.text((x, y + 22), sub, font=f_box_s, fill=mezclar(BG, MUTED, a), anchor="mm")
        return img


def tokens_coloreados(nombre, texto):
    try:
        lexer = get_lexer_for_filename(nombre, stripnl=False)
    except Exception:
        lexer = TextLexer(stripnl=False)
    if nombre.endswith(".env") or nombre.startswith(".env"):
        lexer = get_lexer_for_filename("x.ini", stripnl=False)
    chars = []
    for tok, val in lex(texto, lexer):
        for ch in val:
            chars.append((ch, color_de(tok)))
    if chars and chars[-1][0] == "\n" and not texto.endswith("\n"):
        chars.pop()
    return chars


class Codigo(Escena):
    """Muestra un archivo y 'teclea' los caracteres entre desde..hasta."""

    def __init__(self, paso, archivo, narracion, desde=0, hasta=None, cps=55,
                 espera=3.0, texto=None, titulo=None):
        self.paso, self.narracion = paso, narracion
        self.nombre = titulo or archivo
        texto = texto if texto is not None else (CODIGO / archivo).read_text(encoding="utf-8")
        self.chars = tokens_coloreados(Path(archivo).name, texto)
        self.desde = desde
        self.hasta = len(self.chars) if hasta is None else hasta
        self.cps, self.espera = cps, espera
        self.t_tecleo = (self.hasta - self.desde) / cps
        self.cache_key, self.cache_img = None, None

    def duracion(self):
        return 0.8 + self.t_tecleo + self.espera

    def dibujar(self, t):
        n = self.desde + int(max(0, t - 0.8) * self.cps)
        n = min(n, self.hasta)
        cursor = (int(t * 2) % 2 == 0) or n < self.hasta
        key = (n, cursor)
        if key == self.cache_key:
            return self.cache_img.copy()
        img, d = fondo()
        cabecera(d, self.paso)
        caja = (80, 100, W - 80, H - 170)
        ventana(d, caja, self.nombre)
        visibles = (caja[3] - caja[1] - 80) // LH
        # convertir a líneas
        lineas, actual = [], []
        for ch, col in self.chars[:n]:
            if ch == "\n":
                lineas.append(actual)
                actual = []
            else:
                actual.append((ch, col))
        lineas.append(actual)
        total_lineas = sum(1 for ch, _ in self.chars[:self.hasta] if ch == "\n") + 1
        actual_idx = len(lineas) - 1
        primera = max(0, min(actual_idx - visibles + 3, total_lineas - visibles))
        x0, y0 = caja[0] + 90, caja[1] + 72
        for i in range(primera, min(len(lineas), primera + visibles)):
            y = y0 + (i - primera) * LH
            d.text((caja[0] + 70, y), str(i + 1), font=f_code, fill=(75, 84, 105), anchor="ra")
            # agrupar caracteres seguidos del mismo color
            x, buf, col_buf = x0, "", None
            for ch, col in lineas[i]:
                if col != col_buf and buf:
                    d.text((x, y), buf, font=f_code, fill=col_buf)
                    x += CW * len(buf)
                    buf = ""
                buf += ch
                col_buf = col
            if buf:
                d.text((x, y), buf, font=f_code, fill=col_buf)
        if cursor:
            cy = y0 + (actual_idx - primera) * LH
            cx = x0 + CW * len(lineas[-1])
            d.rectangle((cx, cy + 2, cx + 3, cy + LH - 6), fill=ACCENT)
        self.cache_key, self.cache_img = key, img
        return img.copy()


class Terminal(Escena):
    """Pasos: ("cmd", texto) se teclea; ("out", texto[, color]) aparece; ("in", texto) es
    entrada del usuario tras un prompt ya impreso; ("wait", seg)."""

    PROMPT = "~/asistente $ "

    def __init__(self, paso, titulo, pasos, narracion, cps=22, espera=3.0):
        self.paso, self.titulo, self.narracion = paso, titulo, narracion
        self.cps, self.espera = cps, espera
        self.eventos = []  # (t_inicio, t_fin, tipo, texto, color)
        t = 0.8
        for p in pasos:
            tipo = p[0]
            if tipo == "wait":
                t += p[1]
                continue
            texto = p[1]
            col = p[2] if len(p) > 2 else TEXT
            if tipo in ("cmd", "in"):
                dur = len(texto) / cps
                self.eventos.append((t, t + dur, tipo, texto, col))
                t += dur + 0.6
            elif tipo == "stream":  # respuesta del asistente que va apareciendo
                dur = len(texto) / 45
                self.eventos.append((t, t + dur, tipo, texto, col))
                t += dur + 0.5
            else:
                self.eventos.append((t, t, tipo, texto, col))
                t += 0.25
        self.total = t + espera
        self.cache_key, self.cache_img = None, None

    def duracion(self):
        return self.total

    def dibujar(self, t):
        estado = []
        for t0, t1, tipo, texto, col in self.eventos:
            if t < t0:
                break
            if tipo in ("cmd", "in", "stream"):
                k = len(texto) if t >= t1 else int((t - t0) / (t1 - t0) * len(texto))
                estado.append((tipo, texto[:k], col, t < t1))
            else:
                estado.append((tipo, texto, col, False))
        escribiendo = any(e[3] for e in estado)
        cursor = escribiendo or int(t * 2) % 2 == 0
        key = (tuple((e[0], len(e[1])) for e in estado), cursor)
        if key == self.cache_key:
            return self.cache_img.copy()
        img, d = fondo()
        cabecera(d, self.paso)
        caja = (80, 100, W - 80, H - 170)
        ventana(d, caja, self.titulo, terminal=True)
        # construir líneas visuales
        lineas = []  # lista de lista de (texto, color)
        for tipo, texto, col, _ in estado:
            if tipo == "cmd":
                lineas.append([(self.PROMPT, GREEN), (texto, TEXT)])
            elif tipo == "in":
                # continúa la última línea (prompt de input ya impreso)
                if lineas:
                    lineas[-1] = lineas[-1] + [(texto, TEXT)]
                else:
                    lineas.append([(texto, TEXT)])
            elif tipo == "prompt":
                lineas.append([(texto, col)])
            else:
                for i, parte in enumerate(texto.split("\n")):
                    lineas.append([(parte, col)])
        # ajustar líneas largas
        max_chars = int((caja[2] - caja[0] - 80) / CW)
        visuales = []
        for segs in lineas:
            fila, largo = [], 0
            for txt, col in segs:
                while largo + len(txt) > max_chars:
                    corte = max_chars - largo
                    fila.append((txt[:corte], col))
                    visuales.append(fila)
                    fila, largo, txt = [], 0, txt[corte:]
                fila.append((txt, col))
                largo += len(txt)
            visuales.append(fila)
        visibles = (caja[3] - caja[1] - 80) // LH
        visuales = visuales[-visibles:]
        x0, y0 = caja[0] + 40, caja[1] + 72
        for i, fila in enumerate(visuales):
            x = x0
            for txt, col in fila:
                d.text((x, y0 + i * LH), txt, font=f_code, fill=col)
                x += CW * len(txt)
        if cursor and visuales:
            cx = x0 + CW * sum(len(s) for s, _ in visuales[-1])
            cy = y0 + (len(visuales) - 1) * LH
            d.rectangle((cx, cy + 4, cx + CW - 2, cy + LH - 6), fill=(200, 200, 200))
        self.cache_key, self.cache_img = key, img
        return img.copy()


class Final(Escena):
    def __init__(self, narracion, dur):
        self.narracion, self.dur = narracion, dur

    def duracion(self):
        return self.dur

    def dibujar(self, t):
        img, d = fondo()
        a = ease(t / 1.0)
        d.text((W / 2, 280), "¡Gracias por ver!", font=f_title, fill=mezclar(BG, TEXT, a), anchor="mm")
        d.text((W / 2, 400), "Código completo en GitHub", font=f_h2, fill=mezclar(BG, MUTED, a), anchor="mm")
        d.text((W / 2, 460), "github.com/paulantezana/tutoriales", font=f_h2,
               fill=mezclar(BG, ACCENT, a), anchor="mm")
        b = ease((t - 1.5) / 0.8)
        botones = [("Me gusta", ACCENT), ("Suscríbete", RED), ("Comenta", ACCENT2)]
        x = W / 2 - (3 * 300 + 2 * 40) / 2
        for txt, col in botones:
            y = 600 + (1 - b) * 30
            d.rounded_rectangle((x, y, x + 300, y + 90), 45, fill=mezclar(BG, col, b))
            d.text((x + 150, y + 45), txt, font=f_h2, fill=mezclar(BG, BG, b), anchor="mm")
            x += 340
        return img


# ---------------------------------------------------------------- guion
def indice(archivo, marcador):
    """Posición (en caracteres) de un marcador dentro del archivo."""
    texto = (CODIGO / archivo).read_text(encoding="utf-8")
    return texto.index(marcador)


APP = "app.py"
i_llm = indice(APP, "# --- LLM")
i_ret = indice(APP, "# --- Retriever")
i_mem = indice(APP, "# --- Memoria")
i_cad = indice(APP, "# --- Prompt")
i_chat = indice(APP, "# --- Chat")
ID = "7f3c2a10-5b8e-4d21-9a6f-0c1e2b3d4f5a"

ESCENAS = [
    Titulo([
        "Hola a todos. Hoy vamos a crear nuestro propio asistente de inteligencia artificial en Python.",
        "Usaremos GptLuna, LangChain, Qdrant, Ollama y PostgreSQL.",
    ], dur=9),
    Lista("Introducción", "¿Qué vamos a construir?", [
        ("Un chat que responde con TUS documentos (RAG)", TEXT),
        ("GptLuna como modelo de lenguaje (LLM)", ACCENT2),
        ("Ollama para generar los embeddings", TEXT),
        ("Qdrant como base de datos vectorial", RED),
        ("PostgreSQL para la memoria de cada hilo de chat", ACCENT),
        ("LangChain para unir todas las piezas", GREEN),
    ], [
        "Vamos a construir un chat que responde usando nuestros propios documentos. A esto se le llama RAG.",
        "GptLuna será el cerebro, Ollama generará los embeddings y Qdrant guardará los vectores.",
        "PostgreSQL recordará cada conversación, y LangChain unirá todas las piezas.",
    ], dur=15),
    Diagrama([
        "Primero, ingest.py lee los documentos y los divide en fragmentos.",
        "Ollama convierte cada fragmento en un vector, y los guardamos en Qdrant.",
        "Luego, cuando el usuario pregunta, app.py busca el contexto más parecido en Qdrant...",
        "...y lee el historial del hilo desde PostgreSQL.",
        "Con todo eso arma el prompt y se lo envía a GptLuna, que genera la respuesta.",
    ], dur=19),
    Lista("Requisitos", "Antes de empezar", [
        ("Python 3.10 o superior", TEXT),
        ("Docker y Docker Compose", TEXT),
        ("Una API key de GptLuna", ACCENT2),
        ("Tu editor favorito (VS Code, PyCharm...)", TEXT),
    ], [
        "Solo necesitas Python 3.10 o superior, Docker y una API key de GptLuna.",
    ], dur=8),
    Codigo("Paso 1 · Servicios con Docker", "docker-compose.yml", [
        "Paso uno: levantamos los servicios con Docker. Creamos el archivo docker-compose.yml.",
        "Qdrant, nuestra base de datos vectorial, en el puerto 6333.",
        "PostgreSQL en el puerto 5432, con usuario, contraseña y la base de datos 'asistente'.",
        "Y Ollama en el puerto 11434. Cada servicio tiene su volumen para no perder los datos.",
    ], cps=40),
    Terminal("Paso 1 · Servicios con Docker", "Terminal", [
        ("cmd", "docker compose up -d"),
        ("out", " ✔ Container asistente-qdrant-1    Started", GREEN),
        ("out", " ✔ Container asistente-postgres-1  Started", GREEN),
        ("out", " ✔ Container asistente-ollama-1    Started", GREEN),
        ("wait", 1.0),
        ("cmd", "docker compose exec ollama ollama pull nomic-embed-text"),
        ("out", "pulling manifest", MUTED),
        ("wait", 0.6),
        ("out", "pulling 970aa74c0a90... 100% ▕██████████████████▏ 274 MB", MUTED),
        ("out", "verifying sha256 digest", MUTED),
        ("out", "success", GREEN),
    ], [
        "Levantamos todo con docker compose up -d.",
        "Y descargamos el modelo de embeddings nomic-embed-text dentro de Ollama.",
    ]),
    Codigo("Paso 2 · Entorno de Python", "requirements.txt", [
        "Paso dos: preparamos Python. Estas son las librerías que vamos a usar.",
        "Las integraciones de LangChain para OpenAI, Ollama, Qdrant y Postgres, más psycopg y python-dotenv.",
    ], cps=25),
    Terminal("Paso 2 · Entorno de Python", "Terminal", [
        ("cmd", "python -m venv .venv"),
        ("cmd", "source .venv/bin/activate"),
        ("cmd", "pip install -r requirements.txt"),
        ("wait", 0.8),
        ("out", "Collecting langchain ...", MUTED),
        ("out", "Collecting langchain-openai ...", MUTED),
        ("out", "Collecting langchain-qdrant ...", MUTED),
        ("wait", 0.8),
        ("out", "Successfully installed langchain langchain-ollama langchain-openai\n"
                "langchain-postgres langchain-qdrant psycopg python-dotenv ...", GREEN),
    ], [
        "Creamos un entorno virtual, lo activamos e instalamos las dependencias.",
    ]),
    Codigo("Paso 2 · Configuración", ".env.example", [
        "Ahora creamos el archivo .env con la configuración.",
        "GptLuna expone una API compatible con OpenAI: solo necesitamos la URL base, la API key y el modelo.",
        "Revisa en el panel de GptLuna la URL y el nombre del modelo exactos de tu cuenta.",
        "También las URLs de Ollama, Qdrant y PostgreSQL que levantamos con Docker.",
    ], cps=40, titulo=".env"),
    Codigo("Paso 3 · Nuestros documentos", "docs/empresa.txt", [
        "Como ejemplo, usaremos un documento sobre una cafetería ficticia: Luna Café.",
        "Aquí puedes poner tus propios archivos: manuales, preguntas frecuentes, políticas...",
    ], cps=45),
    Codigo("Paso 3 · Ingesta de documentos", "ingest.py", [
        "Paso tres: el script de ingesta, ingest.py.",
        "Leemos todos los archivos .txt de la carpeta docs y los convertimos en documentos de LangChain.",
        "Los dividimos en fragmentos de 500 caracteres, con un pequeño solapamiento.",
        "Creamos el generador de embeddings con Ollama, usando el modelo nomic-embed-text.",
        "Y con from_documents guardamos todos los fragmentos en una colección de Qdrant.",
    ], cps=50),
    Terminal("Paso 3 · Ingesta de documentos", "Terminal", [
        ("cmd", "python ingest.py"),
        ("wait", 1.2),
        ("out", "Listo: 1 fragmentos guardados en Qdrant", GREEN),
        ("wait", 0.8),
        ("out", "\n# Puedes verlos en el panel: http://localhost:6333/dashboard", MUTED),
    ], [
        "Lo ejecutamos... y nuestros documentos ya están en Qdrant.",
        "Puedes revisarlos en el panel web de Qdrant, en localhost:6333/dashboard.",
    ]),
    Codigo("Paso 4 · El asistente", APP, [
        "Paso cuatro: el asistente, app.py. Primero importamos LangChain y sus integraciones.",
    ], desde=0, hasta=i_llm, cps=70, espera=1.5),
    Codigo("Paso 4 · El LLM: GptLuna", APP, [
        "Configuramos GptLuna con ChatOpenAI. El truco está en cambiar la base_url.",
        "Así funciona con cualquier API compatible con OpenAI. Una temperatura baja da respuestas más precisas.",
    ], desde=i_llm, hasta=i_ret, cps=40),
    Codigo("Paso 4 · Búsqueda en Qdrant", APP, [
        "Nos conectamos a la colección que ya existe en Qdrant, con los mismos embeddings de Ollama.",
        "El retriever devolverá los 3 fragmentos más parecidos a cada pregunta.",
    ], desde=i_ret, hasta=i_mem, cps=45),
    Codigo("Paso 4 · Memoria en PostgreSQL", APP, [
        "Ahora la memoria. Nos conectamos a PostgreSQL y creamos la tabla chat_history.",
        "La función obtener_historial devuelve los mensajes de un hilo según su session_id.",
    ], desde=i_mem, hasta=i_cad, cps=40),
    Codigo("Paso 4 · Prompt y cadena RAG", APP, [
        "El prompt tiene tres partes: las instrucciones con el contexto, el historial y la pregunta.",
        "buscar_contexto consulta Qdrant y une el texto de los fragmentos encontrados.",
        "La cadena: agrega el contexto, arma el prompt, llama a GptLuna y devuelve texto.",
        "RunnableWithMessageHistory lee y guarda automáticamente cada mensaje en PostgreSQL.",
    ], desde=i_cad, hasta=i_chat, cps=45),
    Codigo("Paso 4 · Chat en consola", APP, [
        "Por último, un bucle de chat. Si no escribimos un ID de hilo, se crea uno nuevo.",
        "Cada pregunta se envía con su session_id, así cada hilo tiene su propia memoria.",
    ], desde=i_chat, cps=50),
    Terminal("Paso 5 · ¡A probar!", "Terminal — python app.py", [
        ("cmd", "python app.py"),
        ("wait", 0.8),
        ("prompt", "ID de hilo (Enter = nuevo): ", TEXT),
        ("wait", 0.6),
        ("out", f"Hilo: {ID}  (escribe 'salir' para terminar)\n", MUTED),
        ("prompt", "Tú: ", ACCENT2),
        ("in", "¿Cuál es su producto estrella?"),
        ("wait", 1.2),
        ("stream", "Asistente: ¡Nuestro producto estrella es el Latte de Lúcuma! "
                   "Te lo recomiendo mucho.\n", ACCENT),
        ("prompt", "Tú: ", ACCENT2),
        ("in", "¿Y hasta qué hora atienden?"),
        ("wait", 1.2),
        ("stream", "Asistente: Atendemos de lunes a sábado de 7:00 a 21:00. "
                   "Los domingos estamos cerrados.\n", ACCENT),
        ("prompt", "Tú: ", ACCENT2),
        ("in", "¿Hacen delivery?"),
        ("wait", 1.0),
        ("stream", "Asistente: ¡Sí! El delivery es gratis en pedidos mayores a 30 soles.\n", ACCENT),
        ("prompt", "Tú: ", ACCENT2),
        ("in", "salir"),
    ], [
        "¡Ahora sí, a probar! Ejecutamos python app.py y dejamos que cree un hilo nuevo.",
        "Preguntamos por el producto estrella: responde con la información de nuestro documento.",
        "Las preguntas de seguimiento funcionan porque, en cada mensaje, el asistente recibe el historial del hilo.",
        "Y toda la información sale de Qdrant, no de lo que el modelo 'cree' saber.",
    ], espera=2.5),
    Terminal("Paso 5 · Memoria persistente", "Terminal — python app.py", [
        ("cmd", "python app.py"),
        ("wait", 0.6),
        ("prompt", "ID de hilo (Enter = nuevo): ", TEXT),
        ("in", ID),
        ("out", f"Hilo: {ID}  (escribe 'salir' para terminar)\n", MUTED),
        ("prompt", "Tú: ", ACCENT2),
        ("in", "¿Qué te pregunté antes?"),
        ("wait", 1.2),
        ("stream", "Asistente: Me preguntaste por nuestro producto estrella, el horario de "
                   "atención y si hacemos delivery.\n", ACCENT),
        ("prompt", "Tú: ", ACCENT2),
        ("in", "salir"),
        ("wait", 0.8),
        ("cmd", "docker compose exec postgres psql -U luna -d asistente -c \"SELECT message->>'type' AS tipo, left(message->'data'->>'content', 40) AS texto FROM chat_history LIMIT 4;\""),
        ("wait", 0.6),
        ("out", " tipo  |                  texto\n"
                "-------+------------------------------------------\n"
                " human | ¿Cuál es su producto estrella?\n"
                " ai    | ¡Nuestro producto estrella es el Latte\n"
                " human | ¿Y hasta qué hora atienden?\n"
                " ai    | Atendemos de lunes a sábado de 7:00 a 2\n"
                "(4 rows)", TEXT),
    ], [
        "Si cerramos el programa y lo abrimos con el mismo ID de hilo...",
        "...el asistente recuerda toda la conversación, porque está guardada en PostgreSQL.",
        "Podemos comprobarlo consultando directamente la tabla chat_history.",
    ], cps=30, espera=3.5),
    Lista("Resumen", "¡Listo! Ya tienes tu asistente", [
        ("Docker: Qdrant + PostgreSQL + Ollama", TEXT),
        ("ingest.py: documentos → embeddings → Qdrant", TEXT),
        ("app.py: RAG con GptLuna y LangChain", GREEN),
        ("Memoria por hilo guardada en PostgreSQL", ACCENT),
        ("Siguiente: PDFs, interfaz web con Streamlit o FastAPI, streaming", ACCENT2),
    ], [
        "¡Y listo! Ya tienes un asistente con RAG y memoria persistente, todo en menos de 100 líneas.",
        "Como siguiente paso puedes cargar PDFs, crear una interfaz web con Streamlit o FastAPI, o mostrar las respuestas en streaming.",
    ], dur=14),
    Final([
        "Si te sirvió, dale like, suscríbete y déjame en los comentarios qué quieres que construyamos después. ¡Nos vemos!",
    ], dur=8),
]


# ---------------------------------------------------------------- render
def fmt_srt(s):
    ms = int(round(s * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    sec, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{sec:02},{ms:03}"


def fmt_min(s):
    return f"{int(s // 60)}:{int(s % 60):02}"


def escribir_textos():
    srt, guion, capitulos = [], [], []
    t, n = 0.0, 1
    guion.append("# Guion de narración\n\nLee cada frase en voz alta mientras se ve la escena. "
                 "Los tiempos coinciden con `tutorial.mp4`.\n")
    for e in ESCENAS:
        dur = e.duracion()
        titulo = e.paso or "Introducción"
        if not capitulos or capitulos[-1][1] != titulo:
            capitulos.append((t, titulo))
        guion.append(f"\n## {fmt_min(t)} · {titulo}\n")
        partes = len(e.narracion)
        for i, frase in enumerate(e.narracion):
            a, b = t + dur * i / partes, t + dur * (i + 1) / partes
            srt.append(f"{n}\n{fmt_srt(a)} --> {fmt_srt(b)}\n{frase}\n")
            guion.append(f"- **{fmt_min(a)}** — {frase}")
            n += 1
        t += dur
    (AQUI / "subtitulos.srt").write_text("\n".join(srt), encoding="utf-8")
    capitulos[0] = (0.0, "Introducción")
    guion.append("\n## Capítulos para la descripción de YouTube\n\n```")
    guion += [f"{fmt_min(a)} {tit}" for a, tit in capitulos]
    guion.append("```\n")
    (AQUI / "guion.md").write_text("\n".join(guion), encoding="utf-8")
    return t


def main():
    total = escribir_textos()
    print(f"Duración total: {fmt_min(total)} ({total:.1f} s)")
    if PREVIEW:
        out = AQUI / "preview"
        out.mkdir(exist_ok=True)
        for i, e in enumerate(ESCENAS):
            e.frame(e.duracion() - 0.5).save(out / f"escena_{i:02}.png")
        print("Previews en", out)
        return
    salida = AQUI / "tutorial.mp4"
    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
        "-shortest", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-tune", "stillimage", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart", str(salida),
    ], stdin=subprocess.PIPE)
    negro = Image.new("RGB", (W, H), (0, 0, 0))
    fundido = 0.35
    for idx, e in enumerate(ESCENAS):
        dur = e.duracion()
        nf = int(round(dur * FPS))
        for f in range(nf):
            t = f / FPS
            img = e.frame(t)
            a = min(1.0, t / fundido, (dur - t) / fundido)
            if a < 1.0:
                img = Image.blend(negro, img, max(0.0, a))
            ff.stdin.write(img.tobytes())
        print(f"  escena {idx + 1}/{len(ESCENAS)} lista ({dur:.1f} s)", flush=True)
    ff.stdin.close()
    ff.wait()
    print("Video:", salida)


if __name__ == "__main__":
    main()
