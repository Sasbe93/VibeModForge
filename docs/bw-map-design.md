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

## Campaign terrain (missions)
The terrain generator needs isomtool and your own tileset files (`docs/bw-terrain-setup.md`). Without them stop and
set them up; never fall back to rectangle plateaus or untextured ground. Worked example: `tools/bw/example_mission.py`.
- **Cliff shapes:** paint high ground with overlapping noisy blobs (`Map.blob(cx, cy, r, brush, noise)`), never
  rectangles. Predelivery check 40 (`bw_cliff_outlines`) FAILs a straight axis-aligned cliff run > 24 tiles or a corner
  density < 0.38; aim for runs <= 18 and a mix of convex and concave bends. Map edges are ragged (`Map.edges`), mixing
  cliffs, water and plain ground; no frame of one straight band.
- **Terrain variety:** use at least 3-4 ground textures of the tileset (Badlands: dirt, high dirt, mud, grass, rocky
  ground, water) in irregular patches; roads and riverbeds as meandering paths (`Map.path`) that lead the eye to the
  objectives. Large single-texture areas read as empty.
- **Doodad density:** dress the battlefield, not the bases: about 1 doodad per 40-80 walkable battlefield tiles, in
  small clusters at cliff feet, roads and points of interest; none on bases, ramps, lanes, locations or within 2 tiles
  of units (`missionkit.dress` + `seams` removes hard seams). Doodads must tell something (ruins at an old outpost,
  bones near a Zerg nest).
- **Base layout:** town hall spot first, then the mineral line on the side with water or cliff behind it (every field
  backed by unwalkable ground within 3 tiles), staggered, minerals 2-4 tiles and the geyser 3-5 tiles from the hall,
  every field visible from the hall (`missionkit.res_base` does all of this). Production buildings toward the exit,
  defence toward the approach; enemy bases on creep or with pylon power; keep a 1-tile walking lane around buildings.
- **Ramps and approaches:** normal-size ramps (>= 8x5) only, at least two ways into a big enemy plateau; the attack
  path of scripted waves stays readable (waves come from a visible source, e.g. the enemy gate).
- **Reach:** every objective, rescue and resource must be ground-reachable (placement check
  `tools/bw/placecheck.py`), unless a drop or air mission says otherwise in the Design_Note.

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
