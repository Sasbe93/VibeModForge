#!/usr/bin/env python3
"""Does the map open in ScmDraft 2?   python3 tools/bw/check_scmdraft_open.py [--real] MAP.scx [...]
Exits 1 on any FAIL. Run from the repo root.

Static part (always; each line is named after what it verifies):
  chk_required_sections, chk_section_sizes, dd2_named_doodads (the root cause of the M7 load failure):
  - the MPQ opens and holds staredit\\scenario.chk; the sections ScmDraft reads are present
  - every DD2 doodad id exists in the tileset's NAMED doodad groups (cv5 group-name != 0). ScmDraft builds its
    doodad table only from named groups; one unknown id aborts the whole load with
    'Could not locate information in the tileset for a particular (Type N)' -> 'Could not load the map'.
Real part (--real, or automatically when a harness is found): opens the map in the real ScmDraft 2 under
wine (tools/bw/scmdraft_harness, $SCMDRAFT_HARNESS or external/scmdraft_harness) and requires
'(ENGINE) Loaded map'. Without a harness the real part is reported as skipped (static result only)."""
import sys,os,struct,subprocess
ROOT=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..'))
sys.path.insert(0,os.path.join(ROOT,'tools','lib','bw'))
_cwd=os.getcwd(); os.chdir(ROOT)      # sclib loads repo data with relative paths
import sclib
os.chdir(_cwd)
from eudplib.bindings._rust import mpqapi
NEED=['VER ','DIM ','ERA ','OWNR','SIDE','MTXM','UNIT','MRGN','TRIG','FORC']
# fixed section sizes (staredit.net Scenario.chk wiki 'Validation'); ScmDraft rejects e.g. a 4000-byte UNIS
# ('Could not load the vanilla unit settings'), even though StarCraft itself plays the map
SIZE={'VER ':(2,),'OWNR':(12,),'ERA ':(2,),'DIM ':(4,),'SIDE':(12,),'PUNI':(5700,),'UPGR':(1748,),'PTEC':(912,),
      'UPRP':(1280,),'MRGN':(1280,5100),'SPRP':(4,),'UNIS':(4048,),'UPGS':(598,),'TECS':(216,),'COLR':(8,),'CRGB':(32,),
      'PUPx':(2318,),'PTEx':(1672,),'UNIx':(4168,),'UPGx':(794,),'TECx':(396,)}
MULT={'UNIT':36,'THG2':10,'TRIG':2400,'MBRF':2400}
def sections(chk):
    S={}; i=0
    while i+8<=len(chk):
        n=chk[i:i+4].decode('latin1'); l=struct.unpack_from('<i',chk,i+4)[0]
        if l<0 or i+8+l>len(chk): break      # stacked/protected sections: keep what we have
        S[n]=chk[i+8:i+8+l]; i+=8+l
    return S
def harness():
    for h in (os.environ.get('SCMDRAFT_HARNESS'),os.path.join(ROOT,'external','scmdraft_harness')):
        if h and os.path.exists(os.path.join(h,'scmd','app','ScmDraft 2.exe')) and os.path.isdir(os.path.join(h,'wineprefix')): return h
def static(path):
    R=[]
    try: chk=bytes(mpqapi.MPQ.open(path).extract_file('staredit\\scenario.chk'))
    except Exception as e: return [f'FAIL scmdraft_open: MPQ/scenario.chk unreadable ({e!r})']
    S=sections(chk); miss=[n.strip() for n in NEED if n not in S]+([] if ('STR ' in S or 'STRx' in S) else ['STR/STRx'])
    R.append(('FAIL' if miss else 'OK  ')+f' chk_required_sections: CHK sections ScmDraft reads are present {miss or ""}')
    wrong=[f'{n.strip()}={len(S[n])} (needs {"/".join(map(str,v))})' for n,v in SIZE.items() if n in S and len(S[n]) not in v]
    wrong+=[f'{n.strip()}={len(S[n])} (not a multiple of {k})' for n,k in MULT.items() if n in S and len(S[n])%k]
    if 'FORC' in S and len(S['FORC'])>20: wrong.append(f'FORC={len(S["FORC"])} (max 20)')
    R.append(('FAIL' if wrong else 'OK  ')+f' chk_section_sizes: fixed-size CHK sections have their exact size {wrong or ""}')
    ts=struct.unpack('<H',S['ERA '][:2])[0]&7 if 'ERA ' in S else 0
    dd=S.get('DD2 ',b''); bad={}
    if len(dd)%8: R.append(f'FAIL dd2_named_doodads: DD2 size {len(dd)} is not a multiple of 8')
    named=sclib.named_doodad_ids(ts)
    for i in range(0,len(dd)-len(dd)%8,8):
        did=struct.unpack_from('<H',dd,i)[0]
        if did not in named: bad[did]=bad.get(did,0)+1
    n=len(dd)//8
    R.append(('FAIL' if bad else 'OK  ')+f' dd2_named_doodads: every DD2 doodad id is a named doodad of the tileset ({sclib.TSNAMES[ts]}, {n} doodads)'
             +(f' -- {sum(bad.values())} entries with unknown ids {sorted(bad)[:12]}: ScmDraft refuses to load the map' if bad else ''))
    return R
def real(path,h):
    env=dict(os.environ,HARNESS=h)
    try: out=subprocess.run([os.path.join(ROOT,'tools','bw','scmdraft_harness','openmap.sh'),path],capture_output=True,text=True,env=env,timeout=240).stdout
    except subprocess.TimeoutExpired: return ['FAIL scmdraft_open (real ScmDraft 2): timed out']
    ok=out.strip().endswith('SCMDRAFT_OPEN OK')
    why=[l.split('Warning::')[-1][:110] for l in out.splitlines() if 'Could not' in l and 'sprite' not in l][:3]
    return [('OK  ' if ok else 'FAIL')+' scmdraft_open (real ScmDraft 2 0.9.10 under wine): '+('loaded' if ok else f'NOT loaded {why}')]
def run(path,force_real=False):
    R=static(path); h=harness()
    if h and (force_real or os.environ.get('SCMDRAFT_REAL','1')!='0'): R+=real(path,h)
    elif force_real: R.append('FAIL scmdraft_open: --real requested but no harness (see tools/bw/scmdraft_harness/README.md)')
    else: R.append('OK   scmdraft_open (real run skipped: '+('SCMDRAFT_REAL=0' if h else 'no ScmDraft harness installed')+'; static result only)')
    return R
if __name__=='__main__':
    a=sys.argv[1:]; fr='--real' in a; a=[x for x in a if x!='--real']; rc=0
    for p in a:
        print('###',p)
        for l in run(p,fr): print(l); rc|=l.startswith('FAIL')
    sys.exit(rc)
