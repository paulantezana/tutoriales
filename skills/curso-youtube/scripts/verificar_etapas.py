#!/usr/bin/env python3
"""Compila y prueba el código de CADA video por separado, para que ninguna etapa del curso quede rota.

    python verificar_etapas.py --base /tmp/plantilla/miapp --etapas ~/cursos/x/curso \
        --cmd "flutter pub get" --cmd "flutter analyze" --cmd "flutter test"

--base: un proyecto recién creado (ej. con flutter create / npm create vite / python -m venv ...).
Por cada carpeta NN-nombre/ de --etapas copia la base, pone encima los archivos de la etapa y corre
los comandos. --incremental: cada etapa solo trae lo que cambió (se aplican todas las anteriores).
--quitar ruta:video: archivos de la base que se borran a partir de ese video.
"""
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--etapas", required=True)
    ap.add_argument("--cmd", action="append", default=[])
    ap.add_argument("--incremental", action="store_true")
    ap.add_argument("--quitar", action="append", default=[], help="ruta:video")
    a = ap.parse_args()
    etapas = sorted(p for p in Path(a.etapas).iterdir() if p.is_dir() and p.name[:2].isdigit())
    quitar = {q.split(":")[0]: int(q.split(":")[1]) for q in a.quitar}
    tmp = Path(tempfile.mkdtemp(prefix="etapas_"))
    ok = True
    for k, etapa in enumerate(etapas, 1):
        destino = tmp / etapa.name
        shutil.copytree(a.base, destino, symlinks=True)
        capas = etapas[:k] if a.incremental else [etapa]
        if not a.incremental:
            for carpeta in {p.relative_to(etapa).parts[0] for p in etapa.rglob("*") if p.is_file()} & {"lib", "src", "test", "tests"}:
                shutil.rmtree(destino / carpeta, ignore_errors=True)   # lib/ y test/ vienen completos en la etapa
        for capa in capas:
            shutil.copytree(capa, destino, dirs_exist_ok=True)
        for ruta, desde in quitar.items():
            if k >= desde:
                (destino / ruta).unlink(missing_ok=True)
        print(f"== {etapa.name}")
        for cmd in a.cmd:
            r = subprocess.run(cmd, shell=True, cwd=destino, capture_output=True, text=True)
            ultima = (r.stdout + r.stderr).strip().splitlines()[-1:] or [""]
            print(f"   {'OK ' if r.returncode == 0 else 'ERR'} {cmd}: {ultima[0][:120]}")
            ok &= r.returncode == 0
    print("Todo bien." if ok else "Hay etapas con errores.")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
