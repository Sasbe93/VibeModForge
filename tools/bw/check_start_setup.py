#!/usr/bin/env python3
"""start_setup_variety: what the human player owns at mission start is a deliberate, story-driven choice that differs
from the previous missions, as in the Blizzard campaigns (most missions start from a small core and the player builds).

   python3 tools/bw/check_start_setup.py MAP.scx [--prev PREV1.scx [PREV2.scx]]      (exit 1 on FAIL)
     without --prev: M<k-1>/M<k-2> of the same series next to the map (or in sibling delivery folders) when present
   python3 tools/bw/check_start_setup.py --campaign M1.scx M2.scx M3.scx ...          (each map against the two before it)

Measured: the human player's placed units (UNIT) plus units created for it by 'Always' triggers at start, without
heroes. Start type:
   no-base     no hall and no workers (hero/strike squad, escape, installation)
   build-up    workers without a hall, or a hall with at most 1 tech building
   small-base  a hall with 2-3 tech buildings
   established a hall with 4 or more tech buildings
Blizzard reference (57 released SC/BW campaign missions, scenario.chk read from the game's own files, measured the
same way): 32 % build-up, 28 % no base, 23 % small base, 18 % established; 67 % start without any static defence and
77 % with at most 2; never more than 2 unmorphed Creep Colonies and never more than 8 workers.

Rules (FAIL):
  1 declared type: the design note has 'START_SETUP: <no-base|build-up|small-base|established> :: <story reason>'
    and the measured type matches it.
  2 static defence: more than 2 Sunken/Spore Colonies, Photon Cannons, Bunkers or Missile Turrets need
    'START_DEFENSE_WHY: <what> :: <story reason>'; more than 2 unmorphed Creep Colonies always FAIL (placement artefact).
  3 new tech is earned: a building type that becomes available in this mission (compared with the PUNI of the previous
    missions given) must not stand ready at start, and a newly available unit type appears at most as a sample of 3 (Blizzard hands
    over 1-3 of a new unit in about a quarter of its missions as an introduction); exemption
    'START_GIFT_WHY: <unit or building> :: <reason>'.
  4 variety: the start package must differ from each of the two previous missions (weighted overlap of unit-type counts
    below 0.70; Blizzard's missions stay below that in 93 of 94 pairs one or two missions apart), and not three missions
    in a row may start 'established'.
WARN: more than 8 workers at start.
Sources: CHK layout from the staredit.net Scenario.chk wiki (UNIT 36-byte records, OWNR, PUNI 5700 bytes, TRIG 2400-byte
records; Create Unit = action 44/45, Always = condition 22)."""
import sys,os,re,glob,json,struct,collections
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.abspath(os.path.join(HERE,'..','..'))
IDS={int(k):v for k,v in json.load(open(os.path.join(ROOT,'data','bw','bw_unit_ids.json'))).items()}
HALLS={'Zerg_Hatchery','Zerg_Lair','Zerg_Hive','Terran_Command_Center','Protoss_Nexus'}
WORKERS={'Zerg_Drone','Terran_SCV','Protoss_Probe'}
STATIC={'Zerg_Sunken_Colony','Zerg_Spore_Colony','Terran_Bunker','Terran_Missile_Turret','Protoss_Photon_Cannon'}
CREEP='Zerg_Creep_Colony'
NOT_TECH=HALLS|STATIC|{CREEP,'Zerg_Extractor','Terran_Refinery','Protoss_Assimilator','Terran_Supply_Depot','Protoss_Pylon',
    'Zerg_Larva','Zerg_Egg','Zerg_Overlord'}
PREFIX=('Zerg_','Terran_','Protoss_')
BUILDINGS={v for k,v in IDS.items() if 106<=k<=202 and v.startswith(PREFIX)}
THRESH=0.70
SAMPLE=3
def read_chk(path):
    if path.lower().endswith('.chk'): return open(path,'rb').read()
    from eudplib.bindings._rust import mpqapi
    return bytes(mpqapi.MPQ.open(path).extract_file('staredit\\scenario.chk'))
def sections(d):
    S={}; i=0
    while i+8<=len(d):
        k=d[i:i+4].decode('latin1'); n=struct.unpack_from('<i',d,i+4)[0]
        if n<0 or i+8+n>len(d): n=max(0,len(d)-i-8)
        S[k]=(S.get(k,b'')+d[i+8:i+8+n]) if k in ('UNIT','TRIG') else d[i+8:i+8+n]; i+=8+n
    return S
def human(S):
    own=S.get('OWNR',b'')
    h=[i for i in range(min(8,len(own))) if own[i]==6]
    return h[0] if h else 0
def start_assets(S,p):
    u=collections.Counter(); U=S.get('UNIT',b'')
    for j in range(0,len(U)//36*36,36):
        t=struct.unpack_from('<IHHHHHHBBBBIHHII',U,j)
        if t[7]==p: u[IDS.get(t[3],str(t[3]))]+=1
    T=S.get('TRIG',b'')
    for k in range(len(T)//2400):
        tr=T[k*2400:(k+1)*2400]
        cids={struct.unpack_from('<IIIHBBBBH',tr,c*20)[5] for c in range(16)}-{0}
        if not cids<={22}: continue
        execp={q for q in range(27) if tr[2372+q]}
        for a in range(64):
            loc,s,w,tm,pl,num,ut,at,mod,fl=struct.unpack_from('<IIIIIIHBBB',tr,320+a*32)
            if at in (44,45) and (pl==p or (pl==13 and (p in execp or 17 in execp))): u[IDS.get(ut,str(ut))]+=max(mod,1)
    for k in list(u):
        if k.startswith(('Hero_','Special_','Resource_','Critter_','Powerup_')) or k in ('Zerg_Larva','Zerg_Egg'): del u[k]
    return u
def available(S,p):
    P=S.get('PUNI',b'')
    if len(P)<5700: return None
    out=set()
    for x in range(228):
        v=P[2736+x] if P[2964+p*228+x] else P[p*228+x]
        if v: out.add(IDS.get(x,str(x)))
    return out
def tech_count(u): return sum(c for k,c in u.items() if k in BUILDINGS and k not in NOT_TECH)
def classify(u):
    nw=sum(u[k] for k in WORKERS); nh=sum(u[k] for k in HALLS); tb=tech_count(u)
    if nh==0 and nw==0: return 'no-base'
    if nh==0 or tb<=1: return 'build-up'
    if tb<=3: return 'small-base'
    return 'established'
def norm(n): return {'Zerg_Lair':'Zerg_Hatchery','Zerg_Hive':'Zerg_Hatchery','Terran_Siege_Tank_Siege_Mode':'Terran_Siege_Tank_Tank_Mode'}.get(n,n)
def overlap(a,b):
    A=collections.Counter(); B=collections.Counter()
    for k,v in a.items(): A[norm(k)]+=v
    for k,v in b.items(): B[norm(k)]+=v
    keys=set(A)|set(B); mx=sum(max(A[k],B[k]) for k in keys)
    return sum(min(A[k],B[k]) for k in keys)/mx if mx else 0.0   # two empty starts repeat no package
def design_note(path):
    d=os.path.dirname(os.path.abspath(path))
    return '\n'.join(open(f,encoding='utf8',errors='replace').read() for f in sorted(set(glob.glob(os.path.join(d,'Design_Note*.md'))+glob.glob(os.path.join(d,'*_Design_Note.md')))))
def info(path):
    S=sections(read_chk(path)); p=human(S); u=start_assets(S,p)
    return dict(path=path,u=u,type=classify(u),avail=available(S,p))
def short(n): return n.split('_',1)[1] if n.startswith(PREFIX) else n
def run(path,prev=(),dn=None):
    I=info(path); u=I['u']; F=[]; Wn=[]
    dn=design_note(path) if dn is None else dn
    m=re.search(r'START_SETUP:\s*([\w-]+)\s*::\s*(\S.*)',dn)
    if not m: F.append(f"design note lacks 'START_SETUP: <no-base|build-up|small-base|established> :: <story reason>' (measured: {I['type']})")
    elif m.group(1).lower()!=I['type']: F.append(f"START_SETUP says {m.group(1)} but the map starts {I['type']}")
    st={short(k):c for k,c in u.items() if k in STATIC}; cc=u.get(CREEP,0)
    if sum(st.values())>2 and not re.search(r'START_DEFENSE_WHY:\s*\S.*::\s*\S',dn):
        F.append(f"static defence at start {st}; Blizzard gives more than 2 only in 12 of 57 missions (defence, survival or fortress missions): give the story reason with 'START_DEFENSE_WHY: <what> :: <reason>' or let the player build it")
    if cc>2: F.append(f'{cc} unmorphed Creep Colonies at start (Blizzard: never more than 2); a building placed off creep needs a smaller, creep-covered layout, not extra colonies')
    nw=sum(u[k] for k in WORKERS)
    if nw>8: Wn.append(f'{nw} workers at start (Blizzard campaign maximum: 8)')
    P=[info(x) for x in prev]
    pav=[q['avail'] for q in P if q['avail'] is not None]
    if pav and I['avail'] is not None:
        new=I['avail']-set().union(*pav)      # new = not available in either of the previous missions
        gw={g.strip().lower() for g in re.findall(r'START_GIFT_WHY:\s*([^:\n]+?)\s*::\s*\S',dn)}
        def exempt(g): return short(g).replace('_',' ').lower() in gw or short(g).lower() in gw or g.lower() in gw
        gb=sorted(k for k in u if k in new and k in BUILDINGS and not exempt(k))
        gu=sorted(k for k in u if k in new and k not in BUILDINGS and u[k]>SAMPLE and not exempt(k))
        if gb: F.append('newly unlocked buildings stand ready at start instead of being built by the player: '+', '.join(f'{u[g]}x {short(g)}' for g in gb)+" (exemption: 'START_GIFT_WHY: <building> :: <reason>')")
        if gu: F.append(f'more than a {SAMPLE}-unit sample of a newly unlocked unit at start: '+', '.join(f'{u[g]}x {short(g)}' for g in gu)+" (Blizzard hands over at most 3 as an introduction; exemption: 'START_GIFT_WHY: <unit> :: <reason>')")
    for q in P:
        o=overlap(u,q['u'])
        if o>=THRESH: F.append(f"start package overlaps {o:.2f} with {os.path.basename(q['path'])} (limit {THRESH}); vary the start (type, size, composition)")
    if len(P)>=2 and I['type']==P[0]['type']==P[1]['type']=='established':
        F.append('three missions in a row start established; Blizzard alternates build-up, no-base and small starts')
    head=(f"start_setup_variety: {I['type']}, {nw} workers, halls {sum(u[k] for k in HALLS)}, tech {tech_count(u)}, "
          f"static {sum(st.values())}, creep colonies {cc}"
          +(', overlap '+', '.join(f"{os.path.basename(q['path'])} {overlap(u,q['u']):.2f}" for q in P) if P else ''))
    return [('FAIL ' if F else ('WARN ' if Wn else 'OK   '))+head]+['     - '+x for x in F+Wn]
def previous_missions(path,n=2):
    """the previous missions of the same series next to the map: M<k-1>, M<k-2> (same letter prefix, e.g. M, ML, LY),
    in the map's folder or in sibling folders one level up (one delivery folder per mission)"""
    b=os.path.basename(path); m=re.match(r'([A-Za-z]*?)(\d+)[a-z]?_',b)
    if not m: return []
    pre,k=m.group(1),int(m.group(2)); d=os.path.dirname(os.path.abspath(path))
    pool=set(glob.glob(os.path.join(d,'*.scx'))+glob.glob(os.path.join(d,'..','*','*.scx'))+glob.glob(os.path.join(d,'..','*','*','*.scx'))+glob.glob(os.path.join(d,'..','..','*','*','*.scx')))
    out=[]
    for j in range(k-1,max(0,k-1-n),-1):
        c=sorted(f for f in pool if re.match(rf'{pre}{j}[a-z]?_',os.path.basename(f)))
        if c: out.append(os.path.abspath(c[0]))
        else: break
    return out
def run_auto(path):
    """predelivery entry point: compares with the previous missions found next to the map"""
    return run(path,previous_missions(path))
if __name__=='__main__':
    a=sys.argv[1:]; rc=0
    if a and a[0]=='--campaign':
        maps=a[1:]
        for i,mp in enumerate(maps):
            print('###',mp)
            for l in run(mp,prev=list(reversed(maps[max(0,i-2):i]))): print(l); rc|=l.startswith('FAIL')
    elif a:
        mp=a[0]; prev=a[a.index('--prev')+1:] if '--prev' in a else previous_missions(mp)
        print('###',mp)
        for l in run(mp,prev): print(l); rc|=l.startswith('FAIL')
    else: print(__doc__); rc=2
    sys.exit(rc)
