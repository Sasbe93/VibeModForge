"""Curved, staggered mineral arcs (curved_mineral_arcs >=60 deg) around a 4x3 hall, geyser at the arc end (geyser_back_wall back to wall)."""
import math
from rankedlib import MINERAL,GEYSER,STARTLOC
def arc_base(hx,hy,deg,n=8,span=100,amount=1500,gas=5000,start=True,gside=1,res=None):
    """hx,hy = hall top-left tile; deg = direction from hall to minerals (0=east, 90=south); geyser at the arc end (gside +1/-1)."""
    cx,cy=hx+2,hy+1.5; out=[]; occ=set()
    def free(x,y,w,h): return not any((x+a,y+b) in occ for a in range(-0,w) for b in range(h))
    def put(uid,x,y,w,h,r):
        for a in range(w):
            for b in range(h): occ.add((x+a,y+b))
        out.append((uid,x,y,r))
    for b in range(3):
        for a in range(4): occ.add((hx+a,hy+b))
    angs=[deg-span/2+span*k/(n-1) for k in range(n)]
    for k,a in enumerate(angs):
        t=math.radians(a); st=0.0 if k%2==0 else 1.0     # stagger: every second field one tile further out
        for extra in (0,0.5,1,1.5,2,2.5):
            rx,ry=6.4+st+extra,5.2+st+extra
            mx,my=cx+rx*math.cos(t),cy+ry*math.sin(t)
            x,y=round(mx-1),round(my-0.5)
            # hall gap >=3 tiles (Blizzard 3-tile rule)
            if x+2>hx-3 and x<hx+4+3 and y+1>hy-3 and y<hy+3+3: continue
            if free(x-0,y,2,1) and all((x+aa,y) not in occ for aa in (-1,2)) or free(x,y,2,1) and extra>=1.5:
                if free(x,y,2,1): put(MINERAL,x,y,2,1,amount if res is None else res[k]); break
    if gas:
        t=math.radians(deg+gside*(span/2+38))
        for extra in (0,0.5,1,1.5,2,3):
            gx,gy=round(cx+(7.2+extra)*math.cos(t)-2),round(cy+(5.6+extra)*math.sin(t)-1)
            if gx+4>hx-3 and gx<hx+4+3 and gy+2>hy-3 and gy<hy+3+3: continue
            if free(gx-1,gy-1,6,4): put(GEYSER,gx,gy,4,2,gas); break
    if start: out.append((STARTLOC,hx,hy,0))
    return out
