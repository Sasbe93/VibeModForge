"""no_empty_areas: largest empty square (tiles) on a BW map: walkable tiles whose 4-neighbours share cv5 terrain type and level, more than 2 tiles from any unit and 1 tile from any doodad/sprite. Ladder calibration (no_empty_areas): 4-15, Octagon central arena 30."""
import sys,struct,collections
sys.path.insert(0,'tools/bw')
import check_ranked_bw as C
def empty_square(path,key="type"):
    s=C.sections(path); W,H,wk,lvl=C.walkgrid(s)
    ts=struct.unpack('<H',s['ERA '])[0]%8; cv5=open(f'{C.TD}/{C.TS[ts]}.cv5','rb').read()
    mt=struct.unpack(f'<{W*H}H',s['MTXM'])
    def tid(v):
        g=v>>4; g=g if g*52+52<=len(cv5) else 0
        return struct.unpack_from('<H',cv5,g*52)[0] if key=='type' else g
    T=[[tid(mt[y*W+x]) for x in range(W)] for y in range(H)]
    feat=[[False]*W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if not wk[y][x]: feat[y][x]=True; continue
            for a,b in ((1,0),(0,1),(-1,0),(0,-1)):
                X,Y=x+a,y+b
                if 0<=X<W and 0<=Y<H and (T[Y][X]!=T[y][x] or lvl[Y][X]!=lvl[y][x] or not wk[Y][X]): feat[y][x]=True
    def mark(px,py,r):
        for yy in range(py//32-r,py//32+r+1):
            for xx in range(px//32-r,px//32+r+1):
                if 0<=xx<W and 0<=yy<H: feat[yy][xx]=True
    for u in C.units(s): mark(u['x'],u['y'],2)
    for k,sz in (('DD2 ',8),('THG2',10)):
        d=s.get(k,b'')
        for i in range(0,len(d)-sz+1,sz):
            _,x,y=struct.unpack_from('<HHH',d,i); mark(x,y,1)
    best=0;at=None;dp=[[0]*(W+1) for _ in range(H+1)]
    for y in range(H):
        for x in range(W):
            if not feat[y][x]:
                dp[y+1][x+1]=1+min(dp[y][x],dp[y][x+1],dp[y+1][x])
                if dp[y+1][x+1]>best: best=dp[y+1][x+1]; at=(x-best+1,y-best+1)
    return best,at
