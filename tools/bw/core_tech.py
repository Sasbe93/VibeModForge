"""Check 23: every unit/building available to a human player (placed or enabled) keeps its core abilities
(tech/bw_techtree.json core_abilities): enabled AND (researched, or its research building is available)."""
import json
J=json.load(open('data/bw/tech/bw_techtree.json'))
CORE={int(k):v for k,v in J['core_abilities'].items() if not k.startswith('_')}
T={t['id']:t for t in J['techs']}; UN={int(k):v for k,v in J['unit_names'].items()} if isinstance(J['unit_names'],dict) else dict(enumerate(J['unit_names']))
def check(S):
    puni=S['PUNI']; ptex=S['PTEx']; ownr=S['OWNR']; U=S['UNIT']; bad=[]
    placed=[(U[i+16],int.from_bytes(U[i+8:i+10],'little')) for i in range(0,len(U),36)]
    for p in range(8):
        if ownr[p]!=6: continue
        ud=puni[13*228+p*228:13*228+p*228+228]; gu=puni[12*228:13*228]
        avail={i for i in range(228) if (gu[i] if ud[i] else puni[p*228+i])}|{u for o,u in placed if o==p}
        df=lambda i: ptex[12*44*2+44*2+p*44+i]
        tav=lambda i: ptex[12*44*2+i] if df(i) else ptex[p*44+i]
        tres=lambda i: ptex[12*44*2+44+i] if df(i) else ptex[12*44+p*44+i]
        for u,ts in CORE.items():
            if u not in avail: continue
            for t in ts:
                d=T[t]; nm=f'P{p+1} {UN.get(u,u)}: {d["name"]}'
                if not tav(t): bad.append(nm+' disabled')
                elif not tres(t):
                    if d['researched_by_default']: bad.append(nm+' must be pre-researched (free in BW)')
                    elif d['researched_at'] not in avail: bad.append(nm+f' not researched and {UN.get(d["researched_at"])} unavailable')
    return bad
