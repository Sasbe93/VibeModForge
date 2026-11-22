#!/usr/bin/env python3
"""EXAMPLE (simple, no-base hero squad, Protoss, Twilight): Glass Reef.
Run from the repository root:   python3 tools/bw/examples/ex_glass_reef.py [--no-checks]
Writes output/examples/ex_glass_reef/ (map, design note, voice script, minimap and routes PNG) and runs every check.

STRUCTURE ONLY: copy how this file is built (terrain -> players -> units -> locations -> doodads -> cast -> triggers ->
save -> checks), never its mission design. Every mission invents its own objective, map, start, enemy, story and rewards.

What it demonstrates
  start       no base: a hero squad (hero on its own rescuable slot next to the squad, rescued at once), no workers
  objectives  find and use: reach the Crystal Shrine to wake the Waygate, then reach the Waygate; defeat if the hero dies
  paths       each leg passes two guarded spots, the second leg adds an ambush that springs when the shrine wakes
  side        a rescue whose reward is what it is: the two shrine keepers join (SIDE_OBJECTIVE rescue :: units)
  enemy       a Zerg brood with no base: guard packs only, so there is no town AI to start
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exlib
import sclib
from sclib import *
import missionkit as K

SLUG, NAME = 'ex_glass_reef', 'Ex_Glass_Reef'
P1, P2, P7, P8 = 0, 1, 6, 7
DIRT, HDIRT, MUD, WATER, CRUSH, SUNK, HCRUSH, FLAG, HFLAG, CREV, BASIL = 2, 3, 4, 5, 8, 9, 10, 11, 12, 15, 16   # Twilight ISOM
W, H = 128, 96
AUNVAR = 77                     # Fenix (Zealot) hero unit, renamed

# ---------------- terrain: a reef of glassy ridges and pools between the landing site and the Waygate ----------------
m = Map(W, H, 7, DIRT, seed=7717)
for cx, cy, r in [(30, 74, 8), (58, 58, 9), (84, 40, 7), (100, 70, 6)]: m.blob(cx, cy, r, CRUSH, 0.45)
m.blob(76, 84, 9, HDIRT, 0.35)                                                # a glass ridge south of the track (two ramps)
for cx, cy, r in [(48, 28, 8), (20, 36, 6)]: m.blob(cx, cy, r, CREV, 0.4)      # crevice fields in the north
for cx, cy, r in [(70, 22, 5), (40, 56, 4), (92, 58, 3.5), (122, 54, 3)]: m.blob(cx, cy, r, WATER, 0.4)   # pools
m.path([(0, 44), (28, 43), (56, 41), (80, 45), (95, 49)], 2.6, WATER)           # the reef channel: the north is reached only by the stair road
m.blob(100, 66, 7, FLAG, 0.35); m.blob(112, 14, 6, BASIL, 0.3)      # shrine ruins, Waygate court
m.path([(14, 82), (34, 70), (58, 60), (80, 58), (98, 62)], 1.4, MUD)    # old pilgrim track to the shrine
m.path([(98, 62), (104, 44), (110, 28), (112, 16)], 1.2, MUD)          # stair road to the Waygate
m.edges(DIRT, skip=[(12, 84, 8), (114, 12, 7)], mix=[HDIRT, WATER, CREV])
m.build_terrain()
ti = K.TerrainInfo(m)
ramps = K.auto_ramps(m, ti, 76, 84, 9, angles=[250, 160], need=2)
print('ramps', ramps); assert len(ramps) == 2, 'the south ridge needs two ramps'
ti = K.TerrainInfo(m)

# ---------------- players ----------------
m.ownr = [6, 5, 0, 0, 0, 0, 3, 3] + [0]*4          # human, brood (computer), keepers (rescuable P7), hero slot (rescuable P8)
m.side = [2, 0, 7, 7, 7, 7, 2, 2] + [4]*4
m.colr = [1, 0, 2, 3, 4, 5, 6, 7]; sclib.RENDER_COLR = m.colr
m.forces = [0, 1, 3, 3, 3, 3, 0, 0]; m.forcenames = ['Squad', 'Brood', '', '']; m.forceflags = [2, 0, 0, 0]
g = K.Grid(m)

# ---------------- the squad at the landing site (no base, no workers) ----------------
SX, SY = 16, 80
K.scatter(m, g, ZEALOT, 4, SX, SY, P1, 1.5); K.scatter(m, g, DRAGOON, 2, SX+2, SY-2, P1, 1.2)
m.unit(84, SX+1, SY+2, P1)                          # Observer: detection and scouting
m.rename(AUNVAR, 'Praetor Aunvar', 240, 2, shields=160)
hx, hy = m.hero_spot_near(g, P1); m.unit(AUNVAR, hx, hy, P8); g.occ.add((hx, hy))
m.unit(STARTLOC, SX*32, SY*32, P1, pixel=True)
m.loc('Landing', SX-6, SY-6, SX+7, SY+6)

# ---------------- brood guards along both legs (no base, so no town AI) ----------------
for (cx, cy), grp in [((36, 70), [(ZERGLING, 6)]), ((60, 61), [(HYDRA, 4), (ZERGLING, 4)]),
                      ((84, 73), [(ZERGLING, 4), (HYDRA, 2)]), ((104, 44), [(HYDRA, 3), (ULTRA, 1)]), ((109, 27), [(ZERGLING, 6), (HYDRA, 2)])]:
    for u, n in grp: K.scatter(m, g, u, n, cx, cy, P2, 1.6)
m.loc('Shrine Guard', 56, 57, 65, 66); m.loc('Stair Guard', 100, 40, 109, 49)

# ---------------- shrine, keepers, Waygate ----------------
m.loc('Crystal Shrine', 96, 62, 104, 70)
K.scatter(m, g, HT, 2, 101, 80, P7, 1.0)            # the keepers (high templar) hide in the southern ruins, far from the brood
m.loc('Keepers', 96, 76, 106, 85)
m.loc('Waygate', 108, 10, 117, 18)
K.free_loc(m, g, 'Hollow', 116, 30, 3, 6)          # ambush source: a cave mouth east of the stair road

# ---------------- doodads ----------------
nd, left = K.dress(m, [DIRT, CRUSH, MUD], [HDIRT], forbid=K.auto_forbid(m, [(SX-16, SY-16, SX+17, SY+16)]), counts=(120, 10, 100), seed=33)
print('doodads', nd, 'seams left', left)

# ---------------- cast ----------------
CAST = K.Cast(m, 'gr', {
    'Praetor Aunvar': dict(colour=NAME_COLOURS['yellow'], portrait=AUNVAR,
        voice=dict(voice='en-GB-RyanNeural', pitch='-8Hz', rate='-6%', fx='aecho=0.6:0.5:40:0.25'),
        profile='veteran zealot commander; slow, heavy baritone; speaks in short vows; proud and stubborn'),
    'Adept Selun': dict(colour=NAME_COLOURS['blue'], portrait=84,
        voice=dict(voice='en-US-JennyNeural', pitch='+2Hz', rate='+2%', fx='aecho=0.6:0.5:30:0.2'),
        profile='young templar adept reading the reef through the observer; quick, curious, a little anxious'),
    'Keeper Ishra': dict(colour=NAME_COLOURS['green'], portrait=HT,
        voice=dict(voice='en-AU-NatashaNeural', pitch='-4Hz', rate='-4%', fx='aecho=0.6:0.5:50:0.3'),
        profile='old high templar shrine keeper; dry, quiet, amused by templar pride'),
})
AUN, SEL, ISH = 'Praetor Aunvar', 'Adept Selun', 'Keeper Ishra'
def objtext(stage, opt=''):
    a = "\x04Objectives:\x01\n- Reach the Crystal Shrine with Praetor Aunvar." + (" - done" if stage >= 1 else "")
    if stage >= 1: a += "\n- Reach the Waygate with Praetor Aunvar."
    a += "\n- Praetor Aunvar must not fall."
    if opt: a += "\n\x03Optional:\x01 Find the shrine keepers in the southern ruins." + (opt if opt != '+' else '')
    return a
CAST.brief(objtext(0), [
    (SEL, "[emotion: anxious; pace: quick] The reef is *alive*, Praetor. (0.3) Brood packs on the pilgrim track, more on the stairs."),
    (AUN, "[emotion: stern; pace: slow] Then we walk through them. (0.4) The Waygate sleeps until the shrine wakes it."),
    (SEL, "[emotion: curious] The shrine lies east, past the pools. (beat) The gate is north of it, at the top of the stair road."),
    (AUN, "[emotion: resolute] Shrine first. (0.3) Then home."),
])

# ---------------- triggers ----------------
m.startres = {P1: (0, 0)}
m.hyperplayer = P2
L = m.L
m.T([P1], [m.ALWAYS()],
    CAST.say([(AUN, "[emotion: stern] Squad, on me. (0.3) East along the track, and keep the observer *ahead* of us."),
              (SEL, "[emotion: anxious] Zerglings in the first hollow, Praetor. (beat) Hydralisks near the shrine.")], L('Landing'))
    + [m.ping(L('Crystal Shrine')), m.obj(objtext(0))])
# side objective, announced ~2 minutes in: the keepers' presence is felt before anyone reaches them
m.T([P1], [m.ET(130)],
    m.scene_reveal(L('Keepers'), P1)
    + CAST.say([(SEL, "[emotion: surprised] Praetor... (0.3) I sense *two* minds in the southern ruins. Old keepers, hiding from the brood."),
                (AUN, "[emotion: grudging] Keepers. (0.4) If they will walk with us, they are welcome.")], L('Keepers'))
    + [m.order(P7, HT, L('Keepers'), L('Keepers')), m.ping(L('Keepers')), m.setsw(3), m.setsw(9), m.text('\x07OBJECTIVES UPDATED\x01 - press F10 to review.')])
# the keepers join when the squad reaches them (engine rescue); reward = the keepers themselves
m.T([P1], [m.SW(3), m.cond(3, loc=L('Keepers'), player=P1, qty=1, unit=MEN, cmp=0)],
    CAST.say([(ISH, "[emotion: dry; pace: slow] Templar. (0.4) You took your time. (beat) We will see you to the gate."),
              (AUN, "[emotion: stiff] Your minds are *welcome*, (0.3) Keeper.")], L('Keepers'))
    + [m.setsw(4), m.setsw(9)])
m.T([P1], [m.SW(3), m.SW(4, False), m.cond(2, player=P7, qty=0, unit=MEN, cmp=10)],
    [m.setsw(5), m.setsw(9), m.text('\x06Optional objective failed:\x01 the keepers are lost.')])
# objective text refresh: every event sets switch 9; one trigger per (stage, side state) writes the matching text
SIDE = {'': [m.SW(3, False)], '+': [m.SW(3), m.SW(4, False), m.SW(5, False)], ' - done': [m.SW(4)], ' - failed': [m.SW(5)]}
for stage, sc in ((0, [m.SW(1, False)]), (1, [m.SW(1)])):
    for opt, oc in SIDE.items():
        m.T([P1], [m.SW(9)] + sc + oc, [m.obj(objtext(stage, opt)), m.setsw(9, False)])
# step 1: the shrine wakes when Aunvar reaches it; the brood answers from the Hollow
m.T([P1], [m.cond(3, loc=L('Crystal Shrine'), player=P1, qty=1, unit=AUNVAR, cmp=0)],
    CAST.say([(AUN, "[emotion: reverent; pace: slow] En taro... (0.4) The shrine *answers*."),
              (SEL, "[emotion: alarmed] The Waygate is waking, Praetor. (0.3) And so is the brood. Movement at the cave east of the stairs.")], L('Crystal Shrine'))
    + [m.ping(L('Waygate')), m.setsw(1), m.setsw(9)])
m.T([P2], [m.SW(1)], [m.create(P2, ZERGLING, 4, L('Hollow')), m.create(P2, HYDRA, 2, L('Hollow')), m.order(P2, ANYUNIT, L('Hollow'), L('Stair Guard'))])
# step 2: victory at the Waygate
m.T([P1], [m.SW(1), m.cond(3, loc=L('Waygate'), player=P1, qty=1, unit=AUNVAR, cmp=0)],
    CAST.say([(AUN, "[emotion: weary; pace: slow] The gate holds. (0.4) We go home, all of us.")], L('Waygate'))
    + [m.act(1, flags=0x04)])
# defeat: the hero falls (Deaths covers both owners: before and after the rescue)
for p in (P1, P8):
    m.T([P1], [m.cond(15, player=p, qty=1, unit=AUNVAR, cmp=0)],
        [m.text('\x06Praetor Aunvar has fallen.'), m.wait(2000), m.act(2, flags=0x04)])

# ---------------- save + checks ----------------
import trigsim
exlib.finish(m, SLUG, NAME, 'EXAMPLE: Glass Reef', 'Example mission (VibeModForge): lead a hero squad across the reef.',
             [trigsim.at(100, 'Aunvar reaches the shrine', trigsim.move(P1, AUNVAR, 'Crystal Shrine')),
              trigsim.at(400, 'Aunvar reaches the Waygate', trigsim.move(P1, AUNVAR, 'Waygate'))])
