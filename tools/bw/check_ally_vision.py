#!/usr/bin/env python3
"""ally_shared_vision: allied players share vision both ways, and vision starts exactly when the alliance starts
(never before it, e.g. not at mission start when the alliance only comes with a later pact).
   python3 tools/bw/check_ally_vision.py MAP.scx [...]      (exit 1 on FAIL)

Facts (staredit.net Scenario.chk wiki + vision FAQ, StarEdit AI-script list):
  FORC force flags: bit0 random start, bit1 allies, bit2 allied victory, bit3 shared vision.
  Action 57 Set Alliance Status(player; status in the unit field: 0 enemy, 1 ally, 2 allied victory).
  Action 15/16 Run AI Script [At Location], script id in the number field. 'Turn ON/OFF Shared Vision for
  Player N' = '+Vi<N-1>'/'-Vi<N-1>'. The TRIGGER OWNER receives (or loses) the vision of player N.
Rules checked (pairs of a human and another active player):
  1 a force with the Allies flag holding a human and another player has the Shared vision flag
  2 every Set Alliance Status Ally/Allied victory has, in the SAME trigger, 'Turn ON Shared Vision' for that player
    (vision starts with the alliance)
  3 every 'Turn ON Shared Vision' sits in a trigger that also sets that alliance (Ally/Allied victory) for the pair.
    Vision without the alliance action in the same trigger = vision that starts before or apart from the alliance.
  4 both directions: the human gets the ally's vision AND the ally gets the human's vision
  5 when an alliance with vision ends (Set Alliance Status Enemy), the same trigger turns that vision OFF
  6 alliance timing: if the alliance of a pair changes during the mission (a non-start trigger sets it), the design
    note must say when the alliance with shared vision begins: 'ALLIANCE_STARTS: P<n> :: start' or
    'ALLIANCE_STARTS: P<n> :: switch <k> :: <event>' (k = switch index as the generator uses it in m.SW(k)).
    With 'switch k', every vision ON for that pair must be in a trigger conditioned on switch k being set, and no
    mission-start trigger may turn it on. (Catches 'truce ally at start, real ally after the pact' maps that gave
    vision from the start.)
Exemption: 'ALLY_NO_VISION_OK: P<n> :: reason' (design note / build info / <map>.vision_ok.txt) lifts rules 1, 2
and 4 for that player (allied without vision is intended). Rules 3, 5 and 6 still apply: no vision before an alliance."""
import sys,os,re,glob,struct
from eudplib.bindings._rust import mpqapi
def sections(chk):
    S={}; i=0
    while i+8<=len(chk):
        n=chk[i:i+4].decode('latin1'); l=struct.unpack_from('<i',chk,i+4)[0]
        if l<0 or i+8+l>len(chk): break
        S[n]=chk[i+8:i+8+l]; i+=8+l
    return S
def note_files(path):
    d=os.path.dirname(path); b=os.path.splitext(os.path.basename(path))[0]; pre=b.split('_')[0]
    fs=[path[:-4]+'.vision_ok.txt',f'{d}/{pre}_Design_Note.md',f'{d}/{b}_Design_Note.md',f'{d}/{pre}_build_info.json',
        f'{d}/Design_Note.md',f'{d}/build_info.json']+sorted(glob.glob(f'{d}/Design_Note*.md'))
    return [f for i,f in enumerate(fs) if os.path.exists(f) and f not in fs[:i]]
def notes(path):
    ex={}; starts={}
    for f in note_files(path):
        for l in open(f,encoding='utf8',errors='replace'):
            m=re.search(r'ALLY_NO_VISION_OK:\s*P(\d)\s*::\s*(\S.*)',l)
            if m: ex[int(m.group(1))-1]=m.group(2).strip()
            m=re.search(r'ALLIANCE_STARTS:\s*P(\d)\s*::\s*(start|switch\s*(\d+))',l,re.I)
            if m: starts[int(m.group(1))-1]=('start',None) if m.group(2).lower()=='start' else ('switch',int(m.group(3)))
    return ex,starts
def script(n): return struct.pack('<I',n)
def is_start(conds):   # mission start: only Always, Elapsed Time <= 2 s, or 'switch is cleared' (once-guards)
    return all(c[15]==22 or (c[15]==12 and struct.unpack_from('<I',c,8)[0]<=2 and c[14] in (0,1,10)) or (c[15]==11 and c[14]==3) for c in conds)
def switches_set(conds): return {c[16] for c in conds if c[15]==11 and c[14]==2}
def run(path):
    S=sections(bytes(mpqapi.MPQ.open(path).extract_file('staredit\\scenario.chk')))
    ownr=S['OWNR']; fo=S['FORC']+b'\0'*20; forces=list(fo[:8]); fflags=list(fo[16:20])
    act={p for p in range(8) if ownr[p] in (5,6)}; hum={p for p in range(8) if ownr[p]==6}; ex,starts=notes(path)
    def grp(t):
        if 0<=t<8: return [t]
        if t==17: return list(range(8))
        if 18<=t<=21: return [p for p in range(8) if forces[p]==t-18]
        return []
    T=S.get('TRIG',b''); trigs=[]
    for t in range(0,len(T)-len(T)%2400,2400):
        r=T[t:t+2400]
        c=[r[i*20:i*20+20] for i in range(16) if r[i*20+15]]
        a=[r[320+i*32:352+i*32] for i in range(64) if r[320+i*32+26]]
        own={o for q in range(28) if r[2372+q] for o in grp(q)}
        trigs.append((c,a,own))
    def human_pair(o,t): return o!=t and o in act and t in act and bool({o,t}&hum)
    F=[]; gets=set(); pairs=set(); changed=set()
    for f in range(4):
        mem=sorted(p for p in act if forces[p]==f)
        if fflags[f]&2 and len(mem)>1 and set(mem)&hum:
            if fflags[f]&8:
                gets|={(a,b) for a in mem for b in mem if a!=b}
                for p in mem:
                    if starts.get(p,('start',))[0]=='switch': F.append(f'P{p+1}: force {f+1} shares vision from the start, but the design note says the alliance starts with a switch')
            elif not set(mem)&set(ex): F.append(f'force {f+1} {["P%d"%(p+1) for p in mem]} is allied without the Shared vision flag')
    for ti,(c,a,own) in enumerate(trigs):
        vis={script(struct.unpack_from('<I',x,20)[0]) for x in a if x[26] in (15,16)}
        allies={(o,t) for x in a if x[26]==57 and struct.unpack_from('<H',x,24)[0]>=1 for t in grp(struct.unpack_from('<I',x,16)[0]) for o in own}
        start=is_start(c); sw=switches_set(c)
        for o in own:
            for v in vis:
                if not (v[:3]==b'+Vi' and v[3:4].isdigit()): continue
                t=int(v[3:4])
                if not human_pair(o,t): continue
                gets.add((o,t))
                if (o,t) not in allies:     # rule 3
                    F.append(f'trig{ti}: P{o+1} gets P{t+1}\'s vision without setting the alliance in the same trigger (vision must start exactly when the alliance starts)')
                for p in (o,t):              # rule 6
                    k=starts.get(p)
                    if k and k[0]=='switch' and (start or k[1] not in sw):
                        F.append(f'trig{ti}: vision P{o+1}<-P{t+1} {"at mission start" if start else "outside switch "+str(k[1])}, but the design note says the alliance with P{p+1} starts with switch {k[1]}')
        for x in a:
            if x[26]!=57: continue
            st=struct.unpack_from('<H',x,24)[0]
            for t in grp(struct.unpack_from('<I',x,16)[0]):
                for o in own:
                    if not human_pair(o,t): continue
                    if not start: changed.add(tuple(sorted((o,t))))
                    if st>=1:
                        pairs.add(tuple(sorted((o,t))))
                        if o in ex or t in ex: continue
                        k=starts.get(t) or starts.get(o)
                        if k and k[0]=='switch' and start: continue   # truce at start; the real alliance comes with the switch
                        if b'+Vi%d'%t not in vis: F.append(f'trig{ti}: P{o+1} allies P{t+1} without Run AI Script "Turn ON Shared Vision for Player {t+1}" in the same trigger')
                    else:
                        had=any(b'+Vi%d'%t in {script(struct.unpack_from('<I',y,20)[0]) for y in a2 if y[26] in (15,16)} for _,a2,o2 in trigs if o in o2)
                        if had and b'-Vi%d'%t not in vis: F.append(f'trig{ti}: P{o+1} ends the alliance with P{t+1} but keeps its vision (no "Turn OFF Shared Vision for Player {t+1}")')
    for a,b in sorted(pairs):
        if a in ex or b in ex:
            if ((a,b) in gets)!=((b,a) in gets): F.append(f'P{a+1}/P{b+1}: vision is turned on in one direction only')
            continue
        for r,s in ((a,b),(b,a)):
            if (r,s) not in gets: F.append(f'P{r+1} never receives P{s+1}\'s vision although they are allied (needs a P{r+1}-owned trigger with "Turn ON Shared Vision for Player {s+1}")')
    for a,b in sorted(changed&pairs):     # rule 6 (only pairs that are allied at some point)
        for p in (a,b):
            if p not in hum and p not in starts:
                F.append(f'P{p+1}: the alliance with P{(b if p==a else a)+1} changes during the mission; the design note needs "ALLIANCE_STARTS: P{p+1} :: start" or ":: switch <k> :: <event>" (when vision begins)')
    F=sorted(set(F),key=F.index)
    info=f'alliances with humans {[f"P{a+1}-P{b+1}" for a,b in sorted(pairs)]}'+(f'; exempt {{{", ".join(f"P{k+1}: {v}" for k,v in ex.items())}}}' if ex else '')+(f'; starts {{{", ".join(f"P{k+1}: {v[0]}{" "+str(v[1]) if v[1] is not None else ""}" for k,v in starts.items())}}}' if starts else '')
    return [('FAIL' if F else 'OK  ')+f' ally_shared_vision: allied players share vision both ways, starting with the alliance ({info})'+(''.join('\n     - '+f for f in F[:12]))]
if __name__=='__main__':
    rc=0
    for p in sys.argv[1:]:
        print('###',p)
        for l in run(p): print(l); rc|=l.startswith('FAIL')
    sys.exit(rc)
