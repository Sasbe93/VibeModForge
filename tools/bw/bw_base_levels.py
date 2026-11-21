"""base_elevation: bases use elevation. Height per tile from CV5 (base_elevation.heights).
Calibrated on 21 ladder references (refmaps/bw): mains on the map's highest walkable level in 58/72 starts,
expansions on >=2 height levels in 19/21 maps, 54% of expansions raised/lowered vs their 14-26 tile ring.
FAIL: all expansions on one level, or <25% of expansions off-level vs surroundings. WARN: a start below the top level."""
import sys,os,struct,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import base_elevation as BE, predelivery_check as P
def survey(path):
    S=P.secs(path);U=S['UNIT']
    us=[(struct.unpack_from('<H',U,i+4)[0]//32,struct.unpack_from('<H',U,i+6)[0]//32,struct.unpack_from('<H',U,i+8)[0]) for i in range(0,len(U),36)]
    h,w=BE.heights(S);H,W=h.shape;yy,xx=np.mgrid[0:H,0:W]
    starts=[(x,y) for x,y,i in us if i==214];cl=[]
    for r in [(x,y) for x,y,i in us if i in(176,177,178,188)]:
        for c in cl:
            if any(abs(r[0]-a)+abs(r[1]-b)<=6 for a,b in c): c.append(r);break
        else: cl.append([r])
    B=[]
    for c in [c for c in cl if len(c)>=4]:
        cx=np.mean([a for a,_ in c]);cy=np.mean([b for _,b in c]);d=np.hypot(xx-cx,yy-cy)
        fl=(d<=8)&w;ring=(d>=14)&(d<=26)&w
        B.append((any(np.hypot(cx-a,cy-b)<14 for a,b in starts),int(np.median(h[fl])) if fl.any() else 0,float(np.median(h[ring])) if ring.any() else 0,(int(cx),int(cy))))
    return B,int(h[w].max())
def check(path):
    B,top=survey(path);F=[];s=[b for b in B if b[0]];e=[b for b in B if not b[0]]
    off=[b for b in e if b[1]!=round(b[2])];lv=sorted({b[1] for b in e})
    I=[f'base_elevation base elevation: starts levels {[b[1] for b in s]} (top {top}); expansions levels {lv}, off-level {len(off)}/{len(e)} (refs: 19/21 maps >=2 levels, 54% off-level)']
    if len(lv)<2: F.append(f'base_elevation: all {len(e)} expansions on one height level {lv} - put some on raised/lowered plateaus')
    if e and len(off)<0.25*len(e): F.append(f'base_elevation: only {len(off)}/{len(e)} expansions raised/lowered vs surroundings (<25%)')
    lo=[b[3] for b in s if b[1]<top]
    if lo: I.append(f'WARN base_elevation: start(s) {lo} not on the highest level {top} (refs: 58/72 mains on top level)')
    return F,I
if __name__=='__main__':
    rc=0
    for p in sys.argv[1:]:
        F,I=check(p);print('###',os.path.basename(p));[print('INFO',x) for x in I];[print('FAIL',x) for x in F];rc|=bool(F)
    sys.exit(rc)
