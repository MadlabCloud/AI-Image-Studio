from __future__ import annotations

from pathlib import Path
import shutil
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
DIST = ROOT / "dist"
TMP = ROOT / ".build-dist"


def ignored(rel: Path) -> bool:
    ignored_parts = {".git", ".pytest_cache", "__pycache__", ".build-dist", "dist", ".venv"}
    return any(part in ignored_parts for part in rel.parts) or rel.suffix in {".pyc", ".pyo"}


def zip_dir(source: Path, destination: Path, top_name: str) -> None:
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(source.rglob("*")):
            rel = path.relative_to(source)
            if path.is_file() and not ignored(rel):
                archive.write(path, Path(top_name) / rel)


def copy_common(stage: Path) -> None:
    for name in ("LICENSE", "NOTICE", "README.md"):
        shutil.copy2(ROOT / name, stage / name)


def main() -> None:
    shutil.rmtree(DIST, ignore_errors=True)
    DIST.mkdir()
    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir()

    zip_dir(ROOT, DIST / f"ai-image-studio-full-{VERSION}.zip", "ai-image-studio")

    for kind, manifest in (("claude", ".claude-plugin"), ("openai", ".codex-plugin")):
        stage = TMP / f"ai-image-studio-{kind}"
        stage.mkdir()
        shutil.copytree(ROOT / "skills", stage / "skills")
        shutil.copytree(ROOT / manifest, stage / manifest)
        copy_common(stage)
        zip_dir(stage, DIST / f"ai-image-studio-{kind}-plugin-{VERSION}.zip", "ai-image-studio")

    stage = TMP / "ai-image-studio-standalone-skills"
    stage.mkdir()
    shutil.copytree(ROOT / "skills", stage / "skills")
    copy_common(stage)
    zip_dir(stage, DIST / f"ai-image-studio-standalone-skills-{VERSION}.zip", "ai-image-studio")
    shutil.rmtree(TMP)
    print(DIST)


if __name__ == "__main__":
    main()
