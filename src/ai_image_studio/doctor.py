from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import platform
import shutil
import sys
import tempfile

from . import __version__


def _check(name: str, status: str, detail: str, critical: bool = False) -> dict:
    return {"name": name, "status": status, "detail": detail, "critical": critical}


def _module_check(module: str, label: str, critical: bool) -> dict:
    found = importlib.util.find_spec(module) is not None
    return _check(label, "PASS" if found else ("FAIL" if critical else "INFO"), "instalado" if found else "no instalado", critical)


def _skill_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for p in path.iterdir() if p.is_dir() and (p / "SKILL.md").is_file())


def system_doctor(workspace: str | None = None) -> dict:
    checks: list[dict] = []
    py_ok = sys.version_info >= (3, 10)
    checks.append(_check("Python >= 3.10", "PASS" if py_ok else "FAIL", platform.python_version(), True))
    checks.extend([
        _module_check("PIL", "Pillow", True),
        _module_check("numpy", "NumPy", True),
        _module_check("jsonschema", "jsonschema", True),
        _module_check("mcp", "MCP opcional", False),
    ])

    target = Path(workspace or (Path(tempfile.gettempdir()) / "ai-image-studio-doctor")).expanduser().resolve()
    writable = False
    detail = str(target)
    try:
        target.mkdir(parents=True, exist_ok=True)
        probe = target / ".write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        writable = True
    except Exception as exc:  # pragma: no cover - platform dependent
        detail = f"{target}: {exc}"
    checks.append(_check("Workspace escribible", "PASS" if writable else "FAIL", detail, True))

    home = Path.home()
    claude_dir = home / ".claude" / "skills"
    codex_dir = home / ".agents" / "skills"
    checks.append(_check("Skills Claude Code", "INFO", f"{_skill_count(claude_dir)} skills en {claude_dir}"))
    checks.append(_check("Skills Codex", "INFO", f"{_skill_count(codex_dir)} skills en {codex_dir}"))

    for executable, label in [
        ("exiftool", "ExifTool"),
        ("darktable-cli", "darktable-cli"),
        ("rawtherapee-cli", "RawTherapee CLI"),
        ("magick", "ImageMagick"),
    ]:
        path = shutil.which(executable)
        checks.append(_check(label, "INFO", path or "no instalado; motor opcional"))

    failures = [c for c in checks if c["critical"] and c["status"] == "FAIL"]
    return {
        "ai_image_studio_version": __version__,
        "platform": {"system": platform.system(), "release": platform.release(), "machine": platform.machine()},
        "python_executable": sys.executable,
        "checks": checks,
        "ready": not failures,
        "critical_failures": [c["name"] for c in failures],
        "notes": [
            "La ausencia de motores RAW o ExifTool no impide usar las skills ni las funciones básicas.",
            "No se realizan conexiones de red durante este diagnóstico.",
        ],
    }
