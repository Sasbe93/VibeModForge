"""Check 21: town-hall <-> resource gap (Blizzard layout). Gap = empty tiles between footprints (Chebyshev).
Geyser/gas building: 3..5 tiles (FAIL <3 or >5). Mineral fields nearest the hall: 2..4 tiles; any field <2 FAIL.
Used by predelivery_check.py and the build scripts (ok_slot)."""
import struct
HALLS={106,131,132,133,154,130}; GAS={188,110,149,157}; MIN={176,177,178}
SZ={**{h:(4,3) for h in HALLS},**{g:(4,2) for g in GAS},**{m:(2,1) for m in MIN},214:(4,3)}
def box(u):
    w,h=SZ[u['id']]; return (u['x']/32-w/2,u['y']/32-h/2,u['x']/32+w/2,u['y']/32+h/2)
def gap(a,b):
    A,B=box(a),box(b); dx=max(B[0]-A[2],A[0]-B[2],0); dy=max(B[1]-A[3],A[1]-B[3],0); return max(dx,dy)
def check(units,R=13):
    halls=[u for u in units if u['id'] in HALLS]
    halls+= [dict(u,id=214) for u in units if u['id']==214 and not any(abs(u['x']-h['x'])<64 and abs(u['y']-h['y'])<64 for h in halls)]
    out=[];bad=[]
    for h in halls:
        nb=lambda s:[u for u in units if u['id'] in s and abs(u['x']-h['x'])<=R*32 and abs(u['y']-h['y'])<=R*32]
        g=[gap(h,u) for u in nb(GAS)]; m=sorted(gap(h,u) for u in nb(MIN))
        t=(int(h['x']//32),int(h['y']//32)); s=f'hall {t}: geyser gap {g} min-gap nearest {m[:3]}'
        e=[]
        if not g: e.append('no geyser')
        if any(x<3 or x>5 for x in g): e.append('geyser gap not 3..5')
        if m and (m[0]<2 or m[0]>4): e.append('minerals not 2..4')
        if not m: e.append('no minerals')
        out.append(s+(' -> '+', '.join(e) if e else '')); bad+= [s] if e and not ({'no geyser','no minerals'}>=set(e)) else []
    return bad,out
