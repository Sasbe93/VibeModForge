import sys,struct,os,numpy as np
from scipy import ndimage as nd
sys.path.insert(0,'tools/bw')
import predelivery_check as P, base_elevation as BE
def ramp_sizes(path):
    S=P.secs(path);h,w=BE.heights(S);H,W=h.shape
    m=np.zeros((H,W),bool)
    for dy,dx in((0,1),(1,0)):
        a=w[:H-dy,:W-dx]&w[dy:,dx:]&(h[:H-dy,:W-dx]!=h[dy:,dx:])
        m[:H-dy,:W-dx]|=a; m[dy:,dx:]|=a
    lab,n=nd.label(nd.binary_dilation(m,iterations=1)&m|m,structure=np.ones((3,3)))
    return sorted([int((lab==k).sum()) for k in range(1,n+1)],reverse=True)
if __name__=='__main__':
    for p in sys.argv[1:]:
        try: s=ramp_sizes(p)
        except Exception as e: continue
        print(f'{os.path.basename(p)[:24]:24s} n={len(s)} sizes={s[:16]}')
