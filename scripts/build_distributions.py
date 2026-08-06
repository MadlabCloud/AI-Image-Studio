"""Construye los artefactos de distribucion de AI Image Studio.

Artefactos generados en ``dist/``:

===========================================  ==========================================
Archivo                                      Contenido
===========================================  ==========================================
ai-image-studio-full-VER.zip                 Proyecto completo (CLI, MCP, skills, tests)
ai-image-studio-claude-plugin-VER.zip        Marketplace y plugin de Claude Code
ai-image-studio-codex-marketplace-VER.zip    Marketplace instalable de Codex
ai-image-studio-standalone-skills-VER.zip    Las seis skills y los instaladores
===========================================  ==========================================

Garantias que aplica este script:

*   **Privacidad (fail-closed).** La seleccion de archivos usa ``git ls-files`` cuando
    hay repositorio, de modo que nada ignorado por ``.gitignore`` puede colarse. Sin
    git se usa una lista de exclusion reforzada. En ambos casos, antes de escribir
    cada ZIP se ejecuta un escaneo que **aborta** si detecta material privado.
*   **README por artefacto.** Cada paquete recibe el README de ``packaging/`` que le
    corresponde, nunca el README general del repositorio.
*   **Reproducibilidad, tambien entre plataformas.** Marcas de tiempo fijas, orden
    estable de entradas, finales de linea LF en todo el texto y sistema de origen
    fijado en la cabecera. El mismo commit produce ZIP identicos byte a byte lo
    construya Windows, Linux o macOS, de modo que cualquiera puede reproducir los
    SHA-256 publicados.

    Comprobarlo exige construir en sistemas *distintos*: convertir el arbol a LF y
    volver a construir en la misma maquina no basta, porque deja fuera precisamente
    los metadatos que dependen de la plataforma.
"""

from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
import zipfile
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
DIST = ROOT / "dist"
TMP = ROOT / ".build-dist"
PACKAGING = ROOT / "packaging"

# Fecha fija para que dos construcciones del mismo arbol den ZIP identicos.
FIXED_TIMESTAMP = (2026, 1, 1, 0, 0, 0)

IGNORED_PARTS = {
    ".git", ".pytest_cache", "__pycache__", ".build-dist", "dist", ".venv", "venv",
    ".mypy_cache", ".ruff_cache", ".idea", ".vscode", "node_modules", ".tox", ".eggs",
}
IGNORED_SUFFIXES = {".pyc", ".pyo", ".pyd", ".so", ".dylib", ".log", ".tmp", ".swp"}

# Material que jamas debe viajar dentro de un artefacto publico.
PRIVATE_NAME_PATTERNS = [
    re.compile(r"(?i)^\.env(\..*)?$"),
    re.compile(r"(?i)\.(cr2|nef|arw|dng|orf|rw2|raf|psd)$"),
    re.compile(r"(?i)\.(pem|key|p12|pfx|keystore)$"),
    re.compile(r"(?i)(^|/)(id_rsa|id_ed25519|credentials|secrets?)(\.|$)"),
    re.compile(r"(?i)^img_\d+\.(jpe?g|png|heic)$"),  # fotos personales de prueba
]
# Imagenes permitidas solo si viven en rutas de documentacion o de pruebas.
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".heic", ".webp", ".tif", ".tiff", ".bmp", ".gif"}
IMAGE_ALLOWED_PREFIXES = ("docs/", "assets/", "tests/fixtures/", "skills/")

# Cadenas que delatarian un entorno personal dentro de un archivo de texto.
# El nucleo publico es generico a proposito: aqui no se nombra a ningun cliente,
# empresa ni usuario concreto. Para auditar terminos privados adicionales, define
# la variable de entorno AI_IMAGE_STUDIO_PRIVATE_TERMS con una lista separada por
# comas; los terminos se comprueban sin quedar registrados en el repositorio.
PRIVATE_CONTENT_PATTERNS = [
    re.compile(r"(?i)\bC:\\\\Users\\\\(?!<|USUARIO|USER\b)[A-Za-z0-9._-]+"),
    re.compile(r"(?i)\bOneDrive\b"),
    re.compile(r"(?i)/home/(?!<|usuario|user\b)[a-z0-9._-]+/"),
    re.compile(r"(?i)/Users/(?!<|usuario|user\b)[A-Za-z0-9._-]+/"),
]


def _extra_content_patterns() -> list[re.Pattern[str]]:
    raw = os.environ.get("AI_IMAGE_STUDIO_PRIVATE_TERMS", "")
    terms = [t.strip() for t in raw.split(",") if t.strip()]
    return [re.compile(rf"(?i)\b{re.escape(t)}\b") for t in terms]


TEXT_SUFFIXES = {
    ".md", ".txt", ".json", ".jsonl", ".yml", ".yaml", ".toml", ".cfg", ".ini",
    ".py", ".sh", ".ps1", ".bat", ".example",
}
# El propio escaner contiene las expresiones que busca; no se audita a si mismo.
# Se compara por sufijo de ruta para que la exencion funcione tanto sobre el arbol
# del repositorio como sobre un artefacto ya extraido con directorio raiz propio.
SCAN_EXEMPT_SUFFIXES = ("scripts/build_distributions.py", "scripts/validate_artifacts.py")


class PrivacyError(RuntimeError):
    """Se detecto material privado en un artefacto a punto de publicarse."""


class StaleStageError(RuntimeError):
    """El directorio de preparacion conserva restos de una construccion anterior."""


# --------------------------------------------------------------------------- seleccion

def _git_tracked_files() -> list[Path] | None:
    """Archivos que pertenecen al repositorio. ``None`` si git no es utilizable.

    Se incluyen los versionados (``--cached``) y tambien los nuevos todavia sin
    commitear (``--others``), porque un artefacto de validacion debe reflejar el
    arbol de trabajo. ``--exclude-standard`` respeta ``.gitignore``, que es lo que
    impide que material privado ignorado acabe dentro de un ZIP publico.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "-z",
             "--cached", "--others", "--exclude-standard"],
            capture_output=True, check=True, timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    names = [n for n in result.stdout.decode("utf-8", "replace").split("\0") if n]
    if not names:
        return None
    return [Path(n) for n in names]


def _walk_files(base: Path) -> list[Path]:
    found = []
    for path in sorted(base.rglob("*")):
        rel = path.relative_to(base)
        if any(part in IGNORED_PARTS for part in rel.parts):
            continue
        if path.is_file() and rel.suffix.lower() not in IGNORED_SUFFIXES:
            found.append(rel)
    return found


def source_files() -> list[Path]:
    """Rutas relativas a ROOT que pueden entrar en el paquete Full."""
    tracked = _git_tracked_files()
    if tracked is None:
        print("aviso: git no disponible; se usa exclusion por lista reforzada")
        tracked = _walk_files(ROOT)
    return sorted(p for p in tracked if (ROOT / p).is_file())


# --------------------------------------------------------------------------- privacidad

def privacy_violations(base: Path, relatives: list[Path]) -> list[str]:
    problems: list[str] = []
    content_patterns = PRIVATE_CONTENT_PATTERNS + _extra_content_patterns()
    for rel in relatives:
        posix = rel.as_posix()
        name = rel.name
        for pattern in PRIVATE_NAME_PATTERNS:
            if pattern.search(name) or pattern.search(posix):
                problems.append(f"{posix}: nombre de archivo privado")
                break
        if rel.suffix.lower() in IMAGE_SUFFIXES and not posix.startswith(IMAGE_ALLOWED_PREFIXES):
            problems.append(f"{posix}: imagen fuera de docs/, assets/, tests/fixtures/ o skills/")
        if posix.endswith(SCAN_EXEMPT_SUFFIXES) or rel.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = (base / rel).read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern in content_patterns:
            match = pattern.search(text)
            if match:
                problems.append(f"{posix}: contenido privado -> {match.group(0)!r}")
                break
    return problems


def assert_clean(base: Path, relatives: list[Path], label: str) -> None:
    problems = privacy_violations(base, relatives)
    if problems:
        detail = "\n  ".join(problems)
        raise PrivacyError(f"Artefacto '{label}' contiene material privado:\n  {detail}")


# --------------------------------------------------------------------------- empaquetado

# Sistema de origen declarado en la cabecera de cada entrada. `zipfile` lo deduce de
# la plataforma que construye -- 0 (MS-DOS) en Windows, 3 (Unix) en POSIX -- y eso
# basta para que el mismo arbol produzca archivos con hash distinto segun quien los
# empaquete, aunque el contenido de las 138 entradas sea identico byte a byte. Se fija
# a Unix, que es lo que espera cualquier consumidor POSIX de los `.sh` incluidos.
CREATE_SYSTEM_UNIX = 3


def write_zip(base: Path, relatives: list[Path], destination: Path, top_name: str) -> None:
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in sorted(relatives, key=lambda p: p.as_posix()):
            info = zipfile.ZipInfo(
                (Path(top_name) / rel).as_posix(), date_time=FIXED_TIMESTAMP
            )
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = CREATE_SYSTEM_UNIX
            info.external_attr = 0o644 << 16
            archive.writestr(info, (base / rel).read_bytes())


def _text_normalized(data: bytes) -> bytes:
    """Devuelve el contenido con finales de linea LF si es texto.

    Dos motivos, y el segundo es el importante:

    1.  Un interprete POSIX rechaza un script con CRLF ("bad interpreter: ^M").
    2.  El artefacto debe ser **independiente del sistema que lo construye**. Un
        arbol de trabajo Windows con ``core.autocrlf=true`` entrega CRLF y uno
        Linux entrega LF; sin normalizar, el mismo commit produce ZIP con hashes
        distintos segun quien los construya, y ``SHA256SUMS.txt`` deja de poder
        verificarse de forma independiente.

    Los binarios se dejan intactos: se detectan por la presencia de un byte nulo.
    """
    if b"\x00" in data:
        return data
    return data.replace(b"\r\n", b"\n")


def stage_copy(sources: list[tuple[Path, Path]], stage: Path) -> None:
    """Copia (origen_absoluto, destino_relativo) dentro de ``stage``."""
    for src, rel in sources:
        target = stage / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(_text_normalized(src.read_bytes()))


def skill_files() -> list[Path]:
    return sorted(
        p.relative_to(ROOT)
        for p in (ROOT / "skills").rglob("*")
        if p.is_file() and not any(part in IGNORED_PARTS for part in p.relative_to(ROOT).parts)
    )


def readme_for(artifact: str) -> Path:
    path = PACKAGING / f"README-{artifact}.md"
    if not path.is_file():
        raise FileNotFoundError(f"Falta el README especifico del artefacto: {path}")
    return path


def finish(stage: Path, name: str, top_name: str, label: str) -> Path:
    relatives = sorted(_walk_files(stage), key=lambda p: p.as_posix())
    assert_clean(stage, relatives, label)
    destination = DIST / name
    write_zip(stage, relatives, destination, top_name)
    print(f"  {destination.name}  ({len(relatives)} archivos)")
    return destination


# --------------------------------------------------------------------------- artefactos

def build_full() -> None:
    relatives = source_files()
    assert_clean(ROOT, relatives, "full")
    stage = TMP / "full"
    stage_copy([(ROOT / rel, rel) for rel in relatives], stage)
    # Despues de copiar el arbol: sustituye el README general por el del artefacto.
    stage_copy([(readme_for("full"), Path("README.md"))], stage)
    finish(stage, f"ai-image-studio-full-{VERSION}.zip", "ai-image-studio", "full")


def build_claude_plugin() -> None:
    stage = TMP / "claude"
    sources = [(ROOT / rel, rel) for rel in skill_files()]
    sources += [
        (ROOT / ".claude-plugin/plugin.json", Path(".claude-plugin/plugin.json")),
        (ROOT / ".claude-plugin/marketplace.json", Path(".claude-plugin/marketplace.json")),
        (ROOT / "LICENSE", Path("LICENSE")),
        (ROOT / "NOTICE", Path("NOTICE")),
        (readme_for("claude-plugin"), Path("README.md")),
    ]
    stage_copy(sources, stage)
    finish(
        stage,
        f"ai-image-studio-claude-plugin-{VERSION}.zip",
        "ai-image-studio",
        "claude-plugin",
    )


def build_codex_marketplace() -> None:
    """Marketplace de Codex listo para `codex plugin marketplace add`.

    A diferencia de v0.5.0, el artefacto ya incluye el envoltorio
    ``.agents/plugins/marketplace.json`` + ``plugins/ai-image-studio/``, por lo que el
    usuario no tiene que construirlo a mano (defecto CODEX-DISTRIBUTION-01).
    """
    stage = TMP / "codex"
    plugin_root = Path("plugins/ai-image-studio")
    sources = [(ROOT / rel, plugin_root / rel) for rel in skill_files()]
    sources += [
        (ROOT / ".codex-plugin/plugin.json", plugin_root / ".codex-plugin/plugin.json"),
        (ROOT / "LICENSE", plugin_root / "LICENSE"),
        (ROOT / "NOTICE", plugin_root / "NOTICE"),
        (ROOT / "LICENSE", Path("LICENSE")),
        (ROOT / "NOTICE", Path("NOTICE")),
        (readme_for("codex-marketplace"), Path("README.md")),
    ]
    stage_copy(sources, stage)

    marketplace = {
        "name": "ai-image-studio-marketplace",
        "interface": {"displayName": "AI Image Studio"},
        "plugins": [
            {
                "name": "ai-image-studio",
                "source": {"source": "local", "path": "./plugins/ai-image-studio"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_USE"},
                "category": "Coding",
            }
        ],
    }
    import json

    target = stage / ".agents/plugins/marketplace.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    # write_bytes, no write_text: en Windows el modo texto convertiria \n en \r\n.
    body = json.dumps(marketplace, indent=2, ensure_ascii=False) + "\n"
    target.write_bytes(body.encode("utf-8"))

    finish(
        stage,
        f"ai-image-studio-codex-marketplace-{VERSION}.zip",
        # El directorio raiz se acorta a proposito. Este artefacto anida
        # `plugins/ai-image-studio/skills/<skill>/references/...` y era el unico que
        # se acercaba al limite MAX_PATH de 260 caracteres de Windows: con
        # `ai-image-studio-codex-marketplace` la entrada mas larga medía 132.
        # El nombre del ZIP no cambia.
        "ai-image-studio-codex",
        "codex-marketplace",
    )


def build_standalone_skills() -> None:
    stage = TMP / "standalone"
    sources = [(ROOT / rel, rel) for rel in skill_files()]
    sources += [
        (ROOT / "adapters/install-skills.ps1", Path("adapters/install-skills.ps1")),
        (ROOT / "adapters/install-skills.sh", Path("adapters/install-skills.sh")),
        (ROOT / "LICENSE", Path("LICENSE")),
        (ROOT / "NOTICE", Path("NOTICE")),
        (readme_for("standalone-skills"), Path("README.md")),
    ]
    stage_copy(sources, stage)
    finish(
        stage,
        f"ai-image-studio-standalone-skills-{VERSION}.zip",
        "ai-image-studio",
        "standalone-skills",
    )


def _permitir_escritura(path: Path) -> None:
    """Anade el permiso de escritura conservando el resto del modo.

    Asignar ``stat.S_IWRITE`` a secas seria un error grave en POSIX: deja el archivo
    o el directorio en ``0o200``, y un directorio sin permiso de busqueda ya no se
    puede recorrer, asi que ``rmtree`` falla justo cuando se le pedia lo contrario.
    En Windows la llamada solo conmuta el atributo de solo lectura.
    """
    try:
        path.chmod(path.stat().st_mode | stat.S_IWUSR)
    except OSError:
        pass


def _force_delete(entry: Path) -> None:
    """Borra ``entry`` aunque lleve el atributo de solo lectura.

    En un arbol sincronizado con la nube en Windows, las carpetas se convierten
    en marcadores de posicion con atributos ``ReadOnly`` y ``ReparsePoint``, y
    ``rmtree`` falla con ``PermissionError``.
    """
    if entry.is_dir() and not entry.is_symlink():
        for child in sorted(entry.rglob("*"), reverse=True):
            _permitir_escritura(child)
        _permitir_escritura(entry)
        shutil.rmtree(entry)
    else:
        _permitir_escritura(entry)
        entry.unlink()


def _reset_directory(path: Path, strict: bool = False) -> None:
    """Deja ``path`` vacio y utilizable.

    Con ``strict`` un resto sin borrar **aborta**. Es obligatorio para el
    directorio de preparacion: los ZIP se construyen recorriendo el stage, no el
    repositorio, asi que un resto de una construccion anterior se empaquetaria
    como si formase parte del proyecto. Verificado: un archivo retenido en
    ``.build-dist/full`` acabo dentro de ``ai-image-studio-full-*.zip``.
    """
    path.mkdir(parents=True, exist_ok=True)
    leftovers = []
    for entry in path.iterdir():
        try:
            _force_delete(entry)
        except OSError:
            leftovers.append(entry.name)
    if leftovers:
        message = f"no se pudieron eliminar restos en {path}: {sorted(leftovers)}"
        if strict:
            raise StaleStageError(
                f"{message}. Un stage contaminado empaqueta archivos que ya no "
                "pertenecen al repositorio; cierra los procesos que los retienen "
                "y vuelve a construir."
            )
        print(f"aviso: {message}")


def main() -> None:
    _reset_directory(DIST)
    _reset_directory(TMP, strict=True)
    try:
        print(f"Construyendo artefactos {VERSION}:")
        build_full()
        build_claude_plugin()
        build_codex_marketplace()
        build_standalone_skills()
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    print(DIST)


if __name__ == "__main__":
    main()
