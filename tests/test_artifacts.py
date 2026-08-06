"""Valida los artefactos ZIP como productos independientes.

No basta con que el repositorio funcione: cada ZIP debe ser coherente por si mismo.
Estas pruebas construyen la distribucion, extraen los cuatro artefactos y comprueban
estructura, manifiestos, privacidad, igualdad de skills y — sobre todo — que ningun
README documente rutas que no existen dentro de su propio paquete
(defecto PACKAGING-README-01 de la validacion v0.5.0).
"""

from __future__ import annotations

import hashlib
import json
import re
import stat
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]

ARTIFACTS = {
    "full": f"ai-image-studio-full-{VERSION}.zip",
    "claude-plugin": f"ai-image-studio-claude-plugin-{VERSION}.zip",
    "codex-marketplace": f"ai-image-studio-codex-marketplace-{VERSION}.zip",
    "standalone-skills": f"ai-image-studio-standalone-skills-{VERSION}.zip",
}
SKILL_NAMES = {
    "ai-image-studio-user-guide",
    "image-export-packager",
    "image-intake-router",
    "image-quality-gates",
    "photographer-capture-guide",
    "product-image-pipeline",
}


# --------------------------------------------------------------------------- fixtures

@pytest.fixture(scope="session")
def built(tmp_path_factory) -> dict[str, Path]:
    """Construye la distribucion y extrae cada ZIP. Devuelve la raiz de cada artefacto."""
    workdir = tmp_path_factory.mktemp("artifacts")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_distributions.py")],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    if result.returncode != 0:
        pytest.fail(f"build_distributions.py fallo:\n{result.stdout}\n{result.stderr}")

    roots: dict[str, Path] = {}
    for label, filename in ARTIFACTS.items():
        archive = ROOT / "dist" / filename
        assert archive.is_file(), f"No se genero {filename}"
        target = workdir / label
        with zipfile.ZipFile(archive) as zf:
            names = zf.namelist()
            assert names, f"{filename} esta vacio"
            tops = {n.split("/")[0] for n in names}
            assert len(tops) == 1, f"{filename} no tiene un unico directorio raiz: {tops}"
            zf.extractall(target)
        roots[label] = target / tops.pop()
    return roots


# --------------------------------------------------------------------------- README

PLACEHOLDER = re.compile(r"[<>*$%~]|\.\.\.")
URL_LIKE = re.compile(r"^(https?:|mailto:)")
WINDOWS_ABS = re.compile(r"^[A-Za-z]:[\\/]")


def _is_verifiable(token: str) -> bool:
    """Cierto si el token parece una ruta relativa al artefacto que se puede comprobar."""
    token = token.strip()
    if not token or PLACEHOLDER.search(token) or URL_LIKE.match(token):
        return False
    if token.startswith(("/", "\\")) or WINDOWS_ABS.match(token):
        return False
    if "\\" in token or " " in token:  # comandos o rutas Windows: no se comprueban
        return False
    return "/" in token or "." in token


def _table_paths(readme: str) -> list[str]:
    """Rutas de la seccion 'Contenido real': todas deben existir."""
    section = re.search(r"^## Contenido real\s*$(.*?)^## ", readme, re.M | re.S)
    if not section:
        return []
    found = []
    for line in section.group(1).splitlines():
        if not line.strip().startswith("|"):
            continue
        first_cell = line.split("|")[1] if line.count("|") >= 2 else ""
        for token in re.findall(r"`([^`]+)`", first_cell):
            for part in token.split(", "):
                if _is_verifiable(part):
                    found.append(part.strip())
    return found


def _absent_paths(readme: str) -> list[str]:
    """Rutas que la seccion 'Limitaciones' declara ausentes: no deben existir."""
    section = re.search(r"^## Limitaciones\s*$(.*)", readme, re.M | re.S)
    if not section:
        return []
    text = section.group(1)
    bullet = re.search(r"\*\*no\*\* contiene(.*?)(?:\.\s|\n\n)", text, re.S | re.I)
    if not bullet:
        return []
    return [t.strip() for t in re.findall(r"`([^`]+)`", bullet.group(1)) if _is_verifiable(t)]


@pytest.mark.parametrize("label", sorted(ARTIFACTS))
def test_every_artifact_ships_its_own_readme(built, label):
    readme = built[label] / "README.md"
    assert readme.is_file(), f"El artefacto {label} no incluye README.md"
    text = readme.read_text(encoding="utf-8")
    assert f"README-{label}" not in text  # es el README ya renombrado, no el de packaging
    expected_title = {
        "full": "Paquete Full",
        "claude-plugin": "Plugin de Claude Code",
        "codex-marketplace": "Marketplace de Codex",
        "standalone-skills": "Skills independientes",
    }[label]
    assert expected_title in text.splitlines()[0], (
        f"El README de {label} no corresponde a este artefacto: {text.splitlines()[0]!r}"
    )


@pytest.mark.parametrize("label", sorted(ARTIFACTS))
def test_readme_documented_paths_exist_inside_the_artifact(built, label):
    """Falla si el README describe contenido que el paquete no lleva."""
    root = built[label]
    readme = (root / "README.md").read_text(encoding="utf-8")
    documented = _table_paths(readme)
    assert documented, f"El README de {label} no documenta su contenido real"
    missing = [p for p in documented if not (root / p).exists()]
    assert not missing, (
        f"El README de '{label}' documenta rutas inexistentes en su propio ZIP: {missing}"
    )


@pytest.mark.parametrize("label", sorted(ARTIFACTS))
def test_readme_absent_paths_are_really_absent(built, label):
    root = built[label]
    readme = (root / "README.md").read_text(encoding="utf-8")
    for path in _absent_paths(readme):
        assert not (root / path).exists(), (
            f"El README de '{label}' declara que '{path}' no esta incluido, pero si lo esta"
        )


@pytest.mark.parametrize("label", sorted(ARTIFACTS))
def test_readme_mentions_canonical_repository_and_sha256(built, label):
    readme = (built[label] / "README.md").read_text(encoding="utf-8")
    assert "github.com/MadlabCloud/AI-Image-Studio" in readme
    assert "SHA-256" in readme and "SHA256SUMS.txt" in readme
    for heading in ("Instalación", "Validación", "Actualización", "Desinstalación",
                    "Rollback", "Limitaciones", "Requisitos", "Propósito"):
        assert f"## {heading}" in readme, f"El README de {label} no documenta '{heading}'"


def test_no_readme_references_the_nonexistent_mcp_folder(built):
    """DOC-MCP-01: el servidor vive en src/ai_image_studio/mcp_server.py."""
    for label, root in built.items():
        text = (root / "README.md").read_text(encoding="utf-8")
        assert not re.search(r"`mcp/`", text), f"{label}/README.md aun cita la carpeta mcp/"


# --------------------------------------------------------------------------- contenido

def test_full_artifact_has_the_expected_layout(built):
    root = built["full"]
    for path in ("src/ai_image_studio/mcp_server.py", "pyproject.toml", "tests",
                 "schemas", "skills", "docs/MCP_SETUP.md", ".mcp.json.example"):
        assert (root / path).exists(), f"Falta {path} en el paquete full"


def test_claude_artifact_is_a_valid_marketplace(built):
    root = built["claude-plugin"]
    marketplace = json.loads((root / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
    plugin = json.loads((root / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    assert marketplace.get("description"), "CLAUDE-01: falta la descripcion del marketplace"
    entry = marketplace["plugins"][0]
    assert entry["source"] == "./", f"CLAUDE-01: source debe ser './', es {entry['source']!r}"
    assert entry["version"] == plugin["version"] == VERSION
    assert (root / "skills").is_dir()
    assert not (root / "src").exists(), "el plugin de Claude no debe llevar codigo Python"


def test_codex_artifact_is_an_installable_marketplace(built):
    """CODEX-DISTRIBUTION-01: el ZIP debe ser un marketplace, no un plugin suelto."""
    root = built["codex-marketplace"]
    manifest_path = root / ".agents/plugins/marketplace.json"
    assert manifest_path.is_file(), "falta .agents/plugins/marketplace.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = manifest["plugins"][0]
    assert entry["name"] == "ai-image-studio"
    assert entry["source"]["source"] == "local"
    plugin_dir = root / entry["source"]["path"]
    assert plugin_dir.is_dir(), f"la ruta declarada no existe: {entry['source']['path']}"
    plugin = json.loads((plugin_dir / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    assert plugin["version"] == VERSION
    assert {p.name for p in (plugin_dir / "skills").iterdir() if p.is_dir()} == SKILL_NAMES


def test_standalone_artifact_ships_the_installers_it_documents(built):
    root = built["standalone-skills"]
    assert (root / "adapters/install-skills.sh").is_file()
    assert (root / "adapters/install-skills.ps1").is_file()
    assert not (root / "src").exists()


@pytest.mark.parametrize("label", sorted(ARTIFACTS))
def test_artifact_contains_the_six_skills(built, label):
    root = built[label]
    base = root / "plugins/ai-image-studio/skills" if label == "codex-marketplace" else root / "skills"
    assert {p.name for p in base.iterdir() if p.is_dir()} == SKILL_NAMES
    for skill in base.iterdir():
        if skill.is_dir():
            assert (skill / "SKILL.md").is_file(), f"{skill.name} sin SKILL.md en {label}"


def test_six_skills_are_byte_identical_across_artifacts(built):
    def digest_map(root: Path, base: Path) -> dict[str, str]:
        return {
            p.relative_to(base).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(base.rglob("*")) if p.is_file()
        }

    reference = digest_map(built["full"], built["full"] / "skills")
    assert reference, "no se encontraron archivos de skills en el paquete full"
    for label in ARTIFACTS:
        base = (built[label] / "plugins/ai-image-studio/skills"
                if label == "codex-marketplace" else built[label] / "skills")
        assert digest_map(built[label], base) == reference, (
            f"las skills de '{label}' difieren byte a byte de las del paquete full"
        )


# --------------------------------------------------------------------------- higiene

@pytest.mark.parametrize("label", sorted(ARTIFACTS))
def test_artifact_json_is_valid_utf8(built, label):
    for path in built[label].rglob("*.json"):
        raw = path.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), f"{path} lleva BOM"
        try:
            json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            pytest.fail(f"{path.relative_to(built[label])} invalido en {label}: {exc}")


@pytest.mark.parametrize("label", sorted(ARTIFACTS))
def test_artifact_has_no_private_material(built, label):
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_distributions as bd

    root = built[label]
    relatives = [p.relative_to(root) for p in root.rglob("*") if p.is_file()]
    problems = bd.privacy_violations(root, relatives)
    assert not problems, f"material privado en '{label}': {problems}"


@pytest.mark.parametrize("label", sorted(ARTIFACTS))
def test_artifacts_use_lf_endings_on_every_platform(built, label):
    """Ningun archivo del artefacto puede llevar CRLF.

    No basta con los `.sh`. Si el resto del texto conserva los finales de linea del
    arbol de trabajo, el mismo commit produce ZIP distintos segun quien los construya
    (Windows entrega CRLF, Linux entrega LF) y los SHA-256 publicados dejan de poder
    verificarse de forma independiente.
    """
    for path in built[label].rglob("*"):
        if not path.is_file():
            continue
        data = path.read_bytes()
        if b"\x00" in data:  # binario: se conserva tal cual
            continue
        assert b"\r\n" not in data, (
            f"{path.name} lleva CRLF en '{label}'; el artefacto dejaria de ser "
            "reproducible entre plataformas"
        )


def test_checksums_cover_every_artifact(built):
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/generate_checksums.py"), str(ROOT / "dist")],
        check=True, capture_output=True,
    )
    lines = (ROOT / "dist/SHA256SUMS.txt").read_text(encoding="utf-8").strip().splitlines()
    recorded = {name: digest for digest, name in (line.split("  ", 1) for line in lines)}
    for filename in ARTIFACTS.values():
        assert filename in recorded, f"{filename} no figura en SHA256SUMS.txt"
        actual = hashlib.sha256((ROOT / "dist" / filename).read_bytes()).hexdigest()
        assert recorded[filename] == actual, f"hash incorrecto para {filename}"


# --------------------------------------------------------- limpieza del stage
# Los ZIP se construyen recorriendo `.build-dist/`, no el repositorio. Si esa
# carpeta conserva restos de una construccion anterior, esos archivos viajan
# dentro del artefacto. Reproducido en Windows sobre un arbol sincronizado con
# la nube: las carpetas se convierten en marcadores de posicion de solo lectura,
# `rmtree` falla con PermissionError y un archivo ajeno acabo dentro del ZIP Full.

sys.path.insert(0, str(ROOT / "scripts"))
import build_distributions as bd  # noqa: E402


@pytest.mark.parametrize("label", sorted(ARTIFACTS))
def test_entry_paths_leave_room_under_windows_max_path(built, label):
    """Ningun ZIP puede acercarse al limite MAX_PATH de 260 caracteres.

    El artefacto de Codex anida `plugins/ai-image-studio/skills/<skill>/references/...`
    y es el unico que se acercaba al limite: con la raiz larga su entrada mayor medía
    132 caracteres, y extraerlo bajo un directorio ya profundo fallaba con
    [WinError 206]. Acortar la raiz a `ai-image-studio-codex` lo bajo a 120.

    El presupuesto expresa una garantia concreta: con 128 caracteres de entrada, la
    extraccion cabe en cualquier destino de hasta 132 caracteres sin activar rutas
    largas. Hoy sobran 8; si un archivo nuevo se los come, esta prueba lo dice antes
    de publicar en vez de que lo descubra un usuario de Windows.
    """
    PRESUPUESTO = 128
    raiz = built[label]
    entradas = [p.relative_to(raiz.parent).as_posix() for p in raiz.rglob("*") if p.is_file()]
    mas_larga = max(entradas, key=len)
    assert len(mas_larga) <= PRESUPUESTO, (
        f"la entrada mas larga de '{label}' mide {len(mas_larga)} caracteres "
        f"(presupuesto {PRESUPUESTO}): {mas_larga}"
    )


def test_reset_directory_removes_read_only_leftovers(tmp_path):
    stage = tmp_path / "stage"
    (stage / "sub").mkdir(parents=True)
    resto = stage / "sub" / "resto.txt"
    resto.write_text("de una construccion anterior", encoding="utf-8")
    resto.chmod(stat.S_IREAD)

    bd._reset_directory(stage, strict=True)

    assert stage.is_dir()
    assert list(stage.iterdir()) == [], "el stage quedo contaminado"


def test_reset_directory_aborts_instead_of_packaging_a_dirty_stage(tmp_path, monkeypatch):
    stage = tmp_path / "stage"
    stage.mkdir()
    (stage / "resto-retenido.bin").write_bytes(b"x")

    def refuse(entry):
        raise OSError("retenido por otro proceso")

    monkeypatch.setattr(bd, "_force_delete", refuse)

    with pytest.raises(bd.StaleStageError) as excinfo:
        bd._reset_directory(stage, strict=True)
    assert "resto-retenido.bin" in str(excinfo.value)

    # Sin strict basta el aviso: dist/ solo acumula ZIP que se sobrescriben.
    bd._reset_directory(stage, strict=False)
