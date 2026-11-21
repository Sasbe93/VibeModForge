"""ragged_shore (self-found gap): every base must be reachable by ground from the starts, and the map must not be mostly
cut off. A test map passed all checks with only 40% of the walkable ground reachable (62 resources on islands),
because ranked_layout_rules/natural_in_front only look at reachable tiles. Refs (12 ladder maps): reachable share 0.920-0.998, unreachable
resources 0 except Eclipse (9 = one island base).
FAIL: reachable share < 0.90, or more than 10 unreachable resources (more than one island base). WARN: share < 0.95."""
import sys,math
sys.path.insert(0,'tools/bw')
from check_ranked_bw import sections,walkgrid,near_walk,units,dij,SLOC
RES=(176,177,178,188)
def check(path):
    s=sections(path);W,H,wk,_=walkgrid(s);U=units(s)
    st=[u for u in U if u['id']==SLOC]
    D=dij(W,H,wk,[near_walk(W,H,wk,u['x']//32,u['y']//32) for u in st])
    # water_doodads: ignore tiny unreachable walkable specks (<=6 tiles, e.g. rock/statue decor tiles in water flagged walkable in cv5)
    seen=set();spk=0
    for y in range(H):
        for x in range(W):
            if wk[y][x] and D[y][x]==math.inf and (x,y) not in seen:
                q=[(x,y)];seen.add((x,y));comp=[]
                while q:
                    X,Y=q.pop();comp.append((X,Y))
                    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                        P=(X+dx,Y+dy)
                        if 0<=P[0]<W and 0<=P[1]<H and P not in seen and wk[P[1]][P[0]] and D[P[1]][P[0]]==math.inf: seen.add(P);q.append(P)
                if len(comp)<=6: spk+=len(comp)
    tot=(sum(wk[y][x] for y in range(H) for x in range(W))-spk) or 1
    r=sum(1 for y in range(H) for x in range(W) if wk[y][x] and D[y][x]<math.inf)
    un=[(u['x']//32,u['y']//32) for u in U if u['id'] in RES and all(D[y][x]==math.inf for y in range(max(0,u['y']//32-2),min(H,u['y']//32+3)) for x in range(max(0,u['x']//32-3),min(W,u['x']//32+4)))]
    F=[];I=[f'ragged_shore reachability: {r/tot:.3f} of walkable ground reachable from starts, {len(un)} resources unreachable (refs 0.92-0.998, max 9)']
    if r/tot<0.90: F.append(f'ragged_shore: only {r/tot:.1%} of the walkable ground is reachable from the starts (<90%) - large regions are cut off')
    elif r/tot<0.95: I.append(f'WARN ragged_shore: reachable share {r/tot:.3f} < 0.95')
    if len(un)>10: F.append(f'ragged_shore: {len(un)} resources not ground-reachable from any start (more than one island base): {un[:6]}')
    return F,I
