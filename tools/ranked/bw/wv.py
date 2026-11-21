import sys; sys.path.insert(0,'tools/bw'); import check_ranked_bw as c
f,x0,y0,x1,y1=sys.argv[1],*map(int,sys.argv[2:6])
s=c.sections(f);W,H,wk,l=c.walkgrid(s);U=c.units(s);R={}
for u in U:
    w,h=c.SZ.get(u['id'],(1,1))
    for a in range(w):
        for b in range(h): R[(u['x']//32-w//2+a,u['y']//32-h//2+b)]={176:'m',188:'g',214:'S'}.get(u['id'],'u')
print('   '+''.join(str(x%10) for x in range(x0,x1)))
for y in range(y0,y1): print('%3d'%y,''.join(R.get((x,y)) or (('.' if wk[y][x] else '#') if l[y][x]==0 else (str(l[y][x]) if wk[y][x] else 'X')) for x in range(x0,x1)))
