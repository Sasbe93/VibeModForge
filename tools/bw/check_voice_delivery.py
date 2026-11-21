#!/usr/bin/env python3
"""check_voice_delivery (StarCraft: Brood War): every voiced line carries delivery notes (rule voice_delivery;
VO markup v1, docs/voice-delivery-markup.md). Reads the Voice_Script*.md written by Map.write_voice_script() next to the
.scx (or the .md given directly). FAIL: no Voice_Script for a map that has voice WAVs, a line without a script, no
[emotion: ...], script words != subtitle words, a short clause / exclamation / dramatic beat without *stress* or pause
marker, a pause outside 0.1-0.6 s, a speaker without profile.
Usage: check_voice_delivery.py map.scx|Voice_Script_x.md [...]"""
import sys,os,glob
H=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.join(H,'..','lib'))
import voice_delivery as VD
def scripts_for(p):
    if p.endswith('.md'): return [p]
    d=os.path.dirname(os.path.abspath(p)); b=os.path.splitext(os.path.basename(p))[0]
    own=glob.glob(os.path.join(d,'Voice_Script_%s*.md'%b))
    return own or glob.glob(os.path.join(d,'Voice_Script*.md'))
def has_wav(p):
    """does the map play voice WAVs (staredit\\wav\\... strings in scenario.chk)?"""
    try:
        from eudplib.bindings._rust import mpqapi
        chk=bytes(mpqapi.MPQ.open(p).extract_file('staredit\\scenario.chk')); return b'staredit\\wav\\' in chk.lower()
    except Exception: return True          # cannot tell: assume voiced
def check(p):
    E=[]; F=scripts_for(p)
    if not F:
        if p.endswith('.md') or has_wav(p): E.append('no Voice_Script*.md next to %s (Map.write_voice_script)'%os.path.basename(p))
    rows=[]; prof={}
    for f in F:
        r,pr=VD.read_script_md(f); rows+=r; prof.update({k:v for k,v in pr.items() if v and v!='MISSING PROFILE'})
    for r in rows:
        for e in VD.check_line(r['text'],r['script']): E.append('%s %s: %s'%(r['id'],r['speaker'],e))
    for sp in sorted({r['speaker'] for r in rows}):
        if sp not in prof: E.append('speaker %r has no voice profile'%sp)
    for e in E[:30]: print('  FAIL '+e)
    print('%s RESULT %s (%d voiced lines, %d FAIL)'%(p,'FAIL' if E else 'OK',len(rows),len(E)))
    return E
if __name__=='__main__':
    bad=0
    for p in sys.argv[1:]: bad+=bool(check(p))
    sys.exit(1 if bad else 0)
