from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?", default="dist")
    parser.add_argument("--output", default="SHA256SUMS.txt")
    args = parser.parse_args()
    directory = Path(args.directory).resolve()
    if not directory.is_dir():
        raise SystemExit(f"Directory not found: {directory}")
    files = sorted(p for p in directory.iterdir() if p.is_file() and p.name != args.output)
    output = directory / args.output
    # LF explicito: `sha256sum -c` rechaza las lineas terminadas en CRLF, y el archivo
    # debe ser identico lo genere Windows, Linux o macOS.
    body = "".join(f"{sha256(path)}  {path.name}\n" for path in files)
    output.write_bytes(body.encode("utf-8"))
    print(output)


if __name__ == "__main__":
    main()
