"""zone_doodads: main/natural plateaus (and other expansions) must stay buildable; doodads there only as purposeful
cover at the zone rim (chokes, ramps, cliff edges). Random scatter belongs to open battlefield ground.
Zones: ground Voronoi of starts + expected halls, limited to ground distance <= R from the seed; rest of walkable = battlefield.
Doodad tile = cv5 group >= 1024 (incl. unwalkable doodad tiles touching the zone). 'rim' = within RIM tiles of a
non-doodad unwalkable tile (cliff/water), map border or zone boundary; otherwise 'interior'."""
import sys,math,heapq,collections
sys.path.insert(0,'tools/bw')
from check_ranked_bw import sections,walkgrid,near_walk,units,SLOC
import bw_natural_choke as T
R=14; RIM=3
# calibrated zone_doodads on 22 ref maps (blocking/unbuildable doodad tiles per zone tile, max over zones):
#  main dens 0-2.8% (outliers OdysseyRE 30.5, Deja Vu 20.7, Plasma 18.2), interior 0-3 tiles
#  natural dens 0.9-25 % (Deja Vu 26.6; ramps/cliff doodads at the rim), interior 0-17 (Deja Vu 21, Odyssey 38)
#  other expansions dens 3.8-34.8 % (Polypoid 50.8), interior 0-41 (Polypoid 110)
LIM=dict(main=(3.0,3),nat=(25.0,17),exp=(35.0,41))   # (max density %, max interior doodad tiles)
def zones(path):
    s=sections(path);W,H,wk,lvl=walkgrid(s);G,F=T.tileflags(s)
    st=[];[st.append((u['x']/32,u['y']/32)) for u in units(s) if u['id']==SLOC and all(math.hypot(u['x']/32-a,u['y']/32-b)>4 for a,b in st)]
    seeds=[(near_walk(W,H,wk,int(x),int(y)),'main') for x,y in st]
    for (hx,hy),_ in T.hall_spots(s,W,H,wk):
        if min(math.hypot(hx-a,hy-b) for a,b in st)>10: seeds.append((near_walk(W,H,wk,int(hx),int(hy)),'exp'))
    O=[[-1]*W for _ in range(H)];D=[[math.inf]*W for _ in range(H)];pq=[]
    for i,(p,_) in enumerate(seeds):
        if p: D[p[1]][p[0]]=0;O[p[1]][p[0]]=i;pq.append((0,i,p[0],p[1]))
    heapq.heapify(pq)
    while pq:
        d,i,x,y=heapq.heappop(pq)
        if d>D[y][x] or O[y][x]!=i: continue
        for dx,dy,c in ((1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,1.414),(1,-1,1.414),(-1,1,1.414),(-1,-1,1.414)):
            X,Y=x+dx,y+dy
            if 0<=X<W and 0<=Y<H and wk[Y][X] and (dx==0 or dy==0 or (wk[y][X] and wk[Y][x])) and d+c<D[Y][X] and d+c<=R:
                D[Y][X]=d+c;O[Y][X]=i;heapq.heappush(pq,(d+c,i,X,Y))
    kind=[k for _,k in seeds]
    for a,b in st:
        ex=[(math.hypot(seeds[j][0][0]-a,seeds[j][0][1]-b),j) for j in range(len(seeds)) if kind[j]=='exp' and seeds[j][0]]
        if ex: kind[min(ex)[1]]='nat'
    Z=[[O[y][x] if wk[y][x] else -1 for x in range(W)] for y in range(H)]
    dood=lambda x,y:G[y][x]>=1024 and (not wk[y][x] or F[y][x]&0x80 or F[y][x]&0x4)   # blocking/unbuildable doodad tiles only
    for y in range(H):
        for x in range(W):
            if not wk[y][x] and dood(x,y):
                for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    X,Y=x+dx,y+dy
                    if 0<=X<W and 0<=Y<H and O[Y][X]>=0: Z[y][x]=O[Y][X];break
    rd=[[math.inf]*W for _ in range(H)];q=collections.deque()
    for y in range(H):
        for x in range(W):
            if (not wk[y][x] and not dood(x,y)) or Z[y][x]<0 or x in(0,W-1) or y in(0,H-1) or \
               any(0<=x+dx<W and 0<=y+dy<H and Z[y+dy][x+dx]!=Z[y][x] and (wk[y+dy][x+dx] or dood(x+dx,y+dy)) for dx,dy in((1,0),(-1,0),(0,1),(0,-1))):
                rd[y][x]=0;q.append((x,y))
    while q:
        x,y=q.popleft()
        for dx,dy in((1,0),(-1,0),(0,1),(0,-1)):
            X,Y=x+dx,y+dy
            if 0<=X<W and 0<=Y<H and rd[Y][X]>rd[y][x]+1: rd[Y][X]=rd[y][x]+1;q.append((X,Y))
    res=collections.defaultdict(lambda: dict(tiles=0,dood=0,inter=0,unb=0))
    bf=dict(tiles=0,dood=0)
    for y in range(H):
        for x in range(W):
            z=Z[y][x]
            if z<0:
                if wk[y][x] or dood(x,y): bf['tiles']+=1; bf['dood']+=bool(dood(x,y))
                continue
            r=res[(kind[z],z)];r['tiles']+=1
            if dood(x,y):
                r['dood']+=1
                if rd[y][x]>RIM: r['inter']+=1
            if wk[y][x] and F[y][x]&0x80: r['unb']+=1
    out={}
    for (k,z),r in res.items(): out.setdefault(k,[]).append(r)
    return out,bf
def summary(path):
    out,bf=zones(path);S={}
    for k in('main','nat','exp'):
        L=out.get(k,[])
        if L: S[k]=dict(dens=max(100*r['dood']/max(1,r['tiles']) for r in L),mean=sum(100*r['dood']/max(1,r['tiles']) for r in L)/len(L),inter=max(r['inter'] for r in L),unb=max(100*r['unb']/max(1,r['tiles']) for r in L))
    S['bf']=100*bf['dood']/max(1,bf['tiles'])
    return S
def check(path):
    S=summary(path);F=[];I=[]
    I.append('zone_doodads base-zone doodads (max over zones): '+'; '.join(f"{k} dens {S[k]['dens']:.1f}% interior {S[k]['inter']} unbuildable {S[k]['unb']:.1f}%" for k in('main','nat','exp') if k in S)+f"; battlefield dens {S['bf']:.1f}%")
    if S['bf']<4.8: I.append(f"WARN zone_doodads: battlefield doodad density {S['bf']:.1f}% below ref range (4.8-44.6%)")
    for k in('main','nat','exp'):
        if k not in S or LIM[k][0] is None: continue
        if S[k]['dens']>LIM[k][0]: F.append(f"zone_doodads: {k} zone doodad density {S[k]['dens']:.1f}% > ref max {LIM[k][0]}% - keep base plateaus buildable")
        if S[k]['inter']>LIM[k][1]: F.append(f"zone_doodads: {k} zone has {S[k]['inter']} doodad tiles in its interior (> {LIM[k][1]}); base doodads only as cover at chokes/ramps/edges")
    return F,I
if __name__=='__main__':
    for p in sys.argv[1:]:
        try: S=summary(p)
        except Exception as e: print(p.split('/')[-1],'ERR',e); continue
        print(p.split('/')[-1],' '.join(f"{k}:{v['dens']:.1f}/{v['mean']:.1f}%,int{v['inter']},unb{v['unb']:.0f}%" for k,v in S.items() if k!='bf'),f"bf:{S['bf']:.1f}%")
