from __future__ import annotations

import re
from hashlib import sha256
from pathlib import Path

_SAFE = re.compile(r"[^a-zA-Z0-9._-]+")

def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    p = Path(path)
    h = sha256()
    with p.open("rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()

def safe_filename(name: str) -> str:
    cleaned = _SAFE.sub("-", Path(name).name).strip(".-")
    if not cleaned:
        raise ValueError("El nombre de archivo no contiene caracteres seguros")
    return cleaned

def ensure_within(base: str | Path, candidate: str | Path) -> Path:
    base_p = Path(base).resolve()
    cand_p = Path(candidate).resolve()
    if cand_p != base_p and base_p not in cand_p.parents:
        raise ValueError(f"Ruta fuera del espacio permitido: {cand_p}")
    return cand_p
