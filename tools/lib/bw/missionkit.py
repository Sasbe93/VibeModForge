"""missionkit: generic building blocks for StarCraft: Brood War campaign missions on top of sclib.

Used by tools/bw/example_mission.py and tools/bw/examples/ (docs/bw-example-missions.md). Everything here works for any
mission and any tileset; nothing is tied to a story. The examples show the STRUCTURE of a mission only: never copy their
mission design (objective, map layout, start setup, enemy, story, rewards).
  TerrainInfo     tile flags from the tileset (walkable, buildable, height level)
  Grid            placement grid: free, flat, buildable footprints with a walkable ring; unit spots on the main ground
  near()          deterministic spiral search for a building spot
  res_base()      Blizzard mineral formation (column / 2-deep row / corner L, minform.py), varied per base, blocker behind it
  mineral_plan()  pick the formation before the terrain is built; paint_back() paints water/cliff behind it
  scatter()       a loose group of ground units on free tiles
  free_loc()      a location on free walkable ground (reserved so nothing else is placed there)
  auto_ramps()    seam-aware ramp doodads from a plateau top down to low ground (normal size >= 8x5)
  dress()         doodad dressing on the battlefield, then removes every doodad the delivery checks call a hard seam
  Cast            speakers (TTS voice, colour, portrait), voiced lines, transmissions and the briefing
  CREEP_SRC, ZERG_HALLS, PROTOSS_FREE  unit id sets: creep sources, the Zerg hall morph chain, Protoss without power
  Town            buildings of one owner placed race-correctly (Zerg on creep, Protoss in pylon power, Terran anywhere)
  waves()         scripted attack waves at elapsed times, optionally gated on the producing building still standing
  auto_forbid()   doodad keep-out boxes around given boxes, placed units and locations
Needs the same files as sclib: the isomtool binary and the tileset files (external/README.md).
"""
import math, random, struct, os, sys
from collections import deque
import sclib
from sclib import (Map, TOOLS, TSNAMES, BUILDSIZE, MINERAL, GEYSER, STARTLOC, doodad_catalog_all, _megafeat,
                   _doodad_edge, DOODAD_EDGE_PEAK, place_doodads)

AIR = {42, 43, 44, 8, 12, 58, 70, 72, 9, 11, 60, 71, 84, 45, 47, 62}   # air units (never need ground spots)

class TerrainInfo:
    def __init__(s, m):
        s.m = m; s.cv5 = open(f'{TOOLS}/tileset/{TSNAMES[m.ts]}.cv5', 'rb').read()
    def flags(s, x, y):
        tid = struct.unpack_from('<H', s.m.mtxm, (y*s.m.W+x)*2)[0]
        f = struct.unpack_from('<H', s.cv5, (tid >> 4)*52+2)[0]
        if s.m.ts == 2 and f & 0x80 and not f & 0x01: f |= 0x0004       # installation substructure is unwalkable
        return f
    def walk(s, x, y): return 0 <= x < s.m.W and 0 <= y < s.m.H and not s.flags(x, y) & 4
    def lvl(s, x, y): return s.flags(x, y) & 0x600
    def buildable(s, x, y): return s.walk(x, y) and not s.flags(x, y) & 0x80

def components(W, H, walk):
    """8-connected ground components (diagonal steps only between two walkable orthogonal tiles)"""
    comp = [-1]*(W*H); n = 0
    for i in range(W*H):
        if not walk[i] or comp[i] >= 0: continue
        st = [i]; comp[i] = n
        while st:
            j = st.pop(); x, y = j % W, j//W
            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                X, Y = x+dx, y+dy
                if 0 <= X < W and 0 <= Y < H:
                    k = Y*W+X
                    if walk[k] and comp[k] < 0 and (dx == 0 or dy == 0 or (walk[y*W+X] and walk[Y*W+x])): comp[k] = n; st.append(k)
        n += 1
    return comp

class Grid:
    """Placement grid for one map state. Rebuild it (Grid(m)) after terrain or doodad changes."""
    def __init__(g, m):
        g.m = m; W, H = m.W, m.H; g.W, g.H = W, H
        cv5 = open(f'{TOOLS}/tileset/{TSNAMES[m.ts]}.cv5', 'rb').read(); cat = doodad_catalog_all(m.ts)[0]
        g.f = [[None]*W for _ in range(H)]
        for y in range(H):
            for x in range(W):
                gi = struct.unpack_from('<H', m.mtxm, (y*W+x)*2)[0] >> 4
                t, f = struct.unpack_from('<HH', cv5, gi*52)
                if m.ts == 2 and f & 0x80 and not f & 0x01: f |= 0x0004
                g.f[y][x] = (t, f)
        g.occ = set(); g.block = set()
        for d in getattr(m, 'dd2', []):
            did, px, py, _, _ = struct.unpack('<HHHBB', d); c = cat.get(did)
            if c:
                for yy in range(py//32-c['h']//2, py//32-c['h']//2+c['h']):
                    for xx in range(px//32-c['w']//2, px//32-c['w']//2+c['w']): g.block.add((xx, yy))
        for (x0, y0, x1, y1) in getattr(m, 'reserve', []):
            for yy in range(y0, y1):
                for xx in range(x0, x1): g.block.add((xx, yy))
        walk = [0 if g.f[i//W][i % W][1] & 4 else 1 for i in range(W*H)]
        g.comp = components(W, H, walk)
        for raw in m.units: g.add_raw(raw)
        st = [(px//32, py//32) for u, px, py, o in g.units() if u == STARTLOC and o == 0]
        g.main = g.comp[st[0][1]*W+st[0][0]] if st else -1
    def units(g):
        for raw in g.m.units:
            px, py, uid = struct.unpack_from('<HHH', raw, 4); yield uid, px, py, raw[16]
    def add_raw(g, raw):
        px, py, uid = struct.unpack_from('<HHH', raw, 4)
        if uid in BUILDSIZE:
            w, h = BUILDSIZE[uid]; x0, y0 = px//32-w//2, py//32-h//2
            for yy in range(y0, y0+h):
                for xx in range(x0, x0+w): g.occ.add((xx, yy))
            if uid == MINERAL:      # keep the mining lane free
                for yy in range(y0-2, y0+h+2):
                    for xx in range(x0-2, x0+w+2): g.block.add((xx, yy))
        elif uid not in AIR and uid != STARTLOC: g.occ.add((px//32, py//32))
    def ok(g, uid, x0, y0, hall=False):
        """flat, buildable, free footprint with a free ring (2 tiles for a town hall) touching the main ground"""
        w, h = BUILDSIZE[uid]; el = set(); W, H = g.W, g.H; ring = False
        for yy in range(y0, y0+h):
            for xx in range(x0, x0+w):
                if not (1 <= xx < W-1 and 1 <= yy < H-1): return False
                t, f = g.f[yy][xx]
                if f & 4 or f & 0x80 or t == 1 or (xx, yy) in g.occ or (xx, yy) in g.block: return False
                el.add(f & 0x600)
        if len(el) > 1: return False
        m2 = 2 if hall else 1
        for yy in range(y0-m2, y0+h+m2):
            for xx in range(x0-m2, x0+w+m2):
                if x0 <= xx < x0+w and y0 <= yy < y0+h: continue
                if not (0 <= xx < W and 0 <= yy < H) or (xx, yy) in g.occ: return False
                t, f = g.f[yy][xx]
                if hall and (f & 0x84 or t == 1 or (xx, yy) in g.block): return False
                if g.main < 0 or g.comp[yy*W+xx] == g.main: ring = True
        return ring
    def spot_unit(g, x, y):
        if not (0 <= x < g.W and 0 <= y < g.H): return False
        return not g.f[y][x][1] & 4 and (x, y) not in g.occ and (x, y) not in g.block and (g.main < 0 or g.comp[y*g.W+x] == g.main)
    def resok(g, uid, x0, y0):
        w, h = BUILDSIZE[uid]; el = set()
        for yy in range(y0, y0+h):
            for xx in range(x0, x0+w):
                if not (1 <= xx < g.W-1 and 1 <= yy < g.H-1): return False
                t, f = g.f[yy][xx]
                if f & 0x84 or t == 1 or (xx, yy) in g.occ: return False
                el.add(f & 0x600)
        return len(el) == 1

def near(g, uid, cx, cy, rmin=0, rmax=8, cond=lambda x, y: True, hall=False):
    """top-left tile of the first free spot on rings rmin..rmax around (cx,cy); deterministic, spread by angle"""
    w, h = BUILDSIZE[uid]
    for r in range(rmin, rmax+1):
        cand = [(cx+dx, cy+dy) for dx in range(-r, r+1) for dy in range(-r, r+1) if max(abs(dx), abs(dy)) == r]
        cand.sort(key=lambda p: (math.atan2(p[1]-cy, p[0]-cx)*7) % 1)
        for x, y in cand:
            x0, y0 = x-w//2, y-h//2
            if cond(x0, y0) and g.ok(uid, x0, y0, hall): return x0, y0
    return None

def put(m, g, uid, cx, cy, owner, rmin=0, rmax=8):
    sp = near(g, uid, cx, cy, rmin, rmax) or near(g, uid, cx, cy, rmin, rmax+6)
    if not sp: raise SystemExit(f'no room for unit {uid} near {cx},{cy}')
    m.unit(uid, *sp, owner); g.add_raw(m.units[-1]); return sp

def scatter(m, g, uid, n, cx, cy, owner, spread=2.5, seed=1):
    R = random.Random(seed*7919+uid*31+cx*13+cy); k = tries = 0; got = []
    while k < n and tries < 4000:
        tries += 1; x = int(round(cx+R.uniform(-spread, spread))); y = int(round(cy+R.uniform(-spread, spread)))
        if g.spot_unit(x, y) and all(abs(x-a)+abs(y-b) > 1 for a, b in got):
            m.unit(uid, x, y, owner); g.occ.add((x, y)); got.append((x, y)); k += 1
        if tries % 150 == 0: spread += 1
    assert k == n, f'scatter: only {k}/{n} of unit {uid} near {cx},{cy}'
    return got

def free_loc(m, g, name, x, y, size=3, rmax=10):
    """location of size x size tiles on free walkable main ground near (x,y); its tiles are reserved"""
    for r in range(rmax+1):
        for dx in range(-r, r+1):
            for dy in range(-r, r+1):
                if max(abs(dx), abs(dy)) != r: continue
                x0, y0 = x+dx, y+dy
                if all(g.spot_unit(xx, yy) for xx in range(x0, x0+size) for yy in range(y0, y0+size)):
                    m.loc(name, x0, y0, x0+size, y0+size)
                    for yy in range(y0, y0+size):
                        for xx in range(x0, x0+size): g.block.add((xx, yy))
                    return x0, y0
    raise SystemExit('no free location spot for ' + name)

def _abs(hx, hy, p): return (hx+p[0], hy+p[1])

def mineral_plan(hx, hy, side='auto', n=8, form=None, variant=None, seed=None, used=()):
    """choose a Blizzard mineral formation (minform) for a hall at top-left (hx,hy) BEFORE the terrain is built.
    Returns dict(form, face, variant, fields, geyser_cands, back) in absolute tiles; paint `back` unwalkable
    (paint_back) so the formation has water/cliff behind it, then call res_base(..., plan=plan)."""
    import minform as F
    c = F.candidates(side, n, seed if seed is not None else hx*1000+hy+len(used), used)
    c = [x for x in c if (form is None or x[0] == form) and (variant is None or x[2] == variant)]
    assert c, f'no {form or ""} {variant or ""} formation with {n} fields on side {side}'
    fo, fa, va = c[0]; f, g = F.formation(fo, fa, n, va)
    gy = next(q for q in g if not F.problems(f, q))
    return dict(form=fo, face=fa, variant=va, hall=(hx, hy), fields=[_abs(hx, hy, p) for p in f],
                geyser_cands=[_abs(hx, hy, q) for q in g], back=[_abs(hx, hy, t) for t in F.back_tiles(f, gy)])

def paint_back(m, plan, brush, depth=(8.0, 5.0), r=1.4, noise=0.3, geyser=True):
    """paint the blocker behind a planned mineral line (and its first legal geyser slot): blobs `depth` tiles behind
    each field centre, so the ISOM shore/cliff transition ends right behind the fields. depth = (tiles behind a field
    that faces left/right, tiles behind one that faces up/down): ISOM transitions are wider horizontally (measured on
    Badlands water: 8 / 6 put the shore 0-1 tiles behind the back fields). Call before m.build_terrain()."""
    import minform as F
    hx, hy = plan['hall']; pts = []
    items = [((x-hx, y-hy), 'field') for x, y in plan['fields']]
    if geyser and plan['geyser_cands']:
        gx, gy = plan['geyser_cands'][0]; items.append(((gx-hx, gy-hy), 'geyser'))
    for p, k in items:
        bx, by = F.back_dir(p, k); cx = hx+p[0]+(1 if k == 'field' else 2); cy = hy+p[1]+(0.5 if k == 'field' else 1)
        k_ = 0.75 if bx and by else 1.0; ex, ey = (2.5, 0.0) if k == "geyser" else (0, 0)     # geyser is 4x2
        q = (round(cx+bx*(depth[0]+ex)*k_, 1), round(cy+by*(depth[1]+ey)*k_, 1))
        if q not in pts: pts.append(q)
    for x, y in pts: m.blob(x, y, r, brush, noise)
    return pts

def res_base(m, g, ti, hx, hy, side, n, amounts, gas, owner=None, hall=None, geyser=True, form=None, variant=None,
             plan=None, reach=3):
    """Blizzard mineral formation (tools/lib/bw/minform.py) for a 4x3 hall at top-left (hx,hy).
    side: 'left'/'right' (column), 'up'/'down' (row, two rows deep), 'upleft'/'upright'/'downleft'/'downright' (corner L),
    a list of those, or 'auto'. form/variant pin a shape; plan = mineral_plan(...) result used for the terrain.
    Rules (measured on pro ladder and Empire Wars campaign maps): nearest field 3 empty tiles from the hall, back
    fields 4, real 2-deep stagger, never more than 3 fields flush in a straight line, geyser 3-5 tiles on a free side.
    Every field and the geyser need unwalkable ground (water, cliff, map edge) or another field within `reach` tiles
    straight behind them (resource backs, predelivery resback). Shapes already used in this map are tried last, so the
    bases of one map differ (m._minforms). Build the blocker behind the line into the terrain first (paint_back)."""
    import minform as F
    hl = ti.lvl(hx+1, hy+1)
    assert g.ok(sclib.CC, hx, hy, hall=True), f'hall spot blocked at {hx},{hy}'
    used = getattr(m, '_minforms', [])
    if plan: cands = [(plan['form'], plan['face'], plan['variant'])]
    else:
        cands = F.candidates(side, n, hx*1000+hy+len(used), used)
        cands = [c for c in cands if (form is None or c[0] == form) and (variant is None or c[2] == variant)]
    def tile_ok(x, y): return ti.buildable(x, y) and ti.lvl(x, y) == hl and (x, y) not in g.occ and (x, y) not in g.block
    def blocked(x, y, own): return not ti.walk(x, y) or (x, y) in own
    def backed(p, kind, own):
        # like predelivery resback: straight away from the hall, or along the dominant axis
        w = 2 if kind == 'field' else 4; h = 1 if kind == 'field' else 2
        cx = p[0]+w/2; cy = p[1]+h/2; vx = cx-2; vy = cy-1.5; L = math.hypot(vx, vy) or 1
        for bx, by in (F.back_dir(p, kind), (vx/L, vy/L)):
            ex = abs(w/2/bx) if bx else 1e9; ey = abs(h/2/by) if by else 1e9; e = min(ex, ey)
            for k in range(1, reach*4+1):
                s_ = e+k/4
                for o in (-0.35, 0, 0.35):
                    x = hx+cx+bx*s_-by*o*w; y = hy+cy+by*s_+bx*o*h
                    if blocked(int(math.floor(x)), int(math.floor(y)), own): return True
        return False
    import itertools
    best = None; why = []
    def field_ok(p, own): return all(tile_ok(hx+p[0]+i, hy+p[1]) for i in (0, 1)) and backed(p, 'field', own)
    for fo, fa, va in cands:
        f0, gs = F.formation(fo, fa, n, va)
        own0 = set().union(*[{(hx+x, hy+y), (hx+x+1, hy+y)} for x, y in f0])
        bad = [i for i, p in enumerate(f0) if not field_ok(p, own0)]
        if len(bad) > 4: why.append(f'{fo}/{fa}/{va}: {len(bad)} fields off base ground or without a blocker behind'); continue
        # flexible template: a field that does not fit may step one tile toward / away from its blocker, as long as the
        # line stays a Blizzard line (nearest gap 3, max 3 flush, free sight, n/3 staggered)
        alts = []
        for i in bad:
            bx, by = F.back_dir(f0[i]); p = f0[i]
            alts.append([(p[0]+bx, p[1]+by), (p[0]-bx, p[1]-by), (p[0]+2*bx, p[1]+2*by)])
        found = None
        for combo in itertools.product(*alts) if bad else [()]:
            f = list(f0)
            for i, q in zip(bad, combo): f[i] = q
            own = set().union(*[{(hx+x, hy+y), (hx+x+1, hy+y)} for x, y in f])
            if any(not field_ok(f[i], own) for i in bad): continue
            if F.problems(f) or F.staggered_count(fo, f) < math.ceil(n/3): continue
            gpos = None
            if geyser:
                okg = [q for q in gs if not F.problems(f, q) and g.resok(GEYSER, hx+q[0], hy+q[1])
                       and not any((hx+q[0]+i, hy+q[1]+j) in g.block for i in range(4) for j in range(2))]
                gpos = next((q for q in okg if backed(q, 'geyser', own)), None)
                if gpos is None: continue
            found = (f, gpos); break
        if not found:
            why.append(f'{fo}/{fa}/{va}: ' + (f'{len(bad)} field(s) do not fit even when moved one tile' if bad else 'no legal geyser slot with a blocker behind'))
            continue
        best = (fo, fa, va) + found; break
    assert best, f'no mineral formation fits hall {hx},{hy} (side {side}): ' + '; '.join(why[:6]) + \
        ' -> paint the blocker behind the line first (mineral_plan + paint_back) or move the hall'
    fo, fa, va, f, gpos = best
    m._minforms = used + [(fo, fa, va)]
    for i, (x, y) in enumerate(f): m.unit(MINERAL, hx+x, hy+y, 11, amounts[i % len(amounts)])
    if gpos: gpos = (hx+gpos[0], hy+gpos[1]); m.unit(GEYSER, gpos[0], gpos[1], 11, gas)
    m.reserve = getattr(m, 'reserve', [])+[(hx-1, hy-1, hx+5, hy+4)]
    for raw in m.units[-(n+(1 if gpos else 0)):]: g.add_raw(raw)
    for yy in range(hy-1, hy+4):
        for xx in range(hx-1, hx+5): g.block.add((xx, yy))
    if hall:
        for yy in range(hy-1, hy+4):
            for xx in range(hx-1, hx+5): g.block.discard((xx, yy))
        m.unit(hall, hx, hy, owner); g.add_raw(m.units[-1])
    print(f'res_base hall {hx},{hy}: {fo} {fa} {va}, {n} fields, geyser {gpos}')
    return gpos

# ---------- ramps ----------
RAMP_SN = {0: {1148}, 1: {1167}, 2: set(), 3: {1176, 1178}, 4: {1148}, 5: {1148, 1198}, 6: {1148}, 7: {1148, 1225}}   # cv5 group-name ids of ramp doodads
def ramp_ids(ts, minw=8, minh=5):
    cat, _ = doodad_catalog_all(ts)
    return [d for d, c in cat.items() if c['s'] in RAMP_SN[ts] and c['w'] >= minw and c['h'] >= minh]

def place_ramp(m, dids, spot, radius=6, maxscore=8.0, peak=DOODAD_EDGE_PEAK-1.0, tries=400, top=None):
    """seam-aware ramp: candidates best-first by border match; the first one whose border passes the hard-seam limit and
    that really links the plateau top (`top`, set of tile indices) to low ground is placed. Returns (did,x,y,score,peak)."""
    import numpy as np
    cat, cv5 = doodad_catalog_all(m.ts); F = _megafeat(m.ts)
    mt = list(struct.unpack(f'<{m.W*m.H}H', m.mtxm))
    M = lambda tid: struct.unpack_from('<H', cv5, (tid >> 4)*52+20+(tid & 15)*2)[0] if (tid >> 4)*52+52 <= len(cv5) else 0
    MF = F[np.array([M(v) for v in mt])].reshape(m.H, m.W, 16, 3)
    if not hasattr(m, 'dd2'): m.dd2 = []
    used = getattr(m, 'ramp_cells', set()); sx, sy = spot; cand = []
    for did in dids:
        c = cat[did]; w, h = c['w'], c['h']
        cells = [(r, col, struct.unpack_from('<H', cv5, (c['g']+r)*52+20+col*2)[0]) for r in range(h) for col in range(w)]
        ring = [(r, col, F[mg]) for r, col, mg in cells if mg and (r in (0, h-1) or col in (0, w-1))]
        rr = np.array([r for r, _, _ in ring]); cc = np.array([c_ for _, c_, _ in ring]); fe = np.stack([f for _, _, f in ring])
        for y in range(max(1, sy-radius), min(m.H-h-1, sy+radius)):
            for x in range(max(1, sx-radius), min(m.W-w-1, sx+radius)):
                if any((x+a, y+b) in used for a in range(w) for b in range(h)): continue
                sc = float(np.abs(MF[y+rr, x+cc]-fe).mean())
                if sc <= maxscore: cand.append((sc, did, x, y))
    cand.sort()
    fl = lambda tid: struct.unpack_from('<H', cv5, (tid >> 4)*52+2)[0]
    for sc, did, x, y in cand[:tries]:
        c = cat[did]; w, h = c['w'], c['h']
        nw = {(y+r)*m.W+x+col: (c['g']+r)*16+col for r in range(h) for col in range(w) if struct.unpack_from('<H', cv5, (c['g']+r)*52+20+col*2)[0]}
        _doodad_edge(m.ts, cv5, mt, m.W, m.H, nw, x, y, w, h)
        if _doodad_edge.peak > peak: continue
        if top is not None:
            wk = {k for k, v in nw.items() if not fl(v) & 4}
            def nb(k):
                cx, cy = k % m.W, k//m.W
                for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx, ny = cx+dx, cy+dy
                    if 0 <= nx < m.W and 0 <= ny < m.H: yield ny*m.W+nx
            seed = [k for k in wk if any(n not in nw and n in top for n in nb(k))]
            seen = set(seed); st = list(seed)
            while st:
                k = st.pop()
                for n in nb(k):
                    if n in wk and n not in seen: seen.add(n); st.append(n)
            if not any(n not in nw and n not in top and not fl(mt[n]) & 4 for k in seen for n in nb(k)): continue
        for k, v in nw.items(): mt[k] = v
        for a in range(-2, w+2):
            for b in range(-2, h+2): used.add((x+a, y+b))
        m.dd2.append(struct.pack('<HHHBB', did, x*32+w*16, y*32+h*16, 12, 0)); m.mtxm = struct.pack(f'<{m.W*m.H}H', *mt)
        m.ramp_cells = used
        return (did, x, y, round(sc, 2), round(_doodad_edge.peak, 1))
    return None

def auto_ramps(m, ti, cx, cy, r, angles, need=2, max_top=2500):
    """ramps from the plateau centred at (cx,cy) (radius ~r) toward the given angles (degrees, preferred first)"""
    top = {cy*m.W+cx}; q = deque([(cx, cy)])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = x+dx, y+dy
            if 0 <= nx < m.W and 0 <= ny < m.H and ny*m.W+nx not in top and ti.walk(nx, ny): top.add(ny*m.W+nx); q.append((nx, ny))
    assert len(top) < max_top, 'plateau top is not isolated before ramps (it already connects to low ground)'
    ids = ramp_ids(m.ts); out = []
    for a in list(angles)+[a for a in range(0, 360, 10) if a not in angles]:
        if len(out) >= need: break
        ex = None
        for d in range(2, int(r*2.2)):
            x = int(round(cx+d*math.cos(math.radians(a)))); y = int(round(cy+d*math.sin(math.radians(a))))
            if not (3 <= x < m.W-3 and 3 <= y < m.H-3): break
            if ti.lvl(x, y) == 0 and ti.walk(x, y): ex, ey = x, y; break
        if ex is None or any(math.hypot(ex-a2, ey-b2) < 8 for a2, b2, _ in out): continue
        got = place_ramp(m, ids, (ex-4, ey-3), radius=8, maxscore=16.0, tries=20000, top=top, peak=15.0)
        if got: out.append((ex, ey, got))
    return out

# ---------- doodad dressing ----------
def dress(m, low, high=(), forbid=(), counts=(120, 10, 100), seed=70):
    """battlefield doodads: large ones on low ground, a few on high ground, then small fillers; afterwards every doodad that
    predelivery checks 9/26 would call a hard seam is removed again and the ground under it restored."""
    sys.path.insert(0, os.path.join(TOOLS, '..', '..', 'bw')); import seams
    old_peak = sclib.DOODAD_EDGE_PEAK; sclib.DOODAD_EDGE_PEAK = 12.0      # stricter than the check (15)
    MT0 = m.mtxm; DD0 = list(getattr(m, 'dd2', []))
    nd = place_doodads(m, counts[0], list(low), forbid=forbid, seed=seed)
    if high: nd += place_doodads(m, counts[1], list(high), forbid=forbid, high=True, seed=seed+1)
    nd += place_doodads(m, counts[2], list(low), forbid=forbid, seed=seed+2, maxw=2)
    sclib.DOODAD_EDGE_PEAK = old_peak
    new = set(m.dd2)-set(DD0)
    cat, _ = doodad_catalog_all(m.ts); mt = list(struct.unpack(f'<{m.W*m.H}H', m.mtxm)); m0 = struct.unpack(f'<{m.W*m.H}H', MT0)
    bad = set()
    for _ in range(5):
        sec = {'DIM ': struct.pack('<HH', m.W, m.H), 'ERA ': struct.pack('<H', m.ts), 'MTXM': m.mtxm, 'DD2 ': b''.join(m.dd2)}
        bad = {xy for _d, xy, *r in seams.doodad_seams(sec)} | {xy for _d, xy, _p in seams.doodad_peaks(sec, 15.0)}
        if not bad: break
        keep = []
        for e in m.dd2:
            did, px, py = struct.unpack_from('<HHH', e, 0); c = cat[did]; x0, y0 = px//32-c['w']//2, py//32-c['h']//2
            if (x0, y0) in bad and e in new:
                for yy in range(y0, y0+c['h']):
                    for xx in range(x0, x0+c['w']): mt[yy*m.W+xx] = m0[yy*m.W+xx]
                nd -= 1
            else: keep.append(e)
        m.dd2 = keep; m.mtxm = struct.pack(f'<{m.W*m.H}H', *mt)
    return nd, bad

# ---------- cast, voiced lines, briefing ----------
class Cast:
    """speakers: name -> dict(colour=sclib.NAME_COLOURS[...], portrait=unit id, voice=dict(voice,pitch,rate,fx), profile=str)
    Every line is voiced (m.voice, edge-tts) and carries VO markup delivery notes (docs/voice-delivery-markup.md)."""
    def __init__(s, m, prefix, speakers):
        s.m = m; s.prefix = prefix; s.sp = speakers; s.n = 0
        sys.path.insert(0, os.path.join(TOOLS, '..'))
        import voice_delivery as VD; s.VD = VD
    def line(s, who, script):
        c = s.sp[who]; s.n += 1; text = s.VD.strip(script)
        snd = s.m.voice(f'{s.prefix}_{s.n:02d}', text, script=script, speaker=who, profile=c['profile'], **c['voice'])
        return f"{c['colour']}{who}:\x01 {text}", snd
    def say(s, lines, loc):
        """in-mission conversation: one Transmission per line (portrait + voice + subtitle); sclib.T paces and pauses it"""
        out = []
        for who, script in lines:
            t, snd = s.line(who, script); out.append(s.m.trans(t, s.sp[who]['portrait'], loc, snd))
        return out
    def brief(s, objectives, lines, slots=None):
        """briefing: objectives, each speaker's portrait appears when they first speak, voiced lines, End of Briefing"""
        m = s.m; slots = slots or {}
        order = list(dict.fromkeys(w for w, _ in lines))
        for w in order: slots.setdefault(w, len(slots) % 4)
        acts = [m.b_obj(objectives), m.b_wait(600)]; shown = set()
        for who, script in lines:
            if who not in shown: acts += [m.b_portrait(s.sp[who]['portrait'], slots[who]), m.b_wait(300)]; shown.add(who)
            t, snd = s.line(who, script); acts += m.b_trans(t, slots[who], snd)
        acts += [m.b_wait(300)] + m.b_end(tuple(sorted(set(slots.values()))))
        m.B(acts)

# ---------- shared helpers for the example missions (tools/bw/examples) and any other mission ----------
CREEP_SRC = {131: (9.5, 6.5), 132: (9.5, 6.5), 133: (9.5, 6.5), 143: (5.5, 4), 146: (5.5, 4), 144: (5.5, 4)}
ZERG_HALLS = {131, 132, 133}; PROTOSS_FREE = {154, 156, 157}      # Nexus, Pylon, Assimilator need no power

class Town:
    """buildings of one owner placed race-correctly: Zerg buildings only on creep (Hatchery/colony creep ellipses),
    Protoss buildings only inside a Pylon's power field, Terran anywhere. put() falls back to any free spot (placecheck
    autofix then adds creep/pylons for computer players)."""
    def __init__(s, m, g, owner, race):
        s.m, s.g, s.owner, s.race = m, g, owner, race; s.creep = []; s.pylons = []
    def _ok(s, uid, x0, y0):
        w, h = BUILDSIZE[uid]
        if s.race == 'zerg' and uid not in ZERG_HALLS and uid != 149:
            return any(all(((cx-qx)/rx)**2+((cy-qy)/ry)**2 <= 1 for cx in (x0, x0+w) for cy in (y0, y0+h)) for qx, qy, rx, ry in s.creep)
        if s.race == 'protoss' and uid not in PROTOSS_FREE:
            px, py = x0*32+w*16, y0*32+h*16
            return any(((px-qx)/256)**2+((py-qy)/160)**2 <= 0.85 for qx, qy in s.pylons)
        return True
    def put(s, uid, cx, cy, rmax=6):
        sp = near(s.g, uid, cx, cy, 0, rmax, cond=lambda x0, y0: s._ok(uid, x0, y0)) or near(s.g, uid, cx, cy, 0, rmax+4)
        if not sp: raise SystemExit(f'Town.put: no room for unit {uid} near {cx},{cy}')
        s.m.unit(uid, *sp, s.owner); s.g.add_raw(s.m.units[-1]); s.note(uid, *sp)
        return sp
    def note(s, uid, x0, y0):
        """register a hall/colony/pylon placed elsewhere (e.g. by res_base) as a creep or power source"""
        w, h = BUILDSIZE.get(uid, (1, 1))
        if uid in CREEP_SRC: s.creep.append((x0+w/2, y0+h/2, *CREEP_SRC[uid]))
        if uid == 156: s.pylons.append((x0*32+w*16, y0*32+h*16))
    def workers(s, uid, n, x0, x1, y0, y1):
        k = 0
        for x in range(x0, x1):
            for y in range(y0, y1):
                if k < n and s.g.spot_unit(x, y): s.m.unit(uid, x, y, s.owner); s.g.occ.add((x, y)); k += 1
        return k

def waves(m, owner, times, src, dst, groups, alts=None, switch0=None, extra_conds=()):
    """scripted attack waves: at each elapsed time t (seconds) create the groups [(unit, n), ...] (n <= 4, sclib trickles
    them) at location src and order them to dst. groups may be a function i -> list. alts (e.g. m.target_stands(...))
    gate every wave on 'the producing building still stands' over its whole morph chain; switch0 makes each wave run once."""
    for i, t in enumerate(times):
        gr = groups(i) if callable(groups) else groups
        acts = [m.create(owner, u, n, src) for u, n in gr] + [m.order(owner, 229, src, dst)]
        if alts: m.T_each([owner], [m.ET(t)] + list(extra_conds), alts, acts, switch=None if switch0 is None else switch0+i)
        else: m.T([owner], [m.ET(t)] + list(extra_conds), acts)

def auto_forbid(m, boxes=(), unit_margin=2):
    """doodad keep-out boxes: the given boxes, a margin around every placed unit and every location"""
    out = list(boxes)
    for raw in m.units:
        px, py = struct.unpack_from('<HH', raw, 4); out.append((px//32-unit_margin, py//32-unit_margin, px//32+unit_margin+1, py//32+unit_margin+1))
    out += [(v[1]-1, v[2]-1, v[3]+1, v[4]+1) for k, v in m.locs.items() if k != 'Anywhere']
    return out
