"""Pixel Replay #003 - Wembanyama 50, NOP @ SAS, Nov 21 2026, and his MVP case.

Side-view court, animated with sprite set 2 (tools/animate_sprites_v2.py).
Renders frames to stdout (raw RGB) for ffmpeg.

  python3 episodes/003-wembanyama-50/replay.py stills <dir> 1.0 4.4 ...
  episodes/003-wembanyama-50/render.sh
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root
sys.path.insert(0, os.path.join(HERE, 'tools'))
import animate_sprites as v1
import animate_sprites_v2 as v2

W, H, FPS = 1080, 1920, 30
Z = 8
NW, NH = W // Z, H // Z          # 135 x 240 native view
WW = 360                         # native world width (camera pans)
DUR = 32.4
NF = int(FPS * DUR)

def F(name, size):
    # both fonts are drawn on an 8 px grid: only multiples of 8 keep every font pixel square
    return ImageFont.truetype(os.path.join(HERE, 'fonts', name), max(8, int(round(size / 8)) * 8))
PS = lambda s: F('PressStart2P-Regular.ttf', s)
SK = lambda s: F('Silkscreen-Regular.ttf', s)
SKB = lambda s: F('Silkscreen-Bold.ttf', s)

NAVY = (12, 15, 26); WHITE = (238, 236, 228); GOLD = (250, 196, 40); GREY = (120, 124, 140)
LGREY = (176, 178, 190); BLACK = (8, 8, 12); LINE = (236, 226, 204); RIM_C = (232, 96, 32)
SAS_C = (40, 40, 46); SAS_HI = (196, 200, 206); NOP_C = (12, 35, 64)

# ---------------------------------------------------------------- cast
cfg = json.load(open(os.path.join(HERE, 'sprites', 'sas', 'players.json')))
WEMBY = cfg["players"][0]
SAS_KIT = cfg["kits"]["home"]
TALL = WEMBY.get("tall", 0)
NOP_KIT = {"jersey": [12, 35, 64], "shade": [8, 24, 46], "trim": [200, 16, 46],
           "trim2": [180, 151, 90], "band": [180, 151, 90]}
# generic Pelicans stand-ins: never labelled (same rule as the recoloured opponents in 002)
# PEL_A wears Yves Missi's #21: AP says the one-handed slam came over Missi (look not checked).
# PEL_B is generic: #30 is worn by no current Pelican, so he stands for no one.
PEL_A = {"skin": [150, 100, 72], "hair": "buzz", "hair_color": [20, 16, 14], "beard": "short",
         "beard_color": [26, 20, 18], "shoes": [244, 244, 244], "shoe_accent": [200, 16, 46], "number": "21"}
PEL_B = {"skin": [200, 150, 112], "hair": "curly_short", "hair_color": [30, 22, 18], "beard": "none",
         "shoes": [30, 30, 34], "shoe_accent": [180, 151, 90], "number": "30"}

# ---------------------------------------------------------------- world
GY = 205                  # ground line (feet), native
FLOOR_TOP = 167
RIM = (320, 155)          # rim centre, native world
BASELINE_X = 340
THREE_X = 172             # 23.75 ft from the rim at ~6 px/ft (Wemby 7-4 ~ 44 px)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def lerp(a, b, t): return a + (b - a) * t
def seg(t, t0, t1): return clamp((t - t0) / (t1 - t0))

def build_world():
    im = Image.new('RGB', (WW, NH), NAVY)
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(21)
    # tiered stands: rows of fans (2x2 heads over a darker shirt) with rails
    for row, y in enumerate(range(FLOOR_TOP - 16, 70, -9)):
        d.line([(0, y + 6), (WW, y + 6)], fill=(28, 30, 42))
        k = 1 - row * 0.07
        for x in range(row % 2 * 2, WW, 4):
            if rng.random() < 0.12: continue
            skin = [(110, 74, 54), (170, 120, 90), (210, 168, 136), (84, 56, 42)][int(rng.integers(0, 4))]
            shirt = [(40, 40, 46), (190, 194, 200), (60, 60, 70), (24, 24, 28)][int(rng.integers(0, 4))]
            sk = tuple(int(c * k * 0.75) for c in skin); sh = tuple(int(c * k * 0.6) for c in shirt)
            d.rectangle([x, y, x + 1, y + 1], fill=sk)
            d.rectangle([x, y + 2, x + 2, y + 4], fill=sh)
    d.rectangle([0, FLOOR_TOP - 9, WW, FLOOR_TOP - 1], fill=(22, 24, 34))      # ad board
    for x in range(0, WW, 6):
        d.point((x + 2, FLOOR_TOP - 5), fill=(70, 74, 96))
    # floor
    # maple planks: 3-px boards of uneven length, a tone each, dark seam at the joins
    tones = [(226, 192, 144), (218, 182, 134), (232, 200, 152), (222, 186, 138)]
    for y in range(FLOOR_TOP, NH, 3):
        x = -int(rng.integers(0, 40))
        while x < WW:
            L = int(rng.integers(24, 64))
            d.rectangle([x, y, x + L - 1, y + 2], fill=tones[int(rng.integers(0, 4))])
            d.line([(x, y), (x, y + 2)], fill=(196, 158, 112))
            x += L
        d.line([(0, y + 2), (WW, y + 2)], fill=(210, 172, 126))
    sl = lambda x: [(x + 4, FLOOR_TOP), (x - 4, NH)]     # court lines lean a little (depth)
    # paint between free-throw line and baseline
    ft = RIM[0] - 15 * 6 + 4
    stain = Image.new('RGBA', im.size, (0, 0, 0, 0))     # paint: a stain over the planks, grain shows
    ImageDraw.Draw(stain).polygon([(ft + 4, FLOOR_TOP), (BASELINE_X + 4, FLOOR_TOP), (BASELINE_X - 4, NH),
                                   (ft - 4, NH)], fill=(110, 112, 124, 70))
    im.paste(Image.alpha_composite(im.convert('RGBA'), stain).convert('RGB'))
    d = ImageDraw.Draw(im)
    for x in (ft, BASELINE_X, THREE_X, RIM[0] - 47 * 6):
        d.line(sl(x), fill=(30, 30, 36))
    # hoop, side on: stanchion, arm, backboard edge, rim, net
    d.rectangle([343, GY - 18, 357, GY + 2], fill=(70, 74, 86), outline=(30, 30, 36))
    d.rectangle([348, GY - 86, 351, GY - 18], fill=(150, 156, 166))
    d.line([(349, GY - 82), (333, GY - 74)], fill=(150, 156, 166), width=2)
    d.rectangle([329, GY - 76, 332, GY - 42], fill=(240, 242, 246), outline=(60, 64, 76))
    return im
WORLD = build_world()

def draw_rim(d, shake=0):
    x, y = RIM; y += shake
    for k in range(5):
        xx = x - 7 + k * 3
        d.line([(xx, y + 1), (xx + (1 if k < 2 else -1), y + 8 + abs(shake) * 2)], fill=(250, 250, 250))
    d.line([(x - 6, y + 5), (x + 6, y + 5)], fill=(220, 220, 220))
    d.line([(x - 9, y), (x + 9, y)], fill=RIM_C)
    d.line([(x - 9, y - 1), (x - 8, y - 1)], fill=(170, 60, 20))
    d.line([(x + 9, y), (329, y)], fill=(120, 124, 136))

# ---------------------------------------------------------------- timeline (seconds)
T_B = 2.8                        # 2nd-quarter run + one-handed slam
T_RUN_END = T_B + 1.1
T_DK = T_RUN_END
T_SLAM = T_DK + 13 / FPS         # dk3
T_DROP = T_DK + 16 / FPS
T_C = 6.6                        # block at the other end (illustrative)
T_SHOOT_C = T_C + 0.5
T_SREL = T_SHOOT_C + 11 / FPS
T_SWAT = T_SREL + 0.17
T_BLK = T_SWAT - 12 / FPS
T_D = 9.6                        # halftime card
T_E = 12.6                       # the 50th point
T_JS = T_E + 0.6
T_REL = T_JS + 11 / FPS
T_MAKE = T_REL + 1.0
T_F = 17.0                       # final line
T_G = 20.5                       # history
T_H = 24.0                       # MVP ladder
T_H2 = 26.5                      # per-36 / minutes
T_I = 28.8                       # the catch + CTA

def state(seq, dt):
    """(i, pose, air, travel, tags, local frames) of a v2 move at dt seconds; holds the last step."""
    f = int(dt * FPS)
    acc, start = 0.0, 0
    for i, (p, hold, air, tr, tags) in enumerate(seq):
        if f < start + hold:
            k = (f - start) / hold
            return i, p, air, acc + tr * k, tags, f - start
        start += hold; acc += tr
    p, hold, air, tr, tags = seq[-1]
    return len(seq) - 1, p, air, acc, "", hold

def idle(t, ph=0.0):
    return "idle0" if int((t + ph) * FPS / 12) % 2 == 0 else "idle1"

def cycle(names, t, hold=3):
    return names[int(t * FPS / hold) % len(names)]

CELEB = [("land", 4, 0, 0, "dust"), ("bk1", 6, 8, 0, ""), ("land", 4, 0, 0, "dust"),
         ("bk1", 6, 8, 0, ""), ("land", 4, 0, 0, "dust"), ("idle0", 30, 0, 0, "")]

# actor(t) -> (x, pose, air, face, with_ball, tags, local)
def wemby(t):
    if t < T_B:                                   # hook: triple threat at the top
        return 196, idle(t), 0, 1, True, "", 0
    if t < T_RUN_END:                             # drive
        k = seg(t, T_B, T_RUN_END)
        return lerp(196, 305, ease(k) * 0.4 + k * 0.6), cycle(["run0", "run1", "run2", "run3"], t - T_B), \
            0, 1, True, "", 0
    if t < T_C:                                   # dunk, rim hang, land
        i, p, air, tr, tags, loc = state(v2.MOVES["dunk"], t - T_DK)
        air = air - TALL if air > TALL else air
        return 305 + tr, p, air, 1, i < 4, tags, loc
    if t < T_E:                                   # defends at the other end
        if t < T_BLK:
            return 282, cycle(["df0", "df1"], t - T_C, 6), 0, -1, False, "", 0
        i, p, air, tr, tags, loc = state(v2.MOVES["block"], t - T_BLK)
        return 282, p, air, -1, False, tags, loc
    if t < T_JS:
        return THREE_X, "idle0", 0, 1, True, "", 0
    if t < T_MAKE + 0.15:
        i, p, air, tr, tags, loc = state(v2.MOVES["jumpshot"], t - T_JS)
        return THREE_X, p, air, 1, i < 3, tags, loc
    i, p, air, tr, tags, loc = state(CELEB, t - T_MAKE - 0.15)
    return THREE_X, p, air, 1, False, tags, loc

def pel_a(t):
    """Rim protector on the slam, closes out on the 50th point."""
    if t < T_C:
        if t < T_SLAM - 0.3:
            return 326, cycle(["df0", "df1"], t, 6), 0, -1, False, "", 0
        seq = [("bk0", 3, 0, 0, ""), ("bk1", 8, 6, 0, ""), ("land", 5, 0, 0, "dust"), ("df0", 40, 0, 0, "")]
        i, p, air, tr, tags, loc = state(seq, t - (T_SLAM - 0.3))
        return 326, p, air, -1, False, tags, loc
    return None

def pel_b(t):
    """The shooter Wemby blocks."""
    if t >= T_E:          # closes out on the 50th point
        if t < T_JS + 0.05:
            return 210, "df0", 0, -1, False, "", 0
        seq = [("bk0", 4, 0, 0, ""), ("bk1", 10, 9, 0, ""), ("land", 5, 0, 0, "dust"), ("df1", 60, 0, 0, "")]
        i, p, air, tr, tags, loc = state(seq, t - T_JS - 0.05)
        return 210, p, air, -1, False, tags, loc
    if t < T_C:
        return None
    if t < T_SHOOT_C:
        return 246, idle(t), 0, 1, True, "", 0
    i, p, air, tr, tags, loc = state(v2.MOVES["jumpshot"], t - T_SHOOT_C)
    if p == "idle1":
        p = "df0"
    return 246, p, air, 1, i < 3, "", loc

ACTORS = [(PEL_A, NOP_KIT, pel_a), (PEL_B, NOP_KIT, pel_b), (WEMBY, SAS_KIT, wemby)]

def origin(x, air, face):
    fx = (v2.OX + 11) if face > 0 else (v2.CW - 1 - (v2.OX + 11))
    return int(round(x - fx)), int(GY - (v2.CH - 2) - air)

def ball_world(p, pose_name, x, air, face):
    bx, by = v2.ball_pos(v2.POSES[pose_name], face, p.get("tall", 0))
    ox, oy = origin(x, air, face)
    return ox + bx, oy + by

def free_ball(t):
    """(x, y) of a loose ball, or None while someone holds it."""
    if T_DROP <= t < T_C:                           # through the net, bounces out
        dt = t - T_DROP
        y0, fl = RIM[1] + 3, GY - 4
        g = 700.0
        t1 = math.sqrt(2 * (fl - y0) / g)
        if dt < t1:
            y = y0 + 0.5 * g * dt * dt
        else:
            v = g * t1 * 0.5; tt = dt - t1; y = fl
            for _ in range(4):
                tb = 2 * v / g
                if tt < tb: y = fl - (v * tt - 0.5 * g * tt * tt); break
                tt -= tb; v *= 0.5
        return RIM[0] - 30 * clamp(dt / 1.5), y
    if T_SREL <= t < T_E:                           # shot, swatted
        a = ball_world(PEL_B, "js2", 246, 13, 1)
        ox, oy = origin(282, 14, -1)
        hx = ox + (v2.CW - 1 - (v2.OX + 23)); hy = oy + v2.Y0 - 14 - TALL
        if t < T_SWAT:
            k = seg(t, T_SREL, T_SWAT)
            return lerp(a[0], hx, k), lerp(a[1], hy, k) - 4 * math.sin(math.pi * k)
        dt = t - T_SWAT
        fl = GY - 4
        y = hy + 60 * dt + 500 * dt * dt
        if y > fl:  # bounce away
            tt = dt - (-60 + math.sqrt(60 * 60 + 4 * 500 * (fl - hy))) / 1000
            y = fl - max(0, 90 * tt - 350 * tt * tt)
        return hx - 120 * dt, y
    if T_REL <= t:                                  # the 50th point
        a = ball_world(WEMBY, "js2", THREE_X, 13, 1)
        b = (RIM[0], RIM[1] - 3)
        if t < T_MAKE:
            k = seg(t, T_REL, T_MAKE)
            return lerp(a[0], b[0], k), lerp(a[1], b[1], k) - 78 * math.sin(math.pi * k)
        dt = t - T_MAKE
        if dt < 0.25:
            return RIM[0], RIM[1] - 3 + 60 * dt
        dt -= 0.25
        fl = GY - 4
        y = RIM[1] + 12 + 400 * dt * dt
        if y >= fl:
            tt = dt - math.sqrt((fl - RIM[1] - 12) / 400)
            y = fl - max(0, 60 * tt - 300 * tt * tt)
        return RIM[0] - 20 * clamp(dt), y
    return None

def cam_x(t):
    if t < T_B:
        return 146
    if t < T_C:
        return lerp(146, WW - NW, ease(seg(t, T_B, T_RUN_END)))
    if t < T_E:
        return lerp(WW - NW, 200, ease(seg(t, T_C, T_C + 0.6)))
    if t < T_REL:
        return lerp(200, 116, ease(seg(t, T_E, T_E + 0.5)))
    if t < T_MAKE + 0.7:                 # follow the ball to the rim
        return lerp(116, WW - NW, ease(seg(t, T_REL, T_MAKE)))
    return lerp(WW - NW, 116, ease(seg(t, T_MAKE + 0.7, T_MAKE + 1.4)))

# ---------------------------------------------------------------- overlay helpers
def text_c(d, y, s, font, fill, cx=W // 2):
    tw = d.textlength(s, font=font)
    d.text((int(cx - tw / 2), int(y)), s, font=font, fill=fill)

def text_rich(d, y, s, font, base=WHITE, hi=GOLD, cx=W // 2):
    parts = [(p, hi if i % 2 else base) for i, p in enumerate(s.split('*')) if p]
    tw = sum(d.textlength(p, font=font) for p, _ in parts)
    x = cx - tw / 2
    for p, c in parts:
        d.text((int(x), int(y)), p, font=font, fill=c); x += d.textlength(p, font=font)

CAPS = [(0.0, '50 POINTS.', 'IN *32* MINUTES.'),
        (T_B, 'SECOND QUARTER.', 'ONE-HANDED *SLAM.*'),
        (T_C, 'AND AT THE OTHER END', '*DENIED.*'),
        (T_D, 'AND THAT WAS ONLY', 'THE FIRST *HALF.*'),
        (T_E, '6:29 LEFT IN THE 4TH.', 'ONE MORE *THREE.*'),
        (T_MAKE, "THAT'S *50.*", 'THEN HE SAT DOWN.'),
        (T_F, 'THE FULL LINE.', 'IN JUST *32* MINUTES.'),
        (T_G, 'NO ONE SINCE 1973-74', 'HAS DONE *THIS.*'),
        (T_H, 'SO WHERE DOES THAT', 'LEAVE THE MVP *RACE?*'),
        (T_H2, "THE GAP ISN'T TALENT.", "IT'S *MINUTES.*"),
        (T_I, 'LUKA OR WEMBY?', '*COMMENT* BELOW.')]
SOURCES = [(0.0, 'NOV 21 2026 / NBA.COM BOX SCORE / AP'),
           (T_H, 'NBA.COM KIA MVP LADDER, NOV 20 2026'),
           (T_I, 'NBA.COM PLAYER NEWS, NOV 24 2026')]

def score_state(t):
    if t < T_D: return None, None, '1ST HALF'
    if t < T_E: return 45, 61, 'HALFTIME'
    if t < T_MAKE: return 82, 105, '4TH 6:29'
    if t < T_F: return 82, 108, '4TH 6:29'
    return 91, 114, 'FINAL'

def draw_header(d, t):
    d.rectangle([0, 0, W, 214], fill=NAVY)
    f = PS(40)
    a, b = 'HARDWOOD ', 'INDEX'
    tw = d.textlength(a + b, font=f)
    x = W / 2 - tw / 2
    d.text((x, 26), a, font=f, fill=(222, 52, 52)); d.text((x + d.textlength(a, font=f), 26), b, font=f, fill=(66, 112, 222))
    text_c(d, 92, 'PIXEL REPLAY  #003', SK(32), GREY)
    sa, sb, per = score_state(t)
    d.rectangle([160, 137, 922, 202], fill=BLACK, outline=(62, 64, 78), width=3)
    d.rectangle([163, 140, 283, 199], fill=NOP_C)
    d.rectangle([440, 140, 560, 199], fill=SAS_C)
    f2 = PS(32)
    text_c(d, 154, 'NOP', f2, WHITE, cx=223); text_c(d, 154, '--' if sa is None else str(sa), f2, WHITE, cx=360)
    text_c(d, 154, 'SAS', f2, WHITE, cx=500); text_c(d, 154, '--' if sb is None else str(sb), f2, WHITE, cx=635)
    if T_MAKE <= t < T_MAKE + 0.6 and int((t - T_MAKE) * 10) % 2 == 0:
        text_c(d, 154, str(sb), f2, GOLD, cx=635)
    text_c(d, 168, per, SK(24), GREY, cx=800)

def draw_footer(d, t):
    d.rectangle([0, 1765, W, H], fill=NAVY)
    cap = [c for c in CAPS if c[0] <= t][-1]
    f = SKB(48)
    text_rich(d, 1774, cap[1], f); text_rich(d, 1826, cap[2], f)
    src = [s for s in SOURCES if s[0] <= t][-1][1]
    text_c(d, 1888, src, SK(24), (84, 88, 104))

def tag(d, x, y, label, num=None):
    f = PS(22)
    s = label if num is None else f'{label}  {num}'
    tw = d.textlength(s, font=f)
    bx0, by0 = x - tw / 2 - 12, y - 60
    d.rectangle([bx0, by0, bx0 + tw + 24, by0 + 38], fill=BLACK, outline=GOLD, width=3)
    if num is None:
        d.text((bx0 + 12, by0 + 9), s, font=f, fill=GOLD)
    else:
        d.text((bx0 + 12, by0 + 9), label, font=f, fill=WHITE)
        d.text((bx0 + 12 + d.textlength(label + '  ', font=f), by0 + 9), str(num), font=f, fill=GOLD)
    d.polygon([(x - 7, by0 + 38), (x + 7, by0 + 38), (x, by0 + 47)], fill=GOLD)

def chip(d, x, y, big, small, col=WHITE):
    f1, f2 = PS(44), SK(28)
    tw = max(d.textlength(big, font=f1), d.textlength(small, font=f2))
    d.text((x - d.textlength(big, font=f1) / 2, y), big, font=f1, fill=col)
    d.text((x - d.textlength(small, font=f2) / 2, y + 60), small, font=f2, fill=LGREY)

# ---------------------------------------------------------------- frame
def world_frame(t):
    im = WORLD.copy().convert('RGBA')
    d = ImageDraw.Draw(im)
    acts = []
    for p, kit, fn in ACTORS:
        st = fn(t)
        if st: acts.append((p, kit, st))
    # shadows: translucent, on whole pixels, shrinking with height
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    for p, kit, (x, pose, air, face, wb, tags, loc) in acts:
        sw = int(max(4, 10 - air * 0.3)); x = int(round(x))
        sd.ellipse([x - sw, GY - 1, x + sw, GY + 2], fill=(60, 30, 10, 80))
    fb = free_ball(t)
    if fb:
        bx = int(round(fb[0])); sd.ellipse([bx - 4, GY - 1, bx + 4, GY + 1], fill=(60, 30, 10, 80))
    im.alpha_composite(sh)
    # back to front: Pelicans behind Wemby
    wemby_head = None
    for p, kit, (x, pose, air, face, wb, tags, loc) in acts:
        spr = v2.render(p, kit, v2.POSES[pose], with_ball=wb, face=face)
        o = origin(x, air, face)
        im.alpha_composite(spr, o)
        if "dust" in tags:
            v2.dust(d, x, GY, loc)
        if p is WEMBY:
            wemby_head = (x, o[1] + v2.Y0 - 18 - TALL - 4)
    if fb:
        im.alpha_composite(v1.ball_img(), (int(round(fb[0] - 4)), int(round(fb[1] - 4))))
    # rim over the ball / hands; shake on the slam
    shake = 0
    if T_SLAM <= t < T_SLAM + 0.45:
        shake = 1 if int((t - T_SLAM) * FPS / 2) % 2 == 0 else -1
    draw_rim(d, shake)
    if T_SLAM <= t < T_SLAM + 6 / FPS:
        v2.flash(d, RIM[0], RIM[1] - 2, int((t - T_SLAM) * FPS))
    if T_SWAT <= t < T_SWAT + 6 / FPS:
        ox, oy = origin(282, 14, -1)
        v2.flash(d, ox + (v2.CW - 1 - (v2.OX + 23)), oy + v2.Y0 - 14 - TALL, int((t - T_SWAT) * FPS))
    if T_MAKE <= t < T_MAKE + 0.5:
        a = 1 - seg(t, T_MAKE, T_MAKE + 0.5)
        r = 6 + 14 * (1 - a)
        d.ellipse([RIM[0] - r, RIM[1] - r, RIM[0] + r, RIM[1] + r], outline=GOLD)
    return im, wemby_head

def frame(n):
    t = n / FPS
    world, head = world_frame(t)
    cx = cam_x(t)
    view = world.crop((int(round(cx)), 0, int(round(cx)) + NW, NH)).convert('RGB')
    img = view.resize((W, H), Image.NEAREST)
    d = ImageDraw.Draw(img, 'RGBA')
    d.fontmode = "1"   # no antialiasing: text stays on hard pixels like the sprites
    hx, hy = (head[0] - cx) * Z, head[1] * Z
    # hook
    if t < T_B:
        d.rectangle([80, 281, 1000, 419], fill=BLACK, outline=GOLD, width=4)
        text_c(d, 306, 'WATCH HOW HE', PS(40), WHITE)
        text_c(d, 362, 'GETS TO 50', PS(40), GOLD)
    # name tag + points counter on the 50th
    if t < T_D or (T_E <= t < T_F):
        if T_E <= t:
            tag(d, hx, hy, 'WEMBY', 47 if t < T_MAKE else 50)
        else:
            tag(d, hx, hy, 'WEMBY')
    # +3 pop
    if T_MAKE <= t < T_F:
        k = seg(t, T_MAKE, T_MAKE + 0.25)
        size = 128 if k >= 1 else int(lerp(48, 152, k) // 8 * 8)
        f = PS(size); s = '+3'
        tw = d.textlength(s, font=f)
        d.text((540 - tw / 2 + 8, 520 + 8), s, font=f, fill=(40, 26, 10))
        d.text((540 - tw / 2, 520), s, font=f, fill=GOLD)
    # cards
    card = T_D <= t < T_E or t >= T_F
    if card:
        t0 = T_D if t < T_E else T_F
        a = int(205 * ease(seg(t, t0, t0 + 0.3)))
        d.rectangle([0, 214, W, 1765], fill=(10, 12, 20, a))
    if T_D + 0.2 <= t < T_E:
        text_c(d, 330, 'AT THE HALF', SK(40), LGREY)
        k = ease(seg(t, T_D + 0.3, T_D + 1.3))
        text_c(d, 410, str(int(round(32 * k))), PS(150), GOLD)
        text_c(d, 590, 'POINTS', PS(32), WHITE)
        if t > T_D + 1.4:
            chip(d, 270, 720, '13', 'REB'); chip(d, 540, 720, '3', 'BLK'); chip(d, 810, 720, '3', 'STL')
        if t > T_D + 1.9:
            text_c(d, 900, 'SPURS LEAD 61-45', SK(38), WHITE)
    if T_F + 0.2 <= t < T_G:
        text_c(d, 300, 'FINAL LINE', SK(40), LGREY)
        text_c(d, 370, '50', PS(150), GOLD)
        text_c(d, 550, 'POINTS', PS(32), WHITE)
        if t > T_F + 0.8:
            chip(d, 270, 660, '18', 'REB'); chip(d, 540, 660, '5', 'BLK'); chip(d, 810, 660, '4', 'STL')
        if t > T_F + 1.4:
            chip(d, 270, 830, '20-29', 'FG'); chip(d, 540, 830, '5-11', '3PT'); chip(d, 810, 830, '+35', '+/-')
        if t > T_F + 2.0:
            text_c(d, 1000, 'SPURS 114, PELICANS 91', SK(38), WHITE)
    if T_G + 0.2 <= t < T_H:
        text_c(d, 300, 'FIRST PLAYER SINCE', SK(40), LGREY)
        text_c(d, 360, '1973-74', PS(72), GOLD)
        text_c(d, 460, 'TO POST, IN ONE GAME:', SK(32), LGREY)
        if t > T_G + 0.6:
            chip(d, 150, 540, '50', 'PTS'); chip(d, 410, 540, '15+', 'REB')
            chip(d, 670, 540, '4+', 'STL'); chip(d, 930, 540, '5+', 'BLK')
        if t > T_G + 1.5:
            d.line([(140, 700), (940, 700)], fill=(60, 64, 80), width=3)
            text_c(d, 740, 'ALSO A FIRST SINCE THE', SK(32), LGREY)
            text_c(d, 790, '3-POINTER (1979-80):', SK(32), LGREY)
            text_c(d, 850, '50 PTS + 5 BLK + 5 THREES', SK(40), WHITE)
        if t > T_G + 2.3:
            text_c(d, 960, '2ND 50 THIS MONTH (52 VS DAL, NOV 4)', SK(30), LGREY)
    if T_H + 0.2 <= t < T_I:
        text_c(d, 290, 'NBA.COM MVP LADDER', SK(40), LGREY)
        text_c(d, 345, 'NOV 20 - BEFORE THE 50', SK(30), GREY)
        rows = [('1', 'DONCIC', 'LAL', '38.1'), ('2', 'WEMBANYAMA', 'SAS', '28.6'),
                ('3', 'ANTETOKOUNMPO', 'MIA', '28.2')]
        if t < T_H2:
            for k, (rk, nm, tm, ppg) in enumerate(rows):
                if t < T_H + 0.4 + k * 0.3: continue
                y = 440 + k * 120
                hi = nm == 'WEMBANYAMA'
                d.rectangle([110, y - 16, 970, y + 84], fill=(30, 30, 40, 230) if not hi else (60, 48, 12, 235),
                            outline=GOLD if hi else (60, 64, 80), width=3)
                d.text((140, y + 10), rk, font=PS(44), fill=GOLD if hi else WHITE)
                d.text((230, y + 4), nm, font=SKB(40), fill=WHITE)
                d.text((230, y + 50), tm, font=SK(26), fill=LGREY)
                tw = d.textlength(ppg, font=PS(36))
                d.text((900 - tw, y + 8), ppg, font=PS(36), fill=GOLD if hi else WHITE)
                d.text((900 - d.textlength('PPG', font=SK(24)), y + 52), 'PPG', font=SK(24), fill=LGREY)
            if t > T_H + 1.6:
                text_c(d, 810, 'SPURS: 14 WINS IN 15 GAMES', SK(34), WHITE)
        else:
            text_c(d, 440, 'PER 36 MINUTES', PS(36), WHITE)
            chip(d, 270, 520, '34.1', 'PTS', GOLD); chip(d, 540, 520, '14.2', 'REB', GOLD)
            chip(d, 810, 520, '4.6', 'BLK', GOLD)
            if t > T_H2 + 0.7:
                text_c(d, 700, 'BUT HE PLAYS', SK(36), LGREY)
                text_c(d, 750, '~30 MIN A NIGHT', PS(40), WHITE)
            if t > T_H2 + 1.3:
                text_c(d, 860, 'DONCIC: 38.1 PPG, NO. 1', SK(32), LGREY)
    if t >= T_I:
        text_c(d, 330, 'THE CATCH', SK(40), LGREY)
        text_c(d, 400, 'OUT MONDAY', PS(56), WHITE)
        text_c(d, 480, '(BACK)', PS(36), GREY)
        if t > T_I + 1.0:
            text_c(d, 620, 'LUKA', PS(64), WHITE)
            text_c(d, 710, 'OR', SK(40), LGREY)
            text_c(d, 770, 'WEMBY?', PS(64), GOLD)
            bob = int(10 * abs(math.sin((t - T_I) * 3.2)))
            ax, ay = 540, 900 + bob
            d.rectangle([ax - 8, ay, ax + 8, ay + 36], fill=GOLD)
            d.polygon([(ax - 26, ay + 36), (ax + 26, ay + 36), (ax, ay + 64)], fill=GOLD)
    draw_header(d, t)
    draw_footer(d, t)
    return img

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'stills':
        out = sys.argv[2]; os.makedirs(out, exist_ok=True)
        for ts in sys.argv[3:]:
            frame(int(round(float(ts) * FPS))).save(os.path.join(out, f't{float(ts):05.2f}.png'))
    else:
        o = sys.stdout.buffer
        for n in range(NF):
            o.write(frame(n).tobytes())
