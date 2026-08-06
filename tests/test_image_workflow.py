"""Flujo real con una imagen de prueba y comprobacion de fallo en cerrado.

La imagen se genera en tiempo de ejecucion: es reproducible, no tiene derechos de
autor y no puede filtrar material privado al repositorio ni a los artefactos.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from ai_image_studio.hashing import sha256_file
from ai_image_studio.inspect import inspect_file
from ai_image_studio.jobs import prepare_job

WRONG_SHA256 = "0" * 64


@pytest.fixture
def test_image(tmp_path) -> Path:
    """Imagen JPEG determinista de 640x480 con formas geometricas simples."""
    image = Image.new("RGB", (640, 480), (245, 245, 245))
    draw = ImageDraw.Draw(image)
    draw.rectangle((120, 90, 520, 390), fill=(40, 90, 160))
    draw.ellipse((240, 170, 400, 310), fill=(220, 180, 60))
    path = tmp_path / "muestra-generada.jpg"
    image.save(path, "JPEG", quality=92)
    return path


def _strict_job(source: Path, sha256: str | None = None) -> dict:
    source_block: dict = {"path": str(source), "immutable": True}
    if sha256 is not None:
        source_block["sha256"] = sha256
    return {
        "job_id": "img-fixture-001",
        "category": "product",
        "fidelity": "strict",
        "status": "SPEC_LOCKED",
        "decision": {
            "category": {"type": "product", "subtype": "furniture",
                         "source": "confirmed", "confidence": 1.0},
            "destination": {"primary": "own_web", "platform": "test",
                            "profile_id": "test-web", "requirements_known": True},
            "capture": {
                "device": {"kind": "unknown", "brand": None, "model": None,
                           "metadata_checked": False, "configuration_known": False},
                "source_format": "jpeg",
                "scenario": {"location": "indoor", "lighting": "unknown",
                             "subject_motion": "static", "challenges": []},
                "guidance_requested": False,
            },
            "fidelity": "strict",
            "background": {"relevance": "critical", "policy": "product_catalog",
                           "original_type": "unknown", "target_mode": "solid",
                           "target_value": "#FFFFFF", "profile_id": "test-web",
                           "shadow": "contact-soft"},
            "outputs": {"requested": ["catalog", "web"],
                        "environment": {"requested": False, "context_source": "none",
                                        "description": None, "reference_paths": [],
                                        "recommendations_requested": False}},
        },
        "source": source_block,
        "allowed_operations": ["inspect", "export"],
        "forbidden_operations": ["full_image_generation", "geometry_change"],
        "output": {"width": 1000, "height": 1000, "format": "webp", "quality": 86,
                   "color_space": "sRGB", "remove_metadata": True},
        "confirmed": True,
    }


# --------------------------------------------------------------------------- inspect

def test_inspect_reads_real_image_properties(test_image):
    data = inspect_file(test_image)
    assert data["format"].upper() == "JPEG"
    assert (data["width"], data["height"]) == (640, 480)
    assert data["mode"] == "RGB"
    assert data["sha256"] == sha256_file(test_image)
    assert len(data["sha256"]) == 64


def test_inspect_does_not_modify_the_original(test_image):
    before = sha256_file(test_image)
    inspect_file(test_image)
    assert sha256_file(test_image) == before, "inspect debe ser de solo lectura"


# ----------------------------------------------------------------------- prepare-job

def test_prepare_job_preserves_the_original(test_image, tmp_path):
    original_hash = sha256_file(test_image)
    result = prepare_job(_strict_job(test_image), tmp_path / "workspace")

    assert result["status"] == "SOURCE_PRESERVED"
    assert result["sha256"] == original_hash

    copy = Path(result["source_copy"])
    assert copy.is_file()
    assert copy.parent.name == "00_ORIGINALS"
    assert sha256_file(copy) == original_hash, "la copia inmutable cambio de hash"
    assert sha256_file(test_image) == original_hash, "el original fue modificado"

    lock = json.loads(Path(result["lock_path"]).read_text(encoding="utf-8"))
    assert lock["source_sha256"] == original_hash
    assert lock["job"]["source"]["immutable"] is True
    assert lock["job"]["status"] == "SOURCE_PRESERVED"


def test_prepare_job_accepts_a_correct_declared_hash(test_image, tmp_path):
    correct = sha256_file(test_image)
    result = prepare_job(_strict_job(test_image, correct), tmp_path / "workspace")
    assert result["sha256"] == correct


# ------------------------------------------------------------------- fallo en cerrado

def test_prepare_job_fails_closed_on_wrong_sha256(test_image, tmp_path):
    """Requisito de seguridad: un hash declarado incorrecto detiene el trabajo."""
    workspace = tmp_path / "workspace"
    with pytest.raises(ValueError, match="hash"):
        prepare_job(_strict_job(test_image, WRONG_SHA256), workspace)
    assert not workspace.exists(), "no debe crearse workspace si el hash no coincide"


def test_prepare_job_fails_closed_on_missing_source(tmp_path):
    job = _strict_job(tmp_path / "no-existe.jpg")
    with pytest.raises(FileNotFoundError):
        prepare_job(job, tmp_path / "workspace")


def test_prepare_job_rejects_a_different_original_in_the_workspace(test_image, tmp_path):
    """Si ya hay un original distinto con el mismo nombre, no se sobrescribe."""
    workspace = tmp_path / "workspace"
    prepare_job(_strict_job(test_image), workspace)

    other = Image.new("RGB", (640, 480), (10, 10, 10))
    other.save(test_image, "JPEG", quality=92)

    with pytest.raises(FileExistsError):
        prepare_job(_strict_job(test_image), workspace)
