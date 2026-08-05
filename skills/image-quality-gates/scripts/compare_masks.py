#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys
ROOT=Path(__file__).resolve().parents[3]; sys.path.insert(0,str(ROOT/'src'))
from ai_image_studio.masks import compare_mask_files
p=argparse.ArgumentParser(); p.add_argument('a'); p.add_argument('b'); x=p.parse_args(); print(json.dumps(compare_mask_files(x.a,x.b),indent=2))
