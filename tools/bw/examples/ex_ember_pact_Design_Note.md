# EXAMPLE: Ember Pact - Design Note

EXAMPLE mission (StarCraft: Brood War, .scx, Jungle 128x128), built by `tools/bw/examples/ex_ember_pact.py`.
**Structure only:** copy how this note is organised (sections, design lines), never the mission design (objective, map
layout, start setup, enemy, story, rewards). Every mission invents its own; see docs/bw-example-missions.md.
Complexity: complex (three phases). Placeholder story.

## Campaign outline
Example campaign "Jungle Accord" (placeholder, 4 chapters): 1) a Protoss strike team lands on a jungle world, 2) this
mission: it finds a besieged human fort, makes a pact and breaks the siege, 3) the pact is tested when the brood
returns, 4) humans and Protoss leave the world together.
TONE: hopeful :: comic characters allowed no :: a proud executor, a tired human marshal and a curious young adept

## Story
A Protoss strike team lands without a base. A human colony, Fort Wren, holds out against a brood siege in the centre of
the jungle, and beside it sleeps an old Protoss outpost. Reaching the fort seals a pact: the marshal becomes an ally, the
outpost wakes for the Protoss, and together they break the siege and burn the Brood Hive.

## Objectives
- Phase 1: Reach Fort Wren with the strike team. Defeat: the strike team is wiped out before the pact.
- Phase 2: Destroy the West Nest and the East Nest (both siege Hatcheries, any form of the morph chain). Defeat: Marshal Quill dies.
- Phase 3: Destroy the Brood Hive in the north-east (any form of the chain). Defeat: Marshal Quill dies.
- Optional (from the pact): keep the colony's Academy standing until both nests fall.

## Side objectives
SIDE_OBJECTIVE: Keep the colony's Academy standing :: protect :: units

## Rewards
REWARD_WHY: Reach Fort Wren :: the dormant Protoss outpost (Nexus, Gateway, two Pylons, four Probes) joins the player :: the outpost standing west of the fort from the start, which the adept senses in the briefing
REWARD_WHY: Keep the colony's Academy standing :: four medics and four marines join the player :: the colony's Academy, where the medics train, standing inside the fort

## Mission type
MISSION_TYPE: reach :: none :: 1

## Target duration
TARGET_DURATION: 30 :: Easy 25 / Hard 38 :: Reach Fort Wren with the strike team=4; Destroy the West Nest and the East Nest=6; Brood Hive in the north-east=8; Marshal Quill must not fall=24; strike team must not be wiped out=4; Keep colony's Academy standing until both nests fall=8

## Start setup
START_SETUP: no-base :: a strike team of four Zealots, three Dragoons, two High Templar and an Observer; the base comes with the pact in phase 2

## Objective paths
OBJECTIVE_PATHS: Reach Fort Wren with the strike team :: landing (14,114) north-east along the ruins road to the fort plateau (63,66), about 80 tiles :: zergling and hydralisk packs at 24,100 / 34,88 / 48,78 and the siege waves arriving at the fort from t=150 s :: a small team without a base must fight through three packs and arrive in the middle of a siege
OBJECTIVE_PATHS: Destroy the West Nest and the East Nest :: from the landing or the woken outpost (40,64) to the West Nest (56,45) and the East Nest (90,58), about 30-60 tiles each :: each nest: two sunken colonies, hydralisks and zerglings, and its own town AI; siege waves from both nests to the fort every 180 s :: two fortified targets on opposite sides of the fort while the fort is attacked
OBJECTIVE_PATHS: Destroy the Brood Hive in the north-east :: fort (63,66) north-east along the second ruins road to the hive (110,13), about 75 tiles :: zerglings at 72,50 below the plateau, hydralisks at 80,46, a zergling and hydralisk pack at 92,34, a lurker post at 100,26, the hive's sunkens, hydralisks and an ultralisk; the main town AI :: an assault on a full Zerg main after the siege
OBJECTIVE_PATHS: Marshal Quill must not fall :: the fort under siege :: siege waves from both nests :: the ally hero stands in the fort the waves aim at
OBJECTIVE_PATHS: The strike team must not be wiped out :: the road to the fort :: the three packs on the road :: no base to rebuild before the pact
OBJECTIVE_PATHS: Keep the colony's Academy standing until both nests fall :: inside the fort (67,69) :: the siege waves :: the player must defend the fort while attacking the nests

## Allies and heroes
ALLIANCE_STARTS: P3 :: switch 2 :: the strike team reaches Fort Wren (the pact)
ALLIANCE_STARTS: P4 :: switch 2 :: the strike team reaches Fort Wren (the pact)
HERO_SLOT: Marshal Quill :: P4 :: faction P3

## AI
- P2 runs ZMEx on the Brood Hive and an Area Town AI (ZARx) on each siege nest from the first second.
- P3 runs TMEx on the fort's Command Center from the first second. Truce with the player before the pact, without vision.

## Scene views
SCENE_VIEW: opening orders :: Landing :: own units present
SCENE_VIEW: the pact :: Fort Wren :: own units present
SCENE_VIEW: the outpost wakes :: Old Outpost :: alliance-vision
SCENE_VIEW: the Academy :: Fort Academy :: own units present
SCENE_VIEW: the siege is broken :: Fort Wren :: alliance-vision
SCENE_VIEW: the medics join :: Fort Academy :: alliance-vision
SCENE_VIEW: victory :: Fort Wren :: alliance-vision

## Map
- South-west: the landing. Centre: Fort Wren on a plateau; the dormant outpost west of it (mineral column backed by water).
- Around the fort: the West Nest (north-west) and the East Nest (east).
- North-east: the Brood Hive main.

## Flow
PHASES: hero, base, combat, assault
1. Briefing (executor, adept).
2. Phase 1: fight up the road to the fort (siege waves start at t=150 s).
3. The pact: alliance and vision start, the outpost wakes; when the team steps into the Academy yard the side objective is given.
4. Phase 2: destroy both nests (waves stop with their nest).
5. Phase 3: destroy the Brood Hive: victory.

## Briefing and voice
- Speaking portraits for the executor and the adept; every line voiced; in-mission lines are Transmissions with WAVs.
- Voices: edge-tts; echo for the Protoss, a light filter for the marshal; VO markup v1 on every line.

## Characters
### Executor Nhal
- Trait: measured, proud
- Goal: secure the world for the Protoss
- Weakness: slow to trust humans
- Voice: low, formal
- Tone: resolute
- Moments: "we go to the humans first", "we fight together", "now the hive itself"

### Marshal Quill
- Trait: tired, wry, stubborn
- Goal: keep his people alive
- Weakness: exhausted
- Voice: rough, dry
- Tone: wry, then grateful
- Moments: "didn't think I'd be glad to see you", offers the medics

### Adept Seris
- Trait: curious, quick
- Goal: wake the old outpost
- Weakness: impulsive
- Voice: light, quick
- Tone: awed
- Moments: senses the outpost, "it answers us"

## Difficulty
Three packs on the first road, two fortified nests with their own town AIs and siege waves, a full Zerg main.
Start resources 0/0 (the outpost brings the economy).

## Shortcuts
The strike team brings an Observer; the base from phase 2 can build up to Stargates (no Fleet Beacon or Arbiter
Tribunal), so there are flyers but no Recall.
OBJECTIVE_SHORTCUTS: Reach Fort Wren with the strike team :: flyer (the Observer) :: two hydralisk packs (around 33,88 and 49,79) stand on the straight line to Fort Wren, the same count as the two fights on the road
OBJECTIVE_SHORTCUTS: Fort Academy :: flyer (the Observer) :: the same two hydralisk packs cover the air line to the academy; the assault itself needs the army

## Tech level
TECH_LEVEL: late :: stand-alone (late chapter of a Protoss campaign) :: everything up to the Templar Archives tier (High and Dark Templar, Archons, Reavers, Scouts, Corsairs); no Fleet Beacon or Arbiter Tribunal, so no Carriers, Arbiters or Recall

## Campaign rules
Tech: late tier without Carriers and Arbiters (TECH_LEVEL late). No attack announcements.

## Mission design deviations
- None.
