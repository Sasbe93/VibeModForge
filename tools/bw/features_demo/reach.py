import sys;sys.path.insert(0,'tools/bw');import check_ranked_bw as c
s=c.sections(sys.argv[1]);W,H,wk,l=c.walkgrid(s);U=c.units(s)
st=[u for u in U if u['id']==214]
D=c.dij(W,H,wk,[c.near_walk(W,H,wk,u['x']//32,u['y']//32) for u in st])
tot=sum(wk[y][x] for y in range(H) for x in range(W));r=sum(1 for y in range(H) for x in range(W) if wk[y][x] and D[y][x]<1e9)
un=sorted({(u['x']//32,u['y']//32) for u in U if u['id'] in (176,177,178,188) and all(D[y][x]>1e9 for y in range(max(0,u['y']//32-2),min(H,u['y']//32+3)) for x in range(max(0,u['x']//32-3),min(W,u['x']//32+4)))})
print('reachable share %.3f'%(r/tot),'unreachable resources',len(un),un[:8])
