"""Draw chibi sprites (Hawks chibi v2 template) from a team's players.json.

Usage: python3 tools/make_sprites.py <team>        e.g. python3 tools/make_sprites.py bos
Reads  sprites/<team>/players.json, writes sprites/<team>/<id>_<kit>.png for every kit
in the file, plus sprites/<team>/sheet.png (a labelled check sheet).

players.json:
{
  "team": "Boston Celtics",
  "kits": {"home": {"jersey": [r,g,b], "shade": [...], "trim": [...], "trim2": [...], "band": [...]}, ...},
  "players": [
    {"id": "no27", "label": "#27", "skin": [r,g,b], "hair": "bald", "hair_color": [r,g,b],
     "beard": "none", "beard_color": [r,g,b], "headband": null, "sleeves": null, "armband": null,
     "shoes": [r,g,b], "shoe_accent": [r,g,b], "look_source": "photo"}
  ]
}
hair:  bald | curly_short | wavy_medium | afro_band (pair with "headband")
beard: none | short | full | thick
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAD = 4  # rows available above the head for tall hair

HEAD = [
    "........######.........",
    "......##SSSSSS##.......",
    ".....#SSSSSSSSSS#......",
    "....#SSSSSSSSSSSS#.....",
    "....#SSSSSSSSSSSSS#....",
    "....#SSSSSSSSSSSSS#....",
    "....#SSSSSSSSSSSSs#....",
    "....#S##SSS##SSSs##....",
    "....#SW#SSS#WSSSse#....",
    "....#SW#SSS#WSSSs#.....",
    "....#SSSSSSSSSSs#......",
    ".....#SSSMMSSSs#.......",
    "......#SSSSSSs#........",
    ".......#SSSSS##........",
]
BODY = [
    ".....##STTSSTTS###.....",
    "....#SS#TJTTJKT#SS#....",
    "...#SSS#TJJJJKT#SSS#...",
    "..#SSS##TJJJJKT##SSS#..",
    ".#SSS#.#TJJJJKT#.#SSS#.",
    "#SSS#..#TJJJJKT#..#SSS#",
    "#S#S#..#BBBBBBB#..#S#S#",
    "##.#...#UJJJJKU#...#.##",
    "......#UJJJJJJKU#......",
    "......#UJJJ#JJKU#......",
    "......#SSS#.#SSS#......",
    "......#SSS#.#SSS#......",
    "......#SsS#.#SsS#......",
    "......#XXX#.#XXX#......",
    ".....#ZZZZ#.#ZZZZ#.....",
    ".....#ZQZZ#.#ZZQZ#.....",
    ".....#XXXX#.#XXXX#.....",
    "......####...####......",
]
TEMPLATE = HEAD + BODY  # 32 rows x 23 cols

# Hair overlays: rows are relative to the head top (row 0); negative rows grow upward.
# H = hair, h = hair highlight, # = outline, . = leave as is, _ = make transparent, D = headband, d = band shade
HAIR = {
    "bald": {1: "........ll.............", 2: ".......l...............", },
    "curly_short": {
        -2: ".......#.##.##.........",
        -1: "......#H#HH#HH##.......",
        0:  ".....#HHHhHHHhHH#......",
        1:  "....#HHhHHHhHHHHH#.....",
        2:  "....#HHHHhHHHhHHHH#....",
        3:  "....#HHHHHHHHHHHHH#....",
        4:  "....#HSSSSSSSSSHHH#....",
        5:  "....#SSSSSSSSSSSSH#....",
    },
    "wavy_medium": {
        -2: ".......######..........",
        -1: ".....##HHHHHHH##.......",
        0:  "....#HHHhhHHHHHH#......",
        1:  "...#HHHhHHHHhHHHH#.....",
        2:  "...#HHhHHHHHHHhHHH#....",
        3:  "...#HHHHHHhHHHHHHH#....",
        4:  "...#HHSHHHHSSSHHHH#....",
        5:  "....#SSHSSSSSSSSHH#....",
        6:  "....#SSSSSSSSSSSSH#....",
        7:  "....#S##SSS##SSSHH#....",
        8:  "....#SW#SSS#WSSSHH#....",
    },
    "afro_band": {
        -2: ".....##########........",
        -1: "....#HHhHHHHhHHH#......",
        0:  "...#HHHHhHHHHHhHHH#....",
        1:  "...#HHHHhHHHHHHHHHH#...",
        2:  "...#HHHHHHHHHHHHHHH#...",
        3:  "...#DDDDDDDDDDDDDDD#...",
        4:  "...#dDDDDDDDDDDDDDd#...",
        5:  "...#HSSSSSSSSSSSSHH#...",
        6:  "....#SSSSSSSSSSSSsH#...",
    },
}
# Beard overlays (B = beard, b = beard shade, M = mouth kept). Rows relative to head top.
BEARD = {
    "none": {},
    "short": {
        10: "....#BSSBBBBSSSB#......",
        11: ".....#BBBMMBBBb#.......",
        12: "......#BBBBBBb#........",
        13: ".......#BBBBB##........",
    },
    "full": {
        9:  "....#BW#SSS#WSSSB#.....",
        10: "....#BBSBBBBSSBB#......",
        11: ".....#BBBMMBBBB#.......",
        12: "......#BBBBBBB#........",
        13: ".......#BBBBBb#........",
    },
    "thick": {
        8:  "....#BW#SSS#WSSSBe#....",
        9:  "....#BW#SSS#WSSBB#.....",
        10: "....#BBBBBBBBBBBB#.....",
        11: "....#BBBBMMBBBBBb#.....",
        12: ".....#BBBBBBBBBb#......",
        13: "......#BBBBBBBb#.......",
        14: ".......#BBBBBB#........",
    },
}

def shade(c, k=0.78):
    return tuple(max(0, int(v * k)) for v in c)
def light(c, k=1.18):
    return tuple(min(255, int(v * k + 12)) for v in c)

OUTLINE = (14, 10, 12)

def make(p, kit):
    rows = [list("." * 23) for _ in range(PAD)] + [list(r) for r in TEMPLATE]
    def put(overlay, keep_head=True):
        for r, s in overlay.items():
            rr = r + PAD
            for c, ch in enumerate(s):
                if ch != '.':
                    rows[rr][c] = ch
    put(HAIR[p.get("hair", "bald")])
    put(BEARD[p.get("beard", "none")])
    skin = tuple(p["skin"]); hair = tuple(p.get("hair_color", (20, 16, 14)))
    beard = tuple(p.get("beard_color", hair))
    band = tuple(p.get("headband") or (240, 240, 240))
    sleeve = p.get("sleeves")
    pal = {
        '#': OUTLINE, 'S': skin, 's': shade(skin), 'e': shade(skin, 0.65),
        'W': (250, 250, 250), 'M': shade(skin, 0.6), 'l': light(skin, 1.12),
        'H': hair, 'h': light(hair, 1.6) if sum(hair) < 150 else light(hair),
        'B': beard, 'b': shade(beard), 'D': band, 'd': shade(band, 0.85),
        'J': tuple(kit["jersey"]), 'K': tuple(kit["shade"]), 'T': tuple(kit["trim"]),
        'U': tuple(kit["trim2"]), 'B_': tuple(kit["band"]),
        'X': (244, 244, 244), 'Z': tuple(p.get("shoes", (240, 240, 240))),
        'Q': tuple(p.get("shoe_accent", kit["trim"])),
    }
    im = Image.new('RGBA', (23, len(rows)), (0, 0, 0, 0))
    px = im.load()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in '._':
                continue
            if ch == 'B' and y == PAD + 20:  # waistband row uses the kit band colour
                col = pal['B_']
            else:
                col = pal[ch]
            px[x, y] = col + (255,)
    # waistband: the body template's B row is kit, not beard
    wy = PAD + len(HEAD) + 6
    for x, ch in enumerate(BODY[6]):
        if ch == 'B':
            px[x, wy] = pal['B_'] + (255,)
    # undershirt sleeves over the upper arms
    if sleeve:
        for (y, xs) in [(15, (5, 6, 16, 17)), (16, (4, 5, 6, 16, 17, 18)), (17, (3, 4, 5, 17, 18, 19))]:
            for x in xs:
                px[x, PAD + y] = tuple(sleeve) + (255,)
    if p.get("armband"):
        for x in (19, 20, 21):
            px[x, PAD + 19] = tuple(p["armband"]) + (255,)
    bbox = im.getbbox()
    return im.crop((0, bbox[1], 23, bbox[3]))

def main(team):
    d = os.path.join(ROOT, 'sprites', team)
    cfg = json.load(open(os.path.join(d, 'players.json')))
    kits = cfg["kits"]
    out = {}
    for p in cfg["players"]:
        for k, kit in kits.items():
            im = make(p, kit)
            im.save(os.path.join(d, f'{p["id"]}_{k}.png'))
            out[(p["id"], k)] = im
    # check sheet
    z, cw, ch = 5, 140, 230
    n = len(cfg["players"])
    sheet = Image.new('RGB', (40 + cw * max(n, 1), 60 + ch * len(kits)), (250, 250, 250))
    dr = ImageDraw.Draw(sheet)
    try:
        f = ImageFont.truetype(os.path.join(ROOT, 'fonts', 'Silkscreen-Regular.ttf'), 16)
        fb = ImageFont.truetype(os.path.join(ROOT, 'fonts', 'Silkscreen-Bold.ttf'), 24)
    except OSError:
        f = fb = ImageFont.load_default()
    dr.text((20, 14), f'{cfg["team"]} - chibi v2', font=fb, fill=(20, 20, 20))
    for ki, k in enumerate(kits):
        y0 = 60 + ki * ch
        dr.text((20, y0), k.upper(), font=f, fill=(120, 120, 120))
        for i, p in enumerate(cfg["players"]):
            im = out[(p["id"], k)]
            big = im.resize((im.width * z, im.height * z), Image.NEAREST)
            x = 20 + i * cw + (cw - big.width) // 2
            sheet.paste(big, (x, y0 + 20 + (190 - big.height)), big)
            lab = f'{p["label"]} {p.get("name", "")}'.strip()
            tw = dr.textlength(lab, font=f)
            dr.text((20 + i * cw + (cw - tw) / 2, y0 + 212), lab, font=f, fill=(30, 30, 30))
    sheet.save(os.path.join(d, 'sheet.png'))
    print(f'wrote {len(out)} sprites + sheet.png to sprites/{team}/')

if __name__ == '__main__':
    main(sys.argv[1])
