"""Fetch a team's nba.com headshots into sprites/<team>/source/<id>.jpg and make face sheets.

Usage: python3 tools/fetch_headshots.py <team> [faces_dir]
  <team>      lower-case NBA code, e.g. bkn (roster read from data/rosters/<team>.json)
  faces_dir   where to write faces_<team>_<n>.png contact sheets (9 close-up faces each,
              labelled with number, name and sprite id) for reading each player's look
Prints a JSON list of {id, label, name, full_name, player_id} to start players.json from.
Sprite ids are the ASCII last name without suffixes (Jr., III, ...); players on the same team
who share a last name get their first initial in front (jwilliams).
"""
import json, os, re, sys, unicodedata, urllib.request
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = 'https://cdn.nba.com/headshots/nba/latest/1040x760/{}.png'
SUFFIX = {'jr', 'jr.', 'sr', 'sr.', 'ii', 'iii', 'iv', 'v'}

def ascii_(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()

def last_name(full):
    parts = [p for p in full.replace(',', ' ').split() if p.lower() not in SUFFIX]
    return ' '.join(parts[1:]) if len(parts) > 1 else parts[0]

def ids_for(players):
    base = {p['player_id']: re.sub(r'[^a-z]', '', ascii_(last_name(p['name'])).lower()) for p in players}
    out = {}
    for p in players:
        b = base[p['player_id']]
        if list(base.values()).count(b) > 1:
            b = ascii_(p['name'])[0].lower() + b
        out[p['player_id']] = b
    return out

def main(team, faces_dir=None):
    roster = json.load(open(os.path.join(ROOT, 'data', 'rosters', f'{team}.json')))['players']
    src = os.path.join(ROOT, 'sprites', team, 'source'); os.makedirs(src, exist_ok=True)
    ids = ids_for(roster)
    rows, faces = [], []
    for p in roster:
        pid = ids[p['player_id']]
        dst = os.path.join(src, pid + '.jpg')
        if not os.path.exists(dst):
            try:
                req = urllib.request.Request(URL.format(p['player_id']), headers={'User-Agent': 'Mozilla/5.0'})
                im = Image.open(urllib.request.urlopen(req, timeout=40)).convert('RGBA')
                bg = Image.new('RGBA', im.size, (214, 214, 214, 255)); bg.alpha_composite(im)
                bg.convert('RGB').save(dst, quality=90)
            except Exception as e:
                print(f'no headshot for {p["name"]} ({p["player_id"]}): {e}', file=sys.stderr)
                continue
        label = f'#{p["num"]}' if p['num'] else '#'
        rows.append({'id': pid, 'label': label, 'name': ascii_(last_name(p['name'])),
                     'full_name': p['name'], 'player_id': p['player_id']})
        faces.append((f'{label} {p["name"]} [{pid}]', dst))
    if faces_dir:
        os.makedirs(faces_dir, exist_ok=True)
        f = ImageFont.truetype(os.path.join(ROOT, 'fonts', 'Silkscreen-Regular.ttf'), 16)
        for n in range(0, len(faces), 9):
            sh = Image.new('RGB', (3 * 400, 3 * 420), (200, 200, 200)); dr = ImageDraw.Draw(sh)
            for i, (lab, path) in enumerate(faces[n:n + 9]):
                im = Image.open(path)
                w, h = im.size
                im = im.crop((int(w * .26), 0, int(w * .74), int(h * .66))).resize((400, 396))
                x, y = (i % 3) * 400, (i // 3) * 420
                sh.paste(im, (x, y + 24)); dr.text((x + 4, y + 2), lab, font=f, fill=(0, 0, 0))
            sh.save(os.path.join(faces_dir, f'faces_{team}_{n // 9 + 1}.png'))
    print(json.dumps(rows, ensure_ascii=False))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
