# natural_cut: natural-as-cut metric. Natural region = walkable tiles within R ground tiles of the natural; cutR = smallest R that disconnects main from all enemies (maximin path).
import sys,math,glob,heapq
sys.path.insert(0,'tools/bw')
from check_ranked_bw import sections,walkgrid,dij,near_walk
import bw_natural as N
N8=[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
def maximin(W,H,wk,V,src):
    B=[[-1]*W for _ in range(H)];x,y=src;B[y][x]=V[y][x];pq=[(-B[y][x],x,y)]
    while pq:
        b,x,y=heapq.heappop(pq);b=-b
        if b<B[y][x]: continue
        for dx,dy in N8:
            X,Y=x+dx,y+dy
            if 0<=X<W and 0<=Y<H and wk[Y][X] and (dx==0 or dy==0 or (wk[y][X] and wk[Y][x])):
                v=min(b,V[Y][X])
                if v>B[Y][X]: B[Y][X]=v;heapq.heappush(pq,(-v,X,Y))
    return B
def ang(p,q,e): return abs((math.degrees(math.atan2(q[1]-p[1],q[0]-p[0])-math.atan2(e[1]-p[1],e[0]-p[0]))+180)%360-180)
def metrics(path):
    s=sections(path);W,H,wk,lvl=walkgrid(s);st,cl=N.bases(s)
    nw=lambda p: near_walk(W,H,wk,int(p[0]),int(p[1]))
    exps=[b for b in cl if min(math.hypot(b[0]-a,b[1]-c) for a,c in st)>10]
    Ds=[dij(W,H,wk,[nw(p)]) for p in st];out=[]
    for i,p in enumerate(st):
        sx,sy=nw(p);D=Ds[i]
        opp=[j for j in range(len(st)) if j!=i and Ds[j][sy][sx]<math.inf]
        if not opp: continue
        cand=sorted(exps,key=lambda b: D[nw(b)[1]][nw(b)[0]]);cand=[b for b in cand if D[nw(b)[1]][nw(b)[0]]<=50][:3] or cand[:1]
        best=None
        for nat in cand:   # the natural = the nearby base whose region cuts main from ALL enemies (smallest cut radius)
            a=nw(nat);Dn=dij(W,H,wk,[a]);dn=D[a[1]][a[0]]
            B=maximin(W,H,wk,Dn,(sx,sy))
            cutR=max(B[nw(st[j])[1]][nw(st[j])[0]] for j in opp)   # radius of natural region (ground tiles) needed so that removing it disconnects main from every enemy
            if best is None or cutR<best[0]: best=(cutR,nat,a,dn)
        cutR,nat,a,dn=best
        ne=min(opp,key=lambda j:D[nw(st[j])[1]][nw(st[j])[0]]);e=st[ne];De=Ds[ne]
        # main exits: walkable ring at ground dist 10..12 from start, components that lead (beyond) to enemy
        out.append(dict(cutR=cutR,dn=dn,ang=ang(p,nat,e),ratio=De[a[1]][a[0]]/De[sy][sx],start=p,nat=nat,enemy=e))
    return out
