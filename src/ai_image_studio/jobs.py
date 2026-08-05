from __future__ import annotations
from pathlib import Path
from importlib.resources import files
from datetime import datetime, timezone
import json, shutil
from jsonschema import Draft202012Validator
from .hashing import sha256_file, safe_filename
from .decision import validate_decision

TRANSITIONS = {
    "RECEIVED": {"INSPECTED", "REJECTED"},
    "INSPECTED": {"CLASSIFIED", "NEEDS_NEW_CAPTURE", "REJECTED"},
    "CLASSIFIED": {"SPEC_LOCKED", "REJECTED"},
    "SPEC_LOCKED": {"SOURCE_PRESERVED", "REJECTED"},
    "SOURCE_PRESERVED": {"PROCESSED", "NEEDS_REVIEW", "REJECTED"},
    "PROCESSED": {"AUTOMATIC_QC", "NEEDS_REVIEW", "REJECTED"},
    "AUTOMATIC_QC": {"HUMAN_QC", "APPROVED", "NEEDS_REVIEW", "REJECTED"},
    "HUMAN_QC": {"APPROVED", "REJECTED", "NEEDS_NEW_CAPTURE"},
    "APPROVED": {"EXPORTED"},
    "EXPORTED": {"PACKAGED"},
    "NEEDS_REVIEW": {"HUMAN_QC", "REJECTED", "PROCESSED"},
    "REJECTED": set(), "NEEDS_NEW_CAPTURE": set(), "PACKAGED": set(),
}

def load_schema() -> dict:
    resource = files("ai_image_studio").joinpath("schemas/image-job.schema.json")
    return json.loads(resource.read_text(encoding="utf-8"))

def validate_job(job: dict) -> None:
    validator = Draft202012Validator(load_schema())
    errors = sorted(validator.iter_errors(job), key=lambda e: list(e.path))
    if errors:
        message = "; ".join(f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errors)
        raise ValueError(message)
    allowed = set(job["allowed_operations"])
    forbidden = set(job["forbidden_operations"])
    overlap = allowed & forbidden
    if overlap:
        raise ValueError(f"Operaciones permitidas y prohibidas a la vez: {sorted(overlap)}")
    if job["fidelity"] == "strict" and "full_image_generation" not in forbidden:
        raise ValueError("Fidelidad strict exige prohibir full_image_generation")
    validate_decision(job["decision"])
    if job["category"] != job["decision"]["category"]["type"]:
        raise ValueError("category debe coincidir con decision.category.type")
    if job["fidelity"] != job["decision"]["fidelity"]:
        raise ValueError("fidelity debe coincidir con decision.fidelity")

def transition(current: str, target: str) -> None:
    if target not in TRANSITIONS.get(current, set()):
        raise ValueError(f"Transición no permitida: {current} -> {target}")

def prepare_job(job: dict, workspace: str | Path) -> dict:
    source = Path(job["source"]["path"])
    if not source.is_file():
        raise FileNotFoundError(source)
    actual_hash = sha256_file(source)
    supplied = job["source"].get("sha256")
    if supplied and supplied != actual_hash:
        raise ValueError("El hash del original no coincide")
    job["source"]["sha256"] = actual_hash
    validate_job(job)
    if job.get("status") != "SPEC_LOCKED" or job.get("confirmed") is not True:
        raise ValueError("prepare_job exige status SPEC_LOCKED y confirmed=true")

    ws = Path(workspace) / safe_filename(job["job_id"])
    originals = ws / "00_ORIGINALS"
    originals.mkdir(parents=True, exist_ok=True)
    dst = originals / safe_filename(source.name)
    if dst.exists() and sha256_file(dst) != actual_hash:
        raise FileExistsError(f"Ya existe un original distinto: {dst}")
    if not dst.exists():
        shutil.copy2(source, dst)
    copied_hash = sha256_file(dst)
    if copied_hash != actual_hash:
        raise IOError("La copia inmutable no conserva el hash")

    transition(job["status"], "SOURCE_PRESERVED")
    job["status"] = "SOURCE_PRESERVED"
    lock = {
        "job": job,
        "source_copy": str(dst.resolve()),
        "source_sha256": copied_hash,
        "locked_at": datetime.now(timezone.utc).isoformat(),
    }
    lock_path = ws / "job.lock.json"
    lock_path.write_text(json.dumps(lock, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"workspace": str(ws.resolve()), "lock_path": str(lock_path.resolve()), "source_copy": str(dst.resolve()), "sha256": copied_hash, "status": job["status"]}
