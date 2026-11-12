"""Pixel Replay #002 - Kuminga 74ft, ATL @ DAL, Mar 18 2026. Renders frames to stdout (raw RGB) for ffmpeg."""
import sys, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root
W, H, FPS, DUR = 1080, 1920, 30, 15.0
NF = int(FPS * DUR)

def F(name, size):
    return ImageFont.truetype(os.path.join(HERE, 'fonts', name), size)
PS = lambda s: F('PressStart2P-Regular.ttf', s)
SK = lambda s: F('Silkscreen-Regular.ttf', s)
SKB = lambda s: F('Silkscreen-Bold.ttf', s)

NAVY = (12, 15, 26); WHITE = (238, 236, 228); GOLD = (250, 196, 40); GREY = (120, 124, 140)
LINE = (214, 200, 168); ATL_RED = (200, 16, 46); DAL_BLUE = (0, 83, 188); PAINT = (16, 46, 104)
ORANGE = (232, 104, 32); BLACK = (8, 8, 12)

# ---------- court geometry (world = full-view screen space) ----------
CX0, CX1, CY0, CY1 = 137, 947, 233, 1753
PPF = (CY1 - CY0) / 94.0
MIDX = (CX0 + CX1) / 2
def fy(ft_from_top): return CY0 + ft_from_top * PPF
RIM_TOP = (MIDX, fy(5.25)); RIM_BOT = (MIDX, fy(94 - 5.25))

def build_court():
    im = Image.new('RGB', (W, H), NAVY)
    d = ImageDraw.Draw(im)
    # wood planks
    rng = np.random.default_rng(7)
    shades = [(104, 68, 40), (94, 61, 36), (112, 75, 45), (99, 65, 39)]
    x = 96
    while x < 984:
        w = 48
        y = 192
        while y < 1765:
            seg = int(rng.integers(260, 620))
            c = shades[int(rng.integers(0, 4))]
            d.rectangle([x, y, min(x + w, 984) - 1, min(y + seg, 1765) - 1], fill=c)
            d.rectangle([x, y, min(x + w, 984) - 1, y + 2], fill=(78, 50, 30))
            y += seg
        d.line([x, 192, x, 1764], fill=(80, 52, 31), width=2)
        x += w
    lw = 3
    # paints
    for top in (True, False):
        y0 = CY0 if top else fy(94 - 19)
        y1 = fy(19) if top else CY1
        d.rectangle([MIDX - 8 * PPF, y0, MIDX + 8 * PPF, y1], fill=PAINT, outline=LINE, width=lw)
    d.rectangle([CX0, CY0, CX1, CY1], outline=LINE, width=lw)
    d.line([CX0, fy(47), CX1, fy(47)], fill=LINE, width=lw)
    r = 6 * PPF
    d.ellipse([MIDX - r, fy(47) - r, MIDX + r, fy(47) + r], outline=LINE, width=lw)
    for top in (True, False):
        ftl = fy(19) if top else fy(75)
        d.ellipse([MIDX - r, ftl - r, MIDX + r, ftl + r], outline=LINE, width=lw)
        rim = RIM_TOP if top else RIM_BOT
        # three point line
        R = 23.75 * PPF
        cx_l, cx_r = CX0 + 3 * PPF, CX1 - 3 * PPF
        dy = math.sqrt(R * R - (MIDX - cx_l) ** 2)
        if top:
            d.line([cx_l, CY0, cx_l, rim[1] + dy], fill=LINE, width=lw)
            d.line([cx_r, CY0, cx_r, rim[1] + dy], fill=LINE, width=lw)
            a0 = math.degrees(math.atan2(dy, cx_r - MIDX)); a1 = 180 - a0
            d.arc([MIDX - R, rim[1] - R, MIDX + R, rim[1] + R], a0, a1, fill=LINE, width=lw)
        else:
            d.line([cx_l, CY1, cx_l, rim[1] - dy], fill=LINE, width=lw)
            d.line([cx_r, CY1, cx_r, rim[1] - dy], fill=LINE, width=lw)
            a0 = 180 + math.degrees(math.atan2(dy, MIDX - cx_l)); a1 = 360 - math.degrees(math.atan2(dy, cx_r - MIDX))
            d.arc([MIDX - R, rim[1] - R, MIDX + R, rim[1] + R], a0, a1, fill=LINE, width=lw)
        # backboard + rim
        by = fy(4) if top else fy(90)
        d.rectangle([MIDX - 3 * PPF, by - 2, MIDX + 3 * PPF, by + 2], fill=WHITE)
        rr = 0.75 * PPF
        d.ellipse([rim[0] - rr, rim[1] - rr, rim[0] + rr, rim[1] + rr], outline=ORANGE, width=3)
    return im

# ---------- sprites ----------
SP = os.path.join(HERE, 'sprites')
SCALE = 3
def load(name, recolor=False):
    a = np.array(Image.open(os.path.join(SP, name + '.png')).convert('RGBA'))
    if recolor:  # Hawks home white -> generic Mavericks home (white/royal blue/silver)
        r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
        red = (r > 140) & (g < 90) & (b < 90) & (r - g > 80)
        yel = (r > 170) & (g > 130) & (b < 110)
        a[red, :3] = DAL_BLUE
        a[yel, :3] = (180, 188, 198)
    im = Image.fromarray(a)
    return im.resize((im.width * SCALE, im.height * SCALE), Image.NEAREST)

def ball_sprite(s):
    pat = ["..####..",
           ".#oooo#.",
           "#oo#ooo#",
           "#o#oooo#",
           "#oooo#o#",
           "#ooo#oo#",
           ".#oooo#.",
           "..####.."]
    im = Image.new('RGBA', (8, 8), (0, 0, 0, 0))
    px = im.load()
    for y, row in enumerate(pat):
        for x, ch in enumerate(row):
            if ch == '#': px[x, y] = (60, 24, 10, 255)
            elif ch == 'o': px[x, y] = (236, 112, 36, 255)
    px[2, 1] = (255, 180, 110, 255); px[3, 1] = (255, 180, 110, 255)
    return im.resize((8 * s, 8 * s), Image.NEAREST)
BALLS = {s: ball_sprite(s) for s in range(2, 9)}

# ---------- easing / timeline ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def lerp(a, b, t): return a + (b - a) * t
def seg(t, t0, t1): return clamp((t - t0) / (t1 - t0))

T_REB = 0.75        # ball reaches Kuminga's hands
T_LOAD = 2.9        # gather / rise
T_REL = 3.5         # release
T_ZOOM0, T_ZOOM1 = 3.9, 5.2
T_BUZZ = 4.4
T_LAND = 6.5        # through the rim
T_CARD = 9.2
T_END = 12.2

KPOS = (566, RIM_TOP[1] + 74 * PPF)

TEAM_ATL = [('kuminga_away', KPOS), ('landale_away', (700, 1150)), ('mccollum_away', (300, 1040)),
            ('naw_away', (392, 1330)), ('okongwu_away', (742, 1440))]
TEAM_DAL = [('gueye_home', (440, 1600)), ('dennis_home', (690, 1580)), ('veesaar_home', (262, 1470)),
            ('nembhard_home', (835, 1290)), ('newell_home', (520, 1210))]

class Scene:
    def __init__(self):
        self.court = build_court()
        self.atl = [(load(n), p) for n, p in TEAM_ATL]
        self.dal = [(load(n, True), p) for n, p in TEAM_DAL]
        self.tagfont = PS(16)

    def world(self, t):
        im = self.court.copy()
        d = ImageDraw.Draw(im)
        # ruler (grows with ball)
        prog = ease(seg(t, T_REL, T_LAND))
        if t > T_ZOOM0 + 0.3:
            rx = 913; ya = KPOS[1]; yb = lerp(ya, RIM_TOP[1], prog)
            d.line([rx, yb, rx, ya], fill=GOLD, width=4)
            d.line([rx - 9, ya, rx + 9, ya], fill=GOLD, width=4)
            d.line([rx - 9, yb, rx + 9, yb], fill=GOLD, width=4)
            ft = int(round(74 * prog))
            lab = f"{ft}FT"
            f = PS(24)
            tw = d.textlength(lab, font=f)
            my = (ya + yb) / 2
            d.rectangle([rx - tw - 26, my - 22, rx + 2, my + 22], fill=BLACK)
            d.text((rx - tw - 12, my - 12), lab, font=f, fill=GOLD)
        # players (y-sorted), with small idle bob
        people = []
        for i, (sp, p) in enumerate(self.atl + self.dal):
            x, y = p
            # light drift so the scene breathes
            x += 6 * math.sin(t * 1.3 + i * 1.7)
            y += 4 * math.cos(t * 1.1 + i * 0.9)
            hop = 0
            if i == 0:
                x, y = KPOS
                # rise into the shot, land, then celebration hops after the make
                hop = 26 * math.sin(math.pi * seg(t, T_LOAD + 0.2, T_REL + 0.45)) if T_LOAD + 0.2 < t < T_REL + 0.45 else 0
                if t > T_LAND + 0.1:
                    k = (t - T_LAND - 0.1) * 2.6
                    if k < 3: hop = 30 * abs(math.sin(math.pi * k))
            people.append((y, sp, x, y - hop, i == 0))
        people.sort(key=lambda q: q[0])
        kpos_screen = None
        for _, sp, x, y, is_k in people:
            im.paste(sp, (int(x - sp.width / 2), int(y - sp.height)), sp)
            if is_k: kpos_screen = (x, y - sp.height)
        # name tag over Kuminga (fades into the full view)
        if t < T_CARD:
            kx, ky = kpos_screen
            lab = 'KUMINGA'; f = self.tagfont
            tw = d.textlength(lab, font=f)
            bx0, by0 = kx - tw / 2 - 10, ky - 52
            d.rectangle([bx0, by0, bx0 + tw + 20, by0 + 32], fill=BLACK, outline=GOLD, width=3)
            d.text((bx0 + 10, by0 + 8), lab, font=f, fill=GOLD)
            d.polygon([(kx - 6, by0 + 32), (kx + 6, by0 + 32), (kx, by0 + 40)], fill=GOLD)
        # ball
        self.draw_ball(im, d, t, kpos_screen)
        # net flash on the make
        if T_LAND <= t < T_LAND + 0.5:
            a = 1 - seg(t, T_LAND, T_LAND + 0.5)
            rr = (0.75 + 1.2 * (1 - a)) * PPF
            d.ellipse([RIM_TOP[0] - rr, RIM_TOP[1] - rr, RIM_TOP[0] + rr, RIM_TOP[1] + rr], outline=GOLD, width=4)
        return im

    def draw_ball(self, im, d, t, kh):
        kx, ky = kh
        hold = (kx + 20, ky + 40)
        over = (kx, ky - 6)
        if t < T_REB:
            # carom off the near rim down to Kuminga
            s = seg(t, 0, T_REB)
            gx = lerp(RIM_BOT[0] + 10, hold[0], s); gy = lerp(RIM_BOT[1] - 10, hold[1], s)
            h = 70 * math.sin(math.pi * s)
            sc = 3 + int(round(1.5 * math.sin(math.pi * s)))
        elif t < T_REL:
            s = ease(seg(t, T_LOAD, T_REL))
            gx = lerp(hold[0], over[0], s); gy = lerp(hold[1], over[1], s); h = 0; sc = 3
        else:
            s = seg(t, T_REL, T_LAND)
            if s >= 1:
                # drops through and rolls out under the far rim
                k = seg(t, T_LAND, T_LAND + 1.5)
                gx = RIM_TOP[0] + 30 * k; gy = RIM_TOP[1] - 30 * math.sin(math.pi * k * 0.5) + 10
                h = 0; sc = 3
                if t > T_CARD: return
            else:
                gx = lerp(over[0], RIM_TOP[0], s); gy = lerp(over[1], RIM_TOP[1], s)
                h = 260 * math.sin(math.pi * s)
                sc = 3 + int(round(4 * math.sin(math.pi * s)))
                # shadow on the floor
                sw = 22 - 8 * math.sin(math.pi * s)
                d.ellipse([gx - sw, gy - sw * 0.4 + 10, gx + sw, gy + sw * 0.4 + 10], fill=(52, 34, 20))
        b = BALLS[sc]
        im.paste(b, (int(gx - b.width / 2), int(gy - h - b.height / 2)), b)

# ---------- overlay UI ----------
def text_c(d, y, s, font, fill, cx=W // 2):
    tw = d.textlength(s, font=font)
    d.text((cx - tw / 2, y), s, font=font, fill=fill)

def text_rich(d, y, s, font, base=WHITE, hi=GOLD, cx=W // 2):
    parts = []
    for i, p in enumerate(s.split('*')):
        if p: parts.append((p, hi if i % 2 else base))
    tw = sum(d.textlength(p, font=font) for p, _ in parts)
    x = cx - tw / 2
    for p, c in parts:
        d.text((x, y), p, font=font, fill=c); x += d.textlength(p, font=font)

CAPS = [(0.0, 'HAWKS UP 16.', '*BUZZER* ABOUT TO SOUND.'),
        (2.8, 'HE GRABS THE BOARD', 'AND LETS IT *FLY.*'),
        (T_LAND, '74 FEET.', 'AT THE *BUZZER.*'),
        (T_CARD, 'HAWKS WIN 135-120.', '11TH STRAIGHT *WIN.*'),
        (T_END, 'WHICH PLAY', 'IS *NEXT?*')]

def score_state(t):
    if t < T_LAND: return 98, 82, '3RD QTR'
    if t < T_CARD: return 101, 82, 'END 3RD'
    return 135, 120, 'FINAL'

def draw_header(d, t, hb):
    d.rectangle([0, 0, W, hb], fill=NAVY)
    f = PS(40)
    a, b = 'HARDWOOD ', 'INDEX'
    tw = d.textlength(a + b, font=f)
    x = W / 2 - tw / 2
    d.text((x, 26), a, font=f, fill=(222, 52, 52)); d.text((x + d.textlength(a, font=f), 26), b, font=f, fill=(66, 112, 222))
    text_c(d, 92, 'PIXEL REPLAY  #002', SK(32), GREY)
    # scorebug
    sa, sb, per = score_state(t)
    d.rectangle([160, 137, 922, 202], fill=BLACK, outline=(62, 64, 78), width=3)
    d.rectangle([163, 140, 283, 199], fill=ATL_RED)
    d.rectangle([440, 140, 560, 199], fill=DAL_BLUE)
    f2 = PS(32)
    text_c(d, 154, 'ATL', f2, WHITE, cx=223); text_c(d, 154, str(sa), f2, WHITE, cx=360)
    text_c(d, 154, 'DAL', f2, WHITE, cx=500); text_c(d, 154, str(sb), f2, WHITE, cx=635)
    # flash the score change
    if T_LAND <= t < T_LAND + 0.6 and int((t - T_LAND) * 10) % 2 == 0:
        text_c(d, 154, str(sa), f2, GOLD, cx=360)
    text_c(d, 168, per, SK(24), GREY, cx=800)

def draw_footer(d, t):
    d.rectangle([0, 1765, W, H], fill=NAVY)
    cap = [c for c in CAPS if c[0] <= t][-1]
    f = SKB(48)
    text_rich(d, 1774, cap[1], f); text_rich(d, 1826, cap[2], f)
    text_c(d, 1888, 'MAR 18 2026 / NBA PLAY-BY-PLAY / AP', SK(24), (84, 88, 104))

def frame(scene, n):
    t = n / FPS
    world = scene.world(t)
    # camera
    zc = ease(seg(t, T_ZOOM0, T_ZOOM1))
    z = lerp(2.0, 1.0, zc)
    cx = lerp(KPOS[0] - 10, 540, zc); cy = lerp(1385, 994, zc)
    # take the world rect that maps onto the screen, then nearest-scale it
    x0 = cx - 540 / z; y0 = cy - 994 / z
    crop = world.crop((int(round(x0)), int(round(y0)), int(round(x0 + W / z)), int(round(y0 + H / z))))
    img = crop.resize((W, H), Image.NEAREST)
    d = ImageDraw.Draw(img, 'RGBA')
    # hook box
    if t < 2.8:
        d.rectangle([80, 281, 1000, 419], fill=BLACK, outline=GOLD, width=4)
        text_c(d, 306, 'WATCH WHERE HE', PS(40), WHITE)
        text_c(d, 362, 'LETS IT GO FROM', PS(40), GOLD)
    # +3 pop
    if T_LAND <= t < T_CARD:
        k = seg(t, T_LAND, T_LAND + 0.25)
        size = 128 if k >= 1 else int(lerp(48, 152, k) // 8 * 8)
        if 0.25 < t - T_LAND < 0.4: size = 136
        f = PS(size)
        s = '+3'
        tw = d.textlength(s, font=f)
        x, y = 540 - tw / 2, 700
        d.text((x + 8, y + 8), s, font=f, fill=(40, 26, 10))
        d.text((x, y), s, font=f, fill=GOLD)
    # dim + record card
    if t >= T_CARD:
        a = int(200 * ease(seg(t, T_CARD, T_CARD + 0.35)))
        d.rectangle([0, 0, W, H], fill=(10, 12, 20, a))
    if T_CARD + 0.2 <= t < T_END:
        text_c(d, 430, 'NEW HAWKS RECORD.', SK(40), (190, 192, 204))
        k = ease(seg(t, T_CARD + 0.4, T_CARD + 1.6))
        num = int(round(lerp(63, 74, k)))
        text_c(d, 520, str(num), PS(128), GOLD)
        text_c(d, 680, 'FEET', PS(32), WHITE)
        if t > T_CARD + 1.7:
            f = SK(32)
            text_c(d, 800, 'OLD MARK: 63 FT (J. TERRY, 2000)', f, (170, 172, 186))
            text_c(d, 850, 'LONGEST HAWKS MAKE, PBP ERA', f, (170, 172, 186))
            text_c(d, 900, '6TH-LONGEST IN NBA HISTORY', f, (170, 172, 186))
    if t >= T_END:
        text_c(d, 420, 'NEXT', PS(64), WHITE)
        text_c(d, 510, 'REPLAY', PS(64), GOLD)
        f = SK(40)
        text_c(d, 660, 'YOU PICK THE PLAY.', f, WHITE)
        text_c(d, 720, 'MOST-LIKED COMMENT', f, (190, 192, 204))
        text_c(d, 770, 'GETS RECREATED.', f, (190, 192, 204))
        bob = int(10 * abs(math.sin((t - T_END) * 3.2)))
        ax, ay = 540, 880 + bob
        d.rectangle([ax - 8, ay, ax + 8, ay + 36], fill=GOLD)
        d.polygon([(ax - 26, ay + 36), (ax + 26, ay + 36), (ax, ay + 64)], fill=GOLD)
    hb = int(lerp(224, 192, zc))
    draw_header(d, t, hb)
    draw_footer(d, t)
    return img

if __name__ == '__main__':
    scene = Scene()
    mode = sys.argv[1]
    if mode == 'stills':
        out = sys.argv[2]
        for ts in sys.argv[3:]:
            frame(scene, int(float(ts) * FPS)).save(os.path.join(out, f't{float(ts):05.2f}.png'))
    else:
        o = sys.stdout.buffer
        for n in range(NF):
            o.write(frame(scene, n).tobytes())
