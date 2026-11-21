"""mineral_layout mineral layouts: every field has a free straight line to the hall (single column/row, ends pulled in).
Hall top-left (hx,hy), 4x3. side 'left': column of fields left of the hall + geyser above; 'down': row of fields below + geyser left."""
from rankedlib import MINERAL,GEYSER,STARTLOC
def base2(hx,hy,side,n=9,amount=1500,gas=5000,geysers=1,start=True):
    out=[]
    if side=='left':
        rows=list(range(hy+1-n//2, hy+1-n//2+n))
        for k,y in enumerate(rows): out.append((MINERAL,hx-4 if k in (0,n-1) else hx-5,y,amount))
        if geysers: out.append((GEYSER,hx,min(rows)-2 if min(rows)-2<=hy-5 else hy-5,gas))
    elif side=='down':
        x0=hx+2-n   # n fields x 2 tiles centred on hall centre (hx+2)
        for k in range(n): out.append((MINERAL,x0+2*k,hy+5 if k in (0,n-1) else hy+6,amount))
        if geysers: out.append((GEYSER,hx-7,hy,gas))
    if start: out.append((STARTLOC,hx,hy,0))
    return out
