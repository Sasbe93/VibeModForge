"""(2) Example Ridge 2P - 128x96 Badlands, 180 deg rotational symmetry (Colorless-Fate-size 1v1)."""
import sys; sys.path.insert(0,'tools/ranked/bw')
from rankedlib import *
W,H=128,96; SYM='rot2'
m=MeleeMap(W,H,0,DIRT,seed=650)
C=(14,12)
S=[
 # main enclosure: mesa ring with one choke toward the natural (SE, ~40 deg)
 ('ring',(C[0],C[1],19,2.6,[(42,11)]),HDIRT,5),
 # natural: lake behind its minerals and a mesa arm that funnels the natural entrance
 ('c',(22,46,6),WATER,6),('cap',(8,38,22,46,4),WATER,6),
 ('cap',(40,22,44,36,3),HDIRT,5),
 # third (west) shielded by a rock ridge, opening toward the centre
 ('cap',(22,62,30,74,3),HDIRT,5),
 # centre: lake + flanking mesas -> two main routes
 ('c',(64,48,7),WATER,7),('c',(52,36,4),HDIRT,5),('c',(46,60,3.5),HDIRT,5),
 ('cap',(60,0,60,8,3),HDIRT,4),
 # grass/mud patches for looks (walkable)
 ('c',(30,30,7),GRASS,1),('c',(14,74,7),GRASS,1),('c',(70,18,6),MUD,1),('c',(38,52,5),ROCKY,1),
]
paint(m,SYM,S,DIRT)
U=[]
U+=base_units(9,9,'left',minerals=9,amount=1500)                          # main 9M+1G
U+=base_units(27,33,'down',minerals=8,amount=1500,start=False)               # natural 8M+1G
U+=base_units(9,78,'left',minerals=7,amount=1500,start=False)                # third 7M+1G
U+=base_units(78,6,'up',minerals=6,geysers=0,amount=1000,start=False)        # mineral-only 6M

place(m,SYM,U); setup_players(m,2)
m.build_terrain()
m.tech=None
out='output/ranked/BW_2p_Example_Ridge_2P.scx'
m.save(out,'\x03(2)\x04 Example Ridge 2P','1v1 melee. 128x96 Badlands. 180-degree rotational symmetry. Main 9M+1G, natural 8M+1G.')
print(sclib.validate(out))
sclib.render(out,out.replace('.scx','_preview.png'),{},'(2) Example Ridge 2P 128x96')
