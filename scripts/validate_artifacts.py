"""Valida los artefactos ya construidos en ``dist/`` como productos independientes.

Se ejecuta en CI y en el flujo de Release **despues** de
``scripts/build_distributions.py``. A diferencia de ``validate_bundle.py``, que
inspecciona el arbol del repositorio, este script abre los ZIP y comprueba lo que
un usuario recibiria de verdad.

Comprobaciones:

1. Existen los cuatro artefactos esperados para la version declarada.
2. Cada ZIP tiene un unico directorio raiz.
3. Cada ZIP incluye su README especifico, no el README general.
4. Todo JSON es UTF-8 valido y sin BOM.
5. Los manifiestos de Claude y Codex son correctos e instalables.
6. Las seis skills existen y son identicas byte a byte en los cuatro artefactos.
7. No hay material privado ni rutas locales.
8. Todo el texto usa finales de linea LF, de modo que el ZIP es identico lo
   construya Windows, Linux o macOS.
9. ``SHA256SUMS.txt`` cubre y coincide con todos los artefactos.

Uso:  python scripts/validate_artifacts.py [directorio_dist]
"""

from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_distributions import privacy_violations  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]

EXPECTED = {
    "full": (f"ai-image-studio-full-{VERSION}.zip", "Paquete Full"),
    "claude-plugin": (f"ai-image-studio-claude-plugin-{VERSION}.zip", "Plugin de Claude Code"),
    "codex-marketplace": (f"ai-image-studio-codex-marketplace-{VERSION}.zip", "Marketplace de Codex"),
    "standalone-skills": (f"ai-image-studio-standalone-skills-{VERSION}.zip", "Skills independientes"),
}
SKILL_NAMES = {
    "ai-image-studio-user-guide", "image-export-packager", "image-intake-router",
    "image-quality-gates", "photographer-capture-guide", "product-image-pipeline",
}

errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def skills_base(label: str, root: Path) -> Path:
    return root / "plugins/ai-image-studio/skills" if label == "codex-marketplace" else root / "skills"


def main() -> None:
    dist = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "dist"
    if not dist.is_dir():
        raise SystemExit(f"No existe el directorio de artefactos: {dist}")

    # Se extrae en un directorio temporal del sistema: no ensucia dist/ y evita
    # problemas de borrado en sistemas de archivos sincronizados.
    import tempfile

    tempdir = tempfile.TemporaryDirectory(prefix="ai-image-studio-validate-")
    extracted = Path(tempdir.name)

    roots: dict[str, Path] = {}
    for label, (filename, title) in EXPECTED.items():
        archive = dist / filename
        if not archive.is_file():
            fail(f"{filename}: no se genero")
            continue
        with zipfile.ZipFile(archive) as zf:
            bad = zf.testzip()
            if bad:
                fail(f"{filename}: entrada corrupta {bad}")
                continue
            names = zf.namelist()
            if any(n.startswith("/") or ".." in Path(n).parts for n in names):
                fail(f"{filename}: contiene rutas inseguras")
                continue
            tops = {n.split("/")[0] for n in names}
            if len(tops) != 1:
                fail(f"{filename}: no tiene un unico directorio raiz -> {sorted(tops)}")
                continue
            target = extracted / label
            zf.extractall(target)
            roots[label] = target / tops.pop()

        root = roots[label]
        readme = root / "README.md"
        if not readme.is_file():
            fail(f"{filename}: sin README.md")
        else:
            first = readme.read_text(encoding="utf-8").splitlines()[0]
            if title not in first:
                fail(f"{filename}: README no corresponde al artefacto -> {first!r}")

        for path in root.rglob("*.json"):
            raw = path.read_bytes()
            if raw.startswith(b"\xef\xbb\xbf"):
                fail(f"{filename}: {path.relative_to(root)} lleva BOM")
            try:
                json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                fail(f"{filename}: {path.relative_to(root)} JSON invalido: {exc}")

        # CRLF en cualquier archivo rompe dos cosas: un interprete POSIX rechaza los
        # scripts, y el ZIP deja de ser identico segun el sistema que lo construya.
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            data = path.read_bytes()
            if b"\x00" not in data and b"\r\n" in data:
                fail(f"{filename}: {path.relative_to(root)} usa CRLF; el artefacto debe ser LF")

        relatives = [p.relative_to(root) for p in root.rglob("*") if p.is_file()]
        for problem in privacy_violations(root, relatives):
            fail(f"{filename}: PRIVACIDAD -> {problem}")

        base = skills_base(label, root)
        if not base.is_dir():
            fail(f"{filename}: no contiene skills en {base.relative_to(root)}")
        else:
            names_found = {p.name for p in base.iterdir() if p.is_dir()}
            if names_found != SKILL_NAMES:
                fail(f"{filename}: skills incorrectas -> {sorted(names_found)}")
            for skill in sorted(base.iterdir()):
                if skill.is_dir() and not (skill / "SKILL.md").is_file():
                    fail(f"{filename}: {skill.name} sin SKILL.md")

    # ---- manifiesto de Claude
    if "claude-plugin" in roots:
        root = roots["claude-plugin"]
        try:
            marketplace = json.loads((root / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
            plugin = json.loads((root / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
            if not marketplace.get("description"):
                fail("claude-plugin: el marketplace no declara description (falla en --strict)")
            entry = marketplace["plugins"][0]
            if entry.get("source") != "./":
                fail(f"claude-plugin: source debe ser './', es {entry.get('source')!r}")
            if not (entry.get("version") == plugin.get("version") == VERSION):
                fail("claude-plugin: las versiones de plugin y marketplace no coinciden")
        except Exception as exc:
            fail(f"claude-plugin: manifiesto ilegible: {exc}")

    # ---- marketplace de Codex
    if "codex-marketplace" in roots:
        root = roots["codex-marketplace"]
        manifest = root / ".agents/plugins/marketplace.json"
        if not manifest.is_file():
            fail("codex-marketplace: falta .agents/plugins/marketplace.json (no es instalable)")
        else:
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
                entry = data["plugins"][0]
                if entry["source"]["source"] != "local":
                    fail("codex-marketplace: source.source debe ser 'local'")
                plugin_dir = root / entry["source"]["path"]
                if not plugin_dir.is_dir():
                    fail(f"codex-marketplace: la ruta declarada no existe: {entry['source']['path']}")
                else:
                    plugin = json.loads((plugin_dir / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
                    if plugin.get("version") != VERSION:
                        fail("codex-marketplace: la version del plugin no coincide")
            except Exception as exc:
                fail(f"codex-marketplace: manifiesto invalido: {exc}")

    # ---- igualdad byte a byte de las seis skills
    if "full" in roots:
        def digests(base: Path) -> dict[str, str]:
            return {
                p.relative_to(base).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(base.rglob("*")) if p.is_file()
            }

        reference = digests(skills_base("full", roots["full"]))
        for label, root in roots.items():
            if digests(skills_base(label, root)) != reference:
                fail(f"{label}: las skills difieren byte a byte de las del paquete full")

    # ---- checksums
    sums = dist / "SHA256SUMS.txt"
    if not sums.is_file():
        fail("Falta SHA256SUMS.txt")
    else:
        recorded = {}
        for line in sums.read_text(encoding="utf-8").strip().splitlines():
            digest, _, name = line.partition("  ")
            recorded[name] = digest
        for filename, _ in EXPECTED.values():
            archive = dist / filename
            if not archive.is_file():
                continue
            actual = hashlib.sha256(archive.read_bytes()).hexdigest()
            if filename not in recorded:
                fail(f"{filename}: no figura en SHA256SUMS.txt")
            elif recorded[filename] != actual:
                fail(f"{filename}: hash de SHA256SUMS.txt no coincide con el archivo")

    tempdir.cleanup()

    if errors:
        print("Validacion de artefactos FALLIDA:", file=sys.stderr)
        for message in errors:
            print(f"  - {message}", file=sys.stderr)
        raise SystemExit(1)
    print(f"Artefactos validos ({VERSION}): {len(EXPECTED)} paquetes verificados en {dist}")


if __name__ == "__main__":
    main()
