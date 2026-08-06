#!/usr/bin/env python3
"""Valida el fondo de una imagen y devuelve el informe en JSON.

Uso:  python validate_background.py imagen.png [--mask mascara.png]
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
    from ai_image_studio.qc import validate_background
except ImportError as exc:
    raise SystemExit(
        "error: no se encuentra el paquete ai_image_studio.\n"
        '  Instalalo con:  pip install "ai-image-studio"\n'
        "  O usa el paquete Full, que ya incluye el codigo fuente.\n"
        f"  Detalle: {exc}"
    ) from None

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("image", help="imagen a validar")
parser.add_argument("--mask", help="mascara del producto, si existe")
parser.add_argument("--min-channel", type=int, default=250)
parser.add_argument("--max-nonwhite-ratio", type=float, default=0.002)
args = parser.parse_args()

print(json.dumps(
    validate_background(args.image, args.mask, args.min_channel, args.max_nonwhite_ratio),
    indent=2,
))
