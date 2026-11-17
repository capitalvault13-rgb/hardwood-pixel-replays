"""Animation demo: a short Celtics possession using the pose library in animate_sprites.py.

Pritchard dribbles and passes, Tatum's jumper rims out, Queta rebounds and dunks.
1080x1920, 30 fps, like the replays.

  python3 tools/anim_demo.py stills <dir> 1.0 4.9 7.3      # check frames
  python3 tools/anim_demo.py render <out.mp4>              # full video with sound
"""
import json, math, os, subprocess, sys, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import animate_sprites as A

ROOT = A.ROOT
W, H, FPS, Z = 1080, 1920, 30, 6
NW, NH = W // Z, H // Z            # native canvas 180 x 320
DUR = 10.0
NF = int(DUR * FPS)

NAVY = (12, 15, 26); WHITE = (238, 236, 228); GOLD = (250, 196, 40); GREY = (150, 154, 170)
WOOD = (200, 146, 92); WOOD2 = (188, 134, 82); LINE = (240, 232, 214); PAINT = (0, 104, 52)
RIM_C = (232, 92, 30)

def F(name, size): return ImageFont.truetype(os.path.join(ROOT, 'fonts', name), size)
PS = lambda s: F('PressStart2P-Regular.ttf', s)
SK = lambda s: F('Silkscreen-Regular.ttf', s)

# ---------------------------------------------------------------- cast + court
cfg = json.load(open(os.path.join(ROOT, 'sprites', 'bos', 'players.json')))
PL = {p["id"]: p for p in cfg["players"]}
KIT = cfg["kits"]["home"]
RIM = (90, 118)                       # rim line, native px
BASE_Y = 124
POS = {"queta": (90, 173), "tatum": (146, 212), "pritchard": (30, 246)}   # feet (template col 11)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def lerp(a, b, t): return a + (b - a) * t
def seg(t, t0, t1): return clamp((t - t0) / (t1 - t0))

def build_court():
    im = Image.new('RGB', (NW, NH), NAVY)
    d = ImageDraw.Draw(im)
    # crowd dots in the dark
    rng = np.random.default_rng(7)
    for _ in range(260):
        x, y = rng.integers(0, NW), rng.integers(70, BASE_Y - 2)
        c = tuple(int(v) for v in rng.integers(26, 60, 3))
        d.point((x, y), fill=c)
    d.rectangle([0, BASE_Y, NW, NH], fill=WOOD)
    for y in range(BASE_Y, NH, 4):
        d.line([(0, y), (NW, y)], fill=WOOD2)
        off = (y // 4 % 3) * 23
        for x in range(off, NW, 70):
            d.point((x, y + 2), fill=WOOD2)
    # paint, free-throw circle, 3pt arc, baseline
    d.rectangle([60, BASE_Y, 120, 204], fill=PAINT, outline=LINE)
    d.ellipse([60, 192, 120, 216], outline=LINE)
    d.arc([6, BASE_Y - 110, 174, BASE_Y + 110], 0, 180, fill=LINE)
    d.line([(0, BASE_Y), (NW, BASE_Y)], fill=LINE)
    # backboard on its support
    d.line([(76, 60), (80, 84)], fill=(90, 94, 108)); d.line([(104, 60), (100, 84)], fill=(90, 94, 108))
    d.rectangle([68, 84, 112, 116], fill=(236, 240, 244), outline=(50, 54, 66))
    d.rectangle([82, 104, 98, 116], outline=RIM_C)
    return im
COURT = build_court()

def draw_rim(d):
    x, y = RIM
    for k in range(6):                       # net
        xx = x - 8 + k * 3
        d.line([(xx, y + 1), (xx + (1 if k < 3 else -1), y + 7)], fill=(250, 250, 250))
    d.line([(x - 9, y + 4), (x + 8, y + 4)], fill=(220, 220, 220))
    d.line([(x - 9, y), (x + 9, y)], fill=RIM_C)
    d.line([(x - 9, y - 1), (x + 9, y - 1)], fill=(170, 60, 20))

# ---------------------------------------------------------------- timeline
T_DRIB0, T_PASS = 0.3, 3.2
T_REL_P = T_PASS + 9 / 30            # pass2 starts
T_CATCH = T_REL_P + 0.40
T_SHOT = 4.5
T_REL_S = T_SHOT + 12 / 30           # shoot2 starts
T_RIM = T_REL_S + 0.85
T_REB = T_RIM + 0.45
T_QJ = T_REB - 8 / 30                # Queta's jump, catch at its peak
T_DUNK = 6.9
T_SLAM = T_DUNK + 12 / 30            # dunk2
T_DROP = T_DUNK + 15 / 30            # dunk3: ball through, falling
T_CELEB = 7.7
T_END = 8.7

REB_SEQ = [("jump0", 5, 0), ("shoot1", 3, 6), ("shoot1", 6, 12), ("shoot1", 3, 7), ("shoot0", 8, 0)]

def seq_at(seq, dt):
    """(index, pose, air) of a (pose, hold, air) list at dt seconds, or None when done."""
    if dt < 0:
        return None
    f = dt * FPS
    for i, (p, hold, air) in enumerate(seq):
        if f < hold:
            return i, p, air
        f -= hold
    return None

def idle(t, ph):
    return ("idle0" if int((t + ph) * FPS / 12) % 2 == 0 else "idle1"), 0

def pritchard(t):
    x = lerp(30, 46, seg(t, T_DRIB0, T_PASS))
    if t >= T_CELEB and (s := seq_at(A.MOVES["jump"], t - T_CELEB)):
        return x, s[1], s[2], False
    if t < T_DRIB0:
        return x, "drib0", 0, True
    if t < T_PASS:
        k = int((t - T_DRIB0) * FPS) % 12 // 3
        return x, f"drib{k}", 0, True
    if (s := seq_at(A.MOVES["pass"], t - T_PASS)):
        return x, s[1], s[2], s[0] < 2
    return (x,) + idle(t, 0.0) + (False,)

def tatum(t):
    x = POS["tatum"][0]
    if t >= T_CELEB and (s := seq_at(A.MOVES["jump"], t - T_CELEB - 0.1)):
        return x, s[1], s[2], False
    if t < T_CATCH:
        return (x,) + idle(t, 0.2) + (False,)
    if t < T_SHOT:
        return x, "shoot0", 0, True
    if (s := seq_at(A.MOVES["shoot"], t - T_SHOT)):
        return x, s[1], s[2], s[0] < 3
    return (x,) + idle(t, 0.2) + (False,)

def queta(t):
    x = POS["queta"][0]
    if (s := seq_at(REB_SEQ, t - T_QJ)):
        return x, s[1], s[2], s[0] >= 2
    if T_QJ <= t < T_DUNK:
        return x, "shoot0", 0, True
    if (s := seq_at(A.MOVES["dunk"], t - T_DUNK)):
        return x, s[1], s[2], s[0] <= 3
    return (x,) + idle(t, 0.4) + (False,)

ACTORS = [("queta", queta), ("tatum", tatum), ("pritchard", pritchard)]

def origin(fx, fy, air):
    return fx - (A.OX + 11), fy - (A.CH - 2) - air

def ball_world(pose_name, fx, fy, air):
    pose = A.POSES[pose_name]
    bx, by = pose["ball"]
    if not pose.get("ball_abs"):
        bx += pose["dx"]; by += pose["dy"]
    ox, oy = origin(fx, fy, air)
    return ox + A.OX + bx, oy + A.Y0 + by

def free_ball(t):
    """(x, y, shadow_y) of the ball while no one holds it, else None."""
    if T_REL_P <= t < T_CATCH:
        px_ = pritchard(T_REL_P - 1e-3)[0]
        a = ball_world("pass2", px_, POS["pritchard"][1], 0)
        b = ball_world("shoot0", POS["tatum"][0], POS["tatum"][1], 0)
        s = seg(t, T_REL_P, T_CATCH)
        return lerp(a[0], b[0], s), lerp(a[1], b[1], s) - 6 * math.sin(math.pi * s), \
            lerp(POS["pritchard"][1], POS["tatum"][1], s)
    if T_REL_S <= t < T_RIM:
        a = ball_world("shoot2", POS["tatum"][0], POS["tatum"][1], 11)
        b = (RIM[0] + 6, RIM[1] - 5)
        s = seg(t, T_REL_S, T_RIM)
        return lerp(a[0], b[0], s), lerp(a[1], b[1], s) - 62 * math.sin(math.pi * s), \
            lerp(POS["tatum"][1], POS["queta"][1] - 20, s)
    if T_RIM <= t < T_REB:
        a = (RIM[0] + 6, RIM[1] - 5)
        b = ball_world("shoot1", POS["queta"][0], POS["queta"][1], 12)
        s = seg(t, T_RIM, T_REB)
        return lerp(a[0], b[0], s), lerp(a[1], b[1], s) - 24 * math.sin(math.pi * s), POS["queta"][1] - 20
    if t >= T_DROP:
        a = ball_world("dunk2", POS["queta"][0], POS["queta"][1], 17)
        floor = POS["queta"][1] + 6
        dt = t - T_DROP
        g = 900.0
        # drop, then two damped bounces
        h0 = floor - a[1]
        t1 = math.sqrt(2 * h0 / g)
        if dt < t1:
            y = a[1] + 0.5 * g * dt * dt
        else:
            v = g * t1 * 0.55; tt = dt - t1; y = floor
            for _ in range(3):
                tb = 2 * v / g
                if tt < tb:
                    y = floor - (v * tt - 0.5 * g * tt * tt); break
                tt -= tb; v *= 0.5
        return a[0] + 14 * clamp(dt / 1.2), y, floor
    return None

BOUNCES = [T_DRIB0 + (k * 12 + 6) / FPS for k in range(40) if T_DRIB0 + (k * 12 + 6) / FPS < T_PASS]

# ---------------------------------------------------------------- frame
CAPS = [(0.25, T_PASS, "PRITCHARD", "DRIBBLE"),
        (T_PASS, T_SHOT, "PRITCHARD", "PASS"),
        (T_SHOT, T_RIM + 0.05, "TATUM", "JUMPER"),
        (T_RIM + 0.05, T_DUNK, "QUETA", "REBOUND"),
        (T_DUNK, T_END, "QUETA", "DUNK!")]
_head_cache = {}

def frame(n):
    t = n / FPS
    im = COURT.copy().convert('RGBA')
    d = ImageDraw.Draw(im)
    actors = sorted(ACTORS, key=lambda a: POS[a[0]][1])
    states = {}
    for pid, fn in actors:
        x, pose, air, hold = fn(t)
        fy = POS[pid][1]
        sw = 9 - air * 0.25
        d.ellipse([x - sw, fy - 1, x + sw, fy + 2], fill=(150, 102, 60, 255))
        states[pid] = (x, fy, pose, air, hold)
    fb = free_ball(t)
    if fb:
        bx, by, sy = fb
        sw = 4
        d.ellipse([bx - sw, sy - 1, bx + sw, sy + 1], fill=(150, 102, 60, 255))
    for pid, _ in actors:
        x, fy, pose, air, hold = states[pid]
        spr = A.render(PL[pid], KIT, A.POSES[pose], with_ball=hold)
        ox, oy = origin(x, fy, air)
        im.alpha_composite(spr, (int(round(ox)), int(round(oy))))
    if fb:
        bx, by, _ = fb
        im.alpha_composite(A.ball_img(), (int(round(bx - 4)), int(round(by - 4))))
    draw_rim(d)
    # rim shake on the miss and the slam
    big = im.convert('RGB').resize((W, H), Image.NEAREST)
    D = ImageDraw.Draw(big)
    # header
    D.text((W // 2, 120), "PIXEL MOVES", font=PS(56), fill=GOLD, anchor="mm")
    D.text((W // 2, 200), "CELTICS  -  ANIMATION TEST", font=SK(34), fill=GREY, anchor="mm")
    # flashes
    for tf in (T_RIM, T_SLAM):
        if tf <= t < tf + 0.3:
            a = 1 - seg(t, tf, tf + 0.3)
            r = (10 + 30 * (1 - a)) * Z / 2
            cx, cy = RIM[0] * Z, RIM[1] * Z
            D.ellipse([cx - r, cy - r, cx + r, cy + r], outline=GOLD, width=6)
    # captions
    for t0, t1, who, what in CAPS:
        if t0 <= t < t1:
            k = seg(t, t0, t0 + 0.15)
            y = int(1790 + (1 - k) * 40)
            D.rectangle([0, y - 110, W, y + 70], fill=(8, 8, 12))
            D.text((W // 2, y - 60), who, font=SK(40), fill=WHITE, anchor="mm")
            D.text((W // 2, y + 10), what, font=PS(64), fill=GOLD, anchor="mm")
    if t >= T_END:
        k = seg(t, T_END, T_END + 0.25)
        ov = Image.new('RGBA', (W, H), (8, 8, 12, int(215 * k)))
        big = Image.alpha_composite(big.convert('RGBA'), ov).convert('RGB')
        D = ImageDraw.Draw(big)
        if k > 0.6:
            D.text((W // 2, 820), "ONE POSE LIBRARY", font=PS(52), fill=GOLD, anchor="mm")
            D.text((W // 2, 920), "EVERY PLAYER  -  EVERY KIT", font=SK(44), fill=WHITE, anchor="mm")
            D.text((W // 2, 1060), "DRIBBLE  PASS  SHOOT  JUMP  DUNK", font=SK(32), fill=GREY, anchor="mm")
    return big

# ---------------------------------------------------------------- audio
def audio(path):
    SR = 48000; N = int(SR * DUR); out = np.zeros(N); rng = np.random.default_rng(5)
    def sq(f, dur, duty=0.5):
        tt = np.arange(int(SR * dur)) / SR; return np.where((tt * f) % 1 < duty, 1.0, -1.0)
    def env(n, a=0.005, r=0.08):
        e = np.ones(n); na = int(a * SR); nr = min(int(r * SR), n)
        if na: e[:na] = np.linspace(0, 1, na)
        e[-nr:] *= np.linspace(1, 0, nr); return e
    def add(sig, t, g):
        i = int(t * SR); j = min(N, i + len(sig))
        if i < N: out[i:j] += sig[:j - i] * g
    def lp(x, a):
        y = np.zeros_like(x); s = 0
        for i, v in enumerate(x): s += a * (v - s); y[i] = s
        return y
    note = lambda m: 440 * 2 ** ((m - 69) / 12)
    def thud(t, f0=150, f1=55, g=0.5, dur=0.14):
        s = np.sin(2 * np.pi * np.cumsum(np.linspace(f0, f1, int(dur * SR))) / SR)
        add(s * env(len(s), 0.002, dur * 0.8), t, g)
    def noise(t, dur, a, g, hp=False):
        n = rng.standard_normal(int(dur * SR)); n = n - lp(n, a) if hp else lp(n, a)
        add(n * np.sin(np.linspace(0, np.pi, len(n))), t, g)
    # bed: 120 bpm chiptune in A minor
    beat = 0.5; step = beat / 2
    prog = [(45, [57, 60, 64]), (41, [53, 57, 60]), (43, [55, 59, 62]), (40, [52, 56, 59])]
    t = 0.0; k = 0
    while t < DUR - 0.3:
        root, ch = prog[int(t / (beat * 4)) % 4]
        g = 0.13 if t < T_END else 0.08
        if k % 2 == 0:
            s = sq(note(root), step * 0.9); add(s * env(len(s), 0.003, 0.05), t, g)
        s = sq(note(ch[k % 3] + 12), step * 0.6, 0.25); add(s * env(len(s), 0.002, 0.06), t, g * 0.45)
        t += step; k += 1
    for tb in BOUNCES:
        thud(tb, 170, 70, 0.55, 0.1)
    noise(T_REL_P, 0.35, 0.12, 1.2)                     # pass whoosh
    thud(T_CATCH, 120, 60, 0.45)                         # catch
    noise(T_REL_S, 0.6, 0.08, 1.2)                       # shot whoosh
    tt = np.arange(int(0.35 * SR)) / SR                  # rim clank
    s = (np.sin(2 * np.pi * 520 * tt) + 0.6 * np.sin(2 * np.pi * 1310 * tt)) * np.exp(-tt * 14)
    add(s, T_RIM, 0.35)
    thud(T_REB, 120, 60, 0.45)
    tt = np.arange(int(0.6 * SR)) / SR                   # dunk: rim rattle + thump
    s = (np.sin(2 * np.pi * 380 * tt) + 0.7 * np.sin(2 * np.pi * 990 * tt)) * np.exp(-tt * 7)
    add(s, T_SLAM, 0.45); thud(T_SLAM, 110, 40, 0.7, 0.25)
    n = rng.standard_normal(int(2.6 * SR)); cr = lp(n, 0.05)
    e = np.minimum(1, np.arange(len(cr)) / (0.2 * SR)) * np.exp(-np.arange(len(cr)) / SR / 1.3)
    add(cr * e, T_SLAM, 2.2)
    for tc in [c[0] for c in CAPS] + [T_END]:            # caption blips
        s = np.concatenate([sq(note(84), 0.05), sq(note(91), 0.07)]); add(s * env(len(s), 0.002, 0.03), tc, 0.1)
    for i, m in enumerate([72, 76, 79, 84]):
        s = sq(note(m), 0.09); add(s * env(len(s), 0.002, 0.05), T_SLAM + 0.1 + i * 0.07, 0.12)
    out[-int(0.4 * SR):] *= np.linspace(1, 0, int(0.4 * SR))
    out /= np.abs(out).max() * 1.12
    w = wave.open(path, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes()); w.close()

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'stills':
        out = sys.argv[2]; os.makedirs(out, exist_ok=True)
        for ts in sys.argv[3:]:
            frame(int(float(ts) * FPS)).save(os.path.join(out, f't{float(ts):05.2f}.png'))
    else:
        dst = sys.argv[2]
        with tempfile.TemporaryDirectory() as tmp:
            wav, norm = os.path.join(tmp, 'a.wav'), os.path.join(tmp, 'n.wav')
            audio(wav)
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wav, '-af', 'loudnorm=I=-14:TP=-1.5',
                            '-ar', '48000', norm], check=True)
            p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                                  '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', norm,
                                  '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p',
                                  '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', dst],
                                 stdin=subprocess.PIPE)
            for n in range(NF):
                p.stdin.write(frame(n).tobytes())
            p.stdin.close(); p.wait()
        print('done ->', dst)
