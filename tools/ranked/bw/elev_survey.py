import sys,os,struct,glob,numpy as np
sys.path.insert(0,'tools/bw')
import predelivery_check as P, base_elevation as BE
def bases(p):
    S=P.secs(p);U=S['UNIT']
    us=[dict(x=struct.unpack_from('<H',U,i+4)[0],y=struct.unpack_from('<H',U,i+6)[0],id=struct.unpack_from('<H',U,i+8)[0]) for i in range(0,len(U),36)]
    h,w=BE.heights(S);H,W=h.shape
    res=[(u['x']//32,u['y']//32) for u in us if u['id'] in(176,177,178,188)]
    starts=[(u['x']//32,u['y']//32) for u in us if u['id']==214]
    cl=[]
    for r in res:
        for c in cl:
            if any(abs(r[0]-a)+abs(r[1]-b)<=6 for a,b in c): c.append(r);break
        else: cl.append([r])
    cl=[c for c in cl if len(c)>=4]
    yy,xx=np.mgrid[0:H,0:W];out=[]
    for c in cl:
        cx=np.mean([a for a,b in c]);cy=np.mean([b for a,b in c])
        isS=any(np.hypot(cx-a,cy-b)<14 for a,b in starts)
        # base floor: walkable tiles within 8 of resource centroid
        d=np.hypot(xx-cx,yy-cy); fl=(d<=8)&w; hb=int(np.median(h[fl])) if fl.any() else 0
        ring=(d>=14)&(d<=26)&w; rm=float(np.median(h[ring]))
        out.append((isS,hb,rm))
    return out
tot=dict(sh=0,s=0,eh=0,el=0,e=0,lvls=set())
for p in sorted(glob.glob(sys.argv[1])):
    try: b=bases(p)
    except Exception as e: print('ERR',p,e);continue
    s=[x for x in b if x[0]];e=[x for x in b if not x[0]]
    sh=sum(x[1]>x[2] for x in s);eh=sum(x[1]>x[2] for x in e);el=sum(x[1]<x[2] for x in e)
    lv=sorted(set(x[1] for x in e))
    print(f'{os.path.basename(p):38s} starts {len(s)} raised {sh} | exp {len(e)} raised {eh} lower {el} levels {lv} start_lv {sorted(set(x[1] for x in s))}')
    for k,v in dict(sh=sh,s=len(s),eh=eh,el=el,e=len(e)).items(): tot[k]+=v
print(tot)
