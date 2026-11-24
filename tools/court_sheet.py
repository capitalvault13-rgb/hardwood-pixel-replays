"""Draws every home floor in data/courts.json into one labelled check sheet.

    python3 tools/court_sheet.py                 # all 30 -> data/courts_sheet.png
    python3 tools/court_sheet.py dal bos /tmp/x.png

Each tile is the full floor (aprons, sidelines, both hoops) at 1 px per art pixel, the scale the
replays draw at x3.
"""
import os, sys, json
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'lib'))
from broadcast import Arena, court_look, FLOOR, PS

def floor_tile(abbr):
    A = Arena.__new__(Arena)            # only the floor and hoops: skip the crowd and the 3x upscale
    A.look = court_look(abbr); A.floor_text = 'HARDWOOD INDEX'
    im = A._build_static().convert('RGBA')
    im.alpha_composite(A._build_hoops())
    x0, y0, x1, y1 = FLOOR
    return im.crop((x0, y0 - 2, x1, y1 + 1)).convert('RGB')

def main(args):
    db = json.load(open(os.path.join(ROOT, 'data', 'courts.json')))['courts']
    out = os.path.join(ROOT, 'data', 'courts_sheet.png')
    if args and args[-1].endswith('.png'): out = args.pop()
    teams = [a.lower() for a in args] or list(db)
    tiles = [(a, floor_tile(a)) for a in teams]
    tw, th = tiles[0][1].size
    cols = 3 if len(tiles) > 2 else len(tiles)
    rows = (len(tiles) + cols - 1) // cols
    pad, lab = 12, 22
    sheet = Image.new('RGB', (cols * (tw + pad) + pad, rows * (th + lab + pad) + pad), (18, 20, 28))
    d = ImageDraw.Draw(sheet); d.fontmode = '1'
    for i, (a, t) in enumerate(tiles):
        x = pad + (i % cols) * (tw + pad); y = pad + (i // cols) * (th + lab + pad)
        c = db[a]
        d.text((x, y + 4), f"{c['abbr']}  {c['city'].upper()}  ({c['floor']})", font=PS(8), fill=(230, 230, 230))
        sheet.paste(t, (x, y + lab))
    sheet.save(out)
    print(out, sheet.size)

if __name__ == '__main__':
    main(sys.argv[1:])
