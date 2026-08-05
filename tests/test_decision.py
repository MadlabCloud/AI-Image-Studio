import json
from pathlib import Path
import pytest
from ai_image_studio.decision import validate_decision, decision_gaps, route_decision

ROOT = Path(__file__).resolve().parents[1]

def load(name):
    return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))

def test_product_catalog_decision_valid():
    decision = load("job-product-strict.json")["decision"]
    validate_decision(decision)
    route = route_decision(decision)
    assert route["primary_skill"] == "product-image-pipeline"
    assert route["implementation_status"] == "implemented"
    assert route["specialized_pipeline_available"] is True
    assert route["environment_requested"] is False

def test_environment_requires_context_or_recommendation():
    decision = load("decision-product-environment.json")
    decision["outputs"]["environment"]["recommendations_requested"] = False
    with pytest.raises(ValueError, match="requiere contexto"):
        validate_decision(decision)

def test_product_background_policy_rejected_for_portrait():
    decision = load("job-product-strict.json")["decision"]
    decision["category"]["type"] = "portrait"
    with pytest.raises(ValueError, match="solo se permiten"):
        validate_decision(decision)

def test_unknown_capture_is_valid_and_creates_gap_when_guidance_requested():
    decision = load("job-product-strict.json")["decision"]
    decision["capture"]["guidance_requested"] = True
    decision["capture"]["device"]["kind"] = "unknown"
    decision["capture"]["scenario"]["lighting"] = "unknown"
    gaps = decision_gaps(decision)
    fields = {g["field"] for g in gaps}
    assert "capture.device.kind" in fields
    assert "capture.scenario.lighting" in fields

def test_guidance_routes_to_photographer_skill():
    decision = load("job-product-strict.json")["decision"]
    decision["capture"]["guidance_requested"] = True
    route = route_decision(decision)
    assert route["capture_guidance_requested"] is True
    assert "photographer-capture-guide" in route["secondary_skills"]

def test_unimplemented_category_stays_in_router():
    decision = load("job-product-strict.json")["decision"]
    decision["category"]["type"] = "portrait"
    decision["category"]["subtype"] = "cv"
    decision["background"] = {
        "relevance": "important",
        "policy": "preserve",
        "original_type": "real_environment",
        "target_mode": "preserve",
        "target_value": None,
        "profile_id": None,
        "shadow": "preserve"
    }
    route = route_decision(decision)
    assert route["primary_skill"] == "image-intake-router"
    assert route["implementation_status"] == "planned"
    assert route["specialized_pipeline_available"] is False
