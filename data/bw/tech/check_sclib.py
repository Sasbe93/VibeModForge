import sys,json,re
sys.path.insert(0,'tools/lib/bw'); import sclib
J=json.load(open('bw_techtree.json')); N={int(k):v for k,v in J['unit_names'].items()}
src=open(sclib.__file__).read().split('# hero units')[0]
for line in src.splitlines():
    m=re.match(r'^([A-Z_,]+)=([\d,]+)$',line.strip())
    if m:
        for k,v in zip(m.group(1).split(','),m.group(2).split(',')): print(f'{k:12}{v:>4}  {N.get(int(v),"trigger group (Any unit/Men/Buildings)")}')
print('HEROES non-hero:',[(h,N[h]) for h in sorted(sclib.HEROES)])
print('UPG_MAX diffs:',[(i,sclib.UPG_MAX.get(i),next((g['max_level'] for g in J['upgrades'] if g['id']==i),0)) for i in range(61) if sclib.UPG_MAX.get(i,1)!=next((g['max_level'] for g in J['upgrades'] if g['id']==i),0)])
print('DEFAULT_RESEARCHED:',[(t,J['tech_names'][str(t)]) for t in sorted(sclib.DEFAULT_RESEARCHED)])
