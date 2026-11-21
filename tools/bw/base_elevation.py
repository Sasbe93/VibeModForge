#!/usr/bin/env python3
"""Base elevation trope check for .scx.
Height per tile from the tileset CV5 group flags: 0x0400 high ground=2, 0x0200 mid=1, else low=0.
For every base (Command Center/Nexus/Hatchery/Lair/Hive or start location) compare the hall's tile height
(median of the 4x3 footprint) with the median height of walkable tiles in a ring 12-24 tiles around it.
RAISED = hall height > ring median. Unapproved raised >1 -> FAIL, exactly 1 -> WARN.
Approval: <map>.highground_ok.json: {"bases":[{"hall":[tx,ty],"reason":"..."}]} (match within 3 tiles).
Standalone: base_elevation.py A.scx [B.scx ...] (campaign summary: WARN if >1 in 4 missions has a raised base)."""
import sys,os,struct,json
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import resback
HALLS={106,131,132,133,154}; START=214
def heights(S):
    W,H=struct.unpack('<HH',S['DIM ']); era=struct.unpack('<H',S['ERA '][:2])[0]&7
    cv5=open(resback.TS+resback.ERA[era]+'.cv5','rb').read()
    mt=struct.unpack(f'<{W*H}H',(S.get('MTXM') or S['TILE'])[:2*W*H])
    h=np.zeros((H,W),int); w=np.zeros((H,W),bool)
    for i,t in enumerate(mt):
        g=t>>4
        if g*52+4<=len(cv5):
            fl=struct.unpack_from('<H',cv5,g*52+2)[0]
            h[i//W,i%W]=2 if fl&0x400 else (1 if fl&0x200 else 0); w[i//W,i%W]=not fl&4
    return h,w
def check(S,units,path):
    h,w=heights(S); H,W=h.shape; yy,xx=np.mgrid[0:H,0:W]
    B=[]
    for u in units:
        if u['id'] in HALLS or u['id']==START:
            tx,ty=u['x']//32,u['y']//32
            if not any(abs(tx-b[1])<=4 and abs(ty-b[2])<=4 for b in B): B.append((u['owner'],tx,ty,u['id']))
    ok=[]; sc=os.path.splitext(path)[0]+'.highground_ok.json'
    if os.path.exists(sc): ok=json.load(open(sc)).get('bases',[])
    out=[]; raised=[]; appr=[]
    for o,tx,ty,uid in B:
        hl=int(np.median(h[max(ty-1,0):ty+2,max(tx-2,0):tx+2]))
        r=np.hypot(xx-tx,yy-ty); ring=(r>=12)&(r<=24)&w
        med=float(np.median(h[ring])) if ring.any() else hl
        tag='ok'
        if hl>med:
            a=[e for e in ok if abs(e['hall'][0]-tx)<=3 and abs(e['hall'][1]-ty)<=3]
            if a: tag='RAISED-APPROVED (%s)'%a[0]['reason']; appr.append((tx,ty))
            else: tag='RAISED'; raised.append((tx,ty))
        out.append(f'  P{o+1} {"start" if uid==START else uid} tile ({tx},{ty}) height {hl}, ring median {med:.1f} -> {tag}')
    st='FAIL' if len(raised)>1 else ('WARN' if raised else 'OK  ')
    out.append(f'{st} base elevation (no high-ground trope; <map>.highground_ok.json to approve): {len(raised)} raised unapproved {raised or ""}, {len(appr)} approved, {len(B)} bases')
    return st,bool(raised or appr),out
if __name__=='__main__':
    import predelivery_check as P
    rc=0;n=0;anyr=0
    for p in sys.argv[1:]:
        S=P.secs(p); U=S['UNIT']
        units=[dict(x=struct.unpack_from('<H',U,i+4)[0],y=struct.unpack_from('<H',U,i+6)[0],id=struct.unpack_from('<H',U,i+8)[0],owner=U[i+16]) for i in range(0,len(U),36)]
        st,r,out=check(S,units,p); print('###',p); print('\n'.join(out)); rc|=st=='FAIL'; n+=1; anyr+=r
    if n>1: print('CAMPAIGN: %d/%d missions have a raised base -> %s'%(anyr,n,'WARN trope (>1 in 4)' if anyr*4>n else 'OK'))
    sys.exit(rc)
