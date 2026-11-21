#!/usr/bin/env python3
"""Offline trigger simulator (BW): replays a scripted 'intended playthrough' against the real TRIG/UNIT/MRGN data of a
built .scx and proves the victory action fires (and no defeat fires first). Supports the common condition/action subset
used by campaign missions. It does NOT model combat or AI: script those outcomes as timed events (move/spawn/kill).
Usage from a build script:
    import trigsim
    trigsim.prove(MAP, [trigsim.at(150, 'a marine reaches the outpost', trigsim.move(0, 0, 'Outpost')),
                        trigsim.at(600, 'the hatchery dies', trigsim.kill(1, 131, 'Hatchery'))])"""
import struct,sys,os,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from placecheck import chk_sections, B
from sclib import *
def grp(g,u):
    if g==ANYUNIT: return u!=STARTLOC
    if g==MEN: return u not in B and u!=STARTLOC
    if g==BUILDINGS: return u in B and u not in (MINERAL,GEYSER)
    return g==u
def cmpok(v,q,c): return v>=q if c==0 else v<=q if c==1 else v==q
class Sim:
    def __init__(s,path):
        S=chk_sections(path); s.S=S
        s.locs={}
        strs=S['STR ']; n=struct.unpack_from('<H',strs,0)[0]
        def st(i): o=struct.unpack_from('<H',strs,2*i)[0]; return strs[o:strs.index(b'\0',o)].decode('utf-8','replace')
        for i in range(255 if len(S['MRGN'])>=255*20 else 64):
            l,t,r,b,nm,_=struct.unpack_from('<IIIIHH',S['MRGN'],i*20)
            if nm: s.locs[i+1]=(l,t,r,b,st(nm))
        s.lname={v[4]:k for k,v in s.locs.items()}
        s.units=[]  # [player,uid,x,y,alive]
        for i in range(0,len(S['UNIT']),36):
            px,py,uid=struct.unpack_from('<HHH',S['UNIT'],i+4); own=S['UNIT'][i+16]
            if uid!=STARTLOC: s.units.append([own,uid,px,py])
        s.trigs=[]
        T=S['TRIG']
        for i in range(0,len(T),2400):
            conds=[struct.unpack_from('<IIIHBBBBH',T,i+k*20) for k in range(16)]
            acts=[struct.unpack_from('<IIIIIIHBBB3x',T,i+320+k*32) for k in range(64)]
            pl=T[i+2372:i+2400]
            s.trigs.append(dict(c=[c for c in conds if c[5]],a=[a for a in acts if a[7]],p=[j for j in range(8) if pl[j]],done=False,idx=i//2400))
        s.sw=set(); s.deaths=collections.Counter(); s.cd=0; s.t=0; s.log=[]; s.result=None; s.spawns=[]; s.p1spawns=[]
    def inloc(s,u,L):
        if L==64 or L not in s.locs: return True
        l,t,r,b,_=s.locs[L]; return l<=u[2]<r and t<=u[3]<b
    def center(s,L): l,t,r,b,_=s.locs[L]; return ((l+r)//2,(t+b)//2)
    def count(s,p,g,L=64): return sum(1 for u in s.units if u[0]==p and grp(g,u[1]) and s.inloc(u,L))
    def kill(s,p,g,L=64,n=0,remove=False):
        k=0
        for u in list(s.units):
            if u[0]==p and grp(g,u[1]) and s.inloc(u,L) and (n==0 or k<n):
                s.units.remove(u); k+=1
                if not remove: s.deaths[(p,u[1])]+=1
        return k
    def cond(s,c,owner):
        loc,pl,qty,unit,cmp,ct,res,fl,_=c
        if ct==22: return True
        if ct==12: return s.t>=qty
        if ct==11: return (res in s.sw)==(cmp==2)
        if ct==1: return s.cdset and cmpok(s.cd,qty,cmp)
        if ct==2: return cmpok(s.count(pl,unit),qty,cmp)
        if ct==3: return cmpok(s.count(pl,unit,loc),qty,cmp)
        if ct==15: return cmpok(sum(v for (p,u),v in s.deaths.items() if p==pl and grp(unit,u)),qty,cmp)
        if ct==13: return False
        if ct==5: return cmpok(sum(v for (p,u),v in s.deaths.items() if p!=pl and grp(unit,u)),qty,cmp)
        raise ValueError(f'unsupported condition {ct}')
    def act(s,a,owner,ti):
        loc,st,wav,time,pl,num,unit,typ,mod,fl=a
        if typ==1: s.result=s.result or ('VICTORY',s.t,ti)
        elif typ==2: s.result=s.result or ('DEFEAT',s.t,ti)
        elif typ==13:
            if mod==4: s.sw.add(num)
            elif mod==5: s.sw.discard(num)
        elif typ==14: s.cd=time; s.cdset=True
        elif typ==44:
            if time!=0xC1A5: s.spawns.append((s.t,pl,unit,mod or 1))
            if pl==0: s.p1spawns.append((s.t,pl,unit,mod or 1))
            x,y=s.center(loc)
            for _ in range(mod or 1): s.units.append([pl,unit,x,y])
        elif typ==46:
            x,y=s.center(num)
            for u in s.units:
                if u[0]==pl and grp(unit,u[1]) and u[1] not in B and s.inloc(u,loc): u[2],u[3]=x,y
        elif typ in (22,24): s.kill(pl,unit,0,mod,remove=(typ==24))
        elif typ in (23,25): s.kill(pl,unit,loc,mod,remove=(typ==25))
        elif typ==23: s.kill(pl,unit,64,mod,remove=True)
        elif typ==21: s.kill(pl,unit,64,mod)
        elif typ==48:
            k=0
            for u in s.units:
                if u[0]==pl and grp(unit,u[1]) and s.inloc(u,loc) and (mod==0 or k<mod): u[0]=num; k+=1
    def run(s,scenario,tmax=3600):
        s.cdset=False; ev=sorted(scenario,key=lambda e:e[0])
        while s.t<=tmax and not s.result:
            while ev and ev[0][0]<=s.t:
                _,f,desc=ev.pop(0); f(s); s.log.append((s.t,desc))
            for tr in s.trigs:
                if tr['done']: continue
                for owner in tr['p']:
                    if all(s.cond(c,owner) for c in tr['c']):
                        tr['done']=True; s.log.append((s.t,f"trig{tr['idx']} fires"))
                        for a in tr['a']: s.act(a,owner,tr['idx'])
                        break
                if s.result: break
            if s.cdset and s.cd>0: s.cd-=1
            s.t+=1
        return s.result
# scenario helpers ------------------------------------------------------
def at(t,desc,f): return (t,f,desc)
def move(p,uid,locname,n=1):
    def f(s):
        L=s.lname[locname]; x,y=s.center(L); k=0
        if p==0 and not any(u[0]==0 and grp(uid,u[1]) for u in s.units):
            for u in s.units:   # rescuable (P8) units join P1 when touched in-game
                if u[0]==7 and grp(uid,u[1]): u[0]=0
        for u in s.units:
            if u[0]==p and grp(uid,u[1]) and u[1] not in B and k<n: u[2],u[3]=x,y; k+=1
        assert k>=min(n,1) or n==0, f'no unit {uid} of P{p+1} to move'
    return f
def spawn(p,uid,locname,n):
    def f(s):
        x,y=s.center(s.lname[locname])
        for _ in range(n): s.units.append([p,uid,x,y])
    return f
def kill(p,uid,locname=None,n=0):
    def f(s): s.kill(p,uid,s.lname[locname] if locname else 64,n)
    return f
def prove(path,scenario,tmax=3600,verbose=False,rescue_at_start=False):
    """rescue_at_start=True: a rescuable (P8) unit standing beside the start units joins at second 1."""
    s=Sim(path)
    def rescue(si):
        for u in si.units:
            if u[0]==7: u[0]=0
    scenario=([at(1,"the rescuable unit beside the start units joins",rescue)] if rescue_at_start else [])+list(scenario)
    r=s.run(scenario,tmax)
    if verbose: [print('   ',x) for x in s.log]
    ok=bool(r) and r[0]=='VICTORY'
    print(f'TRIGSIM {path.split("/")[-1]}: {r}  ({len(s.trigs)} triggers, events {len(scenario)})')
    if not ok:
        [print('   ',x) for x in s.log[-25:]]
        raise SystemExit('TRIGSIM FAILED: victory did not fire')
    s.r=r; return s
