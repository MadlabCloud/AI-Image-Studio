from __future__ import annotations

import os
from pathlib import Path

from . import __version__
from .capture_guide import (
    capture_request_gaps,
    recommend_capture,
    validate_capture_request,
)
from .decision import decision_gaps, route_decision, validate_decision
from .doctor import system_doctor
from .export import export_png, export_webp
from .inspect import inspect_file
from .jobs import prepare_job
from .masks import compare_mask_files
from .packaging import package_directory
from .qc import compare_pixels, validate_background, validate_dimensions
from .user_config import validate_user_config


def _guard(path: str, output: bool = False) -> str:
    root = os.environ.get("AI_IMAGE_STUDIO_ALLOWED_ROOT")
    p = Path(path).expanduser().resolve()
    if root:
        allowed = Path(root).expanduser().resolve()
        target = p.parent if output else p
        if target != allowed and allowed not in target.parents:
            raise ValueError(f"Ruta fuera de AI_IMAGE_STUDIO_ALLOWED_ROOT: {p}")
    return str(p)

def _installed_mcp_version() -> str:
    try:
        from importlib.metadata import version

        return version("mcp")
    except Exception:  # pragma: no cover - metadata ausente o corrupta
        return "desconocida"

def build_server():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        import importlib.util

        if importlib.util.find_spec("mcp") is None:
            raise RuntimeError(
                "La capacidad MCP es opcional y no esta instalada. "
                'Instalala con: pip install "ai-image-studio[mcp]"'
            ) from exc
        raise RuntimeError(
            f"El paquete mcp {_installed_mcp_version()} esta instalado pero no expone "
            "mcp.server.fastmcp, por lo que el servidor no puede arrancar. "
            'Version compatible verificada: pip install "mcp>=1.14,<2". '
            "Ejecuta 'ai-image-studio doctor' para el diagnostico completo."
        ) from exc
    mcp=FastMCP("AI Image Studio")

    # FastMCP no acepta `version`, pero el servidor de bajo nivel si. Sin esto queda
    # en None y el handshake `initialize` devuelve la version del paquete mcp como si
    # fuera la del producto: un cliente veria "1.29.0" en lugar de la de AI Image Studio.
    low_level = getattr(mcp, "_mcp_server", None)
    if low_level is not None and hasattr(low_level, "version"):
        low_level.version = __version__

    @mcp.tool()
    def image_system_doctor(workspace: str | None = None) -> dict:
        """Comprueba dependencias esenciales, escritura local, skills instaladas y motores opcionales sin usar la red."""
        return system_doctor(_guard(workspace, output=True) if workspace else None)

    @mcp.tool()
    def image_validate_user_config(config: dict) -> dict:
        """Valida la configuración local y bloquea secretos en texto plano o servicios externos no autorizados."""
        validate_user_config(config)
        return {"valid": True}

    @mcp.tool()
    def image_inspect(path: str) -> dict:
        """Inspecciona un archivo local sin modificarlo: hash, tamaño, formato, dimensiones y metadatos técnicos permitidos."""
        return inspect_file(_guard(path))

    @mcp.tool()
    def image_prepare_job(job: dict, workspace: str) -> dict:
        """Valida un ImageJob, verifica el hash, preserva una copia inmutable y bloquea la especificación."""
        return prepare_job(job, _guard(workspace, output=True))

    @mcp.tool()
    def image_validate_decision(decision: dict) -> dict:
        """Valida las siete variables universales y devuelve las preguntas todavía recomendadas."""
        validate_decision(decision)
        return {"valid": True, "gaps": decision_gaps(decision)}

    @mcp.tool()
    def image_route_decision(decision: dict) -> dict:
        """Selecciona solo flujos implementados y devuelve estado planned para categorías pendientes."""
        return route_decision(decision)

    @mcp.tool()
    def image_validate_capture_request(request: dict) -> dict:
        """Valida los datos necesarios para recomendar una captura fotográfica según sujeto, luz, movimiento, dispositivo y recursos."""
        validate_capture_request(request)
        return {"valid": True, "gaps": capture_request_gaps(request)}

    @mcp.tool()
    def image_recommend_capture(request: dict) -> dict:
        """Genera un plan de captura conservador y trazable, con soporte específico solo para las dos generaciones móviles mantenidas."""
        return recommend_capture(request)

    @mcp.tool()
    def image_compare_masks(mask_a: str, mask_b: str) -> dict:
        """Compara dos máscaras independientes y devuelve IoU, precisión, recall, áreas, cajas y componentes."""
        return compare_mask_files(_guard(mask_a), _guard(mask_b))

    @mcp.tool()
    def image_validate_background(image: str, mask: str | None = None, min_channel: int = 250, max_nonwhite_ratio: float = 0.002) -> dict:
        """Valida un fondo blanco cuando la especificación del trabajo lo exige; usa máscara si está disponible."""
        return validate_background(_guard(image), _guard(mask) if mask else None, min_channel, max_nonwhite_ratio)

    @mcp.tool()
    def image_validate_output(image: str, width: int, height: int, expected_format: str | None = None) -> dict:
        """Valida dimensiones exactas, formato y ausencia de alpha accidental cuando corresponda."""
        return validate_dimensions(_guard(image), width, height, expected_format)

    @mcp.tool()
    def image_compare_pixels(reference: str, result: str, mask: str | None = None) -> dict:
        """Compara píxeles de referencia y resultado ya alineados; opcionalmente restringe la medición a una máscara."""
        return compare_pixels(_guard(reference), _guard(result), _guard(mask) if mask else None)

    @mcp.tool()
    def image_export_webp(source: str, destination: str, width: int = 1000, height: int = 1000, quality: int = 86, fit: str = "contain", background_mode: str = "preserve", background: str = "#FFFFFF") -> dict:
        """Exporta WebP sin imponer fondo: background_mode admite preserve, transparent o solid."""
        return export_webp(_guard(source), _guard(destination, output=True), width, height, quality, fit, background_mode, background)

    @mcp.tool()
    def image_export_png(source: str, destination: str, width: int | None = None, height: int | None = None, background_mode: str = "preserve", background: str = "#FFFFFF") -> dict:
        """Exporta PNG conservando fondo o transparencia, o aplicando un color sólido explícito."""
        return export_png(_guard(source), _guard(destination, output=True), width, height, background_mode, background)

    @mcp.tool()
    def image_package(source_dir: str, zip_path: str, job_id: str = "unassigned") -> dict:
        """Crea ZIP reproducible con manifiesto de artefactos y hashes SHA-256."""
        return package_directory(_guard(source_dir), _guard(zip_path, output=True), job_id)
    return mcp

def main():
    transport=os.environ.get('AI_IMAGE_STUDIO_MCP_TRANSPORT','stdio')
    try:
        server=build_server()
    except RuntimeError:
        raise
    except Exception as exc:
        # FastMCP importa pero la construccion falla (mcp 1.7-1.13 no resuelven las
        # anotaciones diferidas). Sin esto el usuario solo veria un TypeError crudo.
        raise RuntimeError(
            f"El paquete mcp {_installed_mcp_version()} esta instalado y expone "
            "mcp.server.fastmcp, pero el servidor no se puede construir: "
            f"{type(exc).__name__}: {exc}. "
            'Version compatible verificada: pip install "mcp>=1.14,<2". '
            "Ejecuta 'ai-image-studio doctor' para el diagnostico completo."
        ) from exc
    server.run(transport=transport)

if __name__=='__main__': main()
