#!/usr/bin/env python3
"""ally_shared_vision: every player allied with a human player shares vision with them, both ways.
   python3 tools/bw/check_ally_vision.py MAP.scx [...]      (exit 1 on FAIL)

Facts (staredit.net Scenario.chk wiki + vision FAQ, eudplib trigger tables):
  FORC force flags: bit0 random start, bit1 allies, bit2 allied victory, bit3 shared vision.
  Action 57 Set Alliance Status(player; status in the unit field: 0 enemy, 1 ally, 2 allied victory).
  Action 15/16 Run AI Script [At Location], script id in the number field. 'Turn ON/OFF Shared Vision for
  Player N' = '+Vi<N-1>'/'-Vi<N-1>'. The TRIGGER OWNER receives (or loses) the vision of player N.
Rules checked:
  - a force with the Allies flag holding a human and another human/computer player has the Shared vision flag
  - every Set Alliance Status to Ally/Allied victory between a human and another player has, in the same trigger,
    Run AI Script 'Turn ON Shared Vision for <target>' (the owner gets the target's vision)
  - both directions exist: the human gets the ally's vision AND the ally gets the human's vision
  - when an alliance with vision ends (Set Alliance Status Enemy), the same trigger turns that vision OFF
Exemption: a line 'ALLY_NO_VISION_OK: P<n> :: reason' in the design note / build info / <map>.vision_ok.txt."""
import sys,os,re,struct
from eudplib.bindings._rust import mpqapi
def sections(chk):
    S={}; i=0
    while i+8<=len(chk):
        n=chk[i:i+4].decode('latin1'); l=struct.unpack_from('<i',chk,i+4)[0]
        if l<0 or i+8+l>len(chk): break
        S[n]=chk[i+8:i+8+l]; i+=8+l
    return S
def exemptions(path):
    d=os.path.dirname(path); b=os.path.splitext(os.path.basename(path))[0]; pre=b.split('_')[0]; ex={}
    for f in [path[:-4]+'.vision_ok.txt',f'{d}/{pre}_Design_Note.md',f'{d}/{b}_Design_Note.md',f'{d}/{pre}_build_info.json',f'{d}/Design_Note.md',f'{d}/build_info.json']:
        if os.path.exists(f):
            for l in open(f,encoding='utf8',errors='replace'):
                m=re.search(r'ALLY_NO_VISION_OK:\s*P(\d)\s*::\s*(\S.*)',l)
                if m: ex[int(m.group(1))-1]=m.group(2).strip()
    return ex
def script(n): return struct.pack('<I',n)
def run(path):
    S=sections(bytes(mpqapi.MPQ.open(path).extract_file('staredit\\scenario.chk')))
    ownr=S['OWNR']; fo=S['FORC']+b'\0'*20; forces=list(fo[:8]); fflags=list(fo[16:20])
    act={p for p in range(8) if ownr[p] in (5,6)}; hum={p for p in range(8) if ownr[p]==6}; ex=exemptions(path)
    def grp(t):
        if 0<=t<8: return [t]
        if t==17: return list(range(8))
        if 18<=t<=21: return [p for p in range(8) if forces[p]==t-18]
        return []
    T=S.get('TRIG',b''); trigs=[]
    for t in range(0,len(T)-len(T)%2400,2400):
        r=T[t:t+2400]; a=[r[320+i*32:352+i*32] for i in range(64) if r[320+i*32+26]]
        own={o for q in range(28) if r[2372+q] for o in grp(q)}
        trigs.append((a,own))
    F=[]; gets=set(); pairs=set()     # gets: (receiver, source) of vision
    for f in range(4):
        mem=sorted(p for p in act if forces[p]==f)
        if fflags[f]&2 and len(mem)>1 and set(mem)&hum:
            if fflags[f]&8: gets|={(a,b) for a in mem for b in mem if a!=b}
            elif not set(mem)&set(ex): F.append(f'force {f+1} {["P%d"%(p+1) for p in mem]} is allied without the Shared vision flag')
    for ti,(a,own) in enumerate(trigs):
        vis={script(struct.unpack_from('<I',x,20)[0]) for x in a if x[26] in (15,16)}
        for o in own:
            for v in vis:
                if v[:3]==b'+Vi' and v[3:4].isdigit(): gets.add((o,int(v[3:4])))
        for x in a:
            if x[26]!=57: continue
            st=struct.unpack_from('<H',x,24)[0]
            for t in grp(struct.unpack_from('<I',x,16)[0]):
                for o in own:
                    if o==t or o not in act or t not in act or not ({o,t}&hum): continue
                    if o in ex or t in ex: continue
                    if st>=1:
                        pairs.add(tuple(sorted((o,t))))
                        if b'+Vi%d'%t not in vis: F.append(f'trig{ti}: P{o+1} allies P{t+1} without Run AI Script "Turn ON Shared Vision for Player {t+1}" in the same trigger')
                    else:
                        had=any(b'+Vi%d'%t in {script(struct.unpack_from('<I',y,20)[0]) for y in a2 if y[26] in (15,16)} for a2,o2 in trigs if o in o2)
                        if had and b'-Vi%d'%t not in vis: F.append(f'trig{ti}: P{o+1} ends the alliance with P{t+1} but keeps its vision (no "Turn OFF Shared Vision for Player {t+1}")')
    for a,b in sorted(pairs):
        for r,s in ((a,b),(b,a)):
            if (r,s) not in gets: F.append(f'P{r+1} never receives P{s+1}\'s vision although they are allied (needs a P{r+1}-owned trigger with "Turn ON Shared Vision for Player {s+1}")')
    F=sorted(set(F),key=F.index)
    info=f'alliances with humans {[f"P{a+1}-P{b+1}" for a,b in sorted(pairs)]}'+(f'; exempt {{{", ".join(f"P{k+1}: {v}" for k,v in ex.items())}}}' if ex else '')
    return [('FAIL' if F else 'OK  ')+f' ally_shared_vision: allied players share vision both ways ({info})'+(''.join('\n     - '+f for f in F[:12]))]
if __name__=='__main__':
    rc=0
    for p in sys.argv[1:]:
        print('###',p)
        for l in run(p): print(l); rc|=l.startswith('FAIL')
    sys.exit(rc)
