#!/usr/bin/env python3
"""Fixtures for objective_shortcuts, enemy_base_pressure and tech_restriction (predelivery checks 52-54):
each check must FAIL on a bad case and pass on the official example.
  python3 tools/bw/selftest_t1025_checks.py [EXAMPLE.scx]      (exit 1 if a fixture misbehaves)
Uses a built Outpost Nine (default: output/example_mission/Example_Mission.scx) in a temp folder with its design note,
and patches the loaded model (no binary map edits):
  - shortcuts: anti-air removed from the air line -> the Barracks lift-off reaches the ravine camp unopposed;
  - pressure: the second Hatchery removed -> the ridge Hatchery feeds the waves and the town AI alone (exempt while it
    is the victory target; FAIL once the victory link is removed);
  - tech: the Unit/Upgrade/Tech settings replaced by the full default tree.
Set ATTACHED_SCX to an outside map that should fail all three checks (that map is not part of the repository)."""
import sys,os,shutil,tempfile,re
H=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,H); sys.path.insert(0,os.path.join(H,'..','lib','bw'))
import mission_model as MM
import check_objective_shortcuts as SC, check_enemy_base_pressure as BP, check_tech_restriction as TR
import sclib

mp=sys.argv[1] if len(sys.argv)>1 else os.path.join(H,'..','..','output','example_mission','Example_Mission.scx')
if not os.path.isfile(mp):
    print('MISSING built example at',mp,'- build it first (python3 tools/bw/example_mission.py --no-checks)'); sys.exit(1)
note_src=os.path.join(H,'..','..','templates','Design_Note_example_bw_mission.md')
GOOD=open(note_src,encoding='utf8').read()
ok=True

def model(note, src=mp):
    d=tempfile.mkdtemp(prefix='t1025_'); dest=os.path.join(d,'Fixture'+os.path.splitext(src)[1])
    shutil.copy(src,dest)
    if note is not None: open(os.path.join(d,'Design_Note_Fixture.md'),'w',encoding='utf8').write(note)
    M=MM.Model(dest); shutil.rmtree(d); return dest,M

def fails(out): return [l for l in out if l.startswith('FAIL')]

def expect(name, out, want_fail):
    global ok
    f=fails(out); good=bool(f)==want_fail; ok&=good
    print(('pass ' if good else 'WRONG')+f" {name}: {'FAIL' if f else 'OK'}  {(f or out or ['-'])[0][:180]}")

strip=lambda key: '\n'.join(l for l in GOOD.splitlines() if not l.strip().startswith(key))

# objective_shortcuts
p,M=model(GOOD); expect('shortcuts: official example', SC.run(p,M), False)
p,M=model(strip('OBJECTIVE_SHORTCUTS')); expect('shortcuts: note without OBJECTIVE_SHORTCUTS', SC.run(p,M), True)
orig=SC.aa_threats; SC.aa_threats=lambda v: []
try:
    p,M=model(GOOD); expect('shortcuts: no anti-air on the air line (lift-off open)', SC.run(p,M), True)
    p,M=model(GOOD+'\nSHORTCUT_OK: Ravine Camp :: lift-off :: fixture accepts it\nSHORTCUT_OK: Ravine Camp :: flyer :: fixture\nSHORTCUT_OK: Ravine Camp :: transport :: fixture\n')
    expect('shortcuts: open lift-off accepted with SHORTCUT_OK', SC.run(p,M), False)
finally: SC.aa_threats=orig

# enemy_base_pressure
p,M=model(GOOD); expect('pressure: official example', BP.run(p,M), False)
def one_base(M):
    hs=[u for u in M.v.U if u['o'] in M.v.enemy and u['id'] in MM.HALLS]
    far=max(hs,key=lambda u: u['y']); M.v.U=[u for u in M.v.U if u is not far]
p,M=model(GOOD); one_base(M); expect('pressure: one Hatchery feeds everything but it is the victory target', BP.run(p,M), False)
orig=BP.victory_bases; BP.victory_bases=lambda M: set()
try:
    p,M=model(GOOD); one_base(M); expect('pressure: one Hatchery feeds waves and AI, not the objective', BP.run(p,M), True)
    p,M=model(GOOD+'\nPRESSURE_SINGLE_OK: fixture, the base is the climax\n'); one_base(M)
    expect('pressure: single base accepted with PRESSURE_SINGLE_OK', BP.run(p,M), False)
finally: BP.victory_bases=orig

# tech_restriction
p,M=model(GOOD); expect('tech: official example (early)', TR.run(p,M), False)
p,M=model(strip('TECH_LEVEL')); expect('tech: note without TECH_LEVEL', TR.run(p,M), True)
def full(M):
    pupx,ptex,puni,ptec=sclib.tech_sections(None); M.S['PUPx']=pupx; M.S['PTEx']=ptex; M.S['PUNI']=puni
p,M=model(GOOD); full(M); expect('tech: full tree with TECH_LEVEL early', TR.run(p,M), True)
p,M=model(re.sub(r'TECH_LEVEL:.*',"TECH_LEVEL: mid :: chapter 2 :: fixture",GOOD)); full(M); expect('tech: full tree with TECH_LEVEL mid', TR.run(p,M), True)
p,M=model(re.sub(r'TECH_LEVEL:.*',"TECH_LEVEL: full :: finale :: everything for the last stand",GOOD)); full(M); expect('tech: full tree declared full with a reason', TR.run(p,M), False)

att=os.environ.get('ATTACHED_SCX','')
if att and os.path.isfile(att):
    p,M=model(None,att)
    for n,C in (('shortcuts',SC),('pressure',BP),('tech',TR)): expect(f'attached map: {n}', C.run(p,M), True)
else:
    print('skip attached-map fixture (set ATTACHED_SCX=<map.scx>)')
print('SELFTEST', 'PASS' if ok else 'FAIL'); sys.exit(0 if ok else 1)
