"""Minitile (8px) walk grid for badlands via vf4 (ranked_layout_rules brief: real ramp widths)."""
import struct, check_ranked_bw as c
def minigrid(path):
    s=c.sections(path); W,H=struct.unpack('<HH',s['DIM ']); ts=struct.unpack('<H',s['ERA '])[0]%8
    cv5=open(f'{c.TD}/{c.TS[ts]}.cv5','rb').read(); vf=open(c.VF4[c.TS[ts]],'rb').read(); vc=open(c.VF4[c.TS[ts]][:-4]+'.cv5','rb').read(); mt=struct.unpack(f'<{W*H}H',s['MTXM'])
    G=[[False]*(W*4) for _ in range(H*4)]
    for y in range(H):
        for x in range(W):
            v=mt[y*W+x]; g=v>>4
            if g*52+52>len(vc):   # no minitile data for this group: whole tile by cv5 flag
                if g*52+52<=len(cv5) and not struct.unpack_from('<H',cv5,g*52+2)[0]&4:
                    for i in range(16): G[y*4+i//4][x*4+i%4]=True
                continue
            mg=struct.unpack_from('<H',vc,g*52+20+(v&15)*2)[0]
            if mg*32+32>len(vf): continue
            f=struct.unpack_from('<16H',vf,mg*32)
            for i in range(16): G[y*4+i//4][x*4+i%4]=bool(f[i]&1)
    return W*4,H*4,G
if __name__=='__main__':
    import sys; W,H,G=minigrid(sys.argv[1]); x0,y0,x1,y1=map(int,sys.argv[2:6])
    for y in range(y0*4,y1*4): print('%3d'%(y//4) if y%4==0 else '   ',''.join('.' if G[y][x] else '#' for x in range(x0*4,x1*4)))
def mincut_mini(G,W,H,src,dst,limit=64):
    """vertex max-flow (unit capacity per minitile) from src set to dst set; returns flow (= narrowest cross-section in minitiles, /4 = tiles)."""
    import collections
    S=set(src); T=set(dst); flow={}  # node-split: (p,0)->(p,1)
    def nb(p):
        x,y=p
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            X,Y=x+dx,y+dy
            if 0<=X<W and 0<=Y<H and G[Y][X]: yield (X,Y)
    used=collections.defaultdict(int); f=0
    while f<limit:
        par={}; q=collections.deque()
        for s in S: par[(s,1)]=None; q.append((s,1))
        end=None
        while q and end is None:
            u=q.popleft(); p,side=u
            if side==0:
                cand=[((p,1),used[((p,0),(p,1))]<1)]+[((r,1),used[((r,1),(p,0))]>0) for r in nb(p)]
            else:
                cand=[((r,0),used[((p,1),(r,0))]<1) for r in nb(p)]+[((p,0),used[((p,0),(p,1))]>0)]
            for v,ok in cand:
                if ok and v not in par:
                    par[v]=u
                    if v[0] in T and v[1]==0: end=v; break
                    q.append(v)
        if end is None: break
        v=end
        while par[v] is not None:
            u=par[v]
            if used[(v,u)]>0: used[(v,u)]-=1
            else: used[(u,v)]+=1
            v=u
        f+=1
    return f
