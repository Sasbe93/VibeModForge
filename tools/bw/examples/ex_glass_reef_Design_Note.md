# EXAMPLE: Glass Reef - Design Note

EXAMPLE mission (StarCraft: Brood War, .scx, Twilight 128x96), built by `tools/bw/examples/ex_glass_reef.py`.
**Structure only:** copy how this note is organised (sections, design lines), never the mission design (objective, map
layout, start setup, enemy, story, rewards). Every mission invents its own; see docs/bw-example-missions.md.
Complexity: simple. Placeholder story.

## Campaign outline
Example campaign "The Quiet Reef" (placeholder, 3 chapters): 1) this mission: a templar squad crosses the reef to wake a
sleeping Waygate, 2) the keepers lead the templar to a buried archive, 3) the brood that guards the reef is traced to its
source.
TONE: serious :: comic characters allowed no :: a small, solemn pilgrimage; the dry keeper is wry, not a comic figure

## Story
Praetor Aunvar's squad landed on the Glass Reef to reach an old Waygate. It only wakes when someone stands in the
Crystal Shrine east of the landing. A Zerg brood roams the reef. Two old high templar keepers hide in the southern ruins.

## Objectives
- Required: Reach the Crystal Shrine with Praetor Aunvar (find), then reach the Waygate with him (use).
- Defeat: Praetor Aunvar dies.
- Optional (felt by Selun about two minutes in): find the shrine keepers in the southern ruins.

## Rewards
REWARD_WHY: Find the shrine keepers :: the two high templar keepers join the squad :: the keepers themselves, hiding in the southern ruins

## Side objectives
SIDE_OBJECTIVE: Find the shrine keepers :: rescue :: units

## Mission type
MISSION_TYPE: reach :: none :: 0

## Target duration
TARGET_DURATION: 12 :: Easy 10 / Hard 15 :: Crystal Shrine=5; Waygate with Praetor Aunvar=4; find shrine keepers southern ruins=3; Aunvar must not fall=12

## Start setup
START_SETUP: no-base :: a templar strike squad landed by shuttle on the reef; there is nothing to build here

## Objective paths
OBJECTIVE_PATHS: Reach the Crystal Shrine with Praetor Aunvar :: landing (16,80) to the shrine (100,66) along the pilgrim track, about 95 tiles / 50 s at zealot speed :: a zergling pack in the first hollow (36,70) and hydralisks with zerglings at the shrine approach (60,61) :: a small squad without reinforcements has to break two packs and keep the hero alive
OBJECTIVE_PATHS: Reach the Waygate with Praetor Aunvar :: shrine (100,66) up the stair road to the Waygate (112,14), about 60 tiles / 30 s :: hydralisks and an ultralisk on the stairs (104,44), zerglings and hydralisks below the gate (109,27), plus an ambush from the Hollow cave (116,30) that springs when the shrine wakes :: the squad is already worn down; the ambush hits the stair guard fight from the flank
OBJECTIVE_PATHS: Find the shrine keepers :: landing (16,80) past the shrine track south to the ruins (101,80), about 100 tiles :: the zergling pack in the first hollow (36,70) and the hydralisk pack at the shrine approach (60,61) lie on the way :: a detour that costs time and health before the shrine

## Scene views
SCENE_VIEW: opening orders :: Landing :: own units present
SCENE_VIEW: Selun senses the keepers :: Keepers :: revealer
SCENE_VIEW: the keepers join :: Keepers :: own units present
SCENE_VIEW: the shrine wakes :: Crystal Shrine :: own units present
SCENE_VIEW: the gate holds :: Waygate :: own units present

## Map
- South-west: the landing site (no base).
- Centre: the pilgrim track (mud) between glass ridges and pools; zergling and hydralisk packs.
- East: the Crystal Shrine on flagstones; south of it the ruins where the keepers hide.
- North-east: the stair road up to the Waygate court (basilica); the Hollow cave east of the stairs.
- Map edge: ragged dirt, high dirt, water and crevices.

## Flow
PHASES: explore, combat
1. Briefing (Selun, Aunvar).
2. The squad follows the track east; two guard packs.
3. About two minutes in: Selun senses the keepers (optional).
4. Aunvar reaches the shrine: the Waygate wakes, the brood ambushes from the Hollow.
5. Aunvar reaches the Waygate: victory.

## Briefing and voice
- Briefing: speaking portraits for Selun and Aunvar, every line voiced; in-mission lines are Transmissions with WAVs.
- Voices: edge-tts with a light echo (psionic speech); VO markup v1 on every line.

## Characters
### Praetor Aunvar
- Trait: proud, stubborn
- Goal: bring every one of his zealots home
- Weakness: too proud to ask the old keepers for help
- Voice: slow, heavy baritone, short vows
- Tone: serious
- Moments: "shrine first, then home", accepts the keepers stiffly

### Adept Selun
- Trait: curious, anxious
- Goal: prove she can read the reef
- Weakness: second-guesses herself
- Voice: quick, bright
- Tone: warm
- Moments: senses the keepers, warns of the ambush

### Keeper Ishra
- Trait: dry, patient
- Goal: see the Waygate opened again
- Weakness: trusts no young templar
- Voice: quiet, slow, amused
- Tone: cynical
- Moments: "you took your time"

## Difficulty
Four guard packs and one ambush; no reinforcements for the player. No waves (the brood has no base here).

## Shortcuts
No base: the squad has only what it brings, including one Observer.
OBJECTIVE_SHORTCUTS: Find the shrine keepers in the southern ruins :: flyer (the Observer) :: accepted, see SHORTCUT_OK; the later legs count only Praetor Aunvar, who walks
SHORTCUT_OK: Keepers :: flyer :: the Observer is the squad's scout; spotting the keepers from the air is the intended way to find them, and finding them only starts the trip: the Crystal Shrine and the Waygate count only Praetor Aunvar, who has to walk the guarded road with the keepers

## Tech level
TECH_LEVEL: early :: stand-alone (early chapter, hero squad) :: the squad builds nothing in this mission (no Probe, Nexus or production), so the tech settings are not used

## Campaign rules
Tech: not used (the squad builds nothing; TECH_LEVEL early). No attack announcements.

## Mission design deviations
- No base and no enemy base: a hero squad mission (classic start type "no base").
