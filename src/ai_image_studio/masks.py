from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image


def load_mask(path: str | Path) -> np.ndarray:
    with Image.open(path) as img:
        arr = np.asarray(img.convert("L"), dtype=np.uint8)
    return arr >= 128

def _bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1

def _components(mask: np.ndarray, min_pixels: int = 4) -> int:
    """Cuenta componentes conexos de 4 vecinos con al menos ``min_pixels`` pixeles.

    Recorre indices planos sobre ``bytes`` y ``bytearray`` en vez de indexar el array
    de numpy pixel a pixel: el acceso escalar a numpy cuesta unas dos ordenes de
    magnitud mas que el de una secuencia nativa, y solo se visitan los pixeles de
    primer plano en lugar de barrer el fondo desde Python.

    Medido sobre esta maquina, mascara de 1000x1000:

    =============================  =========  =========
    Caso                           antes      ahora
    =============================  =========  =========
    producto tipico (taburete)       0,36 s     0,08 s
    ruido 30 %                       0,53 s     0,15 s
    todo primer plano (patologico)   1,68 s     0,58 s
    =============================  =========  =========

    Techo conocido: el recorrido sigue siendo Python, asi que el coste crece con el
    numero de pixeles de primer plano. Para una mascara de catalogo es de sobra. Si
    algun dia hiciera falta mas, las dos salidas son etiquetado por tramos de fila con
    union-find, o ``scipy.ndimage.label``; esta ultima se descarta hoy porque anade
    decenas de megabytes de dependencia para una sola funcion.
    """
    h, w = mask.shape
    total = h * w
    plano = np.ascontiguousarray(mask, dtype=bool).reshape(-1).tobytes()
    visitado = bytearray(total)
    count = 0

    for inicio in np.flatnonzero(mask.reshape(-1)).tolist():
        if visitado[inicio]:
            continue
        visitado[inicio] = 1
        pila = [inicio]
        size = 0
        while pila:
            idx = pila.pop()
            size += 1
            columna = idx % w
            if columna and plano[idx - 1] and not visitado[idx - 1]:
                visitado[idx - 1] = 1; pila.append(idx - 1)
            if columna + 1 < w and plano[idx + 1] and not visitado[idx + 1]:
                visitado[idx + 1] = 1; pila.append(idx + 1)
            arriba = idx - w
            if arriba >= 0 and plano[arriba] and not visitado[arriba]:
                visitado[arriba] = 1; pila.append(arriba)
            abajo = idx + w
            if abajo < total and plano[abajo] and not visitado[abajo]:
                visitado[abajo] = 1; pila.append(abajo)
        if size >= min_pixels:
            count += 1
    return count

def mask_stats(mask: np.ndarray) -> dict:
    bbox = _bbox(mask)
    return {"width": int(mask.shape[1]), "height": int(mask.shape[0]), "foreground_pixels": int(mask.sum()), "foreground_ratio": float(mask.mean()), "bbox": bbox, "components": _components(mask)}

def compare_masks(a: np.ndarray, b: np.ndarray) -> dict:
    if a.shape != b.shape:
        raise ValueError(f"Las máscaras deben tener el mismo tamaño: {a.shape} != {b.shape}")
    intersection = int(np.logical_and(a,b).sum())
    union = int(np.logical_or(a,b).sum())
    a_sum, b_sum = int(a.sum()), int(b.sum())
    iou = intersection / union if union else 1.0
    precision = intersection / b_sum if b_sum else (1.0 if a_sum == 0 else 0.0)
    recall = intersection / a_sum if a_sum else (1.0 if b_sum == 0 else 0.0)
    sa, sb = mask_stats(a), mask_stats(b)
    def center(box):
        return None if box is None else ((box[0]+box[2])/2, (box[1]+box[3])/2)
    ca, cb = center(sa["bbox"]), center(sb["bbox"])
    if ca and cb:
        shift = (((ca[0]-cb[0]) / a.shape[1])**2 + ((ca[1]-cb[1]) / a.shape[0])**2) ** 0.5
    else:
        shift = 0.0 if ca == cb else 1.0
    return {"iou": iou, "precision": precision, "recall": recall, "area_ratio_b_over_a": (b_sum/a_sum if a_sum else None), "normalized_bbox_center_shift": shift, "a": sa, "b": sb}

def compare_mask_files(path_a: str | Path, path_b: str | Path) -> dict:
    return compare_masks(load_mask(path_a), load_mask(path_b))
