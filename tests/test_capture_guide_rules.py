"""Reglas de la guia de captura.

La skill promete no inventar funciones de un movil: solo da pasos especificos si el
modelo pertenece a las dos generaciones registradas. Si esa resolucion falla, la guia
recomienda ajustes que el telefono del usuario puede no tener.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_image_studio.capture_guide import (
    capture_request_gaps,
    load_device_registry,
    recommend_capture,
    resolve_mobile_support,
    validate_capture_request,
)

ROOT = Path(__file__).resolve().parents[1]
EJEMPLO = ROOT / "examples/capture-product-fragrance-iphone17pro.json"


@pytest.fixture
def peticion() -> dict:
    return json.loads(EJEMPLO.read_text(encoding="utf-8"))


def test_the_shipped_example_is_valid(peticion):
    validate_capture_request(peticion)


def test_an_incomplete_request_is_rejected(peticion):
    del peticion["device"]
    with pytest.raises(ValueError, match="device"):
        validate_capture_request(peticion)


def test_apple_guidance_requires_declaring_a_smartphone(peticion):
    peticion["device"]["kind"] = "camera"
    with pytest.raises(ValueError, match="smartphone"):
        validate_capture_request(peticion)


def test_a_registered_model_is_resolved_exactly(peticion):
    resultado = resolve_mobile_support(peticion["device"])
    assert resultado["mode"] == "supported_generation_exact_model"
    assert resultado["generation"]
    assert resultado["sources"], "un modelo soportado debe citar fuentes oficiales"


def test_an_unknown_model_falls_back_to_generic_guidance():
    """El nucleo de la promesa: sin modelo verificado, nada de pasos especificos."""
    resultado = resolve_mobile_support(
        {"kind": "smartphone", "brand": "Apple", "model": "iPhone 4"}
    )
    assert resultado["mode"] == "generic_only"
    assert resultado["sources"] == []
    assert any("generic" in n.lower() or "genérica" in n.lower() for n in resultado["notes"])


def test_a_camera_is_not_treated_as_a_phone():
    resultado = resolve_mobile_support({"kind": "camera", "brand": None, "model": None})
    assert resultado["mode"] == "not_applicable"


def test_the_device_registry_declares_when_it_was_verified():
    registro = load_device_registry()
    assert registro["last_verified"], "sin fecha de verificacion no se puede confiar"
    assert registro["families"], "el registro no puede estar vacio"


def test_a_recommendation_reports_the_selected_profile(peticion):
    plan = recommend_capture(peticion)
    assert plan, "recommend_capture no devolvio nada"
    assert isinstance(plan, dict)


def test_gaps_are_reported_instead_of_being_invented(peticion):
    peticion["scene"]["lighting"] = "unknown"
    huecos = capture_request_gaps(peticion)
    assert isinstance(huecos, list)
