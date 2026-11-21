# BW ranked melee maps

General rules for all BW maps: `bw-map-design.md`.

Load with `bw-campaign-maps` (sclib, terrain and unit placement rules).

## Reference pool
- ASL S22-era: Odyssey (112x128, 2p), Colorless Fate (128x96, 2p), Aiolos (3p, 128x128), Octagon (4p, 128x128),
  Attitude, KnockOut, Backrooms.
- Classics: Fighting Spirit, Circuit Breakers, Polypoid, Eclipse.
- Typical values:
  - Main: 8-9 mineral fields at 1500 + 1 geyser at 5000.
  - Natural: 7-8 fields + 1 geyser, right outside the main.
  - Further: thirds, mineral-only bases (6x1000), and gold or centre bases.
  - Rush distance ~27-39 s (worker); 1v1 maps are 2p, 4p maps run 2-4 players.

## Design rules
- Symmetry:
  - 2p: 180° rotation.
  - 4p: four-fold mirror or 90° rotation.
  - 3p: 120° is not possible on a tile grid. Use a near-symmetric layout and fair it with path distances, then say so in the report.
- Every start gets the same bases at the same path distances (check by ground path, not air distance).
- Hall spacing: 3 tiles between the hall and the mineral line and geyser (sclib arc); 8-mineral lines drop the middle field.
- The main exit is a choke leading to the natural. Several routes to the enemy; the centre is open but split by obstacles.
- BW cliff tiles are not rotation-symmetric:
  - South faces are taller than north faces, so the exact-tile walk symmetry ends at about 94-95% even when the design is perfect.
  - Measure walk symmetry with a 1-tile tolerance (≥99%).
  - Treat a 2-tile difference in choke width as WARN.
  - Prefer chokes whose two walls have the same face orientation.
- Tech: melee uses the stock tech tree. In campaign/custom tech JSON a Lurker needs Lurker Aspect AND Burrowing.

## Pipeline (box)
- `tools/ranked/bw/rankedlib.py`:
  - `MeleeMap` (no campaign presave), `paint(m, sym, shapes)`.
  - Symmetric ISOM shapes: `c`, `cap`, `ring` with gaps, `rect`.
  - `base_units`, `place(m, sym, units)` (start location owner = copy index), `setup_players`.
- Examples: `example_2p.py` (rot2, 128x96) and `example_4p.py` (mirror4, 128x128).
- Melee slots: OWNR 6 for the used slots, SIDE 5 (user-selectable race). Start location unit 214, neutral resources owner 11.
- Two shapes can produce an overlapping base after rotation. Check that the resource clusters do not merge (the checker reports e.g. "12M" for 6+6).

## Checks
- `python3 tools/bw/check_ranked_bw.py MAP.scx` checks:
  - walk symmetry (exact + tolerant), resource symmetry (pixel transform)
  - rush distance and nearest opponent
  - mineral/gas share by path distance, base #1-3 distance and size per start
  - main-exit bottleneck width (widest path), hall gaps, core tech incl. Lurker→Burrow
- `sclib.validate(out)` (eudplib LoadMap) and a preview render.

## Delivery
- `.scx` + preview PNG + German Design_Note.
- In-game text is English.
- Open points: not tested in game; no high-ground mains or ramps when built with the flat-mesa approach.

## Symmetry tolerance
- Maps need not be 100 % symmetric. Required: gameplay fairness per start (same resources, comparable path/rush distances within a few %, equal choke widths, equal creep/expansion value, equal access to centre/shops).
- Purely visual decoration (doodads, tile variation, non-blocking props) should deliberately differ between sides, as long as it does not affect pathing, vision, building space or resources.
- Therefore near-symmetric layouts (e.g. SC:BW 3-player maps on the tile grid) are acceptable and should be built; checks score fairness with tolerances, not exact tile mirroring.

## Resource placement on walkable ground
- Mineral fields and Vespene geysers must sit entirely on walkable, buildable-height ground: never on water, deep water, lava, space/void, cliff edges or unwalkable doodad tiles.
- Every tile under each resource footprint (mineral 2x1, geyser 4x2) plus the worker harvest ring around it must be walkable, and the base's town-hall spot must reach it by ground.
- Automated check before every delivery: scan all mineral/geyser units against the MTXM tile walkability (and minitile flags); any footprint or harvest tile on water/unwalkable = FAIL. Applies to campaign, ranked and fun maps alike.

## Mineral line access
- No mineral field may be blocked by another mineral field on the direct line to the expected town-hall position; every patch needs a free straight worker path to the hall (single-row or properly staggered arc).
- Automated check: for each base, raycast from each mineral/geyser to the expected hall footprint; any other resource on the line = FAIL.

## ScmDraft compatibility
- Every SC:BW map I make must open in the editor ScmDraft 2 without errors: valid CHK sections/sizes (VER, DIM, ERA, MTXM, UNIT, THG2, STR etc.), no unknown/overlapping sections, valid string table, standard MPQ (staredit\scenario.chk).
- Automated check before delivery: strict CHK parser validation (ScmDraft-like) plus re-save round-trip; deliver only if it passes.

## Diversity dice system
When asked for a map without further constraints, expect diversity. Both first maps had a lake in the centre - that is the anti-example.
- Before designing: `python3 tools/ranked/bw/dice.py --players N [--seed S]`; reroll freely; once chosen, rerun with same seed + `--accept --name MAPNAME` to log it in `dice_history.json`.
- The tool rejects incompatible combos (tag rules `req:`/`no:`, e.g. lava needs Ashworld, river/water edge not on Space/Installation/Ashworld, triangle only 3p, cross positions not 3p) and rerolls if layout or centre matches any of the last 5 maps or tileset matches the last 2.
- Rules: never repeat centre or layout of recent maps; no centre lake again soon; diversity is also visual (tileset, decor theme, palette, edge style must noticeably differ from recent maps). Combine the roll into one coherent theme and write roll + seed in the Design_Note.
- Dice never override the rules above: gameplay fairness (not exact symmetry, decor may/should differ) minerals/geysers only on walkable ground no mineral blocking the line to the hall + ScmDraft opens it. If a rolled option breaks a rule on the chosen tileset, adapt or reroll that table only.
- Extend tables in dice.py (regenerate list below with `--markdown`).

### Tables
**tileset** (8): `badlands` dirt/mud/grass cliffs; classic readable; `space` platform over space; void edges = unbuildable chasms; `installation` indoor metal; no water, tight corridors look natural; `ashworld` lava/magma/ash; lava as unwalkable feature; `jungle` jungle/ruins/temples; water ok; `desert` sand/dunes/tar/compound; tar as unwalkable; `arctic` snow/ice/outpost; water ok; `twilight` basilica/crushed rock/flagstones

**layout** (16): `cross_positions` spawns cross-only (4p) / diagonal (2p); long rush; `ring` bases on a ring road around impassable core; `corridors` 2-3 parallel lanes separated by cliffs; `split_highground` map split by a long high-ground ridge with ramps; `river` walkable shallow/low river with bridges as chokes [no:noWaterTiles]; `plateau_center` large raised centre controlling paths; `backdoor` main has a second, narrow (or mineral-blocked) entry; `mineral_walls` mineral lines (1-8 minerals) wall off shortcuts; `temple_center` doodad temple centrepiece on high ground [req:templeok]; `island_ish` main by land, some expos only reachable by air/drop; `spiral` paths wind rotationally (3p/4p rotation) [no:need2only]; `diagonal_valley` one wide valley between two highland halves; `open_steppe` few cliffs, wide open midfield (macro); `maze_lowground` many small cliffs/doodads forming twisting paths; `pocket_naturals` natural inside main behind single ramp; `triangle` 3 spawns at triangle corners, centre triangle

**center** (14): `hg_plateau` raised plateau with 2-4 ramps [no:core]; `ruins` destroyed-building doodads, unwalkable patches; `choke_maze` small chokes forcing pathing decisions; `open_field` flat open ground, flank-friendly [no:core]; `neutral_buildings` neutral structures to destroy (blocks, vision); `lava_pool` unwalkable lava/tar pit [req:lavaok]; `doodad_garden` dense unwalkable decor (trees/crystals/pipes); `no_center` no special centre; action on sides; `center_expo` contested rich base in middle [no:core]; `void_chasm` space hole / deep chasm (air-only) [req:space]; `crossroads_bridge` bridge/ramp cross over low ground; `watchtower_hills` small raised hills with vision; `mineral_island` middle mineral-only block (minable wall); `temple` temple doodad cluster [req:templeok]

**main_natural** (10): `classic_ramp` main ramp down to natural, natural one wide choke; `pocket` natural inside main; `cliffed_natural` natural below main cliff (drop/siege angle); `forward_natural` natural further forward, open; `backdoor_natural` natural with mineral-blocked backdoor; `double_choke` natural has two narrow entries; `highground_natural` natural on same high ground as main; `side_natural` natural to the side along edge; `gasless_natural` natural without gas (min only); `double_gas_main` main with 2 geysers

**expansions** (11): `linear` bases chained toward centre; `edge_ring` expos along map edges; `cluster_center` expos clustered near centre [no:core]; `island_expo` 1 island expo per player; `rich_contested` one shared richer expo between neighbours; `gas_only` one gas-only/min-low base per side; `min_only` mineral-only thirds; `hidden_backyard` expo behind main; `staircase` expos on rising terraces; `sparse` few bases, aggressive; `plenty` many small bases (6+ per player)

**special** (12): `destructible_path` neutral blocks/rocks open a shortcut; `mineral_backdoor` 1-value minerals block a backdoor; `island_expo` air-only base; `gas_only_base` geyser-only spot; `shortcut_ramps` narrow ramps give fast route; `narrow_bridges` bridge chokes; `assimilator_blocks` neutral geysers / extractors block; `dark_corners` unbuildable high doodads as vision blockers; `creep_none` nothing special (clean); `air_lanes` gaps only air can cross; `blocked_highground` high ground only via destructible; `double_ramps` mains with two ramps

**edge** (8): `cliff_rim` high cliffs border; `water_rim` water edge [no:noWaterTiles]; `void_rim` space void edge [req:space]; `lava_rim` lava edge [req:lavaok]; `wall_rim` indoor walls [req:indoor]; `doodad_rim` trees/crystals; `plain_edge` plain map border; `broken_edge` irregular inlets

**decor** (10): `overgrown` plants everywhere; `industrial` pipes, tanks, machinery; `ancient` statues, temple bits; `battlefield` wrecks, craters; `crystals` crystal clusters; `frozen` ice shards, snowdrifts; `volcanic` vents, magma rocks; `derelict` broken platforms, debris; `sparse_clean` minimal decor; `settlement` houses/outposts

**palette** (8): `bright` bright ground; `dark` dark tiles; `warm` reds/browns; `cold` blues/whites; `mixed` contrasting zones; `monotone` one dominant tile; `checker` alternating patches; `gradient` shift across map


## Reference analysis

| Map | Size | Starts | Main | Natural (path) | Third base (path) | Rush to nearest enemy | Mineral fields / geysers total | Walkable | Height levels | Main exit | Walk symmetry |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Aiolos | 128x128 | 3 | 10×1500 + 1 Gas | 4–30 | 36–42 | 104–130 | 111 / 12 | 72% | 2 | P3 21, P2 17, P1 15 | mirrorY 78.8% |
| AttitudeSE | 128x128 | 4 | 9×1500 + 1 Gas | 33–34 | 47–52 | 137–137 | 120 / 12 | 73% | 2 | P4 5, P1 5, P2 7, P3 5 | rot180 99.6% |
| Benzene | 128x112 | 2 | 9×1500 + 1 Gas | 34–37 | 64–65 | 192–192 | 86 / 10 | 65% | 3 | P1 5, P2 5 | rot180 99.4% |
| CircuitBreakers | 128x128 | 4 | 9×1500 + 1 Gas | 27–31 | 54–57 | 131–131 | 124 / 12 | 70% | 3 | P1 1, P2 1, P3 1, P4 1 | mirrorX 100.0% |
| ColorlessFate | 128x96 | 2 | 9×1500 + 1 Gas | 27–27 | 50–54 | 152–152 | 90 / 12 | 67% | 2 | P2 3, P1 3 | rot180 99.9% |
| Eclipse | 128x112 | 2 | 9×1500 + 1 Gas | 29–31 | 74–92 | 148–148 | 84 / 12 | 74% | 2 | P1 3, P2 5 | mirrorX 78.9% |
| FightingSpirit | 128x128 | 4 | 9×1500 + 1 Gas | 30–32 | 50–75 | 129–141 | 108 / 14 | 75% | 2 | P1 5, P2 5, P3 3, P4 3 | rot180 97.5% |
| KnockOut | 128x128 | 4 | 9×1500 + 1 Gas | 24–26 | 30–31 | 123–127 | 124 / 12 | 76% | 3 | P1 5, P2 5, P3 5, P4 5 | mirrorX 100.0% |
| Octagon | 128x128 | 4 | 9×1500 + 1 Gas | 33–34 | 49–50 | 143–145 | 116 / 12 | 75% | 2 | P1 5, P2 5, P3 5, P4 7 | rot180 99.2% |
| OdysseyRE | 112x128 | 8 | 9×1500 + 1 Gas | 27–29 | 38–40 | 0–0 | 138 / 12 | 68% | 2 | P1 3, P2 1, P3 13, P4 13, P5 13, P6 13, P7 13, P8 13 | rot180 99.1% |
| Plasma | 96x128 | 3 | 9×1500 + 1 Gas | 22–24 | 23–25 | 88–91 | 99 / 9 | 84% | 2 | P1 19, P3 19, P2 17 | mirrorY 99.6% |
| Polypoid | 128x128 | 4 | 9×1500 + 1 Gas | 28–29 | 40–44 | 113–134 | 116 / 12 | 79% | 2 | P2 7, P1 5, P4 3, P3 3 | rot180 98.4% |

Rules derived:
- Main: 9 fields x 1500 + 1 geyser x 5000 (all 12 maps; Aiolos 10). Mineral centres 5.8-7.3 tiles from the start, geyser 5.5 tiles.
- Natural: 7-8 fields + gas at 24-37 tiles ground path (WARN outside 22-40).
- Third: 40-75 tiles (WARN beyond 75). Our test map Z (89-91) and test map A (78-80) are too far.
- Rush: 1v1 maps 148-192 tiles (WARN outside 130-200); 4p nearest opponent 113-145 (WARN outside 105-150).
- Walk symmetry: FAIL < 97% (ladder 97.5-99.98%), WARN < 99%. Resource matching tolerance 1 tile (32 px).
- Main exit 3-7 tiles on 1v1/4p maps; the starts differ by up to 4 tiles on ladder maps.
- Ladder maps are not resource-exact symmetric and give cross/side spawns different shares. Our 1%/3% fairness FAILs are stricter on purpose and stay.
- Walkable share 65-84%; 2-3 height levels; blocker minerals (0-122) used for backdoors.
- MTXM of protected maps comes in several sections, and later sections overlay earlier ones (`sections()` fixed).

## No large empty areas
- Large regions must never stay empty (e.g. blank plain between corner mains and the centre). Every large area needs structure or purpose: height variation, cliffs/water/tar features, alternative paths, an expansion or pocket, neutral/destructible objects, doodad clusters, tile variety.
- Check: grid scan for the largest connected featureless area; too large (about 12x12 BW tiles or equivalent) = FAIL; calibrate so no reference ladder map fails.

## Rule: mineral line shape, main–natural path, number of bases
- **Mineral lines are never straight.** test map J had a straight natural line; it was bad.
  - Place the fields in a curved arc or L shape around the town-hall spot, as on real maps, with staggered rows (offset by 1 tile) and mixed distances of 2–3 tiles to the hall.
  - Check: the fields of a cluster must not sit on one line (max deviation from the best-fit line ≥ 2 tiles), and they must surround the hall in an arc of at least 60°.
- **Exactly one free path from main to natural.**
  - No second walkable route between them that doesn't go through the main exit (e.g. around a ridge).
  - Check: block the main exit tiles, then the natural must not be reachable from the main.
- **Number of expansions per player, measured on the references:**
  - 1v1 maps (Benzene, Colorless Fate, Eclipse) have 84–90 mineral fields and 10–12 geysers in total, so 5–6 bases per player including the main.
  - test map J had only 3 per player (main + 2): too few.
  - Rule: on 2p maps, ≥ 5 bases per player including the main (main, natural, third, at least 2 more, e.g. a gas base or a centre/island base); ≥ 4 per player on 3p/4p maps.
  - Check: count resource clusters per player side, otherwise the map fails.

## Rule: mineral fields with their back to a blocker
- Every mineral line (and the geyser) has its back to a cliff, water or another unwalkable obstacle on the side away from the town-hall spot.
- A small gap is allowed: at most 3 tiles of walkable ground between a field's back edge and the obstacle. No open area behind the line.
- Check: for each field, walk outward from the hall spot. Unwalkable ground must start within 3 tiles for ≥ 80 % of the fields in a cluster, otherwise the map fails.

## Rule: every area needs a reason to go there
- In test map C the strip between the two mains at the top edge, both bottom corners and the bottom centre pocket had nothing interesting in them.
- Decoration or texture alone is not enough. Every reachable area needs a gameplay purpose, for example:
  - an expansion, or a small mineral-only or gas-only base;
  - a high-ground spot or vantage point over a path or base;
  - a shortcut or alternative attack route, for example a narrow back path or one blocked by destructible rocks or minerals;
  - a drop or harass spot next to a main or natural;
  - a neutral building or a space for proxies.
- Dead ends and corners without a purpose are left unwalkable (cliff or water) or turned into one of the purposes above.
- Check: split the walkable ground into zones of about 16×16 tiles. Each zone must contain a resource cluster, a high-ground spot overlooking a path, part of a route between two bases, or a marked drop spot, otherwise the map fails (output lists the zone coordinates).

## Bases use elevation
- Mains are usually on the map's highest walkable level (refs: 58/72 starts on top level, 16/21 maps all mains top), but this is NOT a rule: a main may also sit LOWER than its natural; the main/natural elevation relation is free. The check only gives a WARN (`bw_base_levels.py`) and never a FAIL for this.
- Expansions on at least 2 height levels; aim for ~50% raised or lowered vs their surroundings (refs: 19/21 maps >=2 levels, 124/230 = 54% off-level). Naturals/thirds on plateaus or in low pockets with real ramps.
- Check: `tools/bw_base_levels.py` (in check_ranked_bw.py). FAIL: all expansions on one level or <25% off-level; WARN: a main not on top level. Refs: 35/37 pass (Death Valley, Deja Vu SE fail = old outliers).

## Natural varied edges + doodads
- Map edges never uniform straight bands or square/rectangular water. Irregular organic outlines, mixed themes (water, cliffs, rough terrain, doodads).
- Plenty of doodad tiles spread over the whole map.

## Only normal-size ramps
- Use only full-size standard ramp groups as on ladder maps, never small/narrow ramps. (Check + ref measurement still open.)
- measured (refs, `ranked/bw/ramp_clusters.py`): ladder ramps are composite or large (8x6..16x11 clusters, e.g. jungle 12/13 6x6 pairs, platform 12x9, badlands 14x9). Our test map C used single 6x5 (=small).
- Check: `tools/bw_ramp_size.py` (in check_ranked_bw.py). FAIL: no ramps; <35% of ramp clusters >=8x5 (refs 18/19 pass, KnockOut outlier); small ramps on maps with <=8 ramps.
- Generator: `rankedlib.RAMP_IDS_RAMP_SIZE` (badlands 8x5/14x9; ashworld 8x5). Place with `ramp2.pair(m,ids,box,W)`: picks the mirrored left/right variant pair (badlands 372<->393) without hard seams (RPEAK 20). Plateaus = `cap` shapes with a flat south edge (BW ramps face south only -> mirrorx, not rot2).
- generator pattern: `ranked/bw/map_ochre.py` (high-ground main, raised plateau expansions, random mixed edge blobs water/high-dirt/mud+rocky, `place_doodads` ND=900 on dirt/high-dirt/mud/grass/rocky).

## CORRECTED: the natural is the GATE of the main
- The old detour check (below) was wrong: test map P passed it (detour 1.04) but its natural sat BESIDE the main exit. Correct concept:
  - The main has exactly ONE exit (its ramp), and that ramp leads down INTO the natural.
  - The natural is the area you must cross to leave the main. Its wider choke opens toward the enemy/centre.
  - Geometrically the natural sits between main and enemy main. Removing the natural region must disconnect the main from every enemy (natural = cut/articulation region). Being near the shortest path is not enough.
  - The natural hall is closer to the enemy than the main is (ground distance), and the main->natural direction is within ~115 deg of main->enemy (refs 2p 49-81 deg).
- Check (`tools/bw_natcut.py`, called by `bw_natural.check` in `check_ranked_bw.py`):
  - cutR = smallest ground radius around the natural whose removal cuts the main from all enemies (maximin path). The natural is the best of the 3 nearest bases within 50 tiles.
  - FAIL if cutR >18 (refs 10-17), angle >115, or enemy-distance ratio nat/main >=1.
  - Refs pass 21/31 files. Failures are 4p/old maps with backdoor or ambiguous naturals (Aiolos, Odyssey extra starts, Death Valley, Deja Vu, Pole Star, one FS/Polypoid start, Dominator angle).
- Template fix (`ranked/bw/map_map_template.py`):
  - Seal the main-ramp pocket on the far side with an HDIRT cap `(32,-6,35,24,4)`.
  - Turn the space between the seal, the top lake and the central ridge into an unreachable mesa, built from HDIRT circles at prio 9.
  - Move the fourth base up into the bowl at (43,30) so has no dead zone.
  - Use main ramp box `2,6,25,24`. With a box reaching x>=26 the ramp lands on the seal instead of the main.

##: natural lies IN FRONT of the main, on the way to the enemy
  - Refs have dense centres: many cliffs, high-ground pods and narrow lanes, plus several path options. My maps have wide open dirt plains with a few round hills.
  - Rush is 119-198 tiles on refs (2p 150-198). Ochre is 135 and the template test build 110: too short.
  - Any symmetry is allowed: rotational, mirror (left/right or top/bottom) or diagonal; refs use all of them. What matters is that the ground rush distance stays inside the reference range (>=150 tiles on 128x128) and the rush path does not just hug the map edge.
  - Third/fourth bases are 22-98 tiles away, mostly along the route from the natural or behind it (third detour <=1.2 on 14/24).
- Check: `tools/bw_natural.py` in `check_ranked_bw.py`:
  - FAIL if the natural is not on the route (detour >1.15) or if the natural is more than 45 tiles away.
  - INFO lines report the angles, the closest approach of the rush path (path-pass) and the third base.
- Generator: `ranked/bw/map_natural_in_front.py` (copy of map_ochre with a BASES table):
  - The natural is placed just below the main ramp, toward the centre.
  - A water strip shuts the top corridor between the main and the third.
  - Gate: it prints GATE FAIL when fail.
  - NOT finished: in the test build the top corridor still leaks and the build fails the back checks.

##: resources never on water or cliffs, always harvestable
- Check: `tools/bw_resource_ground.py` in `check_ranked_bw.py`. Lone blocker minerals (fewer than 4 resources within 6 tiles) are skipped.
  - FAIL if more than half of a mineral footprint (2x1) or more than 3/8 of a geyser footprint (4x2) is unwalkable.
  - FAIL if a resource has no walkable tile within 2 tiles of it.
  - WARN if a resource cannot be reached by ground from any start (island base).
  - Footprints spanning two levels and geysers on unbuildable tiles are NOT failed, because refs do both.
  - Refs: 23/24 have no failures (Colorless Fate has 1).
  - test map M: 19/76 resources fail.
  - test map Y: 22, plus 42 unreachable.
  - test map A: 30.
  - test map Z: 10.
  - test map C: 0 fail, 14 unreachable (WARN).
  - test map X: 0 fail, 12 unreachable (WARN).
  - test map J and test map T: 0.
- Cause: edge blobs and water backs are painted over the arc_base mineral ring.
- Generator rule:
  - Paint a clearing disc of base ground at the hall centre with radius about 9.3 and prio 10. In `paint`, the highest prio wins.
  - Paint obstacle backs only outside it. Water shore transitions eat about 3 tiles, so backs must be at radius 12 or more.
  - Always run the gate.

## Two-theme halves (design option)
- Mirrored halves may look different, e.g. one side wasteland (MUD/ROCKY/DIRT) and the other side installation/mechanical (ASPHALT), as in Eclipse.
- The walk footprint must stay identical. Painting asphalt on only one half broke walk symmetry (96%). Instead, paint the SAME shapes in both halves with a different terrain per side, via `paint_half` (west MUD, east ASPH). This gave 98.5–98.9% walk symmetry.
- Badlands has no working "structure" ISOM (IDs 8–13, 16, 17 fail). Use asphalt plus the mechanical doodads.
- Template: `tools/ranked/bw/map_map_template.py`.
  - Use `rect` plateaus for the main, third and fifth, because ramps only fit on straight south edges. Use an HDIRT cliff (not water) behind the natural minerals.
  - Clear plateau bases only toward the mineral side (an offset disc of r6.5), so the ramp edge stays straight.
  - Fix `edge_straight` with small HDIRT bumps on the plateau edges, not water notches next to minerals.


## General rule: contextual doodads
- Doodads are placed in context, never as random props. Themed props come in clusters at a matching POI: graves/tombstones only in a graveyard, ruin or crypt (at least 3 together), bones/skulls/corpses only at creep camps or battle sites, wreckage only at battle sites, barrels/crates at camps, villages and docks.
- No isolated decorative prop on a lane or path. Decorative doodads go at path edges, cliff feet, base outskirts and POIs. Path furniture (sign posts, lamp posts, torches, braziers) may stand beside paths.
- BW: decorative doodads and sprites (skulls, wreckage, crates, statues) go at cliff edges, base outskirts and POIs. Never put them on lanes, ramps or chokes, and they must not block pathing. No automated BW check yet: check by eye on the preview before delivery.

## Natural choke + clean expansions
**: the enemy's way into the natural is a narrow choke.** Checked by `tools/bw_natural_choke.py` (called by check_ranked_bw).
- Ring k is the walkable tiles with k ≤ ground distance from the natural < k+1.5 that lie in the ENEMY component of {dist ≥ k}, for k = cutR+1 … cutR+10.
- width = min ring size / 1.5. entrances = connected groups of that ring.
- Reference values for 2p: total 7.3–16 and 7–13 per entrance (Eclipse 7–9, Benzene 8, Colorless Fate 12.7, Jane Doe 16 over 2 entrances). The 4p refs are noisy (shared or pocket naturals), so 3p+ maps only WARN.
- FAIL if width >16 or per entrance >13.
- Fix: block the open part of the natural with an obstacle (magma/HSHALE pool) and leave a neck of about 5–8 tiles toward the exit ramp. Never leave a wide open plateau front.

**: doodads inside expansions** (CV5 group ≥1024 with flag 0x80 unbuildable, 0x4 unwalkable, or minitile-unwalkable).
- The expected hall spot (4x3 + 1 margin) must have 0 such tiles. The spot is the start location, or else the best buildable spot about 6.3 tiles from the minerals.
- Mining corridor (hall to each resource, width 1.5, excluding 1.5 tiles at each end): at most 2 tiles (refs max 2).
- The rest of the build zone (ground dist ≤8, >2.5 from resources): WARN only above 30 (refs have up to 30 decorative tiles at the edges).
- All 37 refs pass.
- Generator: `place_doodads(..., forbid=FB)` with FB = bbox(hall + resources) +3/+5 per base on BOTH mirror sides (see map_map_template_forbid.py).

## Main area + lower limit
** lower limit:** the natural entrance may also be too narrow. FAIL below 6.5 tiles per entrance (refs min 7.3). A ramp alone (about 4–5 tiles) is too tight.

**: the main needs enough space.** Checked by `tools/bw_main_space.py`.
- Main = ground Voronoi cell of the start. Seeds are all starts plus all expected expansion halls.
- area = walkable tiles; buildable = walkable and not cv5 0x80.
- Refs per start (25 maps, Plasma island gimmick excluded): area min 536, p25 ~657, median ~686, max ~1190. Buildable is nearly the same.
- FAIL if area <530 or buildable <520. WARN if area <655 or buildable <640.
- Fix: a wide main pocket, at least about 25x26 tiles of free low/high ground without magma or doodads. Keep obstacles (rift, cliffs) at the pocket edges.
- `map_map_template_forbid.py` env DX (default 6) moves rift, plateau, ramp2 and third east; NY 96 makes the main taller.

## Pathing-blocker symmetry
Path-blocking doodads should already be placed symmetrically, ideally with different path-blocking doodads on each side that block the same spots. Visual (walkable) doodads are free.
- Check `tools/bw_symmetric_blockers.py` (in check_ranked_bw.py): mask = doodad tiles (CV5 group>=1024) unwalkable (VF4 minitiles; tilesets without VF4 = cv5 proxy flag 0x04|0x80). Transform = symmetry from resources, shift refit on the walk grid. mismatch=|M xor TM|/|M u TM|. FAIL >0.02 or any asym tile within 12 of resources (only WARN if resources themselves <0.9 symmetric). WARN variety 0 (all pairs same id).
- Refs are NOT tile-exact (best CircuitBreakers 0.027, KnockOut 0.055, most 0.3-0.98): our rule is stricter than the refs, on purpose.
- Builder: `ranked/bw/symdood.py place_sym()` instead of sclib.place_doodads: blocking doodads only as pairs A(x,y)+B(W-x-w,y) with mask(B)=fliplr(mask(A)), B a different id when possible; visual ones random. Template map_map_template_forbid: 0.000 mismatch, variety 0.90.

## Organic cliff outlines
Raised areas (main, plateaus, ridges) need curved, organic cliff outlines with diagonal steps; no long axis-aligned straight cliff edges.
- Check `tools/bw_cliff_outlines.py` (in check_ranked_bw.py): on each level mask, longest axis-aligned straight edge run, share of edge length in runs >=8, corners per edge tile (diagonal steps/curvature).
- Refs (n~29): longest med 16 / p90 24 / max 38; straight med 0.116 / p90 0.228; corners min 0.383 / p10 0.40 / med 0.464. Eclipse 16 / 0.07 / 0.522.
- FAIL: longest >24, corners <0.38, or (straight >0.22 and corners <0.40). WARN: longest >18, straight >0.16, corners <0.42. Refs: 3 FAIL (Deja Vu 34, Jane Doe 38, Pole Star 0.235/0.391).
- Builder: rankedlib `paint` kinds `nrect` (x0,y0,x1,y1,amp,seed[,corner_r]) = rounded rect + smooth noise warp, and `nc` (cx,cy,r,amp,seed) = noisy circle. Never use plain `rect` for raised ground; AMP ~3.4 for plateaus, ~2 for pods. Noise is evaluated in shape coords, so the symmetry stays exact. Ramps still need their straight 8-tile edge.

## Reachability (self-found checker gap)
- A test map passed every check while only 40 % of the walkable ground (and 62 resources, i.e. 4 of 6 bases per side) was ground-reachable from the starts: a lake and a hill sealed the outer low ground. only look at reachable tiles only WARNed (and printed just 3 lines).
- Check `tools/bw_reach.py` (in check_ranked_bw.py): FAIL if reachable share of walkable ground < 0.90 or > 10 resources unreachable (more than one island base); WARN < 0.95. Refs 0.920 (Eclipse, 1 island base) – 0.998.
- Generator habit: after every obstacle change, look at the reachability map, not only the RESULT line.

## Base-zone doodads
- Check bw_zone_doodads (zones = ground Voronoi of starts/halls, radius 14). Limits from refs: main <=3.0% doodad tiles and <=3 interior tiles; natural <=25%/17; other expansions <=35%/41. Refs: mains 0-2.8% (Benzene, Circuit Breakers, Eclipse, FS, Radeon, Neo Sylphid all 0); battlefield 4.8-44.6%.
- Generator: forbid boxes over main plateau, natural pocket and every base box; random scatter only on the battlefield; cover doodads only as pairs at chokes/ramps. Never SHALE (unbuildable) under a base. Our battlefields (0-5.6%) are too sparse - aim >=5%.

## Blocked paths (neutral buildings / mineral walls)
- Optional feature (map_blocked_paths.py, env BP=minerals|temple, BPV value, BPN layers): low-ground backdoor natural->corner, closed by a 0-48 value mineral wall (2x1 fields, 2 rows) or a stacked Protoss Temple (174, 7x4, 1500 HP each) owner 11, never invincible (state 0x10).
- The blocker must span the full corridor width (measure with wk.py; temple corridor 6 wide). Generator exits BLOCKFAIL if nothing is sealed.
- Checker: blockers() / apply_blockers() in check_ranked_bw; natcut (bw_natural_choke) counts blockers closed; bw_blocked_paths FAILs on invincible or asymmetric sealing blockers (2p), INFO for decorative low-value minerals (refs KnockOut, Pole Star, Aiolos).
- Mechanics catalogue: catalogues/bw_features/BW_Ranked_Features.md + features.json (verified vs web-only).

## Geyser chokes, eggs, battlefield density
- BP=assim (map_blocked_paths.py): two Vespene Geysers (188) + neutral Assimilator 157 / Extractor 149 / Refinery 110 (GB=assim|extr|ref), owner 11 (P12), state flags 0 (never invincible), gap GAP=2 tiles at GY=92. EGGS=1 EGG=36|97 plugs the gap with neutral eggs (seals the path).
- Checker: a geyser under a neutral gas building counts as a blocker (it stays after the building dies). Tile-level only: sub-tile Assimilator-vs-geyser footprint gaps are not modelled.
- Battlefield density: after the normal scatter run a blocking-only cover pass (symdood.place_sym(...,only_block=True), NB=400) outside all forbid boxes -> 6.3-6.5% (refs 4.8-44.6%). bw_zone_doodads WARNs below 4.8%.

## Assimilator chokes vs eggs work in opposite directions
- Assimilator choke: destroying NARROWS (Assimilator box < geyser box): both standing = all units, one gone = small units, both gone = Ghosts only (Liquipedia Assimilator/Troy/Battle Royal). Extractor is larger than a geyser, Refinery ~ geyser -> not the reference trick; GB=extr/ref test-only.
- Eggs: block until killed (killing OPENS).
- Eggs + Assimilator combo is UNCOMMON (only Block Chain ASL7, TL; none in our refs): never default (EGGS off unless set explicitly).

## Neutral Creep/Sunken/Spore Colonies
- Ids 143/146/144 owner 11 (2x2). Neutral creep lets any Zerg build Sunkens/Spores at a choke without a Hatchery; neutral Sunken/Spore do not attack; non-Zerg cannot build there until it dies and creep recedes.
- Used on Colosseum, Turbine, Kick Back, ASL4 submissions (web). Our 33 reference .scx: zero neutral 143/144/146 -> catalogue only, NO generator support.

## Water decor / cliff doodads
- From the reference scan (doodads_water_cliff.json): water decor jungle 160-163/270-271, twilight 123-128 (mostly near shore, loose symmetry, ~2% of doodads). Cliff-edge doodads jungle 32-37 etc., twilight 26/18/28/29, platform 104-138 (~19% of jungle doodads). Ashworld/desert/ice have no ref ids -> generator places none there.
- Generator: ctxdood.place_ctx(m,'water'|'cliff',n): ids from refs (>=2 maps), mirrored, >=6 tiles from resources/ramps/forbid boxes, edge-blend check, never turns walkable ground unwalkable. bw_reach ignores unreachable walkable specks <=6 tiles (water decor tiles).

## Mineral walk (worker-only paths)
- Mineral walk: worker gathering a VISIBLE mineral/geyser ignores UNIT collision (eggs, units, critters) - not buildings, minerals, terrain. Sliding through mineral lines = stacking glitch to cross a mineral line (Neo Requiem, Iron Curtain, Outsider; legal). Gas walk through building walls is illegal (ICCup/KeSPA).
- Map pattern (web): unit blocker (neutral eggs) + mineral patch on the far side = worker-only path (Block Chain). Our 33 refs contain none -> catalogue only, NO generator option. bw_blocked_paths prints INFO when egg blockers have minerals nearby.

## 3-player layouts and combining every trick on one map
- BW ramp doodads face south only, so a 120° rotation is impossible. Use `SYM='mirrorx'`: P1 west, P2 east (mirror image), P3 on the vertical axis with self-symmetric bases (`tricks.lr_base`) and a single ramp centred on the axis (`tricks.axis_ramp`). Side players use `tricks.ud_base` so all mains have the same resource count.
- West/east ramps: `tricks.mirrored_ramp_pair(m, box)` places a ramp in the box and its mirrored doodad at the exact mirror x; `ramp2.valid(..., RXACT=1)` (env) forces exact mirror positions so the symmetric_blockers check passes.
- Put every trick on the axis or as a mirror pair: backdoor lane with 0-value mineral columns (`tricks.backdoor_lane`), assimilator + egg pass with mineral-walk targets (`tricks.assimilator_egg_pass`), temple stacks (`tricks.temple_stack`), neutral colonies as landmarks (`tricks.neutral_colonies`), water/cliff decor via `ctxdood.place_ctx`.
- Near-symmetric 3-player maps are fine: the checker scores fairness with tolerances. Expect small warnings (axis natural slightly wider, main-exit bottleneck differing by one step because of BW cliff faces) and verify them in-game.
- Mark tricks whose behaviour is only known from web sources (mineral-wall mining-out, sliding niche, worker-only path, neutral colonies) as untested in the map notes until checked in-game.
- Typical tuning knobs exposed as env variables in generator scripts: ramp score limits `RMAX`/`RPEAK`, ramp search boxes, doodad counts for water/cliff/scatter/cover. Sweep them and keep the first combination with 0 FAIL.
