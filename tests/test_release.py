import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]


def test_package_version_is_consistent():
    project_version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    namespace = {}
    exec((ROOT / "src/ai_image_studio/__init__.py").read_text(encoding="utf-8"), namespace)
    assert namespace["__version__"] == project_version


def test_checksum_generator(tmp_path):
    artifact = tmp_path / "artifact.zip"
    artifact.write_bytes(b"ai-image-studio")
    subprocess.run([sys.executable, str(ROOT / "scripts/generate_checksums.py"), str(tmp_path)], check=True)
    line = (tmp_path / "SHA256SUMS.txt").read_text(encoding="utf-8").strip()
    expected = hashlib.sha256(b"ai-image-studio").hexdigest()
    assert line == f"{expected}  artifact.zip"


IGNORED_EXAMPLES = [
    "dist/ai-image-studio-full-0.0.0.zip",
    ".env",
    ".env.local",
    # Mayusculas incluidas a proposito: las camaras escriben asi la extension y en
    # Linux o macOS `*.jpg` NO casa con `.JPG`. Comprobarlo por comportamiento y no
    # por subcadena es lo que detecta ese hueco.
    "IMG_1347.JPG",
    "IMG_1347.jpg",
    "DSC_0001.NEF",
    "captura.PNG",
    "raw.CR2",
    "escaneo.TIFF",
]
ALLOWED_EXAMPLES = [
    "README.md",
    "src/ai_image_studio/cli.py",
    "assets/logo.png",
    "docs/captura.png",
    "tests/fixtures/muestra.jpg",
]


def _is_ignored(relative: str) -> bool:
    """git check-ignore sale 0 si la ruta esta excluida y 1 si no lo esta.

    ``core.ignoreCase=false`` fuerza la semantica de un sistema de archivos sensible
    a mayusculas. Sin esta anulacion, Windows daria por buena una regla `*.jpg` que
    en Linux no casa con `IMG_1347.JPG`, y la prueba no detectaria el hueco.
    """
    result = subprocess.run(
        ["git", "-C", str(ROOT), "-c", "core.ignoreCase=false",
         "check-ignore", "-q", relative],
        capture_output=True,
    )
    return result.returncode == 0


@pytest.mark.skipif(shutil.which("git") is None, reason="requiere git")
@pytest.mark.parametrize("relative", IGNORED_EXAMPLES)
def test_release_assets_and_private_media_are_ignored(relative):
    assert _is_ignored(relative), f"{relative} deberia estar excluido por .gitignore"


@pytest.mark.skipif(shutil.which("git") is None, reason="requiere git")
@pytest.mark.parametrize("relative", ALLOWED_EXAMPLES)
def test_project_files_are_not_ignored(relative):
    assert not _is_ignored(relative), f"{relative} no deberia estar excluido"


# ------------------------------------------------------- esquemas duplicados
# `schemas/` es la copia visible del repositorio y `src/ai_image_studio/schemas/` la
# que carga el codigo (`files("ai_image_studio").joinpath("schemas/...")`). Nada
# mantiene las dos sincronizadas: editar la de la raiz no cambia la validacion, y el
# error es silencioso. Hasta unificarlas, esta prueba impide que diverjan.
PUBLIC_SCHEMAS = ROOT / "schemas"
PACKAGE_SCHEMAS = ROOT / "src/ai_image_studio/schemas"
SCHEMA_NAMES = sorted(p.name for p in PACKAGE_SCHEMAS.glob("*.json"))


def test_both_schema_directories_hold_the_same_files():
    assert sorted(p.name for p in PUBLIC_SCHEMAS.glob("*.json")) == SCHEMA_NAMES


@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_the_public_schema_matches_the_one_the_code_loads(name):
    publico = (PUBLIC_SCHEMAS / name).read_bytes().replace(b"\r\n", b"\n")
    paquete = (PACKAGE_SCHEMAS / name).read_bytes().replace(b"\r\n", b"\n")
    assert publico == paquete, (
        f"schemas/{name} y src/ai_image_studio/schemas/{name} han divergido. "
        "El codigo solo carga la segunda: la primera quedaria como documentacion falsa."
    )
