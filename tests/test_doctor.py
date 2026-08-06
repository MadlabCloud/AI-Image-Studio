import importlib.util

import pytest

from ai_image_studio import doctor as doctor_module
from ai_image_studio.doctor import (
    MCP_CHECK_NAME,
    MCP_STATES,
    mcp_capability,
    system_doctor,
)

_FASTMCP_SKIP_REASON = "requiere un mcp funcional (mcp>=1.14,<2) instalado"


def _fastmcp_available() -> bool:
    """Cierto solo si el servidor MCP puede construirse de verdad.

    No basta con que el paquete ``mcp`` este instalado: mcp 2.x lo esta y aun asi
    carece de ``mcp.server.fastmcp``. Las pruebas que asumen un MCP operativo deben
    omitirse en ese caso; quien debe fallar es la suite de dependencias.
    """
    return mcp_capability(build=True)["state"] == "ok"


def _mcp_check(report):
    return next(check for check in report["checks"] if check["name"] == MCP_CHECK_NAME)


def test_doctor_reports_ready(tmp_path):
    report = system_doctor(str(tmp_path / "workspace"))
    assert report["ai_image_studio_version"] == "0.5.1"
    assert any(
        check["name"] == "Workspace escribible" and check["status"] == "PASS"
        for check in report["checks"]
    )
    # ready solo puede ser False por una capacidad realmente rota; en un entorno de
    # pruebas sano las dependencias obligatorias estan presentes.
    assert report["critical_failures"] in ([], [MCP_CHECK_NAME])


def test_mcp_capability_state_is_always_known():
    assert mcp_capability(build=False)["state"] in MCP_STATES


def test_doctor_exposes_mcp_capability_detail(tmp_path):
    report = system_doctor(str(tmp_path / "workspace"))
    assert report["mcp"]["state"] in MCP_STATES
    assert report["mcp"]["detail"]


# --- Escenario: dependencia ausente -------------------------------------------------

def test_absent_mcp_is_informational_and_keeps_ready_true(tmp_path, monkeypatch):
    real_find_spec = importlib.util.find_spec

    def fake_find_spec(name, *args, **kwargs):
        if name == "mcp":
            return None
        return real_find_spec(name, *args, **kwargs)

    monkeypatch.setattr(doctor_module.importlib.util, "find_spec", fake_find_spec)
    report = system_doctor(str(tmp_path / "workspace"))
    check = _mcp_check(report)
    assert report["mcp"]["state"] == "absent"
    assert check["status"] == "INFO"
    assert check["critical"] is False
    assert report["ready"] is True, "una capacidad opcional ausente no puede romper el diagnostico"


# --- Escenario: version incompatible ------------------------------------------------

def test_incompatible_mcp_fails_and_forces_ready_false(tmp_path, monkeypatch):
    """Reproduce mcp 2.x: el paquete existe pero no expone mcp.server.fastmcp."""
    real_find_spec = importlib.util.find_spec

    def fake_find_spec(name, *args, **kwargs):
        if name == "mcp":
            return object()  # el paquete "esta instalado"
        if name == "mcp.server.fastmcp":
            return None  # pero no publica el submodulo
        return real_find_spec(name, *args, **kwargs)

    monkeypatch.setattr(doctor_module.importlib.util, "find_spec", fake_find_spec)
    monkeypatch.setattr(doctor_module, "_installed_version", lambda dist: "2.0.0")

    report = system_doctor(str(tmp_path / "workspace"))
    check = _mcp_check(report)
    assert report["mcp"]["state"] == "incompatible"
    assert report["mcp"]["usable"] is False
    assert check["status"] == "FAIL"
    assert check["critical"] is True
    assert report["ready"] is False, "ready no puede ser true con MCP instalado e inservible"
    assert MCP_CHECK_NAME in report["critical_failures"]
    assert "2.0.0" in check["detail"] and "mcp>=1.14,<2" in check["detail"]


# --- Escenario: error de importacion ------------------------------------------------

def test_import_error_is_reported_as_failure(tmp_path, monkeypatch):
    real_find_spec = importlib.util.find_spec

    def fake_find_spec(name, *args, **kwargs):
        if name == "mcp":
            return object()
        if name == "mcp.server.fastmcp":
            raise ImportError("submodulo corrupto")
        return real_find_spec(name, *args, **kwargs)

    monkeypatch.setattr(doctor_module.importlib.util, "find_spec", fake_find_spec)
    monkeypatch.setattr(doctor_module, "_installed_version", lambda dist: "1.20.0")

    report = system_doctor(str(tmp_path / "workspace"))
    check = _mcp_check(report)
    assert report["mcp"]["state"] == "import_error"
    assert check["status"] == "FAIL"
    assert check["critical"] is True
    assert report["ready"] is False
    assert "submodulo corrupto" in check["detail"]


# --- Escenario: error al construir el servidor --------------------------------------

@pytest.mark.skipif(not _fastmcp_available(), reason=_FASTMCP_SKIP_REASON)
def test_build_error_is_reported_as_failure(tmp_path, monkeypatch):
    """Reproduce mcp 1.7-1.13: FastMCP importa pero construir el servidor explota."""
    import ai_image_studio.mcp_server as mcp_server

    def exploding_build_server():
        raise TypeError("issubclass() arg 1 must be a class")

    monkeypatch.setattr(mcp_server, "build_server", exploding_build_server)

    report = system_doctor(str(tmp_path / "workspace"))
    check = _mcp_check(report)
    assert report["mcp"]["state"] == "build_error"
    assert check["status"] == "FAIL"
    assert check["critical"] is True
    assert report["ready"] is False
    assert "issubclass()" in check["detail"]


# --- Escenario: todo correcto -------------------------------------------------------

@pytest.mark.skipif(not _fastmcp_available(), reason=_FASTMCP_SKIP_REASON)
def test_working_mcp_passes_and_keeps_ready_true(tmp_path):
    report = system_doctor(str(tmp_path / "workspace"))
    check = _mcp_check(report)
    assert report["mcp"]["state"] == "ok"
    assert report["mcp"]["usable"] is True
    assert check["status"] == "PASS"
    assert check["critical"] is False
    assert report["ready"] is True


def test_build_can_be_skipped_for_fast_diagnostics(tmp_path):
    report = system_doctor(str(tmp_path / "workspace"), build_mcp_server=False)
    assert report["mcp"]["state"] in MCP_STATES
