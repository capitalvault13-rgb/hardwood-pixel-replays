"""Measure every player's skin tone from their nba.com headshot and write it into players.json.

Usage: python3 tools/sample_skin.py [team,team,...] [--dry-run]      (default: every drawn team)
Needs opencv-python-headless < 5 (it bundles the face detector): pip install "opencv-python-headless<5"

For each sprites/<team>/source/<id>.jpg:
  1. find the face (Haar detector, a looser second pass for headbands, a small-face pass for
     full-body photos; otherwise the usual headshot framing)
  2. take the pixels in an oval from forehead to chin whose hue and saturation are skin
     (hair, beard, eyes, teeth and headbands drop out), trim the brightest and darkest 15%
  3. lightness = the lit side (60th percentile), colour = the median
  4. remove each team's photo-shoot colour cast and brightness, measured against players the
     previous tones put in the same lightness bracket, so a roster's mix does not skew it
  5. keep hue (50-68 deg) and chroma (21-32) in the range of real skin; studio light flushes
     pale faces pink
Writes "skin" and "skin_source" for each player, and keeps the hand-picked tone as
"skin_picked" (step 4 brackets on it, so re-running gives the same result). Players without a headshot keep their tone.
Then run tools/make_sprites.py for each team.
"""
import json, os, sys
import cv2, numpy as np
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASC = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml'))
CASC2 = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_alt2.xml'))

def face_box(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = g.shape
    faces = CASC.detectMultiScale(g, 1.08, 5, minSize=(w // 8, w // 8))
    if len(faces) == 0:   # headbands hide the brow line: retry with the alt2 model and an equalised image
        faces = CASC2.detectMultiScale(cv2.equalizeHist(g), 1.05, 3, minSize=(w // 8, w // 8))
    faces = [f for f in faces if f[2] >= w * .18 and abs(f[0] + f[2] / 2 - w / 2) < w * .15]   # big and centred
    if len(faces) == 0:   # full-body photos: a small face near the top centre
        small = CASC.detectMultiScale(g, 1.05, 4, minSize=(w // 14, w // 14), maxSize=(w // 4, w // 4))
        faces = [f for f in small if f[1] < h * .4 and abs(f[0] + f[2] / 2 - w / 2) < w * .12]
    if len(faces) == 0:
        return None
    # the headshot's subject: biggest face nearest the top centre
    return max(faces, key=lambda f: f[2] * f[3] - abs(f[0] + f[2] / 2 - w / 2) * 2)

REGIONS = {   # (x0, x1, y0, y1) as fractions of the face box: drawn on check sheets
    'face': (.22, .78, .14, .92),
}

def skin_pixels(img, box):
    """Skin pixels in an oval over the face: hue/saturation gate that holds for every skin tone."""
    x, y, bw, bh = box
    x0, x1, y0, y1 = REGIONS['face']
    sl = (slice(int(y + y0 * bh), int(y + y1 * bh)), slice(int(x + x0 * bw), int(x + x1 * bw)))
    crop = img[sl]; hh, ww = crop.shape[:2]
    yy, xx = np.mgrid[0:hh, 0:ww]
    oval = ((xx - ww / 2) / (ww / 2)) ** 2 + ((yy - hh / 2) / (hh / 2)) ** 2 <= 1
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV).astype(int)
    H, Sat, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    ok = oval & ((H <= 22) | (H >= 172)) & (Sat >= 40) & (Sat <= 200) & (V >= 35) & (V <= 250)
    return crop[ok]

def sample(path):
    img = cv2.imread(path)
    box = face_box(img)
    found = box is not None
    if not found:   # fall back to the usual headshot framing
        h, w = img.shape[:2]; box = (int(w * .34), int(h * .16), int(w * .32), int(w * .32))
    px = skin_pixels(img, box)
    if len(px) < 200:
        return None, found, [int(v) for v in box], len(px)
    lab = cv2.cvtColor(px.reshape(-1, 1, 3).astype(np.uint8), cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(float)
    L = lab[:, 0]
    lo, hi = np.percentile(L, [15, 85])                       # trim shine and deep shadow
    keep = lab[(L >= lo) & (L <= hi)]
    med = np.median(keep, axis=0)
    med[0] = np.percentile(keep[:, 0], 60)       # the sprite's base tone is the lit side; its own shade pixels do shadow
    return [float(v) for v in med], found, [int(v) for v in box], len(keep)      # Lab, corrected below

def lab2rgb(lab):
    v = np.clip(np.array(lab).reshape(1, 1, 3), 0, 255).astype(np.uint8)
    return [int(x) for x in cv2.cvtColor(v, cv2.COLOR_LAB2RGB).reshape(3)]

def correct(out):
    """Remove each team's photo-shoot colour cast: shift its median a/b chroma to the league's."""
    ok = {k: v for k, v in out.items() if v['lab']}
    league = np.median([v['lab'][1:] for v in ok.values()], axis=0)
    teams = {k.split('/')[0] for k in ok}
    cast = {t: np.median([v['lab'][1:] for k, v in ok.items() if k.startswith(t + '/')], axis=0) - league for t in teams}
    # exposure: compare players the hand-picked tones put in the same lightness bracket across teams
    toL = lambda rgb: float(cv2.cvtColor(np.uint8([[rgb]]), cv2.COLOR_RGB2LAB)[0, 0, 0])
    cur = {k: toL(v['current']) for k, v in ok.items()}
    edges = np.percentile(list(cur.values()), np.linspace(0, 100, 7))
    bracket = lambda L: int(np.clip(np.searchsorted(edges, L) - 1, 0, 5))
    expect = {}
    for k, v in ok.items(): expect.setdefault(bracket(cur[k]), []).append(v['lab'][0])
    expect = {b: np.median(x) for b, x in expect.items()}
    lin = lambda L: ((L / 2.55 + 16) / 116) ** 3            # L (0-255 scale) -> relative luminance
    expo = {t: float(np.median([lin(v['lab'][0]) / lin(expect[bracket(cur[k])]) for k, v in ok.items() if k.startswith(t + '/')])) for t in teams}
    for k, v in out.items():
        if not v['lab']: v['rgb'] = None; continue
        t = k.split('/')[0]; L, a, b = v['lab']; da, db = cast[t]
        # exposure: undo the shoot's brightness as a gain on luminance, then keep L in the range of real skin
        fade = min(1.0, max(0.0, (L - 140) / 60))          # pale skin clips in bright shoots: correct it less
        Y = lin(L) / expo[t] ** (1 - fade)
        L = min(204.0, max(40.0, (116 * Y ** (1 / 3) - 16) * 2.55))
        # colour: remove the shoot's cast, then keep hue and chroma inside the range of real skin
        a, b = a - 128 - da, b - 128 - db
        hue = min(68, max(50, np.degrees(np.arctan2(b, a))))
        C = min(32, max(21, np.hypot(a, b)))
        v['rgb'] = lab2rgb([L, C * np.cos(np.radians(hue)) + 128, C * np.sin(np.radians(hue)) + 128])
        v['raw'] = lab2rgb(v['lab'])
    return {t: [round(float(x), 1) for x in c] + [round(expo[t], 2)] for t, c in cast.items()}

if __name__ == '__main__':
    args = [x for x in sys.argv[1:] if not x.startswith('--')]; dry = '--dry-run' in sys.argv
    allteams = sorted(t for t in os.listdir(f'{R}/sprites') if os.path.exists(f'{R}/sprites/{t}/players.json'))
    teams = args[0].split(',') if args else allteams
    out = {}
    for t in allteams:   # every team is sampled: the cast / exposure correction compares teams
        for p in json.load(open(f'{R}/sprites/{t}/players.json'))['players']:
            f = f'{R}/sprites/{t}/source/{p["id"]}.jpg'
            if not os.path.exists(f): continue
            lab, found, box, n = sample(f)
            out[f'{t}/{p["id"]}'] = dict(lab=lab, face=found, box=box, n=n, current=p.get('skin_picked', p['skin']))
    casts = correct(out)
    changed = 0
    for t in teams:
        path = f'{R}/sprites/{t}/players.json'; cfg = json.load(open(path))
        for p in cfg['players']:
            v = out.get(f'{t}/{p["id"]}')
            if not v or not v['rgb']: continue
            if p['skin'] != v['rgb']: changed += 1
            p.setdefault('skin_picked', p['skin'])      # the hand-picked tone: the brackets for step 4
            p['skin'] = v['rgb']
            p['skin_source'] = 'headshot' + ('' if v['face'] else ' (face position assumed)')
        if not dry:
            json.dump(cfg, open(path, 'w'), indent=1, ensure_ascii=False)
    nofoto = [k for t in teams for k in [f'{t}/{p["id"]}' for p in json.load(open(f'{R}/sprites/{t}/players.json'))['players']] if k not in out or not out[k]['rgb']]
    print(f'{changed} skin tones updated across {len(teams)} teams; kept (no usable headshot): {nofoto}')
