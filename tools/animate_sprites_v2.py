"""Animated chibi sprites, set 2: side-facing (3/4) moves.

Builds on tools/animate_sprites.py (set 1: camera-facing). Same idea, same players:
the head comes from tools/make_sprites.py and the limbs are a rig, so every pose works
for every player and kit. What set 2 adds:

  * a 3/4 head turned toward the hoop (features shifted, a nose, then mirrored), and a
    side rig: far arm and far leg drawn behind the torso in a darker shade
  * lean into runs, squash on gathers and landings, stretch at the top of jumps
  * new moves: running dribble, crossover, stepback, side jump shot, layup, side dunk
    with rim hang, block, defensive slide, rebound, chest pass, lob pass
  * per-frame effect tags for the replay to draw: dust, flash, rim shake, ball release

Poses are authored facing right; render(..., face=-1) mirrors them.

  python3 tools/animate_sprites_v2.py bos [out_dir] [player ...]   -> GIFs + frames.png
"""
import json, math, os, sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_sprites as ms
import animate_sprites as v1

ROOT = ms.ROOT
CW, CH = 56, 92
OX = (CW - 23) // 2
Y0 = CH - 2 - 17

TORSO_SIDE = [
    "......##TSSSSST##......",
    ".......#TJTTTJT#.......",
    ".......#TJJJJKT#.......",
    ".......#TJJJJKT#.......",
    ".......#TJJJJKT#.......",
    ".......#TJJJJKT#.......",
    ".......#NNNNNNN#.......",
    ".......#UJJJJKU#.......",
    "......#UJJJJJJKU#......",
    "......#UJJJ#JJKU#......",
]
SH = {"L": (9, 2), "R": (14, 2)}      # far / near shoulder
HP = {"L": (10, 10), "R": (13, 10)}   # far / near hip

def P(**k):
    k.setdefault("dx", 0); k.setdefault("dy", 0); k.setdefault("head", (0, 0))
    k.setdefault("front", ()); k.setdefault("ball", None); k.setdefault("sq", 1.0)
    k.setdefault("view", "side")
    return k

STAND = {"L": [(9, 13)], "R": [(14, 13)]}
CROUCH = {"L": [(12, 12), (8, 13)], "R": [(16, 12), (14, 13)]}
WIDE = {"L": [(6, 13)], "R": [(17, 13)]}
TUCK = {"L": [(12, 12), (9, 13)], "R": [(16, 11), (14, 12)]}
HANG = {"L": [(10, 13), (9, 15)], "R": [(14, 13), (14, 15)]}
CHEST = dict(R=[(18, 7), (18, 5)], L=[(12, 7), (14, 5)])   # both hands on a chest-high ball

POSES = {
    # ---- stance / idle (triple threat)
    "idle0": P(arms={"L": [(9, 6), (11, 8)], "R": [(16, 5), (18, 7)]}, ball=(19, 9), legs=STAND),
    "idle1": P(dy=1, arms={"L": [(9, 7), (11, 9)], "R": [(16, 6), (18, 8)]}, ball=(19, 10), legs=STAND),

    # ---- running dribble (lean forward, ball out in front)
    "run0": P(dx=1, head=(1, 0), legs={"L": [(8, 12), (6, 12)], "R": [(16, 11), (17, 13)]},
              arms={"L": [(11, 6), (13, 7)], "R": [(17, 5), (19, 8)]}, ball=(22, 10), ball_abs=True),
    "run1": P(dx=1, dy=-1, head=(1, 0), legs={"L": [(12, 11), (11, 12)], "R": [(13, 13)]},
              arms={"L": [(9, 6), (9, 8)], "R": [(17, 4), (19, 6)]}, ball=(23, 13), ball_abs=True,
              squash=True),
    "run2": P(dx=1, head=(1, 0), legs={"L": [(15, 11), (16, 13)], "R": [(9, 12), (7, 12)]},
              arms={"L": [(7, 6), (6, 8)], "R": [(17, 5), (19, 7)]}, ball=(22, 10), ball_abs=True),
    "run3": P(dx=1, dy=-1, head=(1, 0), legs={"L": [(13, 13)], "R": [(12, 11), (11, 12)]},
              arms={"L": [(9, 6), (10, 8)], "R": [(17, 5), (19, 8)]}, ball=(22, 8), ball_abs=True),

    # ---- crossover: squares up to the defender (camera-facing rig from set 1)
    "cross0": v1.P(dx=1, dy=1, arms={"L": [(2, 5), (1, 7)], "R": [(20, 5), (21, 7)]},
                   ball=(22, 11), ball_abs=True, legs={"L": [(5, 13)], "R": [(17, 13)]}),
    "cross1": v1.P(dy=2, arms={"L": [(4, 6), (6, 9)], "R": [(18, 6), (16, 9)]},
                   ball=(11, 14), ball_abs=True, squash=True, legs={"L": [(5, 13)], "R": [(17, 13)]}),
    "cross2": v1.P(dx=-1, dy=1, arms={"L": [(2, 5), (1, 7)], "R": [(20, 4), (21, 6)]},
                   ball=(0, 11), ball_abs=True, legs={"L": [(5, 13)], "R": [(17, 13)]}),
    "cross3": v1.P(dx=-1, dy=2, arms={"L": [(2, 6), (1, 8)], "R": [(20, 4), (21, 6)]},
                   ball=(0, 13), ball_abs=True, squash=True, legs={"L": [(5, 13)], "R": [(17, 13)]}),

    # ---- stepback
    "step0": P(dx=1, head=(1, 0), legs={"L": [(9, 13)], "R": [(16, 12), (17, 13)]},
               arms={"L": [(10, 6), (12, 7)], "R": [(17, 5), (19, 8)]}, ball=(21, 10)),
    "step1": P(dx=-1, head=(-1, 0), legs={"L": [(9, 11), (7, 12)], "R": [(13, 11), (11, 12)]},
               arms=CHEST, ball=(17, 4), ball_back=True),
    "step2": P(dy=2, sq=0.9, legs={"L": [(8, 12), (6, 13)], "R": [(16, 12), (15, 13)]},
               arms=CHEST, ball=(17, 4), ball_back=True),

    # ---- jump shot
    "js0": P(dy=2, sq=0.88, legs=CROUCH, arms=CHEST, ball=(17, 4), ball_back=True),
    "js1": P(legs={"L": [(10, 12), (9, 14)], "R": [(14, 12), (14, 14)]},
             arms={"L": [(8, -5), (12, -17)], "R": [(20, -4), (16, -16)]}, ball=(15, -20),
             front=("R",)),
    "js2": P(head=(0, -1), sq=1.06, legs=TUCK,
             arms={"L": [(8, -5), (11, -15)], "R": [(20, -8), (20, -19), (22, -18)]}, ball=(23, -25),
             front=("R",)),
    "js3": P(legs={"L": [(10, 12), (9, 14)], "R": [(14, 12), (14, 14)]},
             arms={"L": [(8, 4), (7, 7)], "R": [(20, -8), (20, -19), (22, -17)]}, front=("R",)),
    "land": P(dy=2, sq=0.9, legs=CROUCH, arms={"L": [(8, 5), (7, 8)], "R": [(17, 5), (19, 7)]}),

    # ---- layup (one-foot takeoff, ball up high on the near hand)
    "lay0": P(dx=1, head=(1, 0), legs={"L": [(8, 12), (7, 12)], "R": [(16, 11), (17, 13)]},
              arms={"L": [(12, 6), (15, 5)], "R": [(18, 6), (19, 4)]}, ball=(19, 5), ball_back=True),
    "lay1": P(dx=1, head=(1, 0), legs={"L": [(11, 13)], "R": [(16, 9), (15, 11)]},
              arms={"L": [(10, 5), (14, 2)], "R": [(18, 4), (19, 0)]}, ball=(19, -1), ball_back=True),
    "lay2": P(dx=1, head=(1, -1), sq=1.07, legs={"L": [(10, 13), (9, 15)], "R": [(16, 9), (15, 11)]},
              arms={"L": [(7, 4), (5, 7)], "R": [(20, -6), (21, -17)]}, ball=(22, -21), front=("R",)),
    "lay3": P(dx=1, head=(1, -1), legs={"L": [(10, 13), (9, 15)], "R": [(16, 10), (15, 12)]},
              arms={"L": [(7, 4), (5, 7)], "R": [(20, -6), (21, -18), (23, -17)]}, front=("R",)),
    "lay4": P(legs={"L": [(10, 12), (9, 14)], "R": [(14, 12), (14, 14)]},
              arms={"L": [(7, 4), (6, 7)], "R": [(17, -1), (19, -5)]}),

    # ---- dunk: launch, cock back behind the head, slam, rim hang
    "dk0": P(dy=2, sq=0.86, legs=CROUCH, arms=CHEST, ball=(17, 4), ball_back=True),
    "dk1": P(sq=1.08, legs={"L": [(10, 13), (9, 15)], "R": [(14, 13), (14, 15)]},
             arms={"L": [(13, -4), (15, -12)], "R": [(19, -5), (18, -13)]}, ball=(17, -17),
             front=("R",)),
    "dk2": P(head=(0, -1), legs=TUCK,
             arms={"L": [(14, -5), (20, -13)], "R": [(17, -9), (9, -19)]}, ball=(6, -20),
             ball_back=True),
    "dk3": P(head=(1, -1), legs=TUCK,
             arms={"L": [(10, 2), (8, 5)], "R": [(19, -11), (24, -14)]}, ball=(26, -10),
             front=("R",)),
    "dk4": P(legs=HANG, arms={"L": [(16, -8), (21, -17)], "R": [(19, -8), (23, -17)]}, front=("R",)),

    # ---- block
    "bk0": P(dy=2, sq=0.9, legs=CROUCH, arms={"L": [(11, 6), (13, 3)], "R": [(17, 6), (18, 3)]}),
    "bk1": P(sq=1.07, legs=TUCK, arms={"L": [(10, -7), (12, -18)], "R": [(16, -8), (18, -19)]},
             front=("R",)),
    "bk2": P(head=(1, 0), legs=TUCK, arms={"L": [(10, -7), (12, -17)], "R": [(18, -9), (23, -14)]},
             front=("R",)),

    # ---- defensive slide (low, arms wide)
    "df0": P(dy=2, sq=0.94, legs={"L": [(7, 12), (5, 13)], "R": [(17, 12), (18, 13)]},
             arms={"L": [(8, -1), (5, -5)], "R": [(18, 4), (22, 3)]}),
    "df1": P(dy=1, legs={"L": [(10, 12), (9, 13)], "R": [(14, 12), (15, 13)]},
             arms={"L": [(8, 0), (5, -4)], "R": [(18, 4), (22, 2)]}),

    # ---- rebound: two-hand reach, snap to chest
    "rb1": P(sq=1.07, legs=TUCK, arms={"L": [(10, -7), (12, -19)], "R": [(16, -7), (15, -19)]},
             ball=(14, -23), ball_back=True, front=("R",)),
    "rb2": P(dy=1, legs={"L": [(10, 12), (9, 14)], "R": [(14, 12), (14, 14)]},
             arms={"L": [(9, 7), (13, 4)], "R": [(18, 6), (17, 3)]}, ball=(15, 3), ball_back=True),

    # ---- chest pass + lob
    "ps0": P(legs=STAND, arms=CHEST, ball=(17, 4), ball_back=True),
    "ps1": P(dx=1, head=(1, 0), legs={"L": [(9, 13)], "R": [(17, 13)]},
             arms={"L": [(16, 4), (21, 4)], "R": [(20, 4), (24, 3)]}, ball=(27, 3), ball_back=True),
    "ps2": P(dx=1, head=(1, 0), legs={"L": [(9, 13)], "R": [(17, 13)]},
             arms={"L": [(16, 4), (22, 5)], "R": [(20, 4), (25, 5)]}),
    "lb1": P(legs=STAND, arms={"L": [(12, -5), (15, -14)], "R": [(18, -5), (18, -14)]},
             ball=(17, -18), front=("R",)),
    "lb2": P(head=(0, -1), legs=STAND, arms={"L": [(14, -5), (19, -13)], "R": [(19, -6), (22, -14)]},
             front=("R",)),
}

# (pose, hold in 30fps frames, air px, travel px this step, tags)
# tags: dust | flash | release | rimshake
MOVES = {
    "run":       [("run0", 3, 0, 2, ""), ("run1", 3, 1, 2, ""), ("run2", 3, 0, 2, ""), ("run3", 3, 1, 2, "")],
    "crossover": [("cross0", 4, 0, 0, ""), ("cross1", 2, 0, 0, "dust"), ("cross2", 4, 0, -3, "dust"),
                  ("cross3", 3, 0, 0, ""), ("cross2", 3, 0, 0, ""), ("cross1", 2, 0, 0, "dust"),
                  ("cross0", 4, 0, 3, "dust")],
    "stepback":  [("run0", 3, 0, 2, ""), ("step0", 4, 0, 2, "dust"), ("step1", 3, 4, -5, ""),
                  ("step1", 3, 5, -5, ""), ("step2", 5, 0, -1, "dust"), ("idle0", 8, 0, 0, "")],
    "jumpshot":  [("js0", 5, 0, 0, "dust"), ("js1", 3, 6, 0, ""), ("js1", 3, 11, 0, ""),
                  ("js2", 6, 13, 0, "release"), ("js3", 4, 10, 0, ""), ("js3", 3, 4, 0, ""),
                  ("land", 4, 0, 0, "dust"), ("idle1", 8, 0, 0, "")],
    "layup":     [("lay0", 3, 0, 3, ""), ("run2", 3, 0, 3, ""), ("lay0", 3, 0, 3, "dust"),
                  ("lay1", 3, 5, 2, ""), ("lay2", 4, 12, 1, ""), ("lay3", 5, 14, 0, "release"),
                  ("lay4", 4, 8, 0, ""), ("land", 4, 0, 0, "dust"), ("idle1", 8, 0, 0, "")],
    "dunk":      [("dk0", 6, 0, 0, "dust"), ("dk1", 3, 8, 1, ""), ("dk2", 4, 16, 1, ""),
                  ("dk3", 3, 18, 1, "flash rimshake"), ("dk4", 9, 18, 0, "rimshake"),
                  ("dk4", 3, 12, 0, ""), ("land", 5, 0, 0, "dust"), ("idle1", 8, 0, 0, "")],
    "block":     [("df0", 4, 0, 0, ""), ("bk0", 4, 0, 0, "dust"), ("bk1", 4, 10, 0, ""),
                  ("bk2", 4, 14, 0, "flash"), ("bk1", 4, 10, 0, ""), ("land", 5, 0, 0, "dust"),
                  ("df0", 6, 0, 0, "")],
    "defense":   [("df0", 4, 0, -2, ""), ("df1", 4, 0, -2, "dust"), ("df0", 4, 0, -2, ""),
                  ("df1", 4, 0, -2, ""), ("df0", 4, 0, 2, ""), ("df1", 4, 0, 2, "dust"),
                  ("df0", 4, 0, 2, ""), ("df1", 4, 0, 2, "")],
    "rebound":   [("bk0", 5, 0, 0, "dust"), ("bk1", 3, 8, 0, ""), ("rb1", 5, 14, 0, ""),
                  ("rb2", 4, 7, 0, ""), ("land", 5, 0, 0, "dust"), ("idle1", 8, 0, 0, "")],
    "pass":      [("ps0", 6, 0, 0, ""), ("ps1", 3, 0, 1, "release"), ("ps2", 6, 0, 0, ""),
                  ("idle0", 10, 0, 0, "")],
    "lob":       [("ps0", 5, 0, 0, ""), ("lb1", 4, 0, 0, ""), ("lb2", 6, 0, 0, "release"),
                  ("idle0", 10, 0, 0, "")],
}
# where the rim sits for moves that finish at it: template (x, y) at the move's peak air
RIM = {"dunk": (24, -15, 18), "layup": (26, -22, 14)}

# ---------------------------------------------------------------- drawing
def head_rows(p):
    rows = [list("." * 23) for _ in range(ms.PAD)] + [list(r) for r in ms.HEAD]
    for ov in (ms.HAIR[p.get("hair", "bald")], ms.BEARD[p.get("beard", "none")]):
        for r, s in ov.items():
            if 0 <= r + ms.PAD < len(rows):
                for c, ch in enumerate(s):
                    if ch != '.':
                        rows[r + ms.PAD][c] = ch
    return rows

_heads = {}
def side_head(p):
    """3/4 head facing right: features slide toward the face side, nose on the outline."""
    key = json.dumps(p, sort_keys=True)
    if key in _heads:
        return _heads[key]
    rows = head_rows(p)
    for r in range(ms.PAD + 7, ms.PAD + 13):          # eyes .. chin
        row = rows[r]
        ink = [i for i, ch in enumerate(row) if ch != '.']
        if len(ink) < 4:
            continue
        a, b = ink[0], ink[-1]
        inner = row[a + 1:b]
        row[a + 1:b] = inner[1:] + [inner[-1]]       # slide the face one px toward its side
    for r in (ms.PAD + 9, ms.PAD + 10):              # nose bump on the outline
        row = rows[r]
        a = next(i for i, ch in enumerate(row) if ch != '.')
        if row[a] == '#' and a > 0:
            row[a] = 'S' if row[a + 1] not in 'BH' else row[a + 1]
            row[a - 1] = '#'
    pal = v1.palette(p, None)
    im = Image.new('RGBA', (23, len(rows)), (0, 0, 0, 0))
    px = im.load()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch not in '._':
                px[x, y] = pal[ch] + (255,)
    im = im.transpose(Image.FLIP_LEFT_RIGHT)
    _heads[key] = im
    return im

def _limb(px, pts, fill_of, r_in=1.05, r_out=2.0):
    segs = list(zip(pts, pts[1:]))
    lens = [math.dist(a, b) for a, b in segs]
    xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
    for y in range(int(min(ys)) - 3, int(max(ys)) + 4):
        for x in range(int(min(xs)) - 3, int(max(xs)) + 4):
            if not (0 <= x < CW and 0 <= y < CH):
                continue
            best, arc, acc = 1e9, 0, 0
            for (a, b), L in zip(segs, lens):
                d, s = v1._seg_dist(x, y, a, b)
                if d < best:
                    best, arc = d, acc + s
                acc += L
            if best <= r_in:
                px[x, y] = fill_of(arc, sum(lens)) + (255,)
            elif best <= r_out:
                px[x, y] = ms.OUTLINE + (255,)

def _shoe(px, ax, ay, pal):
    rows = [".#XXX#", "#ZZZZ#", "#ZZQZ#", "#XXXX#", ".####."]
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            x, y = ax - 2 + i, ay + j
            if ch != '.' and 0 <= x < CW and 0 <= y < CH:
                px[x, y] = pal[ch] + (255,)

def _dim(pal, k=0.78):
    return {c: (ms.OUTLINE if c == '#' else ms.shade(v, k)) for c, v in pal.items()}

def _render_side(p, kit, pose, with_ball):
    pal = v1.palette(p, kit)
    far = _dim(pal)
    im = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    px = im.load()
    dx, dy = pose["dx"], pose["dy"] - p.get("tall", 0)   # "tall": longer legs, feet stay put
    T = lambda q: (OX + q[0] + dx, Y0 + q[1] + dy)
    A = lambda q: (OX + q[0], Y0 + q[1])

    def arm_fill(side, pl):
        sleeve = p.get("sleeves")
        full = next((a["color"] for a in p.get("sleeve_arm") or [] if a["side"] == side), None)
        wrist = next((a["color"] for a in p.get("wristbands") or [] if a["side"] == side), None)
        if p.get("armband") and side == "R":
            wrist = p["armband"]
        k = 0.78 if pl is far else 1.0
        def f(arc, total):
            if full and arc < total - 1.6: return ms.shade(tuple(full), k)
            if sleeve and arc < 3.2: return ms.shade(tuple(sleeve), k)
            if wrist and total - 3.0 <= arc < total - 1.6: return ms.shade(tuple(wrist), k)
            return pl['S']
        return f

    def leg(side, pl):
        pts = [T(HP[side])] + [A(q) for q in pose["legs"][side]]
        ax, ay = pts[-1]
        _limb(px, pts[:-1] + [(ax, ay - 1)], lambda a, t: pl['S'])
        _shoe(px, int(ax), int(ay), pl)

    def arm(side, pl, forearm_only=False):
        pts = [T(SH[side])] + [T(q) for q in pose["arms"][side]]
        fill = arm_fill(side, pl)
        if forearm_only:
            total = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
            off = total - math.dist(pts[-2], pts[-1])
            _limb(px, pts[-2:], lambda a, t: fill(a + off, total), r_out=1.6)
        else:
            _limb(px, pts, fill)
        hx, hy = pts[-1]
        for ox_, oy_ in ((0, 0), (1, 0), (0, 1), (1, 1)):
            x, y = int(round(hx)) + ox_ - 1, int(round(hy)) + oy_
            if 0 <= x < CW and 0 <= y < CH and px[x, y][3]:
                px[x, y] = pl['S'] + (255,)

    def ball():
        if with_ball and pose["ball"]:
            b = v1.ball_img(pose.get("squash"))
            cx, cy = (A if pose.get("ball_abs") else T)(pose["ball"])
            im.alpha_composite(b, (int(cx - b.width / 2), int(cy - b.height / 2)))

    leg("L", far)
    arm("L", far)
    leg("R", pal)
    for j, row in enumerate(TORSO_SIDE):
        for i, ch in enumerate(row):
            if ch != '.':
                x, y = T((i, j))
                px[x, y] = pal[ch] + (255,)
    if pose.get("ball_back"):
        ball()
    arm("R", pal)
    hx, hy = T((pose["head"][0], -18 + pose["head"][1]))
    im.alpha_composite(side_head(p), (int(hx), int(hy)))
    for s in pose["front"]:
        arm(s, pal if s == "R" else far, forearm_only=True)
    if not pose.get("ball_back"):
        ball()
    return im

def render(p, kit, pose, with_ball=True, face=1):
    """One frame, RGBA CW x CH, feet on row CH-2, template column 11 at x = OX + 11."""
    if pose.get("view") == "front":
        fr = v1.render(p, kit, pose, with_ball)
        im = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
        im.alpha_composite(fr, (OX - v1.OX, Y0 - v1.Y0))
    else:
        im = _render_side(p, kit, pose, with_ball)
    sq = pose.get("sq", 1.0)
    if sq != 1.0:                      # squash / stretch, anchored at the feet
        nh = round(CH * sq); nw = round(CW / math.sqrt(sq))
        big = im.resize((nw, nh), Image.NEAREST)
        out = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
        out.alpha_composite(big.crop((max(0, (nw - CW) // 2), max(0, nh - CH),
                                      max(0, (nw - CW) // 2) + min(nw, CW), nh)),
                            (max(0, (CW - nw) // 2), max(0, CH - nh)))
        im = out
    if face < 0:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return im

def ball_pos(pose, face=1, tall=0):
    """Ball centre in cell coords for a pose (before squash), or None."""
    if not pose.get("ball"):
        return None
    if pose.get("view") == "front":
        bx, by = pose["ball"]
        if not pose.get("ball_abs"):
            bx += pose["dx"]; by += pose["dy"]
        x, y = OX + bx, Y0 + by
    else:
        bx, by = pose["ball"]
        if not pose.get("ball_abs"):
            bx += pose["dx"]; by += pose["dy"] - tall
        x, y = OX + bx, Y0 + by
    return (x if face > 0 else CW - 1 - x), y

# ---------------------------------------------------------------- effects (shared with replays)
def dust(d, x, y, age, z=1):
    """Little dust puffs at a foot position; age in frames 0..7."""
    if age > 7:
        return
    r = 1 + age * 0.6
    col = (236, 222, 196)
    for k, sgn in ((0, -1), (1, 1)):
        cx = x + sgn * (3 + age * 1.2)
        cy = y - age * 0.4
        d.ellipse([cx - r, cy - r * 0.7, cx + r, cy + r * 0.7], outline=None, fill=col)

def flash(d, x, y, age):
    if age > 5:
        return
    L = 3 + age * 2
    col = (255, 236, 140)
    for ang in range(0, 360, 45):
        a = math.radians(ang)
        d.line([(x + math.cos(a) * (L - 2), y + math.sin(a) * (L - 2)),
                (x + math.cos(a) * L, y + math.sin(a) * L)], fill=col)

# ---------------------------------------------------------------- previews
def preview(team, out_dir, ids):
    cfg = json.load(open(os.path.join(ROOT, 'sprites', team, 'players.json')))
    players = {p["id"]: p for p in cfg["players"]}
    kits = list(cfg["kits"].items())
    p, (kname, kit) = players[ids[0]], kits[0]
    os.makedirs(out_dir, exist_ok=True)
    small = ImageFont.truetype(os.path.join(ROOT, 'fonts', 'Silkscreen-Regular.ttf'), 14)
    font = ImageFont.truetype(os.path.join(ROOT, 'fonts', 'Silkscreen-Bold.ttf'), 22)
    names = list(POSES)
    Z2, per = 4, 8
    rows = (len(names) + per - 1) // per
    sheet = Image.new('RGB', (per * CW * Z2, rows * (CH * Z2 + 26) + 50), (250, 250, 250))
    dd = ImageDraw.Draw(sheet)
    dd.text((14, 12), f'{p["name"]} ({kname}) - set 2 pose frames', font=font, fill=(20, 20, 20))
    for i, nm in enumerate(names):
        fr = render(p, kit, POSES[nm])
        big = fr.resize((CW * Z2, CH * Z2), Image.NEAREST)
        x0, y0 = (i % per) * CW * Z2, 50 + (i // per) * (CH * Z2 + 26)
        sheet.paste(big, (x0, y0), big)
        tw = dd.textlength(nm, font=small)
        dd.text((x0 + (CW * Z2 - tw) / 2, y0 + CH * Z2 + 2), nm, font=small, fill=(90, 90, 90))
    sheet.save(os.path.join(out_dir, 'frames_v2.png'))
    print('wrote', os.path.join(out_dir, 'frames_v2.png'))

if __name__ == '__main__':
    team = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'sprites', team, 'anim_preview')
    preview(team, out, sys.argv[3:] or ["tatum"])
