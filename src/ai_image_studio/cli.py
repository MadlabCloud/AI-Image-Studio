from __future__ import annotations
import argparse, json
from pathlib import Path
from .inspect import inspect_file
from .jobs import prepare_job
from .decision import validate_decision, decision_gaps, route_decision
from .capture_guide import validate_capture_request, capture_request_gaps, recommend_capture
from .masks import compare_mask_files
from .qc import validate_background, validate_dimensions, compare_pixels
from .export import export_webp, export_png
from .packaging import package_directory
from .user_config import write_default_user_config, read_and_validate_user_config
from .doctor import system_doctor

def emit(data): print(json.dumps(data, indent=2, ensure_ascii=False))

def main():
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
    elif ns.cmd=='prepare-job': out=prepare_job(json.loads(Path(ns.job_json).read_text(encoding='utf-8')),ns.workspace)
    elif ns.cmd=='validate-decision':
        decision=json.loads(Path(ns.decision_json).read_text(encoding='utf-8')); validate_decision(decision); out={'valid':True,'gaps':decision_gaps(decision)}
    elif ns.cmd=='route-decision': out=route_decision(json.loads(Path(ns.decision_json).read_text(encoding='utf-8')))
    elif ns.cmd=='validate-capture-request':
        req=json.loads(Path(ns.request_json).read_text(encoding='utf-8')); validate_capture_request(req); out={'valid':True,'gaps':capture_request_gaps(req)}
    elif ns.cmd=='recommend-capture': out=recommend_capture(json.loads(Path(ns.request_json).read_text(encoding='utf-8')))
    elif ns.cmd=='compare-masks': out=compare_mask_files(ns.mask_a,ns.mask_b)
    elif ns.cmd=='validate-background': out=validate_background(ns.image,ns.mask,ns.min_channel,ns.max_nonwhite_ratio)
    elif ns.cmd=='validate-output': out=validate_dimensions(ns.image,ns.width,ns.height,ns.format)
    elif ns.cmd=='compare-pixels': out=compare_pixels(ns.reference,ns.result,ns.mask)
    elif ns.cmd=='export-webp': out=export_webp(ns.source,ns.destination,ns.width,ns.height,ns.quality,ns.fit,ns.background_mode,ns.background)
    elif ns.cmd=='export-png': out=export_png(ns.source,ns.destination,ns.width,ns.height,ns.background_mode,ns.background)
    elif ns.cmd=='package': out=package_directory(ns.source_dir,ns.zip_path,ns.job_id)
    emit(out)

if __name__=='__main__': main()
