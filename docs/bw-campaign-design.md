# StarCraft BW campaign maps

## Game boundary: no ports from WC3 (fixed rule)
Rules, checks and ideas that came from Warcraft III feedback or Warcraft III work stay WC3-only. They are never ported to SC:BW (or SC2), not "adapted", not "in spirit", not as an "analog". A rule enters this guide only when it was given for SC:BW or explicitly requested for SC:BW. When unsure, leave it out.

## How the rules are organised
Four levels:
1. **Fixed rules (fixed rules)**: always apply; no campaign or mission design can switch them off. Most have a mandatory check.
2. **Classic standards (classic defaults)**: Blizzard-style defaults. They apply unless the campaign or mission design deliberately deviates WITH a written reason.
3. **Campaign rules**: optional catalog, chosen per campaign in its Design_Note. NOT defaults.
4. **Mission design**: per-mission decisions, recorded with a reason in the mission's Design_Note.

**Precedence:** Fixed rules > mission design > Campaign rules > Classic standards. Mission and campaign design may override classic defaults only with a written reason, never a fixed rule.

**Design_Note:** every Design_Note has the sections "Campaign rules" (which catalog rules this campaign adopts) and "Mission design deviations" (every deviation from a classic default in this mission, with its reason). Checks read these sections before allowing an exception. No entry = classic default applies.

**Feedback into the guides in the same turn:** whenever playtest or design feedback creates a reusable rule, write it into every fitting guide in this same turn (and add a check where feasible). Do not wait to be asked. Campaign and mission design ideas also go into `docs/campaign-design-catalog.md` (classified; only for the game the feedback was about). Delivered maps stay unchanged unless the feedback explicitly asks for a map change.

---
## 1. Fixed rules (fixed rules)
- **Showcase:** every unit, hero or ability NEW in a chapter gets situations in that map where it can fulfil its role and use its abilities well (healer -> wounded allies, siege -> structures/walls, anti-air -> air enemies, detector -> invisible units, caster -> targets worth casting on, mobility -> terrain to cross). Document per new unit in the Design_Note: `SHOWCASE <id> :: <role> :: <abilities> :: <concrete map situation: place, phase, what the enemy brings>` (new ids via `NEW_IDS:` or race json minus `PREV_IDS:`). Check: `tools/bw/check_showcase.py` (wrapper around `tools/wc3/check_showcase.py`; FAIL missing/thin line, WARN situation lacks fitting targets).
- **Characters:** every named speaking character gets in the Design_Note `## Characters` one entry (`### Name`) with `Trait:` (distinct trait), `Goal:` (personal goal beyond the mission objective), `Weakness:` (flaw / inner conflict), `Voice:` (recognisable speech voice: rhythm, vocabulary), `Quirk:` optional, `Tone:` (temperament: serious, funny, cynical, cold, warm ...; the cast must mix tones) and `Moments:` (where this mission reveals something about them). Optional but encouraged: `Relationships:` (relationships and friction with the other characters; how they treat underlings vs superiors), `Secret:` (private secret or backstory hint, revealed slowly), `Arc:` (small arc across chapters), `Speech:` (vocabulary, sentence length, rhythm), plus a contradiction in each character and one surprising moment each. Trait catalog: attitude to others (spiteful, arrogant, warm, caring, distrustful, jealous, blindly loyal, servile-up/harsh-down, flattering, parental, aloof, chummy); worldview (confident, naive, cynical, fatalistic, superstitious, fanatic, idealistic, pragmatic, hardened, fearful, curious, nostalgic); drive (ambitious, greedy, vengeful, duty-obsessed, glory-seeking, lazy, content, guilt-driven, approval-seeking, controlling); temperament (hot-tempered, stoic, nervous, impulsive, deliberate, melancholic, exuberant, dry-humored, grumpy, calm); intellect/demeanor (know-it-all, cunning, simple, well-read, boastful, modest, vain, pedantic, chaotic, taciturn, chatty); moral grey (cowardly but honest, cruel but just, lies out of pity, keeps promises at any cost, betrays out of conviction). Every mission contains reveal moments: banter, a disagreement, a personal stake, a choice. Characters develop across chapters (a tic changes at a turning point, a relationship shifts). Main characters need >= 3 lines that are not just orders/objectives. Check: `tools/bw/check_characters.py` (WC3: `tools/wc3/check_characters.py`; FAIL missing section/fields/entry or single shared Tone, WARN < 3 non-functional lines). Techniques that worked:
  - **Audible tic tied to the story:** a character repeats a small verbal habit under pressure and breaks it only at a turning point; another keeps a running count of followers and corrects it when one dies; a cheerful system voice keeps its routine phrase while things go wrong.
  - **Comic relief with a heart:** a side character keeps a clumsy record of events, mixes up names, and adds dry remarks that also comment on the hero's choices.
  - **Questions that expose the mentor/antagonist:** a companion asks short, innocent questions that reveal the mentor's hidden weakness; small doubts accumulate into a theme.
  - **Personal stake and memory:** the hero counts what she has lost, remembers voices of the fallen, and keeps one object for herself against the mentor's will.
  - **Choice with a voice reaction:** a choice (destroy vs spare) gets a line from the hero ("I will answer for it") and a reaction from a side character, with a later payoff (the spared side joins).
  - **Antagonists with own motive and contrast in voice:** one antagonist speaks quietly while others shout and wants the land as proof before a rival; another's contempt turns into regret; enemies reveal lore in passing.
  - **Recurring relationships with nicknames and friction:** characters address each other by nicknames, rivals argue from opposed values, and enemies may briefly agree.
  - **Unfinished threads:** last line of a mission opens a personal question ("She knew my name.").

### Scope discipline
- Build only what was asked. No invented extra mechanics, buildings or units. If something extra seems useful, propose it instead of building it.
- When fixing feedback, change exactly what was criticised and keep what was praised.
- In-game text is English. Never leak secret story or twist files.
- Lesson: a fix that is one hand-typed line in a map script is not a fix. Every reported bug gets a rule here AND a check on the final .scx.

### Hero setup (technical)
- The hero belongs to ONE rescuable player (usually green, P8), placed right next to the player's starting units, so it is rescued immediately. No beacon rescue.
- Only heroes and hero structures carry the hero colour, owned by that same single rescuable player. No extra allied players, no stray units in other colours, and auto-placement must never give that player extra buildings.
- Rescue range: a hero rescued/handed over at mission start stands right next to a MOBILE player unit, within 2 tiles (buildings do not trigger rescue). Generator: `hx,hy=m.hero_spot_near(g,P1)`; sclib.save asserts it (`check_rescue_heroes`). Predelivery check 27 FAILs otherwise (rescuable-player hero or customised unit without a mobile human unit within 2 tiles).
- Rules tied to a hero structure (e.g. nest: energy recharge, re-creating a fallen hero by trigger, defeat if destroyed) must keep working after the owner changes on rescue. Check by location and both owners.
- Hero spellcasters: unlock AND research their spells for both the player and the rescuable player.
- Check every mission for duplicate hero spawns and unreachable beacons.

### Unit damage: renamed/customised units keep their weapon damage
- UNIx (and UNIS) weapon damage/bonus is indexed by **WEAPON id** (weapons.dat), not unit id, and is used for every unit whose use-default flag is 0 (every `m.rename(...)`). An unset entry = 0 damage.
- Hero units have their own weapons: Kerrigan(16)=weapon 3, Raynor marine(20)=1, Raynor vulture(19)=5, Schezar(17)=9/10, Norad II(29)=21/22, Zeratul=85... Never guess: look it up in `starcraft/tech/bw_weapons.json` (built from BWAPI by `tech/sources/build_weapons.py`).
- sclib.save fills the real default damage for every weapon of every customised unit automatically and asserts >0; `WDMG[w]=(dmg,bonus)` is only for deliberate overrides and warns if w is not a weapon of a customised unit. Do not add per-map WDMG lines for defaults.
- Mandatory check 23 in `tools/bw/predelivery_check.py` (`tools/bw/unit_damage.py MAP.scx`): FAIL if any armed unit (placed, buildable or customised, heroes included) has 0 damage, or UNIS (4048 B, 100 weapons) and UNIx (4168 B, 130 weapons) disagree / have wrong size.

### Tech data
- Verify tech/upgrade IDs against the real BW tables. An off-by-one shift silently enables the wrong spells.
- Write the expansion sections (UPGx/TECx/PUPx/PTEx) AND the vanilla ones (UPGS/TECS/PUPG/PTEC). An empty vanilla section can break unlocks.
- Block unbuildable units via unit availability, not via tech.
- Upgrades must match real tiers (e.g. Metabolic Boost early, Adrenal Glands only with Hive). Tech unlocks match real tiers.
- **Burrow tech dependency:** units that only make sense burrowed (Lurker) are only available if Burrow (tech 11, Hatchery) is researched or researchable. Either enable Burrow or lock the Lurker together with Lurker Aspect. The check runs automatically in `data/bw/tech/check_tech.py` and therefore in predelivery_check. Apply it to all missions before every release.
- After every build, dump the sections from the built .scx and prove each required spell is set (available, researched, per-player override).

### Core abilities stay usable
- Never offer a unit/building while its core abilities are disabled. Table: `tech/bw_techtree.json` -> `core_abilities` (Comsat->Scanner, Medic->Healing, Vessel->Def. Matrix, Ghost->Lockdown, Vulture->Spider Mines, Tank->Siege, Queen->Infestation/Parasite, Defiler->Dark Swarm/Consume, HT->Storm/Hallucination/Archon Warp, DT->DA Meld, Arbiter->Recall/Stasis, Corsair->Disruption Web, Dark Archon->Mind Control/Feedback, Lurker->Lurker Aspect).
- Free-in-BW abilities (Scanner, Def. Matrix, Healing, Infestation, Parasite, Dark Swarm, Archon Warp, DA Meld, Feedback) are enabled AND pre-researched; others must be researchable at an obtainable building.
- Generator: `sclib.tech_sections` auto-adds core techs of every listed unit (`_with_core`). Campaign: sclib DEFAULT_RESEARCHED was off by one (Dark Swarm not free) - fixed.
- Mandatory predelivery check 24 (`tools/bw/core_tech.py`). The tech-tree check missed it because it skips techs that are disabled.

### Terran add-ons are linked, not just placed
- A pre-placed add-on only attaches in the game when the UNIT section links it to its parent: relation bit 9 (0x200) on both records and each record's last u32 = the other unit's serial. Standing in the right spot is not enough; an unlinked add-on stands detached.
- Position: add-on centre = parent centre + (96,16) px (top-left tile = parent top-left + (4,1)). Parents: ComSat/Nuclear Silo -> Command Center, Machine Shop -> Factory, Control Tower -> Starport, Physics Lab/Covert Ops -> Science Facility.
- Use `Map.addon(uid, parent_x, parent_y, owner)` after placing the parent; it writes both links. Trigger `Create Unit` cannot attach add-ons, so attached add-ons are always pre-placed.
- `tools/bw/check_addon_attached.py` (predelivery check 4 `addon_attached`, also run by `sclib.validate`) fails on any unlinked or misplaced add-on. Only Neutral (P12) add-ons may stand loose.

### Text contrast
- Briefing text uses a DIFFERENT palette (glue/tfont) than in-game text. Briefing-bright codes, ALLOWLIST: \x02 periwinkle, \x03 lime green, \x04 yellow-green, \x06 white, \x07 red (\x01 = default periwinkle). Everything else renders black or unpredictable in the briefing: \x05 grey, \x08, \x0e-\x11, \x15-\x1c, and \x1d-\x1f are not listed as working there either. Sources: staredit.net wiki "Color" and "String", topics 6880, 17573, 17796 (consistent; not verified in our own Remastered screenshot except \x0f = dark).
- The same code changes meaning: in-game \x03 yellow, \x04 white, \x06 red, \x07 green, \x02 periwinkle. Speaker names are shared between briefing and in-game lines, so they may use ONLY `sclib.NAME_COLOURS` = \x04, \x03, \x07, \x06, \x02 (bright in both). Never \x08 or player colours, \x0e, \x0f, \x1f for names.
- sclib asserts at build time: briefing text (b_trans/b_text/b_obj) only allowlisted codes; in-game text (text/trans) no dark codes (\x05,\x0e,\x10,\x15,\x18,\x1c).
- Check 21 (contrast part) in predelivery_check.py: strings referenced by MBRF actions are checked against the briefing ALLOWLIST (only whitelisted codes pass); other strings against the in-game dark list. The old check used one in-game blacklist for all strings and even listed \x0f/\x1f as allowed, so a wrongly coloured briefing name passed.

### Mineral lines (Blizzard formations), mandatory check 43
Measured on 12 pro ladder maps (38 halls) and the 38 Empire Wars campaign maps (174 halls):
- **Distance:** the nearest field is always 3 empty tiles from the town hall (left/right for a column, above/below for
  a row), the back fields 4. A field at the end of a line may come one tile closer where it sits diagonally to the hall
  (the gap stays 3).
- **Columns** (line left or right of the hall): one field per tile row, staggered one tile in and out over the whole
  line; the ends curve toward the hall. Never a straight wall with only the top and bottom field bent.
- **Rows** (line above or below the hall): mineral fields are 2x1 tiles, so a row is two rows deep: a back row and a
  front row with gaps, offset by one tile, so workers reach the back fields.
- **Corners** (L around a hall corner): a short column plus a short row.
- **Never more than 3 fields flush in one straight line**; at least a third of the fields off the line's main depth.
- **Geyser** 3 tiles from the hall on a free side (column: above or below; row: left or right; corner: the open side).
- **Variety:** campaign maps mix shapes between bases (23 of 27 Empire Wars maps with several bases). Pro ladder maps
  mostly repeat the column; ranked maps may do the same.
- **Blocker behind:** every field and geyser has water, cliff or another field within 3 tiles behind it.
- **Generator:** `tools/lib/bw/minform.py` holds the formations (column: blizzard / pairs / bulge, row: blizzard /
  zigzag, corner: long_column / long_row, each mirrored and with the geyser on either end). In a build:
  `plan = missionkit.mineral_plan(hx, hy, side, n)` before the terrain, `missionkit.paint_back(m, plan, WATER)` to
  paint the blocker, then `missionkit.res_base(..., plan=plan)` after `build_terrain()`. Without a plan `res_base`
  tries every formation for the given side(s) (`'left'`, `'up'`, `'downright'`, a list, or `'auto'`), shapes already
  used in the map last, and lets a field that does not fit the terrain step one tile as long as the line stays valid.
- **Check 43** (`tools/bw/check_mineral_line_shape.py`, in `predelivery_check.py`): FAIL when a line of 5+ fields has
  more than 3 fields flush in a straight line, fewer than n/3 fields staggered (n/4 for hall-less expansions), the
  nearest field not 3-4 tiles from the hall, a field more than 6 tiles away (lines up to 10 fields), or when all 3+
  bases of a campaign map use the same shape. Map-edge lines are exempt from the straight/stagger rules; maps named
  *Ranked* only get a WARN for the same shape; a deliberate exception needs `MINERAL_SHAPES_OK: <reason>` in the design
  note. On the reference maps the line rules pass 162 of 164 pro ladder lines (the two others: stacked fields on an
  Odyssey RE start location) and 155 of 199 Empire Wars campaign lines (fan maps; the misses are mostly 4 flush fields
  in long 10-18 field lines). The same-shape rule would hit 5 of 12 pro ladder maps (hence only WARN for ranked maps)
  and 1 of 38 Empire Wars maps.

### Town hall to resource gap (Blizzard layout), mandatory check 21
- Geyser or gas building: **3 to 5 empty tiles** between its footprint and the town hall. Nearest mineral fields: 3 tiles (check 43; check 21 still accepts 2 to 4). A refinery, extractor or assimilator touching or almost touching the main is wrong.
- Root cause in 2026-10: `sclib.base()` put the lower geyser at `hy+4` (1-tile gap), up/down at `hx±6` (2-tile gap). Fixed to `hy+6` and `hx±7`. The old `expo()` helpers picked the *nearest* slot that passed resback, including `y+4`. Candidates are now `y-5`/`y+6`. LY3's "step toward the hall" fix shrank gaps to 2. Never move a geyser closer than a 3-tile gap to satisfy another check.
- Check: `tools/bw/hall_gap.py`, wired into `predelivery_check.py` as check 21 (FAIL).
- Resource backs: prove each geyser slot (`gy_at`) against the FINAL built map (autofix changes the walk map), with all other units present, not just hall+geyser. Mineral field footprint = tiles c..c+1. Keep ramps clear of mineral rows.
- A resback exemption file is a last resort; new missions must pass without one.

### Rescue scenes
- Rescuable units must never stand idle among hostile units within attack range. Zerg do not take prisoners. Use a plausible setup instead: survivors hidden or entrenched away from enemies (bunker, walled pocket, high ground), or under active attack (set the enemy hostile to the rescuable player so the fight is real and the player must hurry).
- Check 22 in `predelivery_check.py` (FAIL): a unit of a rescue-role player (OWNR Rescuable, or a computer player whose units a trigger gives to the human) must not start within 8 tiles of an enemy unit. It passes only if they really fight: the enemy is set hostile by trigger (Set Alliance Status, Enemy), or the rescue player is a computer in another force that is never set allied. Allied by trigger = always FAIL.

### Objectives, reveals and custom units
- New objectives must be introduced by a character transmission or short scene right before they appear, never silently.
- Objectives and side quests appear only after the opening scene's transmissions have finished, never during them.
- Reveal timing: if a special unit/mechanic can be seen before its quest/explanation, reveal the explanation no later than the first sighting of that unit.
- Never show unexplained timers or mechanic buildings.
- Quest structure varies: not always 1 main + 2 side quests (credits excluded). Per mission vary it: 2-3 main objectives, none/one/several side quests, objectives added or changed mid-mission. Note the structure in the Design_Note; across a campaign no two consecutive missions share the same count pattern (checked by comparing Design_Noteen).
- Side quests are introduced early: via a character line, scout, rumour or minimap ping before the player reaches the site, not only on arrival. Arrival discovery only as justified mission design (`ARRIVAL_DISCOVERY_OK: <quest var> :: reason`). Check (WC3 tool only; for BW review the trigger list manually): FAIL an optional quest discovered only by a proximity trigger/range poll at its own site with no earlier hint outside that chain (ping near the site, or a line naming a title word).
- Side-quest timing: side quests are announced only some time after the first main sequence, about 60-120 s after the opening transmissions end, but still well before the player reaches the site. Exception only as mission design: Comment `SIDEQUEST_TIMING_OK` in the announcing trigger. Check: predelivery check 30 FAILs the first 'OPTIONAL' announcement (Display Text/Transmission) <60 s after the intro end (first Set Mission Objectives, else end of the opening triggers), timed via Elapsed Time / switch chains / Waits and transmission durations.
- Custom units: every new unit needs a visible purpose (attack/abilities, or a special role explained by its unit name, the briefing or a transmission, with a visible message/effect when the role triggers).
- Choice beacons use distinct colours, are reachable, and the text names which colour means what.
- Scripted camera centring (Center View) must show the unit or place the text talks about, at that moment, with nothing large in the way.

### Triggers and spawns
- Units created by trigger: small, staggered groups (2-4) released one after another at measured free spots (open, walkable, free of buildings and doodads) with a visible source (nydus, cave, portal, drop).
- Mutually hostile enemies mainly target the player. Story fights between enemies must actually happen: temporarily set them hostile with alliance triggers, then restore.

### Doodads (purpose)
- Every notable doodad or sprite is purposeful scene dressing tied to units, camps, settlements, objectives or the place's story. There is no random filler.
- Story-implying props (campfires, crates, barrels, tents, banners, wrecks, statues, ruins, pillars) need nearby units that explain them (enemies, neutrals, critters or a story object referenced by triggers or objectives). Otherwise remove them.

### Cliffs and rock blocks blend in
- Cliffs, ramps and rock blocks must blend seamlessly into the surrounding terrain with proper edge tiles. Never a lone cliff/rock/ramp block that looks like a cliff but is not one, never straight hard seams.
- Real cliffs come from ISOM (always blended). A ramp doodad only where it joins an actual ISOM cliff between two levels.
- Generator: sclib `place_doodads` and `place_ramps` reject a placement whose max single border-edge colour step > `DOODAD_EDGE_PEAK` (15); the mean-only score (5.0/6.0) missed real seam blocks (mean 3.8-5.3, peak 16-28).
- Predelivery check 26 (`seams.doodad_peaks`): FAIL for any DD2 tile doodad with a border edge step >15. Heuristic (pixel colours; the CV5 edge-type data and VF4 heights for Remastered megatiles are not available here), so it may also flag a few blocks that look acceptable; look at the render before exempting.

### Placement and generator pitfalls
- Buildings only on legal ground with no overlaps, and units only on reachable ground. Run the placement check `tools/bw/placecheck.py MAP.scx TILESET` (legal build tiles, no overlaps, reachable units; `placecheck.autofix(m)` in build scripts) and the trigger simulator `tools/bw/trigsim.py` (`trigsim.prove(map, scenario)`); `tools/bw/example_mission.py` runs both.
- Every map has a unique layout. No reused templates. Map edges look natural: a mix of cliffs, water/space/lava (fitting the tileset), normal ground and blended doodads. No straight seams.
- `missionkit.Grid` (`tools/lib/bw/missionkit.py`): place the STARTLOC before `g.ok(hall=True)`; its main component drives the ring check.
- Unit ids: Missile Turret 124, Bunker 125 (`sclib.TURRET`, `sclib.BUNKER`; check older scripts that swapped them). Power Generator 200 is 4x3.
- Fords/land bridges need width ≥2.4, or the banks disconnect after autofix.
- `tools/bw/trigsim.py` does not model combat, rescue by touch or Preserve Trigger; subclass it for preserve (act 3) and log create/order locations. In proof scenarios, SPAWN P1 units at targets (moving them strips earlier objectives). Check counter-attacks via order destinations, not create locations.
- Exclude an effect-only player (a slot that only owns scripted effects or map revealers) from wave-escalation checks.

### Gas buildings need a town hall
- Never place a Refinery, Extractor or Assimilator without its own owner's town hall nearby (about 12 tiles). Only exception: mission design with a reason (e.g. a captured or abandoned outpost), listed in <map>.gas_ok.json.
- Enforced by predelivery_check.py check 25 (FAIL; exemptions in <map>.gas_ok.json {"sites":[{"pos":[tx,ty],"reason":"..."}]}). Note: checks only PRE-PLACED gas buildings; an AI expansion can build its own Hatchery+Extractor, and if the player kills the Hatchery the Extractor stays - that is engine behaviour, not a placement error. If unwanted, give the free expansion no geyser or limit the AI script.

### Allies share vision
- Every player allied with a human player shares vision with them both ways: a force with the Allies flag also gets the Shared vision flag; an alliance set by trigger gets Run AI Script 'Turn ON Shared Vision for Player N' in the same trigger. The trigger owner receives player N's vision, so each side runs it in its own alliance trigger. When the alliance ends, the same trigger turns the vision off again.
- sclib adds this automatically on save next to every `m.ally()` and sets the force flag; exempt a player with `m.ally_no_vision=(p,)` plus `ALLY_NO_VISION_OK: P<n> :: reason` in the design note.
- Vision starts exactly when the alliance starts, never earlier. A computer player that only becomes a real ally through a mid-mission event (pact, rescue, change of heart) shares no vision before that event, even if it is set to Ally from the start only so that both sides do not fight (a truce). Turn vision on in the trigger of that event, both ways, together with Set Alliance Status Ally. Write the moment into the design note: `ALLIANCE_STARTS: P<n> :: start` or `ALLIANCE_STARTS: P<n> :: switch <k> :: <event>`.
- Note for sclib maps: the automatic vision next to every `m.ally()` would also fire for a truce set at mission start, so such a map must add its vision explicitly at the event instead.
- Enforced by predelivery_check.py check 35 `ally_shared_vision` (FAIL; `tools/bw/check_ally_vision.py`): vision ON only in a trigger that sets that alliance; with `ALLIANCE_STARTS ... switch <k>` no vision at mission start or outside triggers conditioned on switch k; a mid-mission alliance change without an `ALLIANCE_STARTS` line is a FAIL.

### Opens in ScmDraft 2
- A delivered map must open in ScmDraft 2. Check 34 `scmdraft_open` (`tools/bw/check_scmdraft_open.py`, FAIL; static lines `chk_required_sections`, `chk_section_sizes`, `dd2_named_doodads`): every DD2 doodad must be a named tileset doodad (cv5 group name != 0; ScmDraft aborts the whole load on one unknown id), and fixed-size CHK sections must have their exact size (e.g. UNIS 4048 bytes; a 4000-byte UNIS plays in StarCraft but ScmDraft refuses it).
- With the wine harness installed (`tools/bw/scmdraft_harness/README.md`) the check also opens the map in the real ScmDraft 2 and requires '(ENGINE) Loaded map'. The static part alone is a proxy; say which one ran.

### Delivery
- Run `tools/bw/predelivery_check.py` (all checks incl. 19-25, 34-41), the placement check (`tools/bw/placecheck.py`) and the trigger simulation (`tools/bw/trigsim.py`). Deliver only with 0 FAIL. Say honestly what was not tested in-game.
- Render a preview PNG per mission, with the hero colour shown correctly. Send a top-down minimap PNG with every map.

---
- **Ability-gated obstacles need a hint (fixed rule):** if something in a mission can only be destroyed or opened with a specific ability (BW examples: a burrowed/cloaked blocker that needs detection, a neutral Command Center only a Queen can infest, a target only a sieged tank outranges), the player must be told before it is needed. The hint can be subtle: a transmission, the mission objectives text or a visible clue next to the obstacle. Exceptions are easter eggs, secret paths and deliberate mission design, marked with `HINT_OK: <reason>`. This applies especially to obstacles only a specific unit or tech can clear: mineral walls only workers mine, structures only a caster or detector can reach, triggers keyed to a unit type. Give the hint in a briefing or mission transmission, or mark the obstacle with `HINT_OK: <reason>` in the design note.

## 2. Classic standards (classic defaults)
Apply unless the Design_Note records a deviation with a reason (campaign: "Campaign rules"; mission: "Mission design deviations").

### Attack announcements
- Default is NO warning text like "The X are marching on Y!" before/at enemy waves. Allowed only occasionally when a mission design note explicitly justifies it, or as a deliberate campaign-wide feature (campaign rule ATTACK_WARNINGS).
- Check 19 in `tools/bw/predelivery_check.py` flags attack announcements in Display Text/Transmission; approve deliberate ones with `ANNOUNCE_OK: <reason>` (or `<substring> :: <reason>`) in <map>.announce_ok.txt beside the .scx, or the check fails.

### Base elevation trope
- Enemy AND player bases are NOT on high/mid ground by default. Use normal/varied elevation; raised only with mission justification, rarely, never as a recurring pattern.
- Check 20 in `tools/bw/predelivery_check.py` (`tools/bw/base_elevation.py`): CV5 height (0x400 high, 0x200 mid) at each CC/Nexus/Hatchery/start vs the walkable ring median at 12-24 tiles. >1 unapproved raised = FAIL, 1 = WARN. Approve in `<map>.highground_ok.json` `{"bases":[{"hall":[tx,ty],"reason":"..."}]}`. Campaign summary: `python3 tools/base_elevation.py *.scx` (WARN if >1 in 4 missions).

### Heroes
- Hero acquisition: a hero who joins (rescued, arrives, recruited) is always part of the main storyline, through a scripted event or a required objective. Never make it an optional side quest.
- Heroes normally stay with the campaign once they join (a hero for one mission only is mission design, see level 4).

### Objectives and balance
- Objective vs. conquest balance: fulfilling the objectives must be clearly easier than destroying all enemy bases. Make the bases strong and fortified (layered static defence, defender groups, rebuilding, reinforcement waves) unless conquest is itself the objective. In the Design_Note, estimate the effort for both paths (enemy HP, defence, travel distance) and require objective effort <= about 75% of conquest effort. When in doubt, make the bases stronger rather than the objectives easier.
- Typically 1-2 main objectives plus optional quests of varied types (see "Side objectives vary"; destroy is one type among many) whose reward follows from the objective (see "Rewards make sense in the story"); vary the structure (see fixed rules, quest structure). Sidequests should still be a real challenge.
- Main objectives vary: hold a position for a time, escort, rescue, recover an artifact, stealth with a small group, stop a ritual/portal, capture points, hunt a leader, evacuate/flee, survive. "Destroy the main base" only when the story calls for it; never the default.
- The difficulty curve is fair: mission 1 is easy, and difficulty rises per chapter. Offer difficulty levels that scale enemy strength.
- Pacing: a calm build-up phase, waves that grow, and the climax at the end. (Waves carry no warning text by default, see attack announcements.)
- Big waves come from real producing enemy bases. Destroying a base visibly reduces the pressure.
- **Start setups vary and the player builds (fixed rule).** What the player owns at mission start follows the story and changes from mission to mission, as in the Blizzard campaigns (57 released missions: 32 % build-up, 28 % no base or hero squad, 23 % small base, 18 % established base). Default: a small core to build up from (a hall, 2-6 workers, at most one tech building, a small squad); the player builds the rest. A larger base only with a story reason (held for a long time, a captured fortress, a base under siege).
  - No static defence at start by default; more than 2 towers only for a defence, survival or fortress mission, with a reason. Never more than 2 unmorphed Creep Colonies (a building off creep means a smaller layout, not extra colonies; `placecheck.autofix` moves player buildings onto creep or stops with a clear message instead of adding colonies) and never more than 8 workers.
  - New tech is earned: a newly unlocked tech building is built by the player, not pre-placed; a newly unlocked unit appears at most as a sample of 1-3 to introduce it. SHOWCASE situations come from the map, not from a handed-over army.
  - Starting supply means enough Overlords/depots and minerals for the first builds, not a pre-placed army.
  - Never reuse the previous mission's start block; consecutive missions differ in type or composition, and never three established starts in a row.
  - Design note: `START_SETUP: <no-base|build-up|small-base|established> :: <story reason>`; `START_DEFENSE_WHY: <what> :: <reason>` for more than 2 towers; `START_GIFT_WHY: <unit or building> :: <reason>` for a ready new building or more than 3 of a new unit.
  - Check: `tools/bw/check_start_setup.py` (`start_setup_variety`, predelivery check 44; compares with the two previous missions `M<n-1>`/`M<n-2>` in the same folder when present). Single map: `python3 tools/bw/check_start_setup.py MAP.scx --prev PREV1.scx PREV2.scx`; whole campaign: `--campaign M1.scx M2.scx ...`.
- Tech progression: each later mission of a campaign unlocks MORE tech than the one before (new units, buildings, upgrade levels or techs), gradually as in the Blizzard campaigns. Same tech only as justified mission design, `TECH_SAME_OK :: reason` in the Design_Note / <M>_build_info.json / <map>.tech_ok.txt (e.g. hero squad without base). Placed or trigger-given units are not tech. A mission after the full race tree is exempt automatically. Check 31 of predelivery_check.py compares PUNI/UNIx, PUPx/UPGx, PTEx/TECx with the previous mission M<n-1>/ML<n-1> in the same folder.
- Air units must be plausible for the plot. Never use them in indoor or installation missions; installation missions are usually branching, maze-like and without buildings.
- Mark important areas in the world itself (effects, warning text with sound, all-clear notice), not only on the minimap.

### Terrain, resources and map
- Terrain varies: visible cliffs, wide plateaus with plenty of ramps (often with enemy buildings or units on top, but bases themselves not raised, see above). Paths and build areas stay readable.
- Resource fields have their backs against cliffs, water or dense doodads.
- Mineral amounts: mineral fields may and should hold varied amounts (e.g. 500/750/1000/1500, or small 250 patches for blocked or low fields), with mission logic: a rich main, poorer or richer expansions, depleted outposts. Do not always use a uniform 1500.
- Defences stand at the chokes enemies actually attack from.
- Maps don't need to be square.
- Open clearings with a single lone object (pillar, cage etc.) feel empty: give such places meaning (creep camp, quest, story event, reward, ambush) and dress them accordingly.
- Natural ambient detail: spread small, unobtrusive, non-blocking decorations generously (small rocks, plants, tileset-fitting details), off build spots, ramps and paths.

---
## 3. Campaign rules — optional, NOT defaults
These are NOT standards. Listed per campaign in its Design_Note under "Campaign rules"; everything else follows the classic defaults. Checks read this before allowing exceptions. Campaign rules can never override a fixed rule.
Prepared catalog (never default):
- ATTACK_WARNINGS: enemy waves announced as a story feature.
- MORAL_CHOICES: branching choices affecting later missions.
- SIGNATURE_MECHANIC: one recurring special mechanic, introduced on first sighting.
- HERO_FOCUS: more hero/commando missions than usual.
- RESTRICTED_TECH: deliberately reduced tech beyond normal unlock pacing.

---
## 4. Mission design
> **Invent freely:** you are always welcome to invent your own new ideas and are NOT limited to the catalogs. The lists are inspiration, not a menu; every example is only an example. Full classified catalogs (gameplay vs story): `docs/campaign-design-catalog.md`.
Per-mission decisions, each recorded in the mission's Design_Note under "Mission design deviations" with a reason. May override classic defaults and campaign rules, never fixed rules. Examples:
- A hero who is present for only one mission (guest hero, departs or dies by story).
- A justified raised base (fortress siege, story) -> also listed in `<map>.highground_ok.json`.
- A gas building without a hall (captured or abandoned outpost) -> also listed in `<map>.gas_ok.json`.
- A deliberate attack warning in one mission -> `ANNOUNCE_OK` reason.
- Conquest as the objective itself (then the objective-vs-conquest balance does not apply).
- An established base at start (4+ tech buildings) when the story says so (`START_SETUP: established :: reason`); an installation mission (maze-like, no buildings, no air).
- A one-off special mechanic in this mission (still introduced by a transmission or scene, see fixed rules).
- Intro cinematic concept: not the template "enemy base, then own base". Each intro follows the mission's story (heroes talking in the landscape, arrival by ship or march, flashback, a raid already under way, staying with the enemy, or almost no intro); justify the choice in the Design_Note under mission design.
- Side quest discovered on arrival, only with a reason (`ARRIVAL_DISCOVERY_OK`).

- **Single-resource expansions:** expansions with only mineral fields or only geysers are allowed occasionally (rarer than mixed expansions), placed with mission logic. Gas-building-needs-hall (check 25) still applies once the player builds there.

- **Temporary reveals:** when enemy positions are shown only briefly, create a temporary Map Revealer and remove it again after the scene; permanent vision only as justified mission design. Predelivery check 28: every Map Revealer created by trigger must be removed later (Remove/Kill Unit of Map Revealer) unless a Comment action in that trigger says REVEAL_PERMANENT_OK. sclib `T()` auto-appends the removal; helper `m.reveal(p,loc,hold_ms)`.
  This applies to every event that does not need to stay visible (not only enemy positions).

- **Scenes are visible from their first line (fixed rule).** When an in-mission dialogue centres the camera on a location (or a Transmission speaks at one), the player sees that location from the first line, never a black screen. One of: the alliance and its shared vision start at or before the first line (not in a later trigger); or a Map Revealer for the human is created at the location before the first line, with Center View, and removed after the scene unless the vision should stay (`m.scene_reveal(loc, player, remove_after=True)`; `remove_after=False` needs a reason); or the player's own units stand there at that moment (a Bring condition, units given in the same trigger, pre-placed units).
  - Design note: `SCENE_VIEW: <scene> :: <location name> :: <alliance-vision | revealer | own units present>`, one line per located scene.
  - Check: `tools/bw/check_scene_view.py` (`scene_location_visible`, predelivery check 45). A Center View scene without vision at the moment the camera arrives is a FAIL; a Transmission-only scene is a WARN. It simulates pre-placed units, units created or given by earlier triggers (mission start, or triggers that set a switch the scene requires), shared vision turned on by then, and live revealers; units that walk there cannot be proven, so 'own units present' in the note turns that FAIL into a WARN.

- **Escort missions are real escorts (fixed rule).** Trace every route before building. An escort route covers at least about a third of the map width or several minutes of travel and runs through dangerous ground: ambushes, chokes held by the enemy, patrol or base range, triggered attacks. The escortee cannot survive the route alone, and every threat on it is reachable by the player's ground units without breaking an enemy base first. A short walk through safe ground (the player has nothing to do) is not an escort.
  - Design note: `ESCORT_ROUTE: <escortee> :: <length tiles/time> :: <threats with locations> :: <what the player must do>`, and the route drawn in the routes PNG.
  - Check: `tools/bw/check_escort_route.py` (`escort_route_challenge`, predelivery check 46). It finds Order actions for an allied computer player whose destination is a Bring objective, pathfinds each leg over walkable ground, and FAILs a route shorter than a third of the map width, fewer than 2 threat encounters (enemy armed units, Bunkers, Sunkens or Cannons within 7 tiles of the path, enemy units created or ordered to a location within 3 tiles of it; threats within 10 path tiles count once), an encounter point the player cannot reach by ground without breaking through enemy buildings, or a missing ESCORT_ROUTE line. Whether the escortee could survive alone stays a design-review question.

- **Neighbouring missions play differently (fixed rule).** Two missions in a row must not share the same objective type and pressure (two "destroy 3 specific structures within a time limit" chapters back to back), nor the same objective type and target count. Vary the type (destroy targets, conquest, escort, hold, rescue, hero, reach, capture), the pressure (time limit, waves, hold timer, none) and the count; plan this in the campaign outline before a chapter is built.
  - Design note: `MISSION_TYPE: <objective type> :: <pressure> :: <target count>`; a deliberate repeat needs `MISSION_TYPE_REPEAT_OK: <reason>`. The campaign outline is a table with a Goal (or Pattern) column.
  - Check: `tools/bw/check_mission_type_variety.py` (`mission_type_variety`, predelivery check 47; `--prev` takes previous maps or design notes, otherwise M<n-1>/M<n-2> next to the map are used). It also infers type and pressure from the triggers (initial objectives text, countdown with defeat or victory at 0, an escort order) and FAILs a missing or wrong line. `--outline NOTE.md` lints the outline table: neighbouring chapters with the same pattern are a WARN.

- **Enemy mineral amounts:** enemy base mineral fields about 2500-4000 per field (varied); 5000-8000 was far too much. Predelivery check 29 WARNs above 4000 on enemy fields (within 12 tiles of a computer town hall); check 5 floor is now 2500. sclib `base(...,enemy=True)` defaults to varied 2500-4000 and clamps at 4000.

- **Character names must not sound like (pronunciation) a well-known Warcraft/StarCraft character unless the story connects them; cross-check each new name by ear (e.g. Garosh ~ Garrosh is too close, Vashi vs Vashj is fine).**

## Testability: challenge first, then "not testable"

- Before anything counts as "not testable", challenge the assumption and try to create the condition:
  - terrain: place water, a cliff, high ground or doodad units in the test
  - matching targets: air, cloaked/burrowed units, hallucinations, casters with energy (Set Energy), hero variants, mechanical/biological targets
  - tech (Tech/Upgrade Settings, unit availability), triggers, dummy units, kill/create unit, Set Resources, game speed
- Every remaining WATCH needs a written reason why no measurable way exists (in the test plan/Design_Note and in the log/guide). "Too much effort" is not a reason.
- Applies equally to mission tests, trigger checks and test maps.

## Resource placement on walkable ground
- Mineral fields and Vespene geysers must sit entirely on walkable, buildable-height ground: never on water, deep water, lava, space/void, cliff edges or unwalkable doodad tiles.
- Every tile under each resource footprint (mineral 2x1, geyser 4x2) plus the worker harvest ring around it must be walkable, and the base's town-hall spot must reach it by ground.
- Automated check before every delivery: scan all mineral/geyser units against the MTXM tile walkability (and minitile flags); any footprint or harvest tile on water/unwalkable = FAIL. Applies to campaign, ranked and fun maps alike.

## ScmDraft compatibility
- Every SC:BW map I make must open in the editor ScmDraft 2 without errors: valid CHK sections/sizes (VER, DIM, ERA, MTXM, UNIT, THG2, STR etc.), no unknown/overlapping sections, valid string table, standard MPQ (staredit\scenario.chk).
- Automated check before delivery: strict CHK parser validation (ScmDraft-like) plus re-save round-trip; deliver only if it passes.

## Ask the user how new content gets tested (required step)
Before building a campaign, mission or fun map that contains new or changed units, heroes, buildings or abilities, the agent must ask the user whether all new content should be tested before the map is delivered, and offer two options:
- **A – the agent tests in-game itself.** Only if the user explicitly grants access to their PC and the game. Without that explicit permission, never touch the user's machine.
- **B – a generated test map the user plays.** Built with `tools/wc3/race_testmap/gen_testmap.py` (see `docs/race-test-harness.md`); the test map spawns every new unit/hero and runs scripted tests, writing `results.txt`.

The test covers: every ability (casts, effects, targets, autocast), requirements and tech reachability (research, training, hero learning), models, icons (including hero learn icons), hero glow and imported assets, and tooltips/hotkeys. Record the answer in the design notes; if the user declines testing, say in the delivery that the new content is untested in-game.

For Brood War: the same question applies to changed units (unit/weapon/tech data in the map); option B is a small BW test map that places each changed unit against targets.

## Briefing and voiced dialogue (fixed rule)
- Every campaign mission has a briefing (MBRF): objectives (`m.b_obj`), speaking portraits (`m.b_portrait`) and voiced lines (`m.b_trans`, built with `m.B(...)`), ending with `m.b_end()`. Predelivery check 36 FAILs an empty briefing. Exception only as mission design: `NO_BRIEFING_OK: <reason>` in the Design_Note.
- Every story line (briefing and in-mission) is voiced: `snd=m.voice(key,text,script=...,speaker=...,profile=...,**CAST[who])` renders a WAV with TTS and embeds it; in-mission lines use `m.trans(text,portrait_unit,loc,snd)` (Transmission), not Display Text. Display Text is for status lines (counters, "OBJECTIVES UPDATED"), never for a character speaking. Predelivery check 37 FAILs a campaign mission with 0 voiced lines or with speaker lines ("Name: text") shown as plain text. Exception only as mission design: `NO_VOICE_OK: <reason>` in the Design_Note.
- Voice engine: edge-tts (online Microsoft service; `pip install edge-tts`, plus ffmpeg). Output rights and alternatives: DEPENDENCIES.md "Voiced dialogue for Brood War". If the engine is not available, stop and tell the user; never ship a text-only mission silently.
- Worked example: `tools/bw/example_mission.py`.

## Rewards make sense in the story (fixed rule, same rule for WC3)
Never hand out flat minerals, gas or units for an unrelated deed (400 minerals for building a Nydus Canal, a squad
appearing because three enemies died). The reward follows from what the objective is in the story; ask "what does
the player actually gain by doing this?" and give exactly that, with an in-world source the player sees. Examples:
- freed prisoners or a rescued squad join (rescuable player, standard BW rescue, or Give Units when the player reaches it);
- a captured depot or refinery hands over the resources it stores, a captured base stays the player's;
- a saved scientist or a protected facility unlocks tech;
- a won ally sends troops or joins the fight (Give Units, alliance);
- a scout's report or a taken watchtower reveals the map or the enemy's route;
- seized convoy cargo is whatever the convoy carried (the convoy is visible before it is stopped).
Resources are the right reward exactly when the objective really yields them (a depot, cargo, a mine); units, tech or an
ally are right when the objective yields those. No objective needs a reward: a side objective can simply matter for the
story or make the mission easier.
Write one Design_Note line per reward:
`REWARD_WHY: <objective> :: <reward> :: <in-world source the player sees>`
Predelivery check 41 (`tools/bw/check_story_delivery.py`) FAILs a non-start trigger that adds minerals/gas to a human
player (Set Resources, Add), or gives units to / creates units for a human player after an event, without a matching
REWARD_WHY line (the amount for resources, a unit name or group word for units). Sources such as "reward" or "bonus"
are rejected. Non-quest income that the story explains (a timed supply drop) carries a Comment action
`INCOME_OK: <reason>` in that trigger. Worked example: the rescued squad in `tools/bw/example_mission.py` hands over
its depot and bunker.

## Side objectives vary (fixed rule, StarCraft)
"Destroy a building on the side" is the side objective an agent reaches for by default, and players notice it fast.
Side objectives are optional and varied; a mission without one is fine.
- Pick from: rescue or free a unit that then joins, capture or protect a place or building, reach or hold a place,
  escort, gain an ally, a secret (hidden path, hidden base), a choice with a consequence. Destroy is one type among
  these, not the default.
- At most one destroy side objective per mission, and never in two neighbouring missions.
- The reward follows from the objective (see "Rewards make sense in the story"); a destroy side objective does not
  automatically pay resources.
- Design note, one line per optional objective:
  `SIDE_OBJECTIVE: <name> :: <rescue|capture|protect|reach|hold|escort|ally|secret|collect|choice|destroy|other> :: <units|tech|base|ally|info|none|resources>`;
  a deliberate repeat needs `SIDE_OBJECTIVE_REPEAT_OK: <reason>`.
- Predelivery check 50 side_objective_variety (`tools/bw/check_side_objective_variety.py`) reads these lines and the
  map (optional objectives in the Set Mission Objectives texts, triggers that add resources) and compares with the
  previous mission M<n-1> (its design note, or its map objectives). It FAILs optional objectives without
  SIDE_OBJECTIVE lines, more destroy-type optional objectives in the map than declared, more than one destroy side
  objective, or a destroy side objective here and in the previous mission. Whether a reward fits is the REWARD_WHY
  line's job (check 41).

## Destroy targets survive morphing (fixed rule, StarCraft)
A Zerg building that morphs changes its unit type in place: the engine moves the unit count from the old type to the
new one and records no death (OpenBW `bwgame.h`, `morph_unit`: unit counts -1 for the old type, reinitialize the type,
+1 for the new type; no kill). Consequences for triggers:
- `Bring/Command exactly 0 Hatchery` becomes true when the Hatchery becomes a Lair: the objective is "done" though
  nothing died.
- `Bring/Command at least 1 Hatchery` becomes false: waves gated on "the hatchery stands" stop.
- `Deaths of Hatchery` never counts the target once it morphed; it dies as a Lair or Hive.
Chains: Hatchery -> Lair -> Hive, Creep Colony -> Sunken or Spore Colony, Spire -> Greater Spire. Terran buildings that
can lift off (Command Center, Barracks, Factory, Starport, Engineering Bay, Science Facility) can leave a location
without dying: use Command (anywhere) or Deaths, not "Bring exactly 0 at a location". A Queen-infested Command Center
changes owner to the Zerg player, so for the Terran owner it is gone.
- Generator (sclib): `m.target_gone(p, HATCH, loc)` returns the conditions "exactly 0 of every chain type" for one
  trigger; `m.target_stands(p, HATCH, loc)` and `m.target_killed(p, HATCH)` return alternatives, one per chain type;
  `m.T_each(players, conds, alts, acts, switch=k)` writes one trigger per alternative and runs the actions once.
  Worked example: the hatchery victory and the wave triggers in `tools/bw/example_mission.py`.
- Predelivery check 49 destroy_target_morph_chain (`tools/bw/check_morph_chain.py`) FAILs a human-owned trigger with an
  "exactly 0" condition on a chain type without the later chain types in the same trigger, or an "at least" or Deaths
  condition without sibling triggers for the later chain types; the same in computer-owned triggers is a WARN, and so
  is "exactly 0" of a lift-off building at a location.
- Fixtures: `python3 tools/bw/selftest_side_and_morph.py` (each check fails on a bad case and passes on a good one).

## Voice delivery notes (fixed rule, same rule for WC3)
Every voiced line carries delivery notes in VO markup v1 (`docs/voice-delivery-markup.md`): `[emotion: ...]` first,
`*stress*`, short pauses `(0.3)`/`(beat)`/`...`/` - ` (0.1-0.6 s, inside the line only; the <= 1 s gap between lines
and immediate interruptions stay), `[pace: ...]`, stage directions such as `[whisper]`. Pass it as
`Map.voice(key, text, script="[emotion: cold] Then let them *come*. (0.35) ...", speaker="Vessirak", profile="...", **CAST[...])`;
the subtitle stays `text`. edge-tts accepts no SSML, so sclib renders the script segment by segment (real silence,
per-segment rate/pitch, local stress). Write `Map.write_voice_script("<map dir>/Voice_Script_<map>.md", "<title>")`
before saving; `tools/bw/check_voice_delivery.py` (predelivery check 33) FAILs lines without notes, a short clause,
exclamation or beat without stress/pause marker, and speakers without a voice profile.
