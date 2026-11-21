#!/usr/bin/env python3
"""scene_location_visible: when a dialogue scene points the camera (Center View) or a Transmission at a location, the
human can see that location from the scene's first line. Otherwise the player watches a black screen while the
characters talk.
   python3 tools/bw/check_scene_view.py MAP.scx [...]      (exit 1 on FAIL)

A scene = a trigger owned by a human with Transmission (7) or Display Text (9) plus Center View (10), or a
Transmission whose location is not the whole map. The scene location is the Center View location (else the first
Transmission's location). Vision counts as present when, at the moment the camera arrives (the Center View action;
for a Transmission-only scene its first located line), one of these holds
(static simulation, nothing is assumed about unit movement):
  own units      a pre-placed unit of the human, one created for or given to the human by an earlier trigger or
                 earlier in the same trigger, or a Bring condition of the scene trigger for the human, within SIGHT
                 tiles of the location centre
  ally vision    a unit (pre-placed or created as above) of a player whose shared vision the human has at that moment
                 (force with Allies + Shared vision flags, or 'Turn ON Shared Vision' run by an earlier human trigger
                 or earlier in the same trigger) within SIGHT tiles
  revealer       a Map Revealer created for the human at that location (or within SIGHT tiles) earlier in the same
                 trigger, or by an earlier trigger that does not remove it again
'Earlier trigger' = a mission-start trigger, or a trigger that sets a switch the scene trigger requires (transitively).
Rules: a Center View scene without vision = FAIL; a Transmission-only scene without vision = WARN.
Design note: 'SCENE_VIEW: <scene> :: <location> :: <alliance-vision | revealer | own units present>'. A scene the
simulation cannot prove but whose note says 'own units present' (units walk there) is a WARN, not a FAIL.
A Center View scene whose location has no SCENE_VIEW line is a WARN."""
import sys,os,re,struct,math
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from check_ally_vision import sections,note_files,is_start
from eudplib.bindings._rust import mpqapi
SIGHT=8          # tiles: typical unit sight; a Map Revealer sees 10
REVEALER=101
def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def u16(b,o): return struct.unpack_from('<H',b,o)[0]
def strings(S):
    if 'STRx' in S:
        b=S['STRx']; n=u32(b,0)
        def g(j): o=u32(b,4*j); return b[o:b.index(b'\0',o)].decode('utf8','replace') if 0<j<=n else ''
    else:
        b=S.get('STR ',b'\0\0'); n=u16(b,0)
        def g(j): o=u16(b,2*j); return b[o:b.index(b'\0',o)].decode('utf8','replace') if 0<j<=n else ''
    return g
def notes(path):
    out={}
    for f in note_files(path):
        for l in open(f,encoding='utf8',errors='replace'):
            m=re.search(r'SCENE_VIEW:\s*(.+?)\s*::\s*(.+?)\s*::\s*(alliance-vision|revealer|own units present)',l,re.I)
            if m: out[m.group(2).strip().lower()]=(m.group(1).strip(),m.group(3).lower())
    return out
def run(path):
    S=sections(bytes(mpqapi.MPQ.open(path).extract_file('staredit\\scenario.chk'))); st=strings(S)
    ownr=S['OWNR']; fo=S.get('FORC',b'')+b'\0'*20; forces=list(fo[:8]); fflags=list(fo[16:20])
    hum={p for p in range(8) if ownr[p]==6}
    W,H=struct.unpack('<HH',S['DIM ']); MR=S.get('MRGN',b'')
    def rect(l): return struct.unpack_from('<IIII',MR,(l-1)*20) if 0<l<=len(MR)//20 else None
    def lname(l): return st(u16(MR,(l-1)*20+16)) if rect(l) else '?'
    def centre(l): r=rect(l); return ((r[0]+r[2])/2,(r[1]+r[3])/2)
    def whole(l):
        r=rect(l); return not r or l==64 or (r[2]-r[0]>=W*32*0.6 and r[3]-r[1]>=H*32*0.6)
    def near(xy,l,rad=SIGHT): c=centre(l); return math.hypot(xy[0]-c[0],xy[1]-c[1])<=rad*32
    def grp(t,own):
        if 0<=t<8: return [t]
        if t==13: return list(own)
        if t==17: return list(range(8))
        if 18<=t<=21: return [p for p in range(8) if forces[p]==t-18]
        return []
    U=S.get('UNIT',b''); placed=[(u16(U,i+4),u16(U,i+6),u16(U,i+8),U[i+16]) for i in range(0,len(U)-len(U)%36,36)]
    T=S.get('TRIG',b''); trigs=[]
    for t in range(0,len(T)-len(T)%2400,2400):
        r=T[t:t+2400]
        c=[r[i*20:i*20+20] for i in range(16) if r[i*20+15]]
        a=[r[320+i*32:352+i*32] for i in range(64) if r[320+i*32+26]]
        own={o for q in range(28) if r[2372+q] for o in grp(q,())}
        trigs.append((c,a,own))
    need=[{x[16] for x in c if x[15]==11 and x[14]==2} for c,a,o in trigs]
    sets=[{u32(x,20) for x in a if x[26]==13 and x[27]==4} for c,a,o in trigs]
    start=[is_start(c) for c,a,o in trigs]
    def earlier(d):
        """triggers that have run before trigger d can fire: mission start + setters of its required switches (transitive)"""
        seen=set(i for i in range(len(trigs)) if start[i] and i!=d); todo=set(need[d]); done=set()
        while todo:
            k=todo.pop(); done.add(k)
            for i in range(len(trigs)):
                if i!=d and k in sets[i] and i not in seen:
                    seen.add(i); todo|=need[i]-done
        return seen
    def effects(acts,own,state):
        """apply actions to the vision state: created units per player, shared vision received, live revealers"""
        units,vis,rev=state
        for x in acts:
            ty=x[26]; l=u32(x,0); pl=grp(u32(x,16),own); uid=u16(x,24)
            if ty in (44,45) and rect(l):
                for p in pl:
                    if uid==REVEALER: rev.add((p,l))
                    else: units.append((centre(l),p))
            elif ty in (22,23,24,25) and uid in (REVEALER,229):
                for p in pl: rev-={(q,k) for q,k in rev if q==p and (ty in (22,23) or k==l or uid==229)}
            elif ty==48 and rect(l):     # Give Units to Player: the new owner has units there
                for p in grp(u32(x,20),own): units.append((centre(l),p))
            elif ty in (15,16):
                s=struct.pack('<I',u32(x,20))
                if s[1:3]==b'Vi' and s[3:4].isdigit():
                    for o in own:
                        if s[:1]==b'+': vis.add((o,int(s[3:4])))
                        elif s[:1]==b'-': vis.discard((o,int(s[3:4])))
        return units,vis,rev
    base_vis=set()
    for f in range(4):
        mem=[p for p in range(8) if forces[p]==f]
        if fflags[f]&2 and fflags[f]&8: base_vis|={(a,b) for a in mem for b in mem if a!=b}
    NV=notes(path); F=[]; Wn=[]; scenes=0
    for d,(c,a,own) in enumerate(trigs):
        if not own&hum: continue
        lines=[i for i,x in enumerate(a) if x[26] in (7,9)]
        if not lines: continue
        first=lines[0]
        cv=[u32(x,0) for x in a if x[26]==10 and rect(u32(x,0))]
        tl=[u32(a[i],0) for i in lines if a[i][26]==7 and rect(u32(a[i],0)) and not whole(u32(a[i],0))]
        if cv: l=cv[0]; kind='Center View'; first=next(i for i,x in enumerate(a) if x[26]==10 and u32(x,0)==l)   # the camera arrives here
        elif tl: l=tl[0]; kind='Transmission'; first=next(i for i in lines if a[i][26]==7 and u32(a[i],0)==l)
        else: continue
        if whole(l): continue
        scenes+=1
        state=([( (x,y),o) for x,y,uid,o in placed],set(base_vis),set())
        for e in sorted(earlier(d)): state=effects(trigs[e][1],trigs[e][2],state)
        for x in c:     # Bring: the trigger only fires while the player has units at that location
            if x[15]==3 and rect(u32(x,0)) and not whole(u32(x,0)) and u32(x,8)>=1 and x[14] in (0,10):
                for p in grp(u32(x,4),own): state[0].append((centre(u32(x,0)),p))
        state=effects(a[:first],own,state)
        units,vis,rev=state
        ok=[]
        for h in own&hum:
            if any(o==h and near(xy,l) for xy,o in units): ok.append('own units')
            if any((h,o) in vis and o!=h and near(xy,l) for xy,o in units): ok.append('ally vision')
            if any(p==h and (k==l or near(centre(k),l,10)) for p,k in rev): ok.append('revealer')
        name=lname(l); txt=next((st(u32(a[i],4)) for i in lines),'')[:60].replace('\n',' ')
        if ok:
            if kind=='Center View' and name.lower() not in NV: Wn.append(f"trig{d}: scene at '{name}' has vision ({ok[0]}) but no design-note line 'SCENE_VIEW: <scene> :: {name} :: <alliance-vision | revealer | own units present>'")
            continue
        msg=f"trig{d}: {kind} scene at '{name}' starts with no vision for the human (no own units within {SIGHT} tiles, no ally vision, no Map Revealer before the first line) - first line: {txt!r}"
        decl=NV.get(name.lower())
        if kind=='Transmission' and decl: continue     # a radio line at a declared place: the note answers it
        if kind=='Transmission' or (decl and decl[1]=='own units present'): Wn.append(msg+(' (note says own units present: cannot be proven statically)' if decl else ''))
        else: F.append(msg)
    out=[('FAIL' if F else 'OK  ')+f' scene_location_visible: dialogue scenes can be seen from their first line ({scenes} located scenes)'+''.join('\n     - '+f for f in F[:10])]
    if Wn: out.append('WARN scene_location_visible:'+''.join('\n     - '+w for w in Wn[:10]))
    return out
if __name__=='__main__':
    rc=0
    for p in sys.argv[1:]:
        print('###',p)
        for l in run(p): print(l); rc|=l.startswith('FAIL')
    sys.exit(rc)
