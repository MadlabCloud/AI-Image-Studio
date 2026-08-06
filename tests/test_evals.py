"""Estructura de los casos de activacion de `evals/`.

Alcance deliberadamente limitado: comprobar que el archivo esta bien formado y que
todo lo que nombra existe. Medir si una skill *se activa de verdad* ante un prompt
exige un arnes con modelo, que no es una prueba determinista y no vive aqui.

Sin estas comprobaciones el archivo era datos muertos: nada lo leia, asi que una
skill renombrada lo dejaba obsoleto en silencio.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ACTIVATION = ROOT / "evals/activation.jsonl"
SKILL_NAMES = {p.name for p in (ROOT / "skills").iterdir() if p.is_dir()}


def casos() -> list[dict]:
    lineas = [linea for linea in ACTIVATION.read_text(encoding="utf-8").splitlines() if linea.strip()]
    return [json.loads(linea) for linea in lineas]


def test_the_activation_file_exists_and_is_not_empty():
    assert ACTIVATION.is_file(), "falta evals/activation.jsonl"
    assert casos(), "el archivo no contiene ningun caso"


def test_every_line_is_valid_json():
    for numero, linea in enumerate(ACTIVATION.read_text(encoding="utf-8").splitlines(), 1):
        if not linea.strip():
            continue
        try:
            json.loads(linea)
        except json.JSONDecodeError as exc:
            pytest.fail(f"linea {numero}: JSON invalido: {exc}")


def test_identifiers_are_unique():
    identificadores = [c["id"] for c in casos()]
    duplicados = {i for i in identificadores if identificadores.count(i) > 1}
    assert not duplicados, f"identificadores repetidos: {sorted(duplicados)}"


def test_every_case_has_a_prompt_and_an_expectation():
    for caso in casos():
        assert caso.get("id"), f"caso sin id: {caso}"
        assert caso.get("prompt"), f"{caso['id']}: sin prompt"
        assert "should_trigger" in caso or "should_not_trigger" in caso, (
            f"{caso['id']}: no declara ninguna expectativa"
        )


def test_every_named_skill_exists():
    """Renombrar una skill sin actualizar los evals los deja apuntando al vacio."""
    for caso in casos():
        for clave in ("should_trigger", "should_not_trigger"):
            for nombre in caso.get(clave, []):
                assert nombre in SKILL_NAMES, (
                    f"{caso['id']}.{clave} nombra '{nombre}', que no es una skill"
                )


def test_every_skill_is_covered_by_at_least_one_case():
    citadas = {n for c in casos() for n in c.get("should_trigger", [])}
    sin_cubrir = sorted(SKILL_NAMES - citadas)
    assert not sin_cubrir, f"skills sin ningun caso de activacion: {sin_cubrir}"
