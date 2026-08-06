"""Contrato de la interfaz de linea de comandos.

Antes, cualquier fallo salia como traza de Python y todos compartian el codigo 1:
un JSON mal escrito era indistinguible de una puerta de integridad que se niega a
continuar. Estas pruebas fijan los codigos y comprueban que el mensaje es legible.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

EXIT_OK = 0
EXIT_BAD_INPUT = 2
EXIT_FAIL_CLOSED = 3


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "ai_image_studio.cli", *args],
        capture_output=True, text=True, cwd=str(ROOT),
    )


@pytest.fixture
def imagen(tmp_path) -> Path:
    ruta = tmp_path / "generada.jpg"
    Image.new("RGB", (800, 600), (18, 122, 90)).save(ruta, "JPEG", quality=92)
    return ruta


def _job(imagen: Path, sha256: str) -> dict:
    job = json.loads((ROOT / "examples/job-product-strict.json").read_text(encoding="utf-8"))
    job["source"]["path"] = str(imagen)
    job["source"]["sha256"] = sha256
    return job


def test_a_correct_job_exits_zero(tmp_path, imagen):
    digest = hashlib.sha256(imagen.read_bytes()).hexdigest()
    job = tmp_path / "job.json"
    job.write_text(json.dumps(_job(imagen, digest)), encoding="utf-8")

    resultado = run_cli("prepare-job", str(job), "--workspace", str(tmp_path / "ws"))

    assert resultado.returncode == EXIT_OK, resultado.stderr
    assert json.loads(resultado.stdout)["status"] == "SOURCE_PRESERVED"


def test_a_wrong_declared_hash_is_a_fail_closed_gate(tmp_path, imagen):
    job = tmp_path / "job.json"
    job.write_text(json.dumps(_job(imagen, "0" * 64)), encoding="utf-8")

    resultado = run_cli("prepare-job", str(job), "--workspace", str(tmp_path / "ws"))

    assert resultado.returncode == EXIT_FAIL_CLOSED, resultado.stderr
    assert "fail-closed" in resultado.stderr
    assert "Traceback" not in resultado.stderr, "el usuario no deberia ver una traza"


def test_malformed_json_is_bad_input(tmp_path):
    roto = tmp_path / "roto.json"
    roto.write_text("{ esto no es json", encoding="utf-8")

    resultado = run_cli("prepare-job", str(roto), "--workspace", str(tmp_path / "ws"))

    assert resultado.returncode == EXIT_BAD_INPUT, resultado.stderr
    assert "JSON mal formado" in resultado.stderr
    assert "Traceback" not in resultado.stderr


def test_a_missing_file_is_bad_input(tmp_path):
    resultado = run_cli("inspect", str(tmp_path / "no-existe.png"))

    assert resultado.returncode == EXIT_BAD_INPUT, resultado.stderr
    assert "Traceback" not in resultado.stderr


def test_json_with_a_utf8_bom_is_accepted(tmp_path, imagen):
    """El Bloc de notas y PowerShell escriben UTF-8 con BOM por defecto en Windows.

    Antes, `json.loads` rechazaba el BOM y el usuario recibia un error incomprensible
    por haber guardado el archivo con el editor mas comun de su sistema.
    """
    digest = hashlib.sha256(imagen.read_bytes()).hexdigest()
    job = tmp_path / "job-bom.json"
    job.write_bytes(b"\xef\xbb\xbf" + json.dumps(_job(imagen, digest)).encode("utf-8"))

    resultado = run_cli("prepare-job", str(job), "--workspace", str(tmp_path / "ws"))

    assert resultado.returncode == EXIT_OK, resultado.stderr


def test_the_documented_exit_codes_exist_in_the_module():
    texto = (ROOT / "src/ai_image_studio/cli.py").read_text(encoding="utf-8")
    for nombre, valor in [
        ("EXIT_OK", 0), ("EXIT_INTERNAL", 1), ("EXIT_BAD_INPUT", 2),
        ("EXIT_FAIL_CLOSED", 3), ("EXIT_IO", 4),
    ]:
        assert f"{nombre} = {valor}" in texto, f"cli.py no define {nombre} = {valor}"
