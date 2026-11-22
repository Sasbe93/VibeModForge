#!/usr/bin/env python3
"""EXAMPLE (medium, capture and hold control points against an expanding AI, Terran, Badlands): Relay Watch.
Run from the repository root:   python3 tools/bw/examples/ex_relay_watch.py [--no-checks]
Writes output/examples/ex_relay_watch/ and runs every check.

STRUCTURE ONLY: copy how this file is built, never its mission design. Every mission invents its own objective, map,
start, enemy, story and rewards.

What it demonstrates
  start       build-up (Command Center, one Barracks, a few marines): the player must spread out from a thin start
  objective   capture three relay stations held by Protoss pickets (no enemy unit or building left at a relay, own
              troops present: the relay's turret is handed over, REWARD_WHY), then hold all three until a visible
              countdown ends; a relay without its turret at zero means defeat
  paths       waves every ~100 s from three directions (north, centre, south), each aimed at a different relay
  enemy       a Protoss base running an expansion town AI from the first second, with free expansion sites it takes
  side        rescue: a stranded Goliath crew in the western canyon joins when reached (SIDE_OBJECTIVE rescue :: units)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exlib
import sclib
from sclib import *
import missionkit as K

SLUG, NAME = 'ex_relay_watch', 'Ex_Relay_Watch'
P1, P2, P8, P12 = 0, 1, 7, 11
DIRT, HDIRT, MUD, WATER, GRASS, HGRASS, ASPH, ROCKY = 2, 3, 4, 5, 6, 7, 14, 15     # Badlands ISOM
W, H = 128, 96
TIMER = 1200
RELAYS = [('North Relay', 58, 14), ('Centre Relay', 64, 48), ('South Relay', 56, 82)]

# ---------------- terrain: three relays between the base and the Protoss ----------------
m = Map(W, H, 0, DIRT, seed=2227)
for cx, cy, r in [(30, 20, 7), (34, 76, 7), (90, 30, 6), (88, 70, 6)]: m.blob(cx, cy, r, GRASS, 0.45)
for cx, cy, r in [(46, 48, 5), (80, 52, 5)]: m.blob(cx, cy, r, MUD, 0.4)
m.blob(64, 48, 8, HDIRT, 0.3)                                       # the centre relay's mesa (two ramps)
for pts, w in [([(40, 0), (44, 18), (40, 32)], 2.4), ([(42, 62), (46, 78), (40, 95)], 2.4), ([(76, 10), (82, 24)], 2.0), ([(78, 72), (84, 86)], 2.0)]:
    m.path(pts, w, WATER)                                            # creeks: each relay has two approaches
for pts in [[(26, 46), (44, 40), (52, 22), (58, 16)], [(26, 50), (44, 58), (52, 76), (56, 80)]]: m.path(pts, 1.2, ASPH)
HX, HY = 12, 46
PPLAN = K.mineral_plan(HX, HY, 'left', 8, form='column'); K.paint_back(m, PPLAN, WATER)
CX, CY = 110, 46
CPLAN = K.mineral_plan(CX, CY, 'right', 8, form='column'); K.paint_back(m, CPLAN, WATER)
E1 = K.mineral_plan(106, 10, 'upright', 7, form='corner'); K.paint_back(m, E1, WATER)
E2 = K.mineral_plan(106, 80, 'downright', 7, form='corner'); K.paint_back(m, E2, WATER)
m.edges(DIRT, skip=[(6, 48, 8), (122, 48, 8), (116, 6, 10), (116, 88, 10)], mix=[WATER, HDIRT, GRASS])
m.build_terrain()
ti = K.TerrainInfo(m)
ramps = K.auto_ramps(m, ti, 64, 48, 8, angles=[180, 0], need=2)
print('ramps', ramps); assert len(ramps) == 2, 'the centre mesa needs two ramps'
ti = K.TerrainInfo(m)

# ---------------- players ----------------
m.ownr = [6, 5, 0, 0, 0, 0, 0, 3] + [0]*4          # human Terran, Protoss (P2), stranded crew (rescuable P8)
m.side = [1, 2, 7, 7, 7, 7, 7, 1] + [4]*4
m.colr = [2, 1, 0, 3, 4, 5, 6, 7]; sclib.RENDER_COLR = m.colr
m.forces = [0, 1, 3, 3, 3, 3, 3, 0]; m.forcenames = ['Signal Corps', 'Templar', '', '']; m.forceflags = [0, 0, 0, 0]
g = K.Grid(m)

# ---------------- the player's thin start ----------------
m.unit(STARTLOC, HX*32+64, HY*32+48, P1, pixel=True); g = K.Grid(m)
K.res_base(m, g, ti, HX, HY, 'left', 8, [1500, 1250, 1500, 1000], 5000, P1, CC, plan=PPLAN)
TP = K.Town(m, g, P1, 'terran')
TP.put(BARRACKS, HX+8, HY-4, 5); TP.put(SUPPLY, HX+3, HY+7, 4)
TP.workers(SCV, 6, HX-3, HX, HY-1, HY+4)
K.scatter(m, g, MARINE, 6, HX+14, HY+1, P1, 1.5)

# ---------------- the Protoss: main with an expansion town AI, two free expansion sites ----------------
TT = K.Town(m, g, P2, 'protoss')
K.res_base(m, g, ti, CX, CY, 'right', 8, [3000, 2500, 3500, 4000], 12000, P2, NEXUS, plan=CPLAN)
for cx, cy in [(CX-6, CY-6), (CX-6, CY+6), (CX-12, CY)]: TT.put(PYLON, cx, cy, 3)
for b, cx, cy in [(GATEWAY, CX-10, CY-5), (GATEWAY, CX-10, CY+4), (166, CX-3, CY-9), (164, CX-3, CY+8)]: TT.put(b, cx, cy, 5)
for cx, cy in [(CX-15, CY-3), (CX-15, CY+3)]: TT.put(CANNON, cx, cy, 4)
TT.workers(PROBE, 8, CX+5, CX+8, CY-1, CY+4)
K.scatter(m, g, ZEALOT, 4, CX-14, CY, P2, 1.5); K.scatter(m, g, DRAGOON, 3, CX-12, CY+1, P2, 1.2)
m.unit(STARTLOC, CX*32+64, CY*32+48, P2, pixel=True)
m.loc('Templar Hall', CX-1, CY-1, CX+5, CY+4)
K.res_base(m, g, ti, 106, 10, 'upright', 7, [1500, 1500, 1000], 5000, plan=E1)
K.res_base(m, g, ti, 106, 80, 'downright', 7, [1500, 1500, 1000], 5000, plan=E2)

# ---------------- the relays: a neutral turret each, held by a Protoss picket ----------------
for name, rx, ry in RELAYS:
    m.unit(TURRET, rx, ry, P12); g.add_raw(m.units[-1])
    m.loc(name, rx-5, ry-4, rx+7, ry+6)
    TT.put(PYLON, rx+4, ry+2, 3); TT.put(CANNON, rx+3, ry-1, 3)
    K.scatter(m, g, ZEALOT, 2, rx-2, ry+3, P2, 0.8); K.scatter(m, g, DRAGOON, 1, rx+1, ry+4, P2, 0.5)
# the stranded Goliath crew in the western canyon (more than 8 tiles from any Protoss)
K.scatter(m, g, GOLIATH, 3, 22, 86, P8, 1.0)
m.loc('Western Canyon', 18, 82, 28, 92)
# two Protoss patrols between the base and the canyon
K.scatter(m, g, ZEALOT, 2, 21, 60, P2, 0.8); K.scatter(m, g, DRAGOON, 1, 23, 61, P2, 0.5); K.scatter(m, g, DRAGOON, 2, 21, 75, P2, 0.8)

# ---------------- locations ----------------
m.loc('Home Base', HX-4, HY-8, HX+20, HY+10)
K.free_loc(m, g, 'North Gate', 92, 22, 3, 6)
K.free_loc(m, g, 'East Gate', 92, 46, 3, 6)
K.free_loc(m, g, 'South Gate', 92, 74, 3, 6)

# ---------------- doodads ----------------
nd, left = K.dress(m, [DIRT, GRASS, MUD], [HDIRT], forbid=K.auto_forbid(m, [(HX-12, HY-14, HX+22, HY+14), (CX-18, CY-14, CX+12, CY+14), (98, 2, 126, 20), (98, 72, 126, 94)]),
                   counts=(110, 8, 90), seed=29)
print('doodads', nd, 'seams left', left)

# ---------------- cast ----------------
CAST = K.Cast(m, 'rw', {
    'Major Ines Calder': dict(colour=NAME_COLOURS['yellow'], portrait=MARINE,
        voice=dict(voice='en-GB-LibbyNeural', pitch='-4Hz', rate='+2%', fx='highpass=f=200,lowpass=f=4000,acompressor'),
        profile='signal corps major; brisk, practical, counts in minutes'),
    'Technician Obi Varga': dict(colour=NAME_COLOURS['white'], portrait=SCV,
        voice=dict(voice='en-US-EricNeural', pitch='+2Hz', rate='+8%', fx='highpass=f=250,lowpass=f=3600'),
        profile='uplink technician; fast, chatty, nervous about his equipment'),
    'Templar Ashai': dict(colour=NAME_COLOURS['blue'], portrait=ZEALOT,
        voice=dict(voice='en-US-GuyNeural', pitch='-8Hz', rate='-6%', fx='aecho=0.6:0.5:40:0.3'),
        profile='Protoss commander; cold, formal, contemptuous of the Terrans'),
})
CAL, VAR, ASH = 'Major Ines Calder', 'Technician Obi Varga', 'Templar Ashai'
def objtext(stage, side=''):
    t = "\x04Objectives:\x01\n- Capture all three relay stations." + (" - done" if stage >= 1 else "")
    t += "\n- Hold out at all three relays until the uplink completes (20 minutes)." + (" - done" if stage >= 2 else "")
    t += "\n- The Command Center must stand."
    if side: t += "\n\x03Optional:\x01 Find the stranded Goliath crew in the Western Canyon." + ('' if side == '+' else side)
    return t
CAST.brief(objtext(0), [
    (CAL, "[emotion: brisk] The uplink needs all three relays, Varga. (0.3) How long?"),
    (VAR, "[emotion: nervous; pace: quick] Twenty minutes, Major. (beat) And the Protoss are sitting on every one of them."),
    (ASH, "[emotion: cold; pace: slow] Terrans. (0.4) You will not speak across this world."),
])

# ---------------- triggers ----------------
m.startres = {P1: (500, 200)}
m.tech = K.tech_level('Terran', 'mid', drop={114, 115, 8, 11, 9, 58, 12})   # middle chapter: Barracks and Factory tier; the Starport comes later
m.hyperplayer = P2
L = m.L
m.T([P1], [m.ALWAYS()],
    CAST.say([(VAR, "[emotion: chatty] Uplink running. (0.3) Twenty minutes on the clock, starting *now*."),
              (CAL, "[emotion: brisk] Clear the pickets and take every relay. Then keep them.")], L('Home Base'))
    + [m.obj(objtext(0)), m.act(14, time=TIMER, mod=7, flags=0x04)] + [m.ping(L(n)) for n, _, _ in RELAYS])
m.town_ai(P2, 'PMEx', (CX, CY))
# capture: own troops at a relay and no Protoss unit or building left there -> the relay's turret joins (REWARD_WHY)
for k, (name, rx, ry) in enumerate(RELAYS):
    m.T([P1], [m.cond(3, loc=L(name), player=P1, qty=3, unit=MEN, cmp=0), m.cond(3, loc=L(name), player=P2, qty=0, unit=MEN, cmp=10),
               m.cond(3, loc=L(name), player=P2, qty=0, unit=BUILDINGS, cmp=10)],
        [m.act(48, loc=L(name), player=P12, unit=TURRET, num=P1, mod=0, flags=0x04), m.setsw(1+k), m.setsw(9)]
        + CAST.say([(VAR, "[emotion: excited] Relay %s is ours! (0.3) Signal is *up*." % name.split()[0].lower())], L(name)))
ALL = [m.SW(1), m.SW(2), m.SW(3)]
m.T([P1], ALL, CAST.say([(CAL, "[emotion: firm] All three. (0.3) Now we *hold* them until the clock runs out.")], L('Centre Relay')) + [m.setsw(4), m.setsw(9)])
# waves: every ~100 s, three directions, each at its own relay; north and centre only while the Protoss main stands
MAIN_UP = [m.cond(3, loc=L('Templar Hall'), player=P2, qty=1, unit=NEXUS, cmp=0)]
grp = lambda i: [(ZEALOT, 2 + min(2, i//2)), (DRAGOON, 1 + min(3, i//2))]
K.waves(m, P2, [170, 470, 770, 1070], L('North Gate'), L('North Relay'), grp, extra_conds=MAIN_UP)
K.waves(m, P2, [270, 570, 870, 1140], L('East Gate'), L('Centre Relay'), grp, extra_conds=MAIN_UP)
# the south column is the templar's field army marching in from beyond the eastern edge: it does not depend on the
# Templar Hall, so breaking the hall early never ends all pressure on the relays (check enemy_base_pressure)
K.waves(m, P2, [370, 670, 970], L('South Gate'), L('South Relay'), grp)
m.T([P1], [m.ET(600)], CAST.say([(ASH, "[emotion: contemptuous] Still here? (0.3) Then the relays will be your graves.")], L('Home Base')))
# side objective: the stranded crew (pointed out ~3 minutes in); rescued by the engine when reached
m.T([P1], [m.ET(180)],
    m.scene_reveal(L('Western Canyon'), P1)
    + CAST.say([(VAR, "[emotion: surprised] Major, a distress beacon. (0.3) Goliath crew, stuck in the Western Canyon.")], L('Western Canyon'))
    + [m.order(P8, GOLIATH, L('Western Canyon'), L('Western Canyon')), m.ping(L('Western Canyon')), m.setsw(7), m.setsw(9), m.text('\x07OBJECTIVES UPDATED\x01 - press F10 to review.')])
m.T([P1], [m.SW(7), m.cond(3, loc=L('Western Canyon'), player=P1, qty=1, unit=GOLIATH, cmp=0)],
    CAST.say([(CAL, "[emotion: pleased] Welcome back, crew. (0.3) Get those walkers to a relay.")], L('Western Canyon')) + [m.setsw(8), m.setsw(9)])
m.T([P1], [m.SW(7), m.SW(8, False), m.cond(2, player=P8, qty=0, unit=GOLIATH, cmp=10)],
    [m.setsw(6), m.setsw(9), m.text('\x06Optional objective failed:\x01 the crew is lost.')])
# objective text refresh (switch 9)
SIDE = {'': [m.SW(7, False)], '+': [m.SW(7), m.SW(8, False), m.SW(6, False)], ' - done': [m.SW(8)], ' - failed': [m.SW(6), m.SW(8, False)]}
for stage, sc in ((0, [m.SW(4, False)]), (1, [m.SW(4)])):
    for opt, oc in SIDE.items():
        m.T([P1], [m.SW(9)] + sc + oc, [m.obj(objtext(stage, opt)), m.setsw(9, False)])
# at zero: victory if every relay has the player's turret, defeat otherwise
HELD = [m.cond(3, loc=L(n), player=P1, qty=1, unit=TURRET, cmp=0) for n, _, _ in RELAYS]
m.T([P1], [m.cond(1, qty=0, cmp=10, flags=0)] + HELD,
    [m.obj(objtext(2))] + CAST.say([(VAR, "[emotion: elated] Uplink complete! (0.4) They heard us, Major. *Everyone* heard us.")], L('Home Base')) + [m.act(1, flags=0x04)])
for n, _, _ in RELAYS:
    m.T([P1], [m.cond(1, qty=0, cmp=10, flags=0), m.cond(3, loc=L(n), player=P1, qty=0, unit=TURRET, cmp=10)],
        [m.text('\x06The uplink failed: %s was not ours when the clock ran out.' % n), m.wait(2000), m.act(2, flags=0x04)])
m.T([P1], [m.cond(2, player=P1, qty=0, unit=CC, cmp=10)], [m.text('\x06The Command Center has fallen.'), m.wait(2000), m.act(2, flags=0x04)])

import trigsim
exlib.finish(m, SLUG, NAME, 'EXAMPLE: Relay Watch', 'Example mission (VibeModForge): take the three relays and keep them until the uplink completes.',
             sum([[trigsim.at(300 + 120*k, f'the {n} picket falls', trigsim.kill(P2, ANYUNIT, n)),
                   trigsim.at(301 + 120*k, f'marines reach the {n}', trigsim.spawn(P1, MARINE, n, 3))] for k, (n, _, _) in enumerate(RELAYS)], [])
             + [trigsim.at(TIMER + 5, 'the countdown ends with the relays held', lambda *a: None)])
