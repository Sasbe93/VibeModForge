"""Check: every armed unit (placed in UNIT or buildable/available via PUNI) must deal >0 base damage.
Weapon damage in UNIS/UNIx is indexed by WEAPON id (weapons.dat), and only applies to units whose
use-default flag is 0. Defaults from tech/bw_weapons.json (BWAPI = units.dat/weapons.dat).
Also checks UNIS (vanilla, 100 weapons) and UNIx (BW, 130 weapons) agree."""
import struct,json,os,sys,io,contextlib
DB=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','data','bw','tech','bw_weapons.json')))
WP={int(k):v for k,v in DB['weapons'].items()}; UN={int(k):v for k,v in DB['units'].items()}
def read(path):
    import eudplib as e
    with contextlib.redirect_stdout(io.StringIO()): e.LoadMap(path)
    from eudplib.core.mapdata import mapdata as md
    c=md.GetChkTokenized(); return {k:c.getsection(k) for k in ['UNIT','PUNI','UNIS','UNIx','OWNR']}
def parse(sec,nw):
    use=sec[:228]; o=228+228*4+228*2+228+228*2*4
    return use,struct.unpack_from(f'<{nw}H',sec,o),struct.unpack_from(f'<{nw}H',sec,o+2*nw)
def check(path):
    S=read(path); fails=[]; info=[]
    U=S['UNIx']
    if len(U)!=4168: return [f'UNIx has {len(U)} bytes, must be 4168'],[]
    use,dmg,bon=parse(U,130)
    if S.get('UNIS') and len(S['UNIS'])!=4048: fails.append(f"UNIS has {len(S['UNIS'])} bytes, must be 4048 (UNIx must be 4168)")
    elif S.get('UNIS'):
        u2,d2,b2=parse(S['UNIS'],100)
        if u2!=use: fails.append('UNIS/UNIx use-default flags differ')
        for w in range(100):
            if (d2[w],b2[w])!=(dmg[w],bon[w]): fails.append(f'UNIS/UNIx weapon {w} {WP[w]["name"]}: {d2[w]}+{b2[w]} vs {dmg[w]}+{bon[w]}')
    own=S['OWNR']; units=set()
    for i in range(0,len(S['UNIT']),36):
        u=struct.unpack_from('<H',S['UNIT'],i+8)[0]; p=S['UNIT'][i+16]
        if u<228 and p<8: units.add(u)
    P=S.get('PUNI')   # 12x228 player avail, 228 global avail, 12x228 player use-global
    if P:
        for u in range(228):
            for p in range(8):
                if own[p] in (5,6) and (P[12*228+u] if P[13*228+p*228+u] else P[p*228+u]): units.add(u)
    units|={u for u in range(228) if not use[u]}   # every customised unit is checked, placed or not
    for u in sorted(units):
        for slot in ('ground','air'):
            w=UN[u][slot]
            if w is None: continue
            if use[u]: d,b,src=WP[w]['dmg'],WP[w]['bonus'],'default'
            else: d,b,src=dmg[w],bon[w],'UNIx'
            tag=f'{UN[u]["name"]} ({u}) {slot} weapon {w} {WP[w]["name"]}: {d}+{b} [{src}]'
            if d==0 and WP[w]['dmg']>0: fails.append('0 DAMAGE: '+tag)
            elif not use[u]: info.append(tag)
    # weapon shared: a customised weapon value that differs from default also changes every default unit using it
    for u in sorted(units):
        if not use[u]: continue
        for slot in ('ground','air'):
            w=UN[u][slot]
            if w is not None and dmg[w] and (dmg[w],bon[w])!=(WP[w]['dmg'],WP[w]['bonus']):
                info.append(f'note: weapon {w} set to {dmg[w]}+{bon[w]} (default {WP[w]["dmg"]}) only affects customised units; {UN[u]["name"]} keeps default')
    return fails,info
if __name__=='__main__':
    bad=0
    for p in sys.argv[1:]:
        f,i=check(p); print(('FAIL ' if f else 'PASS ')+os.path.basename(p))
        for x in f: print('   ',x)
        for x in i: print('    ok',x)
        bad|=bool(f)
    sys.exit(bad)
