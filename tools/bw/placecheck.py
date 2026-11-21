#!/usr/bin/env python3
"""Placement check (BW): every pre-placed building/resource on legal, flat, buildable terrain, no overlaps,
creep for Zerg, pylon power for Protoss, clear margins around town halls, every unit/building/location reachable from
the player start. Data: CV5 tile flags (tileset files, external/README.md) + placement sizes (sclib.BUILDSIZE).
Usage (repository root): python3 tools/bw/placecheck.py MAP.scx TILESET_INDEX     (0 badlands ... 7 twilight)
Library: check(path,ts), check_data(...), autofix(m) for build scripts (moves misplaced non-hall buildings/units,
adds Creep Colonies/Pylons where needed)."""
import struct,os,sys
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','lib','bw'))
from sclib import *
import sclib
INF_CC,SPIRE,QNEST,DEFMOUND,FORGE,ROBO,STARGATE=130,141,138,136,166,155,167
OVERMIND,CEREBRATE,PSI_DISRUPTER,POWER_GEN,ION_CANNON,COMSAT,NUKE_SILO=148,151,190,200,127,107,108
SCIENCE,DROPSHIP,CORSAIR,ARBITER,OBSERVER=9,11,60,71,84
B=sclib.BUILDSIZE
B.update({OVERMIND:(5,4),CEREBRATE:(3,2),INF_CC:(4,3),PSI_DISRUPTER:(5,3),POWER_GEN:(4,3),ION_CANNON:(3,2),SPIRE:(2,2),QNEST:(3,2),
          DEFMOUND:(4,2),NUKE_SILO:(2,2),COMSAT:(2,2),ROBO:(3,2),STARGATE:(4,3),FORGE:(3,2)})
HALLS={HATCH,LAIR,HIVE,CC,NEXUS,INF_CC}
ZERG_B={HATCH,LAIR,HIVE,POOL,HYDEN,EXTRACTOR,CREEP,SUNKEN,SPORE,EVO,SPIRE,QNEST,DEFMOUND,134}
CREEP_SRC={HATCH:(9.5,6.5),LAIR:(9.5,6.5),HIVE:(9.5,6.5),CREEP:(5.5,4),SUNKEN:(5.5,4),SPORE:(5.5,4)}
NESTP=-1   # optional: owner slot of an allied nest that may sit on the player's creep (-1 = none)
TOSS_B={GATEWAY,CANNON,FORGE,ROBO,STARGATE,164}
B.update({164:(3,2),157:(4,2),110:(4,2)})
SPECIAL={CRYSTAL,TEMPLE,XEL_TEMPLE,STASIS,OVERMIND,CEREBRATE,PSI_DISRUPTER,POWER_GEN,ION_CANNON}
ADDON={COMSAT:CC,NUKE_SILO:CC}
def chk_sections(path):
    q=mpqapi.MPQ.open(path); d=bytes(q.extract_file('staredit\\scenario.chk')); s={}; i=0
    while i<len(d):
        k=d[i:i+4].decode(); n=struct.unpack_from('<I',d,i+4)[0]; s.setdefault(k,d[i+8:i+8+n]); i+=8+n
    return s
def check(path,ts):
    s=chk_sections(path); W,H=struct.unpack('<HH',s['DIM '])
    return check_data(W,H,s['MTXM'],s['UNIT'],s.get('DD2 ',b''),ts,s.get('MRGN',b''))
_C={}
AIR={OVERLORD,MUTA,GUARDIAN,WRAITH,BC,VALK,SCOUT,CARRIER,SCIENCE,DROPSHIP,CORSAIR,ARBITER,OBSERVER,QUEEN,SCOURGE,DEVOURER}
def components(W,H,walk):
    comp=[-1]*(W*H); n=0
    for i in range(W*H):
        if not walk[i] or comp[i]>=0: continue
        st=[i]; comp[i]=n
        while st:
            j=st.pop(); x,y=j%W,j//W
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                X,Y=x+dx,y+dy
                if 0<=X<W and 0<=Y<H:
                    k=Y*W+X
                    if walk[k] and comp[k]<0 and (dx==0 or dy==0 or (walk[y*W+X] and walk[Y*W+x])): comp[k]=n; st.append(k)
        n+=1
    return comp
def check_data(W,H,mtxm,unitb,dd2b,ts,mrgn=b''):
    s={'UNIT':unitb,'DD2 ':dd2b}; mt=struct.unpack(f'<{W*H}H',mtxm)
    if ts not in _C: _C[ts]=(open(f'{TOOLS}/tileset/{TSNAMES[ts]}.cv5','rb').read(),doodad_catalog_all(ts)[0])
    cv5,cat=_C[ts]
    def tf(x,y):
        if not(0<=x<W and 0<=y<H): return None
        g=mt[y*W+x]>>4; t,f=struct.unpack_from('<HH',cv5,g*52)
        if ts==2 and f&0x80 and not f&0x01: f|=0x0004   # installation: substructure panels / bottomless pit are unwalkable
        return t,f
    dood=set()
    d=s.get('DD2 ',b'')
    for i in range(0,len(d),8):
        did,px,py,_,_=struct.unpack_from('<HHHBB',d,i); c=cat.get(did)
        if c:
            x0,y0=px//32-c['w']//2,py//32-c['h']//2
            for yy in range(y0,y0+c['h']):
                for xx in range(x0,x0+c['w']): dood.add((xx,yy))
    U=[]
    for i in range(0,len(s['UNIT']),36):
        px,py,uid=struct.unpack_from('<HHH',s['UNIT'],i+4); own=s['UNIT'][i+16]; U.append((uid,px,py,own))
    errs=[]; occ={}; stats=dict(buildings=0,resources=0,units=0)
    def E(kind,uid,px,py,own,msg): errs.append((kind,uid,px//32,py//32,own,msg))
    blds=[(u,px,py,o) for u,px,py,o in U if u in B]
    for u,px,py,o in blds:
        w,h=B[u]; x0,y0=px//32-w//2,py//32-h//2
        stats['resources' if u in (MINERAL,GEYSER) else 'buildings']+=1
        elev=set()
        for yy in range(y0,y0+h):
            for xx in range(x0,x0+w):
                r=tf(xx,yy)
                if r is None: E('offmap',u,px,py,o,''); continue
                t,f=r
                if f&0x0004: E('unwalkable',u,px,py,o,f'tile {xx},{yy} f={f:#x}')
                elif f&0x0080 and not (ts==2 and o!=0 and f&0x0001): E('unbuildable',u,px,py,o,f'tile {xx},{yy} f={f:#x}')   # installation: preplaced enemy structures may stand on walkable station floor (as in Blizzard installation missions)
                if t==1 or (xx,yy) in dood: E('doodad',u,px,py,o,f'tile {xx},{yy}')
                elev.add(f&0x0600)
                if (xx,yy) in occ: E('overlap',u,px,py,o,f'with unit {occ[(xx,yy)]}')
                occ[(xx,yy)]=u
        if len(elev)>1: E('not_flat',u,px,py,o,str(elev))
    # town hall margin: 2-tile ring buildable+walkable+no doodad
    for u,px,py,o in blds:
        if u not in HALLS: continue
        w,h=B[u]; x0,y0=px//32-w//2,py//32-h//2; bad=0; badt=[]
        for yy in range(y0-2,y0+h+2):
            for xx in range(x0-2,x0+w+2):
                if x0<=xx<x0+w and y0<=yy<y0+h: continue
                r=tf(xx,yy)
                if r is None or r[1]&0x0084 or r[0]==1 or (xx,yy) in dood: bad+=1; badt.append((xx,yy,'dood' if (xx,yy) in dood else (hex(r[1]) if r else 'off')))
        if bad: E('hall_margin',u,px,py,o,f'{bad} blocked tiles in 2-tile ring {badt[:6]}')
    # creep / power / addons
    for u,px,py,o in blds:
        if u in ZERG_B and u not in (HATCH,LAIR,HIVE):
            w,h=B[u]; ok=False
            for v,qx,qy,qo in blds:
                if v in CREEP_SRC and (qo==o or (o==NESTP and qo==0)) and (v,qx,qy)!=(u,px,py) and (v in (HATCH,LAIR,HIVE) or u==EXTRACTOR or True):
                    rx,ry=CREEP_SRC[v]
                    if all(((cx-qx)/32/rx)**2+((cy-qy)/32/ry)**2<=1 for cx in (px-w*16,px+w*16) for cy in (py-h*16,py+h*16)): ok=True;break
            if not ok: E('no_creep',u,px,py,o,'')
        if u in TOSS_B:
            if not any(v==PYLON and qo==o and ((px-qx)/256)**2+((py-qy)/160)**2<=1 for v,qx,qy,qo in blds): E('no_power',u,px,py,o,'')
        if u in ADDON:
            if not any(v==ADDON[u] and qo==o and abs((qx+64)-(px-32))<=2 and abs((qy+32)-(py+16))<=2 for v,qx,qy,qo in blds): E('addon_unattached',u,px,py,o,'')
    # ground units must not stand inside buildings or on unwalkable tiles
    for u,px,py,o in U:
        if u in B or u==STARTLOC: continue
        stats['units']+=1
        if u in AIR: continue
        tx,ty=px//32,py//32; r=tf(tx,ty)
        if (tx,ty) in occ: E('unit_in_building',u,px,py,o,f'in {occ[(tx,ty)]}')
        elif r is None or r[1]&0x0004: E('unit_unwalkable',u,px,py,o,'')
    # ---- ground connectivity (tile walkability flood fill) ----
    walk=[0]*(W*H)
    for i in range(W*H):
        g=mt[i]>>4; f=struct.unpack_from('<H',cv5,g*52+2)[0]; walk[i]=0 if (f&0x0004 or (ts==2 and f&0x80 and not f&0x01)) else 1
    comp=components(W,H,walk)
    start=[(px//32,py//32) for u,px,py,o in U if u==STARTLOC and o==0] or [(px//32,py//32) for u,px,py,o in U if o==0 and u not in AIR and u not in B]
    main=comp[start[0][1]*W+start[0][0]] if start else -1
    if main<0 and start:   # start loc on a blocked tile: take the nearest walkable component
        sx,sy=start[0]; best=min(((abs(i%W-sx)+abs(i//W-sy)),comp[i]) for i in range(W*H) if comp[i]>=0); main=best[1]
    stats['main_component_tiles']=sum(1 for c in comp if c==main)
    for u,px,py,o in U:
        if u==STARTLOC or u in AIR or u in (MINERAL,GEYSER): continue
        if u in B:
            w,h=B[u]; x0,y0=px//32-w//2,py//32-h//2
            ring=[(xx,yy) for xx in range(x0-1,x0+w+1) for yy in range(y0-1,y0+h+1) if 0<=xx<W and 0<=yy<H and not(x0<=xx<x0+w and y0<=yy<y0+h)]
            if not any(comp[yy*W+xx]==main for xx,yy in ring): E('unreachable_building',u,px,py,o,'')
        else:
            tx,ty=px//32,py//32
            if comp[ty*W+tx]!=main: E('unreachable_unit',u,px,py,o,'not connected to the player start')
    stats['locations']=0
    for i in range(0,len(mrgn),20):
        l,t,r,b,nm,_=struct.unpack_from('<IIIIHH',mrgn,i)
        if not nm or i//20==63: continue
        stats['locations']+=1
        tiles=[(x,y) for x in range(l//32,min(W,(r+31)//32)) for y in range(t//32,min(H,(b+31)//32))]
        if tiles and not any(comp[y*W+x]==main for x,y in tiles): errs.append(('unreachable_location',0,(l+r)//64,(t+b)//64,i//20+1,'no walkable tile connected to the player start'))
    return errs,stats
if __name__=='__main__':
    import collections
    errs,st=check(sys.argv[1],int(sys.argv[2]))
    print(st,collections.Counter(e[0] for e in errs))
    for e in errs[:60]: print(e)

def autofix(m,log=print):
    """relocate misplaced non-hall buildings / units, add Creep Colonies and Pylons where needed. Halls+resources are handled by terrain pads."""
    import collections
    def run(): return check_data(m.W,m.H,m.mtxm,b''.join(m.units),b''.join(getattr(m,'dd2',[])),m.ts,b''.join(m.mrgn))[0]
    def idx_of(e):
        for i,u in enumerate(m.units):
            px,py,uid=struct.unpack_from('<HHH',u,4)
            if uid==e[1] and px//32==e[2] and py//32==e[3] and u[16]==e[4]: return i
    def setpos(i,px,py):
        px=min(max(px,16),m.W*32-16); py=min(max(py,16),m.H*32-16)
        b=bytearray(m.units[i]); struct.pack_into('<HH',b,4,px,py); m.units[i]=bytes(b)
    def score(es): return len(es)
    moved=added=0
    errs=run(); base=score(errs)
    for rnd in range(6):
        bad=[e for e in errs if e[1] not in HALLS and e[1] not in (MINERAL,GEYSER)]
        if not bad: break
        done=set()
        for e in bad:
            i=idx_of(e)
            if i is None or i in done: continue
            done.add(i)
            u=m.units[i]; px,py,uid=struct.unpack_from('<HHH',u,4); own=u[16]
            if own==NESTP: own=0   # never give an allied nest slot extra buildings
            if e[0]=='no_creep' or e[0]=='no_power':
                # first try inserting a provider next to it
                prov=CREEP if e[0]=='no_creep' else PYLON
                w,h=B[uid]; best=None
                for r in range(1,4):
                    for dx in range(-r-2,r+w+1):
                        for dy in range(-r-2,r+h+1):
                            tx,ty=px//32-w//2+dx,py//32-h//2+dy
                            if not(0<=tx<m.W-2 and 0<=ty<m.H-2): continue
                            m.units.append(struct.pack('<IHHHHHHBBBBIHHII',len(m.units)+1,tx*32+32,ty*32+32,prov,0,0,0x1F,own,100,100,100,0,0,0,0,0))
                            es=run()
                            if len(es)<len(errs) and not any(x[2:4]==(tx+1,ty+1) and x[1]==prov for x in es): best=(len(es),es); break
                            m.units.pop()
                        if best: break
                    if best: break
                if best: errs=best[1]; added+=1; continue
            # relocate: spiral search for a spot that removes this unit's violations without adding new ones
            ok=False
            for r in range(1,4 if uid in SPECIAL else (18 if own==0 else 9)):
                for dx in range(-r,r+1):
                    for dy in range(-r,r+1):
                        if max(abs(dx),abs(dy))!=r: continue
                        setpos(i,px+dx*32,py+dy*32); es=run()
                        if len(es)<len(errs) and not any(x[1]==uid and (x[2],x[3])==((px+dx*32)//32,(py+dy*32)//32) for x in es):
                            errs=es; ok=True; moved+=1; break
                    if ok: break
                if ok: break
            if not ok: setpos(i,px,py)
    # deterministic last resort: drop expendable enemy filler (static defence, creep, pylons) that still collides
    DROP={144,146,124,125,162,156,176,177,178}; dropped=0
    for _ in range(40):
        cand=[e for e in errs if e[1] in DROP and e[4]!=0 and (e[0]=='overlap' or e[1] not in (176,177,178)) and e[0]!='unreachable_location']
        cand+=[e for e in errs if e[0]=='no_creep' and e[4] not in (0,11) and e[1] in (136,137,138,139,140,141,142,135,134)]
        if not cand: break
        i=idx_of(sorted(cand)[0])
        if i is None: break
        m.units.pop(i); dropped+=1; errs=run()
    if dropped: log(f'  autofix: dropped {dropped} colliding enemy filler buildings')
    c=collections.Counter(e[0] for e in errs)
    log(f'  autofix: moved {moved}, added {added} creep/pylon, violations {base} -> {len(errs)} {dict(c)}')
    return errs
