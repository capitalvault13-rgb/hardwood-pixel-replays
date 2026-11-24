"""Broadcast-camera pixel court for Hardwood Index replays.

Style (see README "Animation style"): side-on, slightly elevated camera. The court runs left to right
and its depth is squashed to 5/8 of its length scale. Light maple floor, team-colour paint with a gloss
band, team-colour baseline aprons with the city running up them, stanchions with glass boards, crowd in
the stands on every side, a drop shadow under every player and the ball, and a camera that pans with
the ball. On top: lime sentence-case captions with a heavy black outline, pink dashed circles and
arrows, and full-frame black word cards.

Everything in the world is drawn on a 3 px grid (one "art pixel" = 3 screen pixels), the same grid
the 3x player sprites use, so the floor, crowd, hoops and players all read as one piece of pixel art.

Units: court feet. x runs 0..94 from the left baseline, z runs 0..50 from the far sideline (top of
the screen) to the near sideline, h is height above the floor.
"""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS = 1080, 1920, 30

# ---------- grid ----------
S = 3                 # screen px per art pixel
PX, PZ, PH = 8, 5, 5.3  # art px per foot: along the court, across it (depth), and up
XOFF = 132            # art px from the world's left edge to the left baseline
COURT_TOP = 146       # art px from the world's top to the far sideline
WL, HL = XOFF * 2 + 94 * PX, 576   # world size in art px (1016 x 576)
VIEW_Y = 192          # screen y where the world view starts (header above it)
VIEW_W = W            # screen px of world visible across
FLOOR = (60, 118, WL - 60, 412)    # art px: the playing floor incl. aprons (x0, y0, x1, y1)
LED = (60, 118, WL - 60, 130)      # far-side LED board

def ax(x): return XOFF + x * PX                       # art px
def ay(z, h=0.0): return COURT_TOP + z * PZ - h * PH  # art px
def wx(x): return ax(x) * S                           # world screen px
def wy(z, h=0.0): return ay(z, h) * S
def snap(v): return int(round(v / S)) * S

# ---------- fonts ----------
def font(name, size): return ImageFont.truetype(os.path.join(ROOT, 'fonts', name), size)
PS = lambda s: font('PressStart2P-Regular.ttf', s)
SK = lambda s: font('Silkscreen-Regular.ttf', s)
INTER_XB = lambda s: font('Inter-ExtraBold.otf', s)
INTER_BK = lambda s: font('Inter-Black.otf', s)

# ---------- palette ----------
LINE_DARK = (34, 32, 38)
OUTLINE = (24, 22, 30)
LIME = (158, 222, 0)        # caption fill
PINK = (240, 40, 110)       # annotation colour
NAVY = (12, 15, 26)
WHITE = (238, 236, 228)
GREY = (120, 124, 140)
SKINS = [(255, 214, 176), (241, 194, 150), (224, 172, 125), (198, 140, 96), (160, 104, 70),
         (124, 80, 54), (96, 62, 42), (232, 186, 146)]
HAIRS = [(30, 24, 22), (52, 36, 26), (20, 18, 18), (96, 64, 36), (150, 110, 60), (200, 170, 110),
         (60, 60, 64), (180, 180, 186)]


def lerp(a, b, t): return a + (b - a) * t
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def seg(t, t0, t1): return clamp((t - t0) / (t1 - t0))
def mix(c1, c2, k): return tuple(int(round(lerp(a, b, k))) for a, b in zip(c1, c2))


def up(im):
    """art px -> screen px (nearest)."""
    return im.resize((im.width * S, im.height * S), Image.NEAREST)


# ---------- pixel line helpers (art px) ----------
def plot_curve(px, pts, col, dash=None):
    """Plot a 1 art-px polyline through many sample points; dash=(on, off) in samples."""
    n = 0
    last = None
    for (x, y) in pts:
        p = (int(round(x)), int(round(y)))
        if p == last: continue
        last = p
        n += 1
        if dash and (n % (dash[0] + dash[1])) >= dash[0]: continue
        if 0 <= p[0] < px.width and 0 <= p[1] < px.height:
            px.putpixel(p, col)

def ellipse_pts(cx, cy, rx, ry, a0, a1, step=None):
    step = step or 0.4 / max(rx, ry)
    a = a0; out = []
    while a <= a1 + 1e-9:
        out.append((cx + rx * math.cos(a), cy + ry * math.sin(a))); a += step
    return out


# ---------- team look ----------
def home_look(abbr, city, paint, apron, paint_line=(236, 236, 236), accent=None, logo_ring=None,
              seats=None, shirts=None, wood=(237, 221, 189), floor='planks', line=LINE_DARK, border=None,
              wordmark=None, wordmark_color=(255, 255, 255), emblem=None, emblem_text=(255, 255, 255),
              floor_text_color=None):
    """Colours for the home floor.

    paint / apron / border may be None for natural wood (no painted lane, wood baseline aprons, wood
    sidelines). floor is 'planks', 'parquet' or 'herringbone'. emblem is the centre-circle fill.
    """
    team = [c for c in (paint, apron, border, emblem) if c]
    base = emblem or apron or paint or border or LINE_DARK
    return dict(abbr=abbr, city=city, paint=paint, apron=apron, paint_line=paint_line,
                accent=accent or paint or base, logo_ring=logo_ring or paint_line,
                seats=seats or mix(base, (20, 20, 24), 0.35),
                shirts=shirts or [team[0], team[0], team[0], team[-1], team[-1], (236, 236, 236),
                                  (236, 236, 236), (236, 236, 236), (40, 40, 46), (150, 150, 160),
                                  (200, 60, 60), (230, 190, 60)],
                wood=tuple(wood), floor=floor, line=tuple(line), border=border,
                wordmark=wordmark or city.upper(), wordmark_color=tuple(wordmark_color),
                emblem=emblem or base, emblem_text=tuple(emblem_text),
                floor_text_color=floor_text_color or (line if not border else wordmark_color))


def _rgb(v):
    if v is None: return None
    v = v.lstrip('#'); return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


def court_look(abbr):
    """The home floor of a team from data/courts.json (abbr like 'DAL' or 'dal')."""
    import json
    db = json.load(open(os.path.join(ROOT, 'data', 'courts.json')))
    c = db['courts'][abbr.lower()]
    return home_look(c['abbr'], c['city'], paint=_rgb(c['paint']), apron=_rgb(c['apron']),
                     paint_line=_rgb(c['paint_line']), logo_ring=_rgb(c['emblem_ring']),
                     wood=_rgb(c['wood']), floor=c['floor'], line=_rgb(c['line']), border=_rgb(c['border']),
                     wordmark=c['wordmark'], wordmark_color=_rgb(c['wordmark_color']),
                     emblem=_rgb(c['emblem']), emblem_text=_rgb(c['emblem_text']))


# ---------- crowd ----------
FRONT = ["..hhhh....",
         ".hhhhhh...",
         ".hsssshh..",
         ".ssssss...",
         ".sesses...",
         ".ssssss...",
         "..ssss....",
         ".cccccc...",
         "cccccccc..",
         "cccccccc..",
         "cccccccc..",
         "cccccccc.."]
BACK = ["..hhhh....",
        ".hhhhhh...",
        ".hhhhhh...",
        "shhhhhhs..",
        ".hhhhhh...",
        "..hhhh....",
        "..ssss....",
        ".cccccc...",
        "cccccccc..",
        "cccccccc..",
        "cccccccc..",
        "cccccccc.."]

def _fan(rows, skin, hair, shirt, arms, bald=False, light=1.0):
    skin, hair, shirt = (mix((0, 0, 0), c, light) for c in (skin, hair, shirt))
    w, h = 10, len(rows) + 3
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = im.load()
    for y, r in enumerate(rows):
        for x, ch in enumerate(r[:8]):
            c = None
            if ch == 'h': c = skin if bald else hair
            elif ch == 's': c = skin
            elif ch == 'e': c = (30, 24, 26)
            elif ch == 'c': c = shirt
            if c: px[x + 1, y + 3] = c + (255,)
    if arms:
        for y in range(0, 6):
            px[1, y + 2] = skin + (255,); px[8, y + 2] = skin + (255,)
        px[1, 1] = skin + (255,); px[8, 1] = skin + (255,)
    # 1 px dark outline
    a = np.array(im)
    m = a[..., 3] > 0
    o = np.zeros_like(m)
    o[1:] |= m[:-1]; o[:-1] |= m[1:]; o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]
    o &= ~m
    a[o] = OUTLINE + (255,)
    return up(Image.fromarray(a))

FAN_LIGHT = {'f': 0.80, 'b': 0.58}


class Crowd:
    """Fans in the stands. Front-facing above/beside the floor, backs of heads below it."""
    def __init__(self, look, seed=11):
        rng = np.random.default_rng(seed)
        self.fans = []
        self.variants = {}
        def variant(kind, i, arms):
            key = (kind, i, arms)
            if key not in self.variants:
                r = np.random.default_rng(1000 + i)
                skin = SKINS[int(r.integers(len(SKINS)))]
                hair = HAIRS[int(r.integers(len(HAIRS)))]
                sh = look['shirts']; shirt = sh[int(r.integers(len(sh)))]
                bald = r.random() < 0.12
                self.variants[key] = _fan(FRONT if kind == 'f' else BACK, skin, hair, shirt, arms, bald,
                                          FAN_LIGHT[kind])
            return self.variants[key]
        self.variant = variant
        fx0, fy0, fx1, fy1 = FLOOR
        # front-facing rows: top stands, and the baseline stands left/right of the floor
        y = fy0 - 15
        rows = []
        while y > -16:
            rows.append(y); y -= 14
        side_y = fy0 - 1
        while side_y < fy1 - 4:
            rows.append(side_y); side_y += 14
        for ry in sorted(rows):
            off = int(rng.integers(0, 6))
            for x in range(-4 + off, WL, 10):
                if ry >= fy0 - 15 and fx0 - 9 < x < fx1: continue   # floor covers it
                if rng.random() < 0.08: continue                     # empty seat
                self.fans.append(dict(k='f', x=x, y=ry, v=int(rng.integers(40)), ph=rng.random() * 6.28,
                                      cheer=rng.random() < 0.75, sp=2.5 + 2 * rng.random()))
        # backs of heads below the near apron
        ry = fy1 + 4
        while ry < HL:
            off = int(rng.integers(0, 6))
            for x in range(-4 + off, WL, 10):
                if rng.random() < 0.06: continue
                self.fans.append(dict(k='b', x=x, y=ry, v=int(rng.integers(40)), ph=rng.random() * 6.28,
                                      cheer=rng.random() < 0.6, sp=2.5 + 2 * rng.random()))
            ry += 14
        self.fans.sort(key=lambda f: f['y'])

    def draw(self, img, cam_x, t, cheer_t=None):
        x0 = cam_x / S - 12; x1 = (cam_x + VIEW_W) / S + 2
        for f in self.fans:
            if not (x0 <= f['x'] <= x1): continue
            dy = 0; arms = False
            if cheer_t is not None and t >= cheer_t and f['cheer'] and t < cheer_t + 4.5:
                k = (t - cheer_t) * f['sp'] + f['ph']
                dy = -int(round(2 * abs(math.sin(k))))
                arms = math.sin(k * 0.5 + f['ph']) > -0.6
            elif math.sin(t * 0.9 + f['ph'] * 3) > 0.985:
                dy = -1
            sp = self.variant(f['k'], f['v'], arms)
            img.paste(sp, (int(f['x'] * S - cam_x), int((f['y'] - 3 + dy) * S) + VIEW_Y), sp)


# ---------- arena ----------
class Arena:
    def __init__(self, look, floor_text='HARDWOOD INDEX'):
        self.look = look
        self.floor_text = floor_text
        self.static = up(self._build_static())          # RGB, world size x3
        self.hoops = up(self._build_hoops())            # RGBA, world size x3
        self.crowd = Crowd(look)
        self.shadow = up(self._ellipse_sprite(16, 5, (0, 0, 0, 78)))
        self.ball_shadow = up(self._ellipse_sprite(6, 2, (0, 0, 0, 90)))
        self.ball = up(self._ball())

    @staticmethod
    def _ellipse_sprite(w, h, col):
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im); d.ellipse([0, 0, w - 1, h - 1], fill=col)
        return im

    @staticmethod
    def _ball():
        pat = [".####.",
               "#oh#o#",
               "#o#oo#",
               "##ooo#",
               "#oo#o#",
               ".####."]
        im = Image.new('RGBA', (6, 6), (0, 0, 0, 0)); px = im.load()
        for y, r in enumerate(pat):
            for x, ch in enumerate(r):
                if ch == '#': px[x, y] = (60, 24, 10, 255)
                elif ch == 'o': px[x, y] = (236, 112, 36, 255)
                elif ch == 'h': px[x, y] = (255, 186, 120, 255)
        return im

    # -- floor --
    def _build_static(self):
        L = self.look
        im = Image.new('RGB', (WL, HL), (26, 28, 36))
        d = ImageDraw.Draw(im)
        d.fontmode = '1'
        # stands: risers behind every row of fans
        for y in range(-16, HL, 14):
            d.rectangle([0, y, WL, y + 6], fill=(26, 28, 36))
            d.rectangle([0, y + 7, WL, y + 13], fill=mix((0, 0, 0), L['seats'], 0.8))
            d.line([0, y + 13, WL, y + 13], fill=(18, 18, 24))
        fx0, fy0, fx1, fy1 = FLOOR
        self._wood(im, d, L)
        d.rectangle([fx0, fy1 - 1, fx1 - 1, fy1 + 1], fill=mix(L['wood'], (0, 0, 0), 0.5))  # near floor edge
        # sideline border band (out of bounds along both sidelines)
        if L['border']:
            d.rectangle([fx0, fy0, fx1 - 1, ay(0) - 1], fill=L['border'])
            d.rectangle([fx0, ay(50) + 1, fx1 - 1, fy1 - 2], fill=L['border'])
        # baseline aprons
        if L['apron']:
            for xa, xb in ((fx0, XOFF - 1), (WL - XOFF, fx1 - 1)):
                d.rectangle([xa, fy0, xb, fy1 - 2], fill=L['apron'])
        # wordmark running up/down each apron, beside the baseline (pixel font, then rotated)
        f = PS(16)
        tw = int(d.textlength(L['wordmark'], font=f))
        tim = Image.new('RGBA', (tw + 4, 20), (0, 0, 0, 0))
        td = ImageDraw.Draw(tim); td.fontmode = '1'
        td.text((2, 2), L['wordmark'], font=f, fill=L['wordmark_color'] + (255,))
        left = tim.rotate(90, expand=True); right = tim.rotate(-90, expand=True)
        cy = ay(25)
        im.paste(left, (int(ax(-1.4) - left.width / 2), int(cy - left.height / 2)), left)
        im.paste(right, (int(ax(95.4) - right.width / 2), int(cy - right.height / 2)), right)
        # paints with a gloss band
        gl = mix(L['paint'], (255, 255, 255), 0.16) if L['paint'] else None
        for side in (0, 1) if L['paint'] else ():
            x0 = ax(0) if side == 0 else ax(94 - 19)
            pw, ph = 19 * PX + 1, 16 * PZ + 1
            tile = Image.new('RGB', (pw, ph), L['paint'])
            td = ImageDraw.Draw(tile)
            for k in range(0, 40):   # a diagonal band of light across the paint
                gx = 60 + k
                td.line([gx, 0, gx - ph * 0.6, ph], fill=gl)
            if side == 1: tile = tile.transpose(Image.FLIP_LEFT_RIGHT)
            im.paste(tile, (int(x0), int(ay(17))))
        px = im
        dk, pl = L['line'], L['paint_line']
        # court outline + half-court line + centre circle
        d = ImageDraw.Draw(im); d.fontmode = '1'
        self._centre_logo(im)
        d.rectangle([ax(0), ay(0), ax(94), ay(50)], outline=dk)
        d.line([ax(47), ay(0), ax(47), ay(50)], fill=dk)
        plot_curve(px, ellipse_pts(ax(47), ay(25), 6 * PX, 6 * PZ, 0, 2 * math.pi), dk)
        for side in (0, 1):
            m = (lambda x: x) if side == 0 else (lambda x: 94 - x)
            sgn = 1 if side == 0 else -1
            rim = m(5.25)
            # lane outline + hash marks
            d.rectangle([min(ax(m(0)), ax(m(19))), ay(17), max(ax(m(0)), ax(m(19))), ay(33)], outline=pl)
            for hx in (7, 8, 11, 14):
                for z, dz in ((17, -1), (33, 1)):
                    d.line([ax(m(hx)), ay(z), ax(m(hx)), ay(z) + dz * 2], fill=pl)
            # free-throw circle: solid half outside the paint, dashed half inside
            cx, cy = ax(m(19)), ay(25)
            a0 = -math.pi / 2 if side == 0 else math.pi / 2
            plot_curve(px, ellipse_pts(cx, cy, 6 * PX, 6 * PZ, a0, a0 + math.pi), dk)
            plot_curve(px, ellipse_pts(cx, cy, 6 * PX, 6 * PZ, a0 + math.pi, a0 + 2 * math.pi), pl, dash=(3, 3))
            # restricted area
            plot_curve(px, ellipse_pts(ax(rim), ay(25), 4 * PX, 4 * PZ, a0, a0 + math.pi), pl)
            # three-point line: corners + arc
            R = 23.75
            ang = math.asin(22 / R)
            xc = rim + sgn * R * math.cos(ang)
            for z in (3, 47):
                d.line([ax(m(0)), ay(z), ax(xc), ay(z)], fill=dk)
            if side == 0:
                plot_curve(px, ellipse_pts(ax(rim), ay(25), R * PX, R * PZ, -ang, ang), dk)
            else:
                plot_curve(px, ellipse_pts(ax(rim), ay(25), R * PX, R * PZ, math.pi - ang, math.pi + ang), dk)
            # stanchion base pad on the apron
            bx0, bx1 = sorted((ax(m(-8)), ax(m(-3))))
            top0, top1 = ay(21, 3), ay(29, 3)
            pad = L['apron'] or L['emblem']
            d.rectangle([bx0, top0, bx1, top1], fill=mix(pad, (255, 255, 255), 0.25), outline=OUTLINE)
            d.rectangle([bx0, top1, bx1, ay(29)], fill=mix(pad, (0, 0, 0), 0.25), outline=OUTLINE)
            d.line([bx0 + 1, top1 + 3, bx1 - 1, top1 + 3], fill=(236, 236, 236))
        # brand text on the floor along the far sideline, like arena signage
        f8 = PS(8)
        for xc in (24, 70):
            tw = d.textlength(self.floor_text, font=f8)
            d.text((ax(xc) - tw / 2, ay(0) - 13), self.floor_text, font=f8, fill=L['floor_text_color'])
        return im

    @staticmethod
    def _wood(im, d, L):
        """Floor boards in the team's stain: planks, parquet squares or herringbone."""
        fx0, fy0, fx1, fy1 = FLOOR
        base = L['wood']
        tones = [base, mix(base, (0, 0, 0), 0.015), mix(base, (255, 255, 255), 0.07), mix(base, (0, 0, 0), 0.035)]
        seam = mix(base, (0, 0, 0), 0.07)
        rng = np.random.default_rng(5)
        if L['floor'] == 'planks':      # boards run along the court, 2 art px deep, staggered seams
            for y in range(fy0, fy1, 2):
                x = fx0 - int(rng.integers(0, 50))
                while x < fx1:
                    ln = int(rng.integers(26, 72))
                    c = tones[int(rng.integers(len(tones)))]
                    if x + ln > fx0:
                        d.rectangle([max(x, fx0), y, min(x + ln, fx1) - 1, y + 1], fill=c)
                    if x > fx0: im.putpixel((x, y), seam)
                    x += ln
            return
        a = np.zeros((fy1 - fy0, fx1 - fx0, 3), np.uint8)
        yy, xx = np.mgrid[0:fy1 - fy0, 0:fx1 - fx0]
        T = np.array(tones + [seam], np.uint8)
        if L['floor'] == 'parquet':     # 10 x 6 art-px squares, boards turning 90 degrees square to square
            bx, by = xx // 10, yy // 6
            across = (bx + by) % 2 == 0
            stripe = np.where(across, (yy % 6) // 2, (xx % 10) // 3)
            idx = (stripe + bx * 3 + by * 5) % 4
            idx = np.where((xx % 10 == 0) | (yy % 6 == 0), 4, idx)
        else:                           # herringbone: short boards zig-zagging along the court
            col = xx // 6
            k = np.where(col % 2 == 0, yy + (xx % 6), yy - (xx % 6) + 6)
            idx = (k // 3 + col * 2) % 4
            idx = np.where(k % 3 == 0, 4, idx)
        a[:] = T[idx]
        im.paste(Image.fromarray(a), (fx0, fy0))

    def _centre_logo(self, im):
        """Original Hardwood Index emblem in the home colours (never a team's real logo)."""
        L = self.look
        n = 132
        lg = Image.new('RGBA', (n, n), (0, 0, 0, 0))
        d = ImageDraw.Draw(lg); d.fontmode = '1'
        d.ellipse([2, 2, n - 3, n - 3], fill=OUTLINE)
        d.ellipse([5, 5, n - 6, n - 6], fill=L['logo_ring'])
        d.ellipse([12, 12, n - 13, n - 13], fill=L['emblem'])
        d.ellipse([18, 18, n - 19, n - 19], outline=L['logo_ring'], width=3)
        f = PS(24)
        tw = d.textlength(L['abbr'], font=f)
        d.text(((n - tw) / 2 + 2, n / 2 - 10), L['abbr'], font=f, fill=OUTLINE)
        d.text(((n - tw) / 2, n / 2 - 12), L['abbr'], font=f, fill=L['emblem_text'])
        lg = lg.resize((n, int(n * PZ / PX)), Image.NEAREST)   # lay it flat on the floor
        im.paste(lg, (int(ax(47) - lg.width / 2), int(ay(25) - lg.height / 2)), lg)

    # -- hoops (drawn in depth order with the players) --
    def _build_hoops(self):
        im = Image.new('RGBA', (WL, HL), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        steel = (150, 156, 168); steel_d = (96, 100, 112)
        bx = ax(-5.5)
        # post + boom
        d.rectangle([bx - 2, ay(25, 13.2), bx + 2, ay(25, 3)], fill=steel, outline=OUTLINE)
        d.line([bx + 1, ay(25, 13.2), bx + 1, ay(25, 3)], fill=steel_d)
        d.polygon([(bx - 2, ay(25, 13.6)), (ax(3.6), ay(25, 12.4)), (ax(3.6), ay(25, 11.2)), (bx - 2, ay(25, 12.0))],
                  fill=steel, outline=OUTLINE)
        # glass board, leaned so it reads as a plane seen at an angle
        x = ax(4)
        top_l, top_r = ay(22, 13.0), ay(28, 13.0)
        bot_l, bot_r = ay(22, 9.5), ay(28, 9.5)
        poly = [(x - 5, top_l), (x + 4, top_r - 10), (x + 4, bot_r), (x - 5, bot_l + 10)]
        d.polygon(poly, fill=(196, 228, 244, 140), outline=OUTLINE)
        inner = [(x - 4, top_l + 2), (x + 3, top_r - 8), (x + 3, bot_r - 2), (x - 4, bot_l + 8)]
        d.polygon(inner, outline=(250, 250, 250, 255))
        sq = [(x - 2, ry0 := ay(23.5, 11.5)), (x + 1, ay(26.5, 11.5) - 4), (x + 1, ay(26.5, 10.1) - 4), (x - 2, ay(23.5, 10.1))]
        d.polygon(sq, outline=(250, 250, 250, 255))
        d.line([(x - 3, top_l + 6), (x - 1, top_l + 14)], fill=(255, 255, 255, 220))
        # rim + net
        rx, ry = ax(5.25), ay(25, 10)
        d.line([(x + 2, ry), (rx - 5, ry)], fill=(200, 80, 24, 255))
        d.ellipse([rx - 6, ry - 2, rx + 6, ry + 2], outline=(232, 104, 32, 255))
        d.arc([rx - 6, ry - 2, rx + 6, ry + 3], 0, 180, fill=(140, 52, 14, 255))
        npx = im.load()
        for k in range(1, 11):
            half = 5 - k * 0.25
            for xx in range(int(rx - half), int(rx + half) + 1):
                if (xx + k) % 2 == 0:
                    npx[xx, int(ry + 2 + k)] = (250, 250, 250, 255)
        right = im.transpose(Image.FLIP_LEFT_RIGHT)
        im.alpha_composite(right)
        return im

    # -- per frame --
    def begin(self, cam_x, t, cheer_t=None, led=None):
        """Returns the screen image (W x H) with floor, LED board and crowd drawn for this camera."""
        img = Image.new('RGB', (W, H), NAVY)
        cam_x = snap(cam_x)
        img.paste(self.static.crop((cam_x, 0, cam_x + VIEW_W, H - VIEW_Y)), (0, VIEW_Y))
        self.cam_x = cam_x
        self.crowd.draw(img, cam_x, t, cheer_t)
        self._led(img, cam_x, t, led)
        return img

    def _led(self, img, cam_x, t, led):
        x0, y0, x1, y1 = LED
        L = self.look
        bar = Image.new('RGB', (x1 - x0, y1 - y0), (14, 16, 22))
        d = ImageDraw.Draw(bar); d.fontmode = '1'
        if led and led.get('flash'):
            bar.paste(led['flash'], (0, 0, bar.width, bar.height))
        msg = (led or {}).get('text', f"{self.floor_text}  *  PIXEL REPLAY  *  ")
        col = (led or {}).get('color', (236, 236, 236))
        f = PS(8)
        tw = int(d.textlength(msg, font=f))
        off = int(t * 24) % max(tw, 1)
        xx = -off
        while xx < bar.width:
            d.text((xx, 2), msg, font=f, fill=col); xx += tw
        d.line([0, 0, bar.width, 0], fill=L['accent'])
        d.line([0, bar.height - 1, bar.width, bar.height - 1], fill=L['accent'])
        big = up(bar)
        img.paste(big, (x0 * S - cam_x, y0 * S + VIEW_Y))

    def to_screen(self, x, z, h=0.0):
        """court feet -> screen px."""
        return wx(x) - self.cam_x, wy(z, h) + VIEW_Y

    def draw_actors(self, img, actors, ball=None, ball_behind_net=False):
        """actors: list of dicts {sprite, x, z, h=0, flip=False}. ball: (x, z, h) or None.
        Draws shadows, then players / hoops / ball in depth order."""
        items = []
        for a in actors:
            items.append((a['z'], 'p', a))
        items.append((25.0, 'hoop', None))
        items.sort(key=lambda q: (q[0], q[1] != 'hoop'))
        # shadows first, all on the floor
        for a in actors:
            sx, sy = self.to_screen(a['x'], a['z'])
            sh = self.shadow
            img.paste(sh, (snap(sx - sh.width / 2), snap(sy - sh.height / 2)), sh)
        if ball:
            bx, bz, bh = ball
            sx, sy = self.to_screen(bx, bz)
            bs = self.ball_shadow
            img.paste(bs, (snap(sx - bs.width / 2), snap(sy - bs.height / 2)), bs)
        for _, kind, a in items:
            if kind == 'hoop':
                if ball and ball_behind_net: self._draw_ball(img, ball)
                img.paste(self.hoops.crop((self.cam_x, 0, self.cam_x + VIEW_W, H - VIEW_Y)), (0, VIEW_Y),
                          self.hoops.crop((self.cam_x, 0, self.cam_x + VIEW_W, H - VIEW_Y)))
                continue
            sp = a['sprite']
            if a.get('flip'): sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            sx, sy = self.to_screen(a['x'], a['z'], a.get('h', 0))
            img.paste(sp, (snap(sx - sp.width / 2), snap(sy - sp.height) + S), sp)
        if ball and not ball_behind_net: self._draw_ball(img, ball)

    def _draw_ball(self, img, ball):
        bx, bz, bh = ball
        sx, sy = self.to_screen(bx, bz, bh)
        b = self.ball
        img.paste(b, (snap(sx - b.width / 2), snap(sy - b.height / 2)), b)


# ---------- overlay graphics (screen space) ----------
def caption(img, text, y=1585, size=62, color=LIME, max_w=980):
    """Lime sentence-case subtitle with a heavy black outline and soft shadow, centred on y."""
    f = INTER_XB(size)
    d = ImageDraw.Draw(img)
    words = text.split(); lines = []; cur = ''
    for w_ in words:
        trial = (cur + ' ' + w_).strip()
        if d.textlength(trial, font=f) <= max_w or not cur: cur = trial
        else: lines.append(cur); cur = w_
    if cur: lines.append(cur)
    lh = int(size * 1.12)
    top = int(y - lh * len(lines) / 2)
    # soft dark shadow under the outline
    mask = Image.new('L', (W, lh * len(lines) + 60), 0)
    md = ImageDraw.Draw(mask)
    for i, ln in enumerate(lines):
        tw = md.textlength(ln, font=f)
        md.text((W / 2 - tw / 2, 30 + i * lh), ln, font=f, fill=255, stroke_width=12, stroke_fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(8))
    shadow = Image.new('RGB', mask.size, (0, 0, 0))
    img.paste(shadow, (0, top - 30 + 4), mask.point(lambda v: int(v * 0.75)))
    for i, ln in enumerate(lines):
        tw = d.textlength(ln, font=f)
        d.text((W / 2 - tw / 2, top + i * lh), ln, font=f, fill=color, stroke_width=7, stroke_fill=(0, 0, 0))


def dashed_ellipse(img, cx, cy, rx, ry, color=PINK, width=9, dashes=14, spin=0.0, fill_frac=0.6):
    d = ImageDraw.Draw(img)
    for i in range(dashes):
        a0 = (i / dashes) * 2 * math.pi + spin
        a1 = a0 + fill_frac * 2 * math.pi / dashes
        pts = [(cx + rx * math.cos(a), cy + ry * math.sin(a)) for a in np.linspace(a0, a1, 8)]
        d.line(pts, fill=color, width=width, joint='curve')


def dashed_arrow(img, p0, p1, bend=0.0, color=PINK, width=10, dash=26, gap=16, upto=1.0, head=30):
    """Quadratic dashed arrow from p0 to p1; bend lifts the control point (px, negative = up).
    upto (0..1) draws only the first part, for a draw-on animation."""
    d = ImageDraw.Draw(img)
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + bend
    def q(t):
        return ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * mx + t * t * p1[0],
                (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * my + t * t * p1[1])
    pts = [q(t) for t in np.linspace(0, upto, 240)]
    acc = 0; on = True; cur = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        acc += math.dist(a, b)
        cur.append(b)
        lim = dash if on else gap
        if acc >= lim:
            if on and len(cur) > 1: d.line(cur, fill=color, width=width, joint='curve')
            on = not on; acc = 0; cur = [b]
    if on and len(cur) > 1: d.line(cur, fill=color, width=width, joint='curve')
    if upto >= 0.999 and head > 0:
        e = q(1.0); s = q(0.97)
        ang = math.atan2(e[1] - s[1], e[0] - s[0])
        tip = (e[0] + math.cos(ang) * 6, e[1] + math.sin(ang) * 6)
        l = (e[0] - head * math.cos(ang - 0.5), e[1] - head * math.sin(ang - 0.5))
        r = (e[0] - head * math.cos(ang + 0.5), e[1] - head * math.sin(ang + 0.5))
        d.polygon([tip, l, r], fill=color)


def word_card(img, lines, size=120, sub=None, sub_color=WHITE, y=None):
    """Full-frame black cut-away with big white words (the reference's 'TODAY' / 'FINALLY' cards)."""
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, H], fill=(0, 0, 0))
    f = INTER_BK(size)
    lh = int(size * 1.08)
    total = lh * len(lines)
    y0 = (y if y is not None else H / 2) - total / 2
    for i, ln in enumerate(lines):
        txt, col = ln if isinstance(ln, tuple) else (ln, WHITE)
        tw = d.textlength(txt, font=f)
        d.text((W / 2 - tw / 2, y0 + i * lh), txt, font=f, fill=col)
    return y0 + total
