from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

BACKGROUND_MODES = {"preserve", "transparent", "solid"}


def _prepare_background(img: Image.Image, mode: str, background: str) -> Image.Image:
    if mode not in BACKGROUND_MODES:
        raise ValueError("background_mode debe ser preserve, transparent o solid")
    if mode == "preserve":
        return img.copy()
    rgba = img.convert("RGBA")
    if mode == "transparent":
        return rgba
    canvas = Image.new("RGBA", rgba.size, background)
    canvas.alpha_composite(rgba)
    return canvas.convert("RGB")


def _new_canvas(mode: str, size: tuple[int, int], background: str) -> Image.Image:
    return Image.new("RGBA" if mode == "transparent" else "RGB", size, (0, 0, 0, 0) if mode == "transparent" else background)


def export_webp(source: str | Path, destination: str | Path, width: int = 1000, height: int = 1000, quality: int = 86, fit: str = "contain", background_mode: str = "preserve", background: str = "#FFFFFF") -> dict:
    if not (1 <= quality <= 100):
        raise ValueError("quality debe estar entre 1 y 100")
    src, dst = Path(source), Path(destination)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        base = _prepare_background(im, background_mode, background)
        if fit == "contain":
            fitted = ImageOps.contain(base, (width, height), method=Image.Resampling.LANCZOS)
            canvas = _new_canvas(background_mode, (width, height), background)
            canvas.paste(fitted, ((width - fitted.width) // 2, (height - fitted.height) // 2), fitted if fitted.mode == "RGBA" else None)
            out = canvas
        elif fit == "cover":
            out = ImageOps.fit(base, (width, height), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        elif fit == "stretch":
            out = base.resize((width, height), Image.Resampling.LANCZOS)
        else:
            raise ValueError("fit debe ser contain, cover o stretch")
        out.save(dst, format="WEBP", quality=quality, method=6, optimize=True, exif=b"", icc_profile=b"")
    return {"path": str(dst.resolve()), "width": width, "height": height, "format": "webp", "quality": quality, "background_mode": background_mode, "bytes": dst.stat().st_size, "metadata_removed": True}


def export_png(source: str | Path, destination: str | Path, width: int | None = None, height: int | None = None, background_mode: str = "preserve", background: str = "#FFFFFF") -> dict:
    src, dst = Path(source), Path(destination)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        out = _prepare_background(im, background_mode, background)
        if width and height:
            fitted = ImageOps.contain(out, (width, height), method=Image.Resampling.LANCZOS)
            canvas = _new_canvas(background_mode, (width, height), background)
            canvas.paste(fitted, ((width - fitted.width) // 2, (height - fitted.height) // 2), fitted if fitted.mode == "RGBA" else None)
            out = canvas
        out.save(dst, format="PNG", optimize=True)
    return {"path": str(dst.resolve()), "width": out.width, "height": out.height, "format": "png", "background_mode": background_mode, "bytes": dst.stat().st_size}
