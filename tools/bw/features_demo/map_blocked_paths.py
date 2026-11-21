"""(2) Feature demo (neutral blocker paths). 128x128 Ashworld, mirrorx (BW ramps face south only). SIDE spawns on the west/east edge
(not corners): high main plateau mid-edge, ramp south into a low shale natural; natural exits east through one neck
(water + ridge jaws). Third tucked in the NW corner behind the main (reached around the plateau), fourth SW corner,
fifth on a north-centre plateau, sixth in a south-centre bowl. Centre: high plateau with two ramps + lakes."""
import sys,os,math,random; sys.path.insert(0,'tools/ranked/bw')
from rankedlib import *
DIRT,LAVA,HDIRT,HLAVA,SHALE,HSHALE,MAGMA,BROCK=2,3,4,5,6,7,8,9
GRASS,WATER,MUD,ROCKY=SHALE,MAGMA,LAVA,BROCK
from arcbase import arc_base
import sclib, ramp2, symdood
E=os.environ.get
W,H=128,128; SYM='mirrorx'
m=MeleeMap(W,H,3,DIRT,seed=743)
rnd=random.Random(int(E('SEED','7431')))
A=float(E('AMP','2.2')); C=float(E('CAMP','1.3'))
S=[]
def edge_blob(px,py):
    k=rnd.random(); r=rnd.uniform(2.5,5.5)
    if k<0.4: S.append(('c',(px,py,r),WATER,3))
    elif k<0.7: S.append(('nc',(px,py,r*0.8,C,41+int(py)),HDIRT,4))
    else: S.append(('c',(px,py,r),MUD,1)); S.append(('c',(px+rnd.uniform(-2,2),py+rnd.uniform(-2,2),r*0.45),ROCKY,2))
for y in (26,94,124): edge_blob(rnd.uniform(-4,0),y+rnd.uniform(-2,2))
for xx in range(22,58,8): edge_blob(xx+rnd.uniform(-2,2),H+rnd.uniform(0,4))
PY=int(E('PY','62'))
BASES=[(7,44,180,9,110,True,HDIRT,dict(gside=1)),     # main: high plateau, mid west edge
 (6,72,180,8,100,False,DIRT,dict(gside=-1)),          # natural: low pocket below the main ramp
 (7,5,180,7,100,False,DIRT,{}),                         # third: NW corner behind the main
 (7,112,180,7,100,False,DIRT,{}),                       # fourth: SW corner
 (45,6,270,7,100,False,HDIRT,{}),                       # fifth: north-centre plateau (ramp south)
 (40,96,270,6,100,False,HDIRT,dict(amount=1000,gside=-1))]  # sixth: south bowl, half minerals
NJ=int(E('NJ','90'))
S+=[
 # main plateau (west edge, y 28..PY)
 ('nrect',(-6,30,28,PY,A,11,1.0),HDIRT,6),
 # natural: south jaw ridge (no ramp) + water, exit neck to the east between main spur and lake
 ('nc',(2,NJ,4,C,43),HDIRT,7),('nc',(9,NJ+.5,4,C,44),HDIRT,7),('nc',(16,NJ,4,C,45),HDIRT,7),('nc',(23,NJ+1,3.6,C,46),HDIRT,7),
 ('nc',(30,NJ-1,3.2,C,47),HDIRT,7),
 ('nc',(28,59,3.6,C,59),HDIRT,7),('nc',(31,64,3.2,C,60),HDIRT,7),('nc',(32,69,3.2,C,61),HDIRT,7),('nc',(31,74,3,C,62),HDIRT,7) if E('R74','1') else ('c',(-50,-50,1),WATER,0),
 
 # north-centre plateau for the fifth
 ('nrect',(40,-6,56,14,A,13),HDIRT,6),('nc',(56,7,2.2,C,49),HDIRT,6),
 # central plateau (on the axis) with ramps south, lakes either side
 ('nrect',(54,50,74,66,A,14),HDIRT,6),('c',(38,34,3),WATER,7),
 ('c',(38,22,2.5),ROCKY,2),('nc',(64,110,3,C,52),HDIRT,7),
 ('nrect',(27,88,54,108,A,16),HDIRT,6),('c',(38,87.5,4),WATER,7),('nrect',(-6,12,30,32,1.5,17),WATER,5),('c',(64,124,6),WATER,6),('nc',(20,124,4,C,54),HDIRT,6),
 ('c',(50,80,3),MUD,1),('c',(50,28,3),ROCKY,2),('c',(30,112,3),MUD,1),('c',(56,24,2.5),GRASS,1),
]
# blocked_paths blocked_path: optional low-ground backdoor natural -> SW corner, closed by a mineral wall or a neutral building stack
BP=E('BP','minerals')  # 'minerals' | 'temple' | ''
BPX0,BPY0,BPX1,BPY1=int(E("BX0","1")),80,int(E("BX1","14")),99
if BP: S.append(('nrect',(BPX0,BPY0,BPX1,BPY1,0.0,77,1.0),DIRT,20))
for hx,hy,deg,n,sp,stt,g,kw in BASES:
    if g==HDIRT: a=math.radians(deg); S.append(('c',(hx+2+4*math.cos(a),hy+1.5+4*math.sin(a),6.5),g,10))
    else: S.append(('c',(hx+2,hy+1.5,float(E('CLR','9.3'))),g,10))
paint(m,SYM,S,DIRT)
U=[u for hx,hy,deg,n,sp,stt,g,kw in BASES for u in arc_base(hx,hy,deg,n=n,span=sp,start=stt,**kw)]
place(m,SYM,[u for u in U if not (u[0]==STARTLOC and u[1]!=BASES[0][0])]); setup_players(m,2)
BLK=[]; SZ[36]=SZ[97]=(1,1)
if BP=='minerals': BLK=[(MINERAL,x,y,int(E('BPV','0'))) for y in (89,90) for x in range(int(E("WX0","4")),int(E("WX1","12")),2)]
elif BP=='assim':   # battlefield_cover: two neutral geysers + Assimilator/Extractor/Refinery (owner 11) with a gap; optional eggs plug the gap
    gx0=int(E('WX0','4')); gap=int(E('GAP','1')); bid={'assim':157,'extr':149,'ref':110}[E('GB','assim')]
    gy=int(E('GY','92')); BLK=[(GEYSER,gx0,gy,int(E('GV','0'))),(bid,gx0,gy,0),(GEYSER,gx0+4+gap,gy,int(E('GV','0'))),(bid,gx0+4+gap,gy,0)]
    if E('EGGS'): BLK+=[(int(E('EGG','36')),gx0+4+i,y,0) for i in range(gap) for y in (gy,gy+1)]
elif BP=='temple': BLK=[(174,int(E("WX0","4")),88,0)]*int(E('BPN','3'))   # stacked Protoss Temples (owner 11), Medusa-style
for uid,x,y,res in BLK:
    for gi,f in enumerate(tmap(SYM,W,H)):
        w,h=SZ[uid]; X,Y=f(x,y,w,h); m.unit(uid,X,Y,11,res)
m.build_terrain(); m.tech=None
RB=E('RB',f'2,{PY-2},13,{PY+6};40,12,54,20;50,64,62,72;30,106,48,114').split(';')
RAMPS=[ramp2.pair(m,RAMP_IDS_RAMP_SIZE['ashworld'],tuple(map(int,b.split(','))),W) for b in RB]
print('ramps',RAMPS)
if any(r is None for r in RAMPS) and not E('NORAMPOK'): print('RAMPFAIL'); sys.exit(3)
nd=int(E('ND','1100'))
FB=[(BPX0-2,BPY0-2,BPX1+2,BPY1+2),(W-BPX1-3,BPY0-2,W-BPX0+2,BPY1+2)] if BP else []; DST={}
# zone_doodads: main plateau + natural pocket are build zones -> no random scatter there at all (cover only via COVER pairs below)
for x0,y0,x1,y1 in ((0,28,30,62),(0,60,30,88)): FB+=[(x0,y0,x1,y1),(W-x1-1,y0,W-x0+1,y1)]
for hx,hy,deg,n,sp,stt,g,kw in BASES:
    pts=[(u[1],u[2]) for u in arc_base(hx,hy,deg,n=n,span=sp,start=stt,**kw)]+[(hx-2,hy-2),(hx+6,hy+5)]
    x0=min(p[0] for p in pts)-3;y0=min(p[1] for p in pts)-3;x1=max(p[0] for p in pts)+5;y1=max(p[1] for p in pts)+4
    FB+=[(x0,y0,x1,y1),(W-x1-1,y0,W-x0+1,y1)]
for t,hi in ((DIRT,False),(HDIRT,True),(GRASS,False),(ROCKY,False)):
    print('doodads',t,symdood.place_sym(m,nd//4,[t],forbid=FB,high=hi,seed=rnd.randrange(9999),stats=DST))
# battlefield_cover: battlefield cover pass - blocking doodads only, outside all base/forbid boxes, until density >= 4.8% (refs 4.8-44.6%)
for t,hi in ((DIRT,False),(HDIRT,True)):
    print('cover',t,symdood.place_sym(m,int(E('NB','400')),[t],forbid=FB,high=hi,seed=rnd.randrange(9999),stats=DST,only_block=True))
print('symmetric_blockers pairs',DST)
out=E('OUT','output/blocked_paths_test.scx')
m.save(out,'\x03(2)\x04 Feature Demo 2P','1v1 melee. 128x128 Ashworld. Side spawns on high ledges, low shale naturals, central plateau.')
print(sclib.validate(out))
sclib.render(out,out.replace('.scx','_preview.png'),{},'(2) Feature Demo 2P 128x128')
if BP:   # blocked_paths generator assertion: the blocker must actually seal the backdoor
    sys.path.insert(0,'tools/bw'); import bw_blocked_paths
    F,I=bw_blocked_paths.check(out); print(I)
    if (' 0 seal' in I[0]) and not (BP=='assim' and not E('EGGS')): print('BLOCKFAIL: blocker seals nothing'); sys.exit(4)
