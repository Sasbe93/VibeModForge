#!/usr/bin/env python3
"""computer_ai_started + ai_workers_mining: every computer player that owns a pre-placed base runs its town AI from
mission start, set up the way Blizzard's campaign maps do it, so its workers mine from the first second.
   python3 tools/bw/check_computer_ai.py MAP.scx|scenario.chk [...]      (exit 1 on FAIL)

Reference: all 57 official campaign maps. Every one of the 125 computer players there that
owns a town hall or workers has a start location; the main town script (mission script or campaign script) runs by
'Run AI Script At Location' at a 4x3/4x4 location lying exactly on that player's town hall (location centre 0-0.5
tiles from the hall centre), in a trigger owned by that player (or its force) with condition Always. Large locations
are used only for the Area Town scripts of a second base. The AI town is centred on the location's centre; workers,
buildings and mineral patches are assigned to the town from there (SCAI command guide, start_town / start_areatown;
a town without assigned resources has a worker limit of 0).

computer_ai_started (FAIL), per computer player (OWNR 5) that owns a pre-placed town hall or worker:
  1 a start location (unit 214) of that player
  2 a town script (campaign Easy..Insane, Custom Level, Area Town or a mission script; not the helper scripts such
    as EnBk, VluA, HaHe, +Vi) in a trigger that runs for that player (owner = the player, its force or All Players),
    not only in a trigger of another player (Run AI Script always acts for the trigger's owner)
  3 started at mission start: conditions only Always / none / Elapsed Time <= 2 s
  4 a MAIN town: at least one town script (not Area Town) whose location centre lies on a town hall of that player
    (<= 3.5 tiles from the hall centre; Blizzard 0-0.5, worst official case 3.2), or 'Run AI Script' without location with the start location on a hall.
    Further scripts (Area Town, or Blizzard's second mission scripts on large locations) manage the halls inside
    their location.
ai_workers_mining (FAIL): every pre-placed worker of a computer player that stands within 12 tiles of one of its town
  halls belongs to a hall that is managed by a town script started at mission start and has mineral fields within 12
  tiles (with a valid main town every pre-placed building outside an Area Town location is assigned to that town,
  SCAI guide 'start_town'; without one, only Area Town locations manage halls); a hall with workers and no managing script leaves them idle. (Project rule: computer workers mine
  from the opening on. Blizzard itself starts some campaign AIs later, on a switch or when the player arrives; for us
  that needs the exemption.)
Exemption (design note next to the map): 'AI_IDLE_OK: P<n> :: <hall x,y or "all"> :: reason' (deliberately inactive
outpost, e.g. a station the player must capture intact)."""
import sys,os,struct,json,glob,math,re
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(os.path.dirname(HERE))
HALLS={106,130,131,132,133,154}; WORKERS={7,41,64}; MINERALS={176,177,178}; STARTLOC=214
HELPER={'Suic','SuiR','Rscu','MvTe','ClrC','Enmy','Ally','VluA','EnBk','StTg','StPt','EnTr','ExTr','NuHe','HaHe','JYDg','DWHe','ReHe','PB3F'}
def is_area(sc): return sc[1:3]=='AR'
def sections(chk):
    S={};i=0
    while i+8<=len(chk):
        n=chk[i:i+4].decode('latin1'); l=struct.unpack_from('<i',chk,i+4)[0]
        if l<0: break
        S[n]=chk[i+8:i+8+l]; i+=8+l
    return S
def load(path):
    if path.lower().endswith('.chk'): return open(path,'rb').read()
    from eudplib.bindings._rust import mpqapi
    return bytes(mpqapi.MPQ.open(path).extract_file('staredit\\scenario.chk'))
def note_lines(path):
    d=os.path.dirname(os.path.abspath(path)); out=[]
    for f in glob.glob(os.path.join(d,'*.md'))+glob.glob(os.path.join(d,'*.txt')):
        try: out+=[l.strip() for l in open(f,errors='ignore') if 'AI_IDLE_OK' in l]
        except OSError: pass
    return out
def run(path):
    S=sections(load(path)); ownr=S['OWNR']; forc=S.get('FORC',bytes(8))[:8]; U=S['UNIT']; T=S.get('TRIG',b''); M=S.get('MRGN',b'')
    units=[]
    for i in range(0,len(U)-len(U)%36,36):
        x,y,uid=struct.unpack_from('<HHH',U,i+4); units.append((U[i+16],uid,x/32,y/32))
    comp=[p for p in range(8) if ownr[p]==5]
    def loc(i):
        if i<=0 or i*20>len(M): return None
        l,t,r,b=struct.unpack_from('<IIII',M,(i-1)*20); return (l/32,t/32,r/32,b/32)
    def runs_for(t,p): return bool(t[2372+p] or t[2372+17] or (forc[p]<4 and t[2372+18+forc[p]]))
    def start_ok(conds):
        for c in conds:
            ct=c[15]; qty=struct.unpack_from('<I',c,8)[0]
            if ct==22: continue
            if ct==12 and c[14] in (0,10) and qty<=2: continue
            return False
        return True
    scripts={p:[] for p in comp}; foreign=[]
    for k in range(0,len(T)-len(T)%2400,2400):
        t=T[k:k+2400]; conds=[t[c*20:c*20+20] for c in range(16) if t[c*20+15]]
        if any(t[c*20+19]&2 for c in range(16) if t[c*20+15]): pass   # disabled conditions are ignored like StarCraft does
        for a in range(64):
            x=t[320+a*32:352+a*32]
            if x[26] not in (15,16) or x[28]&2: continue
            sc=x[20:24].decode('latin1','replace')
            if sc in HELPER or sc[1:3]=='Vi': continue
            L=loc(struct.unpack_from('<I',x,0)[0]) if x[26]==16 else None
            owners=[p for p in range(8) if runs_for(t,p)]
            for p in owners:
                if p in scripts: scripts[p].append(dict(sc=sc,loc=L,start=start_ok(conds),trig=k//2400))
            if any(ownr[o]!=5 for o in owners): foreign.append((sc,None,[f'P{o+1}' for o in owners],k//2400))
            for q in comp:
                if q not in owners and L and any(u[0]==q and u[1] in HALLS and L[0]<=u[2]<=L[2] and L[1]<=u[3]<=L[3] for u in units):
                    foreign.append((sc,q,[f'P{o+1}' for o in owners],k//2400))
    ex=note_lines(path); F=[]; W=[]; info=[]
    def exempt(p,h=None):
        for l in ex:
            m=re.search(r'AI_IDLE_OK:\s*P(\d)\s*::\s*([^:]+?)\s*::\s*\S',l)
            if m and int(m.group(1))==p+1:
                w=m.group(2).strip().lower()
                if w=='all' or h is None: return True
                n=[int(v) for v in re.findall(r'\d+',w)]
                if len(n)>=2 and abs(n[0]-h[0])<=3 and abs(n[1]-h[1])<=3: return True
        return False
    for p in comp:
        halls=[(u[2],u[3]) for u in units if u[0]==p and u[1] in HALLS]
        workers=[(u[2],u[3]) for u in units if u[0]==p and u[1] in WORKERS]
        if not halls and not workers: continue
        if exempt(p,None) and any(re.search(r'AI_IDLE_OK:\s*P%d\s*::\s*all'%(p+1),l,re.I) for l in ex): info.append(f'P{p+1} exempt'); continue
        sl=[(u[2],u[3]) for u in units if u[0]==p and u[1]==STARTLOC]
        sc=scripts[p]; start=[s for s in sc if s['start']]
        if not sl: F.append(f'P{p+1} has no start location (every Blizzard computer base has one, on its main town hall)')
        if not sc:
            fs=[f for f in foreign if f[1]==p] or [f for f in foreign if f[1] is None and f[0][0]==('ZTP'[S['SIDE'][p]] if S['SIDE'][p]<3 else '?')]
            F.append(f'P{p+1} runs no town AI script'+(f' (town script {fs[0][0]} sits in trigger #{fs[0][3]} owned by {fs[0][2]}: Run AI Script acts for the trigger owner, so it never runs for this player)' if fs else ''))
        elif not start:
            F.append(f'P{p+1} town AI {sc[0]["sc"]} starts only later (trigger #{sc[0]["trig"]} has conditions other than Always / Elapsed Time <= 2): workers stand idle until then')
        managed=set(); mains=[]; lost=[]
        for s in start:
            if s['loc'] is None:
                c=sl[-1] if sl else None
                h=[hh for hh in halls if c and math.hypot(hh[0]-c[0],hh[1]-c[1])<=3.5]
                if h: mains.append(s); managed|=set(h)
                else: F.append(f'P{p+1} Run AI Script {s["sc"]} without a location uses the start location, which is not on a town hall')
                continue
            l,t_,r,b=s['loc']; cx,cy=(l+r)/2,(t_+b)/2
            inside={h for h in halls if l<=h[0]<=r and t_<=h[1]<=b}
            near=sorted((math.hypot(h[0]-cx,h[1]-cy),h) for h in halls)
            if not is_area(s['sc']) and near and near[0][0]<=3.5: mains.append(s); continue
            if is_area(s['sc']): managed|=inside
            if not is_area(s['sc']): lost.append((s,cx,cy,near))
        if mains: managed|=set(halls)   # start_town takes every pre-placed building not inside an area town (SCAI guide)
        if lost and not mains:
            s,cx,cy,near=lost[0]
            F.append(f'P{p+1} has no main town AI on a town hall: {s["sc"]} location centre ({cx:.0f},{cy:.0f}) is '+(f'{near[0][0]:.1f} tiles from the nearest hall {tuple(round(v) for v in near[0][1])}' if near else 'not near any hall')
                     +' (the AI town is centred on the location centre; Blizzard runs every main town script at a 4x3 location exactly on the hall)')
        idle={}
        for w in workers:
            near=sorted((math.hypot(h[0]-w[0],h[1]-w[1]),h) for h in halls)
            h=near[0][1] if near and near[0][0]<=12 else None
            mins=h and any(u[1] in MINERALS and math.hypot(u[2]-h[0],u[3]-h[1])<=12 for u in units)
            if h in managed and mins: continue
            if not h: continue   # a worker far from every hall is scenery (Blizzard does this too), not a base worker
            key=tuple(round(v) for v in h)
            if h and exempt(p,key): continue
            idle[key]=idle.get(key,0)+1
        if idle: W.append(f'P{p+1}: '+', '.join(f'{n} worker(s) at hall {k}' if k!='no hall within 12 tiles' else f'{n} worker(s) with no hall within 12 tiles' for k,n in idle.items())+' not managed by a town AI started at mission start')
        info.append(f'P{p+1} '+('/'.join(sorted({s["sc"] for s in start})) or 'no AI'))
    R=[('FAIL ' if F else 'OK   ')+'computer_ai_started: every computer base runs its town AI from mission start, at a location on its town hall, with a start location ('+', '.join(info)+')'+''.join('\n     - '+x for x in F[:10])]
    R.append(('FAIL ' if W else 'OK   ')+'ai_workers_mining: pre-placed computer workers belong to a managed town hall with minerals (they mine from the start)'+''.join('\n     - '+x for x in W[:10]))
    return R
if __name__=='__main__':
    rc=0
    for p in sys.argv[1:]:
        print('###',p)
        for l in run(p): print(l); rc|=l.startswith('FAIL')
    sys.exit(rc)
