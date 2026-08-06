"""Comparacion de mascaras: la puerta `mask-agreement` de image-quality-gates.

Si estas metricas mienten, dos segmentaciones distintas pasarian por equivalentes y
un producto con una pata amputada se aprobaria.
"""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from ai_image_studio.masks import (
    compare_mask_files,
    compare_masks,
    load_mask,
    mask_stats,
)


def rectangulo(alto=40, ancho=40, caja=(10, 10, 30, 30)) -> np.ndarray:
    mask = np.zeros((alto, ancho), dtype=bool)
    x0, y0, x1, y1 = caja
    mask[y0:y1, x0:x1] = True
    return mask


def guardar(mask: np.ndarray, ruta) -> None:
    Image.fromarray((mask * 255).astype(np.uint8), mode="L").save(ruta)


def test_identical_masks_agree_completely():
    a = rectangulo()
    resultado = compare_masks(a, a.copy())
    assert resultado["iou"] == 1.0
    assert resultado["precision"] == 1.0
    assert resultado["recall"] == 1.0
    assert resultado["normalized_bbox_center_shift"] == 0.0


def test_disjoint_masks_do_not_agree_at_all():
    a = rectangulo(caja=(0, 0, 10, 10))
    b = rectangulo(caja=(30, 30, 40, 40))
    resultado = compare_masks(a, b)
    assert resultado["iou"] == 0.0
    assert resultado["precision"] == 0.0
    assert resultado["recall"] == 0.0
    assert resultado["normalized_bbox_center_shift"] > 0


def test_a_missing_leg_lowers_recall_but_not_precision():
    """El caso que motiva la puerta: la segunda mascara pierde una parte fina."""
    completa = rectangulo(caja=(10, 10, 30, 30))
    completa[30:38, 12:14] = True  # una pata
    amputada = rectangulo(caja=(10, 10, 30, 30))

    resultado = compare_masks(completa, amputada)

    assert resultado["recall"] < 1.0, "perder una pata tiene que bajar el recall"
    assert resultado["precision"] == 1.0, "la mascara amputada no añade pixeles falsos"
    assert resultado["iou"] < 1.0


def test_masks_of_different_size_are_rejected():
    with pytest.raises(ValueError, match="mismo tamaño"):
        compare_masks(rectangulo(40, 40), rectangulo(20, 20))


def test_stats_count_separate_components():
    mask = rectangulo(caja=(2, 2, 8, 8))
    mask[20:28, 20:28] = True
    assert mask_stats(mask)["components"] == 2


# El conteo de componentes se reescribio por rendimiento. Estas tres pruebas fijan la
# semantica exacta que debe conservar cualquier futura optimizacion.

def test_components_use_four_connectivity_not_eight():
    """Una diagonal son pixeles sueltos, no una sola pieza.

    Con 8 vecinos daria 1 componente; con 4, ninguno llega al minimo de 4 pixeles.
    """
    diagonal = np.zeros((20, 20), dtype=bool)
    for i in range(20):
        diagonal[i, i] = True
    assert mask_stats(diagonal)["components"] == 0


def test_components_below_the_minimum_size_are_ignored():
    """El umbral existe para que el ruido de matting no cuente como pieza."""
    mask = np.zeros((20, 20), dtype=bool)
    mask[1, 1] = True            # 1 pixel: ruido
    mask[5:7, 5:7] = True        # 4 pixeles: pieza valida
    assert mask_stats(mask)["components"] == 1


def test_components_span_rows_and_columns():
    """Una forma en L es una sola pieza aunque cambie de direccion."""
    ele = np.zeros((20, 20), dtype=bool)
    ele[2:15, 2:4] = True
    ele[13:15, 2:15] = True
    assert mask_stats(ele)["components"] == 1


def test_an_empty_mask_reports_no_bounding_box():
    stats = mask_stats(np.zeros((10, 10), dtype=bool))
    assert stats["bbox"] is None
    assert stats["foreground_pixels"] == 0


def test_two_empty_masks_are_treated_as_equivalent():
    resultado = compare_masks(np.zeros((8, 8), bool), np.zeros((8, 8), bool))
    assert resultado["iou"] == 1.0


def test_loading_from_disk_thresholds_at_128(tmp_path):
    gris = np.full((4, 4), 127, dtype=np.uint8)
    gris[0, 0] = 128
    ruta = tmp_path / "m.png"
    Image.fromarray(gris, mode="L").save(ruta)

    mask = load_mask(ruta)

    assert mask[0, 0] is np.True_ or bool(mask[0, 0]) is True
    assert not mask[1, 1]


def test_comparing_files_matches_comparing_arrays(tmp_path):
    a, b = rectangulo(), rectangulo(caja=(12, 12, 30, 30))
    guardar(a, tmp_path / "a.png")
    guardar(b, tmp_path / "b.png")

    assert compare_mask_files(tmp_path / "a.png", tmp_path / "b.png") == compare_masks(a, b)
