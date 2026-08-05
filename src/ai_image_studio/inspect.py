from __future__ import annotations
from pathlib import Path
from typing import Any
import shutil, subprocess, json
from PIL import Image
from .hashing import sha256_file

RAW_EXTENSIONS = {".cr2", ".cr3", ".nef", ".arw", ".raf", ".rw2", ".orf", ".dng"}

def _exiftool(path: Path) -> dict[str, Any] | None:
    exe = shutil.which("exiftool")
    if not exe:
        return None
    proc = subprocess.run([exe, "-json", "-n", str(path)], capture_output=True, text=True, timeout=30, check=False)
    if proc.returncode != 0:
        return {"error": proc.stderr.strip() or "exiftool_failed"}
    raw = json.loads(proc.stdout)[0]
    allowed = ["FileType", "MIMEType", "ImageWidth", "ImageHeight", "Make", "Model", "LensModel", "ISO", "FNumber", "ExposureTime", "FocalLength", "ColorSpace", "DateTimeOriginal", "Orientation"]
    return {k: raw[k] for k in allowed if k in raw}

def inspect_file(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(p)
    result: dict[str, Any] = {
        "path": str(p.resolve()),
        "name": p.name,
        "extension": p.suffix.lower(),
        "bytes": p.stat().st_size,
        "sha256": sha256_file(p),
        "raw_container": p.suffix.lower() in RAW_EXTENSIONS,
    }
    result["exiftool"] = _exiftool(p)
    try:
        with Image.open(p) as img:
            result.update({
                "decoder": "Pillow",
                "format": img.format,
                "width": img.width,
                "height": img.height,
                "mode": img.mode,
                "has_alpha": "A" in img.getbands(),
                "icc_profile_present": bool(img.info.get("icc_profile")),
                "exif_tag_count": len(img.getexif()),
            })
    except Exception as exc:
        result["decoder"] = None
        result["pixel_decode_error"] = f"{type(exc).__name__}: {exc}"
    return result
