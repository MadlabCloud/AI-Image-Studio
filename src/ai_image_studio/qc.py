from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from .masks import load_mask


def validate_background(image_path: str | Path, mask_path: str | Path | None = None, min_channel: int = 250, max_nonwhite_ratio: float = 0.002, border_fraction: float = 0.06) -> dict[str, Any]:
    with Image.open(image_path) as img:
        rgb = np.asarray(img.convert("RGB"), dtype=np.uint8)
    h, w, _ = rgb.shape
    if mask_path:
        fg = load_mask(mask_path)
        if fg.shape != (h, w):
            raise ValueError("La máscara y la imagen deben tener el mismo tamaño")
        region = ~fg
    else:
        by, bx = max(1, int(h*border_fraction)), max(1, int(w*border_fraction))
        region = np.zeros((h,w), dtype=bool)
        region[:by,:] = True; region[-by:,:] = True; region[:,:bx] = True; region[:,-bx:] = True
    pixels = rgb[region]
    if pixels.size == 0:
        raise ValueError("No hay píxeles de fondo para validar")
    white = np.all(pixels >= min_channel, axis=1)
    nonwhite_ratio = float(1.0 - white.mean())
    mean = pixels.mean(axis=0).tolist()
    std = pixels.std(axis=0).tolist()
    status = "PASS" if nonwhite_ratio <= max_nonwhite_ratio else "FAIL"
    return {"status": status, "details": {"evaluated_pixels": int(len(pixels)), "min_channel": min_channel, "max_nonwhite_ratio": max_nonwhite_ratio, "nonwhite_ratio": nonwhite_ratio, "mean_rgb": mean, "std_rgb": std, "method": "mask" if mask_path else "border"}}

def validate_dimensions(image_path: str | Path, width: int, height: int, expected_format: str | None = None) -> dict:
    with Image.open(image_path) as img:
        ok_size = img.size == (width, height)
        actual_format = (img.format or "").lower()
        ok_format = expected_format is None or actual_format == expected_format.lower()
        alpha = "A" in img.getbands()
        return {"status": "PASS" if ok_size and ok_format and not alpha else "FAIL", "details": {"actual_size": list(img.size), "expected_size": [width,height], "actual_format": actual_format, "expected_format": expected_format, "has_alpha": alpha}}

TILE_SIZE = 25


def _local_metrics(per_pixel: np.ndarray, tile: int = TILE_SIZE) -> dict:
    """Peor error concentrado en una region, no repartido por toda la imagen.

    ``per_pixel`` es el error absoluto maximo de cada pixel, con forma (alto, ancho).

    Las medias globales no sirven como puerta: un defecto catastrofico pero local se
    diluye. Medido sobre una foto real de 1000x1000 a la que se borro una franja de
    producto -- el equivalente a una pata perdida por el matting -- el error afectaba
    al 1,2 % de los pixeles y daba ``mae`` 0,81 y ``p95_absolute_error`` 0,0: cualquier
    umbral sobre esas cifras habria aprobado el resultado. Partiendo la imagen en
    bloques, el mismo defecto da un peor bloque de 121,5 y 24 bloques por encima de 10.
    """
    alto, ancho = per_pixel.shape
    if alto < tile or ancho < tile:
        peor = float(per_pixel.mean()) if per_pixel.size else 0.0
        return {"tile_size": tile, "worst_tile_mae": peor, "tiles_evaluated": 1,
                "tiles_over_10": int(peor > 10)}
    # Se recorta al multiplo inferior: un borde parcial no forma un bloque completo.
    recorte = per_pixel[: alto // tile * tile, : ancho // tile * tile]
    bloques = recorte.reshape(alto // tile, tile, ancho // tile, tile).mean(axis=(1, 3))
    return {
        "tile_size": tile,
        "worst_tile_mae": float(bloques.max()),
        "tiles_evaluated": int(bloques.size),
        "tiles_over_10": int((bloques > 10).sum()),
    }


def compare_pixels(reference_path: str | Path, result_path: str | Path, mask_path: str | Path | None = None) -> dict:
    """Compara dos imagenes alineadas y devuelve metricas globales **y locales**.

    Las globales (``mae``, ``rmse``, ``p95_absolute_error``) describen el conjunto.
    Las locales (``max_absolute_error`` y ``local``) describen el peor punto y la peor
    zona, que es donde aparecen las amputaciones, los halos y los huecos. Ninguna
    metrica por si sola es una puerta: ver ``skills/image-quality-gates``.
    """
    with Image.open(reference_path) as a_img, Image.open(result_path) as b_img:
        a = a_img.convert("RGB"); b = b_img.convert("RGB")
        if a.size != b.size:
            raise ValueError("Las imágenes deben estar alineadas y tener el mismo tamaño")
        aa = np.asarray(a, dtype=np.float32); bb = np.asarray(b, dtype=np.float32)
    absoluto = np.abs(aa - bb)
    por_pixel = absoluto.max(axis=2)
    if mask_path:
        mask = load_mask(mask_path)
        if mask.shape != aa.shape[:2]:
            raise ValueError("La máscara no coincide con las imágenes")
        diff = absoluto[mask]
        # Fuera de la mascara no hay nada que juzgar: se anula para que no contamine
        # el peor bloque con diferencias legitimas de fondo.
        por_pixel = np.where(mask, por_pixel, 0.0)
    else:
        diff = absoluto.reshape(-1, 3)
    mae = float(diff.mean()) if diff.size else 0.0
    rmse = float(np.sqrt(np.mean(diff**2))) if diff.size else 0.0
    p95 = float(np.percentile(diff,95)) if diff.size else 0.0
    maximo = float(diff.max()) if diff.size else 0.0
    return {
        "mae": mae,
        "rmse": rmse,
        "p95_absolute_error": p95,
        "max_absolute_error": maximo,
        "changed_pixel_ratio": float((por_pixel > 0).mean()) if por_pixel.size else 0.0,
        "local": _local_metrics(por_pixel),
        "evaluated_values": int(diff.size),
    }

def aggregate_gates(gates: dict[str, dict]) -> str:
    states = {g.get("status") for g in gates.values()}
    if "FAIL" in states: return "FAIL"
    if "REVIEW" in states: return "REVIEW"
    return "PASS"
