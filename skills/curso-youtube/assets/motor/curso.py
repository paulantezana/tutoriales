"""Herramientas del curso: código por etapas, escritura línea por línea, la Debug Console
de VS Code y la app (celular o web) según la etapa.

render.py importa este módulo y agrega estos métodos al Director.
"""
import difflib
import json
import sys
from pathlib import Path

AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
import proyecto as CFG    # noqa: E402

CURSO = (AQUI / CFG.CARPETA_ETAPAS).resolve()     # curso/NN-nombre/: el código al final de cada video
PLANTILLA = AQUI / "plantilla"
ARCHIVOS_PLANTILLA = CFG.ARCHIVOS_PLANTILLA


def carpeta_etapa(n):
    return next(CURSO.glob(f"{n:02d}-*"))


def contenido(ruta, etapa):
    """El archivo tal como queda al final del video 'etapa' (0 = el proyecto recién creado).
    None si en esa etapa el archivo no existe.

    CFG.ETAPAS_COMPLETAS = True: cada carpeta curso/NN-*/ trae TODOS los archivos que difieren de la
    plantilla (si un archivo no está, es el de la plantilla o no existe).
    False: cada carpeta trae solo lo que cambió en ese video (si no está, sigue como en el video anterior).
    CFG.QUITAR = {ruta: video} marca en qué video se borra un archivo."""
    if etapa == 0:
        return (PLANTILLA / ARCHIVOS_PLANTILLA[ruta]).read_text(encoding="utf-8") if ruta in ARCHIVOS_PLANTILLA else None
    p = carpeta_etapa(etapa) / ruta
    if p.exists():
        return p.read_text(encoding="utf-8")
    if ruta in CFG.QUITAR and etapa >= CFG.QUITAR[ruta]:
        return None
    if CFG.ETAPAS_COMPLETAS:
        return contenido(ruta, 0)
    return contenido(ruta, etapa - 1)


class Codigo:
    """Un archivo que pasa de cómo estaba ('antes') a cómo queda ('despues') por pasos:
    se agregan líneas nuevas y se borran líneas viejas, y en cada momento se sabe
    exactamente qué texto hay en el editor."""

    def __init__(self, ruta, despues, antes=""):
        self.ruta = ruta
        self.nuevas = despues.split("\n")
        self.viejas = antes.split("\n") if antes else []
        self.presente = [False] * len(self.nuevas)
        self.viva = [False] * len(self.viejas)
        self.ancla = [0] * len(self.viejas)
        if not self.viejas:
            if self.nuevas[-1] == "":
                self.presente[-1] = True      # el salto de línea final ya está
        else:
            # el salto de línea final es el mismo en los dos archivos: no se compara
            final = self.nuevas[-1] == "" and self.viejas[-1] == ""
            nv, vj = (self.nuevas[:-1], self.viejas[:-1]) if final else (self.nuevas, self.viejas)
            if final:
                self.presente[-1] = True
            sm = difflib.SequenceMatcher(a=vj, b=nv, autojunk=False)
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag == "equal":
                    for k in range(j2 - j1):
                        self.presente[j1 + k] = True
                else:
                    for i in range(i1, i2):
                        self.viva[i] = True
                        self.ancla[i] = j1

    # ---------- estado
    def items(self):
        """Las líneas que hay ahora en el editor, en orden: ("n", j) nuevas o ("v", i) viejas."""
        out = []
        for j in range(len(self.nuevas) + 1):
            out += [("v", i) for i in range(len(self.viejas)) if self.viva[i] and self.ancla[i] == j]
            if j < len(self.nuevas) and self.presente[j]:
                out.append(("n", j))
        return out

    def linea(self, it):
        return self.nuevas[it[1]] if it[0] == "n" else self.viejas[it[1]]

    def texto(self):
        return "\n".join(self.linea(it) for it in self.items())

    def completo(self):
        return all(self.presente) and not any(self.viva)

    def pendientes(self):
        return [j for j, p in enumerate(self.presente) if not p]

    # ---------- buscar líneas
    def j(self, texto, desde=0):
        """Índice de la primera línea nueva (desde 'desde') que contiene 'texto'."""
        for k in range(desde, len(self.nuevas)):
            if texto in self.nuevas[k]:
                return k
        raise KeyError(f"{self.ruta}: no encuentro {texto!r}")

    def rango(self, desde, hasta=None, despues_de=0):
        """Líneas nuevas desde la que contiene 'desde' hasta la que contiene 'hasta' (incluidas)."""
        a = self.j(desde, despues_de)
        b = a if hasta is None else self.j(hasta, a)
        return list(range(a, b + 1))

    def _sangria(self, k):
        return len(self.nuevas[k]) - len(self.nuevas[k].lstrip())

    def _cierre(self, a):
        """Dónde abre y dónde termina el bloque que empieza en la línea 'a'.
        Devuelve (k, c, llaves): k = línea que abre ({ ( [ o los dos puntos de Python), c = última línea
        del bloque (la llave que cierra, o la última línea con más sangría), llaves = si hay llave de cierre."""
        k = a
        while True:
            fin = self.nuevas[k].rstrip()
            if fin.endswith(("{", "(", "[")):
                llaves = True
                break
            if fin.endswith(":"):
                llaves = False
                break
            k += 1
        sangria = self._sangria(a)
        if llaves:
            c = next(m for m in range(k + 1, len(self.nuevas))
                     if self.nuevas[m].strip() and self._sangria(m) == sangria)
            return k, c, True
        c = k
        for m in range(k + 1, len(self.nuevas)):
            if not self.nuevas[m].strip():
                continue
            if self._sangria(m) > sangria:
                c = m
            else:
                break
        return k, c, False

    def firma(self, texto, despues_de=0):
        """La firma de una clase o método (hasta la llave o los dos puntos que abren) y, si el lenguaje
        usa llaves, la que lo cierra. Sin el cuerpo: así se escribe primero la estructura."""
        a = self.j(texto, despues_de)
        k, c, llaves = self._cierre(a)
        return list(range(a, k + 1)) + ([c] if llaves else [])

    def cuerpo(self, texto, despues_de=0):
        """Las líneas de adentro de una clase o método."""
        a = self.j(texto, despues_de)
        k, c, llaves = self._cierre(a)
        return list(range(k + 1, c if llaves else c + 1))

    def bloque(self, texto, despues_de=0):
        """Una clase o método completo (firma, cuerpo y cierre)."""
        a = self.j(texto, despues_de)
        _, c, _ = self._cierre(a)
        return list(range(a, c + 1))

    def i(self, texto):
        for k, v in enumerate(self.viejas):
            if texto in v and self.viva[k]:
                return k
        raise KeyError(f"{self.ruta}: no encuentro la línea vieja {texto!r}")

    def viejas_rango(self, desde, hasta=None):
        a = self.i(desde)
        b = a if hasta is None else next(k for k in range(a, len(self.viejas)) if hasta in self.viejas[k])
        return list(range(a, b + 1))

    def viejas_vivas(self):
        return [i for i, v in enumerate(self.viva) if v]

    # ---------- posiciones para insertar y borrar
    def posicion_insertar(self, js):
        """Dónde quedan las líneas js (índice en items) y verifica que queden juntas."""
        js = sorted(js)
        items = self.items()
        for it in items:
            if it[0] == "n" and js[0] < it[1] < js[-1]:
                raise AssertionError(f"{self.ruta}: hay líneas escritas entre {js[0]} y {js[-1]}")
            if it[0] == "v" and js[0] < self.ancla[it[1]] <= js[-1]:
                raise AssertionError(f"{self.ruta}: hay líneas viejas entre {js[0]} y {js[-1]}")
        for p, it in enumerate(items):
            if (it[0] == "n" and it[1] > js[0]) or (it[0] == "v" and self.ancla[it[1]] > js[0]):
                return p
        return len(items)


def proyecto(etapa, base):
    """Los archivos del explorador al final del video 'etapa'. base = archivos_plantilla() de render.py."""
    f, carpetas = base
    f = dict(f)
    etapas = [etapa] if CFG.ETAPAS_COMPLETAS else range(1, etapa + 1)
    for n in etapas:
        if n < 1:
            continue
        raiz = carpeta_etapa(n)
        for p in sorted(raiz.rglob("*")):
            if p.is_file():
                f[str(p.relative_to(raiz)).replace("\\", "/")] = p.read_text(encoding="utf-8")
    for ruta, desde in CFG.QUITAR.items():
        if etapa >= desde:
            f.pop(ruta, None)
    return f, set(carpetas)


VIDEOS_CURSO = CFG.VIDEOS     # [(título, resultado, ícono)] para el temario


def instalar(Director, render):
    """Agrega al Director los métodos del curso. 'render' es el módulo render.py."""
    R = render

    # ------------------------------------------------------------------ código por etapas
    def codigo(self, ruta, etapa):
        """Prepara un archivo para pasar de la etapa anterior a 'etapa'."""
        antes = self.s.files.get(ruta, "")
        despues = contenido(ruta, etapa)
        assert despues is not None, f"{ruta} no existe en la etapa {etapa}"
        c = Codigo(ruta, despues, antes)
        assert c.texto() == antes, f"{ruta}: el editor no coincide con la etapa anterior"
        c.etapa = etapa
        return c

    def _cps_para(self, texto, frase):
        """Velocidad de tecleo para que la línea se escriba mientras se explica."""
        if not frase:
            return 22
        dur = R.duracion_frase(frase)
        return max(14, min(60, len(texto) / max(1.2, dur * 0.8)))

    def _marcar(self, a, b, titulo=None, nota=None):
        """Selecciona las líneas a..b del editor (y muestra la nota) hasta que termine la frase."""
        top = self._mostrar_linea(a)
        vis = R.lineas_visibles(self.s)
        # que quede espacio debajo de la selección para la nota (si no, taparía el código de arriba)
        libre = 7 if (titulo or nota) else 2
        if b > top + vis - libre:
            sc = dict(self.s.scroll)
            sc[self.s.activo] = max(0, min(a - 1, b - vis + libre + 1))
            self.set(scroll=sc)
        self.set(sel=(a, b))
        if titulo or nota:
            self.set(nota=(titulo, nota or ""))
        self.hold()
        self.wait(0.35)
        self.set(sel=None, nota=None)

    def poner(self, c, js, frase=None, titulo=None, nota=None, modo="escribir", cps=None, marcar=True):
        """Escribe las líneas nuevas js en su lugar exacto mientras se explican."""
        js = sorted(j for j in js if not c.presente[j])
        if not js:
            return
        p = c.posicion_insertar(js)
        lineas = [c.linea(it) for it in c.items()]
        texto = "\n".join(c.nuevas[j] for j in js)
        actual = self.texto()
        assert actual == "\n".join(lineas), f"{c.ruta} desfasado antes de escribir"
        if p > 0:
            pos = len("\n".join(lineas[:p]))
            bloque = "\n" + texto
        else:
            pos = 0
            bloque = texto + "\n"
        if frase:
            self.say(frase)
        lin, col = self._cursor_de(actual, pos)
        if self.s.cursor != (lin, col) or self.s.foco != "editor":
            top = self._mostrar_linea(lin)
            self.clic(R.ED_X + R.GUTTER + col * R.CW + 12, R.ED_Y + (lin - top) * R.LH + R.LH / 2)
            self.set(cursor=(lin, col), foco="editor", sel=None)
            if col == 0 and p > 0:
                self.atajo("End", 0.5)
        self.pos = pos
        if modo == "pegar":
            self.pegar(bloque)
        else:
            self.escribir_codigo(bloque, cps or self._cps_para(texto, frase))
        self.pos = None
        for j in js:
            c.presente[j] = True
        assert self.texto() == c.texto(), f"{c.ruta}: lo escrito no coincide (líneas {js[0]}-{js[-1]})"
        if marcar and (frase or nota):
            self._marcar(p, p + len(js) - 1, titulo, nota)
        else:
            self.hold()

    def quitar(self, c, iis, frase=None, marcar=True):
        """Selecciona líneas viejas y las borra."""
        iis = sorted(iis)
        items = c.items()
        idx = [items.index(("v", i)) for i in iis]
        a, b = idx[0], idx[-1]
        assert b - a + 1 == len(iis), f"{c.ruta}: las líneas a borrar no están juntas"
        if frase:
            self.say(frase)
        top = self._mostrar_linea(a)
        self.mover(R.ED_X + R.GUTTER + 8, R.ED_Y + (a - top) * R.LH + R.LH / 2, 0.45)
        n = b - a + 1
        for k in range(1, min(n, 8) + 1):
            fin = a + round((n - 1) * k / min(n, 8))
            self.set(sel=(a, fin), mouse=(R.ED_X + R.GUTTER + 260, R.ED_Y + (fin - top) * R.LH + R.LH / 2))
            self.emit(2)
        if marcar and frase:
            self.wait(min(1.6, max(0.6, R.duracion_frase(frase) * 0.4)))
        else:
            self.wait(0.5)
        self.atajo("Delete", 0.6)
        for i in iis:
            c.viva[i] = False
        self.set(sel=None)
        nuevo = c.texto()
        self._poner_texto(nuevo, (min(a, max(0, len(nuevo.split("\n")) - 1)), 0))
        self.wait(0.3)

    def cambiar(self, c, iis, js, frase=None, titulo=None, nota=None, modo="escribir", cps=None):
        """Borra líneas viejas y escribe las nuevas en su lugar (una sola explicación)."""
        if frase:
            self.say(frase)
        texto = "\n".join(c.nuevas[j] for j in js)
        self.quitar(c, iis, marcar=False)
        self.poner(c, js, None, titulo, nota, modo, cps or self._cps_para(texto, frase), marcar=False)
        if nota or titulo:
            p = c.items().index(("n", sorted(js)[0]))
            self._marcar(p, p + len(js) - 1, titulo, nota)
        self.hold()

    def vaciar(self, c, frase=None):
        """Ctrl + A y Suprimir: borra todo el archivo (las líneas viejas)."""
        if frase:
            self.say(frase)
        self.borrar_todo()
        for i in range(len(c.viejas)):
            c.viva[i] = False
        for j in range(len(c.nuevas)):          # Ctrl + A también borra lo que coincidía
            c.presente[j] = j == len(c.nuevas) - 1 and c.nuevas[j] == ""
        f = dict(self.s.files)
        f[c.ruta] = c.texto()
        self.set(files=f)
        assert self.texto() == c.texto()

    def terminar(self, c):
        """Guarda y verifica que el archivo quedó igual al de la carpeta curso/."""
        assert c.completo(), f"{c.ruta}: faltan líneas {c.pendientes()[:5]} / viejas {c.viejas_vivas()[:5]}"
        assert self.s.files[c.ruta] == contenido(c.ruta, c.etapa), f"{c.ruta} no coincide con la etapa {c.etapa}"

    def abrir_proyecto(self, etapa):
        """VS Code con el proyecto tal como quedó al final del video 'etapa'."""
        f, carpetas = proyecto(etapa, R.archivos_plantilla())
        self.s = R.Estado()
        self.cwd = CFG.RUTA_TERMINAL
        self.estado_terminales = {}
        abiertas = set(CFG.CARPETAS_ABIERTAS) | {"/".join(r.split("/")[:k]) for r in f
                                                 if r.split("/")[0] in CFG.CARPETAS_ABIERTAS
                                                 for k in range(1, len(r.split("/")))}
        self.set(raiz=CFG.NOMBRE.upper(), files=f, carpetas=carpetas, abiertas=frozenset(abiertas), mouse=(1000, 500))

    def borrar_archivo(self, ruta, frase=None):
        """Clic derecho → Delete en el explorador."""
        if frase:
            self.say(frase)
        partes = ruta.split("/")
        self.set(abiertas=self.s.abiertas | {"/".join(partes[:k]) for k in range(1, len(partes))}, foco="explorer")
        items = R.arbol(self.s)
        idx = next(k for k, it in enumerate(items) if it[2] == ruta)
        self.clic(R.ACT_W + 110 + len(partes) * 18, R.TITLE_H + 70 + idx * 28 + 12)
        self.wait(0.3)
        self.atajo("Delete", 0.8)
        self.wait(0.5)
        f = dict(self.s.files)
        f.pop(ruta, None)
        tabs = tuple(t for t in self.s.tabs if t != ruta)
        activo = self.s.activo if self.s.activo != ruta else (tabs[-1] if tabs else None)
        self.set(files=f, tabs=tabs, activo=activo, foco="editor")
        self.wait(0.4)

    # ------------------------------------------------------------------ Debug Console y depurador
    def depurar(self):
        """F5: ejecuta el programa en modo depuración (los mensajes de arranque vienen de CFG.LANZAR)."""
        self.atajo("F5", 0.8)
        self.wait(0.3)
        self.set(depurando=True, term_abierto=True, panel="debug", consola=())
        for texto, pausa in CFG.LANZAR:
            self.consola(texto, R.G if texto.startswith(("√", "✓")) else R.GRIS, pausa)

    def consola(self, texto, color=None, pausa=0.12, app=False):
        """Una línea en la Debug Console. app=True: lo que imprime la app con debugPrint."""
        if app:
            texto = CFG.PREFIJO_APP + texto
        self.set(consola=self.s.consola + ((texto, color or R.BLANCO),))
        self.wait(pausa)

    def recargar(self):
        """Hot reload (al guardar con Ctrl + S mientras la app corre)."""
        if CFG.RECARGA:
            self.consola(CFG.RECARGA, R.GRIS, 0.5)

    def reiniciar(self):
        """Hot restart: vuelve a ejecutar main()."""
        self.atajo("Ctrl + Shift + F5", 0.8)
        self.consola(CFG.REINICIO, R.GRIS, 0.6)

    def detener(self):
        self.atajo("Shift + F5", 0.8)
        self.consola(CFG.FIN, R.GRIS, 0.3)
        self.set(depurando=False, pausa=None, hover=None)
        self.wait(0.4)

    def punto_de_parada(self, texto):
        """Clic a la izquierda del número de línea: un punto rojo donde la app se va a detener."""
        lineas = self.texto().split("\n")
        lin = next(k for k, l in enumerate(lineas) if texto in l)
        top = self._mostrar_linea(lin)
        self.clic(R.ED_X + 16, R.ED_Y + (lin - top) * R.LH + R.LH / 2)
        self.set(punto=(self.s.activo, lin))
        self.wait(0.4)
        return lin

    def pausar_en(self, lin):
        """La app llegó al punto de parada: la línea se pinta de amarillo."""
        self.set(pausa=(self.s.activo, lin))
        self.wait(0.3)

    def mostrar_valor(self, texto, valor):
        """Pasa el mouse sobre una variable y VS Code muestra su valor."""
        lineas = self.texto().split("\n")
        lin = next(k for k, l in enumerate(lineas) if texto in l)
        col = lineas[lin].index(texto)
        top = self._mostrar_linea(lin)
        x = R.ED_X + R.GUTTER + (col + len(texto) / 2) * R.CW
        self.mover(x, R.ED_Y + (lin - top) * R.LH + R.LH / 2, 0.6)
        self.wait(0.3)
        self.set(hover=(lin, col, texto, valor))

    def continuar(self):
        self.atajo("F5", 0.6)
        self.set(pausa=None, hover=None)
        self.wait(0.3)

    # ------------------------------------------------------------------ la app en el celular
    def celular(self, id_, titulo, pasos, inicial=()):
        """La app (réplica en escenas/CFG.REPLICA) según la etapa del curso.
        titulo: (icono, kicker, html). inicial: eventos en t = 0 (tema, etapa, pantalla...).
        Pasos: ("decir", frase) · ("esperar", s) · ("hasta_fin",) · ("ev", tipo, *args)
               ("toque", id_o_x, y) · ("nota", icono, texto, color)
               ("escribir", texto[, id_del_campo]) · ("enviar"[, id_del_boton])
               ("preguntar", pregunta, respuesta, fuentes, {"voz": bool, "habla": bool, "campo": id, "enviar": id})
        Los toques usan el id de un elemento de la pantalla (ver escenas/app_pantallas.js)."""
        obj = R.DemoApp(id_)
        obj.html = R.APP_HTML
        self.demos_app.append(obj)
        t0 = self.t
        vt = lambda: round(self.t - t0, 3)
        ev = lambda *a: obj.eventos.append([vt(), *a])
        ev("titulo", [titulo[0], titulo[1]], titulo[2])
        for e in inicial:
            ev(*e)

        def avanzar(seg):
            for _ in range(max(0, round(seg * R.FPS))):
                self.set(slide=(obj, self.t - t0, None), ocultar_mouse=True)
                self.emit()

        def hasta_fin_de_frase():
            while self.t < self.say_hasta:
                avanzar(1 / R.FPS)

        def tocar(objetivo, y=None):
            ev("toque", objetivo, y)
            avanzar(0.3)

        def teclear(texto, cps=12):
            for k in range(1, len(texto) + 1):
                ev("campo", texto[:k])
                avanzar(1 / R.FPS * max(1, round(R.FPS / cps * self.rnd.uniform(0.6, 1.4))))

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
                tocar(*p[1:])
            elif tipo == "nota":
                ev("nota", *p[1:])
                avanzar(0.4)
            elif tipo == "escribir":
                tocar(p[2] if len(p) > 2 else "campo")
                ev("foco", True)
                avanzar(0.3)
                teclear(p[1])
                avanzar(0.3)
            elif tipo == "enviar":
                tocar(p[1] if len(p) > 1 else "tecla-enviar")
                ev("foco", False)
                ev("campo", "")
            elif tipo == "preguntar":
                _, pregunta, respuesta, fuentes = p[:4]
                op = p[4] if len(p) > 4 else {}
                if op.get("voz"):
                    hasta_fin_de_frase()
                    tocar("mic")
                    ev("estado", "escuchando")
                    avanzar(0.4)
                    self.log_usuario.append((self.t, pregunta))      # la persona habla
                    avanzar(R.duracion_frase(pregunta) + 1.2)
                    ev("estado", "reposo")
                else:
                    tocar(op.get("campo", "campo"))
                    ev("foco", True)
                    avanzar(0.3)
                    teclear(pregunta)
                    avanzar(0.3)
                    tocar(op.get("enviar", "tecla-enviar"))
                    ev("foco", False)
                ev("campo", "")
                ev("msg", "u", pregunta)
                ev("pendiente")
                ev("estado", "pensando")
                avanzar(op.get("pensar", 1.6))                       # busca y Gemma empieza
                dur = max(1.2, len(respuesta) / 30)                  # token por token
                ev("stream", respuesta, dur, fuentes)
                avanzar(dur + 0.2)
                if op.get("habla"):
                    hasta_fin_de_frase()                             # nunca encima del narrador
                    ev("estado", "hablando")
                    self.log_app.append((self.t, respuesta))      # la app habla
                    avanzar(R.duracion_frase(respuesta, R.VOZ_APP))
                ev("estado", "reposo")
                avanzar(0.4)
        hasta_fin_de_frase()
        avanzar(0.6)
        self.set(slide=None, ocultar_mouse=False)

    app = celular       # D.app(...) es lo mismo: la app en un celular o en un navegador

    for nombre, f in list(locals().items()):
        if callable(f) and nombre not in ("Director", "render", "R"):
            setattr(Director, nombre, f)


# ---------------------------------------------------------------------- textos de las escenas del curso
def datos_escena(**kw):
    return json.loads(json.dumps(kw, ensure_ascii=False))
