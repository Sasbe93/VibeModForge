#!/usr/bin/env python3
"""EXAMPLE (medium, escort with ambushes, Protoss, Jungle): Thorn Road.
Run from the repository root:   python3 tools/bw/examples/ex_thorn_road.py [--no-checks]
Writes output/examples/ex_thorn_road/ and runs every check.

STRUCTURE ONLY: copy how this file is built, never its mission design. Every mission invents its own objective, map,
start, enemy, story and rewards.

What it demonstrates
  start       small base (Nexus, Gateway, Forge, Cybernetics Core): the player readies an escort before the caravan leaves
  objective   escort: an allied archivist (own hero slot and colour, HERO_SLOT) and his bearers walk a long jungle road in
              legs; each leg starts when the archivist reaches the last waypoint, every leg springs an ambush
  ally        allied computer players from the first second (ALLIANCE_STARTS start), vision both ways from that moment
  enemy       a Terran base running its town AI, road guards, and three triggered ambushes along the route
  side        destroy the listening post that spots the caravan: its reward is information, the ridge ambush never comes
              (SIDE_OBJECTIVE destroy :: info)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exlib
import sclib
from sclib import *
import missionkit as K

SLUG, NAME = 'ex_thorn_road', 'Ex_Thorn_Road'
P1, P2, P3, P4 = 0, 1, 2, 3
DIRT, HDIRT, MUD, WATER, JUNGLE, RJUNGLE, HJUNGLE, RUINS, HRUINS, ROCKY, TEMPLE_ = 2, 3, 4, 5, 8, 9, 10, 11, 12, 15, 16   # Jungle ISOM
W, H = 128, 96
TELAR = 87                      # Aldaris hero unit, renamed: the archivist (allied computer hero in his own slot)
CYBER = 164

# ---------------- terrain: a river, a temple plateau and a ridge between the base and the conduit ----------------
m = Map(W, H, 4, DIRT, seed=4401)
for cx, cy, r in [(36, 52, 8), (88, 66, 8), (60, 18, 7), (20, 30, 7)]: m.blob(cx, cy, r, JUNGLE, 0.45)
for cx, cy, r in [(46, 84, 6), (100, 44, 5), (80, 14, 5)]: m.blob(cx, cy, r, RJUNGLE, 0.4)
for cx, cy, r in [(64, 76, 5), (112, 30, 4)]: m.blob(cx, cy, r, MUD, 0.4)
m.path([(46, 0), (48, 24), (44, 46), (50, 58)], 2.6, WATER)        # the river, north part
m.path([(54, 68), (58, 82), (54, 95)], 2.6, WATER)                  # the river, south part (the ford lies between)
m.blob(76, 46, 8, HDIRT, 0.3)                                       # the temple plateau (one stair: a Terran lookout above the road)
m.path([(96, 40), (104, 50), (110, 62)], 2.0, WATER)                # a creek east of the plateau
m.path([(28, 72), (52, 63), (64, 55)], 1.2, RUINS); m.path([(88, 39), (100, 26), (116, 14)], 1.2, RUINS)   # the old road (it climbs over the plateau)
HX, HY = 12, 78
PPLAN = K.mineral_plan(HX, HY, 'left', 8, form='column'); K.paint_back(m, PPLAN, WATER)
CX, CY = 108, 78
CPLAN = K.mineral_plan(CX, CY, 'right', 8, form='column'); K.paint_back(m, CPLAN, WATER)
m.edges(DIRT, skip=[(6, 80, 8), (122, 80, 8)], mix=[WATER, HDIRT, JUNGLE])
m.blob(122, 87, 3, WATER, 0.2)                                      # close the back of the Dominion mineral line
m.build_terrain()
ti = K.TerrainInfo(m)
ramps = K.auto_ramps(m, ti, 76, 46, 8, angles=[210, 30], need=1)
print('ramps', ramps); assert len(ramps) == 1, 'the temple plateau needs its stair'
ti = K.TerrainInfo(m)

# ---------------- players ----------------
m.ownr = [6, 5, 5, 5, 0, 0, 0, 0] + [0]*4          # human Protoss, Terran (P2), caravan (P3), archivist hero slot (P4)
m.side = [2, 1, 2, 2, 7, 7, 7, 7] + [4]*4
m.colr = [9, 0, 5, 4, 2, 3, 6, 7]; sclib.RENDER_COLR = m.colr     # teal player, red Terrans, brown caravan, purple archivist
m.forces = [0, 1, 0, 0, 3, 3, 3, 3]; m.forcenames = ['Templar', 'Dominion', '', '']; m.forceflags = [0, 0, 0, 0]
g = K.Grid(m)

# ---------------- the player's small base ----------------
m.unit(STARTLOC, HX*32+64, HY*32+48, P1, pixel=True); g = K.Grid(m)
K.res_base(m, g, ti, HX, HY, 'left', 8, [1500, 1250, 1500, 1000], 5000, P1, NEXUS, plan=PPLAN)
TP = K.Town(m, g, P1, 'protoss')
for cx, cy in [(HX+7, HY-4), (HX+7, HY+5)]: TP.put(PYLON, cx, cy, 3)
TP.put(GATEWAY, HX+10, HY-1, 5); TP.put(FORGE := 166, HX+4, HY+8, 5); TP.put(CYBER, HX+11, HY+5, 5)
TP.workers(PROBE, 6, HX-3, HX, HY-1, HY+4)
K.scatter(m, g, ZEALOT, 4, HX+16, HY-3, P1, 1.4); K.scatter(m, g, DRAGOON, 2, HX+17, HY+1, P1, 1.0)

# ---------------- the caravan (P3) and the archivist (P4, own slot) at the camp ----------------
m.rename(TELAR, 'Archivist Telar', 180, 1, shields=120)
K.free_loc(m, g, 'Caravan Camp', 30, 70, 3, 6)
K.scatter(m, g, HT, 2, 31, 71, P3, 1.0); K.scatter(m, g, ZEALOT, 2, 29, 69, P3, 0.8)
K.scatter(m, g, TELAR, 1, 30, 70, P4, 0.4)

# ---------------- the Terran base (town AI on the Command Center) ----------------
TT = K.Town(m, g, P2, 'terran')
K.res_base(m, g, ti, CX, CY, 'right', 8, [3000, 2500, 3500, 4000], 12000, P2, CC, plan=CPLAN)
for b, cx, cy in [(BARRACKS, CX-8, CY-2), (BARRACKS, CX-8, CY+4), (FACTORY, CX-3, CY-7), (SUPPLY, CX-12, CY+8), (SUPPLY, CX+1, CY+9), (EBAY, CX-13, CY-4)]: TT.put(b, cx, cy, 5)
for cx, cy in [(CX-16, CY+1), (CX-10, CY-11)]: TT.put(BUNKER, cx, cy, 4)
TT.workers(SCV, 8, CX+5, CX+8, CY-1, CY+4)
K.scatter(m, g, MARINE, 6, CX-12, CY-6, P2, 1.6); K.scatter(m, g, TANK, 1, CX-6, CY-9, P2, 0.5)
m.unit(STARTLOC, CX*32+64, CY*32+48, P2, pixel=True)
m.loc('Dominion Hall', CX-1, CY-1, CX+5, CY+4)
# the listening post north of the road: Academy (cannot lift) and a bunker; while it stands the ridge ambush comes
LX, LY = 62, 30
TT.put(ACADEMY, LX, LY, 3); TT.put(BUNKER, LX+5, LY+3, 3); TT.put(TURRET, LX-3, LY+3, 3)
K.scatter(m, g, MARINE, 3, LX+3, LY+6, P2, 1.0)
m.loc('Listening Post', LX-5, LY-3, LX+8, LY+7)
# road guards
for (cx, cy), grp in [((44, 66), [(MARINE, 3)]), ((66, 56), [(FIREBAT, 2), (MARINE, 2)]), ((90, 34), [(MARINE, 3), (GOLIATH, 1)]), ((56, 44), [(MARINE, 2), (FIREBAT, 2)]), ((38, 58), [(MARINE, 3)]), ((70, 36), [(MARINE, 2), (VULTURE, 1)]), ((108, 20), [(VULTURE, 2), (MARINE, 2)])]:
    for u, n in grp: K.scatter(m, g, u, n, cx, cy, P2, 1.3)
# the lookout on the temple plateau: a siege tank and marines above the road (one stair up)
K.scatter(m, g, TANK, 1, 78, 45, P2, 0.5); K.scatter(m, g, MARINE, 2, 76, 47, P2, 0.8)

# ---------------- route locations ----------------
WP = ['Caravan Camp']
for name, x, y in [('Ford', 52, 63), ('Temple Stair', 70, 50), ('Ridge Foot', 86, 38), ('Ridge Pass', 100, 26)]:
    K.free_loc(m, g, name, x, y, 3, 6); WP.append(name)
m.loc('Warp Conduit', 112, 8, 122, 18); WP.append('Warp Conduit')
for name, x, y in [('Ford Ambush', 58, 72), ('Temple Ambush', 78, 60), ('Ridge Ambush', 96, 14)]: K.free_loc(m, g, name, x, y, 3, 6)
m.loc('Home Base', HX-4, HY-8, HX+20, HY+10)

# ---------------- doodads ----------------
nd, left = K.dress(m, [DIRT, JUNGLE, RJUNGLE, MUD], [HDIRT], forbid=K.auto_forbid(m, [(HX-12, HY-14, HX+22, HY+14), (CX-18, CY-14, CX+12, CY+14), (110, 6, 124, 20)]),
                   counts=(110, 8, 90), seed=53)
print('doodads', nd, 'seams left', left)

# ---------------- cast ----------------
CAST = K.Cast(m, 'tr', {
    'Archivist Telar': dict(colour=NAME_COLOURS['blue'], portrait=TELAR,
        voice=dict(voice='en-GB-RyanNeural', pitch='+4Hz', rate='-2%', fx='aecho=0.6:0.5:40:0.25'),
        profile='old archivist; precise, fussy, brave only when the records are at stake'),
    'Exarch Vael': dict(colour=NAME_COLOURS['yellow'], portrait=ZEALOT,
        voice=dict(voice='en-US-GuyNeural', pitch='-6Hz', rate='-4%', fx='aecho=0.6:0.5:40:0.3'),
        profile='templar exarch commanding the escort; calm, dry, protective'),
    'Captain Ruiz Hale': dict(colour=NAME_COLOURS['white'], portrait=MARINE,
        voice=dict(voice='en-US-ChristopherNeural', pitch='-2Hz', rate='+4%', fx='highpass=f=250,lowpass=f=3600'),
        profile='Dominion captain on the radio; smug, impatient, sure of his ambushes'),
})
TEL, VAE, HAL = 'Archivist Telar', 'Exarch Vael', 'Captain Ruiz Hale'
def objtext(stage, side=''):
    t = "\x04Objectives:\x01\n- Escort Archivist Telar to the Warp Conduit." + (" - done" if stage >= 1 else "")
    t += "\n- Archivist Telar must not fall."
    if side: t += "\n\x03Optional:\x01 Destroy the Terran listening post north of the road." + ('' if side == '+' else side)
    return t
CAST.brief(objtext(0), [
    (VAE, "[emotion: calm; pace: slow] The codex must reach the conduit, Archivist. (0.3) The Dominion holds the road."),
    (TEL, "[emotion: fussy] Then we walk it *carefully*. (0.3) These records are older than their whole species."),
    (HAL, "[emotion: smug; pace: quick] Hale to all squads. (beat) A Protoss caravan is on the old road. Let them come."),
])

# ---------------- triggers ----------------
m.startres = {P1: (300, 150)}
m.hyperplayer = P2
L = m.L
# allied from the first second, vision both ways (sclib adds the vision to the alliance triggers)
m.T([P1], [m.ALWAYS()], [m.ally(P3, 1), m.ally(P4, 1)])
m.T([P3], [m.ALWAYS()], [m.ally(P1, 1), m.ally(P4, 1)])
m.T([P4], [m.ALWAYS()], [m.ally(P1, 1), m.ally(P3, 1)])
m.T([P1], [m.ALWAYS()],
    CAST.say([(VAE, "[emotion: calm] The caravan leaves the camp in two minutes. (0.3) Ready the escort."),
              (TEL, "[emotion: anxious] Two minutes. (beat) I will count them.")], L('Home Base'))
    + [m.ping(L('Caravan Camp')), m.obj(objtext(0))])
m.town_ai(P2, 'TMEx', (CX, CY))
# the caravan walks in legs; each leg starts when the archivist reaches the last waypoint
m.T([P1], [m.ET(120)],
    CAST.say([(TEL, "[emotion: resolute] We go. (0.3) Stay close, Exarch.")], L('Caravan Camp'))
    + [m.order(P4, TELAR, L('Caravan Camp'), L('Ford')), m.order(P3, ANYUNIT, L('Caravan Camp'), L('Ford'))])
POST_UP = [m.cond(3, loc=L('Listening Post'), player=P2, qty=1, unit=ACADEMY, cmp=0)]
AMBUSH = {'Ford': ('Ford Ambush', [(MARINE, 4), (FIREBAT, 2)], []),
          'Temple Stair': ('Temple Ambush', [(VULTURE, 3), (MARINE, 4)], []),
          'Ridge Foot': ('Ridge Ambush', [(MARINE, 4), (GOLIATH, 2)], POST_UP)}
for a, b in zip(WP[1:-1], WP[2:]):
    m.T([P1], [m.cond(3, loc=L(a), player=P4, qty=1, unit=TELAR, cmp=0)],
        [m.order(P4, TELAR, L(a), L(b)), m.order(P3, ANYUNIT, L(a), L(b))])
    amb, grp, extra = AMBUSH.get(a, (None, None, None))
    if amb:
        m.T([P2], [m.cond(3, loc=L(a), player=P4, qty=1, unit=TELAR, cmp=0)] + extra,
            [m.create(P2, u, n, L(amb)) for u, n in grp] + [m.order(P2, ANYUNIT, L(amb), L(b), o=3)])
m.T([P1], [m.cond(3, loc=L('Ford'), player=P4, qty=1, unit=TELAR, cmp=0)],
    CAST.say([(HAL, "[emotion: smug] There they are. (beat) Squad two, hit the ford.")], L('Ford Ambush')))
# side objective: announced ~2.5 minutes in; the listening post calls the ridge ambush while it stands
m.T([P1], [m.ET(150)],
    m.scene_reveal(L('Listening Post'), P1)
    + CAST.say([(VAE, "[emotion: wary] A Dominion listening post, north of the road. (0.3) It reports every step we take."),
                (VAE, "[emotion: calm] *Silence* it, and the ridge will be quiet.")], L('Listening Post'))
    + [m.order(P2, MARINE, L('Listening Post'), L('Listening Post')), m.ping(L('Listening Post')), m.setsw(7), m.setsw(9), m.text('\x07OBJECTIVES UPDATED\x01 - press F10 to review.')])
m.T([P1], [m.SW(7), m.cond(3, loc=L('Listening Post'), player=P2, qty=0, unit=ACADEMY, cmp=10)],
    CAST.say([(HAL, "[emotion: annoyed] Post, report. (beat) Post? ...Blast it, we are blind on the ridge.")], L('Listening Post')) + [m.setsw(8), m.setsw(9)])
m.T([P1], [m.SW(7), m.SW(8, False), m.cond(3, loc=L('Ridge Foot'), player=P4, qty=1, unit=TELAR, cmp=0)],
    [m.setsw(6), m.setsw(9), m.text('\x06Optional objective failed:\x01 the caravan reached the ridge while the post still watched.')])
# objective text refresh (switch 9)
SIDE = {'': [m.SW(7, False)], '+': [m.SW(7), m.SW(8, False), m.SW(6, False)], ' - done': [m.SW(8)], ' - failed': [m.SW(6), m.SW(8, False)]}
for opt, oc in SIDE.items():
    m.T([P1], [m.SW(9)] + oc, [m.obj(objtext(0, opt)), m.setsw(9, False)])
# victory: the archivist reaches the conduit
m.T([P1], [m.cond(3, loc=L('Warp Conduit'), player=P4, qty=1, unit=TELAR, cmp=0)],
    [m.obj(objtext(1))] + CAST.say([(TEL, "[emotion: relieved; pace: slow] The conduit. (0.4) Every record, intact. Thank you, Exarch.")], L('Warp Conduit')) + [m.act(1, flags=0x04)])
# defeat: the archivist dies
m.T([P1], [m.cond(15, player=P4, qty=1, unit=TELAR, cmp=0)], [m.text('\x06Archivist Telar has fallen. The codex is lost.'), m.wait(2000), m.act(2, flags=0x04)])

import trigsim
exlib.finish(m, SLUG, NAME, 'EXAMPLE: Thorn Road', 'Example mission (VibeModForge): escort the archivist along the old road.',
             [trigsim.at(900, 'the archivist reaches the conduit', trigsim.move(P4, TELAR, 'Warp Conduit'))])
