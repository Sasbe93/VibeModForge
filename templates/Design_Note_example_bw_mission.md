# EXAMPLE: Outpost Nine - Design Note

EXAMPLE mission (StarCraft: Brood War, .scx, Badlands 128x96), built by `tools/bw/example_mission.py`.
Placeholder scenario that shows the structure of a campaign design note; replace everything with your own story.
STRUCTURE ONLY: copy the sections and the line formats, never the mission design (objective, map layout, start setup,
enemy, story, rewards). More examples of other types and complexity: `docs/bw-example-missions.md`.
A Terran outpost on an old road is raided again and again by a Zerg brood dug in on the ridge above it.

## Campaign outline
Example campaign "Outpost Nine" (placeholder, 3 chapters): 1) the raids begin, 2) this mission: burn the ridge,
3) the survey squad leads the outpost to what the brood was guarding. Even a stand-alone mission gets this outline first.

## Story
Captain Varn holds Outpost Nine with a handful of marines. The brood on the north-east ridge feeds every raid. A survey
squad under Sergeant Okafor is stranded in the eastern ravine with its field depot and a bunker.

## Objectives
- Required: Destroy the Hatchery on the ridge (it counts as destroyed only when no Hatchery, Lair or Hive stands there: the Zerg may morph it).
- Defeat: the outpost loses all buildings (shown in the defeat text).
- Optional (announced by Okafor about two minutes in, after the opening talk): reach the survey squad in the eastern ravine.

## Rewards
REWARD_WHY: Reach the survey squad :: the squad, its supply depot and its bunker join you :: the squad's camp with depot and bunker standing in the eastern ravine

## Side objectives
SIDE_OBJECTIVE: Reach the survey squad :: rescue :: units

## Mission type
MISSION_TYPE: destroy-targets :: none :: 1

## Start setup
START_SETUP: build-up :: Outpost Nine is a small roadside post: a Command Center, five SCVs, one Barracks and a single bunker toward the road; the player builds everything else.

## Scene views
SCENE_VIEW: opening orders :: Outpost :: own units present
SCENE_VIEW: Okafor's radio call :: Ravine Camp :: revealer
SCENE_VIEW: the squad rejoins :: Ravine Camp :: own units present
SCENE_VIEW: victory call :: Ridge Hall :: own units present

## Planned duration
The mission is meant to take about 10 minutes on Normal (Easy about 14, Hard about 8). Walking is only a small part of
that; the rest is the fights on the road, the push on the ridge, and the optional ravine rescue. Each objective's
encounter count scales with its budget: about one real fight per 1-2 minutes, and a rescue or reach still has at least
two threat sources.
TARGET_DURATION: 10 :: Easy 14 / Hard 8 :: Destroy the Hatchery on the ridge=6; Reach the survey squad=4

## Objective paths
OBJECTIVE_PATHS: Destroy the Hatchery on the ridge :: start to the ridge hatchery, about 100 tiles / 33 s at Marine speed (Fastest) :: two zergling packs on the ridge road (around 36,46 and 60,22) plus the ridge gate held by Sunken Colonies, zerglings and hydralisks (three path encounters); scripted waves leave Ridge Gate for Outpost Front every 160 s from t=240 s, first arrival about t=256 s, from the north-east :: the player has to fight two packs, then push two ramps and the gate, while the hatchery still feeds those waves
OBJECTIVE_PATHS: Reach the survey squad in the eastern ravine :: start to Ravine Camp, 77 tiles / 26 s at Marine speed (Fastest) :: two zergling packs on the southern track (around 46,82 and 66,82), two threat encounters, well clear of the camp; two hydralisk pickets above the track cover the air line :: the player has to fight through both packs to reach the squad; the camp itself is not under fire

## Shortcuts
Checked from what the player can field in this chapter (TECH_LEVEL early: Barracks tier, no Factory or Starport, so no
flyers, Dropships or Recall). Liftable buildings: Command Center and Barracks.
OBJECTIVE_SHORTCUTS: Reach the survey squad in the eastern ravine :: lift-off (a Barracks or the Command Center flies to the camp, lands and trains a marine or SCV) :: two hydralisk pickets stand on the ash rises above the track (around 48,73 and 70,78), right on the air line from the outpost, so a floating Barracks meets two fights just like the walk; no flyers or transports exist in this chapter
OBJECTIVE_SHORTCUTS: Destroy the Hatchery on the ridge :: none that skips the fight (a destroy target needs an army at the hatchery) :: the hatchery has to be killed; lifting a building to the ridge gains nothing

## Pressure sources
The ridge waves only run while the ridge hatchery stands, and that hatchery is the victory target: the waves stop
exactly when the mission is won. The town AI also runs from the Fen expansion, so breaking one base never leaves the
map without pressure while an objective is still open.

## Tech level
TECH_LEVEL: early :: chapter 2 of 3 (example campaign) :: Barracks tier only (Marine, Firebat, Medic, Bunker, Missile Turret, Academy with Stim Packs and Comsat), weapon and armor upgrades to level 1; the Factory and Starport arrive in chapter 3 with the survey squad's findings

## Map
- South-west: the player's outpost, mineral line backed by water, bunker toward the road.
- North-east: the ridge (high dirt) with the Zerg main, two normal-size ramps toward the south-west.
- East: a Zerg expansion on low ground (a second Zerg base that feeds the waves; not an objective).
- South-east: the ravine camp of the survey squad (rescuable, far from enemy units). Two zergling scout packs sit on the southern track to the camp.
- Centre: a pond, grass fields and rocky patches; the old road (mud) meanders from the outpost to the ridge. Two zergling scout packs sit on that road.
- Map edge: ragged dirt/high-dirt/water border; no straight frame.

## Flow
PHASES: base, explore, combat
1. Briefing (Varn, Okafor, voiced, portraits).
2. Opening transmissions, ping on the ridge; small Zerg waves from the visible ridge gate while the hatchery stands.
3. About two minutes in: Okafor announces the optional objective.
4. Reaching the camp: the squad joins and hands over depot and bunker.
5. Push up a ramp, destroy the hatchery: victory.

## Briefing and voice
- Briefing: speaking portraits for Varn and Okafor, every line voiced (Play WAV + Display Speaking Portrait), objectives shown.
- In-mission: every character line is a Transmission with its WAV; Display Text only for status lines.
- Voices: edge-tts with radio filters (Varn en-GB alto, Okafor en-US baritone); VO markup v1 on every line.

## Characters
### Captain Ilse Varn
- Trait: precise, tired, protective of her people
- Goal: end the raids on the road
- Weakness: carries every loss personally
- Voice: low, even alto over a field radio
- Tone: serious
- Moments: briefing order, welcomes the squad back, the hatchery falls

### Sergeant Okafor
- Trait: warm, unflappable
- Goal: get his squad home
- Weakness: hides worry behind jokes
- Voice: rough baritone, a smile in it
- Tone: funny
- Moments: "nobody panic", hands over the depot and bunker

## Difficulty
Waves of 2-4 zerglings (later 2 hydralisks) every ~160 s, only while the hatchery stands. Start resources 300/100.

## Campaign rules
Tech: handed out chapter by chapter (this chapter: TECH_LEVEL early). No attack announcements. Every reward has an in-world source (REWARD_WHY above).

## Mission design deviations
- none
