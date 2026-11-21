"""Symmetric BW melee map builder on top of sclib (ISOM painting by symmetric shape lists)."""
import sys,math,struct,json
sys.path.insert(0,'tools/lib/bw')
import sclib
from sclib import Map,MINERAL,GEYSER,STARTLOC,BUILDSIZE,TSNAMES,TOOLS
DIRT,HDIRT,MUD,WATER,GRASS,HGRASS,ASPH,ROCKY=2,3,4,5,6,7,14,15
class MeleeMap(Map):
    def _presave(s): pass          # melee: no UMS start triggers / hyper triggers
def group_ops(sym,W,H):
    """symmetry group as point maps on continuous tile coords (vertex coords). 'rot2' = 180 deg, 'mirror4' = both axes."""
    I=lambda x,y:(x,y); R=lambda x,y:(W-x,H-y); MX=lambda x,y:(W-x,y); MY=lambda x,y:(x,H-y)
    return {'rot2':[I,R],'mirror4':[I,MX,MY,R],'mirrorx':[I,MX]}[sym]
def _warp(x,y,amp,sd):
    """smooth deterministic 2-octave noise displacement (tiles); wavelengths ~13 and ~6 tiles."""
    import random as _r; R=_r.Random(sd); P=[R.uniform(0,6.283) for _ in range(8)]; A=[R.uniform(0.7,1.3) for _ in range(4)]
    nx=amp*(0.65*A[0]*math.sin(x*0.48+y*0.21+P[0])+0.35*A[1]*math.sin(x*1.05-y*0.83+P[1]))
    ny=amp*(0.65*A[2]*math.sin(y*0.46-x*0.27+P[2])+0.35*A[3]*math.sin(y*1.1+x*0.77+P[3]))
    return nx,ny
def paint(m,sym,shapes,base):
    """shapes: list of (kind,params,terrain,prio). kind 'c'=(cx,cy,r) circle,'cap'=(x0,y0,x1,y1,r) capsule,
    'ring'=(cx,cy,R,th,gapdeg_list[(ang,half)]). Highest prio wins. Painted on every ISOM diamond -> exact symmetry."""
    ops=group_ops(sym,m.W,m.H)
    def inside(k,p,x,y):
        if k=='c': cx,cy,r=p; return (x-cx)**2+(y-cy)**2<=r*r
        if k=='cap':
            x0,y0,x1,y1,r=p; vx,vy=x1-x0,y1-y0; L=vx*vx+vy*vy or 1e-9
            t=max(0,min(1,((x-x0)*vx+(y-y0)*vy)/L)); return (x-x0-t*vx)**2+(y-y0-t*vy)**2<=r*r
        if k=='ring':
            cx,cy,R,th,gaps=p; d=math.hypot(x-cx,y-cy)
            if abs(d-R)>th: return False
            a=math.degrees(math.atan2(y-cy,x-cx))
            return not any(abs((a-g+180)%360-180)<=h for g,h in gaps)
        if k=='rect': x0,y0,x1,y1=p; return x0<=x<=x1 and y0<=y<=y1
        if k=='nrect':   # cliff_outlines: organic rect - rounded corners + low-frequency noise warp of the outline (no long straight cliff runs)
            x0,y0,x1,y1,amp,sd=p[:6]; cr=p[6] if len(p)>6 else 2.2*amp
            wx,wy=_warp(x,y,amp,sd); x,y=x+wx,y+wy
            if not (x0<=x<=x1 and y0<=y<=y1): return False
            qx=max(x0+cr-x,0,x-(x1-cr)); qy=max(y0+cr-y,0,y-(y1-cr)); return qx*qx+qy*qy<=cr*cr
        if k=='nc':
            cx,cy,r,amp,sd=p; wx,wy=_warp(x,y,amp,sd); return (x+wx-cx)**2+(y+wy-cy)**2<=r*r
    for dy in range(0,m.H+1):
        for dx in range(0,m.W//2+1):
            if (dx+dy)%2: continue
            tx,ty=dx*2,dy; best=(-1,base)
            for g in ops:
                gx,gy=g(tx,ty)
                for k,p,t,pr in shapes:
                    if pr>best[0] and inside(k,p,gx,gy): best=(pr,t)
            if best[1]!=base: m.paint.append((dx,dy,best[1],1))
def tmap(sym,W,H):
    """unit transforms for top-left tile placement (x,y,w,h) -> list of (x,y) per group element (player order)."""
    I=lambda x,y,w,h:(x,y); R=lambda x,y,w,h:(W-x-w,H-y-h); MX=lambda x,y,w,h:(W-x-w,y); MY=lambda x,y,w,h:(x,H-y-h)
    return {'rot2':[I,R],'mirror4':[I,MX,R,MY],'mirrorx':[I,MX]}[sym]
def base_units(hx,hy,side,minerals=8,geysers=1,amount=1500,gas=5000,start=True):
    """Blizzard-like arc (same geometry as sclib.base, 3-tile hall gaps). Returns [(uid,x,y,res)] top-left tiles; start -> STARTLOC."""
    arc=[(-5,-4),(-6,-3),(-7,-2),(-6,-1),(-7,0),(-6,1),(-7,2),(-6,3),(-5,4)]
    if minerals==8: arc=arc[:4]+arc[5:]
    arc=arc[:minerals]; out=[]
    amt=amount if isinstance(amount,list) else [amount]*len(arc)
    for k,(dx,dy) in enumerate(arc):
        if side=='left': p=(hx+dx,hy+dy)
        elif side=='right': p=(hx+2-dx,hy+dy)
        elif side=='up': p=(hx+dy+1,hy+dx+1)
        else: p=(hx+dy+1,hy+2-dx)
        out.append((MINERAL,p[0],p[1],amt[k]))
    if geysers:
        if side in('left','right'): out.append((GEYSER,hx,hy-5,gas))
        else: out.append((GEYSER,hx+(-7 if side=='up' else 7),hy,gas))
    if start: out.append((STARTLOC,hx,hy,0))
    return out
SZ=dict(BUILDSIZE); SZ[STARTLOC]=(4,3)
def place(m,sym,units_p1):
    """place P1 units and their symmetric images; STARTLOC owner = group index (player)."""
    T=tmap(sym,m.W,m.H)
    for gi,f in enumerate(T):
        for uid,x,y,res in units_p1:
            w,h=SZ[uid]; X,Y=f(x,y,w,h)
            if uid==STARTLOC: m.unit(STARTLOC,X*32+w*16,Y*32+h*16,gi,pixel=True)
            else: m.unit(uid,X,Y,11,res)
def setup_players(m,n):
    m.ownr=[6 if p<n else 0 for p in range(8)]+[0,0,0,7]
    m.side=[5 if p<n else 7 for p in range(8)]+[7,7,7,4]
    m.forces=[0]*8; m.forcenames=['Players','Force 2','Force 3','Force 4']; m.forceflags=[0,0,0,0]
# ramp_size: only full-size ramps. Per tileset: 8x5 / 14x9 ramp doodad ids (left/right variants). Place with ramp2.pair().
RAMP_IDS_RAMP_SIZE={'badlands':[329,330,331,338,340,361,363,370,372,393],'ashworld':[143,150,152,173]}
