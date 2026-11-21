#!/usr/bin/env python3
"""resource_ground/mineral_layout/ScmDraft checks: resources on walkable ground at hall level, no resource blocking another's line
to the hall, strict CHK structure. Usage: check_bw_rules.py map.scx"""
import sys,struct,math
sys.path.insert(0,'tools/bw')
import check_ranked_bw as C
from eudplib.bindings._rust import mpqapi
SZ=C.SZ; F=[]; I=[]
def strict_chk(path):
    m=mpqapi.MPQ.open(path); d=bytes(m.extract_file('staredit\\scenario.chk')); i=0; seen={}
    while i<len(d):
        if i+8>len(d): F.append('CHK trailing bytes'); break
        k=d[i:i+4].decode('latin1'); n=struct.unpack_from('<i',d,i+4)[0]
        if n<0 or i+8+n>len(d): F.append(f'CHK section {k!r} bad size {n}'); break
        if k in seen: F.append(f'CHK duplicate section {k}')
        seen[k]=d[i+8:i+8+n]; i+=8+n
    for k in ['VER ','DIM ','ERA ','MTXM','UNIT','OWNR','SIDE','STR ']:
        if k not in seen: F.append(f'CHK missing {k}')
    if F: return
    W,H=struct.unpack('<HH',seen['DIM '])
    if len(seen['MTXM'])!=W*H*2: F.append('MTXM size != W*H*2')
    if len(seen['UNIT'])%36: F.append('UNIT size not %36')
    if 'THG2' in seen and len(seen['THG2'])%10: F.append('THG2 size not %10')
    for k in ['OWNR','SIDE']:
        if len(seen[k])!=12: F.append(f'{k} size != 12')
    st=seen['STR ']; n=struct.unpack_from('<H',st,0)[0]
    for j in range(n):
        o=struct.unpack_from('<H',st,2+2*j)[0]
        if o and o>=len(st): F.append(f'STR offset {j+1} out of range')
    I.append(f'CHK sections {len(seen)}, {W}x{H}, ver {struct.unpack("<H",seen["VER "])[0]}')
def rect(u,shrink=0):
    w,h=SZ[u['id']]; return (u['x']-w*16+shrink,u['y']-h*16+shrink,u['x']+w*16-shrink,u['y']+h*16-shrink)
def run(path):
    strict_chk(path)
    s=C.sections(path); W,H,wk,lvl=C.walkgrid(s); U=C.units(s)
    BLK=[u for u in U if u['id'] in (176,177,178) and u['res']<=50]
    for u in BLK:   # blockers: footprint must still be on walkable ground (minable from at least one side)
        x0,y0,x1,y1=rect(u)
        if any(not wk[yy][xx] for yy in range(y0//32,(y1-1)//32+1) for xx in range(x0//32,(x1-1)//32+1)): F.append(f'resource_ground blocker mineral at {u["x"]//32},{u["y"]//32} on unwalkable ground')
    R=[u for u in U if u['id'] in (176,177,178,188) and u not in BLK]; halls=[(u['x'],u['y']) for u in U if u['id']==214]
    cl=[]
    for u in R:
        for c in cl:
            if any(abs(u['x']-v['x'])<=12*32 and abs(u['y']-v['y'])<=12*32 for v in c): c.append(u); break
        else: cl.append([u])
    occ=set()
    for u in R:
        x0,y0,x1,y1=rect(u)
        for yy in range(y0//32,(y1-1)//32+1):
            for xx in range(x0//32,(x1-1)//32+1): occ.add((xx,yy))
    nb=0
    for c in cl:
        cx=sum(u['x'] for u in c)/len(c); cy=sum(u['y'] for u in c)/len(c)
        st=[h for h in halls if abs(h[0]-cx)<12*32 and abs(h[1]-cy)<12*32]
        if st: hx,hy=st[0]; hx-=64; hy-=48
        else:   # best legal 4x3 hall spot: walkable, off resources, gaps >=3 tiles, closest to cluster
            best=None
            for ty in range(H-2):
                for tx in range(W-3):
                    T=[(tx+a,ty+b) for a in range(4) for b in range(3)]
                    if any(not wk[y][x] or (x,y) in occ for x,y in T): continue
                    if any(abs(tx*32+64-u['x'])<(SZ[u['id']][0]*16+64+3*32) and abs(ty*32+48-u['y'])<(SZ[u['id']][1]*16+48+3*32) for u in c): continue
                    d=sum(math.hypot(tx*32+64-u['x'],ty*32+48-u['y']) for u in c)
                    if best is None or d<best[0]: best=(d,tx*32,ty*32)
            if not best: F.append(f'no hall spot for cluster at {int(cx)//32},{int(cy)//32}'); continue
            _,hx,hy=best
        hl=lvl[(hy+48)//32][(hx+64)//32]
        for u in c:
            x0,y0,x1,y1=rect(u)
            T=[(xx,yy) for yy in range(y0//32,(y1-1)//32+1) for xx in range(x0//32,(x1-1)//32+1)]
            if any(not wk[y][x] for x,y in T): F.append(f'resource_ground resource {u["id"]} at {u["x"]//32},{u["y"]//32} on unwalkable ground')
            if any(lvl[y][x]!=hl for x,y in T): F.append(f'resource_ground resource at {u["x"]//32},{u["y"]//32} not on hall level')
            # line to nearest point of hall
            px=min(max(u['x'],hx),hx+128); py=min(max(u['y'],hy),hy+96)
            L=max(1,int(math.hypot(px-u['x'],py-u['y'])/4))
            for v in c:
                if v is u: continue
                a,b,c2,d=rect(v,2)
                if any(a<u['x']+(px-u['x'])*k/L<c2 and b<u['y']+(py-u['y'])*k/L<d for k in range(L+1)):
                    F.append(f'mineral_layout resource at {u["x"]//32},{u["y"]//32} blocked by {v["x"]//32},{v["y"]//32}'); break
        nb+=1
    I.append(f'{nb} resource clusters checked, {len(R)} resources')
    try:
        import sclib; r=sclib.validate(path); I.append(f'sclib.validate: {r}')
    except Exception as e: I.append(f'sclib.validate not run: {e}')
    for x in I: print('INFO',x)
    for x in F: print('FAIL',x)
    print('RESULT','OK' if not F else f'FAIL ({len(F)})'); return not F
if __name__=='__main__': sys.exit(0 if run(sys.argv[1]) else 1)
