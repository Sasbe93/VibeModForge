# EXAMPLE: Hask Hunt - Design Note

EXAMPLE mission (StarCraft: Brood War, .scx, Desert 128x128), built by `tools/bw/examples/ex_hask_hunt.py`.
**Structure only:** copy how this note is organised (sections, design lines), never the mission design (objective, map
layout, start setup, enemy, story, rewards). Every mission invents its own; see docs/bw-example-missions.md.
Complexity: complex. Placeholder story.

## Campaign outline
Example campaign "Second Brood" (placeholder, 4 chapters): 1) a Terran general burns the first brood, 2) this mission:
the second brood hunts him, 3) his papers point at a larger plan, 4) the brood strikes the plan's source.
TONE: dark :: comic characters allowed yes (a jumpy aide) :: a patient cerebrate, an arrogant general and his nervous aide

## Story
General Hask burned the first brood and now watches the valley from a fortified command post on a plateau. The second
brood starts with a Hatchery and a Spawning Pool. When it storms the post, Hask runs for a bolt-hole fortress at the other
end of the map and calls a dropship: the hunt becomes a race.

## Objectives
- Required (stage 1): Storm the Command Post and kill the traitor General Hask.
- Required (stage 2, after the twist; the stage-1 line disappears): Kill the traitor General Hask at the Fallback Bunker before his dropship arrives (6-minute countdown).
- Defeat: the dropship arrives (countdown 0 with Hask alive), or the Home Nest (Hatchery, Lair or Hive) falls.
- Optional (pointed out about 3 minutes in): reach the overlook at Bone Ridge.

## Side objectives
SIDE_OBJECTIVE: Reach the overlook at Bone Ridge :: reach :: info

## Rewards
- The overlook shows the fortress in the south-east: the Fallback Bunker stays revealed (permanent map revealer with a
  REVEAL_PERMANENT_OK reason), so the player knows the bolt hole before the twist. No units or resources.

## Mission type
MISSION_TYPE: destroy-targets :: time-limit :: 1

## Target duration
TARGET_DURATION: 28 :: Easy 23 / Hard 36 :: Storm the Command Post and kill the traitor General Hask=8; Fallback Bunker before his dropship arrives=8; Home Nest must not fall=28; overlook at Bone Ridge=4

## Start setup
START_SETUP: build-up :: the second brood: Hatchery, Spawning Pool, five Drones, six Zerglings and two Overlords; everything else grows during the mission

## Objective paths
OBJECTIVE_PATHS: Storm the Command Post and kill the traitor General Hask :: Home Nest (22,107) north-east to the plateau (60,34) and up its ramp, about 95 tiles :: road guards at 24,96 / 37,81 / 47,71 / 62,57 (vultures and firebats below the ramp), the plateau garrison (two bunkers, a turret, a siege tank, marines, medics); Terran waves to the hive from t=150 s :: a long climb through four guard posts while the hive is attacked; the post itself is a fortified hill
OBJECTIVE_PATHS: Kill the traitor General Hask at the Fallback Bunker before his dropship arrives :: from the plateau (60,34) or the hive (22,107) to the fortress (104,109), about 80-100 tiles :: road guards at 36,112 / 56,106 / 76,110 / 88,104 and the fortress (two bunkers, a turret, two siege tanks, marines) :: a six-minute race across the map into a fortress; knowing the bolt hole early (overlook) lets the player pre-position
OBJECTIVE_PATHS: The Home Nest must not fall :: Terran waves from the Terran Gate (94,32) and the Expansion Gate (98,72) to the Home Nest, about 110 tiles :: eight main waves (t=150 s, then every 150-180 s, rising, tanks from the sixth) and three expansion waves, while the halls stand :: the hive must hold while the brood is out hunting
OBJECTIVE_PATHS: Reach the overlook at Bone Ridge :: Home Nest to the ruins (25,39), about 70 tiles up the west side :: guards at 18,74 and 22,54, a spotter pair on the ridge (26,41) :: a western detour away from the post

## Allies and heroes
HERO_SLOT: General Hask :: P3 :: faction P2

## AI
- P2 runs its town AI (TMEx) on the main Command Center and an Area Town AI (TARx) at the expansion from the first second.
- P3 holds only General Hask (own slot, own colour) and is allied with P2 through the force.

## Scene views
SCENE_VIEW: opening orders :: Home Nest :: own units present
SCENE_VIEW: the overlook is pointed out :: Bone Ridge :: revealer
SCENE_VIEW: the overlook is reached :: Bone Ridge :: own units present
SCENE_VIEW: Hask runs :: Command Post :: own units present
SCENE_VIEW: the hunt begins :: Home Nest :: own units present
SCENE_VIEW: Hask is consumed :: Home Nest :: own units present

## Map
- South-west: the Home Nest (mineral column backed by tar).
- North-centre: the command-post plateau with its ramp.
- North-east: the Terran main; east: its expansion. South-east: the Fallback Bunker fortress.
- West: Bone Ridge overlook.

## Flow
PHASES: base, combat, twist, chase
1. Briefing (cerebrate, Hask).
2. Grow the brood under waves (first at t=150 s); the overlook is pointed out at t=180 s.
3. Storm the plateau: Hask runs, the 6-minute countdown starts, the objective line changes.
4. Catch him at the fortress before the countdown ends: victory.

## Briefing and voice
- Speaking portraits for the cerebrate and Hask; every line voiced; in-mission lines are Transmissions with WAVs.
- Voices: edge-tts; the cerebrate deep with echo, the Terrans through a radio filter; VO markup v1 on every line.

## Characters
### Cerebrate Ulzhar
- Trait: patient, cold
- Goal: avenge the first brood
- Weakness: slow to act
- Voice: deep, slow, layered
- Tone: cold
- Moments: "climb his hill", sees the bolt hole, "catch him"

### General Hask
- Trait: arrogant
- Goal: survive and report
- Weakness: a coward under the bravado
- Voice: cold baritone over a radio
- Tone: arrogant, then furious
- Moments: "nobody climbs my hill", "call the dropship"

### Lieutenant Deke Morrow
- Trait: jumpy, loyal
- Goal: get his general out
- Weakness: talks too much
- Voice: fast, light
- Tone: panicked
- Moments: "they are on the hill"

## Difficulty
Four guard posts on each route, a fortified plateau, a fortress, eleven waves and two town AIs. Start resources 300/50.

## Shortcuts
Zerg up to the Hive with Defilers; no Greater Spire or Ultralisk Cavern. Overlords (with Ventral Sacs), Mutalisks,
Scourge and Queens fly; a Nydus Canal needs creep at the exit (the check only warns).
OBJECTIVE_SHORTCUTS: Reach the overlook at Bone Ridge :: flyer, transport (Overlord with Ventral Sacs), nydus :: four marine squads stand on the air line, more than the three fights on the road; no creep reaches the ridge for a Nydus exit
OBJECTIVE_SHORTCUTS: Storm the Command Post and kill the traitor General Hask :: flyer, transport, nydus :: four marine squads (one with a bunker) cover the air line, as many as the road; the general must be killed at the post anyway

## Tech level
TECH_LEVEL: late :: stand-alone (late chapter of a Zerg campaign) :: Hive tier with Defilers and Nydus Canals; no Greater Spire or Ultralisk Cavern yet (Guardians, Devourers and Ultralisks come in the finale)

## Campaign rules
Tech: Hive tier without Greater Spire and Ultralisk Cavern (TECH_LEVEL late). No attack announcements.

## Mission design deviations
- None.
