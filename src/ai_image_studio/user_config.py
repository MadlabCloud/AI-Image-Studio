from __future__ import annotations

import json
import os
import re
from importlib.resources import files
from pathlib import Path

from jsonschema import Draft202012Validator

ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")


def load_user_config_schema() -> dict:
    resource = files("ai_image_studio").joinpath("schemas/user-config.schema.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def default_user_config(workspace_root: str | None = None, language: str = "es") -> dict:
    root = Path(workspace_root or (Path.home() / "AI-Image-Studio")).expanduser()
    return {
        "schema_version": "0.4.0",
        "language": language,
        "workspace_root": str(root),
        "installation": {"mode": "development", "primary_platform": "unknown"},
        "privacy": {
            "preserve_originals": True,
            "allow_external_uploads": False,
            "strip_metadata_web": True,
            "log_file_paths": False,
        },
        "defaults": {
            "fidelity": "strict",
            "ask_before_edit": True,
            "human_review_on_uncertainty": True,
            "fail_closed": True,
        },
        "paths": {
            "exports": "exports",
            "cache": ".cache",
            "logs": "logs",
        },
        "external_services": [],
    }


def validate_user_config(config: dict) -> None:
    validator = Draft202012Validator(load_user_config_schema())
    errors = sorted(validator.iter_errors(config), key=lambda e: list(e.path))
    if errors:
        message = "; ".join(
            f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errors
        )
        raise ValueError(message)

    allow_external = config["privacy"]["allow_external_uploads"]
    for service in config["external_services"]:
        auth_env = service.get("auth_env")
        if auth_env and not ENV_NAME.fullmatch(auth_env):
            raise ValueError(f"external_services/{service['name']}/auth_env debe ser el nombre de una variable de entorno")
        if service["enabled"] and not allow_external:
            raise ValueError("No puede habilitarse un servicio externo si privacy.allow_external_uploads=false")
        if service["enabled"] and not service["data_policy_acknowledged"]:
            raise ValueError(f"El servicio {service['name']} exige data_policy_acknowledged=true")


def write_default_user_config(destination: str, workspace_root: str | None = None, language: str = "es", overwrite: bool = False) -> dict:
    dest = Path(destination).expanduser().resolve()
    if dest.exists() and not overwrite:
        raise FileExistsError(f"El archivo ya existe: {dest}")
    config = default_user_config(workspace_root=workspace_root, language=language)
    validate_user_config(config)
    dest.parent.mkdir(parents=True, exist_ok=True)
    temp = dest.with_suffix(dest.suffix + ".tmp")
    temp.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temp, dest)
    return {"path": str(dest), "config": config}


def read_and_validate_user_config(path: str) -> dict:
    source = Path(path).expanduser().resolve()
    # utf-8-sig: acepta el BOM que escriben por defecto el Bloc de notas y PowerShell.
    config = json.loads(source.read_text(encoding="utf-8-sig"))
    validate_user_config(config)
    return {"valid": True, "path": str(source), "config": config}
