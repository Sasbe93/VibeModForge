#!/usr/bin/env python3
"""check_map_design_bw: general map-design rules for EVERY StarCraft: Brood War map (ladder, campaign, fun map).

Usage: python3 tools/bw/check_map_design_bw.py MAP.scx|MAP.scm   (run from the repository root; exit 1 on any FAIL)

Rules (one implementation; check_ranked_bw.py calls run() from here and adds the ranked-only rules):
  reach           every base reachable by ground from the starts, map not mostly cut off (bw_reach)
  zone_doodads    base plateaus stay buildable; doodads there only as purposeful cover at the rim (bw_zone_doodads)
  ramp_size       normal-size ramps only (>= 8x5 tiles), no small ramp doodads (bw_ramp_size)
  resource_ground mineral/geyser footprints on walkable ground of the base level, harvest side reachable (bw_resource_ground)
  mineral_access  no resource blocking another's line to the hall (check_bw_rules: mineral_layout)
  scmdraft        strict CHK structure so ScmDraft / StarEdit open the map (check_bw_rules: strict_chk, sclib.validate)
  doodad_fit      BW doodads are tileset-bound by design: info only
A rule that crashes is reported as FAIL, never skipped silently.
Ranked-only (check_ranked_bw.py): ref-pool tolerances, natural/main sizing, rush distances, symmetry."""
import sys, os, io, contextlib, traceback
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
os.chdir(ROOT); sys.path.insert(0, 'tools/bw'); sys.path.insert(0, 'tools/lib/bw')

def _mineral_scm(path):
    import check_bw_rules as CB
    CB.F.clear(); CB.I.clear()
    with contextlib.redirect_stdout(io.StringIO()): CB.run(path)
    return [x for x in CB.F if not x.startswith('resource_ground')], list(CB.I)   # footprint/level: bw_resource_ground

def run(path, I, F, skip=()):
    import bw_reach, bw_zone_doodads, bw_ramp_size, bw_resource_ground
    rules = [('reach', lambda: bw_reach.check(path)), ('zone_doodads', lambda: bw_zone_doodads.check(path)),
             ('ramp_size', lambda: bw_ramp_size.check(path)), ('resource_ground', lambda: bw_resource_ground.check(path)), ('mineral_access+scmdraft', lambda: _mineral_scm(path))]
    for name, fn in rules:
        if name in skip: continue
        try:
            f, i = fn()
            F += [x.replace('FAIL ', '', 1) for x in f]; I += [x.replace('INFO ', '', 1) for x in i]
        except Exception as e:
            F.append(f'map_design: rule {name} CRASHED: {type(e).__name__}: {e}')
            I.append(traceback.format_exc().strip().split('\n')[-2].strip())
    I.append('doodad_fit: BW doodads are tileset-bound (info only)')
    return F, I

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'): print(__doc__); sys.exit(0)
    path = os.path.abspath(sys.argv[1]) if not os.path.isabs(sys.argv[1]) else sys.argv[1]
    I, F = [], []; run(path, I, F)
    for x in I: print('INFO', x)
    for x in F: print('FAIL', x)
    print('RESULT check_map_design_bw:', 'PASS' if not F else f'FAIL ({len(F)} fails)')
    sys.exit(1 if F else 0)
