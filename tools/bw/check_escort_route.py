#!/usr/bin/env python3
"""escort_route_challenge: an escort mission is a real escort. The escortee's route is long enough, crosses dangerous
ground, and the player can reach every threat on it.
   python3 tools/bw/check_escort_route.py MAP.scx [...]      (run from the repository root; exit 1 on FAIL)

Escort detection: an Order action (46) for a computer player that is allied with a human at some point (Set Alliance
Status Ally by a human-owned trigger, or an allied force with a human), whose destination location is used in a Bring
condition for that player (the "reach the exit" objective), or any such order when the design note has an ESCORT_ROUTE
line. Legs from a whole-map location (Anywhere) are stragglers and are not traced.
Route: every leg is pathfound over walkable terrain by tools/bw/path_tool.py (cv5/vf4 walk grid, neutral blockers
applied) from the source location centre to the destination; the route length is the sum of the legs. The same
tool also judges rescue, reach and survive objectives (check_objective_paths, predelivery check 51).
Rules (FAIL):
  1 route length >= map width / 3 tiles
  2 at least 2 threat encounters along the route. Threats: pre-placed armed units, towers and Bunkers of enemy players
    within THREAT_R tiles of the path, and ambush triggers (Create Unit for an enemy player at a location, or an Order
    sending enemy units to a location, within AMBUSH_R tiles of the path). Threats less than GAP path tiles apart
    count as one encounter.
  3 every encounter point on the path is reachable by the player's ground units from the player start without breaking
    through an enemy base (enemy building footprints block)
  4 the design note has 'ESCORT_ROUTE: <escortee> :: <length tiles/time> :: <threats with locations> :: <what the
    player must do>'
WARN: no routes PNG (*routes*.png) next to the map; an ESCORT_ROUTE line but no traceable escort order.
Not checked (design review): whether the escortee could survive alone."""
import sys,os,re,struct,math,glob,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from check_ranked_bw import sections,walkgrid,apply_blockers,units,dij,near_walk
from check_ally_vision import note_files
import path_tool as P
THREAT_R=P.THREAT_R; AMBUSH_R=P.AMBUSH_R; GAP=P.GAP
TOWERS={125,146,162}               # ground defence: Bunker, Sunken Colony, Photon Cannon (Missile Turret/Spore are anti-air)
WORKERS={7,41,64}; SLOC=214
DB=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','data','bw','tech','bw_weapons.json')))
GROUND_ARMED={int(k) for k,v in DB['units'].items() if v.get('ground') is not None}|{72,82,83,125}   # + Carrier, Reaver, Bunker
def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def u16(b,o): return struct.unpack_from('<H',b,o)[0]
def strings(S):
    b=S.get('STR ',b'\0\0'); n=u16(b,0)
    def g(j): o=u16(b,2*j); return b[o:b.index(b'\0',o)].decode('utf8','replace') if 0<j<=n else ''
    return g
def note(path):
    for f in note_files(path):
        for l in open(f,encoding='utf8',errors='replace'):
            m=re.search(r'ESCORT_ROUTE:\s*(.+?)\s*::\s*(.+?)\s*::\s*(.+?)\s*::\s*(\S.*)',l)
            if m: return m.groups()
    return None
def bsize(uid):
    try:
        import sclib; return sclib.BUILDSIZE.get(uid,(3,2))
    except Exception: return (3,2)
def run(path):
    S=sections(path); W,H,wk,_=walkgrid(S); apply_blockers(W,H,wk,S); st=strings(S)
    ownr=S['OWNR']; hum={p for p in range(8) if ownr[p]==6}; comp={p for p in range(8) if ownr[p]==5}
    fo=S.get('FORC',b'')+b'\0'*20; forces=list(fo[:8]); fflags=list(fo[16:20])
    MR=S.get('MRGN',b'')
    def rect(l): return struct.unpack_from('<IIII',MR,(l-1)*20) if 0<l<=len(MR)//20 else None
    def lname(l): return st(u16(MR,(l-1)*20+16)) if rect(l) else '?'
    def whole(l): r=rect(l); return not r or l==64 or (r[2]-r[0]>=W*32*0.6 and r[3]-r[1]>=H*32*0.6)
    def ltile(l): r=rect(l); return near_walk(W,H,wk,min(W-1,int((r[0]+r[2])/64)),min(H-1,int((r[1]+r[3])/64)))
    def grp(t,own=()):
        if 0<=t<8: return [t]
        if t==13: return list(own)
        if t==17: return list(range(8))
        if 18<=t<=21: return [p for p in range(8) if forces[p]==t-18]
        return []
    T=S.get('TRIG',b''); trigs=[]
    for t in range(0,len(T)-len(T)%2400,2400):
        r=T[t:t+2400]
        c=[r[i*20:i*20+20] for i in range(16) if r[i*20+15]]
        a=[r[320+i*32:352+i*32] for i in range(64) if r[320+i*32+26]]
        trigs.append((c,a,{o for q in range(28) if r[2372+q] for o in grp(q)}))
    allied=set()
    for f in range(4):
        mem={p for p in range(8) if forces[p]==f}
        if fflags[f]&2 and mem&hum: allied|=mem-hum
    for c,a,own in trigs:
        if own&hum:
            for x in a:
                if x[26]==57 and u16(x,24)>=1: allied|=set(grp(u32(x,16),own))-hum
    allied&=comp
    enemy=comp-allied
    brings={(p,u32(x,0)) for c,a,own in trigs for x in c if x[15]==3 for p in grp(u32(x,4),own)}
    N=note(path); legs={}
    for c,a,own in trigs:
        for x in a:
            if x[26]!=46: continue
            src,dst=u32(x,0),u32(x,20)
            for p in grp(u32(x,16),own):
                if p in allied and rect(src) and rect(dst) and not whole(src) and not whole(dst) and src!=dst and ((p,dst) in brings or N):
                    legs.setdefault(p,[]); (src,dst) in legs[p] or legs[p].append((src,dst))
    out=[]
    if not legs:
        if N: out.append(f"WARN escort_route_challenge: design note has ESCORT_ROUTE ({N[0]}) but no escort order (Order for an allied computer player to a location) was found to trace")
        return out or ['OK   escort_route_challenge: no escort in this map']
    U=units(S)
    # player reach grid: enemy buildings block
    pw=[row[:] for row in wk]
    for u in U:
        if u['o'] in enemy and u['id']>=106 and u['id'] not in (214,):
            w,h=bsize(u['id']); x0,y0=u['x']//32-w//2,u['y']//32-h//2
            for yy in range(max(0,y0),min(H,y0+h)):
                for xx in range(max(0,x0),min(W,x0+w)): pw[yy][xx]=False
    starts=[(u['x']//32,u['y']//32) for u in U if u['o'] in hum and u['id']==SLOC] or [(u['x']//32,u['y']//32) for u in U if u['o'] in hum]
    PD=dij(W,H,pw,[q for q in (near_walk(W,H,pw,x,y) for x,y in starts) if q])
    threats=[(u['x']/32,u['y']/32,u['id'],'unit') for u in U if u['o'] in enemy and (u['id'] in TOWERS or (u['id'] in GROUND_ARMED and u['id'] not in WORKERS and u['id']<106))]
    amb=[]
    for c,a,own in trigs:
        for x in a:
            if x[26] in (44,45) and any(p in enemy for p in grp(u32(x,16),own)) and rect(u32(x,0)): amb.append(u32(x,0))
            if x[26]==46 and any(p in enemy for p in grp(u32(x,16),own)) and rect(u32(x,20)) and not whole(u32(x,20)): amb.append(u32(x,20))
    F=[]; info=[]
    for p,L in legs.items():
        path_t=[]; length=0.0; broken=[]
        for src,dst in L:
            a_,b_=ltile(src),ltile(dst)
            if not a_ or not b_: broken.append(f'{lname(src)}->{lname(dst)}'); continue
            seg,L,_,_=P.pathfind(W,H,wk,a_,b_)
            if L==math.inf or not seg: broken.append(f'{lname(src)}->{lname(dst)} (no ground path)'); continue
            length+=L; path_t+=seg
        hits=[]
        for tx,ty,uid,kind in threats:
            d,i=min((math.hypot(tx-x,ty-y),i) for i,(x,y) in enumerate(path_t)) if path_t else (1e9,0)
            if d<=THREAT_R: hits.append((i,f'{"tower" if uid in TOWERS else "unit"} {uid} at ({int(tx)},{int(ty)})'))
        for l in set(amb):
            r=rect(l); x0,y0,x1,y1=r[0]/32,r[1]/32,r[2]/32,r[3]/32
            near=[(i) for i,(x,y) in enumerate(path_t) if x0-AMBUSH_R<=x<=x1+AMBUSH_R and y0-AMBUSH_R<=y<=y1+AMBUSH_R]
            if near: hits.append((near[0],f"triggered attack at '{lname(l)}'"))
        hits.sort(); enc=[]
        for i,what in hits:
            if enc and i-enc[-1][0][-1]<=GAP: enc[-1][0].append(i); enc[-1][1].append(what)
            else: enc.append(([i],[what]))
        unreach=[e for e in enc if (lambda q:PD[q[1]][q[0]]==math.inf)(path_t[e[0][0]])]
        need=W/3
        info.append(f"P{p+1}: route {' + '.join(lname(s)+'->'+lname(d) for s,d in L)} = {length:.0f} tiles (min {need:.0f}), {len(enc)} threat encounters")
        if broken: F.append(f'P{p+1}: escort leg(s) cannot be traced: {broken}')
        if length<need: F.append(f'P{p+1}: escort route is {length:.0f} tiles, shorter than a third of the map width ({need:.0f}): lead it through more of the map')
        if len(enc)<2: F.append(f"P{p+1}: {len(enc)} threat encounter(s) along the escort route (need 2+: ambushes, chokes held by enemies, patrols, base range, triggered attacks){' - found: '+'; '.join(w for e in enc for w in e[1][:3]) if enc else ''}")
        if unreach: F.append(f'P{p+1}: {len(unreach)} threat point(s) on the route the player cannot reach by ground without breaking an enemy base: {[e[1][0] for e in unreach][:4]}')
    if not N: F.append("design note lacks 'ESCORT_ROUTE: <escortee> :: <length tiles/time> :: <threats with locations> :: <what the player must do>'")
    out.append(('FAIL' if F else 'OK  ')+' escort_route_challenge: '+'; '.join(info)+''.join('\n     - '+f for f in F))
    if not glob.glob(os.path.join(os.path.dirname(os.path.abspath(path)),'*routes*.png')): out.append('WARN escort_route_challenge: no routes PNG (*routes*.png) next to the map showing the escort route')
    return out
if __name__=='__main__':
    rc=0
    for p in sys.argv[1:]:
        print('###',p)
        for l in run(p): print(l); rc|=l.startswith('FAIL')
    sys.exit(rc)
