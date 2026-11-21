# EXAMPLE: Outpost Nine - Design Note

EXAMPLE mission (StarCraft: Brood War, .scx, Badlands 128x96), built by `tools/bw/example_mission.py`.
Placeholder scenario that shows the structure of a campaign design note; replace everything with your own story.
A Terran outpost on an old road is raided again and again by a Zerg brood dug in on the ridge above it.

## Campaign outline
Example campaign "Outpost Nine" (placeholder, 3 chapters): 1) the raids begin, 2) this mission: burn the ridge,
3) the survey squad leads the outpost to what the brood was guarding. Even a stand-alone mission gets this outline first.

## Story
Captain Varn holds Outpost Nine with a handful of marines. The brood on the north-east ridge feeds every raid. A survey
squad under Sergeant Okafor is stranded in the eastern ravine with its field depot and a bunker.

## Objectives
- Required: Destroy the Hatchery on the ridge.
- Defeat: the outpost loses all buildings (shown in the defeat text).
- Optional (announced by Okafor about two minutes in, after the opening talk): reach the survey squad in the eastern ravine.

## Rewards
REWARD_WHY: Reach the survey squad :: the squad, its supply depot and its bunker join you :: the squad's camp with depot and bunker standing in the eastern ravine

## Map
- South-west: the player's outpost, mineral line backed by water, bunker toward the road.
- North-east: the ridge (high dirt) with the Zerg main, two normal-size ramps toward the south-west.
- East: a Zerg expansion on low ground (second target, optional).
- South-east: the ravine camp of the survey squad (rescuable, far from enemy units).
- Centre: a pond, grass fields and rocky patches; the old road (mud) meanders from the outpost to the ridge.
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
Tech: full tree (example). No attack announcements. Every reward has an in-world source (REWARD_WHY above).

## Mission design deviations
- none
