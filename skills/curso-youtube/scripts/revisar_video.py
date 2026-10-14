#!/usr/bin/env python3
"""Revisa un video renderizado: duración, volumen (LUFS), silencios largos y una hoja de capturas.

    python revisar_video.py videos/02-nombre.mp4 --cada 30 --silencio 9
"""
import argparse
import re
import subprocess
import tempfile
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--cada", type=float, default=30, help="segundos entre capturas")
    ap.add_argument("--silencio", type=float, default=9, help="avisar silencios más largos que esto")
    a = ap.parse_args()
    v = Path(a.video)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(v)],
                               capture_output=True, text=True).stdout)
    print(f"Duración: {int(dur // 60)}:{int(dur % 60):02d}  ·  {v.stat().st_size / 1e6:.1f} MB")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(v), "-vn", "-af", "ebur128=framelog=quiet",
                        "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.search(r"I:\s+(-?[\d.]+) LUFS", r)
    print(f"Volumen integrado: {m.group(1) if m else '?'} LUFS (objetivo: -16)")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(v), "-vn", "-af",
                        f"silencedetect=noise=-45dB:d={a.silencio}", "-f", "null", "-"], capture_output=True, text=True).stderr
    for fin, d in re.findall(r"silence_end: ([\d.]+) \| silence_duration: ([\d.]+)", r):
        ini = float(fin) - float(d)
        print(f"  Silencio de {float(d):.0f} s en {int(ini // 60)}:{int(ini % 60):02d}")
    tmp = Path(tempfile.mkdtemp())
    n = 0
    t = 5.0
    while t < dur:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.1f}", "-i", str(v), "-frames:v", "1",
                        "-vf", "scale=640:360", str(tmp / f"f{n:03d}.png")], check=True)
        n += 1
        t += a.cada
    hoja = v.with_name(v.stem + "_hoja.jpg")
    cols = 4
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp / "f%03d.png"), "-vf",
                    f"tile={cols}x{(n + cols - 1) // cols}", "-frames:v", "1", str(hoja)], check=True)
    print(f"Hoja de capturas ({n}, una cada {a.cada:.0f} s): {hoja}")


if __name__ == "__main__":
    main()
