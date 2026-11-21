#!/usr/bin/env python3
"""check_tech.py <map.scx|scenario.chk> ... : validates tech availability of human players against bw_techtree.json.
Also usable as library: check_sections(sections_dict) (e.g. from sclib map via m.save() chk bytes -> parse_chk)."""
import sys, json, struct, os, tempfile
HERE=os.path.dirname(os.path.abspath(__file__)); J=json.load(open(f'{HERE}/bw_techtree.json'))
UN={int(k):v for k,v in J['unit_names'].items()}; UPN={int(k):v for k,v in J['upgrade_names'].items()}; TNN={int(k):v for k,v in J['tech_names'].items()}
UNITS={u['id']:u for u in J['units']}; UPGS={g['id']:g for g in J['upgrades']}; TECHS={t['id']:t for t in J['techs']}
EQ={int(k):v for k,v in J['equivalents'].items()}
RACE={0:'Zerg',1:'Terran',2:'Protoss'}
ADDON_PARENT={107:106,108:106,120:113,115:114,117:116,118:116}
def parse_chk(b):
    S={};o=0
    while o+8<=len(b):
        k=b[o:o+4].decode('latin1'); n=struct.unpack_from('<i',b,o+4)[0]; S[k]=b[o+8:o+8+n] if k not in S else b[o+8:o+8+n]; o+=8+n
    return S
def read_scx(path):
    if path.endswith('.chk'): return parse_chk(open(path,'rb').read())
    from eudplib.bindings._rust import mpqapi
    m=mpqapi.MPQ.open(path); d=tempfile.mkdtemp(); f=os.path.join(d,'s.chk')
    r=m.extract_file('staredit\\scenario.chk') if True else None
    if isinstance(r,(bytes,bytearray)): return parse_chk(bytes(r))
    raise RuntimeError('cannot extract')
def units_of(S):
    U=S.get('UNIT',b''); return [dict(zip(('x','y','id','owner'),(struct.unpack_from('<HHH',U,i+4)+(U[i+16],)))) for i in range(0,len(U)-35,36)]
def check_sections(S,label=''):
    out=[]; ownr=S['OWNR']; side=S['SIDE']
    puni=S['PUNI']; pupx=S.get('PUPx'); ptex=S.get('PTEx'); placed=units_of(S)
    gu=puni[12*228:13*228]
    for p in range(8):
        if ownr[p]!=6: continue
        race=RACE.get(side[p],'?'); own={u['id'] for u in placed if u['owner']==p}
        ud=puni[13*228+p*228:13*228+p*228+228]
        avail={i for i in range(228) if (gu[i] if ud[i] else puni[p*228+i])}
        def upmax(i):
            if pupx is None: return 0
            usedef=pupx[12*61*2+61*2+p*61+i]; return pupx[12*61*2+i] if usedef else pupx[p*61+i]
        def tav(i):
            usedef=ptex[12*44*2+44*2+p*44+i]; return ptex[12*44*2+i] if usedef else ptex[p*44+i]
        def tres(i):
            usedef=ptex[12*44*2+44*2+p*44+i]; return ptex[12*44*2+44+i] if usedef else ptex[12*44+p*44+i]
        memo={}
        def have(b,stack=()):
            """b obtainable: pre-placed (or upgraded form placed) or buildable with all prereqs obtainable"""
            if b in own or any(e in own for e in EQ.get(b,[])): return True
            if b==130 and 45 in avail and any(q['id']==106 for q in placed) and have(138,stack+(b,)): return True  # infest an enemy CC with a Queen
            if b in memo: return memo[b]
            if b in stack: return False
            ok=False
            for c in [b]+EQ.get(b,[]):
                d=UNITS.get(c)
                if d and c in avail and d['kind']!='unit' and all(have(r,stack+(b,)) for r in d['requires']) and any(have(x,stack+(b,)) or x in (41,64,7) and (x in own or x in avail) for x in d['produced_by']):
                    ok=True;break
            memo[b]=ok; return ok
        def obtain_unit(u):
            if u in own: return True
            d=UNITS.get(u)
            if not d or u not in avail: return False
            if d['how'].startswith('tech:') or d['how']=='auto': return True
            prod_ok=any(x==35 and have(131) or have(x) or (UNITS.get(x,{}).get('kind')=='unit' and obtain_unit(x)) for x in d['produced_by'])
            if u==103 and not (tav(32) and (tres(32) or have(135))): return False
            return prod_ok and all(have(r) for r in d['requires'])
        R=[]
        # enabled units/buildings whose prereqs are missing
        for u,d in UNITS.items():
            if d['race']!=race or u not in avail or d['how'] in('auto',) or d['how'].startswith('tech:'): continue
            if u in own and d['kind']!='unit': continue
            miss=[UN[r] for r in d['requires'] if not have(r)]+([] if any(x==35 and have(131) or have(x) or obtain_unit(x) for x in d['produced_by']) else ['producer '+'/'.join(UN[x] for x in d['produced_by'])])
            if miss: R.append(f"UNIT {u} {UN[u]} enabled but missing: {', '.join(miss)}")
        haveunits={u for u in UNITS if UNITS[u]['kind']=='unit' and obtain_unit(u)}|{u['id'] for u in placed if u['owner']==p}
        for i in range(61):
            mx=upmax(i)
            if not mx: continue
            g=UPGS.get(i)
            if not g: R.append(f"UPG {i} {UPN.get(i)} max={mx}: unknown/unused upgrade id"); continue
            if g['race']!=race: R.append(f"UPG {i} {g['name']} max={mx}: other race ({g['race']})")
            if mx>g['max_level']: R.append(f"UPG {i} {g['name']} max={mx} > official {g['max_level']}")
            miss=[UN[r] for r in [g['researched_at']]+g['requires'] if not have(r)]
            if miss: R.append(f"UPG {i} {g['name']} researchable but missing: {', '.join(miss)}")
            for L,rq in g['level_requires'].items():
                if mx>=int(L) and not all(have(r) for r in rq): R.append(f"UPG {i} {g['name']} level {L} needs {UN[rq[0]]} (not obtainable)")
            if not set(g['benefits'])&haveunits: R.append(f"UPG {i} {g['name']} benefits no available unit")
        for fam in J['families']:
            lv={i:upmax(i) for i in fam if UPGS[i]['race']==race}
            if len(set(lv.values()))>1 and any(lv.values()): R.append('UPG family mismatch: '+', '.join(f'{UPN[i]}={v}' for i,v in lv.items()))
        for i in range(44):
            if not tav(i) or tres(i) and TECHS.get(i,{}).get('researched_at') is None: 
                if tav(i) and i in TECHS and TECHS[i]['race']==race and not set(TECHS[i]['users'])&haveunits and TECHS[i]['researched_at'] is None: pass
                continue
            t=TECHS.get(i)
            if not t: R.append(f"TECH {i} {TNN.get(i)}: unknown/unused tech id"); continue
            if t['race']!=race: continue
            if not tres(i) and t['researched_at'] is not None:
                miss=[UN[r] for r in [t['researched_at']]+t['requires'] if not have(r)]
                if miss: R.append(f"TECH {i} {t['name']} researchable but missing: {', '.join(miss)}")
                if not set(t['users'])&haveunits: R.append(f"TECH {i} {t['name']} researchable but no unit can use it")
        # core_tech : units that only make sense burrowed (Lurker) need Burrow researched or researchable
        BURROW_ONLY={103:'Lurker'}
        bt=TECHS.get(11,{})
        burrow_ok=bool(tav(11)) and (bool(tres(11)) or (bt.get('researched_at') is not None and have(bt['researched_at'])))
        for bu,bn in BURROW_ONLY.items():
            if (bu in haveunits) and not burrow_ok: R.append(f"TECH core_tech {bn} obtainable but Burrow (tech 11) neither researched nor researchable: enable Burrow or remove {bn}/Lurker Aspect")
        # unknown placed ids
        for u in placed:
            if u['id']>227: R.append(f"PLACED unknown unit id {u['id']} at {u['x']},{u['y']}")
        out.append((p,race,R))
    # detached addons (all players)
    A=[]
    for a in placed:
        if a['id'] in ADDON_PARENT:
            par=[q for q in placed if q['id']==ADDON_PARENT[a['id']] and q['owner']==a['owner'] and q['x']+96==a['x'] and q['y']+16==a['y']]
            if not par:
                near=min((q for q in placed if q['id']==ADDON_PARENT[a['id']] and q['owner']==a['owner']),key=lambda q:abs(q['x']-a['x'])+abs(q['y']-a['y']),default=None)
                A.append(f"ADDON {UN[a['id']]} P{a['owner']+1} at px({a['x']},{a['y']}) detached"+(f"; nearest {UN[near['id']]} at ({near['x']},{near['y']}) -> expected ({near['x']+96},{near['y']+16})" if near else '; no parent'))
    return out,A
def main(paths):
    for path in paths:
        S=read_scx(path); res,A=check_sections(S)
        print(f'### {os.path.basename(path)}')
        for p,race,R in res:
            print(f'  P{p+1} ({race}): {len(R)} finding(s)'); [print('   -',r) for r in R]
        for a in A: print('  -',a)
        if not A: print('  addons: ok')
if __name__=='__main__': main(sys.argv[1:])
