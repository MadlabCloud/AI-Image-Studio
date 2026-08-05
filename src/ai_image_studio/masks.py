from __future__ import annotations
from pathlib import Path
from collections import deque
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
    h, w = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    count = 0
    for y in range(h):
        for x in range(w):
            if not mask[y, x] or visited[y, x]:
                continue
            q = deque([(y, x)]); visited[y, x] = True; size = 0
            while q:
                cy, cx = q.popleft(); size += 1
                for ny, nx in ((cy-1,cx),(cy+1,cx),(cy,cx-1),(cy,cx+1)):
                    if 0 <= ny < h and 0 <= nx < w and mask[ny,nx] and not visited[ny,nx]:
                        visited[ny,nx] = True; q.append((ny,nx))
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
