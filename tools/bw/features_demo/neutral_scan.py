import sys,glob,collections,struct,json
sys.path.insert(0,'tools/bw');import check_ranked_bw as c
RES={176,177,178,188,214}
out={}
fs=sorted(set(glob.glob('external/refmaps/bw/set/*.scx')+glob.glob('external/refmaps/bw/s*/*.sc[xm]')))
seen=set()
for f in fs:
    n=f.split('/')[-1]
    try: s=c.sections(f);U=c.units(s)
    except Exception as e: print(n,'ERR',e);continue
    W,H=struct.unpack('<HH',s['DIM '])
    key=(n.split('.')[0].replace('(2)','').replace('(4)','').replace('(3)','').strip()[:8])
    if key in seen: continue
    seen.add(key)
    neu=[u for u in U if u['o']==11 and u['id'] not in RES]
    lowmin=[u for u in U if u['id'] in (176,177,178) and u.get('res',9999)<=64]
    allk=list(U[0].keys()) if U else []
    out[n]=dict(size=(W,H),neutral=[(u['id'],u['x']//32,u['y']//32,u.get('hp'),u.get('res')) for u in neu],lowmin=len(lowmin))
    print(n,W,H,'keys',allk,'neutral',collections.Counter(u['id'] for u in neu),'lowmin',len(lowmin))
json.dump(out,open('data/reference_metrics/bw/neutral_scan.json','w'),indent=0)
