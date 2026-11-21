#!/usr/bin/env python3
"""hero_own_color: important allied or enemy heroes (general, commander, antagonist) have their own player slot with a
colour of their own, and that slot behaves exactly like the hero's faction.
   python3 tools/bw/check_hero_own_color.py MAP.scx [...]      (exit 1 on FAIL)

Which units count as an important hero (computer players only; the human's and rescuable heroes are not checked):
  - a placed unit whose type is a BW hero type (data/bw/bw_unit_ids.json name 'Hero_...'), or
  - a renamed (custom-named, UNIx) non-building unit type of which its owner has exactly one placed.
Rules (FAIL):
  1 own slot: the hero's player holds only heroes (no army, no buildings of the faction)
  2 own colour: the hero's player colour (COLR) differs from every other active player's colour
  3 declared faction: the design note has 'HERO_SLOT: <hero name> :: P<h> :: faction P<f>'
  4 same alliances and vision as the faction: every Set Alliance Status / shared-vision AI script the faction sets
    (or that is set towards the faction) has the same counterpart for the hero slot under the same switch
    conditions; a Run AI Script / Set Alliance Status the faction gets in its own triggers needs a hero-slot trigger too
  5 victory/defeat include the slot: if a Victory/Defeat trigger reads the faction player in a condition,
    some Victory/Defeat trigger also reads the hero slot
Exemption: 'HERO_COLOR_SHARED: <hero name or P<n>> :: reason' (no free slot or colour left) lifts rules 1-5 for that hero.
Sources: CHK layout from the staredit.net Scenario.chk wiki (UNIT 36-byte records, OWNR, COLR, FORC, TRIG 2400-byte
records, UNIx: 228 use-default bytes, then hp, shields, armour, build time, minerals, gas, then the name string ids)."""
import sys,os,re,glob,json,struct
from eudplib.bindings._rust import mpqapi
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.abspath(os.path.join(HERE,'..','..'))
IDS={int(k):v for k,v in json.load(open(os.path.join(ROOT,'data','bw','bw_unit_ids.json'))).items()}
HERO_T={k for k,v in IDS.items() if v.startswith('Hero_')}
NOT_HERO={k for k,v in IDS.items() if v.startswith(('Critter_','Powerup_','Special_','Spell_','Resource_','Unused_'))}|{214}
def sections(chk):
    S={}; i=0
    while i+8<=len(chk):
        n=chk[i:i+4].decode('latin1'); l=struct.unpack_from('<i',chk,i+4)[0]
        if l<0 or i+8+l>len(chk): break
        S[n]=chk[i+8:i+8+l]; i+=8+l
    return S
def strings(S):
    st=S.get('STRx') or S.get('STR ',b'')
    if not st: return {}
    wide='STRx' in S; c=struct.unpack_from('<I' if wide else '<H',st)[0]; w=4 if wide else 2
    out={}
    for i in range(c):
        o=struct.unpack_from('<I' if wide else '<H',st,w+i*w)[0]
        if o<len(st): out[i+1]=st[o:].split(b'\0')[0].decode('utf-8','replace')
    return out
def custom_names(S):
    u=S.get('UNIx') or S.get('UNIS'); STR=strings(S)
    if not u: return {}
    n=228; off=n+n*4+n*2+n+n*2+n*2+n*2          # use-default, hp, shields, armour, build time, minerals, gas
    out={}
    for t in range(n):
        if u[t]==0:
            sid=struct.unpack_from('<H',u,off+t*2)[0]
            if sid and STR.get(sid): out[t]=STR[sid].strip()
    return out
def note(path):
    d=os.path.dirname(os.path.abspath(path)); b=os.path.splitext(os.path.basename(path))[0]
    fs=sorted(set(glob.glob(os.path.join(d,'Design_Note*.md'))+glob.glob(os.path.join(d,b.split('_')[0]+'_Design_Note.md'))+[path[:-4]+'.hero_ok.txt']))
    return '\n'.join(open(f,encoding='utf-8',errors='replace').read() for f in fs if os.path.exists(f) and 'SECRET' not in f)
def run(path):
    S=sections(bytes(mpqapi.MPQ.open(path).extract_file('staredit\\scenario.chk')))
    ownr=S['OWNR']; colr=list(S.get('COLR',bytes(range(8))))[:8]; act={p for p in range(8) if ownr[p] in (5,6)}
    comp={p for p in range(8) if ownr[p]==5}
    U=S['UNIT']; units=[(struct.unpack_from('<H',U,i+8)[0],U[i+16]) for i in range(0,len(U)-len(U)%36,36)]
    names=custom_names(S); nt=note(path)
    slots={}; exl={}
    for m_ in re.finditer(r'HERO_SLOT:\s*(.+?)\s*::\s*P(\d)\s*::\s*faction\s*P(\d)',nt): slots[int(m_.group(2))-1]=(m_.group(1).strip(),int(m_.group(3))-1)
    for m_ in re.finditer(r'HERO_COLOR_SHARED:\s*(.+?)\s*::\s*(\S.{2,})',nt): exl[m_.group(1).strip().lower()]=m_.group(2).strip()
    cnt={}
    for t,o in units: cnt[(t,o)]=cnt.get((t,o),0)+1
    heroes=[]
    for (t,o),k in cnt.items():
        if o not in comp or t in NOT_HERO: continue
        if t in HERO_T or (t in names and t<106 and k==1): heroes.append((t,o,names.get(t,IDS.get(t,str(t)))))
    F=[]; info=[]
    T=S.get('TRIG',b''); trigs=[]
    for i in range(0,len(T)-len(T)%2400,2400):
        r=T[i:i+2400]
        c=[r[k*20:k*20+20] for k in range(16) if r[k*20+15]]
        a=[r[320+k*32:352+k*32] for k in range(64) if r[320+k*32+26]]
        trigs.append((c,a,{q for q in range(8) if r[2372+q]}))
    def swset(c): return frozenset((x[16],x[14]) for x in c if x[15]==11)
    for t,o,nm in heroes:
        info.append(f'{nm} = P{o+1}')
        if nm.lower() in exl or f'p{o+1}' in exl: info[-1]+=' (shared colour, exempt)'; continue
        others=[(t2,k) for (t2,o2),k in cnt.items() if o2==o and t2 not in HERO_T and not (t2 in names and t2<106 and k==1) and t2 not in NOT_HERO]
        if others: F.append(f'{nm} (P{o+1}) shares its slot with {sum(k for _,k in others)} faction unit(s)/building(s) {sorted({IDS.get(x,x) for x,_ in others})[:4]}; give the hero its own player slot')
        same=[p for p in act if p!=o and colr[p]==colr[o]]
        if same: F.append(f'{nm} (P{o+1}) has the same colour ({colr[o]}) as {["P%d"%(p+1) for p in same]}')
        if o not in slots: F.append(f'{nm} (P{o+1}): the design note needs "HERO_SLOT: {nm} :: P{o+1} :: faction P<n>"'); continue
        f=slots[o][1]
        if f not in act: F.append(f'{nm}: faction P{f+1} is not an active player'); continue
        # rule 4: alliance / vision actions, compared under the same switch conditions
        def sig(owner_map):
            out=set()
            for c,a,own in trigs:
                for ow in own:
                    for x in a:
                        if x[26]==57:
                            tgt=struct.unpack_from('<I',x,16)[0]; st=struct.unpack_from('<H',x,24)[0]
                            out.add((owner_map(ow),'ally',owner_map(tgt) if tgt<8 else tgt,st,swset(c)))
                        elif x[26] in (15,16):
                            sc=struct.pack('<I',struct.unpack_from('<I',x,20)[0])
                            if sc[1:3]==b'Vi' and sc[3:4].isdigit(): out.add((owner_map(ow),'vis',owner_map(int(sc[3:4])),sc[:1],swset(c)))
            return out
        fsig={s for s in sig(lambda p:p) if f in (s[0],s[2]) and o not in (s[0],s[2])}
        hsig={s for s in sig(lambda p:f if p==o else p) if f in (s[0],s[2])}
        miss=sorted(fsig-hsig,key=str)
        # alliances between hero slot and faction themselves are fine either way
        miss=[s for s in miss if not (s[0]==f and s[2]==f)]
        if miss:
            def d(s): return f'P{s[0]+1} {"sets alliance "+str(s[3])+" with" if s[1]=="ally" else ("turns "+("ON" if s[3]==b"+" else "OFF")+" vision of")} P{s[2]+1 if isinstance(s[2],int) and s[2]<8 else s[2]}'+(f' (switches {sorted(s[4])})' if s[4] else '')
            F.append(f'{nm} (P{o+1}) does not follow its faction P{f+1}: missing the counterpart of '+'; '.join(d(s) for s in miss[:4]))
        # rule 5
        def reads(p): return any(any(x[26] in (1,2) for x in a) and any(x[15] not in (11,12,22,1) and struct.unpack_from('<I',x,4)[0]==p for x in c) for c,a,own in trigs)
        if reads(f) and not reads(o): F.append(f'{nm} (P{o+1}): a victory/defeat trigger reads faction P{f+1} but none reads the hero slot P{o+1}')
    head=f'hero_own_color: important computer heroes have their own slot and colour and behave like their faction ({", ".join(info) or "no computer heroes"})'
    return [('FAIL ' if F else 'OK   ')+head+''.join('\n     - '+x for x in F[:10])]
if __name__=='__main__':
    rc=0
    for p in sys.argv[1:]:
        print('###',p)
        for l in run(p): print(l); rc|=l.startswith('FAIL')
    sys.exit(rc)
