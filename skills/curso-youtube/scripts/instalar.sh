#!/usr/bin/env bash
# Instala lo que necesita el motor de video. Uso: bash instalar.sh <carpeta video/ del curso>
set -e
VIDEO="${1:-.}"
echo "== Paquetes de Python"
python3 -m pip install --quiet pillow pygments kokoro-onnx soundfile onnxruntime playwright
echo "== ffmpeg"
command -v ffmpeg >/dev/null || { echo "Falta ffmpeg: instálalo (apt install ffmpeg · brew install ffmpeg · winget install ffmpeg)"; exit 1; }
echo "== Chromium para Playwright"
if [ -z "$PLAYWRIGHT_BROWSERS_PATH" ] || [ ! -d "$PLAYWRIGHT_BROWSERS_PATH" ]; then
  python3 -m playwright install chromium || echo "No pude instalar Chromium: si ya hay uno, define PLAYWRIGHT_BROWSERS_PATH."
fi
echo "== Modelo de voz Kokoro (unos 340 MB, una sola vez)"
mkdir -p "$VIDEO/modelos"
cd "$VIDEO/modelos"
BASE=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1
[ -f kokoro-v1.0.onnx ] || curl -fL -o kokoro-v1.0.onnx "$BASE/kokoro-v1.0.onnx"
[ -f voices-v1.0.bin ] || curl -fL -o voices-v1.0.bin "$BASE/voices-v1.0.bin"
echo "Listo."
