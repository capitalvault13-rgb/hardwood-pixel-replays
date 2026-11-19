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
hair:  bald | buzz | crop | curly_short | curly_high | wavy_medium | cornrows | locs
       | afro | locs_top | ... (see HAIR below)
       | afro_band | short_band | locs_band | locs_long_band   (the *_band styles take "headband": [r,g,b])
beard: none | mustache | goatee | chinstrap | short | full | thick | huge
numbers: drawn from "number" (or the "#NN" label) as 5x7 block digits on the fine (DETAIL) grid,
         in the kit's trim colour; a kit may set "number": [r,g,b], "number_outline": [r,g,b]
         or "numbers": false. Output PNGs are DETAIL (3x) the chibi grid.
extras: "earrings": [r,g,b], "armband", "sleeves" (undershirt), "sleeve_arm": [{"side": "left|right", "color"}],
        "wristbands": [{"side", "color"}], "socks"   (sides are as seen on screen)
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
    "curly_high": {
        -4: ".......#.##.##.........",
        -3: "......#H#HH#HH##.......",
        -2: ".....#HHHhHHHhHH#......",
        -1: ".....#HhHHHhHHHHH#.....",
        0:  ".....#HHHHhHHHhHHH#....",
        1:  "....#HHhHHHHHHHHHH#....",
        2:  "....#HHHHhHHHhHHHH#....",
        3:  "....#HHHHHHHHHHHHH#....",
        4:  "....#SSSSSSSSSSSHHH#...",
        5:  "....#SSSSSSSSSSSSH#....",
    },
    "buzz": {
        1:  "......##HHHHHH##.......",
        2:  ".....#HHhHHHHHHH#......",
        3:  "....#HHHHHHHhHHHH#.....",
        4:  "....#HHHHHHHHHHHHH#....",
        5:  "....#SSSSSSSSSSSHH#....",
    },
    "crop": {
        -1: "........######.........",
        0:  "......##HHHHHH##.......",
        1:  ".....#HHHhHHHHHH#......",
        2:  "....#HHHHHHHHhHHH#.....",
        3:  "....#HHHHHHHHHHHHH#....",
        4:  "....#HSSSSSSSSSHHH#....",
        5:  "....#SSSSSSSSSSSSH#....",
    },
    "cornrows": {
        -1: "........######.........",
        0:  "......##HhHhHh##.......",
        1:  ".....#HhHhHhHhHh#......",
        2:  "....#HhHhHhHhHhHh#.....",
        3:  "....#HhHhHhHhHhHhH#....",
        4:  "....#SSSSSSSSSSSHhH#...",
        5:  "....#SSSSSSSSSSSSH#H#..",
        6:  "...................H#..",
        7:  "...................H#..",
        8:  "...................H#..",
        9:  "...................H#..",
        10: "...................##..",
    },
    "locs": {   # thick locs framing the face to the jaw (strands added by _hang below)
        -2: ".......#.##.##.........",
        -1: "......#H#HH#HH##.......",
        0:  ".....#HHHhHHHhHH#......",
        1:  "....#HHhHHHhHHHHH#.....",
        2:  "...#HHHHhHHHhHHHHH#....",
        3:  "..#HHhHHHHHHHHHhHHH#...",
        4:  ".#HhHSSSSSSSSSSSHHhH#..",
        5:  ".#Hh#SSSSSSSSSSSSH#hH#.",
    },
    "locs_band": {   # locs with a headband (strands added by _hang below)
        -2: ".......#.##.##.........",
        -1: "......#H#HH#HH##.......",
        0:  ".....#HHHhHHHhHH#......",
        1:  "....#HHhHHHhHHHHH#.....",
        2:  "...#DDDDDDDDDDDDDDD#...",
        3:  "..#HdDDDDDDDDDDDDDdH#..",
        4:  ".#HhHSSSSSSSSSSSHHhH#..",
        5:  ".#Hh#SSSSSSSSSSSSH#hH#.",
    },
    "locs_long": {   # thinner locs falling past the jaw onto the shoulders (strands: _hang)
        -2: ".......#.##.##.........",
        -1: "......#H#HH#HH##.......",
        0:  ".....#HHHhHHHhHH#......",
        1:  "....#HHhHHHhHHHHH#.....",
        2:  "...#HHHHhHHHhHHHHH#....",
        3:  ".##HHhHHHHHHHHHhHHH##..",
        4:  "#HHhHSSSSSSSSSSSHHhHH#.",
        5:  "#H#H#SSSSSSSSSSSSH#H#H#",
    },
    "braids_back": {   # braids pulled back, long thin braids behind both ears (strands: _hang)
        -1: "........######.........",
        0:  "......##HhHhHh##.......",
        1:  ".....#HhHhHhHhHh#......",
        2:  "....#HhHhHhHhHhHh#.....",
        3:  "....#HhHhHhHhHhHhH#....",
        4:  "..#H#SSSSSSSSSSSHhH#...",
        5:  "..#H#SSSSSSSSSSSSH#H#..",
    },
    "cornrows_left": {   # cornrows with a single braid hanging on the screen-left side
        -1: "........######.........",
        0:  "......##HhHhHh##.......",
        1:  ".....#HhHhHhHhHh#......",
        2:  "....#HhHhHhHhHhHh#.....",
        3:  "...#HhHhHhHhHhHhH#.....",
        4:  "..#H#SSSSSSSSSSSHH#....",
        5:  "..#H#SSSSSSSSSSSSH#....",
        6:  "..#H#..................",
        7:  "..#H#..................",
        8:  "..#H#..................",
        9:  "..#H#..................",
        10: "..##...................",
    },
    "curly_top": {   # rounded curly top, wider than the tight-faded sides
        -3: ".......#.#.##.#........",
        -2: ".....##H#HH#HH##.......",
        -1: "....#HHHhHHHHhHH#......",
        0:  "...#HHhHHHHhHHHHH#.....",
        1:  "...#HHHHHhHHHHHhHH#....",
        2:  "....#HHhHHHHHhHHH#.....",
        3:  "....#sHHHHHHHHHHs#.....",
        4:  "....#SsSSSSSSSSSsS#....",
    },
    "twists_short": {   # flat short twists, sharp line-up receding at the temples
        0:  "......##HhHhHH##.......",
        1:  ".....#HhHhHhHhHH#......",
        2:  ".....#hHhHhHhHhH#......",
        3:  "....#SHhHhHhHhHhS#.....",
    },
    "afro_tail": {   # big messy afro with one thin braid hanging on the screen-left side
        -4: "......#..#.#..#........",
        -3: ".....#H##H#H##H#.......",
        -2: "....#HHHhHHHHhHH#......",
        -1: "...#HhHHHHHhHHHHH##....",
        0:  "..#HHHHhHHHHHHhHHHH#...",
        1:  ".#HHhHHHHHHhHHHHHHH#...",
        2:  "..#HHHHHHhHHHHHHhHHH#..",
        3:  ".#HHhHHHHHHHHHHHHHhH#..",
        4:  "..#HHHSSSSSSSSSSHHHH#..",
        5:  "..#H#HSSSSSSSSSSSSHH#..",
        6:  "..#H#...............#..",
        7:  "..#H#..................",
        8:  "..#H#..................",
        9:  "..#H#..................",
        10: "..#H#..................",
        11: "..##...................",
    },
    "twists_spiky": {   # freeform twists sticking up and out in two puffs
        -4: "...#.#..#.....#.#......",
        -3: "..#H#H##H#...#H#H#.#...",
        -2: "..#HHhHHH#.##HHHhH#H#..",
        -1: ".#HhHHHHHH#HHHHHHHHH#..",
        0:  "..#HHHhHHHHHhHHHHhHH#..",
        1:  ".#HHhHHHHhHHHHHhHHHHH#.",
        2:  "..#HHHHHHHHhHHHHHHHH#..",
        3:  ".#HhHHHHHHHHHHHHHhHHH#.",
        4:  "..#HHHSSSSSSSSSSSHHH#..",
        5:  "...##HSSSSSSSSSSSSH##..",
    },
    "high_tight": {   # short top, faded sides
        -1: "........######.........",
        0:  "......##HHHHHH##.......",
        1:  ".....#HHHHhHHHHH#......",
        2:  ".....#sHHHHHHHHs#......",
        3:  "....#SsHHHHHHHHsS#.....",
    },
    "messy_fringe": {   # textured top with pieces falling onto the forehead
        -2: ".......#.#####.........",
        -1: "......#H#HHhHH##.......",
        0:  ".....#HHHhHHHHHH#......",
        1:  "....#HHhHHHHHhHHH#.....",
        2:  "....#HHHHHhHHHHHHH#....",
        3:  "....#HHhHHHHHHhHHH#....",
        4:  "....#SHHSHHHSSSHHH#....",
        5:  "....#SSSSSSSSSSSSH#....",
    },
    "quiff": {   # side-swept quiff, faded sides
        -3: "......#####............",
        -2: ".....#HhHHH###.........",
        -1: ".....#HHhHHHHH##.......",
        0:  "......#HHHhHHHHH#......",
        1:  ".....#hHHHHHHhHHH#.....",
        2:  ".....#sHHHHHHHHHs#.....",
        3:  "....#SsSSSSSSSSSsS#....",
    },
    "swept_back": {   # medium length, swept up and back, full at the sides
        -2: "........######.........",
        -1: "......##HHhHHHH##......",
        0:  ".....#HHhHHHHhHHH#.....",
        1:  "....#HHHHhHHHHhHHH#....",
        2:  "....#HhHHHHhHHHHhH#....",
        3:  "....#HHHhHHHHHhHHH#....",
        4:  "....#HHSSSSSSSSSHH#....",
        5:  "....#HSSSSSSSSSSSH#....",
    },
    "fade_short": {   # textured top, skin-faded sides, line-up
        0:  "......##HHHHHH##.......",
        1:  ".....#HHhHHHhHHH#......",
        2:  ".....#HHHHHHHHHH#......",
        3:  "....#sHHHHHHHHHHs#.....",
        4:  "....#SsSSSSSSSSSsS#....",
    },
    "afro": {   # big round afro, no headband
        -4: ".......######..........",
        -3: ".....##HHhHHHH##.......",
        -2: "....#HHHHHHhHHHH#......",
        -1: "...#HHhHHHHHHHHhH#.....",
        0:  "...#HHHHHHhHHHHHHH#....",
        1:  "..#HHhHHHHHHHHhHHHH#...",
        2:  "..#HHHHHHHHhHHHHHHH#...",
        3:  "..#HHHHhHHHHHHHHhHH#...",
        4:  "...#HHSSSSSSSSSSHHH#...",
        5:  "....#SSSSSSSSSSSSH#....",
    },
    "locs_top": {   # locs on top falling forward and to the sides, faded sides
        -4: "......#.#..#.#.........",
        -3: ".....#H#H##H#H#........",
        -2: "....#HhH#HhH#HhH#......",
        -1: "...#HHHHHHhHHHHHH#.....",
        0:  "...#hHHhHHHHHhHHHh#....",
        1:  "...#H#HHHHHhHHHH#H#....",
        2:  "...#H#sHHHHHHHHs#H#....",
        3:  "....#ssSSSSSSSSss#.....",
    },
    "short_band": {
        -1: "........######.........",
        0:  "......##HHhHHH##.......",
        1:  ".....#HHHHHHhHHH#......",
        2:  "....#HhHHHHHHHHHH#.....",
        3:  "....#DDDDDDDDDDDD#.....",
        4:  "....#dDDDDDDDDDDDd#....",
    },
}
STRAND = {"thick": (".#Hh#", "#hH#."), "thin": ("..#H#", "#H#.."), "double": ("#H#H#", "#H#H#")}

def _hang(style, top, bottom, kind="thick", sides="lr"):
    """Hang hair strands outside the head outline (cols 0-4 and 18-22), so the face is untouched."""
    rows = HAIR[style]
    lp, rp = STRAND[kind]
    for r in range(top, bottom + 2):
        row = list(rows.get(r, "." * 23))
        for side, pat, x0 in (("l", lp, 0), ("r", rp, 18)):
            if side not in sides:
                continue
            if r > bottom:  # close the strand ends
                pat = "".join("#" if ch in "Hh" else "." for ch in pat)
            elif r % 2:
                pat = pat.translate(str.maketrans("Hh", "hH"))
            for i, ch in enumerate(pat):
                if ch != ".":
                    row[x0 + i] = ch
        rows[r] = "".join(row)

_hang("locs", 6, 11)
_hang("locs_band", 6, 10)
_hang("locs_long", 6, 14, "double")
_hang("braids_back", 6, 14, "thin")
HAIR["afro_long"] = {**HAIR["afro"], 4: HAIR["locs"][4], 5: HAIR["locs"][5]}   # big coils down to the jaw
_hang("afro_long", 6, 10)
HAIR["box_braids"] = {   # center-parted braids hanging to the jaw
    -1: "........######.........",
    0:  "......##HhH#hHh##......",
    1:  ".....#HhHhH#HhHhH#.....",
    2:  "....#HhHhHh#hHhHhH#....",
    3:  "...#HHhHhHh#hHhHhHH#...",
    4:  ".#HhHSSSSSSSSSSSHHhH#..",
    5:  ".#Hh#SSSSSSSSSSSSH#hH#.",
}
_hang("box_braids", 6, 11, "thin")
HAIR["long_hair"] = {**{r: HAIR["wavy_medium"][r] for r in range(-2, 4)},   # straight hair to the jaw
                     4: HAIR["locs"][4], 5: HAIR["locs"][5]}
_hang("long_hair", 6, 10)
HAIR["cornrows_flat"] = {r: HAIR["cornrows"][r] for r in range(-1, 5)}   # cornrows, no hanging braid
HAIR["cornrows_flat"][4] = "....#SSSSSSSSSSSHhH#..."
HAIR["locs_long_band"] = {**HAIR["locs_long"], 2: HAIR["locs_band"][2], 3: HAIR["locs_band"][3]}

# Beard overlays (B = beard, b = beard shade, M = mouth kept). Rows relative to head top.
BEARD = {
    "none": {},
    "mustache": {10: ".......BBBB............"},
    "goatee": {
        10: "....#SSSBBBBSSSs#......",
        11: ".....#SSSMMSSSs#.......",
        12: "......#SSBBSSs#........",
        13: ".......#SBBBS##........",
    },
    "chinstrap": {
        10: "....#BSSSSSSSSSB#......",
        11: ".....#BSSMMSSSB#.......",
        12: "......#BSSSSSB#........",
        13: ".......#BBBBB##........",
    },
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
    "huge": {   # very full beard that spills past the chin onto the chest
        8:  "....#BW#SSS#WSSSBe#....",
        9:  "...#BBW#SSS#WSSBBB#....",
        10: "...#BBBBBBBBBBBBBB#....",
        11: "...#BBBBBMMBBBBBBb#....",
        12: "...#BBBBBBBBBBBBBb#....",
        13: "....#BBBBBBBBBBBb#.....",
        14: ".....#BBBBBBBBBb#......",
        15: "......#bBBBBBBb#.......",
        16: ".......##bBBb##........",
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

# Sprites are drawn on the 23 px chibi grid, then saved DETAIL times larger so the jersey
# number can use finer pixels than the rest of the sprite. Replays draw sprite pixels at 3x,
# so a DETAIL=3 file is loaded at 1x and each number pixel is one screen pixel.
DETAIL = 3

# 5x7 block digits (2 px stems), drawn on the fine grid. The jersey front is body rows 2-5,
# cols 8-14 on the chibi grid = 21x12 fine pixels; two digits take 11 of the 21.
DIGITS = {
    "0": [".###.", "##.##", "##.##", "##.##", "##.##", "##.##", ".###."],
    "1": ["..##.", ".###.", "..##.", "..##.", "..##.", "..##.", ".####"],
    "2": [".###.", "##.##", "...##", "..##.", ".##..", "##...", "#####"],
    "3": ["####.", "...##", "...##", ".###.", "...##", "...##", "####."],
    "4": ["...##", "..###", ".#.##", "#..##", "#####", "...##", "...##"],
    "5": ["#####", "##...", "####.", "...##", "...##", "##.##", ".###."],
    "6": [".###.", "##...", "####.", "##.##", "##.##", "##.##", ".###."],
    "7": ["#####", "...##", "..##.", "..##.", ".##..", ".##..", ".##.."],
    "8": [".###.", "##.##", "##.##", ".###.", "##.##", "##.##", ".###."],
    "9": [".###.", "##.##", "##.##", ".####", "...##", "...##", ".###."],
}
NUM_ROW = PAD + len(HEAD) + 2   # chibi-grid row where the jersey front starts

def draw_number(px, num, top, col, outline=None):
    """Draw num on a DETAIL-scaled sprite; top is the fine-grid y of the jersey front."""
    num = num[-2:]
    x_mid = 8 * DETAIL + (7 * DETAIL) // 2
    width = 5 * len(num) + (len(num) - 1)
    x0, y0 = x_mid - width // 2, top + 2
    pts = set()
    for i, d in enumerate(num):
        for r, line in enumerate(DIGITS[d]):
            for c, ch in enumerate(line):
                if ch == '#':
                    pts.add((x0 + i * 6 + c, y0 + r))
    if outline:
        for (x, y) in pts:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if (x + dx, y + dy) not in pts:
                        px[x + dx, y + dy] = tuple(outline) + (255,)
    for (x, y) in pts:
        px[x, y] = tuple(col) + (255,)

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
    ARM = {"left": [(15, (5, 6)), (16, (4, 5, 6)), (17, (3, 4, 5)), (18, (2, 3, 4)), (19, (1, 2, 3)), (20, (1, 3))],
           "right": [(15, (16, 17)), (16, (16, 17, 18)), (17, (17, 18, 19)), (18, (18, 19, 20)), (19, (19, 20, 21)), (20, (19, 21))]}
    for acc in p.get("sleeve_arm") or []:
        for (y, xs) in ARM[acc["side"]][:5]:  # shoulder to wrist, hands stay bare
            for x in xs:
                px[x, PAD + y] = tuple(acc["color"]) + (255,)
    for acc in p.get("wristbands") or []:
        for x in ARM[acc["side"]][4][1]:
            px[x, PAD + 19] = tuple(acc["color"]) + (255,)
    if p.get("socks"):
        wy2 = PAD + len(HEAD) + 13
        for x, chh in enumerate(BODY[13]):
            if chh == 'X':
                px[x, wy2] = tuple(p["socks"]) + (255,)
    if p.get("earrings"):  # stud under the visible (screen-right) ear
        px[18, PAD + 9] = tuple(p["earrings"]) + (255,)
    if p.get("armband"):
        for x in (19, 20, 21):
            px[x, PAD + 19] = tuple(p["armband"]) + (255,)
    bbox = im.getbbox()
    im = im.crop((0, bbox[1], 23, bbox[3]))
    im = im.resize((23 * DETAIL, im.height * DETAIL), Image.NEAREST)
    num = str(p.get("number", p.get("label", "").lstrip("#")))
    if num.isdigit() and kit.get("numbers", True):
        draw_number(im.load(), num, (NUM_ROW - bbox[1]) * DETAIL,
                    kit.get("number", kit["trim"]), kit.get("number_outline"))
    return im

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
    # check sheet (wraps at PER_ROW players, like the Hawks sheet)
    PER_ROW = 8
    z, cw, ch = 2, 150, 270   # sprites are already DETAIL (3x) size
    n = len(cfg["players"])
    lines = (n + PER_ROW - 1) // PER_ROW
    sheet = Image.new('RGB', (40 + cw * min(n, PER_ROW), 60 + (ch * lines + 30) * len(kits)), (250, 250, 250))
    dr = ImageDraw.Draw(sheet)
    try:
        f = ImageFont.truetype(os.path.join(ROOT, 'fonts', 'Silkscreen-Regular.ttf'), 16)
        fs = ImageFont.truetype(os.path.join(ROOT, 'fonts', 'Silkscreen-Regular.ttf'), 8)
        fb = ImageFont.truetype(os.path.join(ROOT, 'fonts', 'Silkscreen-Bold.ttf'), 24)
    except OSError:
        f = fs = fb = ImageFont.load_default()
    dr.text((20, 14), f'{cfg["team"]} - chibi v2', font=fb, fill=(20, 20, 20))
    for ki, k in enumerate(kits):
        yk = 60 + ki * (ch * lines + 30)
        dr.text((20, yk), k.upper(), font=f, fill=(120, 120, 120))
        for i, p in enumerate(cfg["players"]):
            im = out[(p["id"], k)]
            big = im.resize((im.width * z, im.height * z), Image.NEAREST)
            col, line = i % PER_ROW, i // PER_ROW
            x0, y0 = 20 + col * cw, yk + line * ch
            sheet.paste(big, (x0 + (cw - big.width) // 2, y0 + 20 + (220 - big.height)), big)
            lab = f'{p["label"]} {p.get("name", "")}'.strip()
            lf = f
            for size in (14, 12, 10):  # shrink long names to fit the column
                if dr.textlength(lab, font=lf) <= cw - 6 or not hasattr(f, 'font_variant'):
                    break
                lf = f.font_variant(size=size)
            tw = dr.textlength(lab, font=lf)
            dr.text((x0 + (cw - tw) / 2, y0 + 242), lab, font=lf, fill=(30, 30, 30))
            if ki == 0 and p.get("look_source"):
                src = f'{p["look_source"].split(":")[0]}: {p.get("hair", "bald").replace("_", " ")} / {p.get("beard", "none")}'
                tw = dr.textlength(src, font=fs)
                dr.text((x0 + (cw - tw) / 2, y0 + 260), src, font=fs, fill=(140, 140, 140))
    sheet.save(os.path.join(d, 'sheet.png'))
    print(f'wrote {len(out)} sprites + sheet.png to sprites/{team}/')

if __name__ == '__main__':
    main(sys.argv[1])
