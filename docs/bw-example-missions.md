# Brood War example missions

Eight placeholder missions, built end to end with `tools/lib/bw/sclib.py` and `tools/lib/bw/missionkit.py` (the
examples in `tools/bw/examples/` share their pipeline through `tools/bw/examples/exlib.py`). Each one writes its map,
design note, voice script, minimap and routes PNG to `output/` and passes the full predelivery check (all checks
including objective paths and target duration, placement check, trigger simulation, and opening the map in ScmDraft).

## Structure only, never the mission design (fixed rule)
Copy the STRUCTURE of an example: the build pipeline (terrain -> players -> units -> locations -> doodads -> cast ->
triggers -> save -> checks), the design-note sections and line formats, and the trigger, voice and check conventions.
Never copy its MISSION DESIGN: objective, map layout, start setup, enemy, story and rewards. Every mission invents its
own. Use a different example than for the previous mission, and keep neighbouring missions varied (mission-type
variety rule, predelivery check `mission_type_variety`). The stories here are neutral placeholders.

## The examples

| Example | Complexity | Mission type | Start setup | Player race / tileset | What it demonstrates |
|---|---|---|---|---|---|
| Outpost Nine (`tools/bw/example_mission.py`) | simple | destroy a target + reach | build-up | Terran / Badlands 128x96 | the base example: organic terrain, ridge ramps, Blizzard mineral formations, voiced briefing, waves that stop when their hatchery dies, rescued squad as reward |
| Glass Reef (`examples/ex_glass_reef.py`) | simple | no-base hero squad, find and use | no-base | Protoss / Twilight | hero on a rescuable slot, two legs with guarded spots, ambush that springs on an event, enemy without a base, rescue side objective (units) |
| Last Light (`examples/ex_last_light.py`) | simple | survive a meaningful timer | established | Terran / Desert | visible countdown, START_DEFENSE_WHY, waves every 60-120 s from three directions fed by real hives, no side objective |
| Cinder Run (`examples/ex_cinder_run.py`) | medium | rescue and return | small-base | Zerg / Ashworld | long dangerous path both ways, rescue pocket rules, unit availability (only the captive Queen), pursuit groups, AI_IDLE_OK outpost |
| Thorn Road (`examples/ex_thorn_road.py`) | medium | escort with ambushes | small-base | Protoss / Jungle 128x96 | allied escort hero in his own slot (HERO_SLOT), legs started by waypoints, three triggered ambushes, destroy side objective whose reward is information |
| Relay Watch (`examples/ex_relay_watch.py`) | medium | capture and hold control points | build-up | Terran / Badlands 128x96 | capture by presence, turret hand-over as reward, hold countdown with a defeat condition, expanding enemy AI with free sites, rescue side objective |
| Hask Hunt (`examples/ex_hask_hunt.py`) | complex | kill a boss, with a twist | build-up | Zerg / Desert 128x128 | enemy general in his own slot, escape to a second fortress with a countdown, objective text that changes, two enemy town AIs, reach side objective (information) |
| Ember Pact (`examples/ex_ember_pact.py`) | complex | multi-phase: squad -> base -> assault | no-base, base in phase 2 | Protoss / Jungle 128x128 | truce then alliance by trigger (vision starts at the pact), allied hero, dormant outpost given as reward, morph-chain targets, protect side objective |

## Running
```
python3 tools/bw/example_mission.py
python3 tools/bw/examples/ex_ember_pact.py          # any example; --no-checks skips the checks
```
Requirements as for every BW mission: isomtool and tileset files (`docs/bw-terrain-setup.md`), edge-tts and ffmpeg
(`DEPENDENCIES.md`).

## Lessons the examples encode
- Space guard packs along a route at least about 14 path tiles apart, otherwise the path check merges them into one
  encounter.
- Waves are only traced when they run on Elapsed Time (or on switches set by such triggers); a hold that starts on an
  event cannot be traced, so start its countdown at the beginning and say so in the note.
- Capture objectives are not traced as a path type; give them clear OBJECTIVE_PATHS lines.
- A unit in `HERO_IDS` cannot be used as a plain rescuable unit; rename an ordinary unit instead.
- On Jungle, ramp generation is less reliable: ask for one ramp and verify the plateau is reachable.
- Keep a 2-tile free ring around every town hall (no water, cliffs or doodads), and keep the player's mineral line
  backed by water or cliff.
