"""Las metricas locales de `compare_pixels` deben ver lo que las globales no ven.

Origen de estas pruebas: sobre una fotografia real de 1000x1000 se borro una franja
de producto, el equivalente a una pata perdida por el matting. Afectaba al 1,2 % de
los pixeles y las metricas globales lo daban por bueno --`mae` 0,81 y
`p95_absolute_error` 0,0--, de modo que cualquier umbral basado en ellas habria
aprobado un producto amputado.
"""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from ai_image_studio.qc import compare_pixels

LADO = 200


@pytest.fixture
def referencia(tmp_path):
    rng = np.random.default_rng(7)
    base = rng.integers(60, 200, size=(LADO, LADO, 3), dtype=np.uint8)
    ruta = tmp_path / "referencia.png"
    Image.fromarray(base).save(ruta)
    return ruta, base


def guardar(tmp_path, nombre, datos):
    ruta = tmp_path / nombre
    Image.fromarray(datos.astype(np.uint8)).save(ruta)
    return ruta


def test_identical_images_report_no_damage(tmp_path, referencia):
    ruta, base = referencia
    r = compare_pixels(ruta, guardar(tmp_path, "copia.png", base))
    assert r["mae"] == 0.0
    assert r["max_absolute_error"] == 0.0
    assert r["changed_pixel_ratio"] == 0.0
    assert r["local"]["worst_tile_mae"] == 0.0
    assert r["local"]["tiles_over_10"] == 0


def test_a_small_but_catastrophic_defect_is_visible_locally(tmp_path, referencia):
    """El caso que motiva todo: un defecto pequeño en area pero destructivo."""
    ruta, base = referencia
    amputada = base.copy()
    amputada[150:200, 90:110] = 255          # franja borrada: 1000 px de 40000, un 2,5 %

    r = compare_pixels(ruta, guardar(tmp_path, "amputada.png", amputada))

    # Las globales apenas se inmutan...
    assert r["mae"] < 5, "el area afectada es pequeña; la media no deberia dispararse"
    # ...pero las locales lo delatan.
    assert r["max_absolute_error"] > 50, "el peor pixel debe reflejar el borrado"
    assert r["local"]["worst_tile_mae"] > 10, "el peor bloque debe delatar la zona"
    assert r["local"]["tiles_over_10"] >= 1
    assert 0 < r["changed_pixel_ratio"] < 0.10


def test_a_uniform_change_moves_the_global_metrics(tmp_path, referencia):
    """Un recoloreado general si mueve las globales: no todo defecto es local."""
    ruta, base = referencia
    recolor = np.clip(base.astype(np.int16) + 40, 0, 255)

    r = compare_pixels(ruta, guardar(tmp_path, "recolor.png", recolor))

    assert r["mae"] > 10
    assert r["changed_pixel_ratio"] > 0.9
    assert r["local"]["tiles_over_10"] == r["local"]["tiles_evaluated"], (
        "un cambio uniforme debe afectar a todos los bloques"
    )


def test_a_mask_confines_the_measurement_to_the_product(tmp_path, referencia):
    """Un cambio SOLO en el fondo no puede penalizar al producto."""
    ruta, base = referencia
    mask = np.zeros((LADO, LADO), dtype=bool)
    mask[50:150, 50:150] = True              # el producto vive en el centro
    ruta_mask = tmp_path / "mask.png"
    Image.fromarray((mask * 255).astype(np.uint8), mode="L").save(ruta_mask)

    solo_fondo = base.copy()
    solo_fondo[:40, :] = 0                   # se altera solo fuera de la mascara

    r = compare_pixels(ruta, guardar(tmp_path, "fondo.png", solo_fondo), ruta_mask)

    assert r["mae"] == 0.0, "el cambio esta fuera de la mascara"
    assert r["local"]["worst_tile_mae"] == 0.0, (
        "el peor bloque no puede contaminarse con diferencias legitimas de fondo"
    )


def test_the_report_keeps_the_previous_fields(tmp_path, referencia):
    """Las claves anteriores siguen ahi: nadie que ya las lea se rompe."""
    ruta, base = referencia
    r = compare_pixels(ruta, guardar(tmp_path, "copia.png", base))
    for clave in ("mae", "rmse", "p95_absolute_error", "evaluated_values"):
        assert clave in r, f"falta la clave previa {clave}"
