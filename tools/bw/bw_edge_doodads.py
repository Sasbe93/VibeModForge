"""edge_doodads: natural, varied map edges + enough doodads. Calibrated on the ladder refs (see docs/bw-ranked-maps.md, edge_doodads).
edge: per side, distance from border to first walkable tile per row/col (band 0-16). Straight band -> low std.
variety: distinct CV5 tile groups among unwalkable tiles in the 10-tile border band.
doodads: DD2 entries per 1000 walkable tiles + share of 16x16 sectors containing a doodad."""
import sys,os,struct,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import base_elevation as BE, predelivery_check as P, resback
def metrics(path):
    S=P.secs(path);h,w=BE.heights(S);H,W=w.shape
    mt=np.array(struct.unpack(f'<{W*H}H',(S.get('MTXM') or S['TILE'])[:2*W*H])).reshape(H,W)>>4
    def depth(a):
        return [next((i for i in range(16) if a[r,i]),16) for r in range(a.shape[0])]
    sides=[depth(w),depth(w[:,::-1]),depth(w.T),depth(w.T[:,::-1])]
    stds=[float(np.std(s)) for s in sides]
    band=np.zeros_like(w);band[:10]=band[-10:]=band[:,:10]=band[:,-10:]=True
    groups=len(set(mt[band&~w].tolist()))
    # straight-run share: boundary walk/unwalk edges in the 16-tile band that lie on straight runs >=8 tiles
    b16=np.zeros_like(w);b16[:16]=b16[-16:]=b16[:,:16]=b16[:,-16:]=True
    tot=0;st=0
    for A in (w,w.T):
        e=(A[:,1:]!=A[:,:-1])&b16[:,1:] if A is w else (A[:,1:]!=A[:,:-1])&b16.T[:,1:]
        for c in range(e.shape[1]):
            col=e[:,c];tot+=col.sum();run=0
            for v in list(col)+[False]:
                if v: run+=1
                else:
                    if run>=8: st+=run
                    run=0
    straight=st/max(1,tot)
    dtiles=float((mt>=1024).sum())/max(1,w.sum())*1000
    dsec=len(set((x//16,y//16) for y,x in zip(*np.nonzero(mt>=1024))))
    dd=S.get('DD2 ',b'');D=[(struct.unpack_from('<H',dd,i+2)[0]//32,struct.unpack_from('<H',dd,i+4)[0]//32) for i in range(0,len(dd)-7,8)]
    sec=set((x//16,y//16) for x,y in D)
    return dict(edge_straight=straight,dtile_per_k=dtiles,dtile_sectors=dsec/((W//16)*(H//16)),edge_std_min=min(stds),edge_std_med=float(np.median(stds)),edge_groups=groups,dd_per_k=1000*len(D)/max(1,w.sum()),dd_sectors=len(sec)/((W//16)*(H//16)))
LO=dict(dtile_per_k=50,dtile_sectors=0.5,edge_std_min=1.5)   # refs min: 67 / 0.56 / 1.8 (Plasma)
HI=dict(edge_straight=0.33)                                   # refs max 0.32 (Plasma); test map X 0.40
def check(path):
    m=metrics(path);F=[]
    I=['edge_doodads edge/doodads: '+', '.join(f'{k} {v:.2f}' for k,v in m.items())+' (doodad tiles = CV5 group>=1024)']
    for k,t in LO.items():
        if m[k]<t: F.append(f'edge_doodads: {k} {m[k]:.2f} < {t} (refs min) - irregular varied edges / more doodads spread over the map')
    for k,t in HI.items():
        if m[k]>t: F.append(f'edge_doodads: {k} {m[k]:.2f} > {t} - edge outline too straight/rectangular')
    return F,I
if __name__=='__main__':
    for p in sys.argv[1:]:
        try: print(os.path.basename(p),{k:round(v,2) for k,v in metrics(p).items()})
        except Exception as e: print('ERR',p,e)
