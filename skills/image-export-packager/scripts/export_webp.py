#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys
ROOT=Path(__file__).resolve().parents[3]; sys.path.insert(0,str(ROOT/'src'))
from ai_image_studio.export import export_webp
p=argparse.ArgumentParser(); p.add_argument('source'); p.add_argument('destination'); p.add_argument('--width',type=int,default=1000); p.add_argument('--height',type=int,default=1000); p.add_argument('--quality',type=int,default=86)
a=p.parse_args(); print(json.dumps(export_webp(a.source,a.destination,a.width,a.height,a.quality),indent=2))
