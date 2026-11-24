# Hardwood Index — Pixel Replays

15-second vertical (1080x1920, 30fps) pixel-art recreations of real NBA plays, in the
Hardwood Index broadcast-camera style (see "Animation style" below). Each replay lives in its own folder under `episodes/` and renders
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
data/courts.json      home floor for all 30 teams (stain, paint, aprons, sidelines, lines, wordmark, centre emblem)
data/courts_sheet.png all 30 floors on one labelled check sheet (tools/court_sheet.py)
tools/fetch_rosters.py     refreshes data/ from nba.com
sprites/<team>/       one folder per team (NBA 3-letter code, lower case); cut sheets at native size, drawn teams at 3x
sprites/<team>/source/  the original sprite sheet that team's PNGs were cut from
sprites/atl/          Hawks chibi v2 — 19 players x 3 kits (home / away / statement), numbered at 3x
sprites/atl/plain/    the same sprites as cut from the sheet: native size, no numbers (used for recoloured stand-ins)
sprites/bos/          Celtics — full 2026-27 roster (17), drawn by tools/make_sprites.py from sprites/bos/players.json
sprites/lal/          Lakers — full 2026-27 roster (18), drawn the same way from sprites/lal/players.json
sprites/<team>/       every other team, drawn the same way from each players.json:
                      East  bkn cha chi cle det ind mia mil nyk orl phi tor was
                      West  dal den gsw hou lac mem min nop okc phx por sac sas uta
tools/extract_sprites.py   cuts a sheet into sprites/<team>/plain/*.png
tools/number_sprites.py    adds jersey numbers to cut sprites from sprites/<team>/numbers.json (3x output + sheet.png)
tools/make_sprites.py      draws a team's sprites from players.json (look per player + kit colours)
tools/fetch_headshots.py   pulls a team's nba.com headshots into sprites/<team>/source/ and makes face sheets
tools/sample_skin.py       measures every player's skin tone from their headshot into players.json
tools/court_sheet.py       redraws data/courts_sheet.png from data/courts.json
lib/broadcast.py      shared renderer: side-on court, crowd, hoops, camera, captions, arrows, word cards
fonts/                Press Start 2P, Silkscreen, Inter ExtraBold/Black (all SIL Open Font License)
episodes/NNN-name/    replay.py (visuals), audio.py (chiptune + SFX), render.sh
renders/              finished MP4s
reference/            replay 001 in the original top-down style (kept for reference)
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
Hair styles:
- short, built in `tools/hair_builder.py` from three parts (height above the scalp, hairline:
  straight / line-up / receding / fringe / middle part, and texture: plain / waves / curls /
  twists / straight streaks): buzz, buzz_lineup, buzz_receding, waves, crop, crop_lineup,
  crop_fringe, textured_crop, curly_short, curly_top, curls_forward, sponge, high_top, frohawk,
  middle_part, mullet, swept_side, man_bun, cornrows_flat
- other short cuts: bald, high_tight, fade_short, twists_short, messy_fringe, quiff, swept_back
- longer straight / wavy: wavy_medium, long_hair
- curls and afros: curly_high, afro, afro_wide (a wider round afro), afro_long, afro_tail, twists_spiky
- braids and locs: cornrows (braid on the right), cornrows_left, braids_back, box_braids, locs,
  locs_long, locs_top, locs_knot (locs in a high top-knot)
- with a built-in headband: short_band, afro_band, locs_band, locs_long_band, long_band,
  long_band_wide.
  `"headband": [r,g,b]` on any other style draws a band over it.
- dyed tips: `"hair_tip": [r,g,b]` and `"tip_rows": n` colour the hair down to head row n.

Beards: none, mustache, goatee, chinstrap, short, full, thick, huge. Extras: glasses, earrings,
armband, undershirt sleeves, arm sleeve, wristbands, socks.

Drawn sprites are saved at 3x the 23 px chibi grid (69 px wide), so jersey numbers can use finer
pixels than the rest of the sprite: 5x7 block digits in the kit's `number` colour (default: trim)
with an optional `number_outline` (only the Lakers use one; on most kits an outline swamps the
jersey colour at replay size). Replays draw sprite pixels at 3x, so load these at 1x
(`load()` in `replay.py` picks the factor from the image width). A kit can set `"numbers": false`.

Before drawing a team, refresh the rosters, then pull the headshots:

```bash
python3 tools/fetch_headshots.py bkn /tmp/faces
```

This saves each player's nba.com headshot to `sprites/<team>/source/<id>.jpg` (commit these),
writes close-up face sheets to the folder given, and prints the ids, labels and names to start
`players.json` from. Read hair, beard, skin and extras from the photos. A player with no
headshot yet gets a plain look with `look_source` starting `guess:`. When two players on a team
come out looking alike, compare them side by side with their photos and give them distinct
styles; add a new hair style to `tools/make_sprites.py` rather than reusing a near miss.

### Western Conference sprites

All 15 West teams have sprites. Kits: `home` is the white Association kit, `away` the
team-colour Icon kit, `statement` the alternate kit. Home and away colours follow the team's
primary colours; statement colours are approximate and worth checking against the real
2026-27 uniforms before a team appears in a replay. Looks were read from the nba.com headshots in
`sprites/<team>/source/`, one per player. Richie Saunders (MEM #5) has no nba.com headshot yet, so
his sprite is a generic placeholder (`look_source` says so). Redraw it once a photo is up.

### Skin tones

Skin tones are measured from the headshots, not picked by eye:

```bash
pip install "opencv-python-headless<5"
```

```bash
python3 tools/sample_skin.py
```

It finds the face, keeps the skin-coloured pixels between forehead and chin, removes each team's
photo-shoot colour cast and brightness, and keeps the result in the natural range of skin hue
(studio lights flush pale faces pink). It samples every team, because the per-shoot correction
compares teams, and writes `skin` and `skin_source` into each `players.json`. The original
hand-picked tone stays as `skin_picked` so a re-run gives the same result. Then rerun
`tools/make_sprites.py` for each team. Players with no usable headshot keep their tone.

## Animation style

Since replay 002's re-render, every replay uses the broadcast-camera look in `lib/broadcast.py`:

- **Camera**: side-on and slightly raised. The court runs left to right; depth is squashed to 5/8
  of the length scale (8 art px per foot along the court, 5 across it, 5.3 up). The camera pans
  with the ball and never zooms. The court sits in the middle of the frame, with crowd above and below.
- **Pixel grid**: one art pixel = 3 screen pixels, the same scale as the 3x sprites, and every
  position snaps to it so the floor, crowd, hoops and players read as one piece.
- **Floor**: the home team's floor from `data/courts.json`. That sets the wood stain and pattern
  (planks, parquet, herringbone), the paint with its diagonal gloss band, the baseline aprons,
  the sideline border and the line colours. The inner half of each free-throw circle is dashed,
  and the city runs up each apron beside the baseline. The centre emblem shows the home team's
  abbreviation in our own design, never a real team logo. `HARDWOOD INDEX` sits along the far
  sideline and scrolls on the LED board.
- **Hoops**: stanchion pad on the apron, post and boom, a leaned glass board with a shooter's
  square, an orange rim and a white net. These are depth-sorted with the players at z = 25 ft.
- **Crowd**: fans facing the court in the far and baseline stands, and the backs of heads in the
  near stands (dimmer, so captions read on top). They wear mostly home colours and jump with
  their arms up after a make (`cheer_t`).
- **Players**: soft drop shadow under every player and the ball, a one-pixel walking bob, and
  sprites flip to face the way they move.
- **Captions**: sentence case, Inter ExtraBold, lime `(158,222,0)`, 7 px black outline plus a
  soft shadow, laid over the near stands. No highlight words.
- **Graphics**: pink `(240,40,110)` dashed rings round a player and dashed arrows that draw on.
  Distances are a white dashed line on the floor with a lime `NN ft` label.
- **Cut-aways**: full-frame black word cards with big white Inter Black text (one word may
  be coloured), used for the record card and the end card.
- **Header/footer**: the Hardwood Index header and scorebug stay above the court. The source line
  sits at the bottom.

New episodes build an `Arena(court_look('dal'))` for the home team, then for each frame call
`arena.begin(camera_x, t, cheer_t, led)`, then `arena.draw_actors(img, actors, ball)`, and then the
overlays (`caption`, `dashed_ellipse`, `dashed_arrow`, `word_card`). `episodes/002-kuminga/replay.py`
is the worked example.

## Home floors

`data/courts.json` holds the home floor for all 30 teams. Each team's Main court is matched for
wood stain, paint, aprons, sideline border, line colour and wordmark, using the real floor and
the team's official colours. Only the colours and layout are taken: there are no team logos,
NBA marks or sponsor names, and the centre emblem is our own. `null` means natural wood:
Detroit, Toronto and New Orleans have unpainted lanes, and Denver and Memphis have wood
aprons. Houston's floor was read from broadcast-style gameplay footage (red lane, red apron),
not from a full-floor reference, so check it against the real Toyota Center floor before a
Rockets home replay.

After changing a floor, redraw the check sheet and look at it:

```bash
python3 tools/court_sheet.py
```

Alternate floors (City Edition, playoffs, NBA Cup) are not in the database yet.

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
python3 episodes/002-kuminga/replay.py stills /tmp 1.6 3.3 4.8 6.6 8.8 11.5 13.0
```

## Making the next replay

1. Copy `episodes/002-kuminga/` to `episodes/003-<name>/` and bump `PIXEL REPLAY #00N` in `replay.py`.
2. Edit the top of `replay.py`: timeline constants (`T_REL`, `T_LAND`, ...), the home floor
   (`court_look('<team>')`), the shooter's spot in court feet
   (`KX`, `KZ`, derived from the real shot distance), the two team lists (court feet), the
   camera path (`cam_center`), scorebug states (`score_state`), captions (`CAPS`, sentence case),
   the record card text and the footer source line.
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
- Player positions are illustrative. Kuminga's spot is computed from the 74-ft distance to the far rim
  (14.8 ft from his own baseline, 3 ft off the rim line: inside his own paint).
- The floor is the Dallas home floor from `data/courts.json` (silver-grey stain, navy lanes, aprons and
  sidelines) with our own centre emblem. It has no Mavericks logo, arena name or sponsor marks.
- Left out on purpose: the claim that the heave was a pass intended for Jock Landale (single source, contradicted).
