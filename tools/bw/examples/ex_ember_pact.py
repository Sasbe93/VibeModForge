#!/usr/bin/env python3
"""EXAMPLE (complex, multi-phase: hero squad -> base -> assault, Protoss, Jungle): Ember Pact.
Run from the repository root:   python3 tools/bw/examples/ex_ember_pact.py [--no-checks]
Writes output/examples/ex_ember_pact/ and runs every check.

STRUCTURE ONLY: copy how this file is built, never its mission design. Every mission invents its own objective, map,
start, enemy, story and rewards.

What it demonstrates
  start       no base: a Protoss strike team (START_SETUP no-base); a base arrives only in phase 2
  phase 1     reach a besieged Terran colony through Zerg packs
  phase 2     the colony becomes an ally by trigger (truce before, ALLIANCE_STARTS switch: vision starts exactly at the
              pact), its marshal is an allied hero in his own slot and colour (HERO_SLOT); a dormant Protoss outpost next
              to the colony wakes for the player (REWARD_WHY); objective: destroy the two siege nests (morph chain)
  phase 3     destroy the Brood Hive in the north-east (target_gone over Hatchery -> Lair -> Hive)
  side        protect: keep the colony's Academy standing until the siege breaks; its medics and marines join
              (SIDE_OBJECTIVE protect :: units)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exlib
import sclib
from sclib import *
import missionkit as K

SLUG, NAME = 'ex_ember_pact', 'Ex_Ember_Pact'
P1, P2, P3, P4, P12 = 0, 1, 2, 3, 11
DIRT, HDIRT, MUD, WATER, JUNGLE, RJUNGLE, HJUNGLE, RUINS, HRUINS, ROCKY, TEMPLE_ = 2, 3, 4, 5, 8, 9, 10, 11, 12, 15, 16   # Jungle ISOM
W, H = 128, 128
QUILL = 20                      # Jim Raynor (Marine) hero unit, renamed: the colony's marshal (allied hero, own slot P4)
OBS = 84

# ---------------- terrain: landing in the south-west, the fort in the centre, the brood in the north-east ----------------
m = Map(W, H, 4, DIRT, seed=8805)
for cx, cy, r in [(24, 90, 8), (90, 90, 8), (40, 30, 8), (100, 56, 7)]: m.blob(cx, cy, r, JUNGLE, 0.45)
for cx, cy, r in [(50, 104, 6), (76, 40, 6), (30, 60, 5)]: m.blob(cx, cy, r, RJUNGLE, 0.4)
for cx, cy, r in [(40, 84, 5), (82, 72, 6), (60, 30, 5), (100, 100, 5), (20, 44, 5)]: m.blob(cx, cy, r, WATER, 0.5)
m.blob(64, 64, 9, HDIRT, 0.3)                                       # the fort's plateau
m.path([(14, 116), (30, 100), (46, 80)], 1.2, RUINS); m.path([(76, 52), (92, 36), (104, 22)], 1.2, RUINS)
OX, OY = 40, 64                                                     # the dormant Protoss outpost west of the fort
OPLAN = K.mineral_plan(OX, OY, 'left', 7, form='column'); K.paint_back(m, OPLAN, WATER)
BX, BY = 108, 12
BPLAN = K.mineral_plan(BX, BY, 'upright', 8, form='corner'); K.paint_back(m, BPLAN, WATER)
m.edges(DIRT, skip=[(116, 6, 10)], mix=[WATER, HDIRT, JUNGLE])
m.build_terrain()
ti = K.TerrainInfo(m)
ramps = K.auto_ramps(m, ti, 64, 64, 9, angles=[200, 300, 30], need=2)
print('ramps', ramps); assert len(ramps) >= 1, 'the fort plateau needs a ramp'
ti = K.TerrainInfo(m)

# ---------------- players ----------------
m.ownr = [6, 5, 5, 5, 0, 0, 0, 0] + [0]*4          # human Protoss, Zerg (P2), colony (P3), Marshal Quill (P4, own slot)
m.side = [2, 0, 1, 1, 7, 7, 7, 7] + [4]*4
m.colr = [9, 5, 2, 7, 4, 3, 6, 0]; sclib.RENDER_COLR = m.colr     # teal Protoss, purple brood, blue colony, white marshal
m.forces = [0, 1, 2, 2, 3, 3, 3, 3]; m.forcenames = ['Strike Team', 'Brood', 'Fort Wren', '']; m.forceflags = [0, 0, 0, 0]
m.alliance_switch = {P3: 2, P4: 2}                 # truce at the start, real alliance (and vision) at the pact
g = K.Grid(m)

# ---------------- the strike team (no base) ----------------
SX, SY = 14, 114
m.unit(STARTLOC, SX*32+16, SY*32+16, P1, pixel=True); g = K.Grid(m)
for u, n, dx, dy in [(ZEALOT, 4, 0, 0), (DRAGOON, 3, 3, -2), (HT, 2, -1, -3), (OBS, 1, 2, 2)]: K.scatter(m, g, u, n, SX+dx, SY+dy, P1, 1.2)

# ---------------- the dormant outpost (neutral until the pact) ----------------
K.res_base(m, g, ti, OX, OY, 'left', 7, [1500, 1250, 1500], 5000, P12, NEXUS, plan=OPLAN)
TO = K.Town(m, g, P12, 'protoss')
for cx, cy in [(OX+7, OY-3), (OX+7, OY+5)]: TO.put(PYLON, cx, cy, 3)
TO.put(GATEWAY, OX+9, OY+1, 4)
K.scatter(m, g, PROBE, 4, OX+5, OY+1, P12, 1.0)
m.loc('Old Outpost', OX-4, OY-6, OX+14, OY+9)

# ---------------- Fort Wren on the plateau (colony P3, town AI) and Marshal Quill (P4) ----------------
FX, FY = 61, 65
TC = K.Town(m, g, P3, 'terran')
m.unit(CC, FX, FY, P3); g.add_raw(m.units[-1]); m.unit(STARTLOC, FX*32+64, FY*32+48, P3, pixel=True)
for b, cx, cy in [(BARRACKS, FX-6, FY-3), (SUPPLY, FX-6, FY+4), (ACADEMY, FX+5, FY+3)]: TC.put(b, cx, cy, 4)
for cx, cy in [(FX-4, FY+5), (FX+2, FY+7)]: TC.put(BUNKER, cx, cy, 3)
K.scatter(m, g, MARINE, 5, FX-1, FY+4, P3, 1.2)
m.rename(QUILL, 'Marshal Quill', 260, 1)
K.scatter(m, g, QUILL, 1, FX+1, FY+3, P4, 0.4)
m.loc('Fort Wren', FX-8, FY-6, FX+10, FY+10)
m.loc('Fort Academy', FX+3, FY+1, FX+10, FY+6)

# ---------------- the brood: two siege nests by the fort and the Brood Hive (town AIs) ----------------
TZ = K.Town(m, g, P2, 'zerg')
NESTS = [('West Nest', 54, 44), ('East Nest', 88, 56)]
for name, nx, ny in NESTS:
    m.unit(HATCH, nx, ny, P2); g.add_raw(m.units[-1]); TZ.note(HATCH, nx, ny)
    for cx, cy in [(nx-3, ny+4), (nx+5, ny+3)]: TZ.put(SUNKEN, cx, cy, 3)
    K.scatter(m, g, HYDRA, 3, nx+1, ny+5, P2, 1.0); K.scatter(m, g, ZERGLING, 4, nx-2, ny+2, P2, 1.0)
    m.loc(name, nx-2, ny-2, nx+6, ny+5)
K.res_base(m, g, ti, BX, BY, 'upright', 8, [3000, 2500, 3500, 4000], 12000, P2, HIVE, plan=BPLAN); TZ.note(HIVE, BX, BY)
for b, cx, cy in [(POOL, BX-8, BY+2), (HYDEN, BX-6, BY+8), (EVO, BX-11, BY+6)]: TZ.put(b, cx, cy, 5)
for cx, cy in [(BX-12, BY+14), (BX-4, BY+16)]: TZ.put(SUNKEN, cx, cy, 4)
TZ.workers(DRONE, 8, BX-2, BX+6, BY+4, BY+7)
K.scatter(m, g, HYDRA, 6, BX-6, BY+14, P2, 1.6); K.scatter(m, g, ULTRA, 1, BX-2, BY+12, P2, 0.5)
for i in range(3): m.unit(OVERLORD, BX-4+i*4, BY-2, P2)
m.unit(STARTLOC, BX*32+64, BY*32+48, P2, pixel=True)
m.loc('Brood Hive', BX-1, BY-1, BX+5, BY+4)
# packs on the way to the fort and to the hive
for (cx, cy), grp in [((24, 100), [(ZERGLING, 4)]), ((34, 88), [(HYDRA, 2), (ZERGLING, 2)]), ((48, 78), [(ZERGLING, 4), (HYDRA, 1)]),
                      ((80, 46), [(HYDRA, 3)]), ((92, 34), [(ZERGLING, 4), (HYDRA, 2)]), ((100, 26), [(HYDRA, 2), (LURKER, 1)]), ((72, 50), [(ZERGLING, 4)])]:
    for u, n in grp: K.scatter(m, g, u, n, cx, cy, P2, 1.3)

# ---------------- locations ----------------
m.loc('Landing', SX-6, SY-8, SX+8, SY+6)
K.free_loc(m, g, 'Nest Gate W', 54, 54, 3, 6)
K.free_loc(m, g, 'Nest Gate E', 78, 62, 3, 6)
K.free_loc(m, g, 'Hive Gate', BX-14, BY+20, 3, 6)

# ---------------- doodads ----------------
nd, left = K.dress(m, [DIRT, JUNGLE, RJUNGLE, MUD], [HDIRT], forbid=K.auto_forbid(m, [(OX-12, OY-12, OX+16, OY+12), (BX-20, BY-6, BX+14, BY+22), (52, 52, 76, 76)]),
                   counts=(130, 10, 110), seed=91)
print('doodads', nd, 'seams left', left)

# ---------------- cast ----------------
CAST = K.Cast(m, 'ep', {
    'Executor Nhal': dict(colour=NAME_COLOURS['yellow'], portrait=ZEALOT,
        voice=dict(voice='en-GB-RyanNeural', pitch='-6Hz', rate='-4%', fx='aecho=0.6:0.5:40:0.3'),
        profile='Protoss executor leading the strike team; measured, proud, learning to trust humans'),
    'Marshal Quill': dict(colour=NAME_COLOURS['blue'], portrait=QUILL,
        voice=dict(voice='en-US-GuyNeural', pitch='-2Hz', rate='+2%', fx='highpass=f=200,lowpass=f=4000'),
        profile='colony marshal; tired, wry, stubborn; has held the fort for weeks'),
    'Adept Seris': dict(colour=NAME_COLOURS['green'], portrait=HT,
        voice=dict(voice='en-US-JennyNeural', pitch='+0Hz', rate='+2%', fx='aecho=0.6:0.5:30:0.2'),
        profile='young templar adept; quick, curious, senses the dormant outpost'),
})
NHA, QUI, SER = 'Executor Nhal', 'Marshal Quill', 'Adept Seris'
def objtext(stage, side=''):
    t = "\x04Objectives:\x01\n- Reach Fort Wren with the strike team." + (" - done" if stage >= 1 else "")
    if stage == 0: t += "\n- The strike team must not be wiped out."
    if stage >= 1: t += "\n- Destroy the West Nest and the East Nest." + (" - done" if stage >= 2 else "")
    if stage >= 2: t += "\n- Destroy the Brood Hive in the north-east." + (" - done" if stage >= 3 else "")
    if stage >= 1: t += "\n- Marshal Quill must not fall."
    if side: t += "\n\x03Optional:\x01 Keep the colony's Academy standing until both nests fall." + ('' if side == '+' else side)
    return t
CAST.brief(objtext(0), [
    (NHA, "[emotion: measured; pace: slow] A human fort holds out in the centre of this jungle. (0.3) The brood besieges it."),
    (SER, "[emotion: curious] And beside it, Executor... (beat) something of *ours*. Asleep."),
    (NHA, "[emotion: resolute] Then we go to the humans first. *Quickly*."),
])

# ---------------- triggers ----------------
m.startres = {P1: (0, 0)}
m.tech = K.tech_level('Protoss', 'late', drop={169, 170, 71, 72})   # late chapter: everything but Fleet Beacon/Arbiter Tribunal (Carrier, Arbiter)
m.hyperplayer = P2
L = m.L
# truce at the start (no vision: alliance_switch), the same for the marshal's slot
m.T([P1], [m.ALWAYS()], [m.ally(P3, 1), m.ally(P4, 1)])
m.T([P3], [m.ALWAYS()], [m.ally(P1, 1), m.ally(P4, 1)])
m.T([P4], [m.ALWAYS()], [m.ally(P1, 1), m.ally(P3, 1)])
m.T([P1], [m.ALWAYS()],
    CAST.say([(NHA, "[emotion: measured] North-east, through the ruins. (0.3) Stay together."),
              (SER, "[emotion: alert] Brood scents on the old road. *Many*.")], L('Landing'))
    + [m.ping(L('Fort Wren')), m.obj(objtext(0))])
m.town_ai(P2, 'ZMEx', (BX, BY))
for name, nx, ny in NESTS: m.town_ai(P2, 'ZARx', (nx, ny), area=(nx-8, ny-6, nx+12, ny+9), name='Town ' + name)
m.town_ai(P3, 'TMEx', (FX, FY))
# the siege: waves from the nests at the fort while they stand (morph chain)
for k, (name, nx, ny) in enumerate(NESTS):
    gate = 'Nest Gate W' if k == 0 else 'Nest Gate E'
    K.waves(m, P2, [150 + 60*k, 330 + 60*k, 510 + 60*k, 690 + 60*k, 870 + 60*k], L(gate), L('Fort Wren'),
            lambda i: [(ZERGLING, 4), (HYDRA, 1 + min(3, i))], alts=m.target_stands(P2, HATCH, L(name)), switch0=100 + 10*k)
# phase 2: the strike team reaches the fort -> the pact (switch 2): alliance with vision, the outpost wakes (REWARD_WHY)
m.T([P1], [m.cond(3, loc=L('Fort Wren'), player=P1, qty=2, unit=MEN, cmp=0)],
    CAST.say([(QUI, "[emotion: wry; pace: slow] Protoss. (0.3) Didn't think I'd be glad to see *you*."),
              (NHA, "[emotion: formal] Your enemy is ours, Marshal. (0.3) We fight together.")], L('Fort Wren'))
    + [m.setsw(2), m.setsw(9)])
m.T([P1], [m.SW(2)], [m.ally(P3, 2), m.ally(P4, 2)])
m.T([P3], [m.SW(2)], [m.ally(P1, 2), m.ally(P4, 2)])
m.T([P4], [m.SW(2)], [m.ally(P1, 2), m.ally(P3, 2)])
m.T([P1], [m.SW(2)],
    CAST.say([(SER, "[emotion: awed] The outpost west of the fort... (beat) it answers us, Executor!")], L('Old Outpost'))
    + [m.act(48, loc=L('Old Outpost'), player=P12, unit=ANYUNIT, mod=0, num=P1, flags=0x04), m.ping(L('Old Outpost'))])
# side objective: keep the Academy standing until both nests are gone; its medics and marines join (REWARD_WHY)
m.T([P1], [m.SW(2), m.cond(3, loc=L('Fort Academy'), player=P1, qty=1, unit=MEN, cmp=0)],
    CAST.say([(QUI, "[emotion: worried] Our Academy trains the medics. (0.3) Keep it standing and they are *yours*.")], L('Fort Academy'))
    + [m.ping(L('Fort Academy')), m.setsw(7), m.setsw(9), m.text('\x07OBJECTIVES UPDATED\x01 - press F10 to review.')])
NESTS_GONE = []
for name, nx, ny in NESTS: NESTS_GONE += m.target_gone(P2, HATCH, L(name))
m.T([P1], [m.SW(2)] + NESTS_GONE, CAST.say([(NHA, "[emotion: grim] The siege is broken. (0.3) Now the hive itself.")], L('Fort Wren')) + [m.setsw(3), m.setsw(9), m.ping(L('Brood Hive'))])
m.T([P1], [m.SW(7), m.SW(3), m.cond(3, loc=L('Fort Academy'), player=P3, qty=1, unit=ACADEMY, cmp=0)],
    CAST.say([(QUI, "[emotion: grateful] Academy's still standing. (0.3) Take my medics, and a squad to guard them.")], L('Fort Academy'))
    + [m.create(P1, MEDIC, 4, L('Fort Academy')), m.create(P1, MARINE, 4, L('Fort Academy')), m.setsw(8), m.setsw(9)])
m.T([P1], [m.SW(7), m.SW(8, False), m.cond(3, loc=L('Fort Academy'), player=P3, qty=0, unit=ACADEMY, cmp=10)],
    [m.setsw(6), m.setsw(9), m.text('\x06Optional objective failed:\x01 the Academy has fallen.')])
# objective text refresh (switch 9)
SIDE = {'': [m.SW(7, False)], '+': [m.SW(7), m.SW(8, False), m.SW(6, False)], ' - done': [m.SW(8)], ' - failed': [m.SW(6), m.SW(8, False)]}
for stage, sc in ((0, [m.SW(2, False)]), (1, [m.SW(2), m.SW(3, False)]), (2, [m.SW(3)])):
    for opt, oc in SIDE.items():
        m.T([P1], [m.SW(9)] + sc + oc, [m.obj(objtext(stage, opt)), m.setsw(9, False)])
# phase 3 victory: the Brood Hive (any form of the chain) is gone
m.T([P1], [m.SW(3)] + m.target_gone(P2, HATCH, L('Brood Hive')),
    [m.obj(objtext(3))] + CAST.say([(QUI, "[emotion: relieved] That's the hive. (0.4) Fort Wren owes you, Executor.")], L('Fort Wren')) + [m.act(1, flags=0x04)])
# defeats: the strike team dies before the pact, or the marshal falls
m.T([P1], [m.SW(2, False), m.cond(2, player=P1, qty=0, unit=MEN, cmp=10)], [m.text('\x06The strike team is lost.'), m.wait(2000), m.act(2, flags=0x04)])
m.T([P1], [m.cond(15, player=P4, qty=1, unit=QUILL, cmp=0)], [m.text('\x06Marshal Quill has fallen. Fort Wren is lost.'), m.wait(2000), m.act(2, flags=0x04)])

import trigsim
exlib.finish(m, SLUG, NAME, 'EXAMPLE: Ember Pact', 'Example mission (VibeModForge): reach the besieged fort, win an ally, break the siege, burn the hive.',
             [trigsim.at(240, 'the strike team reaches the fort', trigsim.move(P1, ZEALOT, 'Fort Wren', 2)),
              trigsim.at(800, 'both siege nests fall', lambda s: [trigsim.kill(P2, HATCH, n)(s) for n, _, _ in NESTS]),
              trigsim.at(1500, 'the Brood Hive falls', trigsim.kill(P2, HIVE, 'Brood Hive'))])
