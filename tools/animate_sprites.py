"""Animated chibi sprites: one pose library, every player and kit.

Usage:
  python3 tools/animate_sprites.py <team> [out_dir] [player ...]
      writes <out_dir>/<move>.gif previews (several players side by side, 6x)
      and <out_dir>/frames.png (every frame of every move, labelled).
      out_dir defaults to sprites/<team>/anim_preview.

How it works
  The head (face, hair, beard, headband) comes from tools/make_sprites.py, so it is the
  player's own look. The body is a rig: the torso and shorts are the chibi v2 template,
  and the arms and legs are drawn as outlined 3-px limbs between joint points. A pose is
  just those joint points plus a few offsets, so one pose library animates every player
  in every kit.

  Coordinates are the 23-px chibi template's own (x = column, y = row of the body
  template; the head sits on rows -18..-1). Arm and ball points move with the torso
  (dx/dy). Leg ankles stay where they are put, so feet stay planted when the torso dips.

  Jump height, travel and the ball's flight are NOT in the pose; the replay moves the
  sprite and the ball, as it does now. The previews fake a jump with the "air" value.
"""
import json, math, os, sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_sprites as ms

ROOT = ms.ROOT
CW, CH = 48, 84          # frame cell (native px)
OX = (CW - 23) // 2      # template column 0 in the cell
Y0 = CH - 2 - 17         # template body row 0 in the cell (feet at the bottom)

TORSO = [
    ".....##STTSSTTS###.....",
    "....#SS#TJTTJKT#SS#....",
    ".......#TJJJJKT#.......",
    ".......#TJJJJKT#.......",
    ".......#TJJJJKT#.......",
    ".......#TJJJJKT#.......",
    ".......#NNNNNNN#.......",
    ".......#UJJJJKU#.......",
    "......#UJJJJJJKU#......",
    "......#UJJJ#JJKU#......",
]
SHOULDER = {"L": (5, 2), "R": (17, 2)}
HIP = {"L": (8, 10), "R": (14, 10)}
STAND_LEGS = {"L": [(8, 13)], "R": [(14, 13)]}

BALL_PAT = ["..####..",
            ".#oooo#.",
            "#oo#ooo#",
            "#o#oooo#",
            "#oooo#o#",
            "#ooo#oo#",
            ".#oooo#.",
            "..####.."]

# ---------------------------------------------------------------- pose library
# arms: side -> [elbow, hand] (or [hand]); legs: side -> [knee, ankle] (or [ankle]);
# dx/dy: torso shift; head: extra head offset; ball: centre (moves with torso unless
# ball_abs); front: arms drawn over the head; ball_back: ball drawn behind the arms.
def P(**k):
    k.setdefault("dx", 0); k.setdefault("dy", 0); k.setdefault("head", (0, 0))
    k.setdefault("legs", STAND_LEGS); k.setdefault("front", ()); k.setdefault("ball", None)
    return k

ARMS_DOWN = {"L": [(3, 4), (2, 6)], "R": [(19, 4), (20, 6)]}
CROUCH_LEGS = {"L": [(7, 12), (7, 13)], "R": [(15, 12), (15, 13)]}
TUCK_LEGS = {"L": [(6, 12), (8, 12)], "R": [(16, 11), (14, 11)]}
DANGLE_LEGS = {"L": [(8, 12), (7, 14)], "R": [(14, 12), (15, 14)]}

POSES = {
    "idle0": P(arms=ARMS_DOWN),
    "idle1": P(dy=1, arms={"L": [(3, 4), (2, 5)], "R": [(19, 4), (20, 5)]}),

    # dribble, right hand, ball on the floor beside the right foot
    "drib0": P(dy=1, arms={"L": [(2, 4), (0, 5)], "R": [(20, 4), (21, 6)]},
               ball=(22, 10), ball_abs=True, legs=CROUCH_LEGS),
    "drib1": P(dy=1, arms={"L": [(2, 4), (0, 5)], "R": [(20, 5), (21, 7)]},
               ball=(22, 12), ball_abs=True, legs=CROUCH_LEGS),
    "drib2": P(dy=2, arms={"L": [(2, 5), (0, 6)], "R": [(20, 4), (21, 5)]},
               ball=(22, 13), ball_abs=True, legs=CROUCH_LEGS, squash=True),
    "drib3": P(dy=1, arms={"L": [(2, 4), (0, 5)], "R": [(20, 3), (21, 5)]},
               ball=(22, 11), ball_abs=True, legs=CROUCH_LEGS),

    # chest pass to screen-right
    "pass0": P(dy=1, arms={"L": [(4, 6), (8, 5)], "R": [(18, 6), (14, 5)]}, ball=(11, 4),
               ball_back=True, legs=CROUCH_LEGS),
    "pass1": P(dx=1, arms={"L": [(10, 4), (16, 3)], "R": [(21, 4), (22, 3)]}, ball=(20, 3),
               ball_back=True, legs={"L": [(8, 13)], "R": [(16, 13)]}),
    "pass2": P(dx=2, arms={"L": [(12, 3), (19, 2)], "R": [(22, 3), (26, 2)]}, ball=(28, 2),
               legs={"L": [(9, 13)], "R": [(17, 13)]}),
    "pass3": P(dx=1, arms={"L": [(4, 4), (3, 6)], "R": [(21, 3), (24, 3)]},
               legs={"L": [(8, 13)], "R": [(16, 13)]}),

    # jump (no ball)
    "jump0": P(dy=2, arms={"L": [(2, 6), (1, 8)], "R": [(20, 6), (21, 8)]}, legs=CROUCH_LEGS),
    "jump1": P(arms={"L": [(1, -4), (1, -11)], "R": [(21, -4), (21, -11)]}, legs=TUCK_LEGS),
    "jump2": P(dy=2, arms={"L": [(1, 3), (-1, 3)], "R": [(21, 3), (23, 3)]}, legs=CROUCH_LEGS),

    # jump shot: dip, set point, release, follow-through
    "shoot0": P(dy=2, arms={"L": [(4, 6), (8, 6)], "R": [(18, 6), (14, 6)]}, ball=(11, 5),
                ball_back=True, legs=CROUCH_LEGS),
    "shoot1": P(arms={"L": [(1, -6), (6, -19)], "R": [(21, -6), (16, -19)]}, ball=(11, -23),
                ball_back=True),
    "shoot2": P(head=(0, -1), arms={"L": [(2, -9), (6, -21)], "R": [(20, -9), (16, -22)]},
                ball=(11, -31), legs=TUCK_LEGS),
    "shoot3": P(arms={"L": [(2, -1), (1, -6)], "R": [(19, -8), (16, -18), (14, -16)]},
                front=("R",), legs=TUCK_LEGS),

    # one-hand tomahawk dunk (rim drawn by the preview at the peak)
    "dunk0": P(dy=2, arms={"L": [(4, 6), (8, 6)], "R": [(18, 6), (14, 6)]}, ball=(11, 5),
               ball_back=True, legs=CROUCH_LEGS),
    "dunk1": P(arms={"L": [(1, -3), (3, -11)], "R": [(22, -6), (21, -15)]}, ball=(21, -19),
               legs=TUCK_LEGS),
    "dunk2": P(head=(0, -1), arms={"L": [(1, -4), (4, -12)], "R": [(17, -11), (12, -18)]},
               ball=(11, -14), front=("R",), legs=TUCK_LEGS),
    "dunk3": P(arms={"L": [(2, -9), (7, -20)], "R": [(20, -9), (15, -20)]},
               ball=(11, -2), legs=DANGLE_LEGS),
}

# moves: (pose, hold in 30fps video frames, preview-only jump height in px)
MOVES = {
    "idle":    [("idle0", 12, 0), ("idle1", 12, 0)],
    "dribble": [("drib0", 3, 0), ("drib1", 3, 0), ("drib2", 3, 0), ("drib3", 3, 0)],
    "pass":    [("pass0", 6, 0), ("pass1", 3, 0), ("pass2", 4, 0), ("pass3", 6, 0),
                ("idle0", 10, 0)],
    "jump":    [("jump0", 5, 0), ("jump1", 3, 6), ("jump1", 4, 11), ("jump1", 4, 12),
                ("jump1", 3, 7), ("jump2", 5, 0), ("idle0", 10, 0)],
    "shoot":   [("shoot0", 6, 0), ("shoot1", 3, 4), ("shoot1", 3, 9), ("shoot2", 5, 11),
                ("shoot3", 4, 8), ("shoot3", 4, 3), ("jump2", 4, 0), ("idle0", 10, 0)],
    "dunk":    [("dunk0", 6, 0), ("dunk1", 3, 8), ("dunk1", 3, 15), ("dunk2", 3, 17),
                ("dunk3", 10, 17), ("dunk3", 4, 9), ("jump2", 5, 0), ("idle0", 10, 0)],
}
RIM_Y = -21  # template row of the rim at the dunk's peak (before the jump offset)

# ---------------------------------------------------------------- drawing
def head_layer(p):
    """The player's head rows (PAD + HEAD) as a coloured RGBA image, 23 x 18."""
    rows = [list("." * 23) for _ in range(ms.PAD)] + [list(r) for r in ms.HEAD]
    for ov in (ms.HAIR[p.get("hair", "bald")], ms.BEARD[p.get("beard", "none")]):
        for r, s in ov.items():
            if 0 <= r + ms.PAD < len(rows):
                for c, ch in enumerate(s):
                    if ch != '.':
                        rows[r + ms.PAD][c] = ch
    pal = palette(p, None)
    im = Image.new('RGBA', (23, len(rows)), (0, 0, 0, 0))
    px = im.load()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch not in '._':
                px[x, y] = pal[ch] + (255,)
    return im

def palette(p, kit):
    skin = tuple(p["skin"]); hair = tuple(p.get("hair_color", (20, 16, 14)))
    beard = tuple(p.get("beard_color", hair)); band = tuple(p.get("headband") or (240, 240, 240))
    pal = {'#': ms.OUTLINE, 'S': skin, 's': ms.shade(skin), 'e': ms.shade(skin, 0.65),
           'W': (250, 250, 250), 'M': ms.shade(skin, 0.6), 'l': ms.light(skin, 1.12),
           'H': hair, 'h': ms.light(hair, 1.6) if sum(hair) < 150 else ms.light(hair),
           'B': beard, 'b': ms.shade(beard), 'D': band, 'd': ms.shade(band, 0.85),
           'X': (244, 244, 244), 'Z': tuple(p.get("shoes", (240, 240, 240)))}
    if kit:
        pal.update({'J': tuple(kit["jersey"]), 'K': tuple(kit["shade"]), 'T': tuple(kit["trim"]),
                    'U': tuple(kit["trim2"]), 'N': tuple(kit["band"]),
                    'Q': tuple(p.get("shoe_accent", kit["trim"]))})
    return pal

def _seg_dist(px_, py_, a, b):
    ax, ay = a; bx, by = b
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy
    t = 0 if L2 == 0 else max(0, min(1, ((px_ - ax) * vx + (py_ - ay) * vy) / L2))
    return math.hypot(px_ - (ax + t * vx), py_ - (ay + t * vy)), t * math.sqrt(L2)

def limb(px, pts, fill_of, r_in=1.05, r_out=2.0):
    """Outlined 3-px limb along pts (cell coords). fill_of(arc, total) -> rgb for skin pixels."""
    segs = list(zip(pts, pts[1:]))
    lens = [math.dist(a, b) for a, b in segs]
    total = sum(lens)
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    for y in range(int(min(ys)) - 3, int(max(ys)) + 4):
        for x in range(int(min(xs)) - 3, int(max(xs)) + 4):
            if not (0 <= x < CW and 0 <= y < CH):
                continue
            best, arc, acc = 1e9, 0, 0
            for (a, b), L in zip(segs, lens):
                d, s = _seg_dist(x, y, a, b)
                if d < best:
                    best, arc = d, acc + s
                acc += L
            if best <= r_in:
                px[x, y] = fill_of(arc, total) + (255,)
            elif best <= r_out:
                px[x, y] = ms.OUTLINE + (255,)

def shoe(px, ax, ay, side, pal):
    rows = ["#XXX#.", "#ZZZZ#", "#ZQZZ#", "#XXXX#", ".####."]
    if side == "R":
        rows = [r[::-1] for r in rows]
    x0 = ax - 3 if side == "L" else ax - 2
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            x, y = x0 + i, ay + j
            if ch != '.' and 0 <= x < CW and 0 <= y < CH:
                px[x, y] = pal[ch] + (255,)

def ball_img(squash=False):
    im = Image.new('RGBA', (8, 8), (0, 0, 0, 0))
    px = im.load()
    for y, row in enumerate(BALL_PAT):
        for x, ch in enumerate(row):
            if ch == '#': px[x, y] = (60, 24, 10, 255)
            elif ch == 'o': px[x, y] = (236, 112, 36, 255)
    px[2, 1] = px[3, 1] = (255, 180, 110, 255)
    if squash:
        im = im.resize((9, 7), Image.NEAREST)
    return im

def render(p, kit, pose, with_ball=True):
    """One frame: RGBA CW x CH, feet on row CH-2."""
    pal = palette(p, kit)
    im = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    px = im.load()
    dx, dy = pose["dx"], pose["dy"]
    T = lambda pt: (OX + pt[0] + dx, Y0 + pt[1] + dy)   # moves with torso
    A = lambda pt: (OX + pt[0], Y0 + pt[1])             # planted

    # legs (behind shorts) + shoes
    for side in ("L", "R"):
        pts = [T(HIP[side])] + [A(q) for q in pose["legs"][side]]
        ax, ay = pts[-1]
        limb(px, pts[:-1] + [(ax, ay - 1)], lambda a, t: pal['S'])
        shoe(px, int(ax), int(ay), side, pal)
    # arms that go behind the torso: none in this library; arms are drawn after the torso
    # torso
    for j, row in enumerate(TORSO):
        for i, ch in enumerate(row):
            if ch != '.':
                x, y = T((i, j))
                px[x, y] = pal[ch] + (255,)

    def arm_fill(side):
        sleeve = p.get("sleeves")
        full = next((a["color"] for a in p.get("sleeve_arm") or [] if a["side"] == side), None)
        wrist = next((a["color"] for a in p.get("wristbands") or [] if a["side"] == side), None)
        if p.get("armband") and side == "R":
            wrist = p["armband"]
        def f(arc, total):
            if full and arc < total - 1.6: return tuple(full)
            if sleeve and arc < 3.2: return tuple(sleeve)
            if wrist and total - 3.0 <= arc < total - 1.6: return tuple(wrist)
            return pal['S']
        return f

    def draw_arm(side, forearm_only=False):
        pts = [T(SHOULDER[side])] + [T(q) for q in pose["arms"][side]]
        fill = arm_fill(side)
        if forearm_only:  # last segment only, coloured as it is on the full arm
            total = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
            off = total - math.dist(pts[-2], pts[-1])
            limb(px, pts[-2:], lambda a, t: fill(a + off, total), r_out=1.6)
        else:
            limb(px, pts, fill)
        hx, hy = pts[-1]  # hand: a 2x2 knuckle block at the end
        for (ox, oy) in ((0, 0), (1, 0), (0, 1), (1, 1)):
            x, y = int(round(hx)) + ox - (1 if side == "L" else 0), int(round(hy)) + oy
            if 0 <= x < CW and 0 <= y < CH and px[x, y][3]:
                px[x, y] = pal['S'] + (255,)

    def draw_ball():
        if not (with_ball and pose["ball"]):
            return
        b = ball_img(pose.get("squash"))
        cx, cy = (A if pose.get("ball_abs") else T)(pose["ball"])
        im.alpha_composite(b, (int(cx - b.width / 2), int(cy - b.height / 2)))

    # upper arms always sit behind the big chibi head; "front" arms bring the forearm
    # and hand back over it
    if pose.get("ball_back"):
        draw_ball()
    for s in ("L", "R"):
        draw_arm(s)
    hx, hy = T((pose["head"][0], -18 + pose["head"][1]))
    im.alpha_composite(head_layer(p), (int(hx), int(hy)))
    for s in pose["front"]:
        draw_arm(s, forearm_only=True)
    if not pose.get("ball_back"):
        draw_ball()
    return im

# ---------------------------------------------------------------- previews
COURT = (196, 142, 88)
COURT2 = (184, 130, 78)

def preview(team, out_dir, ids):
    d = os.path.join(ROOT, 'sprites', team)
    cfg = json.load(open(os.path.join(d, 'players.json')))
    players = {p["id"]: p for p in cfg["players"]}
    kits = list(cfg["kits"].items())
    cast = [(players[i], kits[n % len(kits)]) for n, i in enumerate(ids)]
    Z = 6
    os.makedirs(out_dir, exist_ok=True)
    try:
        font = ImageFont.truetype(os.path.join(ROOT, 'fonts', 'Silkscreen-Bold.ttf'), 22)
        small = ImageFont.truetype(os.path.join(ROOT, 'fonts', 'Silkscreen-Regular.ttf'), 14)
    except OSError:
        font = small = ImageFont.load_default()
    head_room = 26  # native px of headroom for jumps
    for move, seq in MOVES.items():
        frames, durs = [], []
        for pose_name, hold, air in seq:
            pose = POSES[pose_name]
            W, H = CW * len(cast), CH + head_room
            bg = Image.new('RGBA', (W, H), COURT + (255,))
            g = ImageDraw.Draw(bg)
            for y in range(0, H, 4):
                g.line([(0, y), (W, y)], fill=COURT2 + (255,))
            for n, (p, (kname, kit)) in enumerate(cast):
                x0 = n * CW
                g.ellipse([x0 + OX + 2, H - 4, x0 + OX + 21 + 0, H - 1],
                          fill=(150, 104, 62, 255))  # shadow
                if move == "dunk":  # rim + net at the peak height
                    ry = head_room + Y0 + RIM_Y - 17
                    g.rectangle([x0 + OX + 2, ry - 12, x0 + OX + 20, ry - 1], fill=(240, 240, 240, 255),
                                outline=(60, 60, 60, 255))
                    g.line([(x0 + OX + 4, ry), (x0 + OX + 18, ry)], fill=(226, 84, 34, 255), width=1)
                    for k in range(5):
                        xx = x0 + OX + 5 + k * 3
                        g.line([(xx, ry + 1), (xx + 1, ry + 5)], fill=(250, 250, 250, 255))
                fr = render(p, kit, pose)
                bg.alpha_composite(fr, (x0, head_room - air))
            big = bg.resize((bg.width * Z, bg.height * Z), Image.NEAREST)
            dd = ImageDraw.Draw(big)
            dd.text((10, 8), move.upper(), font=font, fill=(255, 255, 255))
            for n, (p, (kname, _)) in enumerate(cast):
                lab = f'{p["name"].upper()} - {kname}'
                tw = dd.textlength(lab, font=small)
                dd.text((n * CW * Z + (CW * Z - tw) / 2, big.height - 22), lab, font=small,
                        fill=(60, 36, 16))
            frames.append(big.convert('RGB'))
            durs.append(round(hold * 1000 / 30))
        frames[0].save(os.path.join(out_dir, f'{move}.gif'), save_all=True,
                       append_images=frames[1:], duration=durs, loop=0, disposal=1)
    # contact sheet: every pose of the first cast member, labelled
    p, (kname, kit) = cast[0]
    names = list(POSES)
    Z2, per = 5, 7
    rows = (len(names) + per - 1) // per
    sheet = Image.new('RGB', (per * CW * Z2, rows * (CH * Z2 + 30) + 50), (250, 250, 250))
    dd = ImageDraw.Draw(sheet)
    dd.text((14, 12), f'{p["name"]} ({kname}) - every pose frame', font=font, fill=(20, 20, 20))
    for i, nm in enumerate(names):
        fr = render(p, kit, POSES[nm])
        big = fr.resize((CW * Z2, CH * Z2), Image.NEAREST)
        x0, y0 = (i % per) * CW * Z2, 50 + (i // per) * (CH * Z2 + 30)
        sheet.paste(big, (x0, y0), big)
        tw = dd.textlength(nm, font=small)
        dd.text((x0 + (CW * Z2 - tw) / 2, y0 + CH * Z2 + 4), nm, font=small, fill=(90, 90, 90))
    sheet.save(os.path.join(out_dir, 'frames.png'))
    print(f'wrote {len(MOVES)} GIFs + frames.png to {out_dir}')

if __name__ == '__main__':
    team = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'sprites', team, 'anim_preview')
    ids = sys.argv[3:] or ["tatum", "pritchard", "queta"]
    preview(team, out, ids)
