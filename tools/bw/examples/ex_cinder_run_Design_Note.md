# EXAMPLE: Cinder Run - Design Note

EXAMPLE mission (StarCraft: Brood War, .scx, Ashworld 128x96), built by `tools/bw/examples/ex_cinder_run.py`.
**Structure only:** copy how this note is organised (sections, design lines), never the mission design (objective, map
layout, start setup, enemy, story, rewards). Every mission invents its own; see docs/bw-example-missions.md.
Complexity: medium. Placeholder story.

## Campaign outline
Example campaign "Ash Brood" (placeholder, 4 chapters): 1) the brood lands on the ash world, 2) this mission: the Terrans
have caught Queen Ixa, the brood must free her and bring her home, 3) Ixa leads the brood against the compound's labs,
4) the brood learns what the Terrans were breeding.
TONE: dark :: comic characters allowed no :: a cold hive mind, a furious queen and a scientist who lies to himself

## Story
A Terran research compound caught Brood Queen Ixa and keeps her in a walled pocket below its shelf. The hive mind sends
the brood across the lava fields to free her. The compound's forward outpost was wrecked in an earlier raid.

## Objectives
- Required: Recover the captive Queen from the holding pens, then bring her back to the Home Nest.
- Defeat: Ixa dies, or the Home Nest (Hatchery, Lair or Hive) falls.
- Optional (pointed out by the hive mind about two minutes in, with the hint that a Queen can infest it): infest the
  wrecked outpost's Command Center.

## Side objectives
SIDE_OBJECTIVE: Infest the wrecked outpost's Command Center :: capture :: base

## Rewards
- The infested Command Center is the reward itself (no trigger hands anything out).

## Mission type
MISSION_TYPE: rescue :: none :: 1

## Target duration
TARGET_DURATION: 25 :: Easy 20 / Hard 30 :: Nest must not fall=25; captive Queen holding pens=10; Queen back to the Home Nest=7; infest wrecked outpost=3

## Start setup
START_SETUP: small-base :: the brood's young hive: Hatchery, Spawning Pool, Evolution Chamber, six Drones, six Zerglings; everything else is grown in the mission

## Objective paths
OBJECTIVE_PATHS: Recover the captive Queen from the holding pens :: Home Nest (14,76) along the cooled lava road to the pens (118,42), about 125 tiles / 45 s at zergling speed, minutes for a growing brood :: firebats and marines at the first bend (38,68), the wrecked outpost with a bunker (64,56), marines and a siege tank at the magma ford (84,38), marines and a goliath at the pen ramp (103,31); the compound's bunkers (92,25) overlook the last stretch :: four guarded spots on the way, each costs units; the brood must be grown at home first while Terran waves arrive
OBJECTIVE_PATHS: Bring the Queen back to the Home Nest :: pens (118,42) back down the road to the Home Nest (14,76), about 125 tiles :: the moment she is free, vultures and marines leave the Ridge Ambush (92,48) for the Road Ambush (64,62), and as soon as she leaves the pens marines and firebats from the Road Ambush head for the Hive Front; the remaining road guards :: a slow Queen escorted through two pursuit groups and whatever guards survived the way out
OBJECTIVE_PATHS: The Home Nest must not fall :: Terran waves from the Compound Gate (90,30) down the road to the Home Nest, about 110 tiles / 40 s :: marine/firebat groups (vultures from the fourth) at t=200, 330, 470, 610, 760, 910 s while the compound's Command Center stands :: the home base must hold while the strike force is away
OBJECTIVE_PATHS: Infest the wrecked outpost's Command Center :: Home Nest to the outpost (60,53), about 55 tiles, with the Queen after her rescue :: the outpost bunker with three marines (64,56) and the road guards at the first bend (38,68) :: a detour with the slow Queen while pursuers are on the road

## Rescue setup
The captives (Queen and three Drones, Rescuable P8) stand in the walled pocket on the pen shelf, more than 8 tiles from
any Terran unit; the pen ramp guard sits below the shelf. The player cannot morph Queens (unit availability), so only
the freed Queen satisfies the return objective.

## AI
AI_IDLE_OK: P3 :: 58,52 :: the forward outpost was wrecked in an earlier raid; its crew fled to the compound, nobody runs it

## Scene views
SCENE_VIEW: opening orders :: Home Nest :: own units present
SCENE_VIEW: the hive mind points at the outpost :: Outpost :: revealer
SCENE_VIEW: Ixa takes the outpost :: Outpost :: own units present
SCENE_VIEW: Ixa is free :: Holding Pens :: own units present
SCENE_VIEW: Ixa is home :: Home Nest :: own units present

## Map
- South-west: the Home Nest (mineral column backed by magma).
- Centre: shale and broken-rock fields split by magma rivers; the cooled lava road runs north-east.
- Centre: the wrecked Terran outpost on the road (damaged Command Center, one bunker).
- North-east: the Terran compound (corner mineral line backed by magma); east of it the pen shelf with two ramps.

## Flow
PHASES: base, explore, combat, return
1. Briefing (hive mind, Corvo on the radio).
2. Build up while Terran waves come down the road (first at t=200 s).
3. About two minutes in: the hive mind points at the wrecked outpost (optional).
4. Fight up the road; free Ixa at the pens: pursuit groups start.
5. Bring Ixa home: victory.

## Briefing and voice
- Briefing: speaking portraits for the hive mind and Corvo, every line voiced; in-mission lines are Transmissions with WAVs.
- Voices: edge-tts, the hive mind deep with echo, Corvo through a radio filter; VO markup v1 on every line.

## Characters
### Overmind Voice Sessh
- Trait: cold, patient
- Goal: keep the brood whole
- Weakness: sees units as numbers
- Voice: deep, slow, layered
- Tone: cold
- Moments: "a small brood dies on that road", points at the broken outpost

### Brood Queen Ixa
- Trait: proud, furious
- Goal: revenge on the compound
- Weakness: hates needing help
- Voice: hoarse, sharp
- Tone: savage
- Moments: "out, finally", takes the outpost, "remember this road"

### Doctor Lenn Corvo
- Trait: nervous, self-justifying
- Goal: keep his specimen
- Weakness: panics
- Voice: fast, thin, over a radio
- Tone: anxious
- Moments: doubles the guard, "the specimen is loose"

## Difficulty
Six Terran waves while the compound stands, four guarded spots on the way out, two pursuit groups on the way back.
Start resources 400/100.

## Campaign rules
Tech: full tree except the Queen (the player cannot morph Queens in this mission, so only Ixa counts). No attack announcements.

## Mission design deviations
- AI_IDLE_OK for the wrecked outpost (see AI).
