#!/usr/bin/env python3
"""Crea la carpeta de un curso nuevo con el motor de video listo para usar.

    python nuevo_curso.py ~/cursos/react-tareas --nombre tareas --curso "Curso de React"

Crea:
    <destino>/codigo/            aquí va el proyecto terminado
    <destino>/curso/             el código al final de cada video (01-..., 02-...)
    <destino>/video/             el motor: render.py, curso.py, proyecto.py, escenas/, guiones/, plantilla/, marca/
"""
import argparse
import shutil
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
MOTOR = SKILL / "assets" / "motor"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("destino")
    ap.add_argument("--nombre", required=True, help="nombre de la carpeta del proyecto (ej. tareas)")
    ap.add_argument("--curso", required=True, help='nombre del curso (ej. "Curso de React")')
    ap.add_argument("--canal", default="Tu canal")
    ap.add_argument("--logo", help="PNG cuadrado con fondo transparente (por defecto, el del motor)")
    a = ap.parse_args()

    destino = Path(a.destino).expanduser().resolve()
    video = destino / "video"
    if video.exists():
        raise SystemExit(f"{video} ya existe: no lo sobrescribo.")
    (destino / "codigo").mkdir(parents=True, exist_ok=True)
    (destino / "curso").mkdir(exist_ok=True)
    shutil.copytree(MOTOR, video)
    (video / "plantilla").mkdir(exist_ok=True)
    (video / "modelos").mkdir(exist_ok=True)
    if a.logo:
        shutil.copy(a.logo, video / "marca" / "logo.png")

    cfg = (video / "proyecto.py").read_text(encoding="utf-8")
    cfg = cfg.replace('CURSO = "Curso de ejemplo"', f'CURSO = "{a.curso}"')
    cfg = cfg.replace('NOMBRE = "miapp"', f'NOMBRE = "{a.nombre}"')
    cfg = cfg.replace('RUTA_TERMINAL = "C:\\\\proyectos\\\\miapp"', f'RUTA_TERMINAL = "C:\\\\proyectos\\\\{a.nombre}"')
    cfg = cfg.replace('CANAL = "Tu canal"', f'CANAL = "{a.canal}"')
    (video / "proyecto.py").write_text(cfg, encoding="utf-8")
    (destino / ".gitignore").write_text(
        "video/videos/*.mp4\nvideo/_partes/\nvideo/modelos/\nvideo/_voz/\nvideo/_cache_web/\nvideo/preview/\n"
        "video/narracion.wav\nvideo/escenas/_demos/\n__pycache__/\n", encoding="utf-8")
    print(f"Curso creado en {destino}")
    print("Siguiente: edita video/proyecto.py, pon la plantilla del proyecto en video/plantilla/,")
    print("el proyecto final en codigo/, las etapas en curso/NN-nombre/ y los guiones en video/guiones/.")


if __name__ == "__main__":
    main()
