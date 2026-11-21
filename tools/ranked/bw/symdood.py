"""symmetric_blockers: BW tile doodads with mirror-symmetric pathing/building blockers (mirrorx, x->W-1-x).
Blocking doodads (any placed tile flagged 0x04 unwalkable / 0x80 unbuildable) are placed ONLY as pairs: A at (x,y), B at (W-x-w,y)
with mask(B)==fliplr(mask(A)); B preferably a DIFFERENT id. Visual (non-blocking) doodads stay free/random."""
import struct,random,sys
sys.path.insert(0,'tools/lib/bw')
import sclib
def masks(cat,cv5):
    M={}
    for did,c in cat.items():
        m=[]
        for r in range(c['h']):
            f=struct.unpack_from('<H',cv5,(c['g']+r)*52+2)[0]
            m.append(tuple(bool(struct.unpack_from('<H',cv5,(c['g']+r)*52+20+col*2)[0]) and bool(f&0x84) for col in range(c['w'])))
        M[did]=tuple(m)
    return M
def place_sym(m,count,terrains,forbid=(),high=False,seed=5,maxw=8,stats=None,only_block=False):
    rnd=random.Random(seed); cat,cv5=sclib.doodad_catalog(m.ts); MK=masks(cat,cv5)
    pure=set()
    for t in terrains: pure|=sclib._pure_groups(m.ts,t)
    cands=[c for c in cat.items() if c[1]['high']==high and not c[1]['mid'] and c[1]['w']<=maxw]
    if only_block: cands=[c for c in cands if any(any(r) for r in MK[c[0]])]   # battlefield_cover: battlefield cover pass (blocking doodads only)
    if not cands: return 0
    W,H=m.W,m.H; mt=list(struct.unpack(f'<{W*H}H',m.mtxm)); used=set(); placed=0
    if not hasattr(m,'dd2'): m.dd2=[]
    fl=lambda mk: tuple(tuple(reversed(r)) for r in mk)
    def free(x,y,w,h):
        if x<1 or y<1 or x+w>=W-1 or y+h>=H-3: return False
        for (a,b,c,d_) in list(forbid)+list(getattr(m,'noddrects',[])):
            if x<c and x+w>a and y<d_ and y+h>b: return False
        for yy in range(y-1,y+h+1):
            for xx in range(x-1,x+w+1):
                if (xx,yy) in used or (mt[yy*W+xx]>>4) not in pure: return False
        return True
    def tiles(c,x,y):
        new={}
        for r in range(c['h']):
            for col in range(c['w']):
                mega=struct.unpack_from('<H',cv5,(c['g']+r)*52+20+col*2)[0]
                if mega: new[(y+r)*W+x+col]=(c['g']+r)*16+col
        return new
    def okedge(c,x,y,new):
        return not (sclib._doodad_edge(m.ts,cv5,mt,W,H,new,x,y,c['w'],c['h'])>sclib.DOODAD_EDGE_MAX or sclib._doodad_edge.peak>sclib.DOODAD_EDGE_PEAK)
    def put(did,c,x,y,new):
        for k,v in new.items(): mt[k]=v
        for r in range(c['h']):
            for col in range(c['w']): used.add((x+col,y+r))
        m.dd2.append(struct.pack('<HHHBB',did,x*32+c['w']*16,y*32+c['h']*16,12,0))
    tries=0; npair=0; ndiff=0
    while placed<count and tries<count*400:
        tries+=1; did,c=rnd.choice(cands); w,h=c['w'],c['h']
        x=rnd.randrange(1,W-w-1); y=rnd.randrange(1,H-h-3)
        if not free(x,y,w,h): continue
        new=tiles(c,x,y)
        if not okedge(c,x,y,new): continue
        if not any(any(r) for r in MK[did]):
            put(did,c,x,y,new); placed+=1; continue           # visual doodad: free
        x2=W-x-w
        if x2<x+w+1: continue                                   # pair must not overlap/touch the axis
        want=fl(MK[did])
        P=[(d2,c2) for d2,c2 in cands if c2['w']==w and c2['h']==h and MK[d2]==want]
        if not P: continue
        P.sort(key=lambda t:(t[0]==did,rnd.random()))         # prefer a different id
        ok=False
        for d2,c2 in P:
            if not free(x2,y,w,h): break
            new2=tiles(c2,x2,y)
            if okedge(c2,x2,y,new2):
                put(did,c,x,y,new); put(d2,c2,x2,y,new2); placed+=2; npair+=1; ndiff+=d2!=did; ok=True; break
    m.mtxm=struct.pack(f'<{W*H}H',*mt)
    if stats is not None: stats['pairs']=stats.get('pairs',0)+npair; stats['diff']=stats.get('diff',0)+ndiff
    return placed
