#!/usr/bin/env python3
"""EXAMPLE (complex, kill a boss with a mid-mission twist, Zerg, Desert): Hask Hunt.
Run from the repository root:   python3 tools/bw/examples/ex_hask_hunt.py [--no-checks]
Writes output/examples/ex_hask_hunt/ and runs every check.

STRUCTURE ONLY: copy how this file is built, never its mission design. Every mission invents its own objective, map,
start, enemy, story and rewards.

What it demonstrates
  start       build-up (Hatchery and Spawning Pool only): the brood grows from almost nothing under pressure
  objective   kill an enemy general in his own hero slot and colour (HERO_SLOT) at his command post on a plateau;
              twist: when the brood storms the post he escapes to a fortress at the other end of the map and a
              countdown starts (his dropship); the objective text changes, the old line disappears
  enemy       a Terran main and an expansion, both running town AIs, waves at the hive from the start
  side        reach an overlook: its reward is information, the general's bolt hole is revealed in advance
              (SIDE_OBJECTIVE reach :: info)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exlib
import sclib
from sclib import *
import missionkit as K

SLUG, NAME = 'ex_hask_hunt', 'Ex_Hask_Hunt'
P1, P2, P3 = 0, 1, 2
DIRT, HDIRT, DMUD, TAR, DUNES, PIT, HDUNES, CRAGS, HCRAGS, ROCKY, COMPOUND = 2, 3, 4, 5, 8, 9, 10, 11, 12, 15, 16   # Desert ISOM
W, H = 128, 128
HASK = 100                      # Alexei Stukov hero unit, renamed: the enemy general (own slot P3)
ESCAPE = 360                    # seconds until his dropship arrives after the twist

# ---------------- terrain: the hive in the south-west, the general's plateau in the north, his fortress in the south-east ----------------
m = Map(W, H, 5, DIRT, seed=7124)
for cx, cy, r in [(30, 84, 8), (80, 60, 9), (96, 100, 7), (24, 30, 7)]: m.blob(cx, cy, r, DUNES, 0.45)
for cx, cy, r in [(50, 100, 6), (70, 84, 6), (40, 50, 5)]: m.blob(cx, cy, r, DMUD, 0.4)
for cx, cy, r in [(42, 92, 5), (86, 82, 6), (30, 62, 5), (88, 42, 5), (64, 116, 4)]: m.blob(cx, cy, r, TAR, 0.5)    # lakes shape the routes
m.blob(60, 34, 9, HDIRT, 0.3)                                       # the command-post plateau (two ramps)
HX, HY = 20, 106
PPLAN = K.mineral_plan(HX, HY, 'left', 8, form='column'); K.paint_back(m, PPLAN, TAR)
CX, CY = 108, 12
CPLAN = K.mineral_plan(CX, CY, 'upright', 8, form='corner'); K.paint_back(m, CPLAN, TAR)
EX, EY = 112, 66
EPLAN = K.mineral_plan(EX, EY, 'right', 7, form='column'); K.paint_back(m, EPLAN, TAR)
m.edges(DIRT, skip=[(12, 108, 10), (116, 6, 10), (122, 68, 8)], mix=[TAR, HDIRT, DUNES])
m.build_terrain()
ti = K.TerrainInfo(m)
ramps = K.auto_ramps(m, ti, 60, 34, 9, angles=[120, 200], need=2)
print('ramps', ramps); assert len(ramps) >= 1, 'the plateau needs a ramp'
ti = K.TerrainInfo(m)

# ---------------- players ----------------
m.ownr = [6, 5, 5, 0, 0, 0, 0, 0] + [0]*4          # human Zerg, Terran (P2), General Hask (P3, own slot)
m.side = [0, 1, 1, 7, 7, 7, 7, 7] + [4]*4
m.colr = [5, 0, 7, 3, 4, 1, 6, 2]; sclib.RENDER_COLR = m.colr     # purple brood, red Terrans, white general
m.forces = [0, 1, 1, 3, 3, 3, 3, 3]; m.forcenames = ['Brood', 'Hask Command', '', '']; m.forceflags = [0, 2 | 8, 0, 0]
g = K.Grid(m)

# ---------------- the brood: Hatchery and Spawning Pool ----------------
m.unit(STARTLOC, HX*32+64, HY*32+48, P1, pixel=True); g = K.Grid(m)
K.res_base(m, g, ti, HX, HY, 'left', 8, [1500, 1250, 1500, 1000], 5000, P1, HATCH, plan=PPLAN)
TZ = K.Town(m, g, P1, 'zerg'); TZ.note(HATCH, HX, HY)
TZ.put(POOL, HX+7, HY-4, 5)
TZ.workers(DRONE, 5, HX-3, HX, HY-1, HY+4)
K.scatter(m, g, ZERGLING, 6, HX+12, HY-2, P1, 1.5)
for i in range(2): m.unit(OVERLORD, HX+3+i*4, HY-6, P1)

# ---------------- the Terran main and expansion (town AIs) ----------------
def terran_town(hx, hy, side, plan, amounts, gas, builds, bunkers, scvs, army):
    T = K.Town(m, g, P2, 'terran')
    K.res_base(m, g, ti, hx, hy, side, len(plan['fields']), amounts, gas, P2, CC, plan=plan)
    for b, cx, cy in builds: T.put(b, cx, cy, 5)
    for cx, cy in bunkers: T.put(BUNKER, cx, cy, 4)
    T.workers(SCV, scvs, hx-3, hx, hy-1, hy+4) or T.workers(SCV, scvs, hx+4, hx+7, hy-1, hy+4)
    for u, n, cx, cy in army: K.scatter(m, g, u, n, cx, cy, P2, 1.6)
    return T
TT = terran_town(CX, CY, 'upright', CPLAN, [3000, 2500, 3500, 4000], 12000,
                 [(BARRACKS, CX-8, CY+2), (BARRACKS, CX-8, CY+8), (FACTORY, CX-1, CY+9), (ACADEMY, CX-13, CY+5), (SUPPLY, CX-13, CY-1), (SUPPLY, CX+3, CY+13), (EBAY, CX-4, CY+14)],
                 [(CX-12, CY+14), (CX-17, CY+8)], 8, [(MARINE, 6, CX-10, CY+12), (TANK, 2, CX-6, CY+12)])
terran_town(EX, EY, 'right', EPLAN, [2500, 3000, 2500], 10000, [(BARRACKS, EX-8, EY-3), (SUPPLY, EX-6, EY+5)], [(EX-11, EY+1)], 5,
            [(MARINE, 4, EX-12, EY-2)])
m.unit(STARTLOC, CX*32+64, CY*32+48, P2, pixel=True)
m.loc('Terran Hall', CX-1, CY-1, CX+5, CY+4)

# ---------------- the command post on the plateau, and General Hask (P3) ----------------
m.rename(HASK, 'General Hask', 300, 2)
TT.put(BARRACKS, 58, 30, 4); TT.put(BUNKER, 54, 37, 3); TT.put(BUNKER, 63, 39, 3); TT.put(TURRET, 64, 31, 3)
K.scatter(m, g, MARINE, 4, 58, 36, P2, 1.2); K.scatter(m, g, MEDIC, 2, 60, 35, P2, 0.8); K.scatter(m, g, TANK, 1, 56, 33, P2, 0.5)
K.scatter(m, g, HASK, 1, 61, 33, P3, 0.4)
m.loc('Command Post', 51, 27, 69, 42)
# the fortress in the south-east: the general's bolt hole
m.loc('Fallback Bunker', 98, 104, 110, 114)
TT.put(BUNKER, 100, 102, 3); TT.put(BUNKER, 106, 101, 3); TT.put(TURRET, 104, 112, 3); TT.put(SUPPLY, 108, 108, 3)
K.scatter(m, g, TANK, 2, 104, 107, P2, 0.8); K.scatter(m, g, MARINE, 4, 101, 106, P2, 1.0)
# guards on the roads
for (cx, cy), grp in [((24, 96), [(MARINE, 3)]), ((37, 81), [(FIREBAT, 2), (MARINE, 2)]), ((47, 71), [(MARINE, 3), (MEDIC, 1)]),
                      ((62, 57), [(VULTURE, 2), (FIREBAT, 2)]), ((36, 112), [(MARINE, 3)]), ((56, 106), [(FIREBAT, 2), (MARINE, 2)]),
                      ((76, 110), [(VULTURE, 2), (MARINE, 2)]), ((88, 104), [(GOLIATH, 1), (MARINE, 3)]), ((18, 74), [(MARINE, 2), (FIREBAT, 1)]),
                      ((22, 54), [(MARINE, 3)])]:
    for u, n in grp: K.scatter(m, g, u, n, cx, cy, P2, 1.3)

# ---------------- locations ----------------
m.loc('Home Nest', HX-4, HY-8, HX+18, HY+10)
m.loc('Bone Ridge', 20, 34, 30, 44)
K.scatter(m, g, MARINE, 2, 26, 41, P2, 0.6)   # a Terran spotter pair on the ridge
K.free_loc(m, g, 'Terran Gate', CX-14, CY+20, 3, 6)
K.free_loc(m, g, 'Expansion Gate', EX-14, EY+6, 3, 6)
K.free_loc(m, g, 'Hive Front', HX+18, HY-6, 3, 6)

# ---------------- doodads ----------------
nd, left = K.dress(m, [DIRT, DUNES, DMUD], [HDIRT], forbid=K.auto_forbid(m, [(HX-12, HY-14, HX+22, HY+14), (CX-20, CY-6, CX+14, CY+22), (EX-16, EY-8, EX+12, EY+12), (50, 26, 70, 44), (96, 100, 112, 116)]),
                   counts=(130, 10, 110), seed=83)
print('doodads', nd, 'seams left', left)

# ---------------- cast ----------------
CAST = K.Cast(m, 'hh', {
    'Cerebrate Ulzhar': dict(colour=NAME_COLOURS['green'], portrait=HATCH,
        voice=dict(voice='en-US-RogerNeural', pitch='-12Hz', rate='-8%', fx='aecho=0.7:0.6:60:0.35,lowpass=f=3000'),
        profile='cerebrate; slow, deep, layered; patient hunter'),
    'General Hask': dict(colour=NAME_COLOURS['white'], portrait=HASK,
        voice=dict(voice='en-US-ChristopherNeural', pitch='-6Hz', rate='-2%', fx='highpass=f=200,lowpass=f=3800'),
        profile='Terran general; arrogant, cold, a coward under the bravado'),
    'Lieutenant Deke Morrow': dict(colour=NAME_COLOURS['yellow'], portrait=MARINE,
        voice=dict(voice='en-US-EricNeural', pitch='+0Hz', rate='+6%', fx='highpass=f=250,lowpass=f=3600'),
        profile='Hask aide on the radio; jumpy, loyal, talks too much'),
})
ULZ, HSK, MOR = 'Cerebrate Ulzhar', 'General Hask', 'Lieutenant Deke Morrow'
LINE_A = "Storm the Command Post and kill the traitor General Hask."
LINE_B = "Kill the traitor General Hask at the Fallback Bunker before his dropship arrives."
def objtext(stage, side=''):
    t = "\x04Objectives:\x01\n- " + (LINE_A if stage == 0 else LINE_B) + (" - done" if stage == 2 else "")
    t += "\n- The Home Nest must not fall."
    if side: t += "\n\x03Optional:\x01 Reach the overlook at Bone Ridge." + ('' if side == '+' else side)
    return t
CAST.brief(objtext(0), [
    (ULZ, "[emotion: cold; pace: slow] Hask burned our first brood. (0.4) He watches from his plateau in the north."),
    (ULZ, "[emotion: patient] Grow. (0.3) Climb his hill. *Bring him down*."),
    (HSK, "[emotion: arrogant] Let the bugs come, Morrow. (beat) Nobody climbs my hill."),
])

# ---------------- triggers ----------------
m.startres = {P1: (300, 50)}
m.hyperplayer = P2
L = m.L
m.T([P1], [m.ALWAYS()],
    CAST.say([(ULZ, "[emotion: cold] The Terrans will come for the nest first. (0.3) Grow quickly.")], L('Home Nest'))
    + [m.ping(L('Command Post')), m.obj(objtext(0))])
m.town_ai(P2, 'TMEx', (CX, CY)); m.town_ai(P2, 'TARx', (EX, EY), area=(EX-14, EY-9, EX+9, EY+10))
MAIN_UP = [m.cond(3, loc=L('Terran Hall'), player=P2, qty=1, unit=CC, cmp=0)]
K.waves(m, P2, [150, 300, 450, 620, 800, 980, 1160, 1340], L('Terran Gate'), L('Home Nest'),
        lambda i: [(MARINE, 3 + min(1, i//2))] + ([(FIREBAT, 2)] if i % 2 else []) + ([(VULTURE, 2)] if i >= 3 else []) + ([(TANK, 1)] if i >= 5 else []), extra_conds=MAIN_UP)
K.waves(m, P2, [380, 700, 1040], L('Expansion Gate'), L('Home Nest'), [(MARINE, 4), (MEDIC, 1)])
# side objective: the overlook (~3 minutes in); reaching it reveals the general's bolt hole for the rest of the mission
m.T([P1], [m.ET(180)],
    m.scene_reveal(L('Bone Ridge'), P1)
    + CAST.say([(ULZ, "[emotion: interested] Bone Ridge overlooks the whole valley. (0.3) Send a drone or a ling there.")], L('Bone Ridge'))
    + [m.order(P2, MARINE, L('Bone Ridge'), L('Bone Ridge')), m.ping(L('Bone Ridge')), m.setsw(7), m.setsw(9), m.text('\x07OBJECTIVES UPDATED\x01 - press F10 to review.')])
m.T([P1], [m.SW(7), m.cond(3, loc=L('Bone Ridge'), player=P1, qty=1, unit=MEN, cmp=0)],
    CAST.say([(ULZ, "[emotion: knowing] I see a fortress in the south-east, *empty* of purpose. (0.3) A bolt hole. He has planned to run.")], L('Bone Ridge'))
    + m.reveal(P1, L('Fallback Bunker'), permanent=True, why='the overlook reward: the bolt hole stays visible') + [m.setsw(8), m.setsw(9)])
m.T([P1], [m.SW(7), m.SW(8, False), m.SW(1)], [m.setsw(6), m.setsw(9), m.text('\x06Optional objective failed:\x01 Hask has already run.')])
# the twist: the brood storms the post -> Hask escapes to the fortress, a countdown starts
m.T([P1], [m.cond(3, loc=L('Command Post'), player=P1, qty=3, unit=MEN, cmp=0), m.cond(15, player=P3, qty=0, unit=HASK, cmp=10)],
    CAST.say([(MOR, "[emotion: panicked; pace: quick] They are on the hill, General! (beat) Shuttle is ready!"),
              (HSK, "[emotion: furious] Fall back to the bunker. (0.3) Call the dropship. *Now*.")], L('Command Post'))
    + [m.act(25, loc=L('Command Post'), player=P3, unit=HASK, mod=0, flags=0x04), m.create(P3, HASK, 1, L('Fallback Bunker')),
       m.ping(L('Fallback Bunker')), m.act(14, time=ESCAPE, mod=7, flags=0x04), m.setsw(1), m.setsw(9)])
m.T([P1], [m.SW(1), m.ET(10)],
    CAST.say([(ULZ, "[emotion: cold] He runs. (0.4) Six minutes before his ship comes. *Catch him*.")], L('Home Nest')))
# objective text refresh (switch 9)
SIDE = {'': [m.SW(7, False)], '+': [m.SW(7), m.SW(8, False), m.SW(6, False)], ' - done': [m.SW(8)], ' - failed': [m.SW(6), m.SW(8, False)]}
for stage, sc in ((0, [m.SW(1, False)]), (1, [m.SW(1)])):
    for opt, oc in SIDE.items():
        m.T([P1], [m.SW(9)] + sc + oc, [m.obj(objtext(stage, opt)), m.setsw(9, False)])
# victory: the general dies (wherever he is); defeat: his dropship arrives, or the hive falls
m.T([P1], [m.cond(15, player=P3, qty=1, unit=HASK, cmp=0)],
    [m.obj(objtext(2))] + CAST.say([(ULZ, "[emotion: satisfied; pace: slow] Hask is consumed. (0.4) The first brood is avenged.")], L('Home Nest')) + [m.act(1, flags=0x04)])
m.T([P1], [m.SW(1), m.cond(1, qty=0, cmp=10, flags=0), m.cond(15, player=P3, qty=0, unit=HASK, cmp=10)],
    [m.text('\x06The dropship has lifted off. General Hask has escaped.'), m.wait(2000), m.act(2, flags=0x04)])
m.T([P1], m.target_gone(P1, HATCH, L('Home Nest')), [m.text('\x06The Home Nest has fallen.'), m.wait(2000), m.act(2, flags=0x04)])

import trigsim
exlib.finish(m, SLUG, NAME, 'EXAMPLE: Hask Hunt', 'Example mission (VibeModForge): hunt down the general who burned the first brood.',
             [trigsim.at(900, 'the brood storms the command post', trigsim.spawn(P1, ZERGLING, 'Command Post', 4)),
              trigsim.at(1100, 'the general dies at the fallback bunker', trigsim.kill(P3, HASK, 'Fallback Bunker'))])
