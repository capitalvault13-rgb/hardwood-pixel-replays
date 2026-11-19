"""Build hair overlays for the 23 px chibi head from parts: height, hairline, texture, top.

Overlay characters: H hair, h highlight, k hair shadow, s faded skin, S skin, # outline, . unchanged.
Head outline reference (row: left #, right #): 0: 8-13 top, 1: 6,7|14,15, 2: 5|16, 3: 4|17, 4-6: 4|18.
"""
HEAD_L = {1: 6, 2: 5, 3: 4, 4: 4, 5: 4, 6: 4}      # left outline col per head row
HEAD_R = {1: 15, 2: 16, 3: 17, 4: 18, 5: 18, 6: 18}

def tex(kind, x, y):
    if kind == 'plain':    return 'h' if (x * 3 + y * 5) % 11 == 0 else 'H'
    if kind == 'curls':    return 'h' if (x % 3 == 0 and y % 2 == 0) or (x % 3 == 1 and y % 2 == 1 and x % 2) else ('k' if (x + y) % 3 == 2 else 'H')
    if kind == 'waves':    return 'h' if (y % 2 == 0 and 7 <= x <= 15) or (y % 2 == 1 and x in (6, 16)) else 'H'
    if kind == 'twists':   return 'h' if x % 2 == 0 else 'k' if y % 3 == 0 else 'H'
    if kind == 'straight': return 'h' if (x - y) % 4 == 0 else 'H'
    if kind == 'swept':    return 'h' if (x + y) % 4 == 0 else 'H'
    if kind == 'cornrow':  return 'h' if x % 2 == 0 else 'H'
    return 'H'

def build(raise_=1, hairline='straight', texture='plain', top='round', width=0):
    """raise_: rows the hair sits above the scalp (0 = buzz, 3 = high top); width: extra px per side."""
    rows = {}
    top_row = 1 - raise_ - (1 if raise_ else 0) + (1 if raise_ == 0 else 0)
    top_row = -raise_ if raise_ else 1
    # silhouette: for each row from top to row 3 (scalp), left/right outline cols
    span = {}
    for r in range(top_row, 4):
        if raise_ == 0:
            l, rr = HEAD_L[r] + (0 if r > 1 else 0), HEAD_R[r]
        else:
            k = r - top_row          # rows from the top of the hair
            if top == 'flat':
                l, rr = 4 - width, 18 + width
                if k == 0: l, rr = 5 - width, 17 + width
            else:
                prof = [(7, 14), (5, 16), (4, 17), (4, 18), (3, 18), (3, 19), (3, 19)]
                l, rr = prof[min(k, len(prof) - 1)]
                l -= width; rr += width
                if r >= 1: l, rr = min(l, HEAD_L.get(r, 4)), max(rr, HEAD_R.get(r, 18))
        span[r] = (l, rr)
    for r, (l, rr) in span.items():
        row = ['.'] * 23
        row[l] = '#'; row[rr] = '#'
        for x in range(l + 1, rr):
            row[x] = tex(texture, x, r)
        if r == top_row:              # top edge
            for x in range(l, rr + 1): row[x] = '#'
            if top == 'spiky':
                for x in range(l + 1, rr, 2): row[x] = tex(texture, x, r)
            if top == 'bumpy':
                for x in range(l + 2, rr - 1, 3): row[x] = 'H'
        rows[r] = ''.join(row)
    # sides and hairline on head rows 4-6 (forehead / temples)
    def head_row(r, fill_cols):
        row = ['.'] * 23
        l, rr = HEAD_L[r], HEAD_R[r]
        for x in fill_cols:
            if l < x < rr: row[x] = fill_cols[x]
        return ''.join(row)
    side = 'H'
    if hairline == 'straight':
        rows[4] = head_row(4, {x: (side if x in (5, 6, 16, 17) else 'H') for x in range(5, 18)})
        rows[5] = head_row(5, {5: side, 17: side, 16: side})
    elif hairline == 'lineup':
        rows[4] = head_row(4, {x: (side if x in (5, 17) else 'H') for x in range(5, 18)})
        rows[5] = head_row(5, {5: side, 17: side})
    elif hairline == 'receding':
        rows[3] = rows[3][:8] + 'SSS' + rows[3][11:] if raise_ == 0 else rows[3]
        rows[4] = head_row(4, {5: side, 6: 'H', 15: 'H', 16: side, 17: side})
        rows[5] = head_row(5, {5: side, 17: side})
    elif hairline == 'fringe':
        rows[4] = head_row(4, {x: tex(texture, x, 4) for x in range(5, 18)})
        rows[5] = head_row(5, {x: ('H' if x % 2 == 1 or x in (5, 17) else '.') for x in range(5, 18)})
    elif hairline == 'curtains':     # middle part, falling to both sides
        rows[3] = rows[3][:10] + 'sS' + rows[3][12:]
        rows[4] = head_row(4, {**{x: 'H' for x in range(5, 10)}, **{x: 'H' for x in range(12, 18)}, 10: 'S', 11: 'S'})
        rows[5] = head_row(5, {5: 'H', 6: 'H', 7: 'H', 15: 'H', 16: 'H', 17: 'H'})
        rows[6] = head_row(6, {5: 'H', 6: 'H', 16: 'H', 17: 'H'})
    return rows

def add_bun(rows):
    rows = dict(rows)
    for r, s in {-4: ".........####.........", -3: "........#HhHH#........", -2: "........#HHHk#........"}.items():
        rows[r] = s.ljust(23, '.')
    return rows

def add_back_hair(rows, top=7, bottom=10):   # mullet: hair showing behind the ears
    rows = dict(rows)
    for r in range(top, bottom + 1):
        row = list(rows.get(r, '.' * 23))
        row[2], row[3] = '#', 'H'
        row[19], row[20] = 'H', '#'
        rows[r] = ''.join(row)
    end = list('.' * 23); end[2] = end[3] = end[19] = end[20] = '#'; rows[bottom + 1] = ''.join(end)
    return rows

def frohawk():
    rows = build(raise_=0, hairline='lineup', texture='curls')
    strip = {-3: "........######........", -2: ".......#HhHHhH#.......", -1: ".......#HHhHHH#.......", 0: ".......#hHHHhH#.......",
             1: "......##HhHHhH##......"}
    for r, s in strip.items(): rows[r] = s.ljust(23, '.')
    return rows

def swept_side():   # side part on the left, hair swept up and over to the right
    rows = build(1, 'straight', 'swept')
    rows[-2] = ".........#####.........".ljust(23, '.')
    rows[-1] = "......###hHHHH##......."
    rows[0] = "......#sHhHHhHHH#......"
    rows[1] = ".....#HsHHHhHHHHH#....."
    rows[2] = "....#HHsHHHHhHHHHH#...."
    return rows

STYLES = {
    'buzz':          build(0, 'straight', 'plain'),
    'waves':         build(0, 'lineup', 'waves'),
    'buzz_lineup':   build(0, 'lineup', 'plain'),
    'buzz_receding': build(0, 'receding', 'plain'),
    'crop':          build(1, 'straight', 'plain'),
    'crop_lineup':   build(1, 'lineup', 'plain'),
    'crop_fringe':   build(1, 'fringe', 'straight'),
    'textured_crop': build(1, 'lineup', 'twists', top='spiky'),
    'curly_short':   build(1, 'lineup', 'curls', top='bumpy'),
    'sponge':        build(2, 'lineup', 'twists', top='bumpy'),
    'curly_top':     build(2, 'lineup', 'curls', top='bumpy'),
    'curls_forward': build(2, 'fringe', 'curls', top='bumpy'),
    'high_top':      build(3, 'lineup', 'plain', top='flat'),
    'frohawk':       frohawk(),
    'man_bun':       add_bun(build(0, 'straight', 'swept')),
    'middle_part':   build(1, 'curtains', 'straight'),
    'mullet':        add_back_hair(build(1, 'fringe', 'straight')),
    'swept_side':    swept_side(),
    'cornrows_flat': build(0, 'lineup', 'cornrow'),
}
