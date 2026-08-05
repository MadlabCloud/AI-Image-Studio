from __future__ import annotations

from importlib.resources import files
import json
import re
from jsonschema import Draft202012Validator


def _load_json(relative: str) -> dict:
    return json.loads(files("ai_image_studio").joinpath(relative).read_text(encoding="utf-8"))


def load_capture_request_schema() -> dict:
    return _load_json("schemas/capture-guide-request.schema.json")


def load_capture_plan_schema() -> dict:
    return _load_json("schemas/capture-plan.schema.json")


def load_device_registry() -> dict:
    return _load_json("data/device-registry.json")


def load_capture_profiles() -> list[dict]:
    return _load_json("data/capture-profiles.json")["profiles"]


def validate_capture_request(request: dict) -> None:
    validator = Draft202012Validator(load_capture_request_schema())
    errors = sorted(validator.iter_errors(request), key=lambda e: list(e.path))
    if errors:
        message = "; ".join(
            f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errors
        )
        raise ValueError(message)

    if request["device"]["kind"] != "smartphone" and request["device"]["brand"] in {"Apple", "Samsung"}:
        raise ValueError("Apple/Samsung mobile guidance requires device.kind=smartphone")
    if request["category"] != "event" and request["subject"]["people_count"] > 1 and request["scene"]["subject_motion"] == "fast":
        # Valid, but intentionally no error: group sports/other scenarios can exist.
        pass


def _norm(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def resolve_mobile_support(device: dict) -> dict:
    if device["kind"] != "smartphone":
        return {"mode": "not_applicable", "generation": None, "sources": [], "notes": []}
    brand = _norm(device.get("brand"))
    model = _norm(device.get("model"))
    registry = load_device_registry()
    for family in registry["families"]:
        if _norm(family["brand"]) != brand:
            continue
        if any(token in model for token in family["match_tokens"]):
            exact = any(_norm(m) == model for m in family["models"])
            return {
                "mode": "supported_generation_exact_model" if exact else "supported_generation_model_unverified",
                "generation": family["generation"],
                "sources": family["official_sources"],
                "notes": family["capability_notes"],
                "last_verified": registry["last_verified"],
            }
    return {
        "mode": "generic_only",
        "generation": None,
        "sources": [],
        "notes": ["El modelo no pertenece a las dos generaciones móviles mantenidas; usar guía genérica y no inventar funciones."],
        "last_verified": registry["last_verified"],
    }


def _profile_score(profile: dict, request: dict) -> float:
    if profile["category"] != request["category"]:
        return -100.0
    score = 10.0
    subtype = _norm(request.get("subtype"))
    if subtype and any(_norm(s) in subtype or subtype in _norm(s) for s in profile["subtypes"]):
        score += 6.0
    lighting = request["scene"]["lighting"]
    if profile["id"] == "wedding-night" and lighting in {"night", "low_light", "mixed"}:
        score += 8.0
    if profile["id"] == "wedding-day" and lighting in {"direct_sun", "natural_daylight", "overcast", "golden_hour", "backlit"}:
        score += 8.0
    challenges = set(request["scene"]["challenges"])
    if profile["id"] == "product-fragrance-glass" and challenges & {"transparent", "translucent", "reflective", "glossy"}:
        score += 5.0
    if profile["id"] == "product-furniture-studio" and challenges & {"fine_structure", "fabric_texture"}:
        score += 4.0
    return score


def _select_profile(request: dict) -> tuple[dict, float]:
    scored = sorted(((_profile_score(p, request), p) for p in load_capture_profiles()), key=lambda x: x[0], reverse=True)
    score, profile = scored[0]
    if score < 0:
        # Conservative generic fallback based on category.
        return {
            "id": f"generic-{request['category']}", "category": request["category"], "subtypes": [],
            "camera": {"iso": "Usar el ISO práctico más bajo", "aperture": "Elegir según la profundidad de campo necesaria", "shutter": "Elegir según movimiento y estabilidad", "focal_length": "Evitar deformación de perspectiva", "focus": "Comprobar el enfoque crítico", "format": "RAW+JPEG cuando el flujo lo soporte"},
            "smartphone": {"lens": "Usar la cámara principal", "format": "Máxima calidad", "stability": "Estabilizar cuando sea posible", "exposure": "Proteger las altas luces"},
            "lighting": ["Usar la fuente controlable más grande y suave disponible"],
            "composition": ["Comprobar bordes, fondo y perspectiva"],
            "shot_list": ["plano general", "vista principal", "details"],
            "preflight": ["Limpiar objetivo y sujeto", "Hacer una toma de prueba y revisar al 100 %"],
            "warnings": ["Los ajustes son puntos de partida; medir y probar en la escena real"]
        }, 0.45
    confidence = min(0.98, 0.55 + max(0.0, score - 10.0) * 0.04)
    return profile, confidence


def capture_request_gaps(request: dict) -> list[str]:
    validate_capture_request(request)
    questions: list[str] = []
    if request["subtype"] is None:
        questions.append("¿Qué tipo concreto de producto, retrato, evento o escena vas a fotografiar?")
    if request["device"]["kind"] == "unknown":
        questions.append("¿Usarás cámara, iPhone, Samsung Galaxy u otro dispositivo?")
    if request["scene"]["lighting"] == "unknown":
        questions.append("¿Qué luz habrá: estudio, natural, sol directo, interior, noche o mixta?")
    if request["scene"]["subject_motion"] == "unknown":
        questions.append("¿El sujeto estará quieto, caminará o se moverá rápido?")
    if request["destination"] == "unknown":
        questions.append("¿Cuál es el destino final: web, marketplace, publicidad, impresión, CV u otro?")
    return questions[:5]


def recommend_capture(request: dict) -> dict:
    validate_capture_request(request)
    profile, confidence = _select_profile(request)
    mobile = resolve_mobile_support(request["device"])
    assumptions: list[str] = []
    if request["device"]["model"] is None:
        assumptions.append("No se conoce el modelo exacto; no se recomiendan funciones exclusivas de un dispositivo.")
    if request["scene"]["lighting"] == "unknown":
        assumptions.append("La iluminación no está confirmada; los ajustes son orientativos.")
    if request["device"]["kind"] == "camera":
        assumptions.append("La guía de cámara es universal y debe adaptarse al sensor, objetivo y medición reales.")
    warnings = list(profile["warnings"])
    warnings.extend(mobile.get("notes", []))
    warnings.append("Los valores de exposición son puntos de partida: realiza una toma de prueba, revisa histograma, enfoque y altas luces.")
    sources = list(mobile.get("sources", []))
    plan = {
        "profile_id": profile["id"],
        "confidence": round(confidence, 2),
        "assumptions": assumptions,
        "questions": capture_request_gaps(request),
        "camera": profile["camera"] if request["guidance"]["include_settings"] else {},
        "smartphone": ({**profile["smartphone"], "support": mobile} if request["device"]["kind"] == "smartphone" else {}),
        "lighting": profile["lighting"] if request["guidance"]["include_lighting"] else [],
        "composition": profile["composition"],
        "shot_list": profile["shot_list"] if request["guidance"]["include_shot_list"] else [],
        "preflight": profile["preflight"] if request["guidance"]["include_preflight"] else [],
        "warnings": warnings,
        "sources": sources,
    }
    Draft202012Validator(load_capture_plan_schema()).validate(plan)
    return plan
