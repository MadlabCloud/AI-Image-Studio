#!/usr/bin/env python3
"""Exporta una imagen a WebP con dimensiones exactas y devuelve el informe en JSON.

Uso:  python export_webp.py origen.png destino.webp [--width 1000] [--height 1000]
"""
import argparse
import json
import sys
from pathlib import Path

# Dentro del repositorio o del paquete Full, `src/` esta tres niveles por encima.
# En los ZIP que solo llevan skills no existe: alli el paquete debe estar instalado.
_SRC = Path(__file__).resolve().parents[3] / "src"
if _SRC.is_dir():
    sys.path.insert(0, str(_SRC))

try:
    from ai_image_studio.export import export_webp
except ImportError as exc:
    raise SystemExit(
        "error: no se encuentra el paquete ai_image_studio.\n"
        '  Instalalo con:  pip install "ai-image-studio"\n'
        "  O usa el paquete Full, que ya incluye el codigo fuente.\n"
        f"  Detalle: {exc}"
    ) from None

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("source", help="imagen de origen")
parser.add_argument("destination", help="archivo WebP de salida")
parser.add_argument("--width", type=int, default=1000)
parser.add_argument("--height", type=int, default=1000)
parser.add_argument("--quality", type=int, default=86)
args = parser.parse_args()

print(json.dumps(
    export_webp(args.source, args.destination, args.width, args.height, args.quality),
    indent=2,
))
