# General BW map design (all maps)

Ranked numbers, checkers and generator details stay in `bw-ranked-maps.md`; campaign rules in `bw-campaign-design.md`.

## Purpose and reachability
- No large featureless areas; every reachable area needs a gameplay reason: expansion, vantage point, shortcut/backdoor, drop spot, neutral building. Purposeless corners become cliff or water.
- Reachability: nearly all walkable ground and all resources (except deliberate island bases) must be ground-reachable from the starts. Look at the reachability map after every obstacle change.

## Resources and bases
- Resources on walkable ground, never on water or cliffs, always harvestable; mineral lines curved/staggered, not straight; mineral lines and geysers have their back to a blocker.
- Bases use elevation; mains/naturals/expansions stay buildable: few doodads there, only as cover at chokes; random scatter only on the battlefield. Never unbuildable ground under a base.

## Terrain and doodads
- Organic cliff outlines and map edges, no long straight bands or rectangles; doodads spread over the battlefield.
- Doodads in context: themed props at fitting POIs, cliff edges, base outskirts; never on lanes, ramps or chokes, never blocking pathing unintentionally.
- Pathing blockers symmetric on symmetric maps, ideally with different ids of the same footprint.
- Water decor only in water near shores of tilesets that have such ids (jungle, twilight); cliff-edge doodads only on cliff edges; never turn walkable ground unwalkable.
- Two-theme halves are an option: same footprint, different terrain per side.

## Blocked paths and tricks (catalogue `catalogues/bw_features/`)
- Paths cleared by destroying a neutral blocker: mineral walls (low value) or neutral buildings (e.g. Protoss Temple), spanning the full corridor, never invincible.
- Assimilator chokes: destroying narrows the gap. Eggs: block until killed (killing opens). Combination is uncommon.
- Neutral Creep/Sunken/Spore Colonies: documented on the web, not found in the calibration reference maps.
- Mineral walk: workers gathering pass through units/eggs, not minerals/buildings; eggs + mineral on the far side = worker-only path.

## General map-design rules: the general BW check (all maps)
Apply to EVERY BW map (ladder, campaign, fun map). One implementation: `python3 tools/bw/check_map_design_bw.py MAP.scx` (exit 1 on FAIL; a crashing rule is a FAIL). `check_ranked_bw.py` calls it and adds the ranked-only rules.
- Reach: every base reachable by ground from the starts; the map is not mostly cut off (bw_reach).
- Buildable bases: base plateaus stay buildable; doodads there only as purposeful cover at the rim (bw_zone_doodads).
- Normal-size ramps only (>= 8x5 tiles); no small ramp doodads (bw_ramp_size).
- Mineral line access: mineral/geyser footprints on walkable ground of the base level, harvest side reachable, no resource blocking another's line to the hall (bw_resource_ground, check_bw_rules mineral_layout).
- ScmDraft/StarEdit compatibility: strict CHK structure (check_bw_rules strict_chk, sclib.validate).
- Ranked only: ref-pool tolerances, natural/main sizing, rush distances, symmetry.

## No ports from WC3 (fixed rule)
Warcraft III rules, checks and ideas are never ported to SC:BW. See bw-campaign-design.md "Game boundary".
