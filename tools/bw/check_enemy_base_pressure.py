#!/usr/bin/env python3
"""enemy_base_pressure: the mission's pressure does not hang on one enemy base the player can break early.
   python3 tools/bw/check_enemy_base_pressure.py MAP.scx [...]      (run from the repository root; exit 1 on FAIL)

Sasbe t1025: a Zerg base near the player start fed every attack wave and its town AI; the player destroyed it early,
and the rest of the 'reach the kiln' mission had no attacks at all.

Pressure sources read from the final map:
  - scripted waves: an enemy Create Unit + Order trigger. Its gate is every 'Command/Bring at least 1 <building>' of an
    enemy player in its conditions, also through switches (a wave on 'Switch N is set' inherits the gates of every
    trigger that sets N). A gate on Lair/Hive/Greater Spire/Sunken/Spore resolves to the pre-placed building that
    morphs into it, so the T_each siblings of one hatchery are one base, not three.
  - campaign town AIs ('Run AI Script (At Location)' with a campaign script such as ZMCx/ZMEx; not Area Town or helper
    scripts): alive while any town hall of that computer player stands.
  - waves without a building gate are independent of every base (they keep coming).
A base 'stops' a source when every alternative of one of the source's gates is that base.
FAIL (unless 'PRESSURE_SINGLE_OK: <reason>' is in the design note):
  1 one enemy base stops every pressure source (waves and attacking AIs), it is reachable over ground from the player
    start, and destroying it is not what wins the mission (the victory trigger does not wait for that base to be
    gone). Give the pressure a second, independent source: another base with its own waves or AI, waves that do not
    depend on that base (reinforcements by drop or from off-map), or make that base the objective.
WARN: a base that stops at least half of the sources is closer (ground path) to the player start than the main
objective target and is not an objective.
OK with a note when the map has no waves and no attacking AI (objective_paths judges the pressure then)."""
import sys,os,math,re,struct
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import mission_model as MM
from mission_model import u32,u16
HELPER={'Suic','SuiR','Rscu','MvTe','ClrC','Enmy','Ally','VluA','EnBk','StTg','StPt','EnTr','ExTr','NuHe','HaHe','JYDg','DWHe','ReHe','PB3F','+Vi','-Vi'}
def attack_script(sc):
    """campaign town scripts that build and attack: <race><difficulty><C|E>x, plus custom-level scripts"""
    if sc in HELPER or sc[1:3]=='AR': return False
    return bool(re.match(r'^[TZP][LMHI][CE]x$',sc)) or sc[1:3]=='CU' or sc[2:4]=='Cx'

def gates_of(M,i,memo,stack=()):
    """list of gate clauses (each a frozenset of base positions; the trigger needs one of them) for trigger i"""
    if i in memo: return memo[i]
    if i in stack: return []
    v=M.v; c,a,own=v.trigs[i]; out=[]
    for x in c:
        if x[15] in (2,3) and x[14]==0 and u32(x,8)>=1:
            pl=set(v.grp(u32(x,4),own))&v.enemy; uid=u16(x,12)
            if pl and uid<228 and MM.is_building(uid):
                inst=M.instances(pl,uid,u32(x,0) if x[15]==3 else None)
                if inst: out.append(inst)
    setters=M._setters
    for x in c:
        if x[15]==11 and x[14]==2:
            sw=x[16]; srcs=setters.get(sw,[])
            if not srcs: continue
            alts=[gates_of(M,j,memo,stack+(i,)) for j in srcs]
            if all(alts):
                # the switch can come from any setter: a base stops it only if it stops every setter.
                # Merge: one clause per setter clause set; keep the union of each setter's single-base clauses.
                merged=frozenset().union(*[frozenset().union(*cl) for cl in alts])
                # if every setter is gated by the same single base, that base gates this wave
                singles=[set().union(*cl) for cl in alts]
                if all(len(sg)==1 for sg in singles) and len(set().union(*singles))==1: out.append(frozenset(singles[0]))
                else: out.append(merged)
    memo[i]=out
    return out

def victory_bases(M):
    """base positions whose destruction the victory trigger (directly or through a switch) waits for"""
    v=M.v; out=set(); need_sw=set()
    def gone_inst(c,own):
        r=set()
        for x in c:
            if x[15] in (2,3) and x[14] in (1,10) and u32(x,8)==0:
                pl=set(v.grp(u32(x,4),own))&v.enemy; uid=u16(x,12)
                if pl and uid<228: r|=M.instances(pl,uid,u32(x,0) if x[15]==3 else None)
                elif pl and uid in (MM.ANY,MM.BUILDINGS): r|={(round(u['x']/32,1),round(u['y']/32,1)) for u in v.U if u['o'] in pl and u['id'] in MM.HALLS}
        return r
    for c,a,own in v.trigs:
        if any(x[26]==1 for x in a) and M.human_trig(own):
            out|=gone_inst(c,own)
            need_sw|={x[16] for x in c if x[15]==11 and x[14]==2}
    seen=set()
    while need_sw-seen:
        sw=(need_sw-seen).pop(); seen.add(sw)
        for j in M._setters.get(sw,[]):
            c,a,own=v.trigs[j]; out|=gone_inst(c,own)
            need_sw|={x[16] for x in c if x[15]==11 and x[14]==2}
    return out

def run(path,M=None):
    M=M or MM.Model(path); v=M.v
    M._setters=M.switch_setters()
    memo={}; sources=[]
    for i,(c,a,own) in enumerate(v.trigs):
        if not any(x[26] in (44,45) and any(p in v.enemy for p in v.grp(u32(x,16),own)) for x in a): continue
        if not any(x[26]==46 and any(p in v.enemy for p in v.grp(u32(x,16),own)) for x in a): continue
        g=gates_of(M,i,memo)
        sources.append(dict(kind='waves',trig=i,gates=g))
    # group waves with identical gates into one source
    grouped={}
    for s_ in sources:
        key=tuple(sorted(tuple(sorted(cl)) for cl in s_['gates']))
        grouped.setdefault(key,[]).append(s_['trig'])
    srcs=[dict(kind='waves',trigs=t,gates=[frozenset(cl) for cl in key]) for key,t in grouped.items()]
    for p in sorted(v.enemy):
        scripts=set()
        for c,a,own in v.trigs:
            if p not in v.grp(13,own) and p not in own: continue
            for x in a:
                if x[26] in (15,16):
                    sc=struct.pack('<I',u32(x,20)).decode('latin1')
                    if attack_script(sc): scripts.add(sc)
        if scripts:
            halls=frozenset((round(u['x']/32,1),round(u['y']/32,1)) for u in v.U if u['o']==p and u['id'] in MM.HALLS)
            srcs.append(dict(kind='ai',player=p,scripts=sorted(scripts),gates=[halls] if halls else []))
    out=[]
    if not srcs:
        return ['OK   enemy_base_pressure: no scripted waves and no attacking town AI (pressure is judged by objective_paths)']
    bases=set()
    for s_ in srcs:
        for cl in s_['gates']: bases|=set(cl)
    def stops(b,s_): return any(cl and set(cl)<={b} for cl in s_['gates'])
    vic=victory_bases(M)
    def walk(b):
        seg,L,_,_=v.path(v.start,b); return L
    def label(s_):
        if s_['kind']=='ai': return f"town AI P{s_['player']+1} ({', '.join(s_['scripts'])})"
        return f"waves (trigger{'s' if len(s_['trigs'])>1 else ''} {', '.join(map(str,s_['trigs'][:6]))}{' ...' if len(s_['trigs'])>6 else ''})"
    def bname(b):
        for u in v.U:
            if (round(u['x']/32,1),round(u['y']/32,1))==b and u['o'] in v.enemy: return f"{MM.uname(u['id'])} P{u['o']+1} at ({b[0]:.0f},{b[1]:.0f})"
        return f'base at {b}'
    info=[]
    for s_ in srcs:
        g='; '.join(' or '.join(bname(b) for b in sorted(cl)) for cl in s_['gates']) or 'no base (independent)'
        info.append(f'{label(s_)} <- {g}')
    F=[]; W=[]
    ok=re.search(r'PRESSURE_SINGLE_OK:\s*(\S.*)',M.notes)
    # main objective target distance (first non-optional objective with a traced path)
    objs=P_objs(M)
    main_len=None
    for o in objs:
        if o.get('optional'): continue
        for item in o.get('paths') or []:
            if item[0]=='start_to_target' and item[5]!=math.inf: main_len=item[5]; break
        if main_len: break
    for b in sorted(bases):
        st=[s_ for s_ in srcs if stops(b,s_)]
        L=walk(b); reach=L!=math.inf
        if len(st)==len(srcs) and b not in vic and reach:
            F.append(f"{bname(b)} feeds every pressure source ({len(st)}/{len(srcs)}: {', '.join(label(s_) for s_ in st)}); it is {L:.0f} tiles / {MM.P.travel_sec(L,0):.0f}s of marching from the player start"
                     +(f" (main objective target: {main_len:.0f} tiles)" if main_len else '')+", and destroying it is not the victory condition. Once it dies no attack comes any more; add an independent second source (another base with its own waves or AI, reinforcements that do not need this base) or make the base the objective")
        elif len(st)*2>=len(srcs) and b not in vic and main_len and L<main_len:
            W.append(f"{bname(b)} stops {len(st)}/{len(srcs)} pressure sources and lies closer to the player ({L:.0f} tiles) than the main objective target ({main_len:.0f} tiles)")
    if F and ok:
        return [f'OK   (PRESSURE_SINGLE_OK) enemy_base_pressure: {ok.group(1).strip()} :: '+'; '.join(info)]
    out.append(('FAIL' if F else 'OK  ')+' enemy_base_pressure: '+'; '.join(info)+''.join('\n     - '+f for f in F))
    if W: out.append('WARN enemy_base_pressure:'+''.join('\n     - '+w for w in W))
    return out

def P_objs(M):
    if not hasattr(M,'_objs'): M._objs=MM.P.detect_objectives(M.v)
    return M._objs

if __name__=='__main__':
    rc=0
    for p in sys.argv[1:]:
        print('###',p)
        for l in run(p): print(l); rc|=l.startswith('FAIL')
    sys.exit(rc)
