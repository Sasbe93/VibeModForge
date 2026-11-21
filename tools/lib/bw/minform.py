"""minform: Blizzard-style mineral formations for SC:BW town halls (t1009).

Measured on 12 pro ladder maps (38 main/natural halls) and the 38 'Empire Wars' campaign maps (174 halls), see
docs/bw-campaign-design.md 'Mineral lines':
  - the nearest field is always 3 empty tiles from the 4x3 hall (columns: 3 tiles left/right; rows: 3 tiles above/below),
    the back fields 4, a curled end may come one tile closer where it sits diagonally (Chebyshev gap stays 3)
  - columns (line left/right of the hall) stagger one tile in x, one field per tile row
  - rows (line above/below) are TWO rows deep: fields are 2x1 tiles, so a back row of touching fields and a front row
    with 2-tile gaps between its fields (workers reach the back row through the gaps)
  - corner lines (L) wrap around a hall corner: a short column plus a short row
  - never more than 3 fields flush in one straight line (pro maps: 2, except map-edge lines)
  - geyser 3 tiles from the hall on a free side (column lines: above/below; row lines: left/right)
  - campaign maps mix shapes between bases (23 of 27 maps with several halls); pro ladder maps mostly use columns.

All offsets are tiles relative to the hall's top-left tile (hall = x 0..3, y 0..2). A field is (x, y) = its left tile
(it covers x, x+1); a geyser is its top-left tile (covers 4x2).
"""
import random

FACES = ('W', 'E', 'N', 'S', 'NW', 'NE', 'SW', 'SE')
SIDE_ALIAS = {'left': 'W', 'right': 'E', 'up': 'N', 'down': 'S', 'upleft': 'NW', 'upright': 'NE', 'downleft': 'SW', 'downright': 'SE'}

# ---- canonical templates: column on the W side (geyser N), row on the N side (geyser E), corner NW ----
# column: rows -2..6; depth 0 = front (x -5, gap 3), 1 = back (x -6, gap 4), 'c' = curled end (x -4, only rows <= -4 or >= 6)
_COLX = {0: -5, 1: -6, 'c': -4}
_COLUMN = {
    'blizzard': [0, 1, 0, 1, 0, 1, 0, 0, 'c'],      # Fighting Spirit / Circuit Breakers main
    'pairs':    [1, 0, 0, 1, 1, 0, 1, 0, 'c'],
    'bulge':    [0, 0, 1, 0, 1, 1, 0, 0, 'c'],
}
_ROW = {   # (x, y) along the line left -> right; back row y -5, front row y -4, curl y -3
    'blizzard': [(-5, -3), (-3, -4), (-2, -5), (0, -5), (1, -4), (2, -5), (4, -4), (7, -5), (7, -3)],   # like Fighting Spirit / Colorless Fate
    'zigzag':   [(-5, -3), (-4, -5), (-2, -4), (0, -5), (2, -4), (4, -5), (6, -4), (7, -3)],
}
_CORNER = {   # along the line: column bottom -> elbow -> row end
    'long_column': [(-5, 3), (-6, 2), (-5, 1), (-6, 0), (-5, -1), (-6, -2), (-5, -3), (-3, -4), (-2, -5), (0, -4), (2, -5)],
    'long_row':    [(-5, 1), (-6, 0), (-5, -1), (-6, -2), (-5, -3), (-3, -4), (-2, -5), (0, -5), (1, -4), (3, -5), (4, -4)],
}
_GEY = {'column': [(0, -5), (-1, -5), (1, -5), (-2, -5), (-3, -5), (0, -6), (-1, -6)],
        'row': [(7, 0), (7, 1), (8, 0), (7, -1), (8, 1)], 'corner': [(0, 6), (7, 0), (1, 6), (7, 1), (-1, 6), (8, 0)]}

def _column(variant, n):
    rows = list(range(-2, 7)); d = _COLUMN[variant]
    f = [(_COLX[k], y) for k, y in zip(d, rows)]
    if n > 9: f = [(-5, -3)] + f            # 10th field above the line (still gap 3)
    return f[-n:] if n <= len(f) else None
def _row(variant, n):
    f = _ROW[variant]
    if n > len(f): return None
    drop = len(f) - n; return f[drop//2: len(f) - (drop - drop//2)] if drop else list(f)
def _corner(variant, n):
    f = _CORNER[variant]
    if n > len(f): return None
    drop = len(f) - n; a = (drop+1)//2 if variant == 'long_column' else drop//2
    return f[a: len(f) - (drop - a)]

def _mx_f(p): return (2 - p[0], p[1])                                              # field 2 wide: x -> 2-x
def _mx_g(p): return (-p[0], p[1])                                                # geyser 4 wide: x -> -x
def _my_f(p): return (p[0], 2 - p[1])                                              # field 1 tall: y -> 2-y
def _my_g(p): return (p[0], 1 - p[1])                                              # geyser 2 tall

def formation(form, face, n, variant):
    """(fields, geyser candidates) as offsets from the hall top-left, or None if the variant cannot hold n fields.
    form 'column' faces W/E, 'row' faces N/S, 'corner' faces NW/NE/SW/SE. Column/row variants ending in '/flip' put the
    geyser on the other end (column: below instead of above; row: left instead of right)."""
    flip = variant.endswith('/flip'); v = variant.split('/')[0]
    if form == 'column':
        f = _column(v, n); g = list(_GEY['column'])
        if f is None: return None
        if flip: f = [_my_f(p) for p in f]; g = [_my_g(p) for p in g]
        if face == 'E': f = [_mx_f(p) for p in f]; g = [_mx_g(p) for p in g]
        elif face != 'W': raise ValueError(f'column lines face W or E, not {face}')
    elif form == 'row':
        f = _row(v, n); g = list(_GEY['row'])
        if f is None: return None
        if flip: f = [_mx_f(p) for p in f]; g = [_mx_g(p) for p in g]
        if face == 'S': f = [_my_f(p) for p in f]; g = [_my_g(p) for p in g]
        elif face != 'N': raise ValueError(f'row lines face N or S, not {face}')
    elif form == 'corner':
        f = _corner(v, n); g = list(_GEY['corner'])
        if f is None: return None
        if face not in ('NW', 'NE', 'SW', 'SE'): raise ValueError(f'corner lines face NW/NE/SW/SE, not {face}')
        if 'S' in face: f = [_my_f(p) for p in f]; g = [_my_g(p) for p in g]
        if 'E' in face: f = [_mx_f(p) for p in f]; g = [_mx_g(p) for p in g]
    else: raise ValueError(f'unknown formation {form}')
    return f, g

def variants(form):
    if form == 'column': return [k+s for k in _COLUMN for s in ('', '/flip')]
    if form == 'row': return [k+s for k in _ROW for s in ('', '/flip')]
    return list(_CORNER)

def form_for_face(face):
    face = SIDE_ALIAS.get(face, face)
    return 'column' if face in ('W', 'E') else 'row' if face in ('N', 'S') else 'corner'

# ---- geometry checks (shared with the delivery check) ----
def gap_field(p):
    """empty tiles between the hall (0..3, 0..2) and a field at offset p (Chebyshev)"""
    x, y = p; dx = max(x - 4, -(x + 2), 0); dy = max(y - 3, -(y + 1), 0)
    return max(dx, dy)
def gap_geyser(p):
    x, y = p; dx = max(x - 4, -(x + 4), 0); dy = max(y - 3, -(y + 2), 0); return max(dx, dy)
def straight_run(fields):
    """longest chain flush in one straight line: same x in consecutive rows, or same y at x, x+2, x+4 ..."""
    T = set(map(tuple, fields)); best = 1 if T else 0
    for (x, y) in T:
        k = 1
        while (x, y+k) in T: k += 1
        j = 1
        while (x+2*j, y) in T: j += 1
        best = max(best, k, j)
    return best
def blocked_sight(fields, geyser=None):
    """fields whose straight line (centre -> nearest hall point) crosses another field or the geyser (same test as
    check_bw_rules mineral_layout: rectangles shrunk by 2 px, 4 px steps)"""
    R = [(x*32+2, y*32+2, x*32+62, y*32+30) for x, y in fields]
    if geyser: R.append((geyser[0]*32+2, geyser[1]*32+2, geyser[0]*32+126, geyser[1]*32+62))
    out = []
    for i, (x, y) in enumerate(fields):
        ux, uy = x*32+32, y*32+16; px = min(max(ux, 0), 128); py = min(max(uy, 0), 96)
        L = max(1, int(((px-ux)**2+(py-uy)**2)**0.5/4))
        for j, (a, b, c, d) in enumerate(R):
            if j != i and any(a < ux+(px-ux)*k/L < c and b < uy+(py-uy)*k/L < d for k in range(L+1)): out.append((x, y)); break
    return out
def tiles_field(p): return {(p[0], p[1]), (p[0]+1, p[1])}
def tiles_geyser(p): return {(p[0]+i, p[1]+j) for i in range(4) for j in range(2)}
def problems(fields, geyser=None):
    """geometry rules every formation must meet (empty list = fine)"""
    out = []; seen = {(x, y) for x in range(4) for y in range(3)}
    for p in fields:
        t = tiles_field(p)
        if t & seen: out.append(f'field {p} overlaps')
        seen |= t
    gs = [gap_field(p) for p in fields]
    if gs and min(gs) != 3: out.append(f'nearest field gap {min(gs)} (Blizzard: 3)')
    if gs and max(gs) > 5: out.append(f'field gap {max(gs)} > 5')
    if straight_run(fields) > 3: out.append(f'{straight_run(fields)} fields flush in a straight line (max 3)')
    bs = blocked_sight(fields, geyser)
    if bs: out.append(f'fields {bs} have no free line to the hall')
    if geyser is not None:
        if tiles_geyser(geyser) & seen: out.append(f'geyser {geyser} overlaps')
        if not 3 <= gap_geyser(geyser) <= 5: out.append(f'geyser gap {gap_geyser(geyser)} (3..5)')
    return out

def staggered_count(form, fields):
    """fields off the line's main depth (column: x, row: y); corners count both parts"""
    from collections import Counter
    if form == 'column': off = [p[0] for p in fields]
    elif form == 'row': off = [p[1] for p in fields]
    else:
        col = [p for p in fields if p[1] >= -2 and p[1] <= 4] ; row = [p for p in fields if p not in col]
        return staggered_count('column', col) + staggered_count('row', row) if col and row else 0
    return len(off) - Counter(off).most_common(1)[0][1]
def back_dir(p, kind='field'):
    """unit step pointing away from the hall for a field/geyser at offset p (dominant axis; diagonal for corner spots)"""
    cx = p[0] + (1 if kind == 'field' else 2); cy = p[1] + (0.5 if kind == 'field' else 1)
    dx = cx - 2; dy = cy - 1.5
    sx = (dx > 0) - (dx < 0); sy = (dy > 0) - (dy < 0)
    if abs(dx) > 1.6 * abs(dy): return (sx, 0)
    if abs(dy) > 1.0 * abs(dx): return (0, sy)
    return (sx, sy)
def back_tiles(fields, geyser=None, depth=(1, 2, 3)):
    """tiles directly behind each field/geyser (away from the hall) at the given depths, outside the formation:
    paint these unwalkable (water, cliff, high ground) in the terrain step before placing the base"""
    occ = set().union(*[tiles_field(p) for p in fields]) | (tiles_geyser(geyser) if geyser else set())
    out = []
    items = [(p, 'field') for p in fields] + ([(geyser, 'geyser')] if geyser else [])
    for p, k in items:
        bx, by = back_dir(p, k); w = 2 if k == 'field' else 4; h = 1 if k == 'field' else 2
        for d in depth:
            for i in range(w):
                for j in range(h):
                    t = (p[0]+i+bx*d, p[1]+j+by*d)
                    if t not in occ and t not in out and not (0 <= t[0] < 4 and 0 <= t[1] < 3): out.append(t)
    return out

def candidates(side='auto', n=8, seed=0, used=()):
    """ordered (form, face, variant) candidates. side: one face / alias, a list of faces, or 'auto' (all 8).
    Shapes and faces already used in this map (`used`: list of (form, face, variant)) go last, so bases differ."""
    faces = FACES if side == 'auto' else [SIDE_ALIAS.get(s, s) for s in ([side] if isinstance(side, str) else side)]
    R = random.Random(seed); out = []
    for face in faces:
        form = form_for_face(face)
        for v in variants(form):
            if formation(form, face, n, v) is not None: out.append((form, face, v))
    R.shuffle(out)
    uf = [u[0] for u in used]; uv = {(u[0], u[2].split('/')[0]) for u in used}
    out.sort(key=lambda c: (uf.count(c[0]), (c[0], c[2].split('/')[0]) in uv))
    return out

def _selftest():
    for form in ('column', 'row', 'corner'):
        faces = {'column': ('W', 'E'), 'row': ('N', 'S'), 'corner': ('NW', 'NE', 'SW', 'SE')}[form]
        for face in faces:
            for v in variants(form):
                for n in range(6, 11):
                    r = formation(form, face, n, v)
                    if r is None: continue
                    f, g = r
                    ok = [q for q in g if not problems(f, q)]
                    assert len(f) == n and ok, (form, face, v, n, problems(f, g[0]))
_selftest()
