#!/usr/bin/env python3
"""destroy_target_morph_chain: objective conditions on a building that can morph cover the whole morph chain.
   python3 tools/bw/check_morph_chain.py MAP.scx [...]      (exit 1 on FAIL)

BW semantics: a morphing building (Hatchery -> Lair -> Hive, Creep Colony -> Sunken/Spore Colony, Spire -> Greater
Spire) changes its unit type in place. The engine moves the unit count from the old type to the new one and records no
death (OpenBW bwgame.h, morph_unit: increment_unit_counts(u,-1); reinitialize_unit_type; increment_unit_counts(u,1);
no kill path). So:
  - 'Bring/Command exactly 0 Hatchery' becomes true when the Hatchery morphs into a Lair (a false 'destroyed');
  - 'Bring/Command at least 1 Hatchery' becomes false (waves gated on 'the hatchery stands' stop);
  - 'Deaths of Hatchery' never fires when the target dies after it morphed (it dies as a Lair or Hive).
Rules:
  gone   a Bring/Command condition 'exactly 0' (or 'at most 0') of a chain type needs the same condition for every later
         type of the chain in the SAME trigger (same player, same location)
  stands a Bring/Command 'at least N' or a Deaths condition on a chain type needs sibling triggers (same owners, same
         other conditions) with the same condition for every later chain type (BW conditions are AND only)
  lift   'Bring exactly 0' of a Terran building that can lift off at a location: WARN (it can fly away)
Human-owned triggers (objectives, victory, rewards) FAIL; computer-owned triggers (e.g. waves gated on a base) WARN.
Generator: sclib Map.target_gone / target_stands / target_killed + T_each."""
import sys,os,struct
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from check_ally_vision import sections
CHAIN={131:(131,132,133),132:(132,133),143:(143,146,144),141:(141,137)}
NAMES={131:'Hatchery',132:'Lair',133:'Hive',143:'Creep Colony',146:'Sunken Colony',144:'Spore Colony',141:'Spire',137:'Greater Spire'}
LIFT={106:'Command Center',111:'Barracks',113:'Factory',114:'Starport',122:'Engineering Bay',116:'Science Facility'}
def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def u16(b,o): return struct.unpack_from('<H',b,o)[0]
def parse(T):
    out=[]
    for t in range(0,len(T)-len(T)%2400,2400):
        r=T[t:t+2400]
        c=[r[i*20:i*20+20] for i in range(16) if r[i*20+15]]
        out.append((c,bytes(r[2372:2400])))
    return out
def gone(c): return c[15] in (2,3) and u32(c,8)==0 and c[14] in (1,10)
def stands(c): return (c[15] in (2,3) and c[14]==0 and u32(c,8)>=1) or (c[15]==15 and c[14] in (0,10) and u32(c,8)>=1)
def same_but_unit(a,b,unit):
    return a[15]==b[15] and a[14]==b[14] and u32(a,0)==u32(b,0) and u32(a,4)==u32(b,4) and u32(a,8)==u32(b,8) and u16(b,12)==unit
def analyze(trigs,ownr):
    hum={p for p in range(8) if ownr[p]==6}
    F=[]; W=[]
    for i,(conds,pl) in enumerate(trigs):
        human=any(pl[p] for p in hum) or pl[17]
        sink=F if human else W
        for c in conds:
            u=u16(c,12)
            if gone(c) and c[15]==3 and u in LIFT:
                W.append(f"trig{i}: 'exactly 0 {LIFT[u]}' at a location - a Terran building can lift off and leave it without dying (use Command, or Deaths)")
            if u not in CHAIN: continue
            later=CHAIN[u][1:]
            if gone(c):
                miss=[t for t in later if not any(same_but_unit(c,d,t) for d in conds)]
                if miss: sink.append(f"trig{i}: 'exactly 0 {NAMES[u]}' without {', '.join(NAMES[t] for t in miss)} in the same trigger - fires when the {NAMES[u]} morphs")
            elif stands(c):
                rest=sorted(bytes(d) for d in conds if d is not c)
                miss=[]
                for t in later:
                    ok=False
                    for j,(c2,pl2) in enumerate(trigs):
                        if j==i or pl2!=pl: continue
                        hit=[d for d in c2 if same_but_unit(c,d,t)]
                        if hit and sorted(bytes(d) for d in c2 if d is not hit[0])==rest: ok=True; break
                    if not ok: miss.append(t)
                if miss:
                    what='Deaths of' if c[15]==15 else 'at least 1'
                    sink.append(f"trig{i}: '{what} {NAMES[u]}' has no sibling trigger for {', '.join(NAMES[t] for t in miss)} - "+('never fires once the target has morphed' if c[15]==15 else 'stops being true when the target morphs'))
    return F,W
def run(path):
    from eudplib.bindings._rust import mpqapi
    S=sections(bytes(mpqapi.MPQ.open(path).extract_file('staredit\\scenario.chk')))
    F,W=analyze(parse(S.get('TRIG',b'')),S['OWNR'])
    out=[('FAIL' if F else 'OK  ')+' destroy_target_morph_chain: conditions on morphable buildings cover the whole morph chain'+''.join('\n     - '+f for f in F[:10])]
    if W: out.append('WARN destroy_target_morph_chain:'+''.join('\n     - '+w for w in W[:10]))
    return out
if __name__=='__main__':
    rc=0
    for p in sys.argv[1:]:
        print('###',p)
        for l in run(p): print(l); rc|=l.startswith('FAIL')
    sys.exit(rc)
