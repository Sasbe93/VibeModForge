"""ramp_size: ramp clusters = connected tiles of ramp-sized doodad groups (>=4x3, CV5 type 1) touching a walkable level change.
Size = bounding box (long side, short side) in tiles."""
import sys,struct,os,numpy as np
from scipy import ndimage as nd
sys.path.insert(0,'tools/bw')
import predelivery_check as P, base_elevation as BE, resback
def clusters(path):
    S=P.secs(path);h,w=BE.heights(S);H,W=h.shape
    era=struct.unpack('<H',S['ERA '][:2])[0]&7
    cv5=open(resback.TS+resback.ERA[era]+'.cv5','rb').read()
    mt=np.array(struct.unpack(f'<{W*H}H',(S.get('MTXM') or S['TILE'])[:2*W*H])).reshape(H,W)
    big=np.zeros((H,W),bool)
    for g in np.unique(mt>>4):
        if g*52+18>len(cv5): continue
        typ,f,ov,scr,sn,u,did,dw,dh=struct.unpack_from('<9H',cv5,int(g)*52)
        if typ==1 and did and dw>=4 and dh>=3: big|=(mt>>4)==g
    ch=np.zeros((H,W),bool)
    for dy,dx in((0,1),(1,0)):
        a=w[:H-dy,:W-dx]&w[dy:,dx:]&(h[:H-dy,:W-dx]!=h[dy:,dx:]); ch[:H-dy,:W-dx]|=a; ch[dy:,dx:]|=a
    lab,n=nd.label(big,structure=np.ones((3,3)));out=[]
    for k in range(1,n+1):
        z=lab==k
        if not (z&ch).any(): continue
        ys,xs=np.nonzero(z); a,b=int(np.ptp(xs))+1,int(np.ptp(ys))+1
        if (z&w).sum()<6: continue
        out.append((max(a,b),min(a,b),int((z&ch).sum())))
    return sorted(out,reverse=True)
if __name__=='__main__':
    for p in sys.argv[1:]:
        try: c=clusters(p)
        except Exception as e: continue
        print(f'{os.path.basename(p)[:24]:24s} {len(c)} {c[:12]}')
