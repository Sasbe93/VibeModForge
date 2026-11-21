"""Reusable BW ranked-map building blocks for 3-player axis layouts and catalogue tricks.

Layout pattern "mirrorx + axis player": BW ramp doodads only face south, so a 120-degree rotation is not
possible. Use SYM='mirrorx' with P1 west, P2 east (mirror image) and P3 on the vertical axis (self-symmetric
bases, ramp centred on the axis). Every trick is placed either on the axis or as a mirror pair, so the
symmetric_blockers check stays clean.

All trick units are neutral (owner 11). Unit ids follow tools/ranked/bw/rankedlib.py / data/bw/bw_unit_ids.json.
See catalogues/bw_features/BW_Ranked_Features.md for how each trick works and which ones are verified in-game.
"""
import struct
from rankedlib import MINERAL, GEYSER, STARTLOC
import sclib, ramp2

NEUTRAL = 11
EGG, EGG_ALT = 36, 97
ASSIMILATOR, TEMPLE, CREEP_COLONY, SUNKEN_COLONY = 157, 174, 143, 146
# jungle 8x5 ramp doodads and their mirror counterparts (left-facing <-> right-facing)
JUNGLE_RAMP_MIRROR = {281: 302, 302: 281, 272: 279, 279: 272, 313: 334, 334: 313,
                      345: 366, 366: 345, 304: 311, 311: 304, 336: 343, 343: 336}

def lr_base(hx, hy, gas='n', start=False, amount=1500):
    """Self-symmetric base for an axis player: 4+4 minerals left/right of the hall, geyser north ('n') or south."""
    o = []
    for dx, dy in ((-5, -1), (-6, 0), (-7, 1), (-6, 2)):
        o += [(MINERAL, hx + dx, hy + dy, amount), (MINERAL, 2 * hx + 4 - (hx + dx) - 2, hy + dy, amount)]
    o.append((GEYSER, hx, hy + (-5 if gas == 'n' else 6), 5000))
    if start: o.append((STARTLOC, hx, hy, 0))
    return o

def ud_base(hx, hy, start=False, amount=1500):
    """Side base with the same resource count as lr_base: 4+4 minerals north/south of the hall, geyser west."""
    o = []
    for dx, dy in ((-2, -4), (0, -5), (2, -4), (4, -5)):
        o += [(MINERAL, hx + dx, hy + dy, amount), (MINERAL, hx + dx, 2 * hy + 3 - (hy + dy) - 1, amount)]
    o.append((GEYSER, hx - 7, hy, 5000))
    if start: o.append((STARTLOC, hx, hy, 0))
    return o

def mirrored_ramp_pair(m, box, mirror=JUNGLE_RAMP_MIRROR, any_id=True, maxscore=11, peak=30, shift=-1):
    """Place a ramp in box (x0,y0,x1,y1) on the west side and its mirror ramp at the exact mirror x.
    Returns (id,x,y,id2,x2,y2) or None. Set any_id=False to force the mirrored doodad id."""
    W = m.W; ids = list(mirror)
    for sc, did, x, y, w, h in sorted(ramp2.valid(m, ids, box, maxscore=maxscore, peak=peak)):
        mx = W - x - w + shift
        R = ramp2.valid(m, ids if any_id else [mirror[did]], (mx, y, mx + 1, y + 1), maxscore=maxscore, peak=peak)
        if R:
            ramp2.place_ramp(m, [did], None, maxscore=99, peak=999, exact=(x, y))
            ramp2.place_ramp(m, [R[0][1]], None, maxscore=99, peak=999, exact=(R[0][2], R[0][3]))
            return (did, x, y, R[0][1], R[0][2], R[0][3])
    return None

def axis_ramp(m, x, y0, y1, ids, maxscore=11, peak=30):
    """Single ramp centred on the mirror axis (axis player main)."""
    c = sorted(ramp2.valid(m, ids, (x, y0, x + 1, y1), maxscore=maxscore, peak=peak))
    return c and ramp2.place_ramp(m, [c[0][1]], None, maxscore=99, peak=999, exact=(c[0][2], c[0][3]))

def walkable(m):
    """Return walk(x,y) for tiles after m.build_terrain()."""
    _cat, cv5 = sclib.doodad_catalog_all(m.ts); W = m.W
    def walk(x, y):
        g = struct.unpack_from('<H', m.mtxm, (y * W + x) * 2)[0] >> 4
        return g * 52 + 52 <= len(cv5) and g < 1024 and not struct.unpack_from('<H', cv5, g * 52 + 2)[0] & 4
    return walk

def backdoor_lane(walk, x_cols, y0, y1):
    """Backdoor lane: 0-value mineral columns along a lane (mine them out to open it). A 2-tile pocket between two
    columns doubles as a sliding niche."""
    return [(MINERAL, x, y, 0) for y in range(y0, y1) for x in x_cols if walk(x, y) and walk(x + 1, y)]

def assimilator_egg_pass(xc, y, gap=2, walk_minerals=16, walk_dist=6):
    """Axis pass: two value-0 geysers with neutral Assimilators either side of a gap (destroying one widens the
    choke), the gap plugged with neutral Zerg eggs (blocked until killed), and low-value minerals north and south
    as mineral-walk targets (workers gathering a visible mineral pass through the eggs = worker-only path)."""
    # xc = first gap tile; geysers are 4 tiles wide (left one ends at xc-1, right one starts at xc+gap)
    xl, xr = xc - 4, xc + gap
    o = [(GEYSER, xl, y, 0), (ASSIMILATOR, xl, y, 0), (GEYSER, xr, y, 0), (ASSIMILATOR, xr, y, 0)]
    o += [(EGG, x, yy, 0) for x in range(xc, xc + gap) for yy in (y, y + 1)]
    o += [(MINERAL, xc, y - walk_dist, walk_minerals), (MINERAL, xc, y + walk_dist + 1, walk_minerals)]
    return o

def temple_stack(x, y, n=3, W=None):
    """n stacked neutral Protoss Temples closing a gap (and the mirror stack if W is given)."""
    o = [(TEMPLE, x, y, 0)] * n
    if W: o += [(TEMPLE, W - x - 7, y, 0)] * n
    return o

def neutral_colonies(sunken_xy, creep_xy, W):
    """Neutral Sunken pair (mirror) plus one Creep Colony on the axis, as landmarks. Untested in-game."""
    sx, sy = sunken_xy
    return [(SUNKEN_COLONY, sx, sy, 0), (SUNKEN_COLONY, W - sx - 2, sy, 0), (CREEP_COLONY, creep_xy[0], creep_xy[1], 0)]

def place_tricks(m, units):
    for uid, x, y, res in units: m.unit(uid, x, y, NEUTRAL, res)
