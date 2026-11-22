#!/usr/bin/env python3
"""objective_shortcuts: a reach/rescue/capture objective cannot be skipped with what the player owns or can build.
   python3 tools/bw/check_objective_shortcuts.py MAP.scx [...]      (run from the repository root; exit 1 on FAIL)

Sasbe t1025: 'reach the kiln with a unit' was finished by lifting a Barracks, flying it over every guarded cut to
the kiln, landing and training a Marine there. The ground path had four guard posts; the air line had none.

For every human-owned objective trigger with 'Bring <player> <unit or group> at least 1 at <location>' (a trigger
that wins, sets objectives, gives units/resources, or sets a switch such a trigger needs), the check looks at what
the human player can actually field (pre-placed units plus everything reachable through a production chain under
the map's Unit/Upgrade/Tech settings) and lists the shortcut vectors that satisfy that Bring:
  lift-off   a liftable Terran building (Command Center, Barracks, Factory, Starport; Engineering Bay and Science
             Facility for 'Any unit'/'Buildings') flies to the location, lands and trains a counted unit there
  flyer      a flying unit that the Bring counts (Wraith, Dropship, Valkyrie, Science Vessel, Battlecruiser,
             Overlord, Mutalisk, Scourge, Queen, Guardian, Devourer, Shuttle, Scout, Corsair, Carrier, Arbiter, Observer)
  transport  Dropship, Shuttle, or Overlord with Ventral Sacs carries counted ground units (also a named rescuee)
  recall     an Arbiter with Recall brings counted ground units
  nydus      a Nydus Canal (exit needs creep near the target)              -> WARN
  cloak      Ghost with Personnel Cloaking, Wraith with Cloaking Field, Dark Templar walk past guards that have no
             detection                                                     -> WARN
For lift-off, flyer, transport and recall the air line from the nearest origin (a liftable building or the start)
to the location is checked for anti-air encounters (enemy units with an air weapon, Missile Turret, Spore Colony,
Photon Cannon, Bunker, within 7 tiles, clustered like path encounters). The vector is blocked when the air line has
at least as many anti-air encounters as min(2, ground-path encounters), when the counted unit cannot use it (a named
ground unit that is not trainable at the target), when the needed unit/tech is not available, or when the same
trigger also needs the location cleared of enemies and at least 3 armed enemy units guard it (the fight stays).
Design note:
  OBJECTIVE_SHORTCUTS: <objective or location> :: <vectors the player has> :: <how each one is blocked or why it is fine>
  SHORTCUT_OK: <objective or location> :: <vector> :: <reason>       (accepts one open vector)
FAIL: an open vector without SHORTCUT_OK; or an objective with any vector (open or blocked) and no
OBJECTIVE_SHORTCUTS line. WARN: nydus and cloak vectors (static guess; the enemy AI may build detection or creep).
Static check: it does not play the game; the in-game proof is a playtest that tries the shortcut."""
import sys,os,math,re,struct
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import mission_model as MM
from mission_model import u32,u16
P=MM.P
LIFT={106:(7,),111:(0,32,34,1),113:(2,5,3),114:(8,11,9,58,12),116:(),122:()}
LIFT_SPEED=1.67      # px/frame at Fastest while lifted (Staredit Network unit speed table)
FLYERS={8:6.67,11:5.47,9:5.0,12:2.5,58:6.6,42:0.83,43:6.67,47:6.67,45:6.67,44:2.5,62:5.0,69:4.43,70:5.0,60:6.67,72:3.33,71:5.0,84:3.33}
TRAIN_SEC={7:300,0:360,32:360,34:450,1:750,2:450,5:750,3:600,8:900,11:750,9:1200,58:750,12:2000}   # build frames
TRANSPORTS={11:'Dropship',69:'Shuttle',42:'Overlord'}
AA_BUILD={124,144,162,125}
VENTRAL=24; RECALL=21; PCLOAK=10; WCLOAK=9
DETECTORS={124,144,162,42,9,84}

def counts(group,uid):
    """does a Bring of 'group' count unit uid"""
    b=MM.is_building(uid)
    if group==MM.ANY: return True
    if group==MM.MEN: return not b
    if group==MM.BUILDINGS: return b
    if group==MM.FACTORIES: return uid in (106,111,113,114,131,132,133,154,160,155,167)
    return group==uid

def objective_brings(M):
    v=M.v; setters=M.switch_setters()
    key_trigs=set()
    for i,(c,a,own) in enumerate(v.trigs):
        if not M.human_trig(own): continue
        if any(x[26] in (1,12,48,26) or (x[26]==44 and set(v.grp(u32(x,16),own))&v.hum) for x in a): key_trigs.add(i)
    needed=set()
    for i in key_trigs:
        needed|={x[16] for x in v.trigs[i][0] if x[15]==11 and x[14]==2}
    out=[]
    for i,(c,a,own) in enumerate(v.trigs):
        if not M.human_trig(own): continue
        sets={u32(x,20) for x in a if x[26]==13 and x[27] in (4,6)}
        if i not in key_trigs and not sets&needed: continue
        for x in c:
            if x[15]!=3 or x[14] not in (0,10) or u32(x,8)<1: continue
            loc=u32(x,0)
            if v.whole(loc): continue
            pl=set(v.grp(u32(x,4),own))
            if not pl&v.hum: continue
            # 'the location must be clear of enemies' in the same trigger: the fight at the target stays
            clear=any(y[15] in (2,3) and y[14] in (1,10) and u32(y,8)==0 and u32(y,0)==loc and set(v.grp(u32(y,4),own))&v.enemy for y in c)
            r=v.rect(loc); guards=0
            if clear and r:
                guards=sum(1 for u in v.U if u['o'] in v.enemy and (u['id'] in P.GROUND_ARMED or u['id'] in P.TOWERS) and u['id'] not in P.WORKERS
                           and r[0]<=u['x']<r[2] and r[1]<=u['y']<r[3])
            out.append(dict(trig=i,loc=loc,lname=v.lname(loc),group=u16(x,12),qty=u32(x,8),guards=guards,
                            victory=any(y[26]==1 for y in a),players=sorted(pl&v.hum)))
    # one entry per (location, group)
    seen=set(); uniq=[]
    for o in out:
        k=(o['loc'],o['group'])
        if k in seen: continue
        seen.add(k); uniq.append(o)
    return uniq

def air_line(a,b):
    n=max(1,int(math.hypot(b[0]-a[0],b[1]-a[1])))
    return [(a[0]+(b[0]-a[0])*k/n, a[1]+(b[1]-a[1])*k/n) for k in range(n+1)]

def aa_threats(v):
    out=[]
    for u in v.U:
        if u['o'] not in v.enemy: continue
        uid=u['id']; d=P.DB['units'].get(str(uid))
        air=(d and d.get('air') is not None and uid not in P.WORKERS) or uid in AA_BUILD
        if air: out.append((u['x']/32,u['y']/32,uid,'anti-air'))
    return out

def ground_encounters(M,o):
    v=M.v; c=v.lcenter(o['loc'])
    for ob in M._objs:
        if ob.get('target_loc')==o['lname'] or (ob.get('return_loc')==o['lname']):
            n=sum(len(e) for item,e in zip(ob.get('paths') or [],ob.get('encounters') or []) if item[0] in ('start_to_target','return','escort'))
            L=sum(item[5] for item in ob.get('paths') or [] if item[5]!=math.inf)
            return n,L,ob['name']
    seg,L,_,_=v.path(v.start,c)
    return len(v.enc(seg)),L,None

def note_lines(text,key):
    out=[]
    for m in re.finditer(key+r':\s*(.+)',text):
        out.append([p.strip() for p in m.group(1).split('::')])
    return out

def matches(head,o,objname):
    h=(head or '').lower()
    if o['lname'] and o['lname'].lower() in h: return True
    if objname and MM.P.__dict__.get('D') is None:
        pass
    if objname:
        import mission_duration as D
        return D.line_matches(head,{'name':objname,'type':''})
    return False

def run(path,M=None):
    sys.path.insert(0,os.path.join(MM.ROOT,'tools','lib'))
    M=M or MM.Model(path); v=M.v
    M._objs=P.detect_objectives(v)
    brings=objective_brings(M)
    if not brings:
        return ['OK   objective_shortcuts: no Bring-to-location objective for the human player']
    lines_sc=note_lines(M.notes,'OBJECTIVE_SHORTCUTS'); lines_ok=note_lines(M.notes,'SHORTCUT_OK')
    aa=aa_threats(v)
    det=[(u['x']/32,u['y']/32) for u in v.U if u['o'] in v.enemy and u['id'] in DETECTORS]
    out=[]; anyF=False
    for o in brings:
        p=o['players'][0]
        units,ups,techs=MM.tech_of(M.S,p)
        obt=MM.obtainable(M.S,p,M.placed[p]) if MM.can_produce(M,p) else set(M.placed[p])
        tgt=v.lcenter(o['loc'])
        genc,glen,objname=ground_encounters(M,o)
        need=min(2,genc)
        vectors=[]   # (name, origin, speed px/f, extra sec, blocked_reason or None, detail)
        # lift-off
        for b,trains in LIFT.items():
            if b not in obt: continue
            ok_units=[t for t in trains if t in obt and counts(o['group'],t)]
            if counts(o['group'],b) or ok_units:
                origins=[(u['x']/32,u['y']/32) for u in v.U if u['o']==p and u['id']==b] or [v.start]
                org=min(origins,key=lambda q: math.hypot(q[0]-tgt[0],q[1]-tgt[1]))
                extra=0 if counts(o['group'],b) else min(TRAIN_SEC.get(t,600) for t in ok_units)/24
                what=MM.uname(b).replace('Terran ','')+(' lands' if counts(o['group'],b) else ' lands and trains '+'/'.join(MM.uname(t).replace('Terran ','') for t in ok_units[:3]))
                vectors.append(['lift-off',org,LIFT_SPEED,extra,what])
        # flyers
        fl=[f for f in FLYERS if f in obt and counts(o['group'],f)]
        if fl:
            best=max(fl,key=lambda f: FLYERS[f])
            vectors.append(['flyer',v.start,FLYERS[best],0,'/'.join(MM.uname(f).split(' ',1)[-1] for f in fl[:4])])
        # a named unit that flies by itself (e.g. a rescued Queen) ignores the ground return path
        if o['group']<228 and o['group'] in FLYERS and o['group'] not in fl:
            r=v.rect(o['loc'])
            spots=[(u['x']/32,u['y']/32) for u in v.U if u['id']==o['group'] and (u['o'] in v.hum or u['o'] in v.rescue)
                   and not (r and r[0]<=u['x']<r[2] and r[1]<=u['y']<r[3])]     # already inside: that Bring is the pick-up, not a trip
            if spots:
                vectors.append(['flyer',min(spots,key=lambda q: math.hypot(q[0]-tgt[0],q[1]-tgt[1])),FLYERS[o['group']],0,MM.uname(o['group'])+' flies by itself'])
        # transports (carry ground units the Bring counts)
        ground_ok=any(counts(o['group'],u) and not MM.is_building(u) and u not in FLYERS for u in obt|{o['group']} if u<228)
        tr=[t for t in TRANSPORTS if t in obt and (t!=42 or ups.get(VENTRAL,0)>=1 and (132 in obt or 133 in obt))]
        if tr and ground_ok:
            vectors.append(['transport',v.start,max(FLYERS[t] for t in tr),0,'/'.join(TRANSPORTS[t] for t in tr)])
        if 71 in obt and (techs.get(RECALL,(False,False))[0] or techs.get(RECALL,(False,False))[1]) and ground_ok:
            vectors.append(['recall',v.start,FLYERS[71],0,'Arbiter with Recall'])
        warns=[]
        if 134 in obt and ground_ok: warns.append('nydus: a Nydus Canal can open next to the target if creep reaches it')
        cl=[]
        if 1 in obt and counts(o['group'],1) and techs.get(PCLOAK,(0,0))[0]: cl.append('Ghost (Personnel Cloaking)')
        if 8 in obt and counts(o['group'],8) and techs.get(WCLOAK,(0,0))[0]: cl.append('Wraith (Cloaking Field)')
        if 61 in obt and counts(o['group'],61): cl.append('Dark Templar')
        if cl:
            seg,_,_,_=v.path(v.start,tgt)
            dhit=[d for d in det if any(math.hypot(d[0]-x,d[1]-y)<=9 for x,y in seg[::3])]
            if not dhit: warns.append(f"cloak: {', '.join(cl)} can walk past the guards (no pre-placed detector near the ground path)")
        oks=[l for l in lines_ok if l and matches(l[0],o,objname)]
        has_sc=any(l and matches(l[0],o,objname) for l in lines_sc)
        F=[]; info=[]
        best={}
        for name,org,spd,extra,what in vectors:
            line=air_line(org,tgt)
            enc=P.encounters([(int(x),int(y)) for x,y in line],aa)
            dist=math.hypot(tgt[0]-org[0],tgt[1]-org[1])
            sec=dist*32/(spd*24)+extra
            k=(len(enc),sec)
            if name not in best or k<best[name][0]: best[name]=(k,name,what,dist,sec,enc)
        for k,name,what,dist,sec,enc in [best[n] for n in sorted(best)]:
            st=f"{name} ({what}): {dist:.0f} tiles air line, about {sec:.0f}s, {len(enc)} anti-air encounter(s) vs {genc} on the ground path"
            waived=[l for l in oks if len(l)>1 and l[1].lower().startswith(name)]
            if o.get('guards',0)>=3 and len(enc)<need:
                info.append(st+f" -> blocked: the same trigger needs the location cleared of its {o['guards']} armed guards, so the fight at the target stays")
            elif len(enc)>=need or genc==0:
                info.append(st+' -> blocked' if genc else st+' (ground path has no encounters either; objective_paths judges it)')
            elif waived:
                info.append(st+f" -> SHORTCUT_OK ({waived[0][-1][:80]})")
            else:
                F.append(st+f"; the objective can be skipped this way. Block it (anti-air on the air line, a counted unit the player cannot train or fly, the tech or unit disabled, no landing space at the target) or accept it with 'SHORTCUT_OK: {o['lname']} :: {name} :: <reason>'")
        if vectors and not has_sc:
            F.append(f"design note lacks 'OBJECTIVE_SHORTCUTS: {objname or o['lname']} :: <vectors the player has: {', '.join(sorted({x[0] for x in vectors}))}> :: <how each one is blocked or why it is fine>'")
        head=f"Bring {MM.uname(o['group'])} to '{o['lname']}' (trigger {o['trig']}{', victory' if o['victory'] else ''}"+(f", objective '{objname}'" if objname else '')+")"
        tag='FAIL' if F else 'OK  '
        anyF|=bool(F)
        body='; '.join(info) if info else ('no shortcut vector available to the player' if not vectors else '')
        out.append(f"{tag} objective_shortcuts: {head}: {body}"+''.join('\n     - '+f for f in F))
        if warns: out.append('WARN objective_shortcuts: '+head+''.join('\n     - '+w for w in warns))
    return out

if __name__=='__main__':
    rc=0
    for p in sys.argv[1:]:
        print('###',p)
        for l in run(p): print(l); rc|=l.startswith('FAIL')
    sys.exit(rc)
