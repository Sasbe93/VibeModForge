"""terrain seam check: tile-only doodads are pasted as hard rectangles (ISOM itself always blends).
For each DD2 doodad compare the colour of its outer minitile ring with the touching minitiles of the
neighbouring tiles. Blended/ground-matching doodads score ~1.5-4.5; visible rectangles score >6
(LY3 screenshot: the rock patch and dark plating scored 13-26)."""
import sys,struct,numpy as np
sys.path.insert(0,'tools/lib/bw')
import sclib
_F={}
def tilefeat(mtxm,W,H,ts,cv5):
    if ts not in _F: _F[ts]=sclib._megafeat(ts)
    F=_F[ts]; mt=struct.unpack(f'<{W*H}H',mtxm)
    mega=np.array([struct.unpack_from('<H',cv5,(v>>4)*52+20+(v&15)*2)[0] if (v>>4)*52+52<=len(cv5) else 0 for v in mt]).reshape(H,W)
    return F[np.minimum(mega,len(F)-1)].reshape(H,W,4,4,3)
def rect_score(f,x0,y0,w,h):
    H,W=f.shape[:2]; e=[]
    for y in range(y0,y0+h):
        if 0<x0<W and 0<=y<H: e.append(np.abs(f[y,x0-1,:,3]-f[y,x0,:,0]).mean())
        if 0<x0+w<W and 0<=y<H: e.append(np.abs(f[y,x0+w-1,:,3]-f[y,x0+w,:,0]).mean())
    for x in range(x0,x0+w):
        if 0<y0<H and 0<=x<W: e.append(np.abs(f[y0-1,x,3,:]-f[y0,x,0,:]).mean())
        if 0<y0+h<H and 0<=x<W: e.append(np.abs(f[y0+h-1,x,3,:]-f[y0+h,x,0,:]).mean())
    return float(np.mean(e)) if e else 0.0
def doodad_seams(sec,thr=6.0):
    W,H=struct.unpack('<HH',sec['DIM ']);ts=struct.unpack('<H',sec['ERA '])[0]&7
    cv5=open(f'{sclib.TOOLS}/tileset/{sclib.TSNAMES[ts]}.cv5','rb').read()
    cat,_=sclib.doodad_catalog_all(ts); f=tilefeat(sec['MTXM'],W,H,ts,cv5); bad=[]
    dd=sec.get('DD2 ',b'')
    for j in range(0,len(dd),8):
        did,px,py=struct.unpack_from('<HHH',dd,j); c=cat.get(did)
        if not c: continue
        x0=px//32-c['w']//2; y0=py//32-c['h']//2; sc=rect_score(f,x0,y0,c['w'],c['h'])
        if sc>thr: bad.append((did,(x0,y0),c['w'],c['h'],round(sc,1)))
    return bad

def doodad_peaks(sec,thr=15.0):
    """max single border-edge colour step per tile doodad; >thr = visible hard seam (measured: ramp/rock blocks 16-28)"""
    W,H=struct.unpack('<HH',sec['DIM ']);ts=struct.unpack('<H',sec['ERA '])[0]&7
    cv5=open(f'{sclib.TOOLS}/tileset/{sclib.TSNAMES[ts]}.cv5','rb').read()
    cat,_=sclib.doodad_catalog_all(ts); f=tilefeat(sec['MTXM'][:W*H*2],W,H,ts,cv5); bad=[]
    dd=sec.get('DD2 ',b'')
    for j in range(0,len(dd),8):
        did,px,py=struct.unpack_from('<HHH',dd,j); c=cat.get(did)
        if not c: continue
        x0=px//32-c['w']//2; y0=py//32-c['h']//2; w,h=c['w'],c['h']; e=[]
        for y in range(y0,y0+h):
            if 0<x0<W and y<H: e.append(np.abs(f[y,x0-1,:,3]-f[y,x0,:,0]).mean())
            if 0<x0+w<W and y<H: e.append(np.abs(f[y,x0+w-1,:,3]-f[y,x0+w,:,0]).mean())
        for x in range(x0,x0+w):
            if 0<y0<H and x<W: e.append(np.abs(f[y0-1,x,3,:]-f[y0,x,0,:]).mean())
            if 0<y0+h<H and x<W: e.append(np.abs(f[y0+h-1,x,3,:]-f[y0+h,x,0,:]).mean())
        if e and max(e)>thr: bad.append((did,(x0,y0),round(float(max(e)),1)))
    return bad
