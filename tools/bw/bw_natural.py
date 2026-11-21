# natural_in_front: natural must lie in front of the main, on the way to the enemy/centre.
import sys,math,struct
sys.path.insert(0,'tools/bw')
from check_ranked_bw import sections,walkgrid,units,dij,near_walk,MIN,GAS,SLOC
LIM=dict(detour_max=1.15,ang_centre_max=999,nat_dist_max=45)
def bases(s):
    U=units(s); res=[(u['x']/32,u['y']/32) for u in U if u['id'] in MIN or u['id'] in GAS]
    cl=[]
    for r in res:
        for c in cl:
            if any(abs(r[0]-a)+abs(r[1]-b)<=6 for a,b in c): c.append(r);break
        else: cl.append([r])
    cl=[(sum(a for a,b in c)/len(c),sum(b for a,b in c)/len(c)) for c in cl if len(c)>=4]
    st=[]
    for u in U:
        if u['id']==SLOC and all(math.hypot(u['x']/32-a,u['y']/32-b)>4 for a,b in st): st.append((u['x']/32,u['y']/32))
    return st,cl
def metrics(path):
    s=sections(path); W,H,wk,lvl=walkgrid(s); st,cl=bases(s)
    nw=lambda p: near_walk(W,H,wk,int(p[0]),int(p[1]))
    Ds=[dij(W,H,wk,[nw(p)]) for p in st]; cx,cy=W/2,H/2; out=[]
    exps=[b for b in cl if min(math.hypot(b[0]-a,b[1]-c) for a,c in st)>10]
    for i,p in enumerate(st):
        D=Ds[i]; gd=lambda b,D=D: D[nw(b)[1]][nw(b)[0]] if nw(b) else math.inf
        ex=sorted(exps,key=gd)
        if not ex: continue
        nat=ex[0]; dn=gd(nat); opp=[j for j in range(len(st)) if j!=i]
        det=[]; 
        for j in opp:
            r=Ds[j][nw(p)[1]][nw(p)[0]]; dne=Ds[j][nw(nat)[1]][nw(nat)[0]]
            if r<math.inf: det.append(((dn+dne)/r,r))
        ang=lambda v,w: abs((math.degrees(math.atan2(v[1],v[0])-math.atan2(w[1],w[0]))+180)%360-180)
        vn=(nat[0]-p[0],nat[1]-p[1]); a_c=ang(vn,(cx-p[0],cy-p[1]))
        ne=min(opp,key=lambda j:Ds[j][nw(p)[1]][nw(p)[0]]) if opp else None
        a_e=ang(vn,(st[ne][0]-p[0],st[ne][1]-p[1])) if ne is not None else 0
        pas=99
        for j in opp:
            x,y=nw(p); Dj=Ds[j]
            if Dj[y][x]==math.inf: continue
            for _ in range(2000):
                pas=min(pas,math.hypot(x-nat[0],y-nat[1]))
                nb=min(((Dj[y+dy][x+dx],x+dx,y+dy) for dx in(-1,0,1) for dy in(-1,0,1) if 0<=x+dx<W and 0<=y+dy<H),key=lambda t:t[0])
                if nb[0]>=Dj[y][x]: break
                x,y=nb[1],nb[2]
        th=ex[1] if len(ex)>1 else None
        out.append(dict(pass_dist=pas,nat_dist=dn,detour_min=min(d for d,_ in det) if det else 9,rush=min(r for _,r in det) if det else 0,
            ang_centre=a_c,ang_enemy=a_e,third_dist=gd(th) if th else 0,
            third_detour=min((gd(th)+Ds[j][nw(th)[1]][nw(th)[0]])/Ds[j][nw(p)[1]][nw(p)[0]] for j in opp) if th and opp else 9,
            nat_lvl=lvl[nw(nat)[1]][nw(nat)[0]],main_lvl=lvl[nw(p)[1]][nw(p)[0]],nexp=len(exps)/max(1,len(st))))
    return out
# ---- natural_cut: natural must be a CUT between main and enemy (corrected concept) ----

NAT_R=18     # refs: natural region radius (ground tiles from natural) that cuts main from enemy: typ. 10-17
ANG_MAX=115  # angle main->natural vs main->enemy (refs 2p 49-81, 4p up to ~105)
def cut_metrics(path):
    import bw_natcut; return bw_natcut.metrics(path)
def check(path):
    F,I=check_old(path)
    try: M=cut_metrics(path)
    except Exception as e: return F,I+[f'INFO natural_in_front cut: skipped ({e})']
    for k,x in enumerate(M):
        bad=[]
        if x['cutR']>NAT_R: bad.append(f"natural is NOT a cut: main reaches enemy around the natural (needs radius {x['cutR']:.0f}>{NAT_R}; main has a 2nd exit/bypass)")
        if x['ang']>ANG_MAX: bad.append(f"natural off the enemy direction ({x['ang']:.0f}deg>{ANG_MAX})")
        if x['ratio']>=1.0: bad.append(f"natural not closer to enemy than main (ground ratio {x['ratio']:.2f})")
        I.append(f"INFO natural_in_front cut start {k+1}: cutR {x['cutR']:.0f} (<= {NAT_R}) ang {x['ang']:.0f} enemy-dist ratio nat/main {x['ratio']:.2f}")
        if bad: F.append(f"FAIL natural_in_front start {k+1}: "+'; '.join(bad))
    return F,I
def check_old(path):
    F=[];I=[]
    try: m=metrics(path)
    except Exception as e: return F,[f'INFO natural_in_front natural: skipped ({e})']
    for k,x in enumerate(m):
        bad=[]
        if x['detour_min']>LIM['detour_max']: bad.append(f"natural not on main->enemy path (detour {x['detour_min']:.2f}>{LIM['detour_max']})")
        if x['ang_centre']>LIM['ang_centre_max']: bad.append(f"natural angle to centre {x['ang_centre']:.0f}>{LIM['ang_centre_max']}deg")
        if x['nat_dist']>LIM['nat_dist_max']: bad.append(f"natural {x['nat_dist']:.0f} tiles >{LIM['nat_dist_max']}")
        if bad: I.append(f"INFO WARN natural_in_front(old) start {k+1}: "+'; '.join(bad))
        I.append(f"INFO natural_in_front start {k+1}: nat {x['nat_dist']:.0f}t detour {x['detour_min']:.2f} ang_centre {x['ang_centre']:.0f} ang_enemy {x['ang_enemy']:.0f} path-pass {x['pass_dist']:.1f}t third {x['third_dist']:.0f}t (detour {x['third_detour']:.2f}) lvl main/nat {x['main_lvl']}/{x['nat_lvl']}")
    return F,I
if __name__=='__main__':
    f,i=check(sys.argv[1]); print('\n'.join(i+f))
