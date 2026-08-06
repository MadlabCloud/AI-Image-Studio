"""Integridad estructural de las seis skills.

Una skill es un contrato con el agente: si cita una herramienta MCP que no existe,
o incluye documentacion que nunca enlaza, el agente no puede cumplirlo y el fallo es
invisible hasta que alguien lo sufre en produccion.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
SCHEMAS = ROOT / "src/ai_image_studio/schemas"

SKILL_NAMES = {
    "ai-image-studio-user-guide", "image-export-packager", "image-intake-router",
    "image-quality-gates", "photographer-capture-guide", "product-image-pipeline",
}
CARPETAS = sorted(p for p in SKILLS.iterdir() if p.is_dir())
IDS = [p.name for p in CARPETAS]


def leer(skill: Path) -> str:
    return (skill / "SKILL.md").read_text(encoding="utf-8")


def frontmatter(texto: str) -> dict[str, str]:
    bloque = re.match(r"^---\n(.*?)\n---\n", texto, re.S)
    assert bloque, "SKILL.md sin frontmatter"
    campos = {}
    for linea in bloque.group(1).splitlines():
        if ":" in linea and not linea.startswith(" "):
            clave, _, valor = linea.partition(":")
            campos[clave.strip()] = valor.strip()
    version = re.search(r'version:\s*"([^"]+)"', bloque.group(1))
    campos["version"] = version.group(1) if version else ""
    return campos


def test_the_repository_ships_exactly_the_six_skills():
    assert {p.name for p in CARPETAS} == SKILL_NAMES


@pytest.mark.parametrize("skill", CARPETAS, ids=IDS)
def test_frontmatter_is_complete(skill):
    campos = frontmatter(leer(skill))
    assert campos.get("name") == skill.name, "name debe coincidir con la carpeta"
    for clave in ("description", "license", "compatibility"):
        assert campos.get(clave), f"falta '{clave}' en el frontmatter"
    assert re.fullmatch(r"\d+\.\d+\.\d+", campos["version"]), (
        f"la version debe ser semantica, es {campos['version']!r}"
    )


@pytest.mark.parametrize("skill", CARPETAS, ids=IDS)
def test_every_skill_declares_its_openai_interface(skill):
    """Sin agents/openai.yaml la skill pierde nombre, descripcion e invocacion
    implicita en Codex y en las superficies compatibles de ChatGPT."""
    yaml = skill / "agents/openai.yaml"
    assert yaml.is_file(), "falta agents/openai.yaml"
    texto = yaml.read_text(encoding="utf-8")
    for clave in ("display_name", "short_description", "brand_color",
                  "default_prompt", "allow_implicit_invocation"):
        assert clave in texto, f"agents/openai.yaml no declara {clave}"


@pytest.mark.skipif(
    importlib.util.find_spec("mcp") is None, reason="extra mcp no instalado"
)
@pytest.mark.parametrize("skill", CARPETAS, ids=IDS)
def test_no_skill_cites_a_nonexistent_mcp_tool(skill):
    from ai_image_studio.mcp_server import build_server

    reales = {t.name for t in build_server()._tool_manager.list_tools()}
    texto = leer(skill)
    for referencia in sorted((skill / "references").glob("*")) if (skill / "references").is_dir() else []:
        if referencia.suffix in {".md", ".json"}:
            texto += referencia.read_text(encoding="utf-8")

    citadas = set(re.findall(r"\b(image_[a-z_]+)\b", texto))
    fantasma = sorted(citadas - reales)
    assert not fantasma, f"cita herramientas MCP inexistentes: {fantasma}"


@pytest.mark.parametrize("skill", CARPETAS, ids=IDS)
def test_every_cited_file_exists(skill):
    texto = leer(skill)
    for relativa in sorted(set(re.findall(r"`((?:references|scripts)/[A-Za-z0-9._/-]+)`", texto))):
        assert (skill / relativa).is_file(), f"SKILL.md cita {relativa}, que no existe"
    for esquema in sorted(set(re.findall(r"`([a-z-]+\.schema\.json)`", texto))):
        assert (SCHEMAS / esquema).is_file(), f"cita el esquema inexistente {esquema}"


@pytest.mark.parametrize("skill", CARPETAS, ids=IDS)
def test_no_bundled_file_is_orphaned(skill):
    """Todo lo que viaja dentro de la skill tiene que estar enlazado desde SKILL.md.

    Un archivo que nadie cita ocupa sitio en los cuatro artefactos y el agente jamas
    lo abrira: es documentacion muerta con apariencia de documentacion viva.
    """
    texto = leer(skill)
    for carpeta in ("references", "scripts"):
        directorio = skill / carpeta
        if not directorio.is_dir():
            continue
        citados = set(re.findall(rf"{carpeta}/([A-Za-z0-9._-]+)", texto))
        huerfanos = sorted(
            p.name for p in directorio.iterdir()
            # __pycache__ lo genera `compileall`, que CI ejecuta sobre skills/.
            if p.name not in citados and p.name != "__pycache__" and not p.name.startswith(".")
        )
        assert not huerfanos, f"{carpeta}/ contiene archivos que SKILL.md no cita: {huerfanos}"


@pytest.mark.parametrize("skill", CARPETAS, ids=IDS)
def test_bundled_json_is_valid(skill):
    for archivo in sorted(skill.rglob("*.json")):
        try:
            json.loads(archivo.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            pytest.fail(f"{archivo.relative_to(skill)}: JSON invalido: {exc}")


@pytest.mark.parametrize("skill", CARPETAS, ids=IDS)
def test_bundled_scripts_explain_a_missing_package(skill):
    """Los scripts viajan tambien en los ZIP que no llevan `src/`.

    Alli la insercion de sys.path no resuelve y el import falla. El usuario debe leer
    que le falta el paquete, no un ModuleNotFoundError pelado.
    """
    directorio = skill / "scripts"
    if not directorio.is_dir():
        pytest.skip("la skill no incluye scripts")
    for script in sorted(directorio.glob("*.py")):
        texto = script.read_text(encoding="utf-8")
        assert "except ImportError" in texto, f"{script.name} no captura el import fallido"
        assert "pip install" in texto, f"{script.name} no dice como instalar el paquete"
