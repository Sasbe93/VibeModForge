#!/usr/bin/env python3
"""SC:BW ranked map diversity dice (diversity_dice).
Usage: dice.py [--seed N] [--players 2|3|4] [--accept] [--history FILE] [--markdown]
--accept writes the roll to the history so later rolls avoid it."""
import argparse, json, random, os, sys
HIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dice_history.json")
# Each option: (id, note, tags) ; tags: "req:x" needs tag x present, "no:x" forbids tag x, plain = provides tag
T = {
"tileset": [
 ("badlands","dirt/mud/grass cliffs; classic readable",["land"]),
 ("space","platform over space; void edges = unbuildable chasms",["space","noWaterTiles"]),
 ("installation","indoor metal; no water, tight corridors look natural",["indoor","noWaterTiles"]),
 ("ashworld","lava/magma/ash; lava as unwalkable feature",["lavaok","noWaterTiles"]),
 ("jungle","jungle/ruins/temples; water ok",["land","templeok"]),
 ("desert","sand/dunes/tar/compound; tar as unwalkable",["land","templeok"]),
 ("arctic","snow/ice/outpost; water ok",["land"]),
 ("twilight","basilica/crushed rock/flagstones",["land","templeok"]),
],
"layout": [
 ("cross_positions","spawns cross-only (4p) / diagonal (2p); long rush",["need4or2"]),
 ("ring","bases on a ring road around impassable core",["core"]),
 ("corridors","2-3 parallel lanes separated by cliffs",[]),
 ("split_highground","map split by a long high-ground ridge with ramps",[]),
 ("river","walkable shallow/low river with bridges as chokes",["no:noWaterTiles"]),
 ("plateau_center","large raised centre controlling paths",["centerHG"]),
 ("backdoor","main has a second, narrow (or mineral-blocked) entry",["backdoor"]),
 ("mineral_walls","mineral lines (1-8 minerals) wall off shortcuts",[]),
 ("temple_center","doodad temple centrepiece on high ground",["req:templeok","centerHG"]),
 ("island_ish","main by land, some expos only reachable by air/drop",["islands"]),
 ("spiral","paths wind rotationally (3p/4p rotation)",["no:need2only"]),
 ("diagonal_valley","one wide valley between two highland halves",[]),
 ("open_steppe","few cliffs, wide open midfield (macro)",["open"]),
 ("maze_lowground","many small cliffs/doodads forming twisting paths",[]),
 ("pocket_naturals","natural inside main behind single ramp",[]),
 ("triangle","3 spawns at triangle corners, centre triangle",["need3"]),
],
"center": [
 ("hg_plateau","raised plateau with 2-4 ramps",["centerHG","no:core"]),
 ("ruins","destroyed-building doodads, unwalkable patches",[]),
 ("choke_maze","small chokes forcing pathing decisions",[]),
 ("open_field","flat open ground, flank-friendly",["no:core"]),
 ("neutral_buildings","neutral structures to destroy (blocks, vision)",[]),
 ("lava_pool","unwalkable lava/tar pit",["req:lavaok"]),
 ("doodad_garden","dense unwalkable decor (trees/crystals/pipes)",[]),
 ("no_center","no special centre; action on sides",[]),
 ("center_expo","contested rich base in middle",["no:core"]),
 ("void_chasm","space hole / deep chasm (air-only)",["req:space"]),
 ("crossroads_bridge","bridge/ramp cross over low ground",[]),
 ("watchtower_hills","small raised hills with vision",[]),
 ("mineral_island","middle mineral-only block (minable wall)",[]),
 ("temple","temple doodad cluster",["req:templeok"]),
],
"main_natural": [
 ("classic_ramp","main ramp down to natural, natural one wide choke",[]),
 ("pocket","natural inside main",[]),
 ("cliffed_natural","natural below main cliff (drop/siege angle)",[]),
 ("forward_natural","natural further forward, open",[]),
 ("backdoor_natural","natural with mineral-blocked backdoor",["backdoor"]),
 ("double_choke","natural has two narrow entries",[]),
 ("highground_natural","natural on same high ground as main",[]),
 ("side_natural","natural to the side along edge",[]),
 ("gasless_natural","natural without gas (min only)",[]),
 ("double_gas_main","main with 2 geysers",[]),
],
"expansions": [
 ("linear","bases chained toward centre",[]),
 ("edge_ring","expos along map edges",[]),
 ("cluster_center","expos clustered near centre",["no:core"]),
 ("island_expo","1 island expo per player",["islands"]),
 ("rich_contested","one shared richer expo between neighbours",[]),
 ("gas_only","one gas-only/min-low base per side",[]),
 ("min_only","mineral-only thirds",[]),
 ("hidden_backyard","expo behind main",[]),
 ("staircase","expos on rising terraces",[]),
 ("sparse","few bases, aggressive",[]),
 ("plenty","many small bases (6+ per player)",[]),
],
"special": [
 ("destructible_path","neutral blocks/rocks open a shortcut",[]),
 ("mineral_backdoor","1-value minerals block a backdoor",["backdoor"]),
 ("island_expo","air-only base",["islands"]),
 ("gas_only_base","geyser-only spot",[]),
 ("shortcut_ramps","narrow ramps give fast route",[]),
 ("narrow_bridges","bridge chokes",[]),
 ("assimilator_blocks","neutral geysers / extractors block",[]),
 ("dark_corners","unbuildable high doodads as vision blockers",[]),
 ("creep_none","nothing special (clean)",[]),
 ("air_lanes","gaps only air can cross",[]),
 ("blocked_highground","high ground only via destructible",[]),
 ("double_ramps","mains with two ramps",[]),
],
"edge": [
 ("cliff_rim","high cliffs border",[]),
 ("water_rim","water edge",["no:noWaterTiles"]),
 ("void_rim","space void edge",["req:space"]),
 ("lava_rim","lava edge",["req:lavaok"]),
 ("wall_rim","indoor walls",["req:indoor"]),
 ("doodad_rim","trees/crystals",[]),
 ("plain_edge","plain map border",[]),
 ("broken_edge","irregular inlets",[]),
],
"decor": [
 ("overgrown","plants everywhere",[]),
 ("industrial","pipes, tanks, machinery",[]),
 ("ancient","statues, temple bits",[]),
 ("battlefield","wrecks, craters",[]),
 ("crystals","crystal clusters",[]),
 ("frozen","ice shards, snowdrifts",[]),
 ("volcanic","vents, magma rocks",[]),
 ("derelict","broken platforms, debris",[]),
 ("sparse_clean","minimal decor",[]),
 ("settlement","houses/outposts",[]),
],
"palette": [
 ("bright","bright ground",[]),("dark","dark tiles",[]),("warm","reds/browns",[]),
 ("cold","blues/whites",[]),("mixed","contrasting zones",[]),("monotone","one dominant tile",[]),
 ("checker","alternating patches",[]),("gradient","shift across map",[]),
],
}
TABLES = list(T)

def tags_of(choice):
    return [t for t in choice[2] if not t.startswith(("req:","no:"))]

def ok(combo, players):
    tags=set(sum((tags_of(c) for c in combo.values()),[]))
    if players==3: tags.add("p3")
    for c in combo.values():
        for t in c[2]:
            if t.startswith("req:") and t[4:] not in tags: return False
            if t.startswith("no:") and t[3:] in tags: return False
    if "need3" in tags and players!=3: return False
    if "need4or2" in tags and players==3: return False
    if "islands" in tags and combo["tileset"][0]=="installation": return False
    return True

def roll(seed, players, hist, recent=5):
    rng=random.Random(seed)
    last=hist[-recent:]
    for _ in range(10000):
        c={k:rng.choice(T[k]) for k in TABLES}
        if not ok(c,players): continue
        if any(h["layout"]==c["layout"][0] or h["center"]==c["center"][0] for h in last): continue
        if any(h["tileset"]==c["tileset"][0] for h in hist[-2:]): continue
        return c
    sys.exit("no valid combo")

def main():
    a=argparse.ArgumentParser(); a.add_argument("--seed",type=int); a.add_argument("--players",type=int,default=2,choices=[2,3,4])
    a.add_argument("--accept",action="store_true"); a.add_argument("--history",default=HIST); a.add_argument("--markdown",action="store_true")
    a.add_argument("--name",default="")
    o=a.parse_args()
    if o.markdown:
        for k in TABLES:
            print(f"**{k}** ({len(T[k])}): "+"; ".join(f"`{i}` {n}"+(f" [{','.join(t for t in g if ':' in t)}]" if any(':' in t for t in g) else "") for i,n,g in T[k])+"\n")
        return
    hist=json.load(open(o.history)) if os.path.exists(o.history) else []
    seed=o.seed if o.seed is not None else random.randrange(10**9)
    c=roll(seed,o.players,hist)
    rec={"seed":seed,"players":o.players,"name":o.name,**{k:c[k][0] for k in TABLES}}
    for k in TABLES: print(f"{k:13} {c[k][0]:20} - {c[k][1]}")
    print("seed",seed)
    if o.accept:
        hist.append(rec); json.dump(hist,open(o.history,"w"),indent=1); print("saved to history")
if __name__=="__main__": main()
