#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from ai_image_studio.qc import validate_background
p=argparse.ArgumentParser(); p.add_argument('image'); p.add_argument('--mask'); p.add_argument('--min-channel',type=int,default=250); p.add_argument('--max-nonwhite-ratio',type=float,default=.002)
a=p.parse_args(); print(json.dumps(validate_background(a.image,a.mask,a.min_channel,a.max_nonwhite_ratio),indent=2))
