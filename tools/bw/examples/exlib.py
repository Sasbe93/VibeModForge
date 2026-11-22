"""Shared build-and-check pipeline for the BW example missions in tools/bw/examples/ (see docs/bw-example-missions.md).

STRUCTURE ONLY: the examples show how a mission is built (pipeline, design-note sections, trigger, voice and check
conventions). Never copy an example's mission design (objective, map layout, start setup, enemy, story, rewards)."""
import sys, os, json, shutil, subprocess
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
os.chdir(ROOT)
for p in ('tools/lib/bw', 'tools/bw', 'tools/lib'):
    if p not in sys.path: sys.path.insert(0, p)
import sclib

def paths(slug, name):
    out = os.path.join(ROOT, 'output', 'examples', slug); os.makedirs(out, exist_ok=True)
    return out, os.path.join(out, name + '.scx')

def finish(m, slug, name, title, desc, proofs, highground=None, gas_ok=None):
    """placement autofix, save, voice script, design note copy, minimap and routes PNG, then (unless --no-checks) the
    placement check, the trigger simulation (proofs = trigsim scenarios) and the full predelivery check. Exit code 1 on FAIL."""
    import placecheck, path_tool
    out, MAP = paths(slug, name)
    log = []; placecheck.autofix(m, log=log.append); print('placement autofix:', log[-1] if log else '-')
    m.save(MAP, title, desc)
    m.write_voice_script(os.path.join(out, f'Voice_Script_{name}.md'), title)
    print('validate', sclib.validate(MAP)); print('timelines', m.check_timelines())
    shutil.copy(os.path.join(ROOT, 'tools', 'bw', 'examples', f'{slug}_Design_Note.md'), os.path.join(out, f'Design_Note_{name}.md'))
    base = os.path.splitext(MAP)[0]
    if highground: json.dump({'bases': highground}, open(base + '.highground_ok.json', 'w'), indent=1)
    if gas_ok: json.dump({'sites': gas_ok}, open(base + '.gas_ok.json', 'w'), indent=1)
    sclib.render(MAP, os.path.join(out, name + '_minimap.png'), {}, title)
    path_tool.analyze(MAP, png=os.path.join(out, name + '_routes.png'))
    print('wrote', MAP)
    if '--no-checks' in sys.argv: return MAP
    rc = 0
    errs, stats = placecheck.check(MAP, m.ts); print('placecheck', stats, errs[:8]); rc |= bool(errs)
    import trigsim
    if proofs: trigsim.prove(MAP, proofs)
    r = subprocess.run([sys.executable, 'tools/bw/predelivery_check.py', MAP],
                       env=dict(os.environ, SCMDRAFT_REAL=os.environ.get('SCMDRAFT_REAL', '0')))
    rc |= r.returncode
    print(f'EXAMPLE {name} RESULT:', 'FAIL' if rc else 'PASS (0 FAIL)'); sys.exit(rc)
