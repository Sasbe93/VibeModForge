#!/usr/bin/env python3
"""check_ranked_bw: symmetry/balance checks for BW melee (ranked) maps (.scx/.scm).
FAIL: walk-grid symmetry < 97% (ref_calibration: real ladder maps 97.5-99.98%; <99% = WARN), resource layout not symmetric, a start unreachable, rush distances / nearest-base
distances / resource totals per start differ > 3%, main-exit bottleneck widths differ > 2 tiles (metric step is 2 tiles; 2 = WARN, BW cliff faces), hall gap rule broken,
core tech missing (incl. Lurker needs Burrow, core_tech), not a melee setup (start locations = human slots).
Usage: check_ranked_bw.py MAP.scx [--json out.json]"""
import sys,struct,math,json,heapq,collections
sys.path.insert(0,'tools/bw'); sys.path.insert(0,'tools/lib/bw')
from eudplib.bindings._rust import mpqapi
import hall_gap, core_tech
TS=['badlands','platform','install','ashworld','jungle','desert','ice','twilight']
TD='tools/lib/bw/tileset'
MIN={176,177,178}; GAS={188}; SLOC=214
VF4={'badlands':'tools/lib/bw/tileset/badlands.vf4'}
SZ={176:(2,1),177:(2,1),178:(2,1),188:(4,2),214:(4,3)}
def sections(path):
    m=mpqapi.MPQ.open(path); d=bytes(m.extract_file('staredit\\scenario.chk')); s={}; i=0
    while i<len(d):
        k=d[i:i+4].decode('latin1'); n=struct.unpack_from('<i',d,i+4)[0]
        if n<0: i+=8+n; continue
        b=d[i+8:i+8+n]
        if k=='MTXM' and k in s: b=b+s[k][len(b):]   # ref_calibration: protected ladder maps split MTXM; later sections overlay earlier ones
        s[k]=b; i+=8+n
    if 'DIM ' in s and 'MTXM' in s:
        W,H=struct.unpack('<HH',s['DIM ']); s['MTXM']=s['MTXM'][:W*H*2].ljust(W*H*2,b'\0')
    return s
def walkgrid(s):
    W,H=struct.unpack('<HH',s['DIM ']); ts=struct.unpack('<H',s['ERA '])[0]%8
    cv5=open(f'{TD}/{TS[ts]}.cv5','rb').read(); mt=struct.unpack(f'<{W*H}H',s['MTXM'])
    wk=[[False]*W for _ in range(H)]; lvl=[[0]*W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            g=mt[y*W+x]>>4; g=g if g*52+52<=len(cv5) else 0
            f=struct.unpack_from('<H',cv5,g*52+2)[0]; wk[y][x]=not f&4; lvl[y][x]=(f>>9)&3
    VF=VF4.get(TS[ts])
    if VF:   # minitile walk data available: a tile is walkable when its cv5 flag says so AND >= 8 of its 16 minitiles are (conservative; cliff tiles never leak high<->low)
        vf=open(VF,'rb').read(); n=len(vf)//32; vc=open(VF[:-4]+'.cv5','rb').read()   # matching (older) cv5 of the vf4 set
        for y in range(H):
            for x in range(W):
                v=mt[y*W+x]; g=v>>4
                if g*52+52>len(vc): continue   # groups newer than the vf4 set: keep cv5 tile flag
                mg=struct.unpack_from('<H',vc,g*52+20+(v&15)*2)[0]
                if mg<n: wk[y][x]=wk[y][x] and sum(struct.unpack_from('<16H',vf,mg*32)[i]&1 for i in range(16))>=8
    walkgrid.minitile=bool(VF)
    return W,H,wk,lvl
# blocked_paths: path blockers = neutral low-value mineral walls (res<=48) and neutral non-resource buildings (ids below).
BLOCKER_IDS={174:(7,4),175:(13,6),190:(5,3),168:(4,3),200:(4,3),201:(4,3),127:(4,3),147:(10,7),151:(3,2),157:(4,2),149:(4,2),110:(4,2),36:(1,1),97:(1,1),173:(4,3),183:(4,3),189:(4,3)}
def blockers(s):
    out=[];UU=units(s);GB={(u['x'],u['y']) for u in UU if u['id'] in (157,149,110) and u['o']==11}
    for u in UU:
        if u['o']!=11: continue
        if u['id']==188 and (u['x'],u['y']) in GB: w,h=4,2   # battlefield_cover: geyser under a neutral gas building = choke blocker (stays after the building dies)
        elif u['id'] in (176,177,178) and u['res']<=48: w,h=2,1
        elif u['id']==188: continue
        elif u['id'] in BLOCKER_IDS: w,h=BLOCKER_IDS[u['id']]
        else: continue
        x0=(u['x']-w*16)//32; y0=(u['y']-h*16)//32
        out.append(dict(u,tiles=[(x0+i,y0+j) for i in range(w) for j in range(h)]))
    return out
def apply_blockers(W,H,wk,s):
    B=blockers(s)
    for b in B:
        for x,y in b['tiles']:
            if 0<=x<W and 0<=y<H: wk[y][x]=False
    return B
def units(s):
    U=s['UNIT']; out=[]
    for k in range(len(U)//36):
        _,x,y,uid=struct.unpack_from('<IHHH',U,k*36); o=U[k*36+16]; res=struct.unpack_from('<I',U,k*36+20)[0]
        out.append(dict(id=uid,x=x,y=y,o=o,res=res))
    return out
def dij(W,H,wk,src):
    D=[[math.inf]*W for _ in range(H)]; pq=[]
    for x,y in src: D[y][x]=0; pq.append((0,x,y))
    heapq.heapify(pq)
    while pq:
        d,x,y=heapq.heappop(pq)
        if d>D[y][x]: continue
        for dx,dy,c in ((1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,1.414),(1,-1,1.414),(-1,1,1.414),(-1,-1,1.414)):
            X,Y=x+dx,y+dy
            if 0<=X<W and 0<=Y<H and wk[Y][X] and (dx==0 or dy==0 or (wk[y][X] and wk[Y][x])):
                if d+c<D[Y][X]: D[Y][X]=d+c; heapq.heappush(pq,(d+c,X,Y))
    return D
def near_walk(W,H,wk,x,y):
    for r in range(0,8):
        for dy in range(-r,r+1):
            for dx in range(-r,r+1):
                X,Y=x+dx,y+dy
                if 0<=X<W and 0<=Y<H and wk[Y][X]: return X,Y
def run(path):
    s=sections(path); W,H,wk0,lvl=walkgrid(s); U=units(s); F=[]; I=[]
    ownr=s['OWNR']; humans=[p for p in range(8) if ownr[p]==6]
    starts={u['o']:(u['x']//32,u['y']//32) for u in U if u['id']==SLOC}
    if sorted(starts)!=humans: F.append(f'start locations {sorted(starts)} != human slots {humans}')
    N=len(starts); I.append(f'map {W}x{H}, players {N}')
    # 1 symmetry of the walk grid (best of the standard groups)
    ops={'rot180':lambda x,y:(W-1-x,H-1-y),'mirrorX':lambda x,y:(W-1-x,y),'mirrorY':lambda x,y:(x,H-1-y)}
    if W==H: ops.update({'rot90':lambda x,y:(W-1-y,x),'diag':lambda x,y:(y,x)})
    def m1(f,x,y):
        X,Y=f(x,y); v=wk0[y][x]
        return any(wk0[Y+b][X+a]==v for a in (-1,0,1) for b in (-1,0,1) if 0<=X+a<W and 0<=Y+b<H)
    # BW cliffs are not rotation-symmetric (south faces are taller), so exact tiles differ ~5% at cliff edges:
    # score = share of tiles whose image has the same walkability within 1 tile (exact score reported as info)
    sc={k:sum(m1(f,x,y) for y in range(H) for x in range(W))/(W*H) for k,f in ops.items()}
    ex={k:sum(wk0[y][x]==wk0[f(x,y)[1]][f(x,y)[0]] for y in range(H) for x in range(W))/(W*H) for k,f in ops.items()}
    I.append('exact-tile walk symmetry (info, cliff faces differ): '+', '.join(f'{k} {v*100:.1f}%' for k,v in ex.items()))
    best=max(sc,key=sc.get); I.append('walk symmetry: '+', '.join(f'{k} {v*100:.2f}%' for k,v in sc.items()))
    # resources symmetric under the start permutation: every resource has an image of equal amount
    def ctr(u): w,h=SZ.get(u['id'],(1,1)); return (u['x'],u['y'])
    BLK=[u for u in U if u['id'] in MIN and u['res']<=50]   # path-blocker minerals (backdoors, curved_mineral_arcs 'mineral-blocked'): obstacles, not income
    R=[u for u in U if u['id'] in MIN|GAS and not (u['id'] in MIN and u['res']<=50)]
    if BLK: I.append(f'{len(BLK)} blocker minerals (value <= 50) treated as obstacles, not bases')
    good=[k for k,f in ops.items() if sc[k]>=0.97]   # ref_calibration calibrated (FS 97.5, Polypoid 98.4)
    resym=[]; TOL=32   # ref_calibration: real maps place resources within 1 tile of the image, not pixel-exact
    for k in good:
        f=ops[k]; ok=True
        for u in R:
            tx,ty=f(u['x']/32-0.5,u['y']/32-0.5); px,py=(tx+0.5)*32,(ty+0.5)*32   # = pixel mirror W*32-x / H*32-y
            if not any(v['id']==u['id'] and v['res']==u['res'] and abs(v['x']-px)<=TOL and abs(v['y']-py)<=TOL for v in R): ok=False; break
        if ok: resym.append(k)
    I.append(f'resource layout symmetric under: {resym or "NONE"}')
    if not good: F.append(f'walk grid symmetry {sc[best]*100:.2f}% < 97%')
    elif sc[best]<0.99: I.append(f'WARN walk symmetry {sc[best]*100:.2f}% < 99% (ok per ref_calibration reference range 97.5-99.98%)')
    if not resym: F.append('resource layout (positions+amounts) not symmetric under any standard symmetry')
    # walk grid with resources blocked
    wk=[r[:] for r in wk0]
    for u in R+BLK:
        w,h=SZ[u['id']]; x0,y0=u['x']//32-w//2,u['y']//32-h//2
        for yy in range(y0,y0+h):
            for xx in range(x0,x0+w):
                if 0<=xx<W and 0<=yy<H: wk[yy][xx]=False
    SP={u['o']:(u['x'],u['y']) for u in U if u['id']==SLOC}
    def ring(px,py,r=48):   # walkable tiles whose centre lies within r px of a pixel point (symmetric by construction)
        return [(x,y) for y in range(max(0,py//32-4),min(H,py//32+5)) for x in range(max(0,px//32-4),min(W,px//32+5))
                if wk[y][x] and abs(x*32+16-px)<=r and abs(y*32+16-py)<=r]
    def hallring(px,py):     # tiles just outside a 4x3 hall footprint centred on (px,py)
        return [(x,y) for y in range(H) for x in range(W) if wk[y][x] and -80<=x*32+16-px<=80 and -64<=y*32+16-py<=64
                and not(-64<x*32+16-px<64 and -48<y*32+16-py<48)]
    SRC={p:hallring(*SP[p]) for p in SP}
    for p in SRC:
        if not SRC[p]: F.append(f'P{p+1} start has no walkable tile around the hall footprint')
    S={p:min(SRC[p],key=lambda t:(abs(t[0]*32+16-SP[p][0])+abs(t[1]*32+16-SP[p][1]))) for p in SRC}
    D={p:dij(W,H,wk,SRC[p]) for p in S}
    def dist(p,tiles): return min((D[p][y][x] for x,y in tiles),default=math.inf)
    # 2 reachability + rush distance
    rush={}
    for p in S:
        for q in S:
            if p<q:
                d=dist(p,SRC[q])
                if d==math.inf: F.append(f'P{p+1} cannot reach P{q+1} by ground')
                rush[(p,q)]=d
    I.append('rush distances (tiles, ground path start->start): '+', '.join(f'P{p+1}-P{q+1} {d:.1f}' for (p,q),d in rush.items()))
    nearest={p:min(rush[tuple(sorted((p,q)))] for q in S if q!=p) for p in S}
    I.append('nearest opponent per start: '+', '.join(f'P{p+1} {d:.1f}' for p,d in nearest.items()))
    if max(nearest.values())>min(nearest.values())*1.03: F.append('nearest-opponent rush distance differs >3% between starts')
    # 3 bases: cluster resources, owner by path distance
    cl=[]
    for u in R:
        for c in cl:
            if any(abs(u['x']-v['x'])<=12*32 and abs(u['y']-v['y'])<=12*32 for v in c): c.append(u); break
        else: cl.append([u])
    bases=[]
    for c in cl:
        px=sum(u['x'] for u in c)/len(c); py=sum(u['y'] for u in c)/len(c); cx,cy=int(px//32),int(py//32)
        tg=[]; r=48
        while not tg and r<400: tg=ring(int(px),int(py),r); r+=32
        d={p:dist(p,tg) for p in S}
        bases.append(dict(c=(cx,cy),m=sum(u['res'] for u in c if u['id'] in MIN),g=sum(u['res'] for u in c if u['id'] in GAS),
                          nm=sum(1 for u in c if u['id'] in MIN),ng=sum(1 for u in c if u['id'] in GAS),d=d))
    tot={p:[0,0] for p in S}; order={p:[] for p in S}
    for b in bases:
        dm=min(b['d'].values()); win=[p for p in S if b['d'][p]<=dm*1.03+0.5]
        for p in win: tot[p][0]+=b['m']/len(win); tot[p][1]+=b['g']/len(win)
        for p in S: order[p].append((round(b['d'][p],1),b['nm'],b['ng'],b['m']))
        if b['d'][win[0]]==math.inf: I.append(f'island base at {b["c"]} (no ground path from any start; air/drop only - fairness via symmetric images)')
    I.append(f'{len(bases)} bases (resource clusters)')
    for p in S:
        I.append(f'P{p+1} share: minerals {tot[p][0]:.0f} gas {tot[p][1]:.0f}; bases by distance: '+'; '.join(f'{d}t {nm}M{ng}G' for d,nm,ng,_ in sorted(order[p])[:5]))
    for k in (0,1):
        v=[tot[p][k] for p in S]
        if max(v)>min(v)*1.01+1: F.append(f'{"mineral" if k==0 else "gas"} share per start differs >1%: {v}')
    # nearest bases sequence equal (main, natural, third distances within 3%)
    seqs=[sorted(order[p])[:3] for p in S]
    for i in range(3):
        ds=[sq[i][0] for sq in seqs]
        if max(ds)>min(ds)*1.03+1: F.append(f'base #{i+1} distance differs between starts: {ds}')
        if len({(sq[i][1],sq[i][2],sq[i][3]) for sq in seqs})>1: F.append(f'base #{i+1} resources differ between starts')
    # ref_calibration reference ranges (12 nydus ladder maps, measured): main 9x1500 + 1x5000 gas, mineral centres 5.8-7.3 tiles
    # from the start, natural (7-8 fields) at 24-37 tiles path, third at 40-75, 1v1 rush 148-192, 4p nearest 113-145
    for p in S:
        sq=sorted(order[p])
        if len(sq)>1 and not (22<=sq[1][0]<=40): I.append(f'WARN P{p+1} natural at {sq[1][0]} tiles (reference 24-37)')
        if len(sq)>2 and sq[2][0]>75: I.append(f'WARN P{p+1} third base at {sq[2][0]} tiles (reference 40-75; ref_calibration)')
    rn=min(nearest.values()) if nearest else 0
    if N==2 and not 130<=rn<=200: I.append(f'WARN 1v1 rush {rn:.0f} tiles outside reference 148-192 (ref_calibration)')
    if N==4 and not 105<=rn<=150: I.append(f'WARN 4p nearest rush {rn:.0f} outside reference 113-145 (ref_calibration)')
    for u in [u for u in U if u['id']==SLOC]:
        mm=[v for v in R if v['id'] in MIN and math.hypot(v['x']-u['x'],v['y']-u['y'])<12*32 and v['res']>=500]
        gg=[v for v in R if v['id'] in GAS and math.hypot(v['x']-u['x'],v['y']-u['y'])<12*32]
        if not (8<=len(mm)<=10) or len(gg)!=1: I.append(f'WARN P{u["o"]+1} main has {len(mm)} mineral fields/{len(gg)} geysers (reference 9/1)')
    # 4 main-exit choke: min clearance along the path from start toward the map centre, beyond 6 tiles from start
    import collections as co
    cd=[[0]*W for _ in range(H)]; q=co.deque()
    for y in range(H):
        for x in range(W):
            if not wk0[y][x]: q.append((x,y)); cd[y][x]=0
            else: cd[y][x]=10**6
    while q:
        x,y=q.popleft()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            X,Y=x+dx,y+dy
            if 0<=X<W and 0<=Y<H and cd[Y][X]>cd[y][x]+1: cd[Y][X]=cd[y][x]+1; q.append((X,Y))
    def widest(src,goal):   # max over paths of the min clearance (bottleneck width) - unique, tie-free
        best={t:cd[t[1]][t[0]] for t in src}; pq=[(-v,t) for t,v in best.items()]; heapq.heapify(pq); done=set()
        while pq:
            v,(x,y)=heapq.heappop(pq); v=-v
            if (x,y) in done: continue
            done.add((x,y))
            if goal(x,y): return v
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                X,Y=x+dx,y+dy
                if 0<=X<W and 0<=Y<H and wk[Y][X] and (X,Y) not in done:
                    nv=min(v,cd[Y][X])
                    if nv>best.get((X,Y),-1): best[(X,Y)]=nv; heapq.heappush(pq,(-nv,(X,Y)))
        return 0
    chokes={p:2*widest(SRC[p],lambda x,y,p=p:D[p][y][x]>=30)-1 for p in S}
    I.append('main-exit bottleneck width (widest path out to 30 tiles, tiles): '+', '.join(f'P{p+1} {w}' for p,w in chokes.items()))
    dch=max(chokes.values())-min(chokes.values())
    if dch>2: F.append('main-exit bottleneck widths differ >2 tiles')
    elif dch==2: I.append('WARN main-exit bottleneck differs by one metric step (2 tiles) - BW cliff-face asymmetry; check in-game, all >=3 wide')
    # 5 hall gaps (start locations as halls)
    bad,out=hall_gap.check([dict(id=u['id'],x=u['x'],y=u['y']) for u in U])
    I+=['hall gap: '+o for o in out]; F+=['hall gap: '+b for b in bad]
    # 6 tech
    ct=core_tech.check(s); F+=['core tech: '+x for x in ct]
    I.append('core tech (incl. Lurker->Burrow, core_tech): '+('OK' if not ct else f'{len(ct)} problems'))
    # no_empty_areas: no large empty areas
    import empty_area_bw
    es,at=empty_area_bw.empty_square(path)
    cen=at and at[0]<=W//2<at[0]+es and at[1]<=H//2<at[1]+es
    I.append(f'largest empty square (no_empty_areas): {es}x{es} tiles at {at} (ladder 4-15; Octagon central arena 30)')
    if es>16 and not cen: F.append(f'no_empty_areas: empty area {es}x{es} tiles at {at} > 16x16 (needs structure: height, tar/water, doodads, tile variety, expansion)')
    elif es>16: I.append(f'WARN no_empty_areas: {es}x{es} empty square covers the map centre (accepted only as a deliberate central arena, cf. Octagon)')
    elif es>12: I.append(f'WARN no_empty_areas: empty square {es}x{es} > 12x12 tiles')
    # curved_mineral_arcs: mineral lines never straight; exactly one path main->natural; enough bases
    SL=[(u['x']/32,u['y']/32) for u in U if u['id']==SLOC]; HALLS=[]
    for c,b in zip(cl,bases):
        mm=[(u['x']/32,u['y']/32) for u in c if u['id'] in MIN and u['res']>=100]
        if len(mm)<4: continue
        mx=sum(a for a,_ in mm)/len(mm); my=sum(b_ for _,b_ in mm)/len(mm)
        sxx=sum((a-mx)**2 for a,_ in mm); syy=sum((b_-my)**2 for _,b_ in mm); sxy=sum((a-mx)*(b_-my) for a,b_ in mm)
        th=0.5*math.atan2(2*sxy,sxx-syy); nx,ny=-math.sin(th),math.cos(th)
        dev=max(abs((a-mx)*nx+(b_-my)*ny) for a,b_ in mm)
        hs=[h for h in SL if math.hypot(h[0]-mx,h[1]-my)<10]
        if hs: hx,hy=hs[0]
        else:   # expected hall: walkable 4x3 spot ~6.5 tiles from fields, >=3 tiles clear
            best=None
            for yy in range(int(my)-10,int(my)+11):
                for xx in range(int(mx)-10,int(mx)+11):
                    if not all(0<=xx+a<W and 0<=yy+b_<H and wk[yy+b_][xx+a] for a in (-2,-1,0,1) for b_ in (-1,0,1)): continue
                    ds=[math.hypot(a-xx,b_-yy) for a,b_ in mm]
                    if min(ds)<3: continue
                    sc_=sum((d-6.3)**2 for d in ds)
                    if best is None or sc_<best[0]: best=(sc_,xx,yy)
            if not best: continue
            _,hx,hy=best
        HALLS.append((c,hx,hy))
        ang=sorted(math.degrees(math.atan2(b_-hy,a-hx))%360 for a,b_ in mm)
        gaps=[(ang[(i+1)%len(ang)]-ang[i])%360 for i in range(len(ang))]; span=360-max(gaps)
        rr=[math.hypot(a-hx,b_-hy) for a,b_ in mm]
        tx_,ty_=math.cos(th),math.sin(th)
        sl=sorted(mm,key=lambda q:(q[0]-mx)*tx_+(q[1]-my)*ty_); off=[(a-mx)*nx+(b_-my)*ny for a,b_ in sl]
        zz=sum(abs(off[i+1]-off[i])>=0.5 for i in range(len(off)-1))/(len(off)-1)
        I.append(f'curved_mineral_arcs mineral line at {b["c"]}: deviation {dev:.1f} t, stagger {zz:.2f}, arc {span:.0f} deg, hall dist {min(rr):.1f}-{max(rr):.1f}')
        # calibrated on ladder refs (curved_mineral_arcs): real lines zigzag (stagger >= 0.5) or curve; arc 45-102 deg
        if zz<0.35 and dev<1.5: F.append(f'curved_mineral_arcs: mineral line at {b["c"]} is straight (stagger {zz:.2f} < 0.35, deviation {dev:.1f})')
        if span<35: F.append(f'curved_mineral_arcs: mineral line at {b["c"]} covers only {span:.0f} deg around the hall (< 35)')
        elif span<60: I.append(f'WARN curved_mineral_arcs: mineral arc at {b["c"]} {span:.0f} deg < 60')
    def mincut(p,nat):   # curved_mineral_arcs: vertex max-flow main -> natural hall area; cut tiles = the main exit(s)
        Dn=dij(W,H,wk,[near_walk(W,H,wk,*nat['c'])] if near_walk(W,H,wk,*nat['c']) else [])
        src={(x,y) for y in range(H) for x in range(W) if D[p][y][x]<=8}
        snk={(x,y) for y in range(H) for x in range(W) if Dn[y][x]<=6}
        if src&snk or not snk: return None
        NB=((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1))
        def nbr(x,y):
            for dx,dy in NB:
                X,Y=x+dx,y+dy
                if 0<=X<W and 0<=Y<H and wk[Y][X] and (dx==0 or dy==0 or (wk[y][X] and wk[Y][x])): yield (X,Y)
        flow=collections.defaultdict(int)   # edges: ('i',t)->('o',t) cap1 ; ('o',t)->('i',u) cap inf
        def cap(a,b):
            if a[0]=='i' and b[0]=='o' and a[1]==b[1]: c=10**6 if a[1] in src or a[1] in snk else 1
            elif a[0]=='o' and b[0]=='i': c=10**6
            else: c=0
            return c-flow[(a,b)]+flow[(b,a)]*0 if c else flow[(b,a)]
        def adj(n):
            k,t=n
            if k=='i': yield ('o',t)
            else:
                for u in nbr(*t): yield ('i',u)
            if k=='o': yield ('i',t)
            else:
                for u in nbr(*t): yield ('o',u)
        def res(a,b):
            c=0
            if a[0]=='i' and b[0]=='o' and a[1]==b[1]: c=10**6 if (a[1] in src or a[1] in snk) else 1
            elif a[0]=='o' and b[0]=='i' and a[1]!=b[1]: c=10**6
            return c-flow[(a,b)]+flow[(b,a)]
        S0=[('i',t) for t in src]; total=0
        while total<40:
            par={n:None for n in S0}; q=collections.deque(S0); hit=None
            while q and not hit:
                n=q.popleft()
                for m_ in adj(n):
                    if m_ not in par and res(n,m_)>0:
                        par[m_]=n
                        if m_[0]=='o' and m_[1] in snk: hit=m_; break
                        q.append(m_)
            if not hit: break
            n=hit
            while par[n] is not None:
                a_=par[n]
                if flow[(n,a_)]>0: flow[(n,a_)]-=1
                else: flow[(a_,n)]+=1
                n=a_
            total+=1
        seen=set(par)
        cut=[t for (k,t) in seen if k=='i' and ('o',t) not in seen]
        return total,cut
    for p in S:
        sq=sorted(((b['d'][p],id(b),b) for b in bases))
        if len(sq)<2: continue
        r_=mincut(p,sq[1][2])
        if not r_: I.append(f'WARN curved_mineral_arcs P{p+1}: natural too close to the main to measure the exit'); continue
        tot_,cut=r_; cs=set(cut); seen=set(); grp=0
        for c0 in cut:
            if c0 in seen: continue
            grp+=1; st=[c0]; seen.add(c0)
            while st:
                x,y=st.pop()
                for dx in (-2,-1,0,1,2):
                    for dy in (-2,-1,0,1,2):
                        n=(x+dx,y+dy)
                        if n in cs and n not in seen: seen.add(n); st.append(n)
        I.append(f'curved_mineral_arcs P{p+1} main->natural min cut {tot_} tiles in {grp} separate exit(s)')
        if grp>1: F.append(f'curved_mineral_arcs: P{p+1} has {grp} separate free paths main->natural (must be exactly one)')
    need=5 if N==2 else 4; cnt={p:0.0 for p in S}
    for b in bases:
        dm=min(b['d'].values()); win=[p for p in S if b['d'][p]<=dm*1.03+0.5]
        for p in win: cnt[p]+=1
    I.append('curved_mineral_arcs bases per player (nearest by path, ties count for each): '+', '.join(f'P{p+1} {v:.1f}' for p,v in cnt.items()))
    if N<=4:
        if len(bases)/N<need-0.25: F.append(f'curved_mineral_arcs: {len(bases)} bases for {N} players = {len(bases)/N:.1f} per player < {need} (incl. main)')
        for p,v in cnt.items():
            if v<need: I.append(f'WARN curved_mineral_arcs: P{p+1} nearest-base count {v:.0f} < {need}')
    I.append('walkability source: '+('minitile (vf4)' if getattr(walkgrid,'minitile',False) else 'tile flags (cv5) - ramps approximate'))
    # geyser_back_wall: every mineral field / geyser has its back to an obstacle (<=3 walkable tiles behind it)
    def blocked(x,y): return not(0<=x<W and 0<=y<H) or not wk0[y][x]
    for c,hx,hy in HALLS:
        ok=0; tot=0; bad=[]
        for u in c:
            if u['id'] in MIN and u['res']<100: continue
            w,h=SZ[u['id']]; ux,uy=u['x']/32,u['y']/32; dx,dy=ux-hx,uy-hy; L=math.hypot(dx,dy) or 1; dx/=L; dy/=L
            half=abs(dx)*w/2+abs(dy)*h/2   # distance from centre to footprint edge along the ray
            hit=False
            for da in (0,-0.45,0.45):   # cone: obstacle may sit slightly beside the hall->field ray (calibrated on refs)
                ex,ey=dx*math.cos(da)-dy*math.sin(da),dx*math.sin(da)+dy*math.cos(da); k=0.0
                while k<=3.5 and not hit:
                    if blocked(math.floor(ux+ex*(half+k+0.25)),math.floor(uy+ey*(half+k+0.25))): hit=True
                    k+=0.5
            tot+=1; ok+=hit
            if not hit: bad.append(f'{int(ux)},{int(uy)}')
        I.append(f'geyser_back_wall cluster at ({int(hx)},{int(hy)}): {ok}/{tot} resources backed by an obstacle within 3 tiles')
        if tot and ok/tot<0.7: F.append(f'geyser_back_wall: base at ({int(hx)},{int(hy)}) has open ground behind {tot-ok}/{tot} resources ({" ".join(bad[:6])})')
    # ranked_layout_rules: every reachable ~16x16 zone needs a gameplay purpose
    reach=[[wk[y][x] and any(D[p][y][x]<math.inf for p in S) for x in range(W)] for y in range(H)]
    halltiles=[(int(hx),int(hy)) for _,hx,hy in HALLS]
    HD={}
    for t in halltiles:
        src=[(x,y) for y in range(t[1]-3,t[1]+4) for x in range(t[0]-4,t[0]+5) if 0<=x<W and 0<=y<H and reach[y][x]]
        if src: HD[t]=dij(W,H,wk,src)
    keys=list(HD); route=[[False]*W for _ in range(H)]
    for i in range(len(keys)):
        for j in range(i+1,len(keys)):
            A,B=HD[keys[i]],HD[keys[j]]; d=A[keys[j][1]][keys[j][0]]
            if d==math.inf: continue
            for y in range(H):
                for x in range(W):
                    if reach[y][x] and A[y][x]+B[y][x]<=d*1.12+2: route[y][x]=True
    neut=[(u['x']//32,u['y']//32) for u in U if u['o']==11 and u['id'] not in MIN|GAS and u['id']!=SLOC]
    Z=16; dead=[]
    for zy in range(0,H,Z):
        for zx in range(0,W,Z):
            T=[(x,y) for y in range(zy,min(H,zy+Z)) for x in range(zx,min(W,zx+Z)) if reach[y][x]]
            if len(T)<40: continue
            why=[]
            if any(zx-2<=u['x']//32<zx+Z+2 and zy-2<=u['y']//32<zy+Z+2 for u in R): why.append('base')
            if sum(route[y][x] for x,y in T)>=0.25*len(T) or sum(route[y][x] for x,y in T)>=40: why.append('route')
            if any(zx<=a<zx+Z and zy<=b<zy+Z for a,b in neut): why.append('neutral')
            lv=[lvl[y][x] for x,y in T]
            if max(lv)>min(lv) and any(lvl[y][x]==max(lv) for x,y in T if route[y][x] or True) and sum(1 for v in lv if v==max(lv))>=6 \
               and any(route[y][x] for x,y in T): why.append('vantage')
            if any(math.hypot(x-a/32,y-b/32)<14 for x,y in T[::7] for a,b in SP.values()) and not all(route[y][x] for x,y in T): why.append('drop/harass')
            if not why: dead.append(f'({zx}-{zx+Z-1},{zy}-{zy+Z-1}) {len(T)}t')
            elif why==['drop/harass'] and len(T)>=120 and not any(D[p][y][x]<=14 for p in S for x,y in T): dead.append(f'({zx}-{zx+Z-1},{zy}-{zy+Z-1}) {len(T)}t')
    I.append(f'ranked_layout_rules: {len(dead)} reachable zones without gameplay purpose'+(': '+' '.join(dead) if dead else ''))
    if dead: F.append(f'ranked_layout_rules: zones without purpose (base/route/vantage/neutral/drop): {" ".join(dead)} - make unwalkable or give a purpose')
    return F,I
if __name__=='__main__':
    F,I=run(sys.argv[1])
    import bw_base_levels   # base_elevation
    _f,_i=bw_base_levels.check(sys.argv[1]); F+=_f; I+=_i
    import check_map_design_bw as MDB   # general rules (reach, zone doodads, ramp size, mineral access, ScmDraft)
    MDB.run(sys.argv[1],I,F)
    import bw_edge_doodads   # edge_doodads
    _f,_i=bw_edge_doodads.check(sys.argv[1]); F+=_f; I+=_i
    import bw_natural, bw_resource_ground, bw_natural_choke, bw_main_space, bw_symmetric_blockers, bw_cliff_outlines, bw_reach, bw_zone_doodads, bw_blocked_paths   # natural_in_front, resource_footprint, natural_choke, main_space, symmetric_blockers, ragged_shore
    for _m in (bw_natural,bw_natural_choke,bw_main_space,bw_symmetric_blockers,bw_cliff_outlines,bw_blocked_paths):
        _f,_i=_m.check(sys.argv[1]); F+=[x.replace('FAIL ','',1) for x in _f]; I+=[x.replace('INFO ','',1) for x in _i]
    for x in I: print('INFO',x)
    for x in F: print('FAIL',x)
    print('RESULT', 'OK' if not F else f'FAIL ({len(F)})')
    if '--json' in sys.argv: json.dump(dict(fail=F,info=I),open(sys.argv[sys.argv.index('--json')+1],'w'),indent=1)
    sys.exit(1 if F else 0)
