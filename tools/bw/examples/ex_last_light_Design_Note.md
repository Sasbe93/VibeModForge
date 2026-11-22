# EXAMPLE: Last Light - Design Note

EXAMPLE mission (StarCraft: Brood War, .scx, Desert 128x96), built by `tools/bw/examples/ex_last_light.py`.
**Structure only:** copy how this note is organised (sections, design lines), never the mission design (objective, map
layout, start setup, enemy, story, rewards). Every mission invents its own; see docs/bw-example-missions.md.
Complexity: simple. Placeholder story.

## Campaign outline
Example campaign "Cold Harbour" (placeholder, 3 chapters): 1) the brood wakes under the dune fields, 2) this mission: hold
Kessel Station until the evacuation fleet docks, 3) the evacuees reach the orbital yard and learn what woke the brood.
TONE: grim :: comic characters allowed no :: a last stand far from help; humour stays in single dry lines

## Story
Kessel Station has mined the dune shelf for months. A Zerg brood came out of the north valley and now tunnels under the
sand. The evacuation fleet is fifteen minutes out and can only dock at the station's Command Center.

## Objectives
- Required: Survive until the evacuation fleet arrives (15 minutes, visible countdown).
- Defeat: the Command Center is destroyed.
- No optional objective.

## Side objectives
none (this mission has no optional objective)

## Mission type
MISSION_TYPE: hold :: hold-timer :: 0

## Target duration
TARGET_DURATION: 16 :: Easy 16 / Hard 16 (the timer is fixed; difficulty changes wave size) :: Survive until the evacuation fleet arrives=15; Command Center must stand=15

## Start setup
START_SETUP: established :: a mining station held for months: Command Center, two Barracks, Academy, Factory and Engineering Bay already stand
START_DEFENSE_WHY: three bunkers and one missile turret :: the station has been fortified against the brood for weeks; one bunker per approach

## Objective paths
OBJECTIVE_PATHS: Survive until the evacuation fleet arrives :: waves from North Gate (62,30) down the valley road, about 35 tiles / 15 s; from East Pass (96,48), about 40 tiles; from the Sand Caves (34,88), about 40 tiles :: north waves every 180 s from t=100 s (5 waves), east every 210 s from t=190 s (4 waves), south every 200-230 s from t=330 s (3 waves); together a wave every 60-90 s from three directions, first pressure at about t=2 min; north and east stop when their hive cluster falls :: three approaches, one bunker each: the player cannot sit in one choke, and has to decide whether to strike a hive cluster to end one direction

OBJECTIVE_PATHS: The Command Center must stand :: the three wave paths above end at the station front (bunkers at 61,46 / 78,58 / 62,76) :: every wave that breaks a bunker line walks straight into the mineral line and the Command Center :: losing one approach is not the end, losing the Command Center is

## Scene views
SCENE_VIEW: opening orders :: Station :: own units present
SCENE_VIEW: halfway count :: Station :: own units present
SCENE_VIEW: the fleet docks :: Station :: own units present

## Map
- Centre: Kessel Station (a dune shelf with mud pads), mineral column backed by a tar pit to the west.
- North: the brood's main hive cluster at the head of the valley road.
- East: a second hive cluster behind a tar pit; the East Pass leads to the station.
- South: the Sand Caves, where the brood tunnels up.
- West: a mesa with two ramps (watch post, no base).
- Tar pits funnel the three approaches; dunes and rocky flats as ground variety.

## Flow
PHASES: defend, combat
1. Briefing (Kell, Oduya): the fleet is fifteen minutes out.
2. Countdown starts; waves from the north from about t=100 s, the east from t=190 s, the south from t=330 s.
3. Halfway line at t=450 s.
4. Countdown 0: the fleet docks, victory. The Command Center falls: defeat.

## Briefing and voice
- Briefing: speaking portraits for Kell and Oduya, every line voiced; in-mission lines are Transmissions with WAVs.
- Voices: edge-tts with radio filters; VO markup v1 on every line.

## Characters
### Overseer Bram Kell
- Trait: stubborn, thrifty
- Goal: get every miner off the shelf
- Weakness: cannot leave anything behind
- Voice: gruff, slow baritone
- Tone: grim
- Moments: "nobody gets left in this sand", counts the minutes

### Lieutenant Mara Oduya
- Trait: confident, quick
- Goal: keep her garrison alive
- Weakness: hides fear behind speed
- Voice: clipped, fast
- Tone: dry
- Moments: names the three approaches, calls the fleet in

## Difficulty
Twelve scripted waves in fifteen minutes (zerglings and hydralisks, ultralisks from the fourth north/east wave). The town AI
of both hive clusters attacks on its own as well. Start resources 600/200.

## Shortcuts
A survive objective: there is no place to reach, so lifting or flying gains nothing (check objective_shortcuts finds
no Bring objective).

## Tech level
TECH_LEVEL: mid :: stand-alone (middle chapter of a Terran campaign) :: Barracks, Factory and Starport tier (Siege Tanks, Goliaths, Wraiths, Dropships); no Science Facility tier, so no Vessels, Battlecruisers or nukes for the hold

## Campaign rules
Tech: Factory and Starport tier (TECH_LEVEL mid). No attack announcements.

## Mission design deviations
- Established start and four towers (see START_SETUP and START_DEFENSE_WHY): the station is a fortress under siege.
