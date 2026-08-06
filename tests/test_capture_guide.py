import json
from pathlib import Path

from ai_image_studio.capture_guide import (
    recommend_capture,
    resolve_mobile_support,
    validate_capture_request,
)

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))


def test_fragrance_profile_and_current_iphone_support():
    req = load("capture-product-fragrance-iphone17pro.json")
    validate_capture_request(req)
    plan = recommend_capture(req)
    assert plan["profile_id"] == "product-fragrance-glass"
    assert plan["smartphone"]["support"]["generation"] == "iPhone 17"
    assert plan["smartphone"]["support"]["mode"] == "supported_generation_exact_model"


def test_wedding_night_profile():
    plan = recommend_capture(load("capture-wedding-night-camera.json"))
    assert plan["profile_id"] == "wedding-night"
    assert "1/200" in plan["camera"]["shutter"]


def test_old_mobile_uses_generic_only():
    device = {"kind": "smartphone", "brand": "Apple", "model": "iPhone 15 Pro", "controls": "partial", "raw_capability": "yes"}
    support = resolve_mobile_support(device)
    assert support["mode"] == "generic_only"


def test_capture_plan_has_mandatory_test_warning():
    plan = recommend_capture(load("capture-product-fragrance-iphone17pro.json"))
    assert any("toma de prueba" in warning for warning in plan["warnings"])
