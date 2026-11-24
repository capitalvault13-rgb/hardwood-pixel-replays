# Hardwood Index — Pixel Replays

15-second vertical (1080x1920, 30fps) pixel-art recreations of real NBA plays, in the
Hardwood Index style. Each replay lives in its own folder under `episodes/` and renders
to `renders/`.

| # | Play | Folder | Render |
|---|------|--------|--------|
| 001 | Luka Dončić 61-ft halftime heave (POR @ LAL, Nov 6 2026) | — (reference only) | `reference/pixel-replay-001-luka.mp4` |
| 002 | Jonathan Kuminga 74-ft 3rd-quarter buzzer heave (ATL @ DAL, Mar 18 2026) | `episodes/002-kuminga/` | `renders/pixel-replay-002-kuminga.mp4` |
| 003 | Victor Wembanyama 50 vs Pelicans + his MVP case (NOP @ SAS, Nov 21 2026) | `episodes/003-wembanyama-50/` | `renders/pixel-replay-003-wembanyama-50.mp4` |

## Layout

```
data/teams.json       all 30 NBA teams (abbr, city, name, conference, division, nba.com link)
data/rosters/<abbr>.json   each team's current roster + coaches from nba.com (number, name, position, height, ...)
data/players.csv      every rostered player in one sheet
tools/fetch_rosters.py     refreshes data/ from nba.com
sprites/<team>/       one folder per team (NBA 3-letter code, lower case), native pixel size
sprites/<team>/source/  the original sprite sheet that team's PNGs were cut from
sprites/atl/          Hawks chibi v2 — 19 players x 3 kits (home / away / statement)
sprites/sas/          Spurs — Wembanyama only so far (drawn by tools/make_sprites.py; "tall": 4 for the rig)
sprites/bos/          Celtics — full 2026-27 roster (17), drawn by tools/make_sprites.py from sprites/bos/players.json
tools/extract_sprites.py   cuts a sheet into sprites/<team>/*.png
tools/make_sprites.py      draws a team's sprites from players.json (look per player + kit colours)
tools/animate_sprites.py     animation set 1: camera-facing pose rig (idle, dribble, pass, jump, shoot, dunk)
tools/animate_sprites_v2.py  animation set 2: side-facing 3/4 rig, 11 moves + effect tags; jersey numbers
                             (from the sprite label or "number"), clean 1-px pixel grid (no resampling)
tools/anim_demo.py           set-1 demo possession video;  tools/anim_compare.py  set 1 vs set 2 video
fonts/                Press Start 2P + Silkscreen (both SIL Open Font License)
episodes/NNN-name/    replay.py (visuals), audio.py (chiptune + SFX), render.sh
renders/              finished MP4s
reference/            earlier replays used as the style reference
```

Sprite file names: `sprites/<team>/<player>_<kit>.png`, e.g. `sprites/atl/kuminga_away.png`.
Hawks players: naw, mccollum, johnson, okongwu, ejjofor, flemings, daniels, wiggins, kuminga,
dort, newell, veesaar, nembhard, hield, kispert, gilbert, landale, dennis, gueye.

Opponents with no sprite set are drawn by recolouring Hawks home-kit sprites into the
opponent's colours (see `load(..., recolor=True)` in `replay.py`). They are generic
stand-ins and are never labelled.

## Roster data

`data/` holds every team's roster as listed on nba.com (2026-27 season, fetched 2026-11-17).
Refresh it with `python3 tools/fetch_rosters.py`; rosters change with trades and signings, so
refresh before naming a new team's sprites. Sprite files use the player's last name
(`sprites/bos/tatum_away.png`); `players.json` keeps the full name and nba.com player id.

The Hawks sprite sheet predates the current roster: Kuminga (now MIN), Hield (now CHI),
Nembhard and Gilbert are no longer Hawks, and Finney-Smith (#8) and Jalen Wilson (#22) have no
sprite yet. Kuminga stays in sprites/atl because replay 002 shows him as a Hawk (Mar 2026).

## Adding a team

Upload the team's sprite sheet in a Claude Code session with this repo attached and ask for
it to be added. The sheet goes in `sprites/<team>/source/` and the cut-out sprites in
`sprites/<team>/`. Once a team has sprites, replays can use them as real opponents instead
of recoloured Hawks.

### Drawing a team from photos

Add each player's look to `sprites/<team>/players.json` (skin, hair style, beard style,
headband, undershirt sleeves, armband, shoes) and run:

```bash
python3 tools/make_sprites.py bos
```

This writes `<id>_<kit>.png` for each kit plus `sheet.png`, a labelled check sheet.
Hair styles: bald, curly_short, wavy_medium, afro_band. Beards: none, short, full, thick.

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

### 003 — Wembanyama 50, and the MVP case
First replay animated with sprite set 2 (side view). Spurs 114, Pelicans 91, Nov 21 2026, Frost Bank Center.
- Line (NBA.com player game log): 50 PTS, 18 REB, 5 BLK, 4 STL, 1 AST, 32 MIN, 20-29 FG, 5-11 3PT, 5-6 FT, +35.
  Some NBA.com text and the NBA's post say 19 rebounds; we use the game log's 18.
- Halftime (AP via NBA.com): 32 PTS, 13 REB, 3 BLK, 3 STL; Spurs led 61-45. NBA.com Starting 5 gives 12 rebounds for
  his big half; we use AP's 13.
- The slam: AP — after a shove, he "scored the next seven points, including a one-handed slam over Yves Missi", first
  half (9:27 mark nearby). The defender wears Missi's #21 (nba.com roster); his look is not checked against a photo.
- The other Pelican (shooter on the block, closeout on the 50th) is generic and wears #30, a number no current
  Pelican wears, so he stands for no one.
- The block scene is illustrative (he had 3 blocks by halftime, 5 total); no specific block is claimed.
- 50th point: a 3-pointer for 108-82 with 6:29 left (AP); he then exited. The pre-shot 105-82 and his 47 are derived.
- Records (AP via NBA.com): first player since 1973-74 with 50 PTS, 15 REB, 4 STL, 5 BLK in a game; first with 50 PTS,
  5 BLK and five 3-pointers since 1979-80. Second 50 this month; career high 52 vs DAL, Nov 4.
- MVP (NBA.com Kia MVP Ladder, Nov 20 2026, i.e. before this game): 1 Doncic 38.1 PPG, 2 Wembanyama 28.6 PPG / 11.9 RPG /
  3.9 BPG, 3 Antetokounmpo 28.2 PPG. Per 36: 34.1 PTS, 14.2 REB, 4.6 BLK; "right at 30 minutes per game".
- Spurs "14th win in 15 games" (NBA post in the AP story). Ruled out Monday Nov 23 vs SAC with a back issue (NBA.com player news).
- Left out: betting odds (only reachable via ESPN, not verifiable this session).
- Wembanyama's sprite look (short dark hair, light goatee) was set from description, not checked against a photo.
  Pelicans kit colours and court are illustrative.
