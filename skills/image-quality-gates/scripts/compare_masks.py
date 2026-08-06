#!/usr/bin/env python3
"""Compara dos mascaras y devuelve el informe de acuerdo en JSON.

Uso:  python compare_masks.py mascara_a.png mascara_b.png
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
    from ai_image_studio.masks import compare_mask_files
except ImportError as exc:
    raise SystemExit(
        "error: no se encuentra el paquete ai_image_studio.\n"
        '  Instalalo con:  pip install "ai-image-studio"\n'
        "  O usa el paquete Full, que ya incluye el codigo fuente.\n"
        f"  Detalle: {exc}"
    ) from None

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("a", help="primera mascara")
parser.add_argument("b", help="segunda mascara")
args = parser.parse_args()

print(json.dumps(compare_mask_files(args.a, args.b), indent=2))
