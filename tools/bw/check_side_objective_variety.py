#!/usr/bin/env python3
"""side_objective_variety: side objectives are varied, not 'destroy a building' every time.
   python3 tools/bw/check_side_objective_variety.py MAP.scx [--prev PREV(.scx|.md)]      (exit 1 on FAIL)
Without --prev the previous mission M<n-1> next to the map is used (same search as check_start_setup).

Design note: one line per optional objective
  'SIDE_OBJECTIVE: <name> :: <type> :: <reward type>'
  types: rescue, capture, protect, reach, hold, escort, ally, secret, collect, choice, destroy, other
  reward types: units, tech, base, ally, info, none, resources
  exemption: 'SIDE_OBJECTIVE_REPEAT_OK: <reason>'
The map is read too: optional objectives in the Set Mission Objectives texts (lines with 'Optional'), classified by
their wording ('destroy/kill/break ...' = destroy); triggers that add resources are counted for information only.
Rules (FAIL unless SIDE_OBJECTIVE_REPEAT_OK):
  1 the map has optional objectives but the design note has no SIDE_OBJECTIVE line
  2 the map has more destroy-type optional objectives than the note declares
  3 more than one destroy side objective in the mission
  4 a destroy side objective in this mission AND in the previous mission
The reward itself is not judged here: it follows from the objective and is explained by REWARD_WHY (check 41)."""
import sys,os,re,struct,glob
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from check_ally_vision import sections,note_files
TYPES=('rescue','capture','protect','reach','hold','escort','ally','secret','collect','choice','destroy','other')
def clean(t): return re.sub(r'\s+',' ',re.sub(r'[\x00-\x1f]',' ',t or '')).strip()
def kind(text):
    t=clean(text).lower()
    for k,rx in (('rescue',r'\brescue|\bfree\b|\bsave\b|\bsurvey squad|\bjoin'),('escort',r'\bescort|\bkeep .{0,30} alive until'),
                 ('protect',r'\bprotect|\bdefend|\bkeep .{0,30} alive'),('capture',r'\bcapture|\binfest|\bseize|\btake over'),
                 ('hold',r'\bhold\b'),('ally',r'\bally|\bpact|\balliance'),('secret',r'\bsecret|\bhidden'),('collect',r'\bcollect|\bgather|\bfind\b'),
                 ('choice',r'\bchoose|\bchoice|\beither\b'),('destroy',r'\bdestroy|\bkill|\bbreak\b|\braze|\bwipe'),('reach',r'\breach|\bgo to|\bget .{0,20} to\b')):
        if re.search(rx,t): return k
    return 'other'
def reward_kind(text):
    t=clean(text).lower()
    if re.search(r'mineral|\bgas\b|resource|\bore\b|vespene|cash|money',t): return 'resources'
    if re.search(r'\bnone\b|^-$|no reward',t): return 'none'
    for k in ('tech','base','ally','info'):
        if k in t: return k
    if re.search(r'unit|squad|join|hero|army',t): return 'units'
    return t or 'none'
def note(paths):
    so=[]; rep=None
    for f in paths:
        for l in open(f,encoding='utf8',errors='replace'):
            m=re.search(r'SIDE_OBJECTIVE:\s*(.+?)\s*::\s*(.+?)\s*::\s*(\S.*)',l)
            if m:
                ty=m.group(2).strip().lower(); ty=ty if ty in TYPES else kind(ty)
                so.append((m.group(1).strip(),ty,reward_kind(m.group(3))))
            m=re.search(r'SIDE_OBJECTIVE_REPEAT_OK:\s*(\S.*)',l)
            if m: rep=m.group(1).strip()
    return so,rep
def infer(path):
    """optional objective texts and the number of triggers that add resources (information only)"""
    from eudplib.bindings._rust import mpqapi
    S=sections(bytes(mpqapi.MPQ.open(path).extract_file('staredit\\scenario.chk')))
    ownr=S['OWNR']; hum={p for p in range(8) if ownr[p]==6}
    st=S.get('STR ',b'\0\0'); n=struct.unpack_from('<H',st,0)[0]
    def s(j):
        if not 0<j<=n: return ''
        o=struct.unpack_from('<H',st,2*j)[0]; return st[o:st.index(b'\0',o)].decode('utf8','replace')
    T=S.get('TRIG',b''); opt={}; res=0
    for t in range(0,len(T)-len(T)%2400,2400):
        r=T[t:t+2400]
        if not (any(r[2372+p] for p in hum) or r[2372+17]): continue
        c=[r[i*20:i*20+20] for i in range(16) if r[i*20+15]]
        a=[r[320+i*32:352+i*32] for i in range(64) if r[320+i*32+26]]
        start=all(x[15]==22 or (x[15]==12 and struct.unpack_from('<I',x,8)[0]<=2) for x in c)
        for x in a:
            if x[26]==12:
                for line in s(struct.unpack_from('<I',x,4)[0]).split('\n'):
                    L=clean(line)
                    if re.search(r'optional',L,re.I):
                        body=re.sub(r'(?i)^.*?optional[^:]*:\s*','',L)
                        body=re.sub(r'(?i)[\s.:(\[-]*\b(done|failed|complete[d]?|lost|missed)\b[\s.)\]!]*$','',body).strip(' -.:')
                        if body: opt.setdefault(re.sub(r'\W+',' ',body.lower())[:50],body)
            if x[26]==26 and x[27]==8 and not start and struct.unpack_from('<I',x,20)[0]>0:
                tgt=struct.unpack_from('<I',x,16)[0]
                if tgt in hum or tgt in (13,17): res+=1; break   # one reward per trigger
    return list(opt.values()),res
def mission_of(p):
    if p.endswith('.md'):
        so,_=note([p])
        if so: return so,'design note'
        maps=sorted(glob.glob(os.path.join(os.path.dirname(p),'*.scx')))
        if not maps: return [],'no SIDE_OBJECTIVE line and no map'
        p=maps[0]
    so,_=note(note_files(p))
    if so: return so,'design note'
    opt,_=infer(p); return [(o,kind(o),'?') for o in opt],'map objectives'
def run(path,prev=None):
    import check_start_setup as CS
    prev=CS.previous_missions(path,1) if prev is None else prev
    so,rep=note(note_files(path)); opt,res=infer(path); F=[]; W=[]
    d_decl=sum(1 for _,t,_ in so if t=='destroy'); d_map=sum(1 for o in opt if kind(o)=='destroy')
    if opt and not so: F.append(f"the map has {len(opt)} optional objective(s) {[o[:40] for o in opt]} but the design note has no 'SIDE_OBJECTIVE: <name> :: <type> :: <reward type>' line")
    if d_map>d_decl: F.append(f'the map has {d_map} destroy-type optional objective(s), the design note declares {d_decl}')
    nd=max(d_decl,d_map)
    if nd>1 and not rep: F.append(f'{nd} destroy side objectives in one mission (max 1): use rescue, capture, protect, reach/hold, escort, ally, secret, or none')
    seen=[]
    for p in prev:
        o,src=mission_of(p); pd=[x for x in o if x[1]=='destroy']
        seen.append(f"{os.path.basename(p)}: {', '.join(t for _,t,_ in o) or 'none'} ({src})")
        if nd and pd and not rep: F.append(f"a destroy side objective here and in the previous mission {os.path.basename(p)} ({pd[0][0][:40]}): vary the side objectives")
    info=', '.join(f'{t}/{r}' for _,t,r in so) or ('none' if not opt else 'undeclared')
    out=[('FAIL' if F else 'OK  ')+f" side_objective_variety: side objectives {info}; map: {len(opt)} optional, {res} trigger(s) adding resources"+(f"; previous: {'; '.join(seen)}" if seen else '')+(f'; repeat ok: {rep}' if rep else '')+''.join('\n     - '+f for f in F)]
    if W: out.append('WARN side_objective_variety:'+''.join('\n     - '+w for w in W))
    return out
if __name__=='__main__':
    a=sys.argv[1:]; rc=0; mp=a[0]; prev=a[a.index('--prev')+1:] if '--prev' in a else None
    print('###',mp)
    for l in run(mp,prev): print(l); rc|=l.startswith('FAIL')
    sys.exit(rc)
