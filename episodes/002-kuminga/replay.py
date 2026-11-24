"""Pixel Replay #002 - Kuminga 74ft, ATL @ DAL, Mar 18 2026. Renders frames to stdout (raw RGB) for ffmpeg.

Broadcast-camera style (lib/broadcast.py): side-on court in Dallas, Kuminga rebounds at the left end
and heaves it the length of the floor; the camera pans with the ball to the right-hand rim.
"""
import sys, math, os
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root
sys.path.insert(0, os.path.join(HERE, 'lib'))
from broadcast import (Arena, court_look, caption, dashed_ellipse, dashed_arrow, word_card,
                       W, H, FPS, S, PH, wx, PS, SK, INTER_XB, INTER_BK,
                       NAVY, WHITE, GREY, LIME, PINK, lerp, clamp, ease, seg, snap)

DUR = 15.0
NF = int(FPS * DUR)
GOLD = (250, 196, 40); BLACK = (8, 8, 12)
ATL_RED = (200, 16, 46); DAL_BLUE = (0, 83, 188); DAL_NAVY = (0, 43, 92); DAL_SILVER = (187, 196, 202)

# ---------- timeline ----------
T_REB = 0.75        # ball reaches Kuminga's hands
T_LOAD = 2.9        # gather / rise
T_REL = 3.5         # release
T_BUZZ = 4.4        # buzzer while the ball is in the air
T_LAND = 6.5        # through the rim
T_BACK0, T_BACK1 = 7.3, 8.5   # camera swings back to Kuminga's celebration
T_CARD = 9.2        # cut to black: record card
T_REC = 9.85
T_END = 12.2        # end card

# ---------- court positions (feet; x from the left baseline, z from the far sideline) ----------
RIM_L = (5.25, 25.0)
RIM_R = (94 - 5.25, 25.0)
KZ = 28.0
KX = RIM_R[0] - math.sqrt(74 ** 2 - (KZ - RIM_R[1]) ** 2)   # 74 ft from the far rim: inside his own paint
RIM_H = 10.0

TEAM_ATL = [('kuminga_away', (KX, KZ)), ('landale_away', (22.0, 14.0)), ('mccollum_away', (29.0, 35.0)),
            ('naw_away', (24.0, 45.0)), ('okongwu_away', (9.0, 39.0))]
TEAM_DAL = [('gueye_home', (7.5, 21.0)), ('dennis_home', (18.5, 33.5)), ('veesaar_home', (12.0, 9.0)),
            ('nembhard_home', (27.5, 23.0)), ('newell_home', (35.0, 40.0))]
# after the make: Hawks run to Kuminga, Mavericks head for the bench (left)
HUDDLE = [(0, 0), (-3.2, -2.5), (3.0, -2.2), (-3.4, 2.6), (3.2, 2.8)]

# ---------- sprites ----------
SP = os.path.join(HERE, 'sprites', 'atl')
def load(name, recolor=False):
    # recoloured stand-ins use the un-numbered cut sprites, so they never carry a Hawk's number
    path = os.path.join(SP, 'plain', name + '.png') if recolor else os.path.join(SP, name + '.png')
    a = np.array(Image.open(path).convert('RGBA'))
    if recolor:  # Hawks home white -> generic Mavericks home (white/royal blue/silver)
        r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
        red = (r > 140) & (g < 90) & (b < 90) & (r - g > 80)
        yel = (r > 170) & (g > 130) & (b < 110)
        a[red, :3] = DAL_BLUE
        a[yel, :3] = DAL_SILVER
    im = Image.fromarray(a)
    k = max(1, S * 23 // im.width)  # drawn teams (make_sprites.py) are saved at 3x already
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def cam_center(t):
    """Camera centre in court feet."""
    c0, c1 = 18.0, 76.0
    if t < T_BACK0:
        return lerp(c0, c1, ease(seg(t, T_REL + 0.15, T_LAND - 0.25)))
    return lerp(c1, 22.0, ease(seg(t, T_BACK0, T_BACK1)))


class Scene:
    def __init__(self):
        self.arena = Arena(court_look('dal'))           # data/courts.json
        self.atl = [(load(n), p) for n, p in TEAM_ATL]
        self.dal = [(load(n, True), p) for n, p in TEAM_DAL]

    # -- players --
    def actors(self, t):
        out = []
        celebrate = seg(t, T_LAND + 0.5, T_LAND + 2.0)
        for team, group in (('atl', self.atl), ('dal', self.dal)):
            for i, (sp, (x, z)) in enumerate(group):
                j = i + (0 if team == 'atl' else 5)
                h = 0.0; flip = False
                is_k = team == 'atl' and i == 0
                if is_k:
                    x, z = KX, KZ
                    if T_LOAD + 0.2 < t < T_REL + 0.45:          # rise into the heave
                        h = 5.0 * math.sin(math.pi * seg(t, T_LOAD + 0.2, T_REL + 0.45))
                    if t > T_LAND + 0.1:                          # celebration hops
                        k = (t - T_LAND - 0.1) * 2.6
                        if k < 6: h = 5.5 * abs(math.sin(math.pi * k))
                else:
                    # the floor breathes before the shot; everyone turns to watch the ball after it
                    x += 0.7 * math.sin(t * 1.3 + j * 1.7)
                    z += 0.6 * math.cos(t * 1.1 + j * 0.9)
                    if t > T_REL:
                        drift = ease(seg(t, T_REL, T_LAND)) * (5 if team == 'atl' else 3)
                        x += drift
                    if team == 'atl' and celebrate > 0:
                        hx, hz = HUDDLE[i]
                        k = ease(celebrate)
                        x = lerp(x, KX + hx, k); z = lerp(z, KZ + hz, k)
                        flip = hx > 0
                        if k > 0.95: h = 3.0 * abs(math.sin((t - T_LAND) * 8 + i))
                    elif team == 'dal' and celebrate > 0:
                        x -= 9 * ease(celebrate)
                        flip = True
                    moving = (t > T_REL and t < T_LAND) or (0 < celebrate < 1)
                    if moving and h == 0:
                        h = (1 / PH) * (int(t * 7 + j) % 2)        # one art pixel walking bob
                out.append(dict(sprite=sp, x=x, z=z, h=h, flip=flip, k=is_k))
        return out

    def ball(self, t, k):
        """(x, z, h) of the ball in court feet, and whether it is dropping through the net."""
        hold = (k['x'] + 0.9, k['z'] + 0.3, 3.4 + k['h'])
        over = (k['x'], k['z'] + 0.1, 7.6 + k['h'])
        if t < T_REB:
            s = seg(t, 0, T_REB)
            return (lerp(RIM_L[0] + 0.6, hold[0], s), lerp(RIM_L[1], hold[1], s),
                    lerp(RIM_H, hold[2], s) + 5.0 * math.sin(math.pi * s)), False
        if t < T_REL:
            s = ease(seg(t, T_LOAD, T_REL))
            return tuple(lerp(a, b, s) for a, b in zip(hold, over)), False
        s = seg(t, T_REL, T_LAND)
        if s < 1:
            x = lerp(KX, RIM_R[0], s); z = lerp(KZ + 0.1, RIM_R[1], s)
            h = lerp(7.6, RIM_H + 0.4, s) + 4 * 14.0 * s * (1 - s)   # peak stays over the floor
            return (x, z, h), False
        # through the net, one bounce under the rim, rolls toward the baseline
        k2 = t - T_LAND
        if k2 < 0.35:
            return (RIM_R[0], RIM_R[1], lerp(RIM_H, 0.4, k2 / 0.35)), True
        k3 = k2 - 0.35
        h = 3.2 * abs(math.sin(math.pi * min(k3 / 0.5, 1))) * (1 if k3 < 0.5 else 0) + \
            1.2 * abs(math.sin(math.pi * clamp((k3 - 0.5) / 0.3))) * (0.5 <= k3 < 0.8)
        return (RIM_R[0] + min(k3, 1.6) * 2.2, RIM_R[1] + min(k3, 1.6) * 0.6, h + 0.4), False


# ---------- header / scorebug ----------
def text_c(d, y, s, font, fill, cx=W // 2, **kw):
    tw = d.textlength(s, font=font)
    d.text((cx - tw / 2, y), s, font=font, fill=fill, **kw)

def score_state(t):
    if t < T_BUZZ: return 98, 82, '3RD QTR'
    if t < T_LAND: return 98, 82, 'END 3RD'
    if t < T_CARD: return 101, 82, 'END 3RD'
    return 135, 120, 'FINAL'

def draw_header(d, t):
    d.rectangle([0, 0, W, 191], fill=NAVY)
    f = PS(36)
    a, b = 'HARDWOOD ', 'INDEX'
    tw = d.textlength(a + b, font=f)
    x = W / 2 - tw / 2
    d.text((x, 20), a, font=f, fill=(222, 52, 52)); d.text((x + d.textlength(a, font=f), 20), b, font=f, fill=(66, 112, 222))
    text_c(d, 70, 'PIXEL REPLAY  #002', SK(28), GREY)
    sa, sb, per = score_state(t)
    d.rectangle([160, 114, 922, 176], fill=BLACK, outline=(62, 64, 78), width=3)
    d.rectangle([163, 117, 283, 173], fill=ATL_RED)
    d.rectangle([440, 117, 560, 173], fill=DAL_BLUE)
    f2 = PS(32)
    text_c(d, 130, 'ATL', f2, WHITE, cx=223); text_c(d, 130, str(sa), f2, WHITE, cx=360)
    text_c(d, 130, 'DAL', f2, WHITE, cx=500); text_c(d, 130, str(sb), f2, WHITE, cx=635)
    if T_LAND <= t < T_LAND + 0.6 and int((t - T_LAND) * 10) % 2 == 0:
        text_c(d, 130, str(sa), f2, GOLD, cx=360)
    pc = (232, 60, 60) if T_BUZZ <= t < T_LAND and int((t - T_BUZZ) * 6) % 2 == 0 else GREY
    text_c(d, 142, per, SK(24), pc, cx=800)

def draw_footer(d):
    d.rectangle([0, 1872, W, H], fill=NAVY)
    text_c(d, 1882, 'MAR 18 2026 / NBA PLAY-BY-PLAY / AP', SK(24), (96, 100, 118))


# ---------- frame ----------
CAPS = [(0.0, 'Hawks up 16. The buzzer is about to sound.'),
        (2.8, 'He grabs the board and lets it fly.'),
        (T_LAND, '74 feet. At the buzzer.'),
        (T_REC, 'Hawks win 135-120. 11th straight win.'),
        (T_END, 'Which play is next?')]

def led_state(t):
    if T_BUZZ <= t < T_BUZZ + 0.9:
        on = int((t - T_BUZZ) * 8) % 2 == 0
        return dict(text='0.0  *  END OF 3RD  *  ', color=(255, 255, 255) if on else (255, 120, 120),
                    flash=(150, 16, 24) if on else (60, 8, 12))
    if T_LAND <= t < T_CARD:
        on = int((t - T_LAND) * 6) % 2 == 0
        return dict(text='FROM 74 FEET  *  +3  *  ', color=GOLD if on else (255, 255, 255))
    return None

def frame(scene, n):
    t = n / FPS
    A = scene.arena
    if t < T_CARD:
        cam = wx(cam_center(t)) - W / 2
        img = A.begin(cam, t, cheer_t=T_LAND, led=led_state(t))
        acts = scene.actors(t)
        k = next(a for a in acts if a['k'])
        ball, behind = scene.ball(t, k)
        A.draw_actors(img, acts, ball=ball, ball_behind_net=behind)
        d = ImageDraw.Draw(img)
        kx, ky = A.to_screen(k['x'], k['z'])
        # hook: dashed ring on the floor round Kuminga, then an arrow off toward the far rim
        if 0.9 <= t < T_REL:
            a = seg(t, 0.9, 1.15)
            dashed_ellipse(img, kx, ky - 50, 78 + 40 * (1 - a), 84 + 40 * (1 - a), spin=t * 0.8)
        if 1.5 <= t < T_REL:
            dashed_arrow(img, (kx + 95, ky - 120), (W - 50, ky - 250), bend=-160,
                         upto=ease(seg(t, 1.5, 2.3)))
        # name over his head until the shot is gone
        if t < T_REL + 0.3:
            f = INTER_XB(36)
            text_c(d, ky - k['sprite'].height - 58 - int(k['h'] * PH * S), 'Kuminga', f, WHITE, cx=kx,
                   stroke_width=6, stroke_fill=(0, 0, 0))
        # distance on the floor while the ball is in the air
        if T_REL + 0.25 <= t < T_LAND + 0.8:
            prog = seg(t, T_REL, T_LAND)
            gx, gz = lerp(KX, RIM_R[0], prog), lerp(KZ, RIM_R[1], prog)
            p0 = A.to_screen(KX, KZ); p1 = A.to_screen(gx, gz)
            dashed_arrow(img, p0, p1, color=(255, 255, 255), width=6, dash=18, gap=12, head=0)
            lab = f"{int(round(74 * prog))} ft"
            text_c(d, p1[1] + 22, lab, INTER_XB(48), LIME, cx=clamp(p1[0], 90, W - 90),
                   stroke_width=6, stroke_fill=(0, 0, 0))
        # +3 over the far stands
        if T_LAND <= t < T_CARD:
            kk = seg(t, T_LAND, T_LAND + 0.25)
            size = 128 if kk >= 1 else int(lerp(48, 152, kk) // 8 * 8)
            if 0.25 < t - T_LAND < 0.4: size = 136
            f = PS(size)
            tw = d.textlength('+3', font=f)
            x, y = 540 - tw / 2, 300
            d.text((x + 8, y + 8), '+3', font=f, fill=(40, 26, 10))
            d.text((x, y), '+3', font=f, fill=GOLD)
        cap = [c for c in CAPS if c[0] <= t][-1]
        caption(img, cap[1])
        draw_header(d, t)
        draw_footer(d)
        return img

    img = Image.new('RGB', (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    if t < T_REC:                                   # cut-away word card
        word_card(img, ['NEW', ('HAWKS', (222, 52, 52)), 'RECORD.'], size=150)
    elif t < T_END:                                 # record card
        text_c(d, 600, 'Longest Hawks make of the play-by-play era', INTER_XB(42), (200, 200, 208))
        kk = ease(seg(t, T_REC + 0.15, T_REC + 1.35))
        num = int(round(lerp(63, 74, kk)))
        text_c(d, 680, f'{num} FT', INTER_BK(240), LIME if kk >= 1 else WHITE)
        if t > T_REC + 1.45:
            f = INTER_XB(46)
            text_c(d, 1000, 'Old mark: 63 ft (Jason Terry, 2000)', f, (170, 172, 186))
            text_c(d, 1070, '6th-longest make in NBA history', f, (170, 172, 186))
        caption(img, [c for c in CAPS if c[0] <= t][-1][1])
    else:                                           # end card
        word_card(img, ['NEXT', ('REPLAY', LIME)], size=170, y=760)
        f = INTER_XB(50)
        text_c(d, 1000, 'You pick the play.', f, WHITE)
        text_c(d, 1070, 'Most-liked comment gets recreated.', f, (190, 192, 204))
        bob = int(10 * abs(math.sin((t - T_END) * 3.2)))
        ax_, ay_ = 540, 1200 + bob
        d.rectangle([ax_ - 9, ay_, ax_ + 9, ay_ + 40], fill=LIME)
        d.polygon([(ax_ - 30, ay_ + 40), (ax_ + 30, ay_ + 40), (ax_, ay_ + 72)], fill=LIME)
        caption(img, CAPS[-1][1])
    draw_footer(d)
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
