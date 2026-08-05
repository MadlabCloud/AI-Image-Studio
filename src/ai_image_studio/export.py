from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageOps

def _flatten_white(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    bg = Image.new("RGBA", rgba.size, (255,255,255,255))
    bg.alpha_composite(rgba)
    return bg.convert("RGB")

def export_webp(source: str | Path, destination: str | Path, width: int = 1000, height: int = 1000, quality: int = 86, fit: str = "contain", background: str = "#FFFFFF") -> dict:
    if not (1 <= quality <= 100):
        raise ValueError("quality debe estar entre 1 y 100")
    src, dst = Path(source), Path(destination)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        rgb = _flatten_white(im)
        canvas_color = background
        if fit == "contain":
            fitted = ImageOps.contain(rgb, (width,height), method=Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", (width,height), canvas_color)
            x = (width-fitted.width)//2; y = (height-fitted.height)//2
            canvas.paste(fitted, (x,y)); out = canvas
        elif fit == "cover":
            out = ImageOps.fit(rgb, (width,height), method=Image.Resampling.LANCZOS, centering=(0.5,0.5))
        elif fit == "stretch":
            out = rgb.resize((width,height), Image.Resampling.LANCZOS)
        else:
            raise ValueError("fit debe ser contain, cover o stretch")
        out.save(dst, format="WEBP", quality=quality, method=6, optimize=True, exif=b"", icc_profile=b"")
    return {"path": str(dst.resolve()), "width": width, "height": height, "format": "webp", "quality": quality, "bytes": dst.stat().st_size, "metadata_removed": True}

def export_png(source: str | Path, destination: str | Path, width: int | None = None, height: int | None = None, background: str = "#FFFFFF") -> dict:
    src, dst = Path(source), Path(destination); dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        out = _flatten_white(im)
        if width and height:
            fitted = ImageOps.contain(out, (width,height), method=Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", (width,height), background)
            canvas.paste(fitted, ((width-fitted.width)//2,(height-fitted.height)//2)); out=canvas
        out.save(dst, format="PNG", optimize=True)
    return {"path": str(dst.resolve()), "width": out.width, "height": out.height, "format": "png", "bytes": dst.stat().st_size}
