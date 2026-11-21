#!/usr/bin/env python3
"""Fixtures for the checks destroy_target_morph_chain and side_objective_variety: each must FAIL on a bad case and
pass on a good one.   python3 tools/bw/selftest_side_and_morph.py [EXAMPLE.scx]      (exit 1 if a fixture misbehaves)
The side-objective fixtures copy a built map (default: output/example_mission/Example_Mission.scx) into a temp
folder as M1_/M2_ with hand-written design notes."""
import sys,os,shutil,tempfile
H=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,H); sys.path.insert(0,os.path.join(H,'..','lib','bw'))
import sclib
from sclib import Map,HATCH
import check_morph_chain as MC, check_side_objective_variety as SV
P1,P2=0,1; LOC=5; ownr=bytes([6,5,7,7,7,7,7,7])
def trig(players,conds,acts=()):
    r=bytearray(2400)
    for i,c in enumerate(conds): r[i*20:i*20+20]=c
    for i,a in enumerate(acts): r[320+i*32:352+i*32]=a
    for p in players: r[2372+p]=1
    return bytes(r)
def chain_case(trigs): return MC.analyze(MC.parse(b''.join(trigs)),ownr)
WIN=Map.act(1,flags=0x04); WAVE=Map.act(44,loc=LOC,player=P2,num=2,unit=37,flags=0x14)
def gone(units): return [Map.cond(3,loc=LOC,player=P2,qty=0,unit=u,cmp=10) for u in units]
def stands(u): return Map.cond(3,loc=LOC,player=P2,qty=1,unit=u,cmp=0)
ET=Map.cond(12,qty=240)
ok=True
def expect(name,res,want_fail):
    global ok
    F,W=res if isinstance(res,tuple) else (res,[])
    good=bool(F)==want_fail; ok&=good
    print(('pass ' if good else 'WRONG')+f" {name}: {'FAIL' if F else 'OK'}"+''.join('\n       '+f for f in (F or W)[:3]))
# --- destroy_target_morph_chain
expect('morph chain, victory on Hatchery+Lair only (old example)',chain_case([trig([P1],gone([131,132]),[WIN])]),True)
expect('morph chain, victory on Hatchery only',chain_case([trig([P1],gone([131]),[WIN])]),True)
expect('morph chain, Deaths of Hatchery only (human reward)',chain_case([trig([P1],[Map.cond(15,player=P2,qty=1,unit=131,cmp=0)],[WIN])]),True)
cls=type('M',(),{'cond':staticmethod(Map.cond)})()
expect('morph chain, victory from sclib target_gone (whole chain)',chain_case([trig([P1],Map.target_gone(cls,P2,HATCH,LOC),[WIN])]),False)
expect('morph chain, human trigger on stands copies for every chain type',chain_case([trig([P1],[ET,c],[WIN]) for c in Map.target_stands(cls,P2,HATCH,LOC)]),False)
expect('morph chain, Deaths alternatives for every chain type',chain_case([trig([P1],[c],[WIN]) for c in Map.target_killed(cls,P2,HATCH)]),False)
r=chain_case([trig([P2],[ET,stands(131)],[WAVE])]); expect('morph chain, computer wave on Hatchery only is a WARN, not a FAIL',r,False); ok&=bool(r[1])
# --- side_objective_variety
mp=sys.argv[1] if len(sys.argv)>1 else os.path.join(H,'..','..','output','example_mission','Example_Mission.scx')
def side_case(prev_note,note):
    d=tempfile.mkdtemp(prefix='sidefix_')
    for k,n in ((1,prev_note),(2,note)):
        shutil.copy(mp,f'{d}/M{k}_Fixture.scx'); open(f'{d}/M{k}_Design_Note.md','w').write(n)
    try:
        out=SV.run(f'{d}/M2_Fixture.scx'); return [l for l in out if l.startswith('FAIL')]
    finally: shutil.rmtree(d)
RESC='SIDE_OBJECTIVE: Reach the survey squad :: rescue :: units\n'
BURN='SIDE_OBJECTIVE: Burn the hatchery :: destroy :: resources\n'
expect('side objectives, destroy here and in the previous mission',side_case(BURN,RESC+BURN),True)
expect('side objectives, two destroy side objectives in one mission',side_case(RESC,RESC+BURN+'SIDE_OBJECTIVE: Kill the brood mother :: destroy :: tech\n'),True)
expect('side objectives, two resource rewards',side_case(RESC,RESC+'SIDE_OBJECTIVE: Hold the refinery :: hold :: resources\nSIDE_OBJECTIVE: Find the cache :: secret :: minerals\n'),True)
expect('side objectives, map has an optional objective but the note none',side_case(RESC,'(no side objective lines)\n'),True)
expect('side objectives, rescue after a destroy in the previous mission',side_case(BURN,RESC),False)
expect('side objectives, repeat with SIDE_OBJECTIVE_REPEAT_OK',side_case(BURN,RESC+BURN+'SIDE_OBJECTIVE_REPEAT_OK: the second strike finishes the first\n'),False)
print('ALL FIXTURES BEHAVE' if ok else 'FIXTURE MISMATCH'); sys.exit(0 if ok else 1)
