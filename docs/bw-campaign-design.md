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
- **Showcase:** every unit, hero or ability NEW in a chapter gets situations in that map where it can fulfil its role and use its abilities well (healer -> wounded allies, siege -> structures/walls, anti-air -> air enemies, detector -> invisible units, caster -> targets worth casting on, mobility -> terrain to cross). Document per new unit in the Design_Note: `SHOWCASE <id> :: <role> :: <abilities> :: <concrete map situation: place, phase, what the enemy brings>` (new ids via `NEW_IDS:` or race json minus `PREV_IDS:`). Check: `check_showcase.py` (warcraft3/tools; FAIL missing/thin line, WARN situation lacks fitting targets).
- **Characters:** every named speaking character gets in the Design_Note `## Characters` one entry (`### Name`) with `Trait:` (distinct trait), `Goal:` (personal goal beyond the mission objective), `Weakness:` (flaw / inner conflict), `Voice:` (recognisable speech voice: rhythm, vocabulary), `Quirk:` optional, `Tone:` (temperament: serious, funny, cynical, cold, warm ...; the cast must mix tones) and `Moments:` (where this mission reveals something about them). Optional but encouraged: `Relationships:` (relationships and friction with the other characters; how they treat underlings vs superiors), `Secret:` (private secret or backstory hint, revealed slowly), `Arc:` (small arc across chapters), `Speech:` (vocabulary, sentence length, rhythm), plus a contradiction in each character and one surprising moment each. Trait catalog: attitude to others (spiteful, arrogant, warm, caring, distrustful, jealous, blindly loyal, servile-up/harsh-down, flattering, parental, aloof, chummy); worldview (confident, naive, cynical, fatalistic, superstitious, fanatic, idealistic, pragmatic, hardened, fearful, curious, nostalgic); drive (ambitious, greedy, vengeful, duty-obsessed, glory-seeking, lazy, content, guilt-driven, approval-seeking, controlling); temperament (hot-tempered, stoic, nervous, impulsive, deliberate, melancholic, exuberant, dry-humored, grumpy, calm); intellect/demeanor (know-it-all, cunning, simple, well-read, boastful, modest, vain, pedantic, chaotic, taciturn, chatty); moral grey (cowardly but honest, cruel but just, lies out of pity, keeps promises at any cost, betrays out of conviction). Every mission contains reveal moments: banter, a disagreement, a personal stake, a choice. Characters develop across chapters (a tic changes at a turning point, a relationship shifts). Main characters need >= 3 lines that are not just orders/objectives. Check: `check_characters.py` (tools/wc3, linked in tools/bw; FAIL missing section/fields/entry or single shared Tone, WARN < 3 non-functional lines). Techniques that worked:
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
- Mandatory check 23 in `tools/predelivery_check.py` (`tools/unit_damage.py MAP.scx`): FAIL if any armed unit (placed, buildable or customised, heroes included) has 0 damage, or UNIS (4048 B, 100 weapons) and UNIx (4168 B, 130 weapons) disagree / have wrong size.

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
- Mandatory predelivery check 24 (`tools/core_tech.py`). check_tech.py missed it because it skips techs that are disabled.

### Text contrast
- Briefing text uses a DIFFERENT palette (glue/tfont) than in-game text. Briefing-bright codes, ALLOWLIST: \x02 periwinkle, \x03 lime green, \x04 yellow-green, \x06 white, \x07 red (\x01 = default periwinkle). Everything else renders black or unpredictable in the briefing: \x05 grey, \x08, \x0e-\x11, \x15-\x1c, and \x1d-\x1f are not listed as working there either. Sources: staredit.net wiki "Color" and "String", topics 6880, 17573, 17796 (consistent; not verified in our own Remastered screenshot except \x0f = dark).
- The same code changes meaning: in-game \x03 yellow, \x04 white, \x06 red, \x07 green, \x02 periwinkle. Speaker names are shared between briefing and in-game lines, so they may use ONLY `sclib.NAME_COLOURS` = \x04, \x03, \x07, \x06, \x02 (bright in both). Never \x08 or player colours, \x0e, \x0f, \x1f for names.
- sclib asserts at build time: briefing text (b_trans/b_text/b_obj) only allowlisted codes; in-game text (text/trans) no dark codes (\x05,\x0e,\x10,\x15,\x18,\x1c).
- Check 21 (contrast part) in predelivery_check.py: strings referenced by MBRF actions are checked against the briefing ALLOWLIST (only whitelisted codes pass); other strings against the in-game dark list. The old check used one in-game blacklist for all strings and even listed \x0f/\x1f as allowed, so a wrongly coloured briefing name passed.

### Town hall to resource gap (Blizzard layout), mandatory check 21
- Geyser or gas building: **3 to 5 empty tiles** between its footprint and the town hall. Nearest mineral fields: 2 to 4 tiles. A refinery, extractor or assimilator touching or almost touching the main is wrong.
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
- Buildings only on legal ground with no overlaps, and units only on reachable ground. Run the placement check (legal build tiles, no overlaps, reachable units) and the trigger simulator.
- Every map has a unique layout. No reused templates. Map edges look natural: a mix of cliffs, water/space/lava (fitting the tileset), normal ground and blended doodads. No straight seams.
- fortify.Grid: place the STARTLOC before `g.ok(hall=True)`; its main component drives the ring check.
- sclib TURRET/BUNKER constants are swapped (use 124/125). Power Generator 200 is 4x3.
- Fords/land bridges need width ≥2.4, or the banks disconnect after autofix.
- trigsim does not model combat, rescue or preserve; subclass it for preserve (act 3) and log create/order locations. In proof scenarios, SPAWN P1 units at targets (moving them strips earlier objectives). Check counter-attacks via order destinations, not create locations.
- Exclude the P5 effect/uplink player from wave-escalation checks.

### Gas buildings need a town hall
- Never place a Refinery, Extractor or Assimilator without its own owner's town hall nearby (about 12 tiles). Only exception: mission design with a reason (e.g. a captured or abandoned outpost), listed in <map>.gas_ok.json.
- Enforced by predelivery_check.py check 25 (FAIL; exemptions in <map>.gas_ok.json {"sites":[{"pos":[tx,ty],"reason":"..."}]}). Note: checks only PRE-PLACED gas buildings; an AI expansion can build its own Hatchery+Extractor, and if the player kills the Hatchery the Extractor stays - that is engine behaviour, not a placement error. If unwanted, give the free expansion no geyser or limit the AI script.

### Delivery
- Run `tools/bw/predelivery_check.py` (all checks incl. 19-25), the placement check and the trigger simulation. Say honestly what was not tested in-game.
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
- Check 20 in predelivery_check.py (tools/base_elevation.py): CV5 height (0x400 high, 0x200 mid) at each CC/Nexus/Hatchery/start vs the walkable ring median at 12-24 tiles. >1 unapproved raised = FAIL, 1 = WARN. Approve in `<map>.highground_ok.json` `{"bases":[{"hall":[tx,ty],"reason":"..."}]}`. Campaign summary: `python3 tools/base_elevation.py *.scx` (WARN if >1 in 4 missions).

### Heroes
- Hero acquisition: a hero who joins (rescued, arrives, recruited) is always part of the main storyline, through a scripted event or a required objective. Never make it an optional side quest.
- Heroes normally stay with the campaign once they join (a hero for one mission only is mission design, see level 4).

### Objectives and balance
- Objective vs. conquest balance: fulfilling the objectives must be clearly easier than destroying all enemy bases. Make the bases strong and fortified (layered static defence, defender groups, rebuilding, reinforcement waves) unless conquest is itself the objective. In the Design_Note, estimate the effort for both paths (enemy HP, defence, travel distance) and require objective effort <= about 75% of conquest effort. When in doubt, make the bases stronger rather than the objectives easier.
- Typically 1-2 main objectives plus optional quests with a tangible reward, but vary the structure (see fixed rules, quest structure). Sidequests should still be a real challenge.
- Main objectives vary: hold a position for a time, escort, rescue, recover an artifact, stealth with a small group, stop a ritual/portal, capture points, hunt a leader, evacuate/flee, survive. "Destroy the main base" only when the story calls for it; never the default.
- The difficulty curve is fair: mission 1 is easy, and difficulty rises per chapter. Offer difficulty levels that scale enemy strength.
- Pacing: a calm build-up phase, waves that grow, and the climax at the end. (Waves carry no warning text by default, see attack announcements.)
- Big waves come from real producing enemy bases. Destroying a base visibly reduces the pressure.
- Give the player enough starting supply plus headroom, unless the story deliberately says otherwise. Start each mission with a small ready-made base.
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
- Less starting supply or no starting base, when the story says so; an installation mission (maze-like, no buildings, no air).
- A one-off special mechanic in this mission (still introduced by a transmission or scene, see fixed rules).
- Intro cinematic concept: not the template "enemy base, then own base". Each intro follows the mission's story (heroes talking in the landscape, arrival by ship or march, flashback, a raid already under way, staying with the enemy, or almost no intro); justify the choice in the Design_Note under mission design.
- Side quest discovered on arrival, only with a reason (`ARRIVAL_DISCOVERY_OK`).

- **Single-resource expansions:** expansions with only mineral fields or only geysers are allowed occasionally (rarer than mixed expansions), placed with mission logic. Gas-building-needs-hall (check 25) still applies once the player builds there.

- **Temporary reveals:** when enemy positions are shown only briefly, create a temporary Map Revealer and remove it again after the scene; permanent vision only as justified mission design. Predelivery check 28: every Map Revealer created by trigger must be removed later (Remove/Kill Unit of Map Revealer) unless a Comment action in that trigger says REVEAL_PERMANENT_OK. sclib `T()` auto-appends the removal; helper `m.reveal(p,loc,hold_ms)`.
  This applies to every event that does not need to stay visible (not only enemy positions).

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

## Voice delivery notes (fixed rule, same rule for WC3)
Every voiced line carries delivery notes in VO markup v1 (`docs/voice-delivery-markup.md`): `[emotion: ...]` first,
`*stress*`, short pauses `(0.3)`/`(beat)`/`...`/` - ` (0.1-0.6 s, inside the line only; the <= 1 s gap between lines
and immediate interruptions stay), `[pace: ...]`, stage directions such as `[whisper]`. Pass it as
`Map.voice(key, text, script="[emotion: cold] Then let them *come*. (0.35) ...", speaker="Vessirak", profile="...", **CAST[...])`;
the subtitle stays `text`. edge-tts accepts no SSML, so sclib renders the script segment by segment (real silence,
per-segment rate/pitch, local stress). Write `Map.write_voice_script("<map dir>/Voice_Script_<map>.md", "<title>")`
before saving; `tools/bw/check_voice_delivery.py` (predelivery check 33) FAILs lines without notes, a short clause,
exclamation or beat without stress/pause marker, and speakers without a voice profile.
