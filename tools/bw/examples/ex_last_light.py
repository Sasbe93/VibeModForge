#!/usr/bin/env python3
"""EXAMPLE (simple, survive with a meaningful timer, Terran, Desert): Last Light.
Run from the repository root:   python3 tools/bw/examples/ex_last_light.py [--no-checks]
Writes output/examples/ex_last_light/ and runs every check.

STRUCTURE ONLY: copy how this file is built, never its mission design. Every mission invents its own objective, map,
start, enemy, story and rewards.

What it demonstrates
  start       established (a mining station held for months): START_SETUP established + START_DEFENSE_WHY for the bunkers
  objective   survive until the evacuation fleet arrives: a visible countdown, victory at 0, defeat if the Command Center falls
  paths       waves from three directions (north valley, east pass, south sand caves), each direction three or more times
              within the timer; every direction is fed by a real producing hive cluster and stops when it falls
  enemy       one Zerg brood with a main and an expansion, both running their town AI from the first second
  side        none: a mission does not need a side objective
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exlib
import sclib
from sclib import *
import missionkit as K

SLUG, NAME = 'ex_last_light', 'Ex_Last_Light'
P1, P2 = 0, 1
DIRT, HDIRT, DMUD, TAR, DUNES, PIT, HDUNES, CRAGS, HCRAGS, ROCKY, COMPOUND = 2, 3, 4, 5, 8, 9, 10, 11, 12, 15, 16   # Desert ISOM
W, H = 128, 96
TIMER = 900

# ---------------- terrain: a mining station on a dune shelf, three ways in ----------------
m = Map(W, H, 5, DIRT, seed=5518)
for cx, cy, r in [(64, 62, 10), (30, 30, 7), (96, 76, 7)]: m.blob(cx, cy, r, DMUD, 0.45)
for cx, cy, r in [(84, 24, 6), (20, 66, 6), (104, 88, 5)]: m.blob(cx, cy, r, DUNES, 0.4)
m.blob(76, 70, 3, COMPOUND, 0.3)                                    # landing pad east of the station
m.blob(26, 46, 8, HDIRT, 0.35)                                     # the west mesa (two ramps)
for cx, cy, r in [(40, 22, 5), (88, 70, 4)]: m.blob(cx, cy, r, ROCKY, 0.4)    # rocky flats
for pts, w in [([(80, 40), (90, 48), (88, 58)], 2.8), ([(40, 74), (48, 80), (60, 84)], 2.4),
               ([(70, 36), (76, 44)], 2.0), ([(100, 60), (110, 70), (124, 72)], 2.2)]:
    m.path(pts, w, TAR)                                              # tar pits funnel the approaches
m.path([(66, 54), (64, 36), (62, 22)], 1.2, ROCKY); m.path([(70, 62), (90, 56), (100, 50)], 1.2, ROCKY)
HX, HY = 58, 60
PPLAN = K.mineral_plan(HX, HY, 'left', 8, form='column'); K.paint_back(m, PPLAN, TAR)
NX, NY = 60, 12
NPLAN = K.mineral_plan(NX, NY, 'upleft', 8, form='corner'); K.paint_back(m, NPLAN, TAR)
EX, EY = 108, 40
EPLAN = K.mineral_plan(EX, EY, 'right', 7, form='corner' if False else 'column'); K.paint_back(m, EPLAN, TAR)
m.edges(DIRT, skip=[(8, 64, 8), (58, 6, 12), (122, 42, 8)], mix=[TAR, HDIRT, DUNES])
m.build_terrain()
ti = K.TerrainInfo(m)
ramps = K.auto_ramps(m, ti, 26, 46, 8, angles=[0, 300], need=2)
print('ramps', ramps); assert len(ramps) == 2, 'the mesa needs two ramps'
ti = K.TerrainInfo(m)

# ---------------- players ----------------
m.ownr = [6, 5, 0, 0, 0, 0, 0, 0] + [0]*4
m.side = [1, 0, 7, 7, 7, 7, 7, 7] + [4]*4
m.colr = [0, 5, 2, 3, 4, 1, 6, 7]; sclib.RENDER_COLR = m.colr
m.forces = [0, 1, 3, 3, 3, 3, 3, 3]; m.forcenames = ['Station', 'Brood', '', '']; m.forceflags = [2, 0, 0, 0]
g = K.Grid(m)

# ---------------- the station: established (held for months) ----------------
m.unit(STARTLOC, HX*32+64, HY*32+48, P1, pixel=True); g = K.Grid(m)
K.res_base(m, g, ti, HX, HY, 'left', 8, [1500, 1000, 1500, 1200], 5000, P1, CC, plan=PPLAN)
T1 = K.Town(m, g, P1, 'terran')
for b, cx, cy in [(BARRACKS, HX+8, HY-4), (BARRACKS, HX+9, HY+2), (ACADEMY, HX+6, HY+7), (FACTORY, HX+13, HY-1),
                  (EBAY, HX+3, HY-7), (SUPPLY, HX+1, HY+8), (SUPPLY, HX+4, HY+10), (SUPPLY, HX+12, HY+6)]: T1.put(b, cx, cy, 5)
for cx, cy in [(HX+3, HY-14), (HX+20, HY-2), (HX+4, HY+16)]: T1.put(BUNKER, cx, cy, 4)    # one bunker per approach
T1.put(TURRET, HX+10, HY-9, 4)
T1.workers(SCV, 8, HX-3, HX, HY-1, HY+4)
K.scatter(m, g, MARINE, 10, HX+8, HY+12, P1, 2.0); K.scatter(m, g, MEDIC, 2, HX+10, HY+12, P1, 1.0)
K.scatter(m, g, FIREBAT, 2, HX+16, HY+2, P1, 1.0); K.scatter(m, g, TANK, 2, HX+5, HY-11, P1, 1.0)

# ---------------- the brood: main in the north, expansion in the east (town AI from second one) ----------------
def zerg_town(hx, hy, plan, side, amounts, gas, builds, sunkens, drones, army):
    T = K.Town(m, g, P2, 'zerg')
    K.res_base(m, g, ti, hx, hy, side, len(plan['fields']), amounts, gas, P2, HATCH, plan=plan); T.note(HATCH, hx, hy)
    for cx, cy in [(hx-5, hy+5), (hx+6, hy+6)]: T.put(CREEP, cx, cy, 4)
    for b, cx, cy in builds: T.put(b, cx, cy, 6)
    for cx, cy in sunkens: T.put(SUNKEN, cx, cy, 5)
    T.workers(DRONE, drones, hx-2, hx+6, hy+4, hy+7)
    for u, n, cx, cy in army: K.scatter(m, g, u, n, cx, cy, P2, 1.8)
    return T
zerg_town(NX, NY, NPLAN, 'upleft', [3000, 2500, 3500, 4000], 12000, [(POOL, NX-6, NY+4), (HYDEN, NX+8, NY+5), (EVO, NX-8, NY+8)],
          [(NX+2, NY+12), (NX-4, NY+11)], 8, [(ZERGLING, 6, NX, NY+15), (HYDRA, 4, NX+4, NY+14)])
zerg_town(EX, EY, EPLAN, 'right', [2500, 3000, 3500], 10000, [(EVO, EX-6, EY+6)], [(EX-7, EY), (EX-4, EY+9)], 6,
          [(ZERGLING, 4, EX-9, EY+4)])
for i in range(3): m.unit(OVERLORD, NX-4+i*4, NY-2, P2)
m.unit(STARTLOC, NX*32+64, NY*32+48, P2, pixel=True)
m.loc('North Hall', NX-1, NY-1, NX+5, NY+4); m.loc('East Hall', EX-1, EY-1, EX+5, EY+4)
g = K.Grid(m)

# ---------------- locations ----------------
m.loc('Station', HX-6, HY-10, HX+22, HY+14)
K.free_loc(m, g, 'North Gate', NX+1, NY+18, 3, 6)
K.free_loc(m, g, 'East Pass', EX-12, EY+8, 3, 6)
K.free_loc(m, g, 'Sand Caves', 34, 88, 3, 6)
K.free_loc(m, g, 'Station Front N', HX+3, HY-18, 3, 6)
K.free_loc(m, g, 'Station Front E', HX+24, HY+2, 3, 6)
K.free_loc(m, g, 'Station Front S', HX+2, HY+20, 3, 6)

# ---------------- doodads ----------------
nd, left = K.dress(m, [DIRT, DMUD, DUNES, ROCKY], [HDIRT], forbid=K.auto_forbid(m, [(HX-14, HY-16, HX+26, HY+20), (NX-14, NY-6, NX+14, NY+18), (EX-14, EY-8, EX+12, EY+14)]),
                   counts=(110, 8, 90), seed=61)
print('doodads', nd, 'seams left', left)

# ---------------- cast ----------------
CAST = K.Cast(m, 'll', {
    'Overseer Bram Kell': dict(colour=NAME_COLOURS['white'], portrait=SCV,
        voice=dict(voice='en-US-ChristopherNeural', pitch='-6Hz', rate='-4%', fx='highpass=f=200,lowpass=f=4000,acompressor'),
        profile='mining station overseer; gruff, slow baritone; counts everything, hates waste'),
    'Lieutenant Mara Oduya': dict(colour=NAME_COLOURS['yellow'], portrait=MARINE,
        voice=dict(voice='en-GB-LibbyNeural', pitch='-2Hz', rate='+4%', fx='highpass=f=250,lowpass=f=3800,acompressor'),
        profile='garrison lieutenant; clipped, fast, confident; jokes only when things are bad'),
})
KELL, ODU = 'Overseer Bram Kell', 'Lieutenant Mara Oduya'
OBJ = "\x04Objectives:\x01\n- Survive until the evacuation fleet arrives (15 minutes).\n- The Command Center must stand."
CAST.brief(OBJ, [
    (KELL, "[emotion: grim; pace: slow] Kessel Station, this is Kell. (0.3) The fleet is *fifteen* minutes out."),
    (ODU, "[emotion: clipped] The brood knows it, Overseer. (beat) North valley, east pass, and they have been tunnelling under the sand."),
    (KELL, "[emotion: stubborn] Then we hold all three. (0.3) Nobody gets left in this sand."),
])

# ---------------- triggers ----------------
m.startres = {P1: (600, 200)}
m.hyperplayer = P2
L = m.L
m.T([P1], [m.ALWAYS()],
    CAST.say([(ODU, "[emotion: clipped] Bunkers north, east and south are manned. (0.3) Tanks on the north road."),
              (KELL, "[emotion: grim] Keep the Command Center standing. The fleet docks *there*, or not at all.")], L('Station'))
    + [m.obj(OBJ), m.act(14, time=TIMER, mod=7, flags=0x04)])
m.town_ai(P2, 'ZMEx', (NX, NY)); m.town_ai(P2, 'ZARx', (EX, EY), area=(EX-12, EY-9, EX+9, EY+10))
NORTH = m.target_stands(P2, HATCH, L('North Hall')); EAST = m.target_stands(P2, HATCH, L('East Hall'))
def grp(base):
    return lambda i: [(ZERGLING, 4)] + [(HYDRA, min(4, 1+i))] + ([(ULTRA, 1)] if i >= 3 else [])
K.waves(m, P2, [100, 280, 460, 640, 800], L('North Gate'), L('Station'), grp('n'), alts=NORTH, switch0=120)
K.waves(m, P2, [190, 400, 610, 820], L('East Pass'), L('Station'), grp('e'), alts=EAST, switch0=130)
K.waves(m, P2, [330, 560, 760], L('Sand Caves'), L('Station'), lambda i: [(ZERGLING, 4), (ZERGLING, 4)] + ([(HYDRA, 3)] if i else []), alts=EAST, switch0=140)
# mid-way morale line (pure story, no objective change)
m.T([P1], [m.ET(450)], CAST.say([(KELL, "[emotion: weary] Halfway. (0.4) Seven and a half minutes, people. Count them with me.")], L('Station')))
# victory at countdown 0, defeat when the Command Center falls (Command counts it anywhere: a lifted CC still counts)
m.T([P1], [m.cond(1, qty=0, cmp=10, flags=0)],
    [m.obj(OBJ.replace('(15 minutes).', '(15 minutes). - done'))] + CAST.say([(ODU, "[emotion: relieved; pace: slow] Fleet on the pad. (0.3) Everybody *up*, now!")], L('Station')) + [m.act(1, flags=0x04)])
m.T([P1], [m.cond(2, player=P1, qty=0, unit=CC, cmp=10)], [m.text('\x06The Command Center has fallen. The fleet has nowhere to dock.'), m.wait(2000), m.act(2, flags=0x04)])

import trigsim
exlib.finish(m, SLUG, NAME, 'EXAMPLE: Last Light', 'Example mission (VibeModForge): hold the station until the fleet arrives.',
             [trigsim.at(TIMER + 5, 'the countdown ends', lambda *a: None)])
