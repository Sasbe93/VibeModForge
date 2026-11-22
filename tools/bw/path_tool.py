#!/usr/bin/env python3
"""Reusable BW path tool: walkable pathfinding, threat encounters along a path, scripted-wave arrival
times and approach chokes, and a routes PNG.
   python3 tools/bw/path_tool.py MAP.scx [--png routes.png] [--json out.json]
Run from the repository root (needs tools/lib/bw/tileset for the walk grid; a terrain underlay needs the
full tileset files). Used by check_objective_paths.py and check_escort_route.py."""
import sys,os,re,struct,math,json,tempfile
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from check_ranked_bw import sections,walkgrid,apply_blockers,units,dij,near_walk
from check_ally_vision import note_files

FPS=24.0
THREAT_R=7; AMBUSH_R=3; GAP=10
TOWERS={125,146,162}          # Bunker, Sunken Colony, Photon Cannon
WORKERS={7,41,64}; SLOC=214
HALLS={106,107,108,131,132,133,154}
MEN,BUILDINGS,FACTORIES,ANYUNIT=229,230,231,229
# Flingy speeds in pixels/frame at Fastest (Liquipedia / flingy.dat). Travel seconds = tiles*32/(speed*FPS).
SPEED={0:4.0,1:4.0,2:6.4,3:4.69,5:4.0,7:4.92,8:6.67,9:5.0,11:5.47,12:2.5,13:12.5,
       32:4.0,34:4.0,37:5.49,38:3.66,39:5.12,40:6.67,41:4.92,42:0.83,43:6.67,44:2.5,
       45:6.67,46:4.0,47:6.67,58:6.6,61:4.92,62:5.0,64:4.92,65:4.0,66:5.0,67:3.2,68:4.92,
       69:4.92,71:4.43,83:3.33,103:5.82}
DB=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','data','bw','tech','bw_weapons.json')))
GROUND_ARMED={int(k) for k,v in DB['units'].items() if v.get('ground') is not None}|{72,82,83,125}
UN=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','data','bw','tech','bw_techtree.json')))['unit_names']

def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def u16(b,o): return struct.unpack_from('<H',b,o)[0]
def uname(i): return UN.get(str(i), f'uid{i}')
def travel_sec(tiles, uid=0):
    if tiles==math.inf or tiles is None: return math.inf
    return tiles*32/(SPEED.get(uid,4.0)*FPS)
def travel_fmt(tiles, uid=0):
    s=travel_sec(tiles,uid)
    if s==math.inf: return 'unreachable'
    return f'{tiles:.0f} tiles / {s:.0f}s ({s/60:.1f} min) at Fastest ({uname(uid) if uid in SPEED else "unit"} speed)'
def strings(S):
    b=S.get('STR ',b'\0\0'); n=u16(b,0)
    def g(j):
        if not (0<j<=n): return ''
        o=u16(b,2*j)
        try: return b[o:b.index(b'\0',o)].decode('utf8','replace')
        except ValueError: return ''
    return g
def strip(s): return re.sub(r'[\x00-\x09\x0b-\x1f]','',s or '').strip()
def bsize(uid):
    try:
        import sclib; return sclib.BUILDSIZE.get(uid,(3,2))
    except Exception: return (3,2)

def pathfind(W,H,wk,src,dst):
    """Walkable path from src to dst (tile or (x,y) centres). Returns (segment tiles, length, start, end)."""
    a=near_walk(W,H,wk,int(src[0]),int(src[1]))
    b=near_walk(W,H,wk,int(dst[0]),int(dst[1]))
    if not a or not b: return [], math.inf, a, b
    D=dij(W,H,wk,[b])
    if D[a[1]][a[0]]==math.inf: return [], math.inf, a, b
    x,y=a; seg=[(x,y)]; guard=0
    while (x,y)!=b and guard<W*H*2:
        cand=[(x+dx,y+dy) for dx in (-1,0,1) for dy in (-1,0,1)
              if (dx or dy) and 0<=x+dx<W and 0<=y+dy<H and D[y+dy][x+dx]<math.inf]
        if not cand: break
        x,y=min(cand, key=lambda q: D[q[1]][q[0]])
        seg.append((x,y)); guard+=1
    return seg, D[a[1]][a[0]], a, b

def encounters(path, threats, ambs=(), rect=None, lname=None, threat_r=THREAT_R, ambush_r=AMBUSH_R, gap=GAP):
    """Cluster threat hits along a path. threats: (x,y,uid,kind); ambs: location ids."""
    hits=[]
    for tx,ty,uid,kind in threats:
        if not path: continue
        d,i=min((math.hypot(tx-x,ty-y),i) for i,(x,y) in enumerate(path))
        if d<=threat_r: hits.append((i,f'{kind} {uname(uid) if isinstance(uid,int) else uid} at ({int(tx)},{int(ty)})'))
    for l in set(ambs or ()):
        r=rect(l) if rect else None
        if not r or not path: continue
        x0,y0,x1,y1=r[0]/32,r[1]/32,r[2]/32,r[3]/32
        near=[i for i,(x,y) in enumerate(path) if x0-ambush_r<=x<=x1+ambush_r and y0-ambush_r<=y<=y1+ambush_r]
        if near: hits.append((near[0], f"triggered attack at '{lname(l) if lname else l}'"))
    hits.sort(); enc=[]
    for i,what in hits:
        if enc and i-enc[-1][0][-1]<=gap: enc[-1][0].append(i); enc[-1][1].append(what)
        else: enc.append(([i],[what]))
    return enc

def compass(base, point):
    dx,dy=point[0]-base[0], point[1]-base[1]
    ang=(math.degrees(math.atan2(dx,-dy))+360)%360          # 0=N, 90=E (y grows south)
    return ['N','NE','E','SE','S','SW','W','NW'][int((ang+22.5)%360/45)]

class MapView:
    """Parsed campaign map plus walk grid, locations, triggers, factions and threat lists."""
    def __init__(s,path):
        s.map_path=path; s.S=sections(path)
        s.W,s.H=struct.unpack('<HH',s.S['DIM '])
        s.st=strings(s.S)
        s.wk_W,s.wk_H,s.wk,_=walkgrid(s.S); apply_blockers(s.W,s.H,s.wk,s.S)
        s.U=units(s.S)
        ownr=s.S['OWNR']; s.hum={p for p in range(8) if ownr[p]==6}; s.comp={p for p in range(8) if ownr[p]==5}
        s.rescue={p for p in range(8) if ownr[p]==3}
        fo=s.S.get('FORC',b'')+b'\0'*20; s.forces=list(fo[:8]); s.fflags=list(fo[16:20])
        MR=s.S.get('MRGN',b''); s.MR=MR
        s.locs=[]
        for i in range(len(MR)//20):
            l,t,r,b,nm,f=struct.unpack_from('<IIIIHH',MR,i*20); name=s.st(nm)
            if name or (r>l and b>t): s.locs.append((i+1,name,l,t,r,b))
        T=s.S.get('TRIG',b''); s.trigs=[]
        for off in range(0,len(T)-len(T)%2400,2400):
            r=T[off:off+2400]
            c=[r[i*20:i*20+20] for i in range(16) if r[i*20+15]]
            a=[r[320+i*32:352+i*32] for i in range(64) if r[320+i*32+26]]
            own={q for q in range(28) if r[2372+q]}
            s.trigs.append((c,a,own))
        s.allied=set()
        for f in range(4):
            mem={p for p in range(8) if s.forces[p]==f}
            if s.fflags[f]&2 and mem&s.hum: s.allied|=mem-s.hum
        for c,a,own in s.trigs:
            if own&s.hum:
                for x in a:
                    if x[26]==57 and u16(x,24)>=1: s.allied|=set(s.grp(u32(x,16),own))-s.hum
        s.allied&=s.comp
        s.enemy=s.comp-s.allied
        s.threats=[(u['x']/32,u['y']/32,u['id'],'tower' if u['id'] in TOWERS else 'unit')
                   for u in s.U if u['o'] in s.enemy and (u['id'] in TOWERS or (u['id'] in GROUND_ARMED and u['id'] not in WORKERS and u['id']<106))]
        s.ambs=[]
        for c,a,own in s.trigs:
            for x in a:
                if x[26] in (44,45) and any(p in s.enemy for p in s.grp(u32(x,16),own)) and s.rect(u32(x,0)): s.ambs.append(u32(x,0))
                if x[26]==46 and any(p in s.enemy for p in s.grp(u32(x,16),own)) and s.rect(u32(x,20)) and not s.whole(u32(x,20)): s.ambs.append(u32(x,20))
        starts=[(u['x']/32,u['y']/32) for u in s.U if u['o'] in s.hum and u['id']==SLOC]
        if not starts: starts=[(u['x']/32,u['y']/32) for u in s.U if u['o'] in s.hum and u['id'] in HALLS]
        if not starts: starts=[(u['x']/32,u['y']/32) for u in s.U if u['o'] in s.hum]
        s.start=starts[0] if starts else (s.W/2,s.H/2)
        s.start_tile=(int(s.start[0]),int(s.start[1]))
        # player-reach grid: enemy buildings block
        s.pw=[row[:] for row in s.wk]
        for u in s.U:
            if u['o'] in s.enemy and u['id']>=106 and u['id'] not in (214,):
                w,h=bsize(u['id']); x0,y0=u['x']//32-w//2,u['y']//32-h//2
                for yy in range(max(0,y0),min(s.H,y0+h)):
                    for xx in range(max(0,x0),min(s.W,x0+w)): s.pw[yy][xx]=False
        seeds=[q for q in (near_walk(s.W,s.H,s.pw,int(x),int(y)) for x,y in starts) if q]
        s.PD=dij(s.W,s.H,s.pw,seeds) if seeds else [[math.inf]*s.W for _ in range(s.H)]
    def grp(s,t,own=()):
        if 0<=t<8: return [t]
        if t==13: return list(own)
        if t==17: return list(range(8))
        if 18<=t<=21: return [p for p in range(8) if s.forces[p]==t-18]
        return []
    def rect(s,l): return struct.unpack_from('<IIII',s.MR,(l-1)*20) if 0<l<=len(s.MR)//20 else None
    def lname(s,l):
        r=s.rect(l)
        return s.st(u16(s.MR,(l-1)*20+16)) if r else '?'
    def whole(s,l):
        r=s.rect(l); return not r or l==64 or (r[2]-r[0]>=s.W*32*0.6 and r[3]-r[1]>=s.H*32*0.6)
    def ltile(s,l):
        r=s.rect(l)
        if not r: return None
        return near_walk(s.W,s.H,s.wk,min(s.W-1,int((r[0]+r[2])/64)),min(s.H-1,int((r[1]+r[3])/64)))
    def lcenter(s,l):
        r=s.rect(l)
        if not r: return None
        return ((r[0]+r[2])/64,(r[1]+r[3])/64)
    def loc_by_name(s,name):
        name=(name or '').lower()
        for i,n,l,t,r,b in s.locs:
            if n and n.lower()==name: return i
        for i,n,l,t,r,b in s.locs:
            if n and name and name in n.lower(): return i
        return None
    def path(s,src,dst):
        return pathfind(s.W,s.H,s.wk,src,dst)
    def enc(s,seg):
        return encounters(seg,s.threats,s.ambs,s.rect,s.lname)
    def reachable(s,tile):
        if not tile: return False
        x,y=int(tile[0]),int(tile[1])
        if not (0<=x<s.W and 0<=y<s.H): return False
        return s.PD[y][x]<math.inf

def parse_notes(path):
    lines=[]; easy=None
    for f in note_files(path):
        for l in open(f,encoding='utf8',errors='replace'):
            m=re.search(r'OBJECTIVE_PATHS:\s*(.+?)\s*::\s*(.+?)\s*::\s*(.+?)\s*::\s*(\S.*)',l)
            if m: lines.append(tuple(x.strip() for x in m.groups()))
            m=re.search(r'OBJECTIVE_PATHS_EASY_OK:\s*(\S.*)',l)
            if m: easy=m.group(1).strip()
            m=re.search(r'ESCORT_ROUTE:\s*(.+?)\s*::\s*(.+?)\s*::\s*(.+?)\s*::\s*(\S.*)',l)
            if m: lines.append(('ESCORT '+m.group(1).strip(), m.group(2).strip(), m.group(3).strip(), m.group(4).strip()))
    return lines, easy

def objective_texts(v):
    """Unique objective lines from Set Mission Objectives, without done/failed suffixes."""
    seen=[]; out=[]
    for c,a,own in v.trigs:
        for x in a:
            if x[26]!=12: continue
            raw=strip(v.st(u32(x,4)))
            raw=re.sub(r'(?i)^objectives?\s*:\s*','',raw).strip()
            # a later update may list several bullets, possibly with Optional: on the same line
            parts=re.split(r'(?i)(?:\n|;|\s{2,})(?=\s*(?:[-*]|optional\s*:))', raw)
            for line in parts or [raw]:
                t=re.sub(r'(?i)^\s*(?:[-*]|optional\s*:)\s*','',line).strip()
                t=re.sub(r'(?i)^\s*optional\s*:\s*','',t).strip()
                t=re.sub(r'\s*-\s*(done|failed)\s*$','',t,flags=re.I).strip()
                t=re.sub(r'(?i)^objectives?\s*:\s*','',t).strip()
                if not t or re.match(r'^(objectives?|optional)\s*:?\s*$',t,re.I): continue
                key=t.lower()
                if key not in seen: seen.append(key); out.append(t)
    return out

def classify(text):
    t=(text or '').lower()
    if re.search(r'\b(escort|convoy)\b',t): return 'escort'
    if re.search(r'\b(survive|hold out|hold for|last for|defend for|withstand)\b',t): return 'survive'
    if re.search(r'\b(rescue|recover|bring .+ back|save the|extract)\b',t): return 'rescue'
    if re.search(r'\b(reach|get to|go to|find the|arrive at)\b',t): return 'reach'
    if re.search(r'\b(destroy|burn|kill the|raze|annihilate|wipe out|tear down)\b',t): return 'destroy'
    return 'other'

def _unit_in_text(text):
    t=(text or '').lower()
    for i,n in UN.items():
        if n.lower() in t or n.split()[-1].lower() in t and len(n.split()[-1])>3:
            if n.split()[-1].lower() in t: return int(i)
    return None

def detect_objectives(v):
    """Infer main and side objectives and the paths that belong to them."""
    objs=[]
    texts=objective_texts(v)
    # victory / defeat hooks
    victory_brings=[]; destroy_at=[]; countdown=None; cd_defeat=False
    for c,a,own in v.trigs:
        if any(x[26]==14 and u32(x,12)>0 for x in a):
            # Set Countdown: time at offset 12, mod at 27 (7=set)
            countdown=u32(next(x for x in a if x[26]==14 and u32(x,12)>0),12)   # Set Countdown Timer stores whole seconds in bytes 12-15 (docs.scmjs.dev, action 14)
        if any(x[15]==1 and u32(x,8)==0 for x in c) and any(x[26]==2 for x in a): cd_defeat=True
        if any(x[26]==1 for x in a):   # Victory
            for x in c:
                if x[15]==3 and not v.whole(u32(x,0)):
                    uid=u16(x,12); pl=u32(x,4); loc=u32(x,0)
                    if pl in v.hum or pl in v.rescue or (0<=pl<8 and pl not in v.enemy):
                        victory_brings.append((uid,loc,u32(x,8),x[14]))
                    if pl in v.enemy and x[14] in (1,10) and u32(x,8)==0:
                        destroy_at.append((uid,loc))
                if x[15]==2 and u32(x,4) in v.enemy and x[14] in (1,10) and u32(x,8)==0:
                    destroy_at.append((u16(x,12),None))
    # escort legs (allied computer Order to a Bring destination)
    brings={(p,u32(x,0)) for c,a,own in v.trigs for x in c if x[15]==3 for p in v.grp(u32(x,4),own)}
    escort_legs={}
    for c,a,own in v.trigs:
        for x in a:
            if x[26]!=46: continue
            src,dst=u32(x,0),u32(x,20)
            for p in v.grp(u32(x,16),own):
                if p in v.allied and v.rect(src) and v.rect(dst) and not v.whole(src) and not v.whole(dst) and src!=dst and (p,dst) in brings:
                    escort_legs.setdefault(p,[]); (src,dst) in escort_legs[p] or escort_legs[p].append((src,dst))

    used_types=set()
    for text in texts:
        typ=classify(text)
        optional=bool(re.search(r'\boptional\b',text,re.I))
        rec={'name':text,'type':typ,'optional':optional,'paths':[],'timer':None,'waves':[],'notes':[]}
        if typ=='rescue':
            # target unit: victory Bring, or a rescuable/pre-placed special unit named in the text
            unit=None; ret=None
            for uid,loc,qty,cmp in victory_brings:
                if uid<228: unit=uid; ret=v.lcenter(loc); rec['return_loc']=v.lname(loc); break
            if unit is None:
                unit=_unit_in_text(text)
            spots=[(u['x']/32,u['y']/32,u['id']) for u in v.U if u['o'] in v.rescue|v.hum and u['id'] not in WORKERS|HALLS|{SLOC,109,110,111,106} and u['id']<106]
            if unit is not None:
                spots=[p for p in spots if p[2]==unit] or [(u['x']/32,u['y']/32,u['id']) for u in v.U if u['id']==unit]
            if not spots:
                # any rescuable mobile unit
                spots=[(u['x']/32,u['y']/32,u['id']) for u in v.U if u['o'] in v.rescue and u['id']<106]
            if spots:
                tx,ty,uid=spots[0]
                rec['paths'].append(('start_to_target', v.start, (tx,ty), uid if uid<106 else 0))
                if ret is None: ret=v.start
                rec['paths'].append(('return', (tx,ty), ret, uid if uid<106 else 1))
            used_types.add('rescue')
        elif typ=='reach':
            loc=None
            for i,n,l,t,r,b in v.locs:
                if n and n.lower() not in ('anywhere',) and n.lower() in text.lower(): loc=i; break
            if loc is None:
                # first Bring of human men/any to a named location in a later (non-start) trigger
                for c,a,own in v.trigs:
                    for x in c:
                        if x[15]==3 and v.grp(u32(x,4),own) and set(v.grp(u32(x,4),own))&v.hum and not v.whole(u32(x,0)):
                            loc=u32(x,0); break
            if loc:
                c=v.lcenter(loc)
                if c: rec['paths'].append(('start_to_target', v.start, c, 0)); rec['target_loc']=v.lname(loc)
            used_types.add('reach')
        elif typ=='destroy':
            loc=None; uid=None
            for i,n,_,_,_,_ in v.locs:
                if n and n.lower() not in ('anywhere',) and n.lower() in text.lower(): loc=i; break
            for uid0,loc0 in destroy_at:
                if loc is None: loc=loc0
                uid=uid0
            if loc is None and uid is not None:
                halls=[(u['x']/32,u['y']/32) for u in v.U if u['o'] in v.enemy and u['id']==uid]
                if halls: rec['paths'].append(('start_to_target', v.start, halls[0], 0))
            elif loc:
                c=v.lcenter(loc)
                # prefer the actual building inside the location if we know the type
                if uid is not None:
                    r=v.rect(loc)
                    for u in v.U:
                        if u['o'] in v.enemy and u['id']==uid and r and r[0]<=u['x']<r[2] and r[1]<=u['y']<r[3]:
                            c=(u['x']/32,u['y']/32); break
                if c: rec['paths'].append(('start_to_target', v.start, c, 0)); rec['target_loc']=v.lname(loc)
            used_types.add('destroy')
        elif typ=='survive':
            rec['timer']=countdown
            m=re.search(r'(\d+)\s*(minute|min|second|sec)',text,re.I)
            if m and rec['timer'] is None:
                rec['timer']=int(m.group(1))* (60 if 'min' in m.group(2).lower() else 1)
            used_types.add('survive')
        elif typ=='escort' and escort_legs:
            for p,L in escort_legs.items():
                rec['escort_legs']=L; rec['escort_player']=p
            used_types.add('escort')
        objs.append(rec)

    # objectives that only exist as triggers
    if escort_legs and 'escort' not in used_types:
        rec={'name':'Escort','type':'escort','optional':False,'paths':[],'timer':None,'waves':[],'notes':[]}
        p=next(iter(escort_legs)); rec['escort_legs']=escort_legs[p]; rec['escort_player']=p
        objs.append(rec)
    if countdown and cd_defeat and 'survive' not in used_types and not any(o['type']=='survive' for o in objs):
        # only add if the objectives or mission suggest a hold; a destroy-with-timer is time-limit, not survive
        if any(classify(t)=='survive' for t in texts) or (texts and any('survive' in t.lower() or 'hold' in t.lower() for t in texts)):
            objs.append({'name':'Survive','type':'survive','optional':False,'paths':[],'timer':countdown,'waves':[],'notes':[]})
    if victory_brings and not any(o['type'] in ('rescue','reach','escort') for o in objs):   # an escort's arrival Bring is the escort, not a rescue
        uid,loc,qty,cmp=victory_brings[0]
        if uid<228:
            spots=[(u['x']/32,u['y']/32,u['id']) for u in v.U if u['id']==uid and u['o'] in v.rescue|v.hum]
            rec={'name':f'Return {uname(uid)} to {v.lname(loc)}','type':'rescue','optional':False,'paths':[],'timer':None,'waves':[],'notes':[]}
            if spots:
                rec['paths'].append(('start_to_target', v.start, (spots[0][0],spots[0][1]), uid))
                rec['paths'].append(('return', (spots[0][0],spots[0][1]), v.lcenter(loc) or v.start, uid))
            objs.append(rec)

    # resolve path geometry
    for o in objs:
        if o['type']=='escort' and o.get('escort_legs'):
            for src,dst in o['escort_legs']:
                a,b=v.ltile(src),v.ltile(dst)
                if not a or not b: continue
                seg,L,sa,sb=v.path(a,b)
                o['paths'].append(('escort', a, b, 0, seg, L))
        resolved=[]
        for item in o['paths']:
            if len(item)==6: resolved.append(item); continue
            kind,src,dst,uid=item
            if src is None or dst is None: continue
            seg,L,sa,sb=v.path(src,dst)
            resolved.append((kind,src,dst,uid,seg,L))
        o['paths']=resolved
        for item in o['paths']:
            o.setdefault('encounters',[])
            o['encounters'].append(v.enc(item[4]))
    return objs

def detect_waves(v):
    """Scripted enemy Create Unit + Order waves, with spawn time, origin, destination and travel."""
    # switch -> elapsed time that sets it (one-shot)
    switch_t={}
    for c,a,own in v.trigs:
        ets=[u32(x,8) for x in c if x[15]==12 and x[14] in (0,10)]
        if not ets: continue
        t0=min(ets)
        for x in a:
            if x[26]==13 and x[27]==4: switch_t[u32(x,20)]=t0
    waves=[]
    for c,a,own in v.trigs:
        if not any(x[26] in (44,45) and any(p in v.enemy for p in v.grp(u32(x,16),own)) for x in a): continue
        if not any(x[26]==46 and any(p in v.enemy for p in v.grp(u32(x,16),own)) for x in a): continue
        # spawn time
        t0=None
        ets=[u32(x,8) for x in c if x[15]==12 and x[14] in (0,10)]
        if ets: t0=min(ets)
        for x in c:
            if x[15]==11 and x[14]==2 and x[16] in switch_t: t0=switch_t[x[16]] if t0 is None else min(t0,switch_t[x[16]])
        if t0 is None: continue
        # hatchery-still-stands conditions are fine; we still count the wave
        creates=[]
        dest=None; origin=None
        for x in a:
            if x[26] in (44,45) and any(p in v.enemy for p in v.grp(u32(x,16),own)):
                uid=u16(x,24); n=x[27] or 1; loc=u32(x,0)
                creates.append((uid,n,loc)); origin=v.lcenter(loc) or origin
            if x[26]==46 and any(p in v.enemy for p in v.grp(u32(x,16),own)) and not v.whole(u32(x,20)):
                dest=v.lcenter(u32(x,20)); 
        if not creates or not origin or not dest: continue
        uid,n,loc=creates[0]
        seg,L,sa,sb=v.path(origin,dest)
        sec=travel_sec(L,uid)
        arrive=(t0+sec) if sec!=math.inf else math.inf
        # entry: first tile within 14 of the destination (player-base side)
        entry=None
        for x,y in seg:
            if math.hypot(x-dest[0],y-dest[1])<=14:
                entry=(x,y); break
        if entry is None and seg: entry=seg[-1]
        waves.append(dict(t0=t0,origin=origin,dest=dest,uid=uid,n=n,seg=seg,length=L,
                          travel=sec,arrive=arrive,entry=entry,
                          direction=compass(dest,entry or origin) if entry or origin else '?',
                          label=f't={t0:.0f}s {n}x {uname(uid)}'))
    waves.sort(key=lambda w: w['t0'])
    return waves

def wave_chokes(waves, cluster=8):
    """Cluster wave entry points. One cluster = one choke."""
    clusters=[]
    for w in waves:
        e=w.get('entry')
        if not e: continue
        placed=False
        for c in clusters:
            if math.hypot(e[0]-c[0][0], e[1]-c[0][1])<=cluster:
                c.append(e); placed=True; break
        if not placed: clusters.append([e])
    dirs=sorted({w.get('direction','?') for w in waves})
    return clusters, dirs

def render_routes(v, png, objs=(), waves=(), title=''):
    """Draw start, targets, paths and threats on a terrain (or walk-grid) underlay."""
    from PIL import Image, ImageDraw, ImageFont
    W,H=v.W,v.H
    under=None; scale=None
    try:
        import sclib
        tmp=tempfile.NamedTemporaryFile(suffix='.png',delete=False); tmp.close()
        sclib.render(v.map_path, tmp.name, {}, title or os.path.basename(v.map_path))
        raw=Image.open(tmp.name).convert('RGBA')
        os.unlink(tmp.name)
        # sclib adds a 110px legend bar under the map
        map_h=raw.size[1]-110 if raw.size[1]>110 else raw.size[1]
        under=raw.crop((0,0,raw.size[0],map_h))
        scale=under.size[0]/W          # px per tile (sclib: 32 * S, S=1024/(max(W,H)*32))
    except Exception:
        under=None
    if under is None:
        scale=8
        under=Image.new('RGBA',(W*scale,H*scale),(20,18,16,255))
        dr=ImageDraw.Draw(under)
        for y in range(H):
            for x in range(W):
                c=(70+((x*3+y*5)%20),62,48,255) if v.wk[y][x] else (28,26,24,255)
                dr.rectangle([x*scale,y*scale,(x+1)*scale-1,(y+1)*scale-1], fill=c)
        COL={0:(80,160,255,255),1:(220,60,60,255),7:(240,200,60,255),11:(160,160,160,255)}
        for u in v.U:
            col=COL.get(u['o'],(200,200,200,255)); x,y=u['x']/32*scale,u['y']/32*scale
            r=5 if u['id']>=106 else 3
            if u['id']==SLOC: dr.ellipse([x-7,y-7,x+7,y+7], outline=(255,255,255,255), width=2)
            elif u['id'] in (176,177,178): dr.rectangle([x-4,y-2,x+4,y+2], fill=(80,180,220,255))
            elif u['id']==188: dr.rectangle([x-6,y-3,x+6,y+3], fill=(60,200,90,255))
            else: dr.ellipse([x-r,y-r,x+r,y+r], fill=col, outline=(0,0,0,255))
    img=under.convert('RGBA')
    ov=Image.new('RGBA',img.size,(0,0,0,0)); dr=ImageDraw.Draw(ov)
    def xy(t): return t[0]*scale+scale/2, t[1]*scale+scale/2
    def draw_path(seg, col, width=4):
        if len(seg)<2: return
        pts=[xy(p) for p in seg]
        # outline
        dr.line(pts, fill=(0,0,0,200), width=width+2)
        dr.line(pts, fill=col, width=width)
    COLORS=[(0,220,255,230),(50,255,140,230),(255,180,40,230),(200,120,255,230),(255,255,80,230)]
    used=[]
    ci=0
    for o in objs:
        for item in o.get('paths') or []:
            kind,src,dst,uid,seg,L=item
            col=COLORS[ci%len(COLORS)]; ci+=1
            draw_path(seg,col,4)
            if src: 
                x,y=xy(src); dr.ellipse([x-10,y-10,x+10,y+10], outline=col, width=3)
            if dst:
                x,y=xy(dst); dr.rectangle([x-10,y-10,x+10,y+10], outline=col, width=3)
            used.append((kind,col,L,uid,o['name']))
    for w in waves:
        draw_path(w.get('seg') or [], (255,70,70,220), 3)
    # labels
    try:
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 16)
        font2=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
    except Exception:
        font=font2=ImageFont.load_default()
    def lab(tile, text, col):
        x,y=xy(tile)
        x=max(4,min(img.size[0]-8,x)); y=max(4,min(img.size[1]-20,y))
        dr.text((x,y), text, font=font, fill=col, stroke_width=3, stroke_fill=(0,0,0,255))
    def nearest_loc(tile):
        best,bd=None,1e9
        for i,n,l,tt,r,b in v.locs:
            if not n or n.lower()=='anywhere' or n.lower().startswith('ai town'): continue
            c=((l+r)/64,(tt+b)/64); d=math.hypot(c[0]-tile[0],c[1]-tile[1])
            if d<bd and d<10: bd=d; best=n
        return best
    lab(v.start, 'START', (255,255,255,255))
    seen_labs=set()
    for o in objs:
        for item in o.get('paths') or []:
            kind,src,dst,uid,seg,L=item
            if kind in ('start_to_target','escort') and dst:
                name=(o.get('target_loc') or nearest_loc(dst) or 'target')[:18]
                key=(round(dst[0]/4),round(dst[1]/4),name)
                if key not in seen_labs:
                    lab(dst, name, (255,255,220,255)); seen_labs.add(key)
            # a return that ends at the player start is already labelled START; do not stack 'return' on it
    img=Image.alpha_composite(img,ov)
    # legend bar
    legend=[title or os.path.basename(v.map_path),
            'Cyan/green/gold = objective paths; red = scripted attack waves. Circle = start of a path, square = target.']
    for o in objs:
        bits=[]
        for item,enc in zip(o.get('paths') or [], o.get('encounters') or []):
            kind,src,dst,uid,seg,L=item
            bits.append(f'{kind}: {travel_fmt(L,uid)}, {len(enc)} encounter(s)')
        legend.append(f"{o['type']}{' (optional)' if o.get('optional') else ''}: {o['name'][:60]}")
        for b in bits: legend.append('    '+b)
    for w in waves:
        legend.append(f"wave {w['label']}: {w['length']:.0f} tiles / {w['travel']:.0f}s, arrives t={w['arrive']:.0f}s from the {w['direction']}")
    if waves:
        cl,dirs=wave_chokes(waves)
        legend.append(f'scripted waves use {len(cl)} choke(s), directions: {", ".join(dirs)}')
    lh=18; box_h=16+lh*len(legend)
    bar=Image.new('RGB',(img.size[0], box_h),(18,14,12))
    bd=ImageDraw.Draw(bar)
    for i,line in enumerate(legend):
        bd.text((12, 8+i*lh), line, fill=(240,230,210), font=font2)
    out=Image.new('RGB',(img.size[0], img.size[1]+box_h))
    out.paste(img.convert('RGB'),(0,0)); out.paste(bar,(0,img.size[1])); out.save(png)
    return png

def analyze(path, png=None):
    v=MapView(path)
    objs=detect_objectives(v)
    waves=detect_waves(v)
    for o in objs:
        if o['type']=='survive' or (o['type']!='survive' and waves):
            o['waves']=waves
    if png: render_routes(v,png,objs,waves,title=os.path.basename(path))
    return v,objs,waves

def main(argv):
    import argparse
    ap=argparse.ArgumentParser(description='Trace objective paths, threats and waves on a BW map.')
    ap.add_argument('maps', nargs='+')
    ap.add_argument('--png', default='')
    ap.add_argument('--json', default='')
    a=ap.parse_args(argv)
    for i,p in enumerate(a.maps):
        png=a.png or os.path.join(os.path.dirname(os.path.abspath(p)) or '.', 'routes.png')
        if len(a.maps)>1 and a.png=='':
            png=os.path.join(os.path.dirname(os.path.abspath(p)) or '.', 'routes.png')
        v,objs,waves=analyze(p, png)
        print(f'### {p}  {v.W}x{v.H}  start=({v.start[0]:.1f},{v.start[1]:.1f})')
        print(f'    routes PNG: {png}')
        for o in objs:
            print(f"  {o['type']}{' optional' if o.get('optional') else ''}: {o['name']}")
            for item,enc in zip(o.get('paths') or [], o.get('encounters') or []):
                kind,src,dst,uid,seg,L=item
                print(f'    {kind}: {travel_fmt(L,uid)}; {len(enc)} threat encounter(s)')
                for e in enc:
                    print('      - '+'; '.join(e[1][:4]))
            if o['type']=='survive':
                print(f"    timer={o.get('timer')}s")
        if waves:
            cl,dirs=wave_chokes(waves)
            print(f'  {len(waves)} scripted wave(s), {len(cl)} choke(s), directions {dirs}')
            for w in waves:
                print(f"    {w['label']}: path {w['length']:.0f} tiles / {w['travel']:.0f}s, arrives t={w['arrive']:.0f}s from the {w['direction']}, entry {w['entry']}")
        notes,easy=parse_notes(p)
        if notes:
            print('  OBJECTIVE_PATHS lines:', len(notes))
        if easy: print('  EASY_OK:', easy)
        if a.json:
            def ser(o):
                d={k:v for k,v in o.items() if k not in ('paths','encounters','waves')}
                d['paths']=[{'kind':k,'src':s,'dst':t,'uid':u,'length':L,'encounters':len(e)} for (k,s,t,u,seg,L),e in zip(o.get('paths') or [], o.get('encounters') or [])]
                return d
            json.dump({'map':p,'start':v.start,'objectives':[ser(o) for o in objs],
                       'waves':[{k:w[k] for k in w if k!='seg'} for w in waves]},
                      open(a.json,'w'), indent=1, default=str)
if __name__=='__main__':
    main(sys.argv[1:])
