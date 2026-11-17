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
sprites/<team>/       one folder per team (NBA 3-letter code, lower case), native pixel size
sprites/<team>/source/  the original sprite sheet that team's PNGs were cut from
sprites/atl/          Hawks chibi v2 — 19 players x 3 kits (home / away / statement)
tools/extract_sprites.py   cuts a sheet into sprites/<team>/*.png
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

## Adding a team

Upload the team's sprite sheet in a Claude Code session with this repo attached and ask for
it to be added. The sheet goes in `sprites/<team>/source/` and the cut-out sprites in
`sprites/<team>/`. Once a team has sprites, replays can use them as real opponents instead
of recoloured Hawks.

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
