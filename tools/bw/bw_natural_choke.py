"""natural_choke: (a) the enemy's way into the natural must be a narrow choke; (b) no unbuildable/path-blocking doodads inside expansions or in the hall<->resource mining corridor."""
import sys,math,struct
sys.path.insert(0,'tools/bw')
from check_ranked_bw import sections,walkgrid,units,dij,near_walk,MIN,GAS,SLOC,TD,TS
import bw_natural as N, bw_natcut as NC
CHOKE_MAX=None   # set after calibration
def hall_spots(s,W,H,wk,UB=None):
    U=units(s); res=[u for u in U if u['id'] in MIN|GAS]; cl=[]
    for u in res:
        p=(u['x']/32,u['y']/32)
        for c in cl:
            if any(abs(p[0]-q['x']/32)+abs(p[1]-q['y']/32)<=6 for q in c): c.append(u);break
        else: cl.append([u])
    SL=[(u['x']/32,u['y']/32) for u in U if u['id']==SLOC]; out=[]
    for c in cl:
        mm=[(u['x']/32,u['y']/32) for u in c if u['id'] in MIN and u['res']>=100]
        if len(mm)<4: continue
        mx=sum(a for a,_ in mm)/len(mm); my=sum(b for _,b in mm)/len(mm)
        hs=[h for h in SL if math.hypot(h[0]-mx,h[1]-my)<10]
        if hs: hx,hy=hs[0]
        else:
            best=None
            for yy in range(int(my)-10,int(my)+11):
                for xx in range(int(mx)-10,int(mx)+11):
                    if not all(0<=xx+a<W and 0<=yy+b<H and wk[yy+b][xx+a] and not (UB and UB[yy+b][xx+a]) for a in (-2,-1,0,1) for b in (-1,0,1)): continue
                    ds=[math.hypot(a-xx,b-yy) for a,b in mm]
                    if min(ds)<3: continue
                    sc=sum((d-6.3)**2 for d in ds)
                    if best is None or sc<best[0]: best=(sc,xx,yy)
            if not best: continue
            _,hx,hy=best
        out.append(((hx,hy),[(u['x']/32,u['y']/32,u['id']) for u in c]))
    return out
def tileflags(s):
    W,H=struct.unpack('<HH',s['DIM ']); ts=struct.unpack('<H',s['ERA '])[0]%8
    cv5=open(f'{TD}/{TS[ts]}.cv5','rb').read(); mt=struct.unpack(f'<{W*H}H',s['MTXM'])
    G=[[0]*W for _ in range(H)];F=[[0]*W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            g=mt[y*W+x]>>4; G[y][x]=g
            F[y][x]=struct.unpack_from('<H',cv5,g*52+2)[0] if g*52+52<=len(cv5) else 0
    return G,F
def choke(path):
    """natural outer choke: for ring k (k<=Dn<k+1 ground tiles from natural hall area), tiles in the ENEMY's component of {Dn>=k};
    width = min ring size over k in 6..cutR; entrances = 8-connected groups of that ring; area = walkable tiles with Dn<k* (minus main side)."""
    s=sections(path);W,H,wk,lvl=walkgrid(s);out=[]
    import check_ranked_bw as _c; _c.apply_blockers(W,H,wk,s)   # blocked_paths: natcut counts mineral walls / neutral buildings as closed
    for x in NC.metrics(path):
        a=near_walk(W,H,wk,int(x['nat'][0]),int(x['nat'][1]));Dn=dij(W,H,wk,[a])
        e=near_walk(W,H,wk,int(x['enemy'][0]),int(x['enemy'][1]));st=near_walk(W,H,wk,int(x['start'][0]),int(x['start'][1]))
        best=None
        for k in range(int(x['cutR'])+1,int(x['cutR'])+11):
            # flood enemy side in {Dn>=k}
            if Dn[e[1]][e[0]]<k: break
            seen={e};q=[e]
            while q:
                X,Y=q.pop()
                for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                    P=(X+dx,Y+dy)
                    if 0<=P[0]<W and 0<=P[1]<H and P not in seen and wk[P[1]][P[0]] and Dn[P[1]][P[0]]>=k: seen.add(P);q.append(P)
            if st in seen: continue
            ring=[p for p in seen if Dn[p[1]][p[0]]<k+1.5]
            if best is None or len(ring)<len(best[1]): best=(k,ring)
        if not best: out.append(dict(width=None,entr=0,area=0,start=x['start']));continue
        k,ring=best;R=set(ring);grp=0;sn=set()
        for p in ring:
            if p in sn: continue
            grp+=1;q=[p];sn.add(p)
            while q:
                X,Y=q.pop()
                for dx in(-1,0,1):
                    for dy in(-1,0,1):
                        P=(X+dx,Y+dy)
                        if P in R and P not in sn: sn.add(P);q.append(P)
        area=sum(1 for y in range(H) for X in range(W) if wk[y][X] and Dn[y][X]<k)
        out.append(dict(width=len(ring)/1.5,entr=grp,area=area,k=k,ring=ring,start=x['start'],nat=x['nat']))
    return out
def doodads(path,R=8):
    """doodad tiles (CV5 group>=1024) flagged unbuildable(0x80) or unwalkable(0x4/minitile) near each expected hall:
    hall = hall footprint 4x3 +1 margin; corr = mining corridor (between hall box and resource box, width 1.5);
    base = rest of the build zone (same level, ground dist <=R from hall, >2.5 tiles from any resource)."""
    s=sections(path);W,H,wk,lvl=walkgrid(s);G,F=tileflags(s);out=[]
    UB=[[G[y][x]>=1024 and bool(F[y][x]&0x84) for x in range(W)] for y in range(H)]
    for (hx,hy),res in hall_spots(s,W,H,wk,UB):
        a=near_walk(W,H,wk,int(hx),int(hy))
        if not a: continue
        L0=lvl[a[1]][a[0]]
        wk2=[[wk[y][x] or (G[y][x]>=1024 and lvl[y][x]==L0) for x in range(W)] for y in range(H)]
        D=dij(W,H,wk2,[a]);hall=[];base=[];corr=[]
        for y in range(max(0,int(hy)-R-2),min(H,int(hy)+R+3)):
            for x in range(max(0,int(hx)-R-2),min(W,int(hx)+R+3)):
                if G[y][x]<1024 or not (F[y][x]&0x84 or not wk[y][x]) or lvl[y][x]!=L0: continue
                cx,cy=x+.5,y+.5
                if abs(cx-hx)<=3 and abs(cy-hy)<=2.5: hall.append((x,y));continue
                if D[y][x]>R: continue
                inc=False;near=False
                for rx,ry,_ in res:
                    if math.hypot(cx-rx,cy-ry)<2.5: near=True
                    vx,vy=rx-hx,ry-hy;Ln=math.hypot(vx,vy) or 1;t=((cx-hx)*vx+(cy-hy)*vy)/Ln
                    if 1.5<t<Ln-1.5 and math.hypot(cx-hx-t*vx/Ln,cy-hy-t*vy/Ln)<1.5: inc=True
                if inc: corr.append((x,y))
                elif not near: base.append((x,y))
        out.append(dict(hall=(round(hx),round(hy)),hallt=hall,base=base,corr=corr))
    return out
CHOKE_MAX=16;ENTR_MAX=13;ENTR_MIN=6.5;CORR_MAX=2;BASE_WARN=30   # calibrated natural_choke on ladder refs
def check(path):
    F=[];I=[]
    try:
        C=choke(path);np_=len(C)
        for i,c in enumerate(C):
            if c['width'] is None: I.append(f'natural_choke_a start {i+1}: no outer choke found');continue
            pe=c['width']/max(1,c['entr'])
            I.append(f"natural_choke_a natural choke start {i+1}: width {c['width']:.1f} (<= {CHOKE_MAX}) entrances {c['entr']} per-entrance {pe:.1f} (<= {ENTR_MAX}) area {c['area']}")
            if pe<ENTR_MIN:
                m=f"natural_choke_a: natural entrance of start {i+1} too narrow ({pe:.1f} < {ENTR_MIN} tiles per entrance; refs min 7.3)"
                (F if np_<=2 else I).append(m if np_<=2 else 'WARN '+m)
            if c['width']>CHOKE_MAX or pe>ENTR_MAX:
                m=f"natural_choke_a: natural entrance of start {i+1} too wide (width {c['width']:.1f}/{CHOKE_MAX}, per entrance {pe:.1f}/{ENTR_MAX}; refs 2p 7-16 total, 7-13 per entrance)"
                (F if np_<=2 else I).append(m if np_<=2 else 'WARN '+m)
    except Exception as e: I.append(f'natural_choke_a skipped ({e})')
    for d in doodads(path):
        if d['hallt']: F.append(f"natural_choke_b: unbuildable/blocking doodad on the town-hall spot {d['hall']}: {d['hallt'][:6]}")
        if len(d['corr'])>CORR_MAX: F.append(f"natural_choke_b: blocking/unbuildable doodad tiles in mining corridor of hall {d['hall']}: {len(d['corr'])} {d['corr'][:6]}")
        if len(d['base'])>BASE_WARN: I.append(f"WARN natural_choke_b: {len(d['base'])} unbuildable doodad tiles in build zone of hall {d['hall']}")
    return F,I
if __name__=='__main__':
    f,i=check(sys.argv[1]);[print('INFO',x) for x in i];[print('FAIL',x) for x in f]
