"""Refresh data/ from nba.com: every team's current roster and coaching staff.

Usage: python3 tools/fetch_rosters.py
Needs network access to www.nba.com (the hardwood-pixel-replays cloud environment allows it).
Writes data/teams.json, data/rosters/<abbr>.json and data/players.csv.
"""
import csv, datetime, json, os, re, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data')
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36'

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    return urllib.request.urlopen(req, timeout=40).read().decode('utf-8')

def next_data(html):
    return json.loads(re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S).group(1))

def num_key(n):
    return (int(n) if (n or '').isdigit() else 999, n or '')

def main():
    today = datetime.date.today().isoformat()
    os.makedirs(os.path.join(OUT, 'rosters'), exist_ok=True)
    links = sorted(set(re.findall(r'/team/16106127\d{2}/[a-z0-9-]+', get('https://www.nba.com/teams'))))
    teams, allp = [], []
    for link in links:
        t = next_data(get('https://www.nba.com' + link))['props']['pageProps']['team']
        i = t['info']
        players = [{"num": p.get("NUM"), "name": p["PLAYER"], "slug": p.get("PLAYER_SLUG"), "player_id": p.get("PLAYER_ID"),
                    "position": p.get("POSITION"), "height": p.get("HEIGHT"), "weight": p.get("WEIGHT"),
                    "birth_date": p.get("BIRTH_DATE"), "age": p.get("AGE"), "exp": p.get("EXP"),
                    "school": p.get("SCHOOL"), "how_acquired": p.get("HOW_ACQUIRED")} for p in t['roster']]
        players.sort(key=lambda p: num_key(p["num"]))
        rec = {"team_id": i['TEAM_ID'], "abbr": i['TEAM_ABBREVIATION'], "city": i['TEAM_CITY'], "name": i['TEAM_NAME'],
               "slug": i['TEAM_SLUG'], "conference": i['TEAM_CONFERENCE'], "division": i['TEAM_DIVISION'],
               "season": i['SEASON_YEAR'], "source": 'https://www.nba.com' + link, "fetched": today,
               "players": players,
               "coaches": [{"name": c["COACH_NAME"], "role": c.get("COACH_TYPE")} for c in t.get('coaches', [])]}
        with open(os.path.join(OUT, 'rosters', rec['abbr'].lower() + '.json'), 'w', encoding='utf-8') as fh:
            json.dump(rec, fh, indent=1, ensure_ascii=False)
        teams.append({k: rec[k] for k in ("abbr", "city", "name", "team_id", "conference", "division", "slug", "source")}
                     | {"players": len(players)})
        allp += [{"team": rec['abbr'], **p} for p in players]
        print(rec['abbr'], len(players))
        time.sleep(1)
    teams.sort(key=lambda x: x['abbr'])
    with open(os.path.join(OUT, 'teams.json'), 'w', encoding='utf-8') as fh:
        json.dump({"season": rec['season'], "fetched": today, "source": "https://www.nba.com/teams", "teams": teams},
                  fh, indent=1, ensure_ascii=False)
    with open(os.path.join(OUT, 'players.csv'), 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=list(allp[0].keys()))
        w.writeheader()
        w.writerows(sorted(allp, key=lambda p: (p['team'], num_key(p['num']))))
    print(len(teams), 'teams,', len(allp), 'players')

if __name__ == '__main__':
    main()
