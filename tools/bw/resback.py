"""Resource back-side check: every mineral field / geyser must have its back (side away from the
town-hall spot) against unwalkable terrain (cliff, high-ground edge, water, doodad) or another resource.
Hall spot = real hall within 12 tiles, else 6 tiles in front of the mineral line (normal of the line, on the geyser / open side)."""
import struct, math
import numpy as np
TS='tools/lib/bw/tileset/'
ERA=['badlands','platform','install','ashworld','jungle','desert','ice','twilight']
MIN={176,177,178}; GEY=188; HALLS={106,130,131,132,133,154}
SZ={176:(64,32),177:(64,32),178:(64,32),188:(128,64)}
def walkmap(S):
    W,H=struct.unpack('<HH',S['DIM ']); era=struct.unpack('<H',S['ERA '][:2])[0]&7
    cv5=open(TS+ERA[era]+'.cv5','rb').read()
    mt=struct.unpack(f'<{W*H}H',(S.get('MTXM') or S['TILE'])[:2*W*H])
    w=np.zeros((H,W),bool)
    for i,t in enumerate(mt):
        g=t>>4
        if g*52+4<=len(cv5): w[i//W,i%W]=not (struct.unpack_from('<H',cv5,g*52+2)[0]&4)
    return w
def clusters(res):
    cl=[]
    for r in res:
        hit=[c for c in cl if any(abs(r[0]-q[0])<=6*32 and abs(r[1]-q[1])<=6*32 for q in c)]
        new=[r]+[q for c in hit for q in c]; cl=[c for c in cl if c not in hit]+[new]
    return cl
def circle(pts):
    A=np.array([[2*x,2*y,1] for x,y in pts],float); b=np.array([x*x+y*y for x,y in pts],float)
    cx,cy,_=np.linalg.lstsq(A,b,rcond=None)[0]; return cx,cy
def check(S,units,walk=None,reach=3.25):
    """units: dicts x,y,id. returns list of (kind,tx,ty,hall_tx,hall_ty) with open backs."""
    walk=walk if walk is not None else walkmap(S); H,W=walk.shape
    res=[(u['x'],u['y'],u['id']) for u in units if u['id'] in MIN or u['id']==GEY]
    halls=[(u['x'],u['y']) for u in units if u['id'] in HALLS]
    bad=[]
    for c in clusters(res):
        mx=np.mean([p[0] for p in c]); my=np.mean([p[1] for p in c])
        near=[h for h in halls if math.hypot(h[0]-mx,h[1]-my)<12*32]
        if near: hx,hy=min(near,key=lambda h:math.hypot(h[0]-mx,h[1]-my))
        else:
            mins=[(p[0],p[1]) for p in c if p[2]!=GEY]
            if len(mins)<3: continue
            P=np.array(mins,float); cen=P.mean(0); _,_,vt=np.linalg.svd(P-cen); n=vt[1]
            gy=[(p[0],p[1]) for p in c if p[2]==GEY]
            if gy: sg=np.sign(np.dot(np.array(gy[0],float)-cen,n)) or 1
            else:
                def open_(v): return sum(1 for d in range(3,8) if (lambda q:0<=int(q[1]//32)<H and 0<=int(q[0]//32)<W and walk[int(q[1]//32),int(q[0]//32)])(cen+v*d*32))
                sg=1 if open_(n)>=open_(-n) else -1
            hx,hy=cen+n*sg*6*32
        occ=set()
        for x,y,i in c:
            w,h=SZ[i]
            for tx in range((x-w//2)//32,(x+w//2-1)//32+1):
                for ty in range((y-h//2)//32,(y+h//2-1)//32+1): occ.add((tx,ty))
        for x,y,i in c:
            dx0,dy0=x-hx,y-hy; d=math.hypot(dx0,dy0) or 1; dx0/=d; dy0/=d
            # gap of up to 3 walkable tiles behind is allowed; back = straight away from the hall, or along its dominant axis (arc corner fields sit diagonally)
            dirs=[(dx0,dy0),((1.0 if dx0>0 else -1.0),0.0) if abs(dx0)>=abs(dy0) else (0.0,(1.0 if dy0>0 else -1.0))]
            blocked=False
            for dx,dy in dirs:
                w,h=SZ[i]; edge=min(abs(w/2/dx) if dx else 1e9,abs(h/2/dy) if dy else 1e9)
                s=edge+4
                while s<=edge+reach*32 and not blocked:
                    for o in (-0.35,0,0.35):
                        px=x+dx*s-dy*o*w; py=y+dy*s+dx*o*h; tx,ty=int(px//32),int(py//32)
                        if not(0<=tx<W and 0<=ty<H) or not walk[ty,tx] or (tx,ty) in occ: blocked=True;break
                    s+=8
                if blocked: break
            if not blocked: bad.append(('geyser' if i==GEY else 'mineral',x//32,y//32,int(hx//32),int(hy//32)))
    return bad
