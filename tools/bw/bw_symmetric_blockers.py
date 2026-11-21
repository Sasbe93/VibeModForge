"""symmetric_blockers: pathing-blocking doodads must be symmetric in the cells they block (under the map symmetry);
ideally DIFFERENT blocker doodads on each side blocking the same cells. Visual (walkable) doodads are free.
Mask = doodad tiles (CV5 group>=1024) that are unwalkable. Transform = the symmetry that best maps resources onto resources."""
import sys,math,struct
sys.path.insert(0,'tools/bw')
from check_ranked_bw import sections,walkgrid,units,MIN,GAS,SLOC
import bw_natural_choke as T
TOL=0.02;NEAR_MAX=0   # symmetric_blockers: stricter than BW refs (refs are not tile-exact symmetric, see docs/bw-ranked-maps.md)
def transforms(W,H):
    t={'mirrorx':lambda x,y:(W-1-x,y),'mirrory':lambda x,y:(x,H-1-y),'rot180':lambda x,y:(W-1-x,H-1-y)}
    if W==H: t.update(diag=lambda x,y:(y,x),antidiag=lambda x,y:(W-1-y,H-1-x),rot90=lambda x,y:(H-1-y,x))
    return t
def metrics(path):
    s=sections(path);W,H,wk,lvl=walkgrid(s);G,F=T.tileflags(s)
    R=[(u['x']/32,u['y']/32) for u in units(s) if u['id'] in MIN|GAS]
    best=None
    TT={}
    for n,f0 in transforms(W,H).items():
        for dx in range(-4,5):
            for dy in range(-4,5): TT[(n,dx,dy)]=(lambda f0,dx,dy:(lambda x,y:(f0(x,y)[0]+dx,f0(x,y)[1]+dy)))(f0,dx,dy)
    for n,f in TT.items():
        sc=sum(1 for x,y in R if any(abs(f(x-.5,y-.5)[0]+.5-a)<1.1 and abs(f(x-.5,y-.5)[1]+.5-b)<1.1 for a,b in R))/max(1,len(R))
        if best is None or sc>best[0]: best=(sc,n,f)
    sc,name,f=best
    # symmetric_blockers: tile blockers follow the TERRAIN symmetry; resource units may sit off by a pixel-rounding tile. Re-fit the shift on the walk grid.
    f0=transforms(W,H)[name[0]];bs=None
    for dx in range(-2,3):
        for dy in range(-2,3):
            ag=sum(1 for y in range(2,H-2,2) for x in range(2,W-2,2) if 0<=f0(x,y)[0]+dx<W and 0<=f0(x,y)[1]+dy<H and wk[y][x]==wk[f0(x,y)[1]+dy][f0(x,y)[0]+dx])
            if bs is None or ag>bs[0]: bs=(ag,dx,dy)
    # walk-grid ties are common (ramps/rounding): evaluate the blocker mask at the best shift AND its 1-tile neighbours incl. 0,0, keep the lowest mismatch
    Mb={(x,y) for y in range(H) for x in range(W) if G[y][x]>=1024 and (not wk[y][x] or (not walkgrid.minitile and F[y][x]&0x84))}
    cand={(bs[1],bs[2]),(0,0)}|{(bs[1]+a,bs[2]+b) for a in(-1,0,1) for b in(-1,0,1)}
    def _mm(d):
        g=lambda x,y:(f0(x,y)[0]+d[0],f0(x,y)[1]+d[1]); T_={g(x,y) for x,y in Mb}; return len(Mb^T_)/max(1,len(Mb|T_))
    d=min(cand,key=lambda d:(_mm(d),abs(d[0])+abs(d[1])))
    name=(name[0],d[0],d[1]);f=(lambda f0,dx,dy:(lambda x,y:(f0(x,y)[0]+dx,f0(x,y)[1]+dy)))(f0,d[0],d[1])
    proxy=not walkgrid.minitile   # no VF4 minitile data for this tileset: cv5 flags only. Proxy blocker = doodad tile flagged unwalkable OR unbuildable (0x4/0x80)
    M={(x,y) for y in range(H) for x in range(W) if G[y][x]>=1024 and (not wk[y][x] or (proxy and F[y][x]&0x84))}
    TM={f(x,y) for x,y in M}; X=M^TM; U=M|TM
    near=[p for p in X if any(math.hypot(p[0]-a,p[1]-b)<12 for a,b in R)]
    dd=s.get('DD2 ',b'');D=[(struct.unpack_from('<H',dd,i)[0],struct.unpack_from('<H',dd,i+2)[0]/32,struct.unpack_from('<H',dd,i+4)[0]/32) for i in range(0,len(dd)-7,8)]
    Bd=[d for d in D if (int(d[1]),int(d[2])) in M or any((int(d[1])+a,int(d[2])+b) in M for a in(-1,0) for b in(-1,0))]
    pairs=0;diff=0
    for i,x,y in Bd:
        tx,ty=f(x-.5,y-.5);tx+=.5;ty+=.5
        p=[j for j,a,b in Bd if abs(a-tx)<1.6 and abs(b-ty)<1.6]
        if p: pairs+=1;diff+=p[0]!=i
    return dict(proxy=proxy,sym=f'{name[0]}{name[1]:+d}{name[2]:+d}',symscore=sc,blocked=len(M),mismatch=len(X)/max(1,len(U)),near=len(near),pairs=pairs,variety=diff/pairs if pairs else None,nearpts=sorted(near)[:6])
def check(path):
    F=[];I=[];m=metrics(path)
    v='n/a' if m['variety'] is None else f"{m['variety']:.2f}"
    I.append(f"symmetric_blockers blocker symmetry ({m['sym']}): {m['blocked']} blocked doodad tiles{" (cv5 proxy)" if m["proxy"] else ""}, mismatch {m['mismatch']:.3f} (<= {TOL}), near bases {m['near']} (<= {NEAR_MAX}), variety {v} over {m['pairs']} pairs")
    bad=m['mismatch']>TOL or m['near']>NEAR_MAX
    if bad and m['symscore']<0.9: I.append(f"WARN symmetric_blockers: map resources not exactly symmetric (best {m['sym']} {m['symscore']:.2f}); blocker mismatch {m['mismatch']:.3f}")
    elif bad: F.append(f"symmetric_blockers: pathing-blocking doodads not symmetric ({m['sym']}): mismatch {m['mismatch']:.3f} > {TOL} or {m['near']} asym tiles near bases > {NEAR_MAX} e.g. {m['nearpts']}")
    if m['pairs'] and m['variety']==0: I.append("WARN symmetric_blockers: mirrored blocker pairs all use the SAME doodad id (prefer different ids with same footprint)")
    return F,I
