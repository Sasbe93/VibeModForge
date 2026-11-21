"""water_doodads/cliff_doodads: context doodads matching reference usage.
place_ctx(m, ctx, count, forbid, seed, sym) with ctx='water' (footprint + 1-tile ring pure water, terrain 5) or
'cliff' (footprint unwalkable, ring touches >=2 walkable height levels, >=6 tiles from ramps/resources/forbid).
Ids per tileset come from the reference scan (catalogues/bw_features/doodads_water_cliff.json); a tileset without
reference ids gets nothing (ashworld: none in refs). Every placement is mirrored (same id) under the map symmetry."""
import json,random,struct,sys
sys.path.insert(0,'tools/lib/bw'); import sclib
REF=json.load(open('catalogues/bw_features/doodads_water_cliff.json'))
RAMPISH=lambda w,h: w>=6 and h>=5
def ids_for(ts,ctx,minmaps=2):
    d=REF['water' if ctx=='water' else 'cliff'].get(sclib.TSNAMES[ts],{})
    return [int(k) for k,v in d.items() if v['nmaps']>=minmaps and not (ctx=='cliff' and RAMPISH(v['w'],v['h']))]
def place_ctx(m,ctx,count,forbid=(),seed=1,sym='mirrorx',avoid_pts=(),ids=None,stats=None):
    rnd=random.Random(seed); cat,cv5=sclib.doodad_catalog_all(m.ts); ids=ids or ids_for(m.ts,ctx)
    cands=[(d,cat[d]) for d in ids if d in cat]
    if not cands: return 0
    W,H=m.W,m.H; mt=list(struct.unpack(f'<{W*H}H',m.mtxm)); water=sclib._pure_groups(m.ts,5) if ctx=='water' else set()
    def fl(i):
        g=mt[i]>>4; return struct.unpack_from('<H',cv5,g*52+2)[0] if g*52+52<=len(cv5) else 0
    walk=lambda x,y: not fl(y*W+x)&4; lvl=lambda x,y:(fl(y*W+x)>>9)&3
    used=set(); placed=0
    def mirror(x,y,w,h):
        return [(W-x-w,y)] if sym=='mirrorx' else [(W-x-w,H-y-h)] if sym=='rot2' else [(W-x-w,y),(W-x-w,H-y-h),(x,H-y-h)]
    def ok(x,y,w,h):
        if x<1 or y<1 or x+w>=W-1 or y+h>=H-3: return False
        for a,b,c,d in forbid:
            if x<c+6 and x+w>a-6 and y<d+6 and y+h>b-6: return False
        for px,py in avoid_pts:
            if abs(px-(x+w/2))<6+w/2 and abs(py-(y+h/2))<6+h/2: return False
        foot=[(xx,yy) for xx in range(x,x+w) for yy in range(y,y+h)]
        ring=[(xx,yy) for xx in range(x-1,x+w+1) for yy in range(y-1,y+h+1) if (xx,yy) not in foot]
        if any(p in used for p in foot+ring): return False
        if ctx=='water': return all((mt[yy*W+xx]>>4) in water for xx,yy in foot+ring)
        if all(walk(xx,yy) for xx,yy in foot): return False      # must sit on cliff tiles
        r2=[(xx,yy) for xx in range(x-2,x+w+2) for yy in range(y-2,y+h+2) if 0<=xx<W and 0<=yy<H]
        return len({lvl(xx,yy) for xx,yy in r2 if walk(xx,yy)})>=2
    def tiles(c,x,y):
        new={}
        for r in range(c['h']):
            for col in range(c['w']):
                mega=struct.unpack_from('<H',cv5,(c['g']+r)*52+20+col*2)[0]
                if mega: new[(y+r)*W+x+col]=(c['g']+r)*16+col
        return new
    if not hasattr(m,'dd2'): m.dd2=[]
    tries=0
    while placed<count and tries<count*3000:
        tries+=1; did,c=rnd.choice(cands); w,h=c['w'],c['h']
        x=rnd.randrange(1,max(2,W//2-w)); y=rnd.randrange(1,H-h-3)
        spots=[(x,y)]+mirror(x,y,w,h)
        if not all(ok(a,b,w,h) for a,b in spots): continue
        if len({(a,b) for a,b in spots})<len(spots): continue
        news=[tiles(c,a,b) for a,b in spots]
        def fv(v):
            g=v>>4; return struct.unpack_from('<H',cv5,g*52+2)[0] if g*52+52<=len(cv5) else 0
        if any(((not fl(k)&4) and fv(v)&4) for n in news for k,v in n.items()): continue   # never turn walkable ground unwalkable (no path/resource blocking)
        if any(sclib._doodad_edge(m.ts,cv5,mt,W,H,n,a,b,w,h)>sclib.DOODAD_EDGE_MAX*1.6 for n,(a,b) in zip(news,spots)): continue
        for n,(a,b) in zip(news,spots):
            for k,v in n.items(): mt[k]=v
            used.update((a+i,b+j) for i in range(-1,w+1) for j in range(-1,h+1))
            m.dd2.append(struct.pack('<HHHBB',did,a*32+w*16,b*32+h*16,12,0))
        placed+=1
    m.mtxm=struct.pack(f'<{W*H}H',*mt)
    if stats is not None: stats[ctx]=placed
    return placed
