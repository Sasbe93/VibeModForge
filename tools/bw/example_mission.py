#!/usr/bin/env python3
"""EXAMPLE StarCraft: Brood War campaign mission, built end to end with sclib + missionkit.

Run from the repository root:   python3 tools/bw/example_mission.py [--no-checks]
Writes output/example_mission/Example_Mission.scx plus Design_Note_Example_Mission.md, Voice_Script_Example_Mission.md
and a minimap PNG, then runs the delivery checks (predelivery_check.py incl. map design and cliff shape, placement
check, trigger simulation). The scenario is a neutral placeholder: copy this file as the base for a real mission and
replace terrain, cast, story and objectives with your own (keep the structure and the checks).

What it demonstrates
  terrain     organic ISOM painting (blobs, meandering roads, ragged map edge), a raised ridge with seam-aware normal-size
              ramps, water and cliffs BEHIND every mineral line, ground-texture variety (dirt, grass, mud, rocky ground)
  bases       Blizzard mineral formations (columns and a corner line, minform.py), geyser gaps, a full enemy base
              on the ridge plus an expansion
  dressing    battlefield doodads (never on bases, ramps, lanes or locations), hard seams removed automatically
  story       a briefing with speaking portraits and voiced lines; voiced in-mission transmissions (edge-tts + VO markup)
  objectives  main + optional objective, announced by a character, with done/failed versions of every line
  reward      an organic reward: the rescued squad joins and hands over its field depot and bunker (REWARD_WHY)
  triggers    start resources, AI scripts, small waves from the enemy base that stop when its hatchery dies,
              victory/defeat, Set Next Scenario hook
Requirements: isomtool + tileset files (external/README.md), edge-tts + ffmpeg (DEPENDENCIES.md), external/bw/vcod_seeds.txt.
"""
import sys, os, math, struct, json, subprocess
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
os.chdir(ROOT); sys.path.insert(0, 'tools/lib/bw'); sys.path.insert(0, 'tools/bw'); sys.path.insert(0, 'tools/lib')
import sclib
from sclib import *
import missionkit as K

OUT = os.path.join(ROOT, 'output', 'example_mission'); os.makedirs(OUT, exist_ok=True)
NAME = 'Example_Mission'; MAP = os.path.join(OUT, NAME + '.scx')
P1, P2, P8, NEU = 0, 1, 7, 11
DIRT, HDIRT, MUD, WATER, GRASS, HGRASS, ASPH, ROCKY = 2, 3, 4, 5, 6, 7, 14, 15      # Badlands ISOM brushes
W, H = 128, 96

# ---------------- terrain ----------------
m = Map(W, H, 0, DIRT, seed=4242)
for cx, cy, r in [(40, 60, 9), (70, 40, 8), (60, 78, 7), (22, 30, 6), (86, 66, 6)]: m.blob(cx, cy, r, GRASS, 0.45)   # grass fields
for cx, cy, r in [(52, 22, 4), (78, 82, 4), (30, 84, 3)]: m.blob(cx, cy, r, ROCKY, 0.4)                              # rough ground
m.blob(60, 52, 4.5, WATER, 0.4)                                                                                         # central pond
m.blob(100, 24, 15, HDIRT, 0.3)                 # the ridge: enemy main on high ground
m.blob(103, 22, 6, HGRASS, 0.4)
m.path([(3, 56), (2, 66), (3, 76), (1, 84)], 2.4, WATER)                  # water behind the player's minerals
m.path([(119, 8), (118, 20), (119, 32)], 2.4, WATER)                      # behind the ridge minerals
# (the water behind the enemy expansion comes from paint_back below)
m.path([(24, 72), (48, 64), (70, 58), (88, 50), (92, 42)], 1.2, MUD)      # old road from the outpost to the ridge
m.path([(48, 64), (66, 74), (92, 80)], 1.0, MUD)                          # side road to the ravine camp
# mineral formations differ between bases (check 43): the player base gets a column, the expansion a corner line; plan
# them before the terrain is built and paint water behind them (missionkit.mineral_plan + paint_back, tools/lib/bw/minform.py)
HX, HY = 16, 66
PPLAN = K.mineral_plan(HX, HY, 'left', 8, form='column')
K.paint_back(m, PPLAN, WATER)
XX, XY = 103, 56
XPLAN = K.mineral_plan(XX, XY, 'downright', 7, form='corner')
K.paint_back(m, XPLAN, WATER)
m.edges(DIRT, skip=[(8, 70, 10), (116, 22, 10), (112, 58, 8)], mix=[HDIRT, WATER])
m.build_terrain()
ti = K.TerrainInfo(m)
ramps = K.auto_ramps(m, ti, 100, 24, 15, angles=[135, 200], need=2)
print('ramps', ramps); assert len(ramps) == 2, 'ridge needs two ramps'

# ---------------- players ----------------
m.ownr = [6, 5, 0, 0, 0, 0, 0, 3] + [0]*4          # human, computer, rescuable (P8)
m.side = [1, 0, 7, 7, 7, 7, 7, 1] + [4]*4          # Terran, Zerg, -, Terran survey squad
m.colr = [1, 0, 2, 3, 4, 5, 6, 7]; sclib.RENDER_COLR = m.colr
m.forces = [0, 1, 3, 3, 3, 3, 3, 0]; m.forcenames = ['Outpost', 'Brood', '', '']; m.forceflags = [2, 0, 0, 0]
g = K.Grid(m)

# ---------------- player base: SW outpost ----------------
m.unit(STARTLOC, HX*32+64, HY*32+48, P1, pixel=True); g = K.Grid(m)
pg = K.res_base(m, g, ti, HX, HY, 'left', 8, [1500, 1200, 1500, 1800], 5000, P1, CC, plan=PPLAN)
for b, cx, cy in [(SUPPLY, HX+8, HY-5), (SUPPLY, HX+8, HY+7), (BARRACKS, HX+12, HY-1)]: K.put(m, g, b, cx, cy, P1, 0, 5)
K.put(m, g, 125, HX+18, HY-4, P1, 0, 4)                              # Bunker (id 125) toward the road
for x in range(HX-3, HX):
    for y in range(HY-1, HY+4):
        if sum(1 for r in m.units if struct.unpack_from('<H', r, 8)[0] == SCV and r[16] == P1) < 8 and g.spot_unit(x, y):
            m.unit(SCV, x, y, P1); g.occ.add((x, y))
K.scatter(m, g, MARINE, 8, HX+15, HY+2, P1, 2.0); K.scatter(m, g, 34, 2, HX+13, HY+3, P1, 1.0)   # marines, medics

# ---------------- enemy: Zerg main on the ridge + expansion ----------------
EX, EY = 97, 19
eg = K.res_base(m, g, ti, EX, EY, ['right', 'upright', 'downright'], 8, [3000, 2500, 3500, 4000], 12000, P2, HATCH)
CREEPS = [(EX+2, EY+1.5, 9.5, 6.5)]
def zput(uid, cx, cy, rmax=6, src=False):
    sp = K.near(g, uid, cx, cy, 0, rmax, cond=lambda x0, y0: K_in(uid, x0, y0)) or K.near(g, uid, cx, cy, 0, rmax)
    assert sp, ('no spot', uid, cx, cy)
    m.unit(uid, *sp, P2); g.add_raw(m.units[-1])
    if src: CREEPS.append((sp[0]+1, sp[1]+1, 5.5, 4))
    return sp
def K_in(uid, x0, y0):
    w, h = BUILDSIZE[uid]
    return any(all(((cx-qx)/rx)**2+((cy-qy)/ry)**2 <= 1 for cx in (x0, x0+w) for cy in (y0, y0+h)) for qx, qy, rx, ry in CREEPS)
for cx, cy in [(EX-6, EY+6), (EX-8, EY-3), (EX-3, EY+9)]: zput(CREEP, cx, cy, 4, src=True)
for b, cx, cy in [(POOL, EX-5, EY-5), (HYDEN, EX-9, EY+2), (EVO, EX-2, EY+7)]: zput(b, cx, cy, 5)
for cx, cy in [(EX-10, EY+8), (EX-9, EY+1)]: zput(SUNKEN, cx, cy, 6, src=True)
for cx, cy in [(EX-7, EY+11)]: zput(SPORE, cx, cy, 4, src=True)
m.gas_building(EXTRACTOR, P2, eg[0], eg[1], 12000)
dr = 0
for x in range(EX+4, EX+7):
    for y in range(EY-1, EY+4):
        if dr < 8 and g.spot_unit(x, y): m.unit(DRONE, x, y, P2); g.occ.add((x, y)); dr += 1
K.scatter(m, g, ZERGLING, 8, EX-9, EY+5, P2, 2.0); K.scatter(m, g, HYDRA, 4, EX-6, EY+3, P2, 1.5)
for i in range(3): m.unit(OVERLORD, EX-4+i*3, EY-6, P2)
m.loc('Ridge Town', EX-18, EY-12, EX+10, EY+16); m.loc('Ridge Hall', EX-1, EY-1, EX+5, EY+4)
xg = K.res_base(m, g, ti, XX, XY, 'downright', 7, [2500, 3000, 3500], 10000, P2, HATCH, plan=XPLAN)
CREEPS.append((XX+2, XY+1.5, 9.5, 6.5))
for cx, cy in [(XX-5, XY+3), (XX-4, XY-3)]: zput(SUNKEN, cx, cy, 4, src=True)
dr = 0
for x in range(XX+4, XX+7):
    for y in range(XY-1, XY+4):
        if dr < 5 and g.spot_unit(x, y): m.unit(DRONE, x, y, P2); g.occ.add((x, y)); dr += 1
K.scatter(m, g, ZERGLING, 4, XX-6, XY, P2, 1.5)
m.loc('Fen Town', XX-12, XY-9, XX+9, XY+10)

# ---------------- the stranded survey squad (rescuable P8) in the SE ravine ----------------
RX, RY = 88, 82
dep = K.put(m, g, SUPPLY, RX+3, RY-2, P8, 0, 4); bun = K.put(m, g, 125, RX-2, RY-3, P8, 0, 4)
K.scatter(m, g, MARINE, 3, RX, RY+1, P8, 1.2); K.scatter(m, g, 32, 1, RX+1, RY+2, P8, 0.8); K.scatter(m, g, 34, 1, RX-1, RY+2, P8, 0.8)
m.loc('Ravine Camp', RX-6, RY-6, RX+8, RY+6)

# ---------------- locations ----------------
m.loc('Outpost', HX-4, HY-10, HX+24, HY+12)
K.free_loc(m, g, 'Outpost Front', HX+20, HY-2, 3, 8)
K.free_loc(m, g, 'Ridge Gate', EX-12, EY+4, 3, 6)
K.free_loc(m, g, 'Fen Gate', XX-8, XY, 3, 6)

# ---------------- doodads (bases, ramps, roads, units and locations kept clear) ----------------
forbid = [(HX-10, HY-10, HX+26, HY+13), (EX-20, EY-13, EX+12, EY+17), (XX-13, XY-10, XX+11, XY+11), (RX-8, RY-8, RX+10, RY+8)]
for raw in m.units:
    px, py = struct.unpack_from('<HH', raw, 4); forbid.append((px//32-2, py//32-2, px//32+3, py//32+3))
forbid += [(v[1]-1, v[2]-1, v[3]+1, v[4]+1) for k, v in m.locs.items() if k != 'Anywhere']
nd, left = K.dress(m, [DIRT, GRASS, MUD, ROCKY], [HDIRT], forbid=forbid, counts=(140, 10, 110), seed=81)
print('doodads', nd, 'seams left', left)
g = K.Grid(m)

# ---------------- cast (VO markup v1 on every line) ----------------
CAST = K.Cast(m, 'ex', {
    'Captain Ilse Varn': dict(colour=NAME_COLOURS['white'], portrait=MARINE,
        voice=dict(voice='en-GB-SoniaNeural', pitch='-6Hz', rate='-2%', fx='highpass=f=200,lowpass=f=4200,acompressor'),
        profile='outpost commander over a field radio; low, even alto; tired, precise, never raises her voice'),
    'Sergeant Okafor': dict(colour=NAME_COLOURS['yellow'], portrait=32,
        voice=dict(voice='en-US-GuyNeural', pitch='-4Hz', rate='+4%', fx='highpass=f=250,lowpass=f=3600,acompressor'),
        profile='survey squad sergeant; warm, rough baritone; jokes to keep his people calm'),
})
VARN, OKA = 'Captain Ilse Varn', 'Sergeant Okafor'
OBJ = "\x04Objectives:\x01\n- Destroy the Hatchery on the ridge."
CAST.brief(OBJ, [
    (VARN, "[emotion: weary; pace: slow] This is Captain Varn, Outpost Nine. (0.3) The brood has dug in on the ridge above our road."),
    (VARN, "[emotion: resolute] Their hatchery feeds every raid on this outpost. Burn it, and the raids *stop*."),
    (OKA, "[emotion: dry] Okafor here, survey team. We are... (beat) *stuck* in the eastern ravine. Nobody panic."),
    (VARN, "[emotion: calm] First the ridge, Sergeant. (0.3) I have not forgotten you."),
])

# ---------------- triggers ----------------
m.startres = {P1: (300, 100)}
m.hyperplayer = P2
L = m.L
def objtext(opt, done_main=False, opt_state=''):
    t = "\x04Objectives:\x01\n- Destroy the Hatchery on the ridge." + (" - done" if done_main else "")
    if opt: t += "\n\x03Optional:\x01 Reach the survey squad in the eastern ravine." + opt_state
    return t
m.T([P1], [m.ALWAYS()],
    CAST.say([(VARN, "[emotion: resolute] Outpost Nine, the ridge is north-east, up the old road. (0.3) Two ramps lead *up*."),
              (VARN, "[emotion: weary] Keep the bunker manned. The brood probes our front every few minutes.")], L('Outpost'))
    + [m.ping(L('Ridge Hall')), m.obj(objtext(False))])
m.T([P2], [m.ALWAYS()], [m.ai('ZMEx', loc=L('Ridge Town'), keep=True), m.ai('ZMEx', loc=L('Fen Town'), keep=True)])
# optional objective, announced by a character ~2 minutes in (>= 60 s after the opening talk)
m.T([P1], [m.ET(120)],
    m.scene_reveal(L('Ravine Camp'), P1)      # the camp is outside the player's sight: reveal it for the talk, removed after
    + CAST.say([(OKA, "[emotion: dry] Captain, Okafor again. The ravine is *quiet*... for now. (0.3) We still have our depot and a bunker down here."),
              (VARN, "[emotion: calm] Send anyone east along the side road, and the squad is ours again.")], L('Ravine Camp'))
    + [m.ping(L('Ravine Camp')), m.obj(objtext(True)), m.text('\x07OBJECTIVES UPDATED\x01 - press F10 to review.')])
# reward: reaching the camp -> the squad joins (engine rescue) and hands over its depot and bunker (Give Units)
m.T([P1], [m.ET(121), m.cond(3, loc=L('Ravine Camp'), player=P1, qty=1, unit=MEN, cmp=0)],
    [m.act(48, loc=L('Ravine Camp'), player=P8, unit=ANYUNIT, mod=0, num=P1, flags=0x14)]
    + CAST.say([(OKA, "[emotion: cheerful] Took you long enough. (beat) The depot and the bunker are yours, Captain. So are *we*."),
                (VARN, "[emotion: tender; pace: slow] Welcome back, Sergeant. (0.3) Now help me finish the ridge.")], L('Ravine Camp'))
    + [m.obj(objtext(True, False, ' - done')), m.setsw(5)])
m.T([P1], [m.ET(121), m.SW(5, False), m.cond(2, player=P8, qty=0, unit=MEN, cmp=10)],
    [m.obj(objtext(True, False, ' - failed')), m.text('\x06Optional objective failed:\x01 the survey squad was lost.')])
# small waves from the enemy base, only while its hatchery stands (the base visibly feeds the pressure)
HAS = m.cond(3, loc=L('Ridge Hall'), player=P2, qty=1, unit=HATCH, cmp=0)
for i, t in enumerate(range(240, 1500, 160)):
    n = 2 + min(2, i//2)
    acts = [m.create(P2, ZERGLING, n, L('Ridge Gate'))] + ([m.create(P2, HYDRA, 2, L('Ridge Gate'))] if i >= 2 else []) + [m.order(P2, ANYUNIT, L('Ridge Gate'), L('Outpost Front'))]
    m.T([P2], [m.ET(t), HAS], acts)
# victory / defeat
m.T([P1], [m.cond(3, loc=L('Ridge Hall'), player=P2, qty=0, unit=HATCH, cmp=10), m.cond(3, loc=L('Ridge Hall'), player=P2, qty=0, unit=LAIR, cmp=10)],
    [m.obj(objtext(False, True))]
    + CAST.say([(VARN, "[emotion: triumphant; pace: slow] The hatchery is *down*. (0.3) No more raids on this road. Outpost Nine, stand easy.")], L('Ridge Hall'))
    + [m.act(1, flags=0x04)])
m.T([P1], [m.cond(2, player=P1, qty=0, unit=BUILDINGS, cmp=10)], [m.text('\x06Outpost Nine has fallen.'), m.wait(2000), m.act(2, flags=0x04)])

# ---------------- save ----------------
import placecheck
log = []; errs = placecheck.autofix(m, log=log.append); print('placement autofix:', log[-1] if log else '-')
m.save(MAP, 'EXAMPLE: Outpost Nine', 'Example mission (VibeModForge): destroy the hatchery on the ridge.')
m.write_voice_script(os.path.join(OUT, f'Voice_Script_{NAME}.md'), 'EXAMPLE: Outpost Nine')
print('validate', validate(MAP)); print('timelines', m.check_timelines())
import shutil
shutil.copy(os.path.join(ROOT, 'templates', 'Design_Note_example_bw_mission.md'), os.path.join(OUT, f'Design_Note_{NAME}.md'))
# the raised enemy main is a deliberate story choice (the brood dug in on the ridge): approve it explicitly
json.dump({'bases': [{'hall': [EX+1, EY+1], 'reason': 'story: the brood holds the ridge above the road; two normal ramps lead up'}]},
          open(os.path.splitext(MAP)[0] + '.highground_ok.json', 'w'), indent=1)
render(MAP, os.path.join(OUT, NAME + '_minimap.png'), {}, 'EXAMPLE: Outpost Nine')
print('wrote', MAP)

# ---------------- delivery checks (deliver only on 0 FAIL) ----------------
if '--no-checks' not in sys.argv:
    rc = 0
    errs, stats = placecheck.check(MAP, m.ts); print('placecheck', stats, errs[:8]); rc |= bool(errs)
    import trigsim
    trigsim.prove(MAP, [trigsim.at(150, 'a marine reaches the ravine camp', trigsim.move(P1, MARINE, 'Ravine Camp')),
                        trigsim.at(600, 'the ridge hatchery is destroyed', trigsim.kill(P2, HATCH, 'Ridge Hall'))])
    r = subprocess.run([sys.executable, 'tools/bw/predelivery_check.py', MAP], env=dict(os.environ, SCMDRAFT_REAL=os.environ.get('SCMDRAFT_REAL', '0')))
    rc |= r.returncode
    print('EXAMPLE RESULT:', 'FAIL' if rc else 'PASS (0 FAIL)'); sys.exit(rc)
