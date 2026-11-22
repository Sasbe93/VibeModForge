#!/usr/bin/env python3
"""EXAMPLE (medium, rescue and return over a long dangerous path, Zerg, Ashworld): Cinder Run.
Run from the repository root:   python3 tools/bw/examples/ex_cinder_run.py [--no-checks]
Writes output/examples/ex_cinder_run/ and runs every check.

STRUCTURE ONLY: copy how this file is built, never its mission design. Every mission invents its own objective, map,
start, enemy, story and rewards.

What it demonstrates
  start       small base (Hatchery, Spawning Pool, Evolution Chamber, six Drones): the player builds the strike force
  objective   rescue and return: free a captive Queen from a Terran holding pen across the lava fields and bring her
              back to the Home Nest; the way there passes four guarded spots, the way back is chased by two pursuit groups
  rescue      the captives stand in a walled pocket more than 8 tiles from any Terran (rescue rule), owned by a
              Rescuable player; the player cannot morph Queens of its own (unit availability), so only she counts
  enemy       a Terran research compound running its town AI on the Command Center from the first second, a wrecked
              forward outpost marked AI_IDLE_OK, and waves toward the Home Nest while the compound stands
  side        capture: the rescued Queen can infest the wrecked outpost's Command Center (ability hint given);
              the reward is what it is: an infested base (SIDE_OBJECTIVE capture :: base)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exlib
import sclib
from sclib import *
import missionkit as K

SLUG, NAME = 'ex_cinder_run', 'Ex_Cinder_Run'
P1, P3, P8 = 0, 2, 7
DIRT, LAVA, HDIRT, HLAVA, SHALE, HSHALE, MAGMA, BROKEN = 2, 3, 4, 5, 6, 7, 8, 9     # Ashworld ISOM
W, H = 128, 96
ICC = 130

# ---------------- terrain: lava fields between the hive and the compound ----------------
m = Map(W, H, 3, DIRT, seed=3324)
for cx, cy, r in [(40, 66, 8), (70, 52, 9), (96, 72, 7), (30, 30, 7)]: m.blob(cx, cy, r, SHALE, 0.45)
for cx, cy, r in [(56, 80, 6), (82, 60, 5), (50, 36, 6)]: m.blob(cx, cy, r, BROKEN, 0.4)
for pts, w in [([(24, 50), (44, 46), (60, 40)], 2.6), ([(66, 70), (80, 82), (100, 86)], 2.4), ([(76, 30), (86, 44), (84, 52)], 2.2)]:
    m.path(pts, w, MAGMA)                                           # magma rivers split the fields
m.blob(116, 40, 6, HDIRT, 0.3)                                      # the holding-pen shelf (two ramps)
m.path([(26, 72), (40, 68), (62, 58), (84, 40), (96, 28)], 1.3, LAVA)   # the cooled lava road (walkable, not buildable)
HX, HY = 15, 74
PPLAN = K.mineral_plan(HX, HY, 'left', 8, form='column'); K.paint_back(m, PPLAN, MAGMA)
CX, CY = 100, 12
CPLAN = K.mineral_plan(CX, CY, 'upright', 8, form='corner'); K.paint_back(m, CPLAN, MAGMA)
m.edges(DIRT, skip=[(9, 76, 8), (104, 6, 10)], mix=[MAGMA, HDIRT, SHALE])
m.blob(61, 54, 5, DIRT, 0.2)                                       # the outpost's levelled pad (buildable)
m.build_terrain()
ti = K.TerrainInfo(m)
ramps = K.auto_ramps(m, ti, 116, 40, 6, angles=[180, 240], need=2)
print('ramps', ramps); assert len(ramps) == 2, 'the pen shelf needs two ramps'
ti = K.TerrainInfo(m)

# ---------------- players ----------------
m.ownr = [6, 0, 5, 0, 0, 0, 0, 3] + [0]*4          # human Zerg, Terran compound (P3), captives (rescuable P8)
m.side = [0, 7, 1, 7, 7, 7, 7, 0] + [4]*4
m.colr = [3, 1, 0, 2, 4, 5, 6, 7]; sclib.RENDER_COLR = m.colr
m.forces = [0, 3, 1, 3, 3, 3, 3, 0]; m.forcenames = ['Brood', 'Compound', '', '']; m.forceflags = [2, 0, 0, 0]
m.tech = dict(player=0, units=set(range(228)) - {QUEEN}, upgrades={i: UPG_MAX.get(i, 1) for i in range(61)}, techs=set(range(44)))
g = K.Grid(m)

# ---------------- the Home Nest: small base ----------------
m.unit(STARTLOC, HX*32+64, HY*32+48, P1, pixel=True); g = K.Grid(m)
K.res_base(m, g, ti, HX, HY, 'left', 8, [1500, 1250, 1500, 1000], 5000, P1, HATCH, plan=PPLAN)
TZ = K.Town(m, g, P1, 'zerg'); TZ.note(HATCH, HX, HY)
TZ.put(POOL, HX+7, HY-3, 5); TZ.put(EVO, HX+7, HY+4, 5)
TZ.workers(DRONE, 6, HX-3, HX, HY-1, HY+4)
K.scatter(m, g, ZERGLING, 6, HX+12, HY, P1, 1.5)
for i in range(2): m.unit(OVERLORD, HX+3+i*4, HY-5, P1)

# ---------------- the Terran compound (town AI on the Command Center) ----------------
TT = K.Town(m, g, P3, 'terran')
K.res_base(m, g, ti, CX, CY, 'upright', 8, [3000, 2500, 3500, 4000], 12000, P3, CC, plan=CPLAN)
for b, cx, cy in [(BARRACKS, CX-7, CY+2), (ACADEMY, CX-6, CY+7), (FACTORY, CX+2, CY+8), (SUPPLY, CX-10, CY-2), (SUPPLY, CX-10, CY+6)]: TT.put(b, cx, cy, 5)
for cx, cy in [(CX-8, CY+13), (CX-2, CY+15)]: TT.put(BUNKER, cx, cy, 4)
TT.workers(SCV, 8, CX+4, CX+7, CY-1, CY+4)
K.scatter(m, g, MARINE, 6, CX-5, CY+12, P3, 1.6); K.scatter(m, g, FIREBAT, 2, CX-3, CY+11, P3, 1.0); K.scatter(m, g, TANK, 1, CX-1, CY+6, P3, 0.5)
m.unit(STARTLOC, CX*32+64, CY*32+48, P3, pixel=True)
m.loc('Compound Hall', CX-1, CY-1, CX+5, CY+4)
# the wrecked forward outpost: a damaged Command Center (infestable), one bunker, no crew to run it (AI_IDLE_OK)
OX, OY = 58, 52
m.unit(CC, OX, OY, P3, hp=40); g.add_raw(m.units[-1])
TT.put(BUNKER, OX+6, OY+4, 4); K.scatter(m, g, MARINE, 3, OX+5, OY+7, P3, 1.0)
m.loc('Outpost', OX-2, OY-2, OX+9, OY+10)
# guards along the road
for (cx, cy), grp in [((38, 68), [(FIREBAT, 2), (MARINE, 2)]), ((84, 38), [(MARINE, 4), (TANK, 1)])]:
    for u, n in grp: K.scatter(m, g, u, n, cx, cy, P3, 1.4)
m.loc('Pen Ramp Guard', 100, 28, 108, 36); K.scatter(m, g, MARINE, 3, 103, 31, P3, 1.0); K.scatter(m, g, GOLIATH, 1, 104, 32, P3, 0.5)

# ---------------- the captives in the pen pocket (> 8 tiles from any Terran) ----------------
K.scatter(m, g, QUEEN, 1, 118, 42, P8, 0.6); K.scatter(m, g, DRONE, 3, 117, 44, P8, 1.0)
m.loc('Holding Pens', 112, 37, 123, 48)

# ---------------- locations ----------------
m.loc('Home Nest', HX-4, HY-6, HX+14, HY+9)
K.free_loc(m, g, 'Compound Gate', CX-10, CY+18, 3, 6)
K.free_loc(m, g, 'Road Ambush', 64, 62, 3, 6)
K.free_loc(m, g, 'Ridge Ambush', 92, 48, 3, 6)
K.free_loc(m, g, 'Hive Front', HX+16, HY-2, 3, 6)

# ---------------- doodads ----------------
nd, left = K.dress(m, [DIRT, SHALE, BROKEN], [HDIRT], forbid=K.auto_forbid(m, [(HX-12, HY-14, HX+20, HY+14), (CX-14, CY-6, CX+12, CY+20), (110, 34, 126, 50)]),
                   counts=(110, 8, 90), seed=47)
print('doodads', nd, 'seams left', left)

# ---------------- cast ----------------
CAST = K.Cast(m, 'cr', {
    'Overmind Voice Sessh': dict(colour=NAME_COLOURS['green'], portrait=HATCH,
        voice=dict(voice='en-US-RogerNeural', pitch='-14Hz', rate='-10%', fx='aecho=0.7:0.6:60:0.35,lowpass=f=3000'),
        profile='the hive mind of this brood; deep, slow, layered; cold and patient'),
    'Brood Queen Ixa': dict(colour=NAME_COLOURS['red'], portrait=QUEEN,
        voice=dict(voice='en-GB-SoniaNeural', pitch='-10Hz', rate='-4%', fx='aecho=0.6:0.5:40:0.3'),
        profile='captive brood queen; hoarse, furious, proud; hates being helped'),
    'Doctor Lenn Corvo': dict(colour=NAME_COLOURS['white'], portrait=SCV,
        voice=dict(voice='en-US-ChristopherNeural', pitch='+0Hz', rate='+6%', fx='highpass=f=250,lowpass=f=3600'),
        profile='Terran compound scientist on the radio; fast, nervous, self-justifying'),
})
SES, IXA, COR = 'Overmind Voice Sessh', 'Brood Queen Ixa', 'Doctor Lenn Corvo'
def objtext(stage, side=''):
    t = "\x04Objectives:\x01\n- Recover the captive Queen from the holding pens." + (" - done" if stage >= 1 else "")
    if stage >= 1: t += "\n- Bring the Queen back to the Home Nest."
    t += "\n- The Home Nest must not fall."
    if side: t += "\n\x03Optional:\x01 Infest the wrecked outpost's Command Center with the Queen." + ('' if side == '+' else side)
    return t
CAST.brief(objtext(0), [
    (SES, "[emotion: cold; pace: slow] The Terrans took Ixa. (0.4) They keep her in cages, beyond the lava."),
    (SES, "[emotion: cold] Grow the brood. (0.3) Cross the fields. *Bring her home*."),
    (COR, "[emotion: nervous; pace: quick] Compound to all posts... (beat) the specimen is agitated. Double the guard on the pens."),
])

# ---------------- triggers ----------------
m.startres = {P1: (400, 100)}
m.hyperplayer = P3
L = m.L
m.T([P1], [m.ALWAYS()],
    CAST.say([(SES, "[emotion: cold] The cooled lava road leads north-east. (0.3) The Terrans guard it at every bend."),
              (SES, "[emotion: patient] Build first. (0.4) A small brood dies on that road.")], L('Home Nest'))
    + [m.ping(L('Holding Pens')), m.obj(objtext(0))])
m.town_ai(P3, 'TMEx', (CX, CY))
# Terran waves toward the Home Nest while the compound's Command Center stands (Command Center cannot morph: no chain)
COMPOUND_UP = [m.cond(3, loc=L('Compound Hall'), player=P3, qty=1, unit=CC, cmp=0)]
K.waves(m, P3, [200, 330, 470, 610, 760, 910], L('Compound Gate'), L('Home Nest'),
        lambda i: [(MARINE, 3 + min(1, i//2))] + ([(FIREBAT, 2)] if i % 2 else []) + ([(VULTURE, 2)] if i >= 3 else []), extra_conds=COMPOUND_UP)
# side objective: announced ~2 minutes in, with the ability hint (only a Queen can infest a damaged Command Center)
m.T([P1], [m.ET(140)],
    m.scene_reveal(L('Outpost'), P1)
    + CAST.say([(SES, "[emotion: interested] Their forward outpost is *broken*. (0.3) Its Command Center burns at less than half strength."),
                (SES, "[emotion: cold] A Queen can infest it. (0.4) Then it is ours: a nest on their own road.")], L('Outpost'))
    + [m.order(P3, MARINE, L('Outpost'), L('Outpost')), m.ping(L('Outpost')), m.setsw(7), m.setsw(9), m.text('\x07OBJECTIVES UPDATED\x01 - press F10 to review.')])
m.T([P1], [m.SW(7), m.cond(2, player=P1, qty=1, unit=ICC, cmp=0)],
    CAST.say([(IXA, "[emotion: savage] Mine now. (beat) Let them *see* what they built for us.")], L('Outpost')) + [m.setsw(8), m.setsw(9)])
m.T([P1], [m.SW(7), m.SW(8, False), m.cond(2, player=P3, qty=0, unit=CC, cmp=10), m.cond(2, player=P1, qty=0, unit=ICC, cmp=10)],
    [m.setsw(6), m.setsw(9), m.text('\x06Optional objective failed:\x01 the outpost Command Center is gone.')])
# the Queen is freed when a brood unit reaches the pens (engine rescue); the way back is chased
m.T([P1], [m.cond(3, loc=L('Holding Pens'), player=P1, qty=1, unit=QUEEN, cmp=0)],
    CAST.say([(IXA, "[emotion: furious; pace: slow] Out. (0.4) *Finally*. Take me home, little ones."),
              (COR, "[emotion: panicked] The specimen is loose! (beat) All units, cut them off on the road!")], L('Holding Pens'))
    + [m.setsw(1), m.setsw(9), m.ping(L('Home Nest'))])
m.T([P3], [m.SW(1)], [m.create(P3, VULTURE, 3, L('Ridge Ambush')), m.create(P3, MARINE, 4, L('Ridge Ambush')), m.order(P3, ANYUNIT, L('Ridge Ambush'), L('Road Ambush'))])
m.T([P3], [m.SW(1), m.cond(3, loc=L('Holding Pens'), player=P1, qty=0, unit=QUEEN, cmp=10)], [m.create(P3, MARINE, 4, L('Road Ambush')), m.create(P3, FIREBAT, 2, L('Road Ambush')), m.order(P3, ANYUNIT, L('Road Ambush'), L('Hive Front'))])
# objective text refresh (switch 9) per (stage, side state)
SIDE = {'': [m.SW(7, False)], '+': [m.SW(7), m.SW(8, False), m.SW(6, False)], ' - done': [m.SW(8)], ' - failed': [m.SW(6)]}
for stage, sc in ((0, [m.SW(1, False)]), (1, [m.SW(1)])):
    for opt, oc in SIDE.items():
        m.T([P1], [m.SW(9)] + sc + oc, [m.obj(objtext(stage, opt)), m.setsw(9, False)])
# victory: the freed Queen is back at the Home Nest (the player cannot morph Queens, so only she counts)
m.T([P1], [m.SW(1), m.cond(3, loc=L('Home Nest'), player=P1, qty=1, unit=QUEEN, cmp=0)],
    CAST.say([(IXA, "[emotion: proud; pace: slow] Home. (0.4) Remember this road, Terrans. *I* will.")], L('Home Nest')) + [m.act(1, flags=0x04)])
# defeat: the Queen dies (before or after the rescue), or every hatchery form at home is gone
for p in (P1, P8):
    m.T([P1], [m.cond(15, player=p, qty=1, unit=QUEEN, cmp=0)], [m.text('\x06Ixa is dead.'), m.wait(2000), m.act(2, flags=0x04)])
m.T([P1], m.target_gone(P1, HATCH, L('Home Nest')), [m.text('\x06The Home Nest has fallen.'), m.wait(2000), m.act(2, flags=0x04)])

import trigsim
exlib.finish(m, SLUG, NAME, 'EXAMPLE: Cinder Run', 'Example mission (VibeModForge): free the captive Queen and bring her home.',
             [trigsim.at(300, 'a zergling reaches the pens', trigsim.move(P1, QUEEN, 'Holding Pens')),
              trigsim.at(700, 'the Queen is home', trigsim.move(P1, QUEEN, 'Home Nest'))])
