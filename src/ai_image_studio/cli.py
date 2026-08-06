"""Interfaz de linea de comandos.

Codigos de salida, alineados con los instaladores de ``adapters/``:

===  ==========================================================================
0    correcto
2    entrada invalida: archivo ausente, JSON mal formado, esquema incumplido
3    puerta fail-closed: el trabajo es valido pero no puede continuar, por
     ejemplo cuando el SHA-256 declarado no coincide con el original
4    error de entrada/salida
1    fallo interno no previsto; se muestra la traza completa
===  ==========================================================================
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .capture_guide import (
    capture_request_gaps,
    recommend_capture,
    validate_capture_request,
)
from .decision import decision_gaps, route_decision, validate_decision
from .doctor import system_doctor
from .errors import FailClosed
from .export import export_png, export_webp
from .inspect import inspect_file
from .jobs import prepare_job
from .masks import compare_mask_files
from .packaging import package_directory
from .qc import compare_pixels, validate_background, validate_dimensions
from .user_config import read_and_validate_user_config, write_default_user_config

EXIT_OK = 0
EXIT_INTERNAL = 1
EXIT_BAD_INPUT = 2
EXIT_FAIL_CLOSED = 3
EXIT_IO = 4

def emit(data): print(json.dumps(data, indent=2, ensure_ascii=False))

def load_json(path: str):
    """Lee un JSON del usuario.

    ``utf-8-sig`` en lugar de ``utf-8``: el Bloc de notas y PowerShell escriben UTF-8
    con BOM por defecto en Windows, y ``json.loads`` rechaza el BOM. Un archivo sin
    BOM se lee igual, asi que la lectura es correcta en los dos casos.
    """
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def main():
    """Punto de entrada. Traduce los fallos a codigos de salida y a un mensaje.

    Sin esto, cualquier error del usuario salia como traza de Python y todos los
    fallos compartian el codigo 1, de modo que no se podia distinguir un JSON mal
    escrito de una puerta de integridad que se niega a continuar.
    """
    try:
        _run()
    # El orden importa: FailClosed y JSONDecodeError heredan de ValueError, y
    # FileNotFoundError y FileExistsError heredan de OSError.
    except FailClosed as exc:
        _exit(EXIT_FAIL_CLOSED, f"puerta fail-closed: {exc}")
    except (FileNotFoundError, FileExistsError) as exc:
        _exit(EXIT_BAD_INPUT, f"entrada invalida: {exc}")
    except json.JSONDecodeError as exc:
        _exit(EXIT_BAD_INPUT, f"JSON mal formado: {exc}")
    except ValueError as exc:
        _exit(EXIT_BAD_INPUT, f"entrada invalida: {exc}")
    except OSError as exc:
        _exit(EXIT_IO, f"error de entrada/salida: {exc}")

def _exit(code: int, message: str):
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(code)

def _run():
    p=argparse.ArgumentParser(prog='ai-image-studio')
    sp=p.add_subparsers(dest='cmd',required=True)
    a=sp.add_parser('inspect'); a.add_argument('path')
    a=sp.add_parser('doctor'); a.add_argument('--workspace')
    a=sp.add_parser('init-config'); a.add_argument('destination'); a.add_argument('--workspace-root'); a.add_argument('--language',choices=['es','en'],default='es'); a.add_argument('--overwrite',action='store_true')
    a=sp.add_parser('validate-config'); a.add_argument('config_json')
    a=sp.add_parser('prepare-job'); a.add_argument('job_json'); a.add_argument('--workspace',required=True)
    a=sp.add_parser('validate-decision'); a.add_argument('decision_json')
    a=sp.add_parser('route-decision'); a.add_argument('decision_json')
    a=sp.add_parser('validate-capture-request'); a.add_argument('request_json')
    a=sp.add_parser('recommend-capture'); a.add_argument('request_json')
    a=sp.add_parser('compare-masks'); a.add_argument('mask_a'); a.add_argument('mask_b')
    a=sp.add_parser('validate-background'); a.add_argument('image'); a.add_argument('--mask'); a.add_argument('--min-channel',type=int,default=250); a.add_argument('--max-nonwhite-ratio',type=float,default=0.002)
    a=sp.add_parser('validate-output'); a.add_argument('image'); a.add_argument('--width',type=int,required=True); a.add_argument('--height',type=int,required=True); a.add_argument('--format')
    a=sp.add_parser('compare-pixels'); a.add_argument('reference'); a.add_argument('result'); a.add_argument('--mask')
    a=sp.add_parser('export-webp'); a.add_argument('source'); a.add_argument('destination'); a.add_argument('--width',type=int,default=1000); a.add_argument('--height',type=int,default=1000); a.add_argument('--quality',type=int,default=86); a.add_argument('--fit',choices=['contain','cover','stretch'],default='contain'); a.add_argument('--background-mode',choices=['preserve','transparent','solid'],default='preserve'); a.add_argument('--background',default='#FFFFFF')
    a=sp.add_parser('export-png'); a.add_argument('source'); a.add_argument('destination'); a.add_argument('--width',type=int); a.add_argument('--height',type=int); a.add_argument('--background-mode',choices=['preserve','transparent','solid'],default='preserve'); a.add_argument('--background',default='#FFFFFF')
    a=sp.add_parser('package'); a.add_argument('source_dir'); a.add_argument('zip_path'); a.add_argument('--job-id',default='unassigned')
    ns=p.parse_args()
    if ns.cmd=='inspect': out=inspect_file(ns.path)
    elif ns.cmd=='doctor': out=system_doctor(ns.workspace)
    elif ns.cmd=='init-config': out=write_default_user_config(ns.destination,ns.workspace_root,ns.language,ns.overwrite)
    elif ns.cmd=='validate-config': out=read_and_validate_user_config(ns.config_json)
    elif ns.cmd=='prepare-job': out=prepare_job(load_json(ns.job_json),ns.workspace)
    elif ns.cmd=='validate-decision':
        decision=load_json(ns.decision_json); validate_decision(decision); out={'valid':True,'gaps':decision_gaps(decision)}
    elif ns.cmd=='route-decision': out=route_decision(load_json(ns.decision_json))
    elif ns.cmd=='validate-capture-request':
        req=load_json(ns.request_json); validate_capture_request(req); out={'valid':True,'gaps':capture_request_gaps(req)}
    elif ns.cmd=='recommend-capture': out=recommend_capture(load_json(ns.request_json))
    elif ns.cmd=='compare-masks': out=compare_mask_files(ns.mask_a,ns.mask_b)
    elif ns.cmd=='validate-background': out=validate_background(ns.image,ns.mask,ns.min_channel,ns.max_nonwhite_ratio)
    elif ns.cmd=='validate-output': out=validate_dimensions(ns.image,ns.width,ns.height,ns.format)
    elif ns.cmd=='compare-pixels': out=compare_pixels(ns.reference,ns.result,ns.mask)
    elif ns.cmd=='export-webp': out=export_webp(ns.source,ns.destination,ns.width,ns.height,ns.quality,ns.fit,ns.background_mode,ns.background)
    elif ns.cmd=='export-png': out=export_png(ns.source,ns.destination,ns.width,ns.height,ns.background_mode,ns.background)
    elif ns.cmd=='package': out=package_directory(ns.source_dir,ns.zip_path,ns.job_id)
    emit(out)

if __name__=='__main__': main()
