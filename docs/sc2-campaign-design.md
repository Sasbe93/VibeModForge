# StarCraft II campaign design (duration and objective paths)

VibeModForge does not yet read StarCraft II maps, so there is no automated SC2 check. The planned-duration and
objective-path rules still apply, the same way they do in Brood War and Warcraft III. Write them in the shared
design-note template (`templates/Design_Note_template.md`) and judge the mission against them before delivery.

## Planned duration
Every mission declares how long it should take on Normal (and on Easy/Hard, or Casual/Hard/Brutal when those are the
labels in use) and gives each main and side objective a share of that time:

```
TARGET_DURATION: <Normal minutes> :: <Easy/Hard> :: <objective>=<minutes>; <objective>=<minutes>
```

Walking is only a small part of the budget; the rest is fighting, choices and pressure. Path encounters scale with
that budget: about one real encounter or decision point per 1-2 minutes of the objective's time. A rescue, reach or
escort route still has at least two threat sources (the two-encounter baseline is additional, not a replacement for
the budget). A survive or hold objective gets scripted waves about every 60-120 seconds, rising, from more than one
direction. The first real pressure arrives in the first 2-4 minutes.

A walk+fight estimate below about a third of the budget, or a main objective that can be finished before the first
wave or path encounter, means a redesign (or a shorter declared duration). `OBJECTIVE_PATHS_EASY_OK: <reason>` waives
the difficulty rules, not a missing TARGET_DURATION line.

## Objective paths
For every main and side objective, trace the real path on the map before building (start to each target, a rescue
there and back, escort routes, scripted attack waves to the player's base with travel and arrival times, approach
directions and chokes) and write:

```
OBJECTIVE_PATHS: <objective> :: <path(s) with length and travel time> :: <threats on the way / waves and directions> :: <why it is a challenge>
```

Draw the paths on a routes image next to the map when you can. The Brood War and Warcraft III checkers
(`tools/bw/check_objective_paths.py`, `tools/wc3/check_objective_paths.py`, shared math in
`tools/lib/mission_duration.py`) are the reference for the numbers; apply the same thresholds by hand on an SC2
mission until this repository can read the map.
