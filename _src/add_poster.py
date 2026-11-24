#!/usr/bin/env python3
"""Turn a Burger of the Month poster into the web images the site uses.

usage: python3 _src/add_poster.py <poster file> <YYYY-MM> <slug>
Writes botm/<YYYY-MM>-<slug>.webp and .jpg (900px wide) and prints the width/height
to put in _src/botm.json. Only the web-sized copies are committed, not the original.
"""
import sys, pathlib
from PIL import Image
ROOT = pathlib.Path(__file__).resolve().parent.parent
W = 900

def add(src, ym, slug):
    im = Image.open(src).convert('RGB')
    h = round(im.height * W / im.width)
    im = im.resize((W, h), Image.LANCZOS)
    base = ROOT / 'botm' / f'{ym}-{slug}'
    im.save(base.with_suffix('.jpg'), quality=82, optimize=True, progressive=True)
    im.save(base.with_suffix('.webp'), quality=80, method=6)
    return W, h

if __name__ == '__main__':
    w, h = add(*sys.argv[1:4])
    print(f'"w": {w}, "h": {h}')
