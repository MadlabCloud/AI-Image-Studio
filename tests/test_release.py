from pathlib import Path
import hashlib
import subprocess
import sys

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


def test_github_release_assets_are_ignored_from_source_control():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "dist/" in gitignore
    assert "*.cr2" in gitignore
    assert ".env" in gitignore
