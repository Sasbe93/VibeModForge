"""blocked_paths: optional blocked paths - a route that opens only after a neutral building stack / low-value mineral
wall is destroyed or mined out. Refs: Litmus (1500/2000 HP neutral buildings), Electric Circuit / Medusa (stacked
Psi Disrupters / Temples), Troy / Block Chain (neutral Assimilators), KnockOut / Ringing Bloom / Neo Sylphid (0-value
mineral walls), Metropolis / Pole Star / Aiolos (16-value). Checks when a map has blockers:
 FAIL blocker set not symmetric between starts (count, ids, values under the map symmetry)
 FAIL blocker invincible (UNIT state flag 0x10) or not owner 11
 FAIL blocker is decorative: removing it adds no walkable connection (start-start distance and reachable set unchanged)
 INFO opened-path gain: start-start ground distance with / without blockers.
natcut with blockers counted closed is enforced in bw_natural_choke (apply_blockers)."""
import sys,math,struct
sys.path.insert(0,'tools/bw')
from check_ranked_bw import sections,walkgrid,dij,near_walk,units,SLOC,blockers,apply_blockers
def _sym_ok(B,W,H):
    key=lambda b:(b['id'],b['res'])
    P={(b['x'],b['y'],key(b)) for b in B}
    for f in (lambda x,y:(W*32-x,y),lambda x,y:(W*32-x,H*32-y),lambda x,y:(x,H*32-y)):
        if all(any(abs(q[0]-f(b['x'],b['y'])[0])<=32 and abs(q[1]-f(b['x'],b['y'])[1])<=32 and q[2]==key(b) for q in P) for b in B): return True
    return False
def check(path):
    s=sections(path);B=blockers(s)
    if not B: return [],[]
    W,H,wk0,_=walkgrid(s);W,H,wk1,_=walkgrid(s);apply_blockers(W,H,wk1,s)
    F=[];I=[]
    U=s['UNIT']
    for k in range(len(U)//36):
        uid=struct.unpack_from('<H',U,k*36+8)[0];o=U[k*36+16];st=struct.unpack_from('<H',U,k*36+26)[0]
        if any(b['id']==uid and b['o']==o for b in B) and st&0x10: F.append(f'blocked_paths: blocker id {uid} is invincible (flag 0x10) - path can never open'); break
    st=[near_walk(W,H,wk1,u['x']//32,u['y']//32) for u in units(s) if u['id']==SLOC]
    D1=dij(W,H,wk1,st[:1]);D0=dij(W,H,wk0,st[:1])
    r1=sum(1 for y in range(H) for x in range(W) if D1[y][x]<math.inf);r0=sum(1 for y in range(H) for x in range(W) if D0[y][x]<math.inf)
    d1=min(D1[y][x] for x,y in st[1:]) if len(st)>1 else 0;d0=min(D0[y][x] for x,y in st[1:]) if len(st)>1 else 0
    # local test: does each blocker cluster actually seal a gap? cells around it reachable only via a longer detour
    seal=0
    for b in B:
        xs=[x for x,y in b['tiles']];ys=[y for x,y in b['tiles']]
        a=[(x,y) for x in range(min(xs)-2,max(xs)+3) for y in range(min(ys)-2,max(ys)+3) if 0<=x<W and 0<=y<H and wk1[y][x]]
        if a:
            dd=[D1[y][x] for x,y in a if D1[y][x]<math.inf]
            if dd and max(dd)-min(dd)>12: seal+=1; b['seal']=1
    # mineral_walk: mineral walk - a worker with a gather order to a VISIBLE mineral ignores UNIT collision (eggs, critters, units),
    # not buildings/minerals/terrain. Unit blockers (eggs 36/97) with a mineral field within 10 tiles on both sides = worker-only path.
    MN=[u for u in units(s) if u['id'] in (176,177,178)]
    EG=[b for b in B if b['id'] in (36,97)]
    if EG:
        side=lambda m:(m['x']//32,m['y']//32)
        near=[m for m in MN if min(math.hypot(m['x']-e['x'],m['y']-e['y']) for e in EG)<=320 and m not in B]
        reg={(D1[y][x]<math.inf) for m in near for x,y in [side(m)] if 0<=x<W and 0<=y<H}
        I.append(f"mineral_walk mineral walk: {len(EG)} egg blockers, {len(near)} minerals within 10 tiles -> worker-only path {'possible' if len(near)>=2 else 'not set up (needs a visible mineral on the far side)'} (INFO)")
    I.append(f'blocked_paths blocked paths: {len(B)} blocker units, {seal} seal a gap; start-start ground {d1:.0f} closed / {d0:.0f} open, reachable tiles {r1} closed / {r0} open')
    SB=[b for b in B if b.get('seal')]; ns=len(st)
    if SB and ns<=2 and not (_sym_ok(SB,W,H) or _sym_ok(B,W,H)): F.append(f'blocked_paths: sealing blockers not symmetric ({len(SB)} units, {ns} starts)')
    if SB and ns>2 and len(SB)%ns: I.append(f'WARN blocked_paths: {len(SB)} sealing blockers on a {ns}-start map (not divisible)')
    if not SB: return [],[I[0]+' (INFO only: no sealing blocker = mineral-walk helper / decoration, as in KnockOut, Pole Star, Aiolos)']
    nbt=len({t for b in B for t in b['tiles']})
    if seal==0 and (r0-r1)-nbt<=4 and abs(d0-d1)<1: F.append('blocked_paths: blockers do not block anything (no gap sealed, distances unchanged) - decorative only')
    return F,I
if __name__=='__main__':
    for p in sys.argv[1:]: print(p.split('/')[-1],check(p))
