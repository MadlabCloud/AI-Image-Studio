from __future__ import annotations

from importlib.resources import files
import json
from jsonschema import Draft202012Validator

PRODUCT_ENV_DESTINATIONS = {
    "own_web", "ecommerce_platform", "marketplace", "social_media", "advertising"
}
PRODUCT_BACKGROUND_POLICIES = {"product_catalog", "product_environment"}


def load_decision_schema() -> dict:
    resource = files("ai_image_studio").joinpath("schemas/universal-decision.schema.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def validate_decision(decision: dict) -> None:
    validator = Draft202012Validator(load_decision_schema())
    errors = sorted(validator.iter_errors(decision), key=lambda e: list(e.path))
    if errors:
        message = "; ".join(
            f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errors
        )
        raise ValueError(message)

    category = decision["category"]["type"]
    destination = decision["destination"]["primary"]
    background = decision["background"]
    outputs = decision["outputs"]
    environment = outputs["environment"]

    if category != "product" and background["policy"] in PRODUCT_BACKGROUND_POLICIES:
        raise ValueError("Las políticas product_catalog/product_environment solo se permiten para category=product")

    if background["target_mode"] == "generate_environment" and category != "product":
        raise ValueError("generate_environment solo se permite para category=product")

    requested_environment = "environment" in outputs["requested"]
    if environment["requested"] != requested_environment:
        raise ValueError("outputs.environment.requested debe coincidir con la presencia de 'environment' en outputs.requested")

    if requested_environment:
        if category != "product":
            raise ValueError("La salida environment de esta versión solo se permite para productos")
        if destination not in PRODUCT_ENV_DESTINATIONS:
            raise ValueError("La salida environment requiere un destino web, marketplace, social o publicitario")
        has_context = bool(environment.get("description")) or bool(environment.get("reference_paths"))
        if not has_context and not environment.get("recommendations_requested"):
            raise ValueError("La imagen de ambiente requiere contexto, referencia o recommendations_requested=true")
        if environment["context_source"] == "none" and has_context:
            raise ValueError("context_source=none no puede incluir descripción o referencias")

    if background["relevance"] == "not_applicable":
        if background["policy"] != "not_applicable" or background["target_mode"] != "not_applicable":
            raise ValueError("background not_applicable exige policy y target_mode not_applicable")

    if background["target_mode"] == "solid" and not background.get("target_value"):
        raise ValueError("background.target_mode=solid exige target_value")


def decision_gaps(decision: dict) -> list[dict]:
    """Devuelve preguntas recomendadas; los valores unknown son válidos, no errores."""
    validate_decision(decision)
    gaps: list[dict] = []
    if decision["destination"]["primary"] == "unknown":
        gaps.append({"field": "destination.primary", "priority": "high", "question": "¿Dónde se utilizará la imagen?"})
    if decision["capture"]["guidance_requested"] and decision["capture"]["device"]["kind"] == "unknown":
        gaps.append({"field": "capture.device.kind", "priority": "high", "question": "¿Se fotografiará con cámara, móvil u otro dispositivo?"})
    if decision["capture"]["guidance_requested"] and decision["capture"]["scenario"]["lighting"] == "unknown":
        gaps.append({"field": "capture.scenario.lighting", "priority": "high", "question": "¿Qué iluminación habrá durante la captura?"})
    if decision["destination"]["requirements_known"] is False:
        gaps.append({"field": "destination.requirements_known", "priority": "medium", "question": "¿Quieres que se recomienden requisitos de salida para ese canal?"})
    if decision["background"]["policy"] == "custom" and not decision["background"].get("profile_id"):
        gaps.append({"field": "background.profile_id", "priority": "medium", "question": "¿Qué perfil visual o reglas de fondo debe seguirse?"})
    env = decision["outputs"]["environment"]
    if env["requested"] and env["recommendations_requested"] and not env.get("description") and not env.get("reference_paths"):
        gaps.append({"field": "outputs.environment", "priority": "medium", "question": "¿Quieres propuestas de ambiente basadas en producto, canal y público?"})
    return gaps


def route_decision(decision: dict) -> dict:
    validate_decision(decision)
    category = decision["category"]["type"]
    routes = {
        "product": "product-image-pipeline",
        "portrait": "portrait-image-pipeline",
        "event": "event-image-pipeline",
        "travel": "travel-image-pipeline",
        "architecture": "architecture-image-pipeline",
        "real_estate": "real-estate-image-pipeline",
        "food": "food-image-pipeline",
        "restoration": "restoration-image-pipeline",
        "document": "document-image-pipeline",
        "creative": "creative-image-pipeline",
        "other": "image-intake-router",
    }
    secondary_skills = []
    if decision["capture"]["guidance_requested"]:
        secondary_skills.append("photographer-capture-guide")
    return {
        "category": category,
        "primary_skill": routes[category],
        "secondary_skills": secondary_skills,
        "capture_guidance_requested": decision["capture"]["guidance_requested"],
        "background_policy": decision["background"]["policy"],
        "environment_requested": decision["outputs"]["environment"]["requested"],
        "gaps": decision_gaps(decision),
    }
