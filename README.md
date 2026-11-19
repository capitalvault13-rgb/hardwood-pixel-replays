# Hardwood Index — Pixel Replays

15-second vertical (1080x1920, 30fps) pixel-art recreations of real NBA plays, in the
Hardwood Index style. Each replay lives in its own folder under `episodes/` and renders
to `renders/`.

| # | Play | Folder | Render |
|---|------|--------|--------|
| 001 | Luka Dončić 61-ft halftime heave (POR @ LAL, Nov 6 2026) | — (reference only) | `reference/pixel-replay-001-luka.mp4` |
| 002 | Jonathan Kuminga 74-ft 3rd-quarter buzzer heave (ATL @ DAL, Mar 18 2026) | `episodes/002-kuminga/` | `renders/pixel-replay-002-kuminga.mp4` |

## Layout

```
data/teams.json       all 30 NBA teams (abbr, city, name, conference, division, nba.com link)
data/rosters/<abbr>.json   each team's current roster + coaches from nba.com (number, name, position, height, ...)
data/players.csv      every rostered player in one sheet
tools/fetch_rosters.py     refreshes data/ from nba.com
sprites/<team>/       one folder per team (NBA 3-letter code, lower case); cut sheets at native size, drawn teams at 3x
sprites/<team>/source/  the original sprite sheet that team's PNGs were cut from
sprites/atl/          Hawks chibi v2 — 19 players x 3 kits (home / away / statement), numbered at 3x
sprites/atl/plain/    the same sprites as cut from the sheet: native size, no numbers (used for recoloured stand-ins)
sprites/bos/          Celtics — full 2026-27 roster (17), drawn by tools/make_sprites.py from sprites/bos/players.json
sprites/lal/          Lakers — full 2026-27 roster (18), drawn the same way from sprites/lal/players.json
tools/extract_sprites.py   cuts a sheet into sprites/<team>/plain/*.png
tools/number_sprites.py    adds jersey numbers to cut sprites from sprites/<team>/numbers.json (3x output + sheet.png)
tools/make_sprites.py      draws a team's sprites from players.json (look per player + kit colours)
fonts/                Press Start 2P + Silkscreen (both SIL Open Font License)
episodes/NNN-name/    replay.py (visuals), audio.py (chiptune + SFX), render.sh
renders/              finished MP4s
reference/            earlier replays used as the style reference
```

Sprite file names: `sprites/<team>/<player>_<kit>.png`, e.g. `sprites/atl/kuminga_away.png`.
Hawks players: naw, mccollum, johnson, okongwu, ejjofor, flemings, daniels, wiggins, kuminga,
dort, newell, veesaar, nembhard, hield, kispert, gilbert, landale, dennis, gueye.

Opponents with no sprite set are drawn by recolouring the plain (un-numbered) Hawks home-kit
sprites into the opponent's colours (see `load(..., recolor=True)` in `replay.py`). They are generic
stand-ins and are never labelled.

## Roster data

`data/` holds every team's roster as listed on nba.com (2026-27 season, fetched 2026-11-17).
Refresh it with `python3 tools/fetch_rosters.py`; rosters change with trades and signings, so
refresh before naming a new team's sprites. Sprite files use the player's last name
(`sprites/bos/tatum_away.png`); `players.json` keeps the full name and nba.com player id.

The Hawks sprite sheet predates the current roster: Kuminga (now MIN), Hield (now CHI),
Nembhard and Gilbert are no longer Hawks, and Finney-Smith (#8) and Jalen Wilson (#22) have no
sprite yet. Kuminga stays in sprites/atl because replay 002 shows him as a Hawk (Mar 2026).

Hawks numbers (`sprites/atl/numbers.json`) follow the 2026-27 nba.com roster for current Hawks.
Former Hawks keep the number they wore in Atlanta: Kuminga #0 and Hield #8 (both reported);
Nembhard #9 and Gilbert #00 come from the sheet's labels and are unverified.

## Adding a team

Upload the team's sprite sheet in a Claude Code session with this repo attached and ask for
it to be added. The sheet goes in `sprites/<team>/source/`, the cut-out sprites in `sprites/<team>/plain/`,
and `python3 tools/number_sprites.py <team>` writes the numbered sprites to `sprites/<team>/`. Once a team has sprites, replays can use them as real opponents instead
of recoloured Hawks.

### Drawing a team from photos

Add each player's look to `sprites/<team>/players.json` (skin, hair style, beard style,
headband, undershirt sleeves, armband, shoes) and run:

```bash
python3 tools/make_sprites.py bos
```

This writes `<id>_<kit>.png` for each kit plus `sheet.png`, a labelled check sheet.
Hair styles: bald, buzz, crop, high_tight, fade_short, messy_fringe, quiff, swept_back,
wavy_medium, curly_short, curly_top, curly_high, twists_short, twists_spiky, afro_tail,
cornrows, cornrows_left, braids_back, locs, locs_long, and the headband styles afro_band,
short_band, locs_band. Beards: none, goatee, chinstrap, short, full, thick. Extras: earrings,
armband, undershirt sleeves, arm sleeve, wristbands, socks.

Drawn sprites are saved at 3x the 23 px chibi grid (69 px wide), so jersey numbers can use finer
pixels than the rest of the sprite: 5x7 block digits in the kit's `number` colour (default: trim)
with an optional `number_outline`. Replays draw sprite pixels at 3x, so load these at 1x
(`load()` in `replay.py` picks the factor from the image width). A kit can set `"numbers": false`.

Before drawing a team, pull each player's nba.com headshot
(`https://cdn.nba.com/headshots/nba/latest/1040x760/<player_id>.png`) and commit it to
`sprites/<team>/source/<id>.jpg`, then read hair, beard, skin and extras from it. When two
players come out looking alike, compare them side by side with their photos and give them
distinct styles; add a new hair style to `tools/make_sprites.py` rather than reusing a near miss.

## Render a replay

Needs Python 3 with `numpy`, `Pillow` (and `scipy` only for `tools/extract_sprites.py`), plus `ffmpeg`.

```bash
pip install numpy pillow scipy
```

```bash
episodes/002-kuminga/render.sh
```

Quick check of a few frames before a full render (writes PNGs into the given folder):

```bash
python3 episodes/002-kuminga/replay.py stills /tmp 0.4 3.4 5.6 7.0 10.8 13.0
```

## Making the next replay

1. Copy `episodes/002-kuminga/` to `episodes/003-<name>/` and bump `PIXEL REPLAY #00N` in `replay.py`.
2. Edit the top of `replay.py`: timeline constants (`T_REL`, `T_LAND`, ...), shooter position
   (`KPOS`, derived from the real shot distance), the two team lists, scorebug states
   (`score_state`), captions (`CAPS` — `*word*` = gold, one gold word per caption), the hook box,
   record card text and footer source line.
3. Every number on screen must come from a source; list them in the episode notes below.
4. Render, check, commit the MP4 to `renders/`.

## Episode notes

### 002 — Kuminga, 74 ft
- Hawks 135, Mavericks 120 in Dallas, Mar 18 2026; Hawks' 11th straight win (AP via CBS Sports / Fox Sports).
- Kuminga defensive rebound, heave at the 3rd-quarter buzzer. Official play-by-play: 74-ft 3-pointer.
  Headlines say 75 ft; we use the play-by-play figure.
- Longest Hawks make of the play-by-play era (since 1996-97), passing Jason Terry's 63 ft (Jan 5 2000);
  sixth-longest make in NBA history (Fox News / Wikipedia "List of longest NBA field goals").
- Pre-shot scorebug 98-82 is derived from the quarter line (ATL 37-30-34, DAL 30-26-26) minus the
  buzzer three; it is not quoted directly by a source.
- Player positions are illustrative. Kuminga's spot is computed from the 74-ft distance (inside his own paint).
- Left out on purpose: the claim that the heave was a pass intended for Jock Landale (single source, contradicted).
