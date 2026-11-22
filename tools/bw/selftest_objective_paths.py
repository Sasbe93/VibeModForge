#!/usr/bin/env python3
"""Fixtures for objective_paths (predelivery check 51), including the TARGET_DURATION rules:
each new FAIL must fire on a bad note, and the official example must pass with a good one.
  python3 tools/bw/selftest_objective_paths.py [EXAMPLE.scx]     (exit 1 if a fixture misbehaves)
Copies a built map (default: output/example_mission/Example_Mission.scx) into a temp folder with handwritten
design notes. Set ATTACHED_SCX to a rescue map that should fail the early-win / empty-path rules to include
that fixture (the file is not part of the repository)."""
import sys,os,shutil,tempfile,glob
H=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,H)
import check_objective_paths as C

mp=sys.argv[1] if len(sys.argv)>1 else os.path.join(H,'..','..','output','example_mission','Example_Mission.scx')
ok=True

PATHS=('OBJECTIVE_PATHS: Destroy the Hatchery on the ridge :: start to the ridge, 100 tiles / 33 s :: three encounters :: a fight\n'
       'OBJECTIVE_PATHS: Reach the survey squad in the eastern ravine :: start to the camp, 77 tiles / 26 s :: two packs :: a fight\n')
GOOD=('TARGET_DURATION: 10 :: Easy 14 / Hard 8 :: Destroy the Hatchery on the ridge=6; Reach the survey squad=4\n'+PATHS)
HUGE=('TARGET_DURATION: 80 :: Easy 90 / Hard 70 :: Destroy the Hatchery on the ridge=40; Reach the survey squad=40\n'+PATHS)
INCOMPLETE='TARGET_DURATION: 10\n'+PATHS
EASY_ONLY=PATHS+'OBJECTIVE_PATHS_EASY_OK: this is a tutorial walk\n'
EASY_AND_DUR=GOOD+'OBJECTIVE_PATHS_EASY_OK: this is a tutorial walk\n'

def case(note, src=None):
    d=tempfile.mkdtemp(prefix='opath_')
    src=src or mp
    ext=os.path.splitext(src)[1]
    dest=os.path.join(d,'Fixture'+ext)
    shutil.copy(src,dest)
    open(os.path.join(d,'Design_Note_Fixture.md'),'w').write(note)
    try:
        out=C.run(dest)
        return [l for l in out if l.startswith('FAIL')], out
    finally:
        shutil.rmtree(d)

def expect(name, fails, want_fail):
    global ok
    good=bool(fails)==want_fail; ok&=good
    preview='; '.join((fails or ['OK'])[:1])
    print(('pass ' if good else 'WRONG')+f" {name}: {'FAIL' if fails else 'OK'}  {preview[:200]}")

if not os.path.isfile(mp):
    print('MISSING built example at', mp, '- build it first (python3 tools/bw/example_mission.py --no-checks)'); sys.exit(1)

expect('missing TARGET_DURATION (OBJECTIVE_PATHS present)', case(PATHS)[0], True)
expect('incomplete TARGET_DURATION (only Normal minutes)', case(INCOMPLETE)[0], True)
expect('budget far above the walk+fight estimate (40 min each)', case(HUGE)[0], True)
expect('official example numbers (10 min, budgets 6 and 4)', case(GOOD)[0], False)
expect('EASY_OK does not waive a missing TARGET_DURATION', case(EASY_ONLY)[0], True)
expect('EASY_OK waives difficulty when TARGET_DURATION is complete', case(EASY_AND_DUR)[0], False)

att=os.environ.get('ATTACHED_SCX','')
if att and os.path.isfile(att):
    # declare a duration so the early-win / empty-path rules can fire (missing duration would already FAIL)
    note=('TARGET_DURATION: 15 :: Easy 20 / Hard 12 :: Rescue Holt=8; Burn the Hatchery at the nest=7\n'
          'OBJECTIVE_PATHS: Rescue Holt :: start to Crash and back :: no threats on the road :: empty walk\n'
          'OBJECTIVE_PATHS: Burn the Hatchery at the nest :: start to the nest :: one encounter at the nest :: far corner\n')
    fails,_=case(note, src=att)
    expect('rescue map: main completable before the first wave / too few encounters', fails, True)
else:
    print('skip  attached rescue map not present (optional fixture)')

print('ALL FIXTURES BEHAVE' if ok else 'FIXTURE MISMATCH'); sys.exit(0 if ok else 1)
