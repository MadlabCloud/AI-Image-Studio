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

def compare_pixels(reference_path: str | Path, result_path: str | Path, mask_path: str | Path | None = None) -> dict:
    with Image.open(reference_path) as a_img, Image.open(result_path) as b_img:
        a = a_img.convert("RGB"); b = b_img.convert("RGB")
        if a.size != b.size:
            raise ValueError("Las imágenes deben estar alineadas y tener el mismo tamaño")
        aa = np.asarray(a, dtype=np.float32); bb = np.asarray(b, dtype=np.float32)
    if mask_path:
        mask = load_mask(mask_path)
        if mask.shape != aa.shape[:2]:
            raise ValueError("La máscara no coincide con las imágenes")
        diff = np.abs(aa-bb)[mask]
    else:
        diff = np.abs(aa-bb).reshape(-1,3)
    mae = float(diff.mean()) if diff.size else 0.0
    rmse = float(np.sqrt(np.mean(diff**2))) if diff.size else 0.0
    p95 = float(np.percentile(diff,95)) if diff.size else 0.0
    return {"mae": mae, "rmse": rmse, "p95_absolute_error": p95, "evaluated_values": int(diff.size)}

def aggregate_gates(gates: dict[str, dict]) -> str:
    states = {g.get("status") for g in gates.values()}
    if "FAIL" in states: return "FAIL"
    if "REVIEW" in states: return "REVIEW"
    return "PASS"
