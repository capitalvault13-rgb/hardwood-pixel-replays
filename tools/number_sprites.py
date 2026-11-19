"""Add jersey numbers to a team's cut sprites (from tools/extract_sprites.py).

Usage: python3 tools/number_sprites.py <team>        e.g. python3 tools/number_sprites.py atl
Reads  sprites/<team>/plain/<id>_<kit>.png (native chibi grid, no numbers) and
       sprites/<team>/numbers.json: {"kits": {kit: {"number": [r,g,b], "number_outline": [r,g,b]}},
                                     "players": {id: "NN"}}
Writes sprites/<team>/<id>_<kit>.png at DETAIL (3x) size with the number drawn on the fine grid,
the same way tools/make_sprites.py does for drawn teams, plus sprites/<team>/sheet.png.
"""
import glob, json, os, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_sprites import DETAIL, draw_number, ROOT

BODY_ROWS = 18   # the chibi body is the bottom 18 rows; the jersey front is body rows 2-5

def main(team):
    d = os.path.join(ROOT, 'sprites', team)
    cfg = json.load(open(os.path.join(d, 'numbers.json')))
    out = {}
    for f in sorted(glob.glob(os.path.join(d, 'plain', '*_*.png'))):
        pid, kit = os.path.basename(f)[:-4].rsplit('_', 1)
        im = Image.open(f).convert('RGBA')
        assert im.width == 23, f
        top = (im.height - BODY_ROWS + 2) * DETAIL
        im = im.resize((23 * DETAIL, im.height * DETAIL), Image.NEAREST)
        num, k = cfg["players"].get(pid), cfg["kits"].get(kit, {})
        if num is not None and k.get("numbers", True):
            draw_number(im.load(), str(num), top, k["number"], k.get("number_outline"))
        im.save(os.path.join(d, f'{pid}_{kit}.png'))
        out[(pid, kit)] = im
    # check sheet
    ids = list(dict.fromkeys(p for p, _ in out))
    kits = [k for k in cfg["kits"] if any((p, k) in out for p in ids)]
    PER_ROW, z, cw, ch = 8, 2, 150, 260
    lines = (len(ids) + PER_ROW - 1) // PER_ROW
    sheet = Image.new('RGB', (40 + cw * min(len(ids), PER_ROW), 60 + (ch * lines + 30) * len(kits)), (250, 250, 250))
    dr = ImageDraw.Draw(sheet)
    font = lambda n, s: ImageFont.truetype(os.path.join(ROOT, 'fonts', n), s)
    f, fb = font('Silkscreen-Regular.ttf', 16), font('Silkscreen-Bold.ttf', 24)
    dr.text((20, 14), f'{cfg.get("team", team)} - chibi v2 (numbered)', font=fb, fill=(20, 20, 20))
    for ki, k in enumerate(kits):
        yk = 60 + ki * (ch * lines + 30)
        dr.text((20, yk), k.upper(), font=f, fill=(120, 120, 120))
        for i, pid in enumerate(ids):
            if (pid, k) not in out:
                continue
            im = out[(pid, k)]
            big = im.resize((im.width * z, im.height * z), Image.NEAREST)
            x0, y0 = 20 + (i % PER_ROW) * cw, yk + (i // PER_ROW) * ch
            sheet.paste(big, (x0 + (cw - big.width) // 2, y0 + 20 + (220 - big.height)), big)
            lab = f'#{cfg["players"].get(pid, "?")} {pid}'
            tw = dr.textlength(lab, font=f)
            dr.text((x0 + (cw - tw) / 2, y0 + 236), lab, font=f, fill=(30, 30, 30))
    sheet.save(os.path.join(d, 'sheet.png'))
    print(f'wrote {len(out)} numbered sprites + sheet.png to sprites/{team}/')

if __name__ == '__main__':
    main(sys.argv[1])
