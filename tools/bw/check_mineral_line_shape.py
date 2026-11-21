#!/usr/bin/env python3
"""Check 43 mineral_line_shape: mineral lines look like Blizzard lines, and a campaign map does not repeat one
shape everywhere.   python3 check_mineral_line_shape.py MAP.scx [...]

Per base (town hall or start location; hall-less fields: the cluster on its own), lines of 5+ fields:
  FAIL straight:   more than 3 fields flush in one straight line (same x in consecutive tile rows for a column, same
                   y at x, x+2, x+4 ... for a row). Pro ladder maps: 2 (166 of 172 lines), the only longer ones hug the
                   map edge (exempt: every field within 5 tiles of the map edge).
  FAIL unstaggered: fewer than n/3 fields (n/4 for hall-less expansions) off the line's main depth (perpendicular
                   offset), i.e. a flat line with only its ends bent ('almost all in one line except the top and bottom
                   one', The Poisoned Well). Map-edge lines are exempt from both rules.
  FAIL too_close / too_far: nearest field not 3 empty tiles from the hall (Blizzard: always 3; allowed 3..4) or a
                   field more than 6 tiles away (lines of up to 10 fields).
Per map (campaign maps with 3+ bases with a hall or start location):
  FAIL same_shape: every line has the same shape (all columns left/right of the hall, or all rows, or all corners).
                   Empire Wars campaign: 23 of 27 maps with several bases mix shapes. Pro ladder maps mostly repeat the
                   column, so maps named *Ranked* only WARN. Deliberate exception: 'MINERAL_SHAPES_OK: <reason>' in the
                   design note / build info / <map>.mineral_ok.txt.
"""
import sys, os, struct, math, re, glob
from collections import Counter
HALLS = {106, 131, 132, 133, 154}; START = 214; MIN = {176, 177, 178}

def _chk(path):
    from eudplib.bindings._rust import mpqapi
    q = mpqapi.MPQ.open(path); d = bytes(q.extract_file('staredit\\scenario.chk')); s = {}; i = 0
    while i+8 <= len(d):
        k = d[i:i+4].decode('latin1'); n = struct.unpack_from('<i', d, i+4)[0]
        if n < 0: break
        if k == 'UNIT': s['UNIT'] = d[i+8:i+8+n]
        else: s.setdefault(k, d[i+8:i+8+n])
        i += 8+n
    return s
def _units(s):
    u = s.get('UNIT', b'')
    return [dict(id=r[3], x=r[1], y=r[2]) for r in (struct.unpack_from('<IHHHHHHBBBBIHHII', u, j) for j in range(0, len(u)//36*36, 36))]
def gap(h, u):
    A = (h['x']/32-2, h['y']/32-1.5, h['x']/32+2, h['y']/32+1.5); B = (u['x']/32-1, u['y']/32-0.5, u['x']/32+1, u['y']/32+0.5)
    return max(max(B[0]-A[2], A[0]-B[2], 0), max(B[1]-A[3], A[1]-B[3], 0))
def side(h, u):
    dx = (u['x']-h['x'])/32; dy = (u['y']-h['y'])/32
    if abs(dx) >= abs(dy)*1.4: return 'W' if dx < 0 else 'E'
    if abs(dy) >= abs(dx): return 'N' if dy < 0 else 'S'
    return 'diag'
def straight_run(M):
    T = {(int(u['x']//32-1), int(u['y']//32)) for u in M}; best = 1 if T else 0
    for (x, y) in T:
        k = 1
        while (x, y+k) in T: k += 1
        j = 1
        while (x+2*j, y) in T: j += 1
        best = max(best, k, j)
    return best
def lines(us):
    """[(anchor or None, [fields])]: fields go to the nearest hall/start location within 12 tiles (gap <= 7)"""
    an = [u for u in us if u['id'] in HALLS]
    an += [u for u in us if u['id'] == START and not any(abs(u['x']-h['x']) < 96 and abs(u['y']-h['y']) < 96 for h in an)]
    B = [(h, []) for h in an]; left = []
    for r in (u for u in us if u['id'] in MIN):
        d = [math.hypot(r['x']-h['x'], r['y']-h['y']) for h, _ in B]
        k = min(range(len(B)), key=d.__getitem__) if B else None
        if k is not None and d[k] <= 12*32 and gap(B[k][0], r) <= 7: B[k][1].append(r)
        else: left.append(r)
    out = [(h, M) for h, M in B if len(M) >= 4]
    cl = []
    for p in left:
        hit = [c for c in cl if any(abs(p['x']-q['x']) <= 96 and abs(p['y']-q['y']) <= 96 for q in c)]
        cl = [c for c in cl if c not in hit]+[[p]+[q for c in hit for q in c]]
    return out+[(None, c) for c in cl if len(c) >= 4]
def shape(h, M):
    c = Counter(side(h, u) for u in M); n = len(M); v = c['W']+c['E']; hz = c['N']+c['S']
    return 'column' if v >= 0.75*n else 'row' if hz >= 0.75*n else 'corner' if v >= 2 and hz >= 2 else 'diagonal'
def staggered(M, shp):
    """fields off the line's main depth: column -> x offset, row -> y offset, else distance from the fitted line"""
    if shp == 'column': off = [int(u['x']//32) for u in M]
    elif shp == 'row': off = [int(u['y']//32) for u in M]
    else:
        xs = [u['x']/32 for u in M]; ys = [u['y']/32 for u in M]; cx = sum(xs)/len(xs); cy = sum(ys)/len(ys)
        a = 0.5*math.atan2(2*sum((x-cx)*(y-cy) for x, y in zip(xs, ys)), sum((x-cx)**2 for x in xs)-sum((y-cy)**2 for y in ys))
        off = [round((-(x-cx)*math.sin(a)+(y-cy)*math.cos(a))) for x, y in zip(xs, ys)]
    return len(M)-Counter(off).most_common(1)[0][1]
def _note_ok(path):
    d = os.path.dirname(os.path.abspath(path)); pre = os.path.splitext(os.path.basename(path))[0]
    fs = [path[:-4]+'.mineral_ok.txt'] + glob.glob(os.path.join(d, '*Design_Note*.md')) + glob.glob(os.path.join(d, '*build_info*.json'))
    for f in fs:
        if os.path.exists(f):
            m = re.search(r'MINERAL_SHAPES_OK:\s*([^\n"]+)', open(f, encoding='utf-8', errors='replace').read())
            if m: return m.group(1).strip()
    return None
def run(path):
    s = _chk(path); us = _units(s); W, H = struct.unpack('<HH', s['DIM ']); R = []; bad = []; shapes = []
    for h, M in lines(us):
        if len(M) < 5: continue
        tx = [int(u['x']//32) for u in M]; ty = [int(u['y']//32) for u in M]
        where = f'hall ({int(h["x"]//32)},{int(h["y"]//32)})' if h else f'fields near ({sum(tx)//len(tx)},{sum(ty)//len(ty)})'
        edge = all(x <= 5 or x >= W-6 or y <= 5 or y >= H-6 for x, y in zip(tx, ty))
        if h: shp = shape(h, M); shapes.append(shp)
        else:
            xs = set(tx); ys = set(ty); shp = 'column' if len(ys) >= len(M)-1 and len(xs) <= 3 else 'row' if len(ys) <= 3 else 'corner'
        run_ = straight_run(M)
        if run_ > 3 and not edge: bad.append(f'{where}: {run_} fields flush in one straight line (max 3)')
        st = staggered(M, shp); need = math.ceil(len(M)/(3 if h else 4))
        if st < need and not edge: bad.append(f'{where}: only {st} of {len(M)} fields staggered off the line (need {need}); a flat line with bent ends is not a Blizzard line')
        if h:
            g = sorted(gap(h, u) for u in M)
            if not 3 <= g[0] <= 4: bad.append(f'{where}: nearest field {g[0]:g} tiles from the hall (Blizzard: 3)')
            if g[-1] > 6 and len(M) <= 10: bad.append(f'{where}: a field {g[-1]:g} tiles from the hall (max 6)')
    R += [f'FAIL mineral_line_shape: {b}' for b in bad] or [f'OK   mineral_line_shape: every line staggered, max 3 flush, nearest field 3 tiles ({len(shapes)} bases)']
    if len(shapes) >= 3:
        c = Counter(shapes)
        if len(c) == 1:
            ok = _note_ok(path); msg = f'all {len(shapes)} bases use the same mineral line shape ({shapes[0]}): mix columns, two-deep rows and corners (minform)'
            if ok: R.append(f'OK   mineral_line_shape: {msg} - MINERAL_SHAPES_OK: {ok}')
            elif 'ranked' in os.path.basename(path).lower(): R.append(f'WARN mineral_line_shape: {msg}')
            else: R.append(f'FAIL mineral_line_shape: {msg}')
        else: R.append(f'OK   mineral_line_shape: shapes vary {dict(c)}')
    return R
if __name__ == '__main__':
    rc = 0
    for p in sys.argv[1:]:
        print('###', p)
        for l in run(p): print(l); rc |= l.startswith('FAIL')
    sys.exit(rc)
