"""(4) Example Crossing 4P - 128x128 Badlands, 4-fold mirror symmetry (Octagon/Fighting-Spirit-style 4p)."""
import sys; sys.path.insert(0,'tools/ranked/bw')
from rankedlib import *
W,H=128,128; SYM='mirror4'
GAP=int(sys.argv[1]) if len(sys.argv)>1 else 45
m=MeleeMap(W,H,0,DIRT,seed=651)
S=[
 ('ring',(14,13,18,2.6,[(GAP,11)]),HDIRT,5),          # main enclosure, choke toward the natural
 ('c',(6,40,5),WATER,6),                                # pond behind the natural minerals (west edge)
 ('cap',(34,20,38,34,3),HDIRT,5),                       # mesa arm between main and inner area
 ('c',(64,64,9),WATER,7),                               # central lake -> ring road around it
 ('c',(44,44,4),HDIRT,5),                               # pillars on the diagonals
 ('cap',(64,0,64,7,3),HDIRT,4),('cap',(0,64,7,64,3),HDIRT,4),   # edge separators between neighbours
 ('c',(28,30,6),GRASS,1),('c',(50,20,5),MUD,1),('c',(20,52,5),ROCKY,1),
]
paint(m,SYM,S,DIRT)
U=[]
U+=base_units(9,9,'left',minerals=9,amount=1500)                     # main 9M+1G
U+=base_units(18,40,'left',minerals=8,amount=1500,start=False)          # natural 8M+1G
U+=base_units(48,8,'up',minerals=7,amount=1250,start=False)             # edge third 7M+1G
place(m,SYM,U); setup_players(m,4)
m.build_terrain(); m.tech=None
out=sys.argv[2] if len(sys.argv)>2 else 'output/ranked/BW_4p_Example_Crossing_4P.scx'
m.save(out,'\x03(4)\x04 Example Crossing 4P','2-4 player melee. 128x128 Badlands. 4-fold mirror symmetry. Main 9M+1G, natural 8M+1G, third 7M+1G.')
print(sclib.validate(out))
sclib.render(out,out.replace('.scx','_preview.png'),{},'(4) Example Crossing 4P 128x128')
