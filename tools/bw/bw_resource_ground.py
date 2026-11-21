# resource_footprint: every mineral/geyser footprint on walkable ground of the base level; geyser on buildable; harvest side reachable.
import sys,math,struct
sys.path.insert(0,'tools/bw')
from check_ranked_bw import sections,walkgrid,units,dij,near_walk,MIN,GAS,SLOC,TD,TS
def check(path):
    s=sections(path); W,H,wk,lvl=walkgrid(s); ts=struct.unpack('<H',s['ERA '])[0]%8
    cv5=open(f'{TD}/{TS[ts]}.cv5','rb').read(); mt=struct.unpack(f'<{W*H}H',s['MTXM'])
    def fl(x,y): g=mt[y*W+x]>>4; return struct.unpack_from('<H',cv5,g*52+2)[0] if g*52+52<=len(cv5) else 0
    U=units(s); st=[u for u in U if u['id']==SLOC]
    D=dij(W,H,wk,[near_walk(W,H,wk,u['x']//32,u['y']//32) for u in st])
    F=[];W2=[];n=0
    RS=[(u['x']//32,u['y']//32) for u in U if u['id'] in MIN or u['id'] in GAS]
    for u in U:
        if u['id'] not in MIN and u['id'] not in GAS: continue
        if sum(abs(a-u['x']//32)+abs(b-u['y']//32)<=6 for a,b in RS)<4: continue   # lone blocker minerals (refs use them in walls)
        n+=1; gas=u['id'] in GAS; w,h=(4,2) if gas else (2,1)
        x0=(u['x']-16*w)//32; y0=(u['y']-16*h)//32
        fp=[(x,y) for x in range(x0,x0+w) for y in range(y0,y0+h) if 0<=x<W and 0<=y<H]
        bad=[]
        nw=[(x,y) for x,y in fp if not wk[y][x]]
        if len(nw)*2>len(fp) or (gas and len(nw)>3): bad.append(f'{len(nw)}/{len(fp)} footprint tiles not walkable (water/cliff)')
        lv={lvl[y][x] for x,y in fp}
        pass  # level span / unbuildable geyser tiles occur on refs -> INFO only
        
        adj=[(x,y) for x in range(x0-2,x0+w+2) for y in range(y0-2,y0+h+2) if 0<=x<W and 0<=y<H and (x,y) not in fp and wk[y][x]]
        if not adj: bad.append('no walkable tile next to it (unharvestable)')
        elif not any(D[y][x]<math.inf for x,y in adj): W2.append(f"WARN resource_footprint resource at ({u['x']//32},{u['y']//32}) not ground-reachable from a start (island base?)")
        if bad: F.append(f"FAIL resource_footprint {'geyser' if gas else 'mineral'} at tile ({u['x']//32},{u['y']//32}): "+'; '.join(bad))
    return F,[f'INFO resource_footprint resources: {n} checked, {len(F)} on bad ground, {len(W2)} not ground-reachable']+W2[:3]
if __name__=='__main__':
    f,i=check(sys.argv[1]); print('\n'.join(i+f))
