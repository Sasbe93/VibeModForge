# EXAMPLE: Thorn Road - Design Note

EXAMPLE mission (StarCraft: Brood War, .scx, Jungle 128x96), built by `tools/bw/examples/ex_thorn_road.py`.
**Structure only:** copy how this note is organised (sections, design lines), never the mission design (objective, map
layout, start setup, enemy, story, rewards). Every mission invents its own; see docs/bw-example-missions.md.
Complexity: medium. Placeholder story.

## Campaign outline
Example campaign "The Codex" (placeholder, 4 chapters): 1) a templar outpost finds an old codex in the jungle,
2) this mission: the codex must leave through the warp conduit before the Dominion takes it, 3) the Dominion learns
what the codex holds and follows, 4) the templar decide whether to open it.
TONE: adventurous :: comic characters allowed yes (a fussy archivist) :: a calm exarch, a fussy old scholar and a smug captain

## Story
An archivist and two templar bearers carry an old Protoss codex to the warp conduit in the north-east. The only road runs past
a Dominion base and a listening post that reports every step. The exarch's small base must escort them.

## Objectives
- Required: Escort Archivist Telar to the Warp Conduit.
- Defeat: Archivist Telar dies.
- Optional (pointed out about 2.5 minutes in): destroy the Terran listening post north of the road.

## Side objectives
SIDE_OBJECTIVE: Destroy the Terran listening post :: destroy :: info

## Rewards
- The listening post is what calls the ridge ambush: while it stands, the ambush at the ridge foot comes; destroyed, the
  ridge stays quiet and the Dominion captain says so on the radio. No units or resources are handed out.

## Mission type
MISSION_TYPE: escort :: none :: 1

## Target duration
TARGET_DURATION: 18 :: Easy 15 / Hard 23 :: Escort Archivist Telar to the Warp Conduit=10; Archivist Telar must not fall=18; listening post north of the road=4

## Start setup
START_SETUP: small-base :: the exarch's outpost: Nexus, Gateway, Forge, Cybernetics Core, two Pylons, six Probes, four Zealots and two Dragoons; two minutes to ready the escort before the caravan leaves

## Objective paths
OBJECTIVE_PATHS: Escort Archivist Telar to the Warp Conduit :: Caravan Camp (30,70) - Ford (52,63) - Temple Stair (70,50) - Ridge Foot (86,38) - Ridge Pass (100,26) - Warp Conduit (117,13), about 120 tiles in five legs, several minutes at the archivist's walking speed :: road guards at the ford (44,66) and 38,58, below the temple (66,56), north of the plateau (70,36), at the ridge (90,34) and at the pass (108,20); the siege-tank lookout on the temple plateau (78,45); triggered ambushes at the ford (from 58,72), at the temple stair (from 78,60) and, while the listening post stands, at the ridge foot (from 96,14); the Dominion base's town AI attacks on its own :: the caravan walks on by itself once a leg starts; the player must clear ahead and stay with it when each ambush hits
OBJECTIVE_PATHS: Archivist Telar must not fall :: the escort route above :: every ambush and guard on the route targets the caravan :: losing the archivist ends the mission
OBJECTIVE_PATHS: Destroy the Terran listening post north of the road :: home base (12,78) to the post (62,30), about 75 tiles across the river ford :: the ford guards (44,66), a picket at 38,58, a patrol on the north bank (56,44), the post's bunker, turret and three marines :: a detour away from the caravan while it is on the move, but it cancels the ridge ambush

## Escort route
ESCORT_ROUTE: Archivist Telar and his bearers :: about 120 tiles in five legs, roughly four to five minutes of walking :: guards at 44,66 / 66,56 / 90,34 / 108,20 (plus pickets at 38,58 and 70,36 and a patrol at 56,44), the plateau lookout at 78,45, ambushes from 58,72 / 78,60 / 96,14 :: clear the road ahead of each leg and protect the caravan when the ambushes hit; optionally destroy the listening post first to cancel the ridge ambush

## Allies and heroes
ALLIANCE_STARTS: P3 :: start
ALLIANCE_STARTS: P4 :: start
HERO_SLOT: Archivist Telar :: P4 :: faction P3

## AI
- P2 runs its town AI (TMEx) on its Command Center from the first second.
- P3 (the bearers) and P4 (the archivist) have no AI: they walk only when a trigger orders the next leg.

## Scene views
SCENE_VIEW: opening orders :: Home Base :: own units present
SCENE_VIEW: the caravan leaves :: Caravan Camp :: alliance-vision
SCENE_VIEW: the ford ambush :: Ford Ambush :: alliance-vision
SCENE_VIEW: the listening post :: Listening Post :: revealer
SCENE_VIEW: the post goes silent :: Listening Post :: own units present
SCENE_VIEW: the conduit :: Warp Conduit :: alliance-vision

## Map
- South-west: the exarch's base (mineral column backed by water); the caravan camp east of it.
- Centre: a river with a single ford; the temple plateau with one stair and a Terran lookout on top.
- North: the listening post on open jungle ground.
- South-east: the Dominion base. North-east: the ridge, the pass and the warp conduit.

## Flow
PHASES: base, escort, combat
1. Briefing (exarch, archivist, the Dominion captain on the radio).
2. Two minutes to ready the escort; the caravan leaves at t=120 s.
3. About 2.5 minutes in: the listening post is pointed out (optional).
4. Five legs: ford ambush, temple ambush, ridge ambush (unless the post is gone), the pass guards.
5. The archivist reaches the conduit: victory.

## Briefing and voice
- Briefing: speaking portraits for the exarch, the archivist and the captain, every line voiced; in-mission lines are Transmissions with WAVs.
- Voices: edge-tts; the captain through a radio filter; VO markup v1 on every line.

## Characters
### Archivist Telar
- Trait: precise, fussy
- Goal: deliver every record intact
- Weakness: slow, anxious under fire
- Voice: light, quick, a little prim
- Tone: fussy but brave
- Moments: counts the two minutes, "older than their whole species", "every record, intact"

### Exarch Vael
- Trait: calm, dry
- Goal: bring the caravan through
- Weakness: trusts the road too much
- Voice: low, steady
- Tone: protective
- Moments: "ready the escort", points out the listening post

### Captain Ruiz Hale
- Trait: smug, impatient
- Goal: take the codex for the Dominion
- Weakness: relies on his listening post
- Voice: fast, over a radio
- Tone: smug, then annoyed
- Moments: "let them come", "we are blind on the ridge"

## Difficulty
Four guard posts and a plateau lookout on the road, two or three triggered ambushes, the town AI's own attacks.
Start resources 300/150.

## Tech level
TECH_LEVEL: mid :: stand-alone (middle chapter of a Protoss campaign) :: Gateway, Citadel, Robotics and Stargate tier (Zealots with Leg Enhancements, Dragoons, Reavers, Shuttles, Scouts, Corsairs); no Templar Archives tier yet

## Campaign rules
Tech: Citadel, Robotics and Stargate tier (TECH_LEVEL mid). No attack announcements.

## Mission design deviations
- The temple plateau has one stair only (it is a lookout, not a route).
