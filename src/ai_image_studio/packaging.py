from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import zipfile, json
from .hashing import sha256_file

def package_directory(source_dir: str | Path, zip_path: str | Path, job_id: str = "unassigned") -> dict:
    src, dst = Path(source_dir), Path(zip_path)
    if not src.is_dir(): raise NotADirectoryError(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    artifacts=[]
    files=[p for p in sorted(src.rglob('*')) if p.is_file() and p.resolve()!=dst.resolve()]
    for p in files:
        artifacts.append({"name": p.relative_to(src).as_posix(), "sha256": sha256_file(p), "bytes": p.stat().st_size, "role": "output"})
    manifest={"job_id": job_id, "artifacts": artifacts, "created_at": datetime.now(timezone.utc).isoformat()}
    with zipfile.ZipFile(dst,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as zf:
        for p in files: zf.write(p, arcname=p.relative_to(src).as_posix())
        zf.writestr('artifact-manifest.json', json.dumps(manifest, indent=2, ensure_ascii=False))
    return {"zip_path": str(dst.resolve()), "files": len(files), "bytes": dst.stat().st_size, "sha256": sha256_file(dst), "manifest": manifest}
