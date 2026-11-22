# EXAMPLE: Relay Watch - Design Note

EXAMPLE mission (StarCraft: Brood War, .scx, Badlands 128x96), built by `tools/bw/examples/ex_relay_watch.py`.
**Structure only:** copy how this note is organised (sections, design lines), never the mission design (objective, map
layout, start setup, enemy, story, rewards). Every mission invents its own; see docs/bw-example-missions.md.
Complexity: medium. Placeholder story.

## Campaign outline
Example campaign "Signal Corps" (placeholder, 4 chapters): 1) the corps lands on a dead colony world, 2) this mission:
the corps must send a distress call through three old relay stations held by Protoss pickets, 3) the answer is not the
one they hoped for, 4) the corps leaves with whatever answered.
TONE: tense :: comic characters allowed yes (a chatty technician) :: a brisk major, a nervous technician and a cold templar

## Story
The Signal Corps needs a twenty-minute uplink, and the uplink needs all three relay stations at the moment it completes.
A Protoss host holds the relays with pickets and expands from its base in the east.

## Objectives
- Required: Capture all three relay stations.
- Required: Hold out at all three relays until the uplink completes (a visible 20-minute countdown from the start).
- Defeat: the Command Center falls, or a relay is not the player's (its turret gone) when the countdown ends.
- Optional (pointed out about 3 minutes in): find the stranded Goliath crew in the Western Canyon.

## Side objectives
SIDE_OBJECTIVE: Find the stranded Goliath crew :: rescue :: units

## Rewards
REWARD_WHY: Capture all three relay stations :: each relay's Missile Turret joins the player :: the turret standing at the centre of each relay, visible from the start
- The Goliath crew joins when reached (engine rescue): the reward is the crew itself.

## Mission type
MISSION_TYPE: hold :: time-limit :: 3

## Target duration
TARGET_DURATION: 21 :: Easy 21 / Hard 21 (the countdown is fixed; difficulty changes wave size) :: Capture all three relay stations=10; Hold out at all three relays until the uplink completes=20; Command Center must stand=20; find stranded Goliath crew western canyon=3

## Start setup
START_SETUP: build-up :: a thin landing: Command Center, one Barracks, one Supply Depot, six SCVs and six marines; everything else is built while the clock runs

## Objective paths
OBJECTIVE_PATHS: Capture all three relay stations :: base (14,47) along the north road to the North Relay (58,14), about 60 tiles; across the centre to the mesa relay (64,48), about 55 tiles up one of two ramps; along the south road to the South Relay (56,82), about 60 tiles :: each relay: a photon cannon on a pylon, two zealots and a dragoon; Protoss waves to every relay from t=170 s :: three pickets to break in three directions while the clock runs and waves arrive
OBJECTIVE_PATHS: Hold out at all three relays until the uplink completes :: Protoss waves from the North Gate (92,22), the East Gate (92,46) and the South Gate (92,74), each to its own relay, about 35-40 tiles :: eleven waves at t=170, 270, 370 s and then every 100 s by turns, rising in size, while the Protoss main stands :: three relays far apart, attacked by turns from three directions; the player cannot sit in one choke
OBJECTIVE_PATHS: The Command Center must stand :: the expansion AI's own attacks along the centre :: town AI attacks on top of the scripted waves :: the base is thin at the start
OBJECTIVE_PATHS: Find the stranded Goliath crew in the Western Canyon :: base to the canyon (22,86), about 45 tiles past the south road :: two Protoss patrols (two zealots and a dragoon at 21,60, two dragoons at the canyon mouth 21,75), the South Relay picket and the south waves nearby :: a detour while the south relay is contested

## AI
- P2 runs the expansion town AI (PMEx) on its Nexus from the first second; two free expansion sites (north-east, south-east) give it room to expand.

## Scene views
SCENE_VIEW: opening orders :: Home Base :: own units present
SCENE_VIEW: relay captured :: North Relay :: own units present
SCENE_VIEW: relay captured :: Centre Relay :: own units present
SCENE_VIEW: relay captured :: South Relay :: own units present
SCENE_VIEW: distress beacon :: Western Canyon :: revealer
SCENE_VIEW: crew joins :: Western Canyon :: own units present

## Map
- West: the landing (mineral column backed by water).
- Centre: the mesa relay (two ramps); north and south relays behind creeks, each with two approaches.
- East: the Protoss main; free expansion sites in the north-east and south-east corners.

## Flow
PHASES: base, expand, combat, hold
1. Briefing; the 20-minute countdown starts with the mission.
2. Build up; first wave at t=170 s.
3. Capture the relays (any order); the stranded crew is pointed out at t=180 s.
4. Hold all three until zero: victory; any relay without the player's turret at zero: defeat.

## Briefing and voice
- Speaking portraits for the major, the technician and the templar; every line voiced; in-mission lines are Transmissions with WAVs.
- Voices: edge-tts; radio filter for the Terrans, echo for the templar; VO markup v1 on every line.

## Characters
### Major Ines Calder
- Trait: brisk, practical
- Goal: get the call out
- Weakness: overcommits
- Voice: clipped, mid
- Tone: firm
- Moments: "clear the pickets", "now we hold them"

### Technician Obi Varga
- Trait: chatty, nervous
- Goal: keep his uplink alive
- Weakness: panics about equipment
- Voice: fast, light
- Tone: anxious, then elated
- Moments: starts the clock, cheers every relay, "everyone heard us"

### Templar Ashai
- Trait: cold, formal
- Goal: silence the Terrans
- Weakness: contempt
- Voice: deep, slow
- Tone: contemptuous
- Moments: "you will not speak across this world", taunts at ten minutes

## Difficulty
Three pickets, eleven rising waves from three directions (north and centre fed by the Templar Hall, the south column independent of it), an expanding town AI. Start resources 500/200.

## Shortcuts
The player has Barracks and Factory tech (no Starport this chapter), so the only vector is lift-off: a Barracks,
Factory or the Command Center flies to a relay or the canyon, lands and trains there.
OBJECTIVE_SHORTCUTS: North Relay :: lift-off :: the relay's dragoon and photon cannon cover the air approach (one anti-air encounter, as many as the road), and the capture trigger also needs every picket at the relay dead and three own troops there, so the fight at the relay stays
OBJECTIVE_SHORTCUTS: Centre Relay :: lift-off :: the capture trigger needs the four guards on the mesa dead and three own troops there; a landed Barracks cannot take the relay on its own
OBJECTIVE_SHORTCUTS: South Relay :: lift-off :: the capture trigger needs the four guards at the relay dead and three own troops there; a landed Barracks cannot take the relay on its own
OBJECTIVE_SHORTCUTS: Find the stranded Goliath crew in the Western Canyon :: lift-off (a Factory lands and trains a Goliath) :: the trigger counts Goliaths; two dragoon patrols cover the air line as well as the road (two anti-air encounters)

## Pressure sources
North and centre waves run only while the Templar Hall stands (it visibly feeds them), and so does the town AI. The
south column is the templar's field army marching in from beyond the eastern edge: it keeps coming when the hall
falls, so breaking the hall early never ends the pressure on the relays.

## Tech level
TECH_LEVEL: mid :: stand-alone (middle chapter of a Terran campaign) :: Barracks and Factory tier with the Armory (Marine, Firebat, Medic, Vulture, Siege Tank, Goliath); no Starport, no Science Facility tier yet

## Campaign rules
Tech: Barracks and Factory tier (TECH_LEVEL mid). No attack announcements.

## Mission design deviations
- None.
