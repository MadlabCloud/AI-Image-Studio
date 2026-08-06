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


MCP_CHECK_NAME = "MCP opcional"

# Estados posibles del diagnostico MCP. El comando doctor debe distinguirlos:
#   absent              el paquete opcional no esta instalado (no es un fallo)
#   incompatible        el paquete existe pero no expone mcp.server.fastmcp
#   import_error        mcp.server.fastmcp existe pero falla al importarse
#   build_error         FastMCP importa pero el servidor no se puede construir
#   ok                  el servidor se construye correctamente
MCP_STATES = ("absent", "incompatible", "import_error", "build_error", "ok")


def _installed_version(distribution: str) -> str | None:
    try:
        from importlib.metadata import PackageNotFoundError, version
    except ImportError:  # pragma: no cover - Python < 3.8
        return None
    try:
        return version(distribution)
    except PackageNotFoundError:
        return None
    except Exception:  # pragma: no cover - metadata corrupta
        return None


def mcp_capability(build: bool = True) -> dict:
    """Diagnostica la capacidad MCP de forma real, sin arrancar ningun proceso.

    Comprueba en orden: presencia del paquete, disponibilidad de
    ``mcp.server.fastmcp.FastMCP``, y construccion del servidor en memoria.
    Devuelve siempre uno de los estados de ``MCP_STATES``.
    """
    if importlib.util.find_spec("mcp") is None:
        return {
            "state": "absent",
            "installed": False,
            "version": None,
            "usable": False,
            "detail": "no instalado; capacidad opcional. Instalalo con: pip install \"ai-image-studio[mcp]\"",
        }

    installed_version = _installed_version("mcp")
    shown = installed_version or "desconocida"

    try:
        fastmcp_spec = importlib.util.find_spec("mcp.server.fastmcp")
    except Exception as exc:  # el propio find_spec puede fallar si mcp esta roto
        return {
            "state": "import_error",
            "installed": True,
            "version": installed_version,
            "usable": False,
            "detail": f"mcp {shown} instalado pero mcp.server.fastmcp no se puede resolver: {type(exc).__name__}: {exc}",
        }

    if fastmcp_spec is None:
        return {
            "state": "incompatible",
            "installed": True,
            "version": installed_version,
            "usable": False,
            "detail": (
                f"mcp {shown} instalado pero INCOMPATIBLE: no expone mcp.server.fastmcp. "
                "Requiere mcp>=1.14,<2. Reinstala con: pip install \"mcp>=1.14,<2\""
            ),
        }

    try:
        from mcp.server.fastmcp import FastMCP  # noqa: F401
    except Exception as exc:
        return {
            "state": "import_error",
            "installed": True,
            "version": installed_version,
            "usable": False,
            "detail": f"mcp {shown} instalado pero fallo al importar FastMCP: {type(exc).__name__}: {exc}",
        }

    if not build:
        return {
            "state": "ok",
            "installed": True,
            "version": installed_version,
            "usable": True,
            "detail": f"mcp {shown}; FastMCP importable (construccion del servidor no verificada)",
        }

    try:
        # Importacion diferida: mcp_server importa este modulo.
        from .mcp_server import build_server

        server = build_server()
    except Exception as exc:
        return {
            "state": "build_error",
            "installed": True,
            "version": installed_version,
            "usable": False,
            "detail": (
                f"mcp {shown}: FastMCP importa pero el servidor no se puede construir: "
                f"{type(exc).__name__}: {exc}"
            ),
        }

    tools = None
    manager = getattr(server, "_tool_manager", None)
    if manager is not None:
        try:
            tools = len(manager.list_tools())
        except Exception:  # pragma: no cover - API interna opcional
            tools = None
    suffix = f"; {tools} herramientas expuestas" if tools is not None else ""
    return {
        "state": "ok",
        "installed": True,
        "version": installed_version,
        "usable": True,
        "detail": f"mcp {shown}; servidor construido correctamente{suffix}",
    }


def _mcp_check(build: bool = True) -> tuple[dict, dict]:
    """Devuelve (check, capability). El check es critico solo si mcp esta instalado y roto."""
    capability = mcp_capability(build=build)
    if capability["state"] == "absent":
        status, critical = "INFO", False
    elif capability["state"] == "ok":
        status, critical = "PASS", False
    else:
        # Capacidad declarada como instalada que no puede funcionar: fallo real.
        status, critical = "FAIL", True
    return _check(MCP_CHECK_NAME, status, capability["detail"], critical), capability


def _skill_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for p in path.iterdir() if p.is_dir() and (p / "SKILL.md").is_file())


def system_doctor(workspace: str | None = None, build_mcp_server: bool = True) -> dict:
    checks: list[dict] = []
    py_ok = sys.version_info >= (3, 10)
    checks.append(_check("Python >= 3.10", "PASS" if py_ok else "FAIL", platform.python_version(), True))
    checks.extend([
        _module_check("PIL", "Pillow", True),
        _module_check("numpy", "NumPy", True),
        _module_check("jsonschema", "jsonschema", True),
    ])
    mcp_check, mcp_capability_report = _mcp_check(build=build_mcp_server)
    checks.append(mcp_check)

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
        "mcp": mcp_capability_report,
        "ready": not failures,
        "critical_failures": [c["name"] for c in failures],
        "notes": [
            "La ausencia de motores RAW o ExifTool no impide usar las skills ni las funciones básicas.",
            "MCP es opcional: si no está instalado no es un fallo, pero si está instalado y no puede funcionar sí lo es.",
            "No se realizan conexiones de red durante este diagnóstico.",
        ],
    }
