import sys,struct,glob,os,collections,numpy as np
sys.path.insert(0,'tools/bw')
import predelivery_check as P, base_elevation as BE, resback
def ramps(path):
    S=P.secs(path);h,w=BE.heights(S);H,W=h.shape
    era=struct.unpack('<H',S['ERA '][:2])[0]&7
    cv5=open(resback.TS+resback.ERA[era]+'.cv5','rb').read()
    mt=np.array(struct.unpack(f'<{W*H}H',(S.get('MTXM') or S['TILE'])[:2*W*H])).reshape(H,W)
    c=collections.Counter()
    for y in range(H-1):
        for x in range(W-1):
            for dx,dy in((1,0),(0,1)):
                a,b=(y,x),(y+dy,x+dx)
                if w[a] and w[b] and h[a]!=h[b]:
                    for t in (mt[a],mt[b]):
                        g=t>>4
                        typ,f,ov,scr,sn,u,did,dw,dh=struct.unpack_from('<9H',cv5,g*52)
                        if typ==1 and did: c[(resback.ERA[era],did,dw,dh)]+=1
    return c
if __name__=='__main__':
    T=collections.Counter()
    for p in sys.argv[1:]:
        try: c=ramps(p)
        except Exception as e: print('ERR',os.path.basename(p),e);continue
        print(os.path.basename(p),sorted(c.items(),key=lambda x:-x[1])[:8]);T.update({k:1 for k in c})
    print('maps per ramp doodad', sorted(T.items(),key=lambda x:-x[1]))
