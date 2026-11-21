import os
"""ramp_size ramp placer: evaluates every (ramp id, x, y) in a window, sorted by cliff-match score; first one without a hard seam wins."""
import struct,numpy as np,sclib
def place_ramp(m,ids,box,maxscore=9.0,peak=sclib.DOODAD_EDGE_PEAK,exact=None):
    cat,cv5=sclib.doodad_catalog_all(m.ts); F=sclib._megafeat(m.ts)
    mt=list(struct.unpack(f'<{m.W*m.H}H',m.mtxm))
    M=lambda tid: struct.unpack_from('<H',cv5,(tid>>4)*52+20+(tid&15)*2)[0] if (tid>>4)*52+52<=len(cv5) else 0
    MF=F[np.array([M(v) for v in mt])].reshape(m.H,m.W,16,3)
    C=[]
    x0,y0,x1,y1=box if box else (0,0,0,0)
    for did in ids:
        c=cat[did]; w,h=c['w'],c['h']
        cells=[(r,col,struct.unpack_from('<H',cv5,(c['g']+r)*52+20+col*2)[0]) for r in range(h) for col in range(w)]
        ring=[(r,col,F[mg]) for r,col,mg in cells if mg and (r in(0,h-1) or col in(0,w-1))]
        rr=np.array([r for r,_,_ in ring]); cc=np.array([q for _,q,_ in ring]); fe=np.stack([f for _,_,f in ring])
        pos=[exact] if exact else [(x,y) for y in range(max(1,y0),min(m.H-h-1,y1)) for x in range(max(1,x0),min(m.W-w-1,x1))]
        for x,y in pos:
            C.append((float(np.abs(MF[y+rr,x+cc]-fe).mean()),did,x,y))
    C.sort()
    if os.environ.get('RDBG'): print('cands',box,C[:5])
    for sc,did,x,y in C:
        if sc>maxscore: break
        c=cat[did]; w,h=c['w'],c['h']
        nw={(y+r)*m.W+x+col:(c['g']+r)*16+col for r in range(h) for col in range(w) if struct.unpack_from('<H',cv5,(c['g']+r)*52+20+col*2)[0]}
        sclib._doodad_edge(m.ts,cv5,mt,m.W,m.H,nw,x,y,w,h)
        if os.environ.get('RDBG'): print('  try',did,x,y,round(sc,2),'peak',round(sclib._doodad_edge.peak,1))
        if sclib._doodad_edge.peak>peak: continue
        for k,v in nw.items(): mt[k]=v
        m.mtxm=struct.pack(f'<{m.W*m.H}H',*mt)
        if not hasattr(m,'dd2'): m.dd2=[]
        m.dd2.append(struct.pack('<HHHBB',did,x*32+w*16,y*32+h*16,12,0))
        m.ramp_cells=getattr(m,'ramp_cells',set())|{(x+a,y+b) for a in range(-2,w+2) for b in range(-2,h+2)}
        return (did,x,y,round(sc,2),w,h)
    return None
def valid(m,ids,box,maxscore=float(os.environ.get("RMAX","9")),peak=float(os.environ.get("RPEAK","20"))):
    cat,cv5=sclib.doodad_catalog_all(m.ts); F=sclib._megafeat(m.ts)
    mt=list(struct.unpack(f'<{m.W*m.H}H',m.mtxm))
    M=lambda tid: struct.unpack_from('<H',cv5,(tid>>4)*52+20+(tid&15)*2)[0] if (tid>>4)*52+52<=len(cv5) else 0
    MF=F[np.array([M(v) for v in mt])].reshape(m.H,m.W,16,3)
    x0,y0,x1,y1=box; out=[]
    for did in ids:
        c=cat[did]; w,h=c['w'],c['h']
        cells=[(r,col,struct.unpack_from('<H',cv5,(c['g']+r)*52+20+col*2)[0]) for r in range(h) for col in range(w)]
        ring=[(r,col,F[mg]) for r,col,mg in cells if mg and (r in(0,h-1) or col in(0,w-1))]
        rr=np.array([r for r,_,_ in ring]); cc=np.array([q for _,q,_ in ring]); fe=np.stack([f for _,_,f in ring])
        for y in range(max(1,y0),min(m.H-h-1,y1)):
            for x in range(max(1,x0),min(m.W-w-1,x1)):
                sc=float(np.abs(MF[y+rr,x+cc]-fe).mean())
                if sc>maxscore: continue
                nw={(y+r)*m.W+x+col:(c['g']+r)*16+col for r in range(h) for col in range(w) if struct.unpack_from('<H',cv5,(c['g']+r)*52+20+col*2)[0]}
                sclib._doodad_edge(m.ts,cv5,mt,m.W,m.H,nw,x,y,w,h)
                if sclib._doodad_edge.peak<=peak: out.append((sc,did,x,y,w,h))
    return out
def pair(m,ids,box,W):
    L=valid(m,ids,box); x0,y0,x1,y1=box
    R=valid(m,ids,(W-x1-8,y0,W-x0,y1))
    if os.environ.get('RDBG'): print('valid',box,len(L),len(R),sorted(L)[:4],sorted(R)[:4])
    best=None
    for a in L:
        for b in R:
            d=abs((W-b[2]-b[4])-a[2])+abs(b[3]-a[3])
            if os.environ.get('RXACT') and d: continue   # exact_mirror: exact mirror position (symmetric_blockers near-base symmetry)
            k=d*6+a[0]+b[0]
            if best is None or k<best[0]: best=(k,a,b)
    if not best: return None
    for s in best[1:]: place_ramp(m,[s[1]],None,maxscore=99,peak=999,exact=(s[2],s[3]))
    return best
