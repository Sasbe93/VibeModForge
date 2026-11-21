"""main_space: the main must have enough space. Main region = ground-Voronoi cell of the start location
(seeds: all start locations + all expected expansion halls), connected to the start. Area = walkable tiles, buildable = walkable and not cv5 0x80."""
import sys,math,heapq
sys.path.insert(0,'tools/bw')
from check_ranked_bw import sections,walkgrid,near_walk,units,SLOC
import bw_natural_choke as T
AREA_MIN=530;AREA_P25=655;BUILD_MIN=520;BUILD_P25=640   # main_space calibrated on ladder refs (per start; Plasma island gimmick excluded)
def mains(path):
    s=sections(path);W,H,wk,lvl=walkgrid(s);G,F=T.tileflags(s)
    st=[];[st.append((u['x']/32,u['y']/32)) for u in units(s) if u['id']==SLOC and all(math.hypot(u['x']/32-a,u['y']/32-b)>4 for a,b in st)]
    seeds=[near_walk(W,H,wk,int(x),int(y)) for x,y in st]
    for (hx,hy),_ in T.hall_spots(s,W,H,wk):
        if min(math.hypot(hx-a,hy-b) for a,b in st)>10: seeds.append(near_walk(W,H,wk,int(hx),int(hy)))
    O=[[-1]*W for _ in range(H)];D=[[math.inf]*W for _ in range(H)];pq=[]
    for i,p in enumerate(seeds):
        if p: D[p[1]][p[0]]=0;O[p[1]][p[0]]=i;pq.append((0,i,p[0],p[1]))
    heapq.heapify(pq)
    while pq:
        d,i,x,y=heapq.heappop(pq)
        if d>D[y][x] or O[y][x]!=i: continue
        for dx,dy,c in ((1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,1.414),(1,-1,1.414),(-1,1,1.414),(-1,-1,1.414)):
            X,Y=x+dx,y+dy
            if 0<=X<W and 0<=Y<H and wk[Y][X] and (dx==0 or dy==0 or (wk[y][X] and wk[Y][x])) and d+c<D[Y][X]:
                D[Y][X]=d+c;O[Y][X]=i;heapq.heappush(pq,(d+c,i,X,Y))
    out=[]
    for i in range(len(st)):
        cell=[(x,y) for y in range(H) for x in range(W) if O[y][x]==i]
        b=sum(1 for x,y in cell if not F[y][x]&0x80)
        out.append(dict(start=st[i],area=len(cell),build=b,cell=cell))
    return out
def check(path):
    F=[];I=[]
    for k,m in enumerate(mains(path)):
        I.append(f"main_space main {k+1}: area {m['area']} walkable, {m['build']} buildable (FAIL < {AREA_MIN}/{BUILD_MIN}, WARN < {AREA_P25}/{BUILD_P25})")
        if m['area']<AREA_MIN or m['build']<BUILD_MIN: F.append(f"main_space: main {k+1} too small ({m['area']} walkable / {m['build']} buildable < ref min {AREA_MIN}/{BUILD_MIN})")
        elif m['area']<AREA_P25 or m['build']<BUILD_P25: I.append(f"WARN main_space: main {k+1} small ({m['area']}/{m['build']} < ref p25 {AREA_P25}/{BUILD_P25})")
    return F,I
