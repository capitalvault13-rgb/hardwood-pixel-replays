"""Side-by-side video: animation set 1 (camera-facing) vs set 2 (side-facing, 3/4).

Top panel = set 1 (tools/animate_sprites.py), bottom panel = set 2 (tools/animate_sprites_v2.py).
Shared moves first, then the moves that only set 2 has.

  python3 tools/anim_compare.py stills <dir> 3.0 10.5
  python3 tools/anim_compare.py render renders/anim-compare-v1-v2.mp4
"""
import json, math, os, subprocess, sys, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import animate_sprites as v1
import animate_sprites_v2 as v2

ROOT = v1.ROOT
W, H, FPS, Z = 1080, 1920, 30, 8
NW = W // Z
NAVY = (12, 15, 26); WHITE = (238, 236, 228); GOLD = (250, 196, 40); GREY = (150, 154, 170)
WOOD = (200, 146, 92); WOOD2 = (188, 134, 82); LINE = (240, 232, 214); RIM_C = (232, 92, 30)
GREEN = (60, 200, 110)

def F(name, size): return ImageFont.truetype(os.path.join(ROOT, 'fonts', name), size)
PS = lambda s: F('PressStart2P-Regular.ttf', s)
SK = lambda s: F('Silkscreen-Regular.ttf', s)

cfg = json.load(open(os.path.join(ROOT, 'sprites', 'bos', 'players.json')))
PL = {p["id"]: p for p in cfg["players"]}
KITS = cfg["kits"]

# panels in native px
TOP = (26, 100)      # y0, height
BOT = (139, 100)

SEGS = [  # title, set-1 move, set-2 move, player, kit
    ("DRIBBLE", "dribble", "run", "tatum", "home"),
    ("PASS", "pass", "pass", "pritchard", "away"),
    ("JUMP SHOT", "shoot", "jumpshot", "tatum", "home"),
    ("DUNK", "dunk", "dunk", "queta", "statement"),
    ("REBOUND", "jump", "rebound", "robinson", "home"),
    ("CROSSOVER", None, "crossover", "pritchard", "away"),
    ("STEPBACK", None, "stepback", "white", "home"),
    ("LAYUP", None, "layup", "scheierman", "away"),
    ("BLOCK", None, "block", "robinson", "statement"),
    ("DEFENSE", None, "defense", "mitchell", "home"),
    ("LOB PASS", None, "lob", "conley", "away"),
]
INTRO, OUTRO = 54, 75

def norm(seq):
    return [s if len(s) == 5 else (s[0], s[1], s[2], 0, "") for s in seq]
def seq_len(seq): return sum(s[1] for s in seq)

def seg_frames(m2):
    n = seq_len(v2.MOVES[m2])
    return max(84, 2 * n + 6)

TIMELINE = []
_t = INTRO
for s in SEGS:
    n = seg_frames(s[2]); TIMELINE.append((_t, _t + n, s)); _t += n
NF = _t + OUTRO
DUR = NF / FPS

def state(seq, f):
    """index, pose, air, travel, tags, frames into step, step start frame (loop-relative)."""
    seq = norm(seq)
    f %= seq_len(seq)
    acc_travel, start = 0.0, 0
    for i, (p, hold, air, tr, tags) in enumerate(seq):
        if f < start + hold:
            k = (f - start) / hold
            return i, p, air, acc_travel + tr * k, tags, f - start, start
        start += hold; acc_travel += tr
    raise AssertionError

# ---------------------------------------------------------------- panel drawing
def panel_bg(h, scroll=0.0, dim=False):
    im = Image.new('RGBA', (NW, h), NAVY + (255,))
    d = ImageDraw.Draw(im)
    fy = h - 30
    d.rectangle([0, fy, NW, h], fill=WOOD)
    for y in range(fy, h, 4):
        d.line([(0, y), (NW, y)], fill=WOOD2)
        off = int((y // 4 % 3) * 23 - scroll) % 70
        for x in range(off, NW, 70):
            d.point((x, y + 2), fill=WOOD2)
    for x in range(-int(scroll) % 90, NW, 90):     # floor marks so a run reads as moving
        d.line([(x, fy + 6), (x + 10, fy + 30)], fill=LINE)
    d.line([(0, fy), (NW, fy)], fill=LINE)
    if dim:
        im = Image.alpha_composite(im, Image.new('RGBA', im.size, (8, 8, 12, 150)))
    return im

def rim(d, cx, y, shake=0):
    y += shake
    d.rectangle([cx - 10, y - 18, cx + 12, y - 2], fill=(236, 240, 244), outline=(50, 54, 66))
    d.rectangle([cx - 4, y - 9, cx + 6, y - 2], outline=RIM_C)
    for k in range(5):
        xx = cx - 6 + k * 3
        d.line([(xx, y + 1), (xx + (1 if k < 2 else -1), y + 6 + abs(shake) * 2)], fill=(250, 250, 250))
    d.line([(cx - 7, y), (cx + 8, y)], fill=RIM_C)

def draw_v1(h, move, p, kit, f):
    im = panel_bg(h)
    d = ImageDraw.Draw(im)
    gy = h - 20
    fx = 46
    _, pose, air, _, _, _, _ = state(v1.MOVES[move], f)
    if move == "dunk":   # same rim placement as the set-1 GIF preview
        ox = fx - (v1.OX + 11); ry = gy - (v1.CH - 2) + v1.Y0 + v1.RIM_Y - 17
        rim(d, ox + v1.OX + 11, ry)
    d.ellipse([fx - 9, gy - 1, fx + 9, gy + 2], fill=(150, 102, 60))
    spr = v1.render(p, kit, v1.POSES[pose])
    im.alpha_composite(spr, (fx - (v1.OX + 11), gy - (v1.CH - 2) - air))
    return im

def draw_v2(h, move, p, kit, f, events):
    seq = norm(v2.MOVES[move])
    i, pose_n, air, travel, tags, local, start = state(seq, f)
    fl = f % seq_len(seq)
    scroll = f * 2 / 3 if move == "run" else 0
    im = panel_bg(h, scroll)
    d = ImageDraw.Draw(im)
    gy = h - 20
    base = 44 if move not in ("stepback", "layup", "defense", "dunk") else 32
    fx = base + (0 if move == "run" else travel)
    pose = v2.POSES[pose_n]
    org = lambda a: (int(round(fx - (v2.OX + 11))), int(gy - (v2.CH - 2) - a))
    # rim for moves that finish at it
    rim_xy = None
    if move in v2.RIM:
        rx, ry, pk = v2.RIM[move]
        # travel at the frame the move reaches the rim
        j = next(k for k, s in enumerate(seq) if ("rimshake" in s[4] or "release" in s[4]))
        tr_at = sum(s[3] for s in seq[:j])
        o = (base + tr_at - (v2.OX + 11), gy - (v2.CH - 2) - pk)
        rim_xy = (o[0] + v2.OX + rx, o[1] + v2.Y0 + ry)
        shake = 0
        if "rimshake" in tags:
            shake = 1 if (local // 2) % 2 == 0 else -1
            if local == 0: events.append("clang")
        rim(d, int(rim_xy[0]), int(rim_xy[1]), shake)
    # shadow shrinks as the player rises
    sw = max(4, 9 - air * 0.3)
    d.ellipse([fx - sw, gy - 1, fx + sw, gy + 2], fill=(150, 102, 60))
    # free ball
    rel = next((k for k, s in enumerate(seq) if "release" in s[4]), None)
    with_ball = True
    fb = None
    if rel is not None and i >= rel:
        with_ball = False
        rs = sum(s[1] for s in seq[:rel])
        rp = v2.POSES[seq[rel][0]] if v2.POSES[seq[rel][0]].get("ball") else v2.POSES[seq[rel - 1][0]]
        rtr = sum(s[3] for s in seq[:rel])
        o = (base + rtr - (v2.OX + 11), gy - (v2.CH - 2) - seq[rel][2])
        bx0, by0 = v2.ball_pos(rp)
        bx0 += o[0]; by0 += o[1]
        t = (fl - rs) / FPS
        if fl == rs: events.append("whoosh")
        if move == "layup":
            k = min(1, t / 0.35)
            tx, ty = rim_xy[0] + 1, rim_xy[1] - 4
            if k < 1:
                fb = (bx0 + (tx - bx0) * k, by0 + (ty - by0) * k - 8 * math.sin(math.pi * k))
            else:
                fb = (tx, ty + (t - 0.35) * 120)
                if abs(t - 0.35) < 1 / FPS / 2 + 1e-6: events.append("swish")
        elif move == "jumpshot":
            fb = (bx0 + 70 * t, by0 - 170 * t + 120 * t * t)
        elif move == "lob":
            fb = (bx0 + 110 * t, by0 - 110 * t + 150 * t * t)
        else:  # chest pass
            fb = (bx0 + 200 * t, by0 + 10 * t)
    if move == "rebound":   # ball drops in from the miss
        cj = next(k for k, s in enumerate(seq) if s[0] == "rb1")
        cs = sum(s[1] for s in seq[:cj])
        if fl < cs:
            with_ball = False
            k = fl / cs
            tgt = v2.ball_pos(v2.POSES["rb1"]); o = org(seq[cj][2])
            tx, ty = tgt[0] + o[0], tgt[1] + o[1]
            fb = (tx + 40 * (1 - k), ty - 60 * (1 - k) + 25 * math.sin(math.pi * k))
        elif fl == cs:
            events.append("catch")
    if move == "block":     # shot comes in from the right, gets swatted
        bj = next(k for k, s in enumerate(seq) if "flash" in s[4])
        bs = sum(s[1] for s in seq[:bj])
        hand = (fx + 12, gy - (v2.CH - 2) - seq[bj][2] + v2.Y0 - 14)
        if bs - 12 <= fl < bs:
            k = (fl - (bs - 12)) / 12
            fb = (hand[0] + 50 * (1 - k), hand[1] + 20 * (1 - k) - 10 * math.sin(math.pi * k))
        elif bs <= fl < bs + 20:
            t = (fl - bs) / FPS
            fb = (hand[0] + 120 * t, hand[1] + 40 * t + 300 * t * t)
    # player
    spr = v2.render(p, kit, pose, with_ball=with_ball)
    im.alpha_composite(spr, org(air))
    # effects
    if fb:
        im.alpha_composite(v1.ball_img(), (int(fb[0] - 4), int(fb[1] - 4)))
    if "dust" in tags:
        v2.dust(d, fx, gy, local)
        if local == 0: events.append("thud")
    else:   # dust lingers a few frames past its step
        if i > 0 and "dust" in seq[i - 1][4]:
            v2.dust(d, fx, gy, local + seq[i - 1][1])
    if "flash" in tags:
        if move == "block":
            v2.flash(d, fx + 13, gy - (v2.CH - 2) - air + v2.Y0 - 14, local)
            if local == 0: events.append("swat")
        elif rim_xy:
            v2.flash(d, rim_xy[0], rim_xy[1], local)
    if pose.get("squash") and local == 0:
        events.append("bounce")
    return im

def draw_label(D, y, txt, sub, col):
    D.text((28, y), txt, font=PS(26), fill=col)
    D.text((28, y + 40), sub, font=SK(26), fill=GREY)

def frame(n, events=None):
    events = [] if events is None else events
    canvas = Image.new('RGBA', (NW, H // Z), NAVY + (255,))
    seg = next((s for s in TIMELINE if s[0] <= n < s[1]), None)
    if seg:
        t0, t1, (title, m1, m2, pid, kname) = seg
        f = n - t0
        p, kit = PL[pid], KITS[kname]
        if m1:
            top = draw_v1(TOP[1], m1, p, kit, f)
        else:
            top = draw_v1(TOP[1], "idle", p, kit, f)
            top = Image.alpha_composite(top, Image.new('RGBA', top.size, (8, 8, 12, 170)))
        bot = draw_v2(BOT[1], m2, p, kit, f, events)
        if f == 0: events.append("blip")
    else:
        # intro / outro: everyone idles (set 1 top, set 2 bottom)
        f = n
        top = panel_bg(TOP[1]); bot = panel_bg(BOT[1], f * 2 / 3 if n >= TIMELINE[-1][1] else 0)
        cast = [("tatum", "home"), ("queta", "statement"), ("pritchard", "away")]
        for k, (pid, kn) in enumerate(cast):
            fx = 26 + k * 42
            pose = v1.POSES["idle0" if (f // 12 + k) % 2 == 0 else "idle1"]
            top.alpha_composite(v1.render(PL[pid], KITS[kn], pose),
                                (fx - (v1.OX + 11), TOP[1] - 20 - (v1.CH - 2)))
            if n >= TIMELINE[-1][1]:
                st = state(v2.MOVES["run"], f + k * 3)
                pose2 = v2.POSES[st[1]]; air = st[2]
            else:
                pose2 = v2.POSES["idle0" if (f // 12 + k) % 2 == 0 else "idle1"]; air = 0
            bot.alpha_composite(v2.render(PL[pid], KITS[kn], pose2),
                                (fx - (v2.OX + 11), BOT[1] - 20 - (v2.CH - 2) - air))
        if n in (0, TIMELINE[-1][1]): events.append("blip")
    canvas.alpha_composite(top, (0, TOP[0]))
    canvas.alpha_composite(bot, (0, BOT[0]))
    big = canvas.convert('RGB').resize((W, H), Image.NEAREST)
    D = ImageDraw.Draw(big)
    # header
    if seg:
        title = seg[2][0]
        D.text((W // 2, 80), title, font=PS(58), fill=GOLD, anchor="mm")
        if not seg[2][1]:
            D.text((W // 2, 150), "NEW IN SET 2", font=SK(34), fill=GREEN, anchor="mm")
        else:
            D.text((W // 2, 150), "SET 1  vs  SET 2", font=SK(34), fill=GREY, anchor="mm")
        p = PL[seg[2][3]]
        D.text((W - 28, TOP[0] * Z + 18), f'{p["label"]} {p["name"].upper()}', font=SK(26),
               fill=GREY, anchor="ra")
        if not seg[2][1]:
            D.text((W // 2, (TOP[0] + 34) * Z), "NOT IN SET 1", font=PS(34),
                   fill=(110, 114, 130), anchor="mm")
    else:
        D.text((W // 2, 80), "SPRITE MOVES", font=PS(58), fill=GOLD, anchor="mm")
        D.text((W // 2, 150), "SET 1  vs  SET 2", font=SK(34), fill=GREY, anchor="mm")
    draw_label(D, TOP[0] * Z + 14, "SET 1", "FACING CAMERA", WHITE)
    draw_label(D, BOT[0] * Z + 14, "SET 2", "SIDE VIEW - LEAN, SQUASH, DUST", GOLD)
    if n >= TIMELINE[-1][1]:
        k = min(1, (n - TIMELINE[-1][1]) / 10)
        D.rectangle([0, 1836 - int(40 * k), W, H], fill=(8, 8, 12))
        D.text((W // 2, 1872 - int(20 * k)), f"SET 2: {len(v2.MOVES)} MOVES - {len(v2.POSES)} POSE FRAMES",
               font=SK(32), fill=WHITE, anchor="mm")
    return big

# ---------------------------------------------------------------- audio
def audio(path, ev):
    SR = 48000; N = int(SR * DUR); out = np.zeros(N); rng = np.random.default_rng(9)
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
    def thud(t, f0, f1, g, dur):
        s = np.sin(2 * np.pi * np.cumsum(np.linspace(f0, f1, int(dur * SR))) / SR)
        add(s * env(len(s), 0.002, dur * 0.8), t, g)
    beat = 0.5; step = beat / 2
    prog = [(45, [57, 60, 64]), (41, [53, 57, 60]), (43, [55, 59, 62]), (40, [52, 56, 59])]
    t = 0.0; k = 0
    while t < DUR - 0.3:
        root, ch = prog[int(t / (beat * 4)) % 4]
        if k % 2 == 0:
            s = sq(note(root), step * 0.9); add(s * env(len(s), 0.003, 0.05), t, 0.11)
        s = sq(note(ch[k % 3] + 12), step * 0.6, 0.25); add(s * env(len(s), 0.002, 0.06), t, 0.05)
        t += step; k += 1
    for n, kinds in ev.items():
        t = n / FPS
        for kd in kinds:
            if kd == "bounce": thud(t, 170, 70, 0.4, 0.09)
            elif kd == "thud": thud(t, 110, 50, 0.35, 0.12)
            elif kd == "catch": thud(t, 130, 60, 0.4, 0.12)
            elif kd == "whoosh":
                x = rng.standard_normal(int(0.35 * SR)); x = lp(x, 0.1) * np.sin(np.linspace(0, np.pi, len(x)))
                add(x, t, 1.1)
            elif kd == "swish":
                x = rng.standard_normal(int(0.3 * SR)); x = x - lp(x, 0.2); add(x * env(len(x), 0.003, 0.25), t, 0.3)
            elif kd in ("clang", "swat"):
                tt = np.arange(int(0.4 * SR)) / SR
                f0 = 420 if kd == "clang" else 700
                s = (np.sin(2 * np.pi * f0 * tt) + 0.6 * np.sin(2 * np.pi * f0 * 2.4 * tt)) * np.exp(-tt * 9)
                add(s, t, 0.35); thud(t, 110, 40, 0.5, 0.2)
            elif kd == "blip":
                s = np.concatenate([sq(note(84), 0.05), sq(note(91), 0.07)]); add(s * env(len(s), 0.002, 0.03), t, 0.1)
    out[-int(0.5 * SR):] *= np.linspace(1, 0, int(0.5 * SR))
    out /= np.abs(out).max() * 1.12
    w = wave.open(path, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes()); w.close()

if __name__ == '__main__':
    if sys.argv[1] == 'stills':
        out = sys.argv[2]; os.makedirs(out, exist_ok=True)
        for ts in sys.argv[3:]:
            frame(int(float(ts) * FPS)).save(os.path.join(out, f't{float(ts):05.2f}.png'))
        print('segments:', [(round(a / FPS, 2), s[0]) for a, b, s in TIMELINE], 'dur', round(DUR, 2))
    else:
        dst = sys.argv[2]
        with tempfile.TemporaryDirectory() as tmp:
            vid = os.path.join(tmp, 'v.mp4')
            p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                                  '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264',
                                  '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', vid],
                                 stdin=subprocess.PIPE)
            ev = {}
            for n in range(NF):
                e = []
                p.stdin.write(frame(n, e).tobytes())
                if e: ev[n] = e
            p.stdin.close(); p.wait()
            wav, norm_ = os.path.join(tmp, 'a.wav'), os.path.join(tmp, 'n.wav')
            audio(wav, ev)
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wav, '-af', 'loudnorm=I=-14:TP=-1.5',
                            '-ar', '48000', norm_], check=True)
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', vid, '-i', norm_, '-c:v', 'copy',
                            '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', dst],
                           check=True)
        print('done ->', dst, f'({DUR:.1f}s)')
