"""Protege el intervalo de versiones de MCP verificado empiricamente.

Historial que justifica estas comprobaciones (defecto MCP-02 de la validacion v0.5.0):

*   ``mcp < 1.2``      no publica ``mcp.server.fastmcp``.
*   ``mcp 1.7``-``1.13`` importan ``FastMCP`` pero fallan al construir el servidor con
    ``TypeError: issubclass() arg 1 must be a class`` porque no resuelven las
    anotaciones diferidas (``from __future__ import annotations`` + ``str | None``).
*   ``mcp >= 2.0``     elimino ``mcp.server.fastmcp``.

La restriccion declarada debe excluir los tres casos.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FLOOR = (1, 14)
REQUIRED_CEILING = (2,)
KNOWN_BROKEN_RANGE = ((1, 7), (1, 13))  # ambos extremos incluidos


def _parse_version(text: str) -> tuple[int, ...]:
    numbers = re.findall(r"\d+", text.split("+")[0])
    return tuple(int(n) for n in numbers[:3])


def _declared_specifier() -> str:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    extras = data["project"]["optional-dependencies"]["mcp"]
    assert len(extras) == 1, f"Se esperaba una unica dependencia en el extra mcp: {extras}"
    return extras[0]


def test_declared_specifier_has_floor_and_ceiling():
    spec = _declared_specifier()
    assert spec.replace(" ", "").startswith("mcp"), spec

    lower = re.search(r">=\s*([0-9][0-9.]*)", spec)
    upper = re.search(r"<\s*([0-9][0-9.]*)", spec)

    assert lower, f"Falta limite inferior en '{spec}'"
    assert upper, (
        f"Falta limite SUPERIOR en '{spec}'. Sin el, pip puede resolver mcp 2.x, "
        "que no expone mcp.server.fastmcp y deja el servidor inservible."
    )
    assert "==" not in spec, f"No se debe fijar una version exacta: '{spec}'"

    assert _parse_version(lower.group(1)) >= REQUIRED_FLOOR, (
        f"El limite inferior '{lower.group(1)}' permite versiones rotas; "
        f"minimo verificado: {'.'.join(map(str, REQUIRED_FLOOR))}"
    )
    assert _parse_version(upper.group(1)) <= REQUIRED_CEILING, (
        f"El limite superior '{upper.group(1)}' permite mcp 2.x"
    )


def test_requirements_dev_matches_pyproject():
    """requirements-dev.txt no puede contradecir al extra declarado en pyproject."""
    lines = [
        line.strip()
        for line in (ROOT / "requirements-dev.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    mcp_lines = [line for line in lines if line.lower().replace(" ", "").startswith("mcp")]
    assert mcp_lines, "requirements-dev.txt deberia declarar la dependencia mcp"
    for line in mcp_lines:
        assert "<2" in line.replace(" ", ""), (
            f"'{line}' carece de limite superior; permitiria instalar mcp 2.x"
        )
        floor = re.search(r">=\s*([0-9][0-9.]*)", line)
        assert floor and _parse_version(floor.group(1)) >= REQUIRED_FLOOR, line


@pytest.mark.skipif(importlib.util.find_spec("mcp") is None, reason="extra mcp no instalado")
def test_installed_mcp_version_is_inside_the_supported_range():
    from importlib.metadata import version

    installed = _parse_version(version("mcp"))
    assert installed >= REQUIRED_FLOOR, (
        f"mcp {version('mcp')} es anterior al minimo soportado "
        f"{'.'.join(map(str, REQUIRED_FLOOR))}"
    )
    assert installed[:1] < REQUIRED_CEILING, (
        f"mcp {version('mcp')} pertenece a la serie 2.x, que elimino mcp.server.fastmcp"
    )
    low, high = KNOWN_BROKEN_RANGE
    assert not (low <= installed[:2] <= high), (
        f"mcp {version('mcp')} esta en el rango roto conocido "
        f"{'.'.join(map(str, low))}-{'.'.join(map(str, high))}"
    )


@pytest.mark.skipif(importlib.util.find_spec("mcp") is None, reason="extra mcp no instalado")
def test_fastmcp_is_importable_when_mcp_is_installed():
    from mcp.server.fastmcp import FastMCP

    assert FastMCP is not None


def test_entry_point_turns_a_build_failure_into_actionable_guidance(monkeypatch):
    """Con mcp 1.7-1.13 la construccion revienta con TypeError. El ejecutable
    ``ai-image-studio-mcp`` no debe mostrar ese rastro crudo, sino el intervalo
    soportado y la orden de diagnostico."""
    from ai_image_studio import mcp_server

    def explode():
        raise TypeError("issubclass() arg 1 must be a class")

    monkeypatch.setattr(mcp_server, "build_server", explode)

    with pytest.raises(RuntimeError) as excinfo:
        mcp_server.main()

    message = str(excinfo.value)
    assert "mcp>=1.14,<2" in message
    assert "doctor" in message
    assert isinstance(excinfo.value.__cause__, TypeError)


@pytest.mark.skipif(importlib.util.find_spec("mcp") is None, reason="extra mcp no instalado")
def test_server_can_be_built_without_starting_a_process():
    """Construye el servidor en memoria; nunca llama a server.run()."""
    from ai_image_studio.mcp_server import build_server

    server = build_server()
    assert server is not None
    tools = server._tool_manager.list_tools()
    assert len(tools) >= 15, f"Se esperaban al menos 15 herramientas, hay {len(tools)}"


@pytest.mark.skipif(importlib.util.find_spec("mcp") is None, reason="extra mcp no instalado")
def test_handshake_announces_the_project_version_not_the_library_version():
    """El `initialize` debe identificar a AI Image Studio, no al paquete mcp.

    FastMCP deja `version` en None y el servidor de bajo nivel responde entonces con
    la version de la libreria mcp, de modo que un cliente veria 1.x como si fuera la
    version del producto.
    """
    from importlib.metadata import version

    from ai_image_studio import __version__
    from ai_image_studio.mcp_server import build_server

    announced = build_server()._mcp_server.version

    assert announced == __version__, (
        f"el handshake anuncia {announced!r} en lugar de {__version__!r}"
    )
    assert announced != version("mcp"), "se esta anunciando la version del paquete mcp"
