#!/usr/bin/env python3
"""MANDATORY before any SC:BW map is delivered:  python3 predelivery_check.py MAP.scx [...]
Parses the FINAL .scx (not the build script) and exits 1 on any FAIL. Checks:
 1 every human player gets a deliberate Set Resources (minerals AND gas, Set To) at mission start
 2 pre-placed gas buildings carry gas (>0)
 3 no Create Unit (+ no Map Revealer created after Pause Game) (except Map Revealer) at mission start / during the opening; opening camera targets contain pre-placed units
 4 Terran addons attached to a parent (addon top-left = parent top-left + (4,1))
 5 enemy (computer) mineral patches >= 2500, geysers >= 10000 (near their town halls)
 6 every unit ID (placed and trigger-created) is a real BW unit (data/bw/bw_unit_ids.json)
 7 tech tree (check_tech.check_sections)
 8 dialogue: silence between two spoken lines <= 1 s (briefing + in-mission, incl. trigger-pass latency)
36-41 story delivery and campaign map shape (check_story_delivery.py): briefing present (NO_BRIEFING_OK), voiced dialogue
   and no character lines as plain text (NO_VOICE_OK), no escaped colour-code residue (u0003, \\x03, <03>),
   check_map_design_bw.py and the cliff-shape rule (bw_cliff_outlines) for campaign maps too, and every objective reward
   (resources added, units given/created after an event) has a REWARD_WHY line with an in-world source.
Robustness: a crashing sub-check is a FAIL with its error and the remaining checks still run; maps without optional
   sections (UNIS, MBRF, WAV, PUPx ...) are checked with game defaults instead of crashing.
 9 terrain: tile doodads must blend into the ground (no hard rectangles)
10 structures named in dialogue/objectives exist pre-placed (unless the text asks the player to build/bring/land one)
11 no leaderboards for objective progress (cannot be removed in BW); counters paced under hyper triggers; every objective line gets a done/removed version
13 camera moves at timers/events (ET>=60 s or countdown) point where a scripted effect acts within -2..+10 s
14 heroes the player gains mid-mission come from a Rescuable player (no direct Give Units of a hero to the human)
15 Modify Unit Hit Points <100% only on units created in the same trigger (else it heals damaged units)
16 effect-only players (no units, no AI): every unit they get is made invincible and killed (Kill Unit) in the same trigger, no orders, no alliance/AI
17 effect units: max 1 per location per trigger, count 1, air units
18 mineral lines are staggered (Blizzard arc), not straight flush rows
19 no attack announcements in Display Text/Transmission unless <map>.announce_ok.txt (or build info/design note) has 'ANNOUNCE_OK: <reason>'
21 town hall to geyser gap 3..5 tiles, nearest minerals 2..4 tiles (hall_gap.py; refinery touching the CC = FAIL)
22 rescue scene: rescuable units within 8 tiles of enemy units FAIL unless the enemy is set hostile (Set Alliance Status) to them by trigger
24 core abilities: every available unit/building (placed or buildable) has its core spells enabled and researched or researchable (core_tech.py)
23 every armed unit (placed, buildable or customised, heroes included) deals >0 base damage; UNIx weapon table is by WEAPON id; UNIS/UNIx consistent (unit_damage.py)
25 every pre-placed Refinery/Extractor/Assimilator has a same-owner town hall within 12 tiles, unless listed in <map>.gas_ok.json {"sites":[{"pos":[tx,ty],"reason":"..."}]}
28 every Map Revealer created by trigger is removed later (Remove/Kill Unit [at Location] of Map Revealer) unless a Comment in that trigger says REVEAL_PERMANENT_OK
29 WARN: enemy-base mineral fields (within 12 tiles of a computer town hall) above 4000
30 side-quest timing: the first optional-objective announcement (Display Text/Transmission/Set Mission
   Objectives containing 'OPTIONAL', not '...complete') fires >= 60 s after the intro end (first Set Mission Objectives,
   else end of the opening triggers). Times are chained: Elapsed Time conditions, Switch conditions set by earlier timed
   triggers, Wait/Transmission durations inside a trigger. Proximity/countdown-driven reveals are reported, not timed.
   Exception: Comment 'SIDEQUEST_TIMING_OK' in the announcing trigger.
31 tech progression: in a campaign folder (missions named M<n>_*.scx / ML<n>_*.scx),
   mission N must unlock tech that mission N-1 did not have (unit/building availability PUNI, upgrade max levels PUPx/UPGx,
   tech available/researched PTEx/TECx) for the human player(s). Placed or trigger-given units are not tech.
   Exception: 'TECH_SAME_OK :: <reason>' in the Design_Note/build info/<map>.tech_ok.txt (e.g. hero-only mission).
12 a started countdown timer has a Countdown = 0 trigger with a real effect (directly or via a switch it sets)
34 scmdraft_open: the map opens in ScmDraft 2 -- dd2_named_doodads: every DD2 doodad is a named tileset doodad (an unnamed cv5 slot aborts
   the whole load); plus a real ScmDraft 2 run under wine when the harness is installed (check_scmdraft_open.py,
   scmdraft_harness/README.md). SCMDRAFT_REAL=0 skips only the real run.
35 ally_shared_vision: every player allied with a human shares vision both ways (FORC shared-vision flag, or Run AI
   Script 'Turn ON Shared Vision for Player N' in the same trigger as Set Alliance Status, owner = receiver); vision
   off again when the alliance ends. Vision must start exactly when the alliance starts: every 'Turn ON Shared Vision'
   sits in a trigger that sets that alliance; if an alliance changes mid-mission, the design note says when it begins
   ('ALLIANCE_STARTS: P<n> :: start' or ':: switch <k> :: <event>') and no vision for that pair is turned on before it.
   Exemption: 'ALLY_NO_VISION_OK: P<n> :: reason' (allied without vision) in the design note (check_ally_vision.py)
42 hero_own_color: important computer heroes (general, commander, antagonist) have their own player slot and a colour
   of their own; that slot has the same alliances, vision and switch conditions as its faction, and victory/defeat
   triggers read it too. Design note 'HERO_SLOT: <hero> :: P<h> :: faction P<f>'; exemption 'HERO_COLOR_SHARED:
   <hero> :: reason' (check_hero_own_color.py)
"""
DBG=0
import sys,os,struct,json,re,subprocess,tempfile
sys.path.insert(0,'data/bw/tech'); sys.path.insert(0,'tools/bw'); sys.path.insert(0,'tools/lib/bw')
import check_tech, seams, sclib
from eudplib.bindings._rust import mpqapi
IDS={int(k):v for k,v in json.load(open('data/bw/bw_unit_ids.json')).items()}
ADDONS={107:106,108:106,115:114,117:116,118:116,120:113}
HALLS={106,131,132,133,154}; GASB={110,149,157}
NAMES={'Command Center':106,'Bunker':125,'Missile Turret':124,'Barracks':111,'Factory':113,'Starport':114,'Supply Depot':109,'Refinery':110,
 'Academy':112,'Engineering Bay':122,'Armory':123,'Science Facility':116,'Comsat':107,'Nexus':154,'Pylon':156,'Gateway':160,'Stargate':167,
 'Photon Cannon':162,'Forge':166,'Templar Archives':165,'Hatchery':131,'Lair':132,'Hive':133,'Spawning Pool':142,'Spire':141,'Sunken':146,'Spore':144,
 'Defiler Mound':136,'Ultralisk Cavern':140,'Hydralisk Den':135,'Nydus':134,'Queen\'s Nest':138,'Evolution Chamber':139}
MAKE=re.compile(r'\b(build|bring|land|clear a pad|have a|construct|morph|warp in|need(s)? a|get a|get \w+ up)\b',re.I)
def tech_set(S):
    """union over human players of available tech: U:<unit>, R:<upg>:<lvl>, T:<tech>"""
    ownr=S['OWNR']; side=S['SIDE']; puni=S['PUNI']; pupx=S.get('PUPx') or b''; ptex=S.get('PTEx') or b''
    race={0:'Zerg',1:'Terran',2:'Protoss'}; out=set(); gu=puni[12*228:13*228]
    for p in range(8):
        if ownr[p]!=6: continue
        rc=race.get(side[p]); ud=puni[13*228+p*228:13*228+p*228+228]
        for u,d in check_tech.UNITS.items():
            if d['race']==rc and (gu[u] if ud[u] else puni[p*228+u]) and d['how']!='auto' and not d['how'].startswith('tech:'): out.add(f'U:{u}')
        if pupx:
            for i in range(61):
                mx=pupx[12*61*2+i] if pupx[12*61*2+61*2+p*61+i] else pupx[p*61+i]
                out|={f'R:{i}:{L}' for L in range(1,mx+1)}
        if ptex:
            for i in range(44):
                dflt=ptex[12*44*2+44*2+p*44+i]
                av=ptex[12*44*2+i] if dflt else ptex[p*44+i]; rs=ptex[12*44*2+44+i] if dflt else ptex[12*44+p*44+i]
                if av or rs: out.add(f'T:{i}')
    return out
def mission_no(path):
    m=re.match(r'M[A-Z]?(\d+)[_.]',os.path.basename(path)); return int(m.group(1)) if m else None
def tech_same_ok(path):
    d=os.path.dirname(path); b=os.path.splitext(os.path.basename(path))[0]; pre=b.split('_')[0]
    for f in [path[:-4]+'.tech_ok.txt',f'{d}/{pre}_Design_Note.md',f'{d}/{pre}_build_info.json',f'{d}/Design_Note.md',f'{d}/../Design_Note.md']:
        if os.path.exists(f):
            for l in open(f,encoding='utf8',errors='replace'):
                if 'TECH_SAME_OK' in l and (pre in l or not re.search(r'TECH_SAME_OK\s*M[A-Z]?\d',l)): return l.strip()
    return None
def tech_progression(path):
    n=mission_no(path)
    if n is None: return 'OK   tech progression: not a numbered campaign mission'
    pr=[f for f in os.listdir(os.path.dirname(path) or '.') if f.endswith('.scx') and mission_no(f)==n-1]
    if not pr: return f'OK   tech progression: no mission {n-1} in this folder (baseline)'
    prev=os.path.join(os.path.dirname(path),sorted(pr)[0]); A=tech_set(secs(prev)); B=tech_set(secs(path))
    new=sorted(B-A); lost=sorted(A-B)
    def nm(k):
        t=k.split(':'); i=int(t[1])
        return {'U':check_tech.UN,'R':check_tech.UPN,'T':check_tech.TNN}[t[0]].get(i,k)+(f' L{t[2]}' if t[0]=='R' else '')
    info=f'tech vs {os.path.basename(prev)}: {len(B)} vs {len(A)} entries; new [{", ".join(map(nm,new[:12]))}{" ..." if len(new)>12 else ""}]; removed [{", ".join(map(nm,lost[:8]))}]'
    if new: return 'OK   '+info
    races={check_tech.UNITS[int(k[2:])]['race'] for k in B if k[0]=='U'}
    full={f'U:{u}' for u,d in check_tech.UNITS.items() if d['race'] in races and d['how']!='auto' and not d['how'].startswith('tech:')}|{f'R:{g}:{L}' for g,d in check_tech.UPGS.items() if d['race'] in races for L in range(1,d['max_level']+1)}|{f'T:{t}' for t,d in check_tech.TECHS.items() if d.get('race') in races}
    if A>=full: return 'OK   (full tech tree already unlocked in the previous mission) '+info
    ok=tech_same_ok(path)
    return (f'OK   (TECH_SAME_OK) {info} [{ok}]' if ok else 'FAIL no new tech: '+info)
def secs(path):
    chk=bytes(mpqapi.MPQ.open(path).extract_file('staredit\\scenario.chk')); S=check_tech.parse_chk(chk)
    # optional sections: editors and other writers may omit them; use the game's defaults instead of crashing
    for k,v in (('MBRF',b''),('TRIG',b''),('WAV ',b'\0'*2048),('MRGN',b''),('STR ',b'\0\0'),('FORC',b'\0'*20)):
        S.setdefault(k,v)
    if 'UNIS' not in S and len(S.get('UNIx',b''))==4168:
        x=S['UNIx']; S['UNIS']=x[:3648]+x[3648:3848]+x[3908:4108]
    return S
def _guard(R,label,fn,default=None):
    """run one sub-check; a crash becomes a FAIL line with its error instead of aborting the whole run"""
    try: return fn()
    except Exception as e:
        R.append(f'FAIL {label} check crashed: {type(e).__name__}: {e}'[:400]); return default
def run(path,R=None):
    S=secs(path); M=mpqapi.MPQ.open(path); R=[] if R is None else R
    def res(ok,msg): R.append(('OK  ' if ok else 'FAIL')+' '+msg)
    STR=S['STR ']
    def st(j):
        if not j: return ''
        o=struct.unpack_from('<H',STR,2*j)[0]; return STR[o:STR.index(b'\0',o)].decode('utf8','replace')
    ownr=S['OWNR']; W,H=struct.unpack('<HH',S['DIM '])
    U=S['UNIT']; units=[]
    for i in range(0,len(U),36):
        _,x,y,uid=struct.unpack_from('<IHHH',U,i); units.append(dict(x=x,y=y,id=uid,owner=U[i+16],res=struct.unpack_from('<I',U,i+20)[0]))
    MR=S['MRGN']
    def loc(l): return struct.unpack_from('<IIII',MR,(l-1)*20) if 0<l<=len(MR)//20 else None
    def locname(l): return st(struct.unpack_from('<H',MR,(l-1)*20+16)[0]) if loc(l) else '?'
    T=S['TRIG']; trigs=[]
    for t in range(0,len(T),2400):
        r=T[t:t+2400]
        c=[r[i*20:i*20+20] for i in range(16) if r[i*20+15]]
        a=[r[320+i*32:352+i*32] for i in range(64) if r[320+i*32+26]]
        trigs.append((c,a,[p for p in range(8) if r[2372+p]]))
    def start(c):  # mission start / opening: only Always or Elapsed Time <= 5
        return all(x[15]==22 or (x[15]==12 and struct.unpack_from('<I',x,8)[0]<=5 and x[14] in (0,1,10)) or (x[15]==11 and x[14]==3) for x in c)
    # 1 start resources
    for p in range(8):
        if ownr[p]!=6: continue
        got={}
        for c,a,pl in trigs:
            if p in pl and start(c):
                for x in a:
                    if x[26]==26 and struct.unpack_from('<I',x,16)[0] in (p,13) and x[27]==7: got[struct.unpack_from('<H',x,24)[0]]=struct.unpack_from('<I',x,20)[0]
        ok=(0 in got or 2 in got) and (1 in got or 2 in got)
        res(ok,f'P{p+1} starting resources set deliberately {got}' if ok else f'P{p+1} (human) has NO Set Resources minerals+gas at mission start -> starts with 0/0')
    # 2 gas buildings
    z=[(u['id'],u['x']//32,u['y']//32,u['owner']+1) for u in units if u['id'] in GASB and u['res']==0]
    res(not z,f'pre-placed gas buildings carry gas {z or ""}')
    # 3 creates at start / opening camera
    bad=[];cam=[]
    for c,a,pl in trigs:
        if not start(c): continue
        for x in a:
            if x[26]==44 and struct.unpack_from('<H',x,24)[0]!=101: bad.append((IDS.get(struct.unpack_from('<H',x,24)[0]),'P%d'%(struct.unpack_from('<I',x,16)[0]+1),locname(struct.unpack_from('<I',x,0)[0])))
            if x[26]==10 and pl and ownr[pl[0]]==6:
                l=struct.unpack_from('<I',x,0)[0]; b=loc(l)
                if b:
                    inside=[u for u in units if b[0]<=u['x']<=b[2] and b[1]<=u['y']<=b[3] and u['id'] not in (176,177,178,188,214) and u['owner']!=11]
                    cam.append((locname(l),len(inside)))
    res(not bad,f'no units/buildings created by trigger at mission start or during the opening {bad[:10] or ""}'+(f' ... {len(bad)} total' if len(bad)>10 else ''))
    res(all(n for _,n in cam),f'opening camera targets show pre-placed units {cam}')
    late=[]
    for c,a,pl in trigs:
        seen=False
        for x in a:
            if x[26]==5: seen=True     # Pause Game
            if seen and x[26]==44 and struct.unpack_from('<H',x,24)[0]==101: late.append(locname(struct.unpack_from('<I',x,0)[0]))
    res(not late,f'revealers are created before Pause Game (fog does not update while paused: the spot looks empty, units seem to appear after the talk) {late or ""}')
    # 4 addons
    loose=[]
    for u in units:
        if u['id'] in ADDONS:
            ax,ay=u['x']//32-1,u['y']//32-1   # addons are 2x2
            par=[v for v in units if v['id']==ADDONS[u['id']] and v['owner']==u['owner'] and (v['x']//32-2,v['y']//32-1)==(ax-4,ay-1)]
            if not par: loose.append((IDS[u['id']],ax,ay))
    res(not loose,f'addons attached {loose or ""}')
    # 5 enemy resources
    comp={p for p in range(8) if ownr[p]==5}
    halls=[u for u in units if u['id'] in HALLS and u['owner'] in comp]
    near=lambda u: any(abs(u['x']-h['x'])<=12*32 and abs(u['y']-h['y'])<=12*32 for h in halls)
    lowm=[(u['x']//32,u['y']//32,u['res']) for u in units if u['id'] in (176,177,178) and near(u) and u['res']<2500]
    lowg=[(u['x']//32,u['y']//32,u['res']) for u in units if (u['id']==188 or (u['id'] in GASB and u['owner'] in comp)) and near(u) and u['res']<10000]
    res(not lowm,f'enemy mineral patches >= 2500 {lowm[:6] or ""}'); res(not lowg,f'enemy geysers >= 10000 {lowg or ""}')
    # 6 unit ids
    used={u['id'] for u in units}|{struct.unpack_from('<H',x,24)[0] for c,a,_ in trigs for x in a if x[26]==44}
    unk=sorted(i for i in used if i not in IDS and i<228)
    res(not unk,f'all unit IDs are real BW units {unk or ""}')
    # 7 tech
    try:
        out=check_tech.check_sections(S,os.path.basename(path)); txt='\n'.join(out) if isinstance(out,list) else str(out)
        n=sum(int(m) for m in re.findall(r'(\d+) finding',txt)); res(n==0,f'tech tree: {n} finding(s)'+('' if n==0 else '\n'+txt))
    except Exception as e: res(False,f'tech check crashed: {e!r}')
    # 8 dialogue gaps
    td=tempfile.mkdtemp(); cache={}; BADWAV=[]
    def lead_tail(sid):
        if sid in cache: return cache[sid]
        f=f'{td}/{sid}.wav'
        try:
            open(f,'wb').write(bytes(M.extract_file(st(sid))))
            d=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f],capture_output=True,text=True).stdout)*1000
        except Exception as ex:   # unreadable/corrupt sound in the MPQ: report as finding, do not crash
            BADWAV.append(f'{st(sid)!r}: {type(ex).__name__} {ex}'[:160]); cache[sid]=(0.0,0.0,0.0); return cache[sid]
        e=subprocess.run(['ffmpeg','-hide_banner','-i',f,'-af','silencedetect=n=-45dB:d=0.03','-f','null','-'],capture_output=True,text=True).stderr
        ss=[float(x)*1000 for x in re.findall(r'silence_start: (-?[\d.]+)',e)]; se=[float(x)*1000 for x in re.findall(r'silence_end: ([\d.]+)',e)]
        lead=se[0] if ss and ss[0]<=10 else 0; tail=d-ss[-1] if ss and (len(se)<len(ss) or se[-1]>=d-10) else 0
        cache[sid]=(d,lead,tail); return cache[sid]
    hyper=any(sum(1 for x in a if x[26]==4 and struct.unpack_from('<I',x,12)[0]==0)>=60 for c,a,_ in trigs)
    PASS=84 if hyper else 1300   # end of a Transmission: with hyper triggers the next pass is <=2 frames away; without, assume the 31-frame pass (1.3 s at Fastest, worst case)
    worst=0; lines=[]
    B=S.get('MBRF',b'')
    for t in range(0,len(B),2400):
        a=[B[t+320+i*32:t+352+i*32] for i in range(64) if B[t+320+i*32+26]]; tm=0; tl=[]
        for x in a:
            ty=x[26]; ms=struct.unpack_from('<I',x,12)[0]
            if ty==1: tm+=ms
            elif ty in (2,8): d,l,tr=lead_tail(struct.unpack_from('<I',x,8)[0]); tl.append((tm,d,l,tr,ty))
            if ty==8: tm+=ms   # briefing Transmission holds the briefing for its duration (like in-game)
        for (t0,d,l,tr,ty),(t1,d1,l1,_,_) in zip(tl,tl[1:]):
            g=(t1+l1)-(t0+d-tr); worst=max(worst,g); lines.append(('briefing',round(g)))
    for c,a,pl in trigs:
        tm=0; tl=[]
        for x in a:
            ty=x[26]
            if ty==4: tm+=struct.unpack_from('<I',x,12)[0]   # a Wait running out pulls the next pass to the next frame
            elif ty==7:
                d,l,tr=lead_tail(struct.unpack_from('<I',x,8)[0]); md=x[27]; n=struct.unpack_from('<I',x,20)[0]; ms=struct.unpack_from('<I',x,12)[0]
                tl.append((tm,d,l,tr)); tm+=(n if md==7 else ms+n if md==8 else ms)+PASS
        for (t0,d,l,tr),(t1,d1,l1,_) in zip(tl,tl[1:]):
            g=(t1+l1)-(t0+d-tr); worst=max(worst,g); lines.append(('trigger',round(g)))
    res(worst<=1000,f'dialogue silence between lines <= 1 s (worst {round(worst)} ms over {len(lines)} line changes; hyper triggers {"on" if hyper else "OFF"})')
    res(not BADWAV,f"all dialogue sound files readable from the MPQ {BADWAV or ''}")
    R.append('     gaps: '+' '.join(f'{k[0]}{v}' for k,v in lines))
    # 9 terrain
    sb=_guard(R,'26 doodad seams',lambda: seams.doodad_seams(S),[]); res(not sb,f'terrain doodads blend in (no hard rectangles) {sb[:8] or ""}'+(f' ... {len(sb)} total' if len(sb)>8 else ''))
    # 10 referenced structures exist
    texts=[st(struct.unpack_from('<I',x,4)[0]) for c,a,_ in trigs for x in a if x[26] in (7,9,12)]
    texts+=[st(struct.unpack_from('<I',B,t+320+i*32+4)[0]) for t in range(0,len(B),2400) for i in range(64) if B[t+320+i*32+26] in (3,4,8)]
    have={u['id'] for u in units}; miss=set()
    for tx in texts:
        for sent in re.split(r'(?<=[.!?\n])\s+',re.sub(r'[\x01-\x1f]',' ',tx)):
            for nm,i in NAMES.items():
                if nm.lower() in sent.lower() and i not in have and not MAKE.search(sent): miss.add((nm,sent.strip()[:70]))
    res(not miss,f'structures named in dialogue/objectives exist on the map {sorted(miss) or ""}')
    # 11: progress displays must go away when the objective is done
    LB={17,18,19,20,21,33,34,35,36,37,39,40}
    lbs=[st(struct.unpack_from('<I',x,4)[0]) for c,a2,_ in trigs for x in a2 if x[26] in LB]
    res(not lbs,f'no leaderboards for objective progress (BW cannot remove one: it stays on screen after the objective is done) {lbs or ""}')
    bad=[i for i,(c,a2,_) in enumerate(trigs) if hyper and any(x[26]==3 for x in a2) and not any(x[26]==4 and struct.unpack_from('<I',x,12)[0]>0 for x in a2)
         and any(x[26] in (26,27,45) and x[27]==8 for x in a2)]
    res(not bad,f'progress counters pace themselves (no per-pass Add in preserved triggers with hyper triggers) {bad or ""}')
    import re as _re
    objs=[_re.sub(r'[\x01-\x1f]','',st(struct.unpack_from('<I',x,4)[0])) for c,a2,_ in trigs for x in a2 if x[26]==12]
    DONE=_re.compile(r'done|complete|lost|failed|destroyed|repaired|erledigt',_re.I)
    keys={l.strip()[:30] for o in objs for l in o.split('\n') if l.strip() and not DONE.search(l) and not l.strip().endswith(':')}
    stuck=[k for k in keys if not any(k not in o or any(l.strip().startswith(k) and DONE.search(l) for l in o.split('\n')) for o in objs)]
    res(not stuck,f'every objective line has a done/removed version in the objective texts {stuck or ""}')
    # 12: every countdown timer that is started must do something real when it reaches 0
    EFFECT={1,2,22,23,24,25,26,27,44,45,48,49,50,51,52,53,54,55,56,58}
    def eff(acts,seen=()):
        if any(x[26] in EFFECT for x in acts): return True
        sws={struct.unpack_from('<I',x,20)[0] for x in acts if x[26]==13 and x[27]==4}-set(seen)
        return any(eff(a2,tuple(seen)+tuple(sws)) for c2,a2,_ in trigs for x in c2 if x[15]==11 and x[14]==2 and x[16] in sws)
    # 13: a camera move during a timer/event must show where the scripted effect acts (same trigger or an event within -2..+10 s)
    FX={22,23,24,25,44,45,46,48,49,50,51,52}
    def etof(c):
        v=[struct.unpack_from('<I',x,8)[0] for x in c if x[15]==12 and x[14] in (0,10)]
        return max(v) if v else None
    def ovl(l1,l2):
        r1,r2=loc(l1),loc(l2)
        if not r1 or not r2: return False
        a1=max(1,(r1[2]-r1[0])*(r1[3]-r1[1])); a2=max(1,(r2[2]-r2[0])*(r2[3]-r2[1]))
        return r1[0]<r2[2] and r2[0]<r1[2] and r1[1]<r2[3] and r2[1]<r1[3] and a2<=4*a1
    blind=[]
    for c,a2,_ in trigs:
        t0=etof(c); timer=any(x[15]==1 for x in c)
        if (t0 is None or t0<60) and not timer: continue
        for x in a2:
            if x[26]!=10: continue
            cl=struct.unpack_from('<I',x,0)[0]
            near=[a3 for c3,a3,_ in trigs if (c3==c) or (t0 is not None and etof(c3) is not None and t0-2<=etof(c3)<=t0+10)]
            # follow switches this trigger sets (sclib moves enemy spawns into staggered triggers gated on a switch)
            sws={struct.unpack_from('<I',y,20)[0] for y in a2 if y[26]==13 and y[27]==4}
            near+=[a3 for c3,a3,_ in trigs if any(z[15]==11 and z[14]==2 and z[16] in sws for z in c3)]
            # a discovery (new objective + ping on the spot) shows pre-placed things, no scripted effect needed
            disc=any(y[26]==28 and ovl(cl,struct.unpack_from('<I',y,0)[0]) for y in a2) and any(y[26]==9 and 'NEW' in st(struct.unpack_from('<I',y,4)[0]) for y in a2)
            if not disc and not any(y[26] in FX and struct.unpack_from('<H',y,24)[0]!=101 and ovl(cl,struct.unpack_from('<I',y,0)[0]) for a3 in near for y in a3):
                blind.append(f"ET{t0} {locname(cl)}")
                if DBG: print("blind",t0,locname(cl),loc(cl),[(y[26],struct.unpack_from("<H",y,24)[0],locname(struct.unpack_from("<I",y,0)[0]),loc(struct.unpack_from("<I",y,0)[0])) for a3 in near for y in a3 if y[26] in FX][:6])
            elif DBG: print("cam",t0,locname(cl),[(y[26],locname(struct.unpack_from("<I",y,0)[0])) for a3 in near for y in a3 if y[26] in FX and struct.unpack_from("<H",y,24)[0]!=101 and ovl(cl,struct.unpack_from("<I",y,0)[0])][:4])
    res(not blind,f'event cameras show a scripted effect at that spot (spawn/kill/damage/order/give nearby) {sorted(set(blind)) or ""}')
    # 14: heroes the player gains mid-mission come via a Rescuable player (rescue colour + standard BW rescue)
    HER={10,16,17,19,20,21,22,23,25,27,28,29,48,49,51,52,53,54,75,76,77,78,79,86,87,88,98,99,100}|set(range(191,200))
    OW=S.get('OWNR',b'\0'*12)
    hum={i for i in range(8) if OW[i]==6}; resc={i for i in range(8) if OW[i]==3}
    direct=[f'{struct.unpack_from("<H",x,24)[0]} P{struct.unpack_from("<I",x,16)[0]+1}->P{struct.unpack_from("<I",x,20)[0]+1}' for c,a2,_ in trigs for x in a2
            if x[26]==48 and struct.unpack_from('<H',x,24)[0] in HER and struct.unpack_from('<I',x,20)[0] in hum]
    res(not direct,f'heroes reach the player through a Rescuable player, not a direct Give Units {direct or ""}')
    # 15: Modify Unit Hit Points is not damage - units already below the value get healed
    heal=[f'{struct.unpack_from("<I",x,20)[0]}% on unit {struct.unpack_from("<H",x,24)[0]} at {locname(struct.unpack_from("<I",x,0)[0])}'
          for c,a2,_ in trigs for i,x in enumerate(a2) if x[26]==49 and struct.unpack_from('<I',x,20)[0]<100
          and not any(y[26]==44 and y[24:26]==x[24:26] and y[16:20]==x[16:20] for y in a2[:i])]
    res(not heal,f'no Set HP used as damage on existing units (it heals units below the value) {sorted(set(heal)) or ""}')
    # 16: effect-only players (no pre-placed units, no AI): their units exist only as a death animation.
    # every create is killed in the SAME trigger, they get no orders, no AI, no alliance/vision changes -> can never fight
    OW2=S.get('OWNR',b'\0'*12); placed={u['owner'] for u in units}
    ai={struct.unpack_from('<I',x,16)[0] for c,a2,_ in trigs for x in a2 if x[26] in (15,16)}
    fxp=[p for p in range(8) if OW2[p]==5 and p not in placed and p not in ai and any(x[26]==44 and struct.unpack_from('<I',x,16)[0]==p for c,a2,_ in trigs for x in a2)]
    prob=[]
    for p in fxp:
        for c,a2,_ in trigs:
            for i,x in enumerate(a2):
                if x[26]==44 and struct.unpack_from('<I',x,16)[0]==p:
                    u=struct.unpack_from('<H',x,24)[0]
                    if u in (33,101): continue   # scanner sweep / map revealer cannot fight
                    rest=a2[i+1:]; w=next((k for k,y in enumerate(rest) if y[26]==4),len(rest))
                    if not any(y[26] in (22,23,25) and struct.unpack_from('<I',y,16)[0]==p and struct.unpack_from('<H',y,24)[0] in (u,229) for y in rest[:w]):
                        prob.append(f'P{p+1} unit {u} not killed in the same trigger (or a Wait in between)')
                    elif not any(y[26]==43 and struct.unpack_from('<I',y,16)[0]==p and y[27]==4 and struct.unpack_from('<H',y,24)[0] in (u,229) for y in rest[:w]) or \
                         not any(y[26]==22 and struct.unpack_from('<I',y,16)[0]==p for y in rest[:w]):
                        prob.append(f'P{p+1} unit {u} not made invincible before a Kill Unit (Kill, not Remove, keeps the death animation)')
                if x[26] in (46,47) and struct.unpack_from('<I',x,16)[0]==p: prob.append(f'P{p+1} gets an order')
                if x[26]==57 and struct.unpack_from('<I',x,16)[0]==p and struct.unpack_from('<H',x,24)[0]!=0: prob.append(f'P{p+1} alliance changed')
            if p in _ and any(x[26] in (57,15,16) for x in a2): prob.append(f'P{p+1} runs alliance/AI actions')
    # 17: effect units: ONE per location per trigger, n=1, and an air unit (can be created anywhere -> no placement errors)
    AIRU={8,11,12,21,42,43,44,45,47,55,56,57,58,59,60,62,63,70,71,72,73,80,84,88,89,98}
    p17=[]
    for p in fxp:
        for ti,(c,a2,_) in enumerate(trigs):
            cr=[x for x in a2 if x[26]==44 and struct.unpack_from('<I',x,16)[0]==p and struct.unpack_from('<H',x,24)[0] not in (33,101)]
            ls=[struct.unpack_from('<I',x,0)[0] for x in cr]
            if len(ls)!=len(set(ls)): p17.append(f'trig{ti}: several effect units at one location')
            if any(x[27]!=1 for x in cr): p17.append(f'trig{ti}: create count >1')
            if any(struct.unpack_from('<H',x,24)[0] not in AIRU for x in cr): p17.append(f'trig{ti}: ground effect unit (placement errors) - use an air unit')
    res(not p17,f'effect units: one per location per trigger, air units (no placement failures) {sorted(set(p17))[:6] or ""}')
    res(not prob,f'effect-only players {[f"P{p+1}" for p in fxp]} never have a live unit: created+killed in one trigger, no orders/AI/alliance {sorted(set(prob)) or ""}')
    # resource backs: mineral fields / geysers must have their back side (away from the town-hall spot) against
    # unwalkable ground (cliff, high-ground edge, water, map edge) or another resource -- never open ground
    # 18: mineral lines are staggered like Blizzard arcs, never a straight flush row
    import numpy as _np
    mins=[(u['x'],u['y']) for u in units if u['id'] in (176,177,178)]
    cl=[]
    for p_ in mins:
        hit=[c for c in cl if any(abs(p_[0]-q[0])<=3*32 and abs(p_[1]-q[1])<=3*32 for q in c)]
        cl=[c for c in cl if c not in hit]+[[p_]+[q for c in hit for q in c]]
    flat=[]
    for c in cl:
        if len(c)<5: continue
        P_=_np.array(c,float); cen=P_.mean(0); _,_,vt=_np.linalg.svd(P_-cen); nrm=vt[1]
        off=_np.round((P_-cen)@nrm/32).astype(int)
        if len(set(off.tolist()))<2: flat.append((int(cen[0]//32),int(cen[1]//32)))
    res(not flat,f'mineral lines staggered (no straight flush rows) {flat or ""}')
    import resback
    rb=resback.check(S,units)
    # documented exemptions: <map>.resback_exempt.json beside the .scx: {"sites":[{"hall":[tx,ty],"reason":"..."}]}
    # only for sites the owner explicitly froze (e.g. "do not touch the restored mains"); every exemption is printed.
    exf=os.path.splitext(path)[0]+'.resback_exempt.json'
    if os.path.exists(exf):
        ex=json.load(open(exf)).get('sites',[])
        for e in ex:
            hit=[q for q in rb if abs(q[3]-e['hall'][0])<=1 and abs(q[4]-e['hall'][1])<=1]
            if hit: R.append(f'EXEMPT resource backs at hall {tuple(e["hall"])}: {len(hit)} field(s) - {e["reason"]}')
            rb=[q for q in rb if q not in hit]
    res(not rb,f'resource backs against cliff/water/unwalkable (not open ground) {sorted({(r[3],r[4]):sum(1 for q in rb if q[3:5]==r[3:5]) for r in rb}.items()) if rb else ""}{" ...%d total"%len(rb) if len(rb)>12 else ""}')
    # 22 rescue scene: units of a rescue-role player (OWNR Rescuable, or a computer player whose units a
    # trigger gives to the human) must not idle within 8 tiles of enemy units. OK only if they really fight: the enemy is set
    # hostile by trigger (Set Alliance Status 57, status 0) - or, for a computer rescue player, sits in another force and is
    # never set allied. Allied by trigger (status 1/2) = always FAIL (enemies standing peacefully next to captives).
    hum={p for p in range(8) if ownr[p]==6}
    fz=S.get('FORC',b'\0'*8)[:8]
    rel={}
    for c,a2,pl in trigs:
        for x in a2:
            if x[26]==57:
                g=struct.unpack_from('<I',x,16)[0]; stt=struct.unpack_from('<H',x,24)[0]
                for q in pl: rel[(q,g)]=stt
    resc={p for p in range(8) if ownr[p]==3}|{struct.unpack_from('<I',x,16)[0] for c,a2,pl in trigs for x in a2
          if x[26]==48 and struct.unpack_from('<I',x,20)[0] in hum and struct.unpack_from('<I',x,16)[0]<8 and ownr[struct.unpack_from('<I',x,16)[0]]==5}
    enem={p for p in range(8) if ownr[p]==5 and p not in resc and not any(fz[p]==fz[h] for h in hum)}
    def fights(e,r):
        st_=rel.get((e,r),rel.get((e,13)))
        if st_ is not None: return st_==0
        return ownr[r]==5 and fz[e]!=fz[r]
    neut={214,176,177,178,188,101}; p22=[]
    for r_ in [u for u in units if u['owner'] in resc and u['id'] not in neut]:
        e_=next((e for e in units if e['owner'] in enem and e['id'] not in neut and abs(e['x']-r_['x'])<=8*32 and abs(e['y']-r_['y'])<=8*32),None)
        if e_ and not fights(e_['owner'],r_['owner']):
            p22.append((f"P{r_['owner']+1} {IDS.get(r_['id'],r_['id'])}",r_['x']//32,r_['y']//32,f"near P{e_['owner']+1} {IDS.get(e_['id'],e_['id'])}","allied by trigger" if rel.get((e_['owner'],r_['owner'])) in (1,2) else "no hostility"))
    res(not p22,f'rescue scene: captives/rescue units not idle beside enemies (set enemy hostile by trigger so they fight) {p22[:6] or ""}'+(f' ...{len(p22)} total' if len(p22)>6 else ''))
    # 23 armed units deal damage: UNIx/UNIS weapon damage by weapon id
    import unit_damage
    _df,_di=_guard(R,'23 unit damage',lambda: unit_damage.check(path),([],[]))
    for _x in _di:
        if not _x.startswith('note'): R.append('OK   customised weapon '+_x)
    res(not _df,f'armed units have >0 damage, UNIS/UNIx consistent {_df or ""}')
    # 21 town-hall <-> resource gap (Blizzard layout): geyser 3..5 empty tiles, nearest minerals 2..4 (hall_gap.py)
    import hall_gap
    _hb,_ho=_guard(R,'21 hall gap',lambda: hall_gap.check(units),([],[]))
    res(not _hb,f'town hall resource gaps (geyser 3..5 tiles, minerals 2..4) {_hb or ""}')
    # 20 base elevation trope: bases not on high ground by default (approve via <map>.highground_ok.json)
    import base_elevation
    _st,_r,_out=_guard(R,'20 base elevation',lambda: base_elevation.check(S,units,path),('OK',0,['OK   base elevation: not checked (crash above)']))
    R.extend(l for l in _out[:-1]); R.append(_out[-1] if _st!='WARN' else 'OK   (WARN) '+_out[-1][5:])
    started=any(x[26]==14 and x[27] in (7,8) for c,a2,_ in trigs for x in a2)
    zero=[a2 for c,a2,_ in trigs if any(x[15]==1 and struct.unpack_from('<I',x,8)[0]==0 and x[14] in (1,10) for x in c)]
    okz=any(eff(a2) for a2 in zero)
    res(not started or okz,f'countdown timer reaching 0 triggers a real effect (kill/damage/HP/give/victory/defeat...) {"" if okz or not started else "no Countdown Timer = 0 trigger with an effect"}')
    # 19 attack announcements: default none; allowed only via ANNOUNCE_OK: <reason> (optionally '<substring> :: <reason>')
    APAT=re.compile(r"marching|attack(s|ing)? (on|the)|incoming|approach(es|ing)|wave|are coming|march on|assault|strike force|send(ing)? .* against",re.I)
    base=os.path.splitext(path)[0]; dd=os.path.dirname(os.path.abspath(path)); aok=[]
    import glob as _g
    for f in [base+'.announce_ok.txt']+_g.glob(os.path.join(dd,'*build_info.json'))+_g.glob(os.path.join(dd,'..','*esign*.md'))+_g.glob(os.path.join(dd,'*esign*.md')):
        if os.path.exists(f):
            for l in open(f,encoding='utf8',errors='replace'):
                mm=re.search(r'ANNOUNCE_OK:\s*([^"\n]+)',l)
                if mm:
                    sub,_,why=mm.group(1).partition('::'); aok.append((sub.strip().lower() if why else '',(why or sub).strip()))
    ann=[];okd=[]
    for ti,(c,a2,_) in enumerate(trigs):
        for x in a2:
            if x[26] in (7,9):
                txt=re.sub(r'[\x01-\x1f]','',st(struct.unpack_from('<I',x,4)[0]))
                if APAT.search(txt):
                    w=[o for o in aok if not o[0] or o[0] in txt.lower()]
                    (okd if w else ann).append(f'trig{ti}: "{txt[:100]}"'+(f' (ANNOUNCE_OK: {w[0][1]})' if w else ''))
    for o in okd: R.append('OK   approved announcement '+o)
    res(not ann,f'no attack announcements (default; ANNOUNCE_OK: <reason> in <map>.announce_ok.txt if deliberate) {ann or ""}')
    # 21 text contrast. Briefing strings use the GLUE palette (tfont.pcx): only 02 periwinkle, 03 lime, 04 yellow-green,
    # 06 white, 07 red are bright; 05 grey and 08,0E-11,15-1C (also 1D-1F) render black/unpredictable (staredit.net wiki
    # "Color"/"String", topics 6880, 17573, 17796). ALLOWLIST: any other colour code before visible text = FAIL.
    BRIEF_OK={0x01,0x02,0x03,0x04,0x06,0x07}
    GAME_DARK={0x05:'grey',0x0e:'blue',0x10:'purple',0x15:'brown',0x18:'dark green',0x1c:'dark cyan'}
    FMT={0x09,0x0a,0x0b,0x0c,0x0d,0x12,0x13,0x14}
    MB=S.get('MBRF',b''); bsids=set()
    for t in range(0,len(MB),2400):
        for i in range(64):
            x=MB[t+320+i*32:t+352+i*32]
            if x[26] in (3,4,8): bsids.add(struct.unpack_from('<I',x,4)[0])
    nstr=struct.unpack_from('<H',STR,0)[0]; bad=[]
    for j in range(1,nstr+1):
        try: t=st(j)
        except Exception: continue
        br=j in bsids
        for mm in re.finditer(r'([\x01-\x1f])([^\x01-\x1f]*)',t):
            c=ord(mm.group(1)); vis=mm.group(2).strip()
            if not vis or c in FMT: continue
            if (br and c not in BRIEF_OK) or (not br and c in GAME_DARK):
                spk=re.match(r'([^:\n]{1,40}):',vis)
                bad.append(f'{"BRIEFING " if br else ""}str{j} \\x{c:02x}'+(f' speaker "{spk.group(1)}"' if spk else '')+f': "{vis[:40]}"')
    res(not bad,f'text contrast (briefing allowlist \\x01-04,06,07; in-game no dark codes; {len(bsids)} briefing strings) {bad[:12] or ""}{" ...%d total"%len(bad) if len(bad)>12 else ""}')
    # 26 hard seams at tile doodads
    sp=_guard(R,'26 doodad peaks',lambda: seams.doodad_peaks(S,15.0),[]); res(not sp,f'tile doodads / rock-cliff blocks blend (no border edge step >15) {sp[:8] or ""}'+(f' ... {len(sp)} total' if len(sp)>8 else ''))
    # 27 rescue hero at start must have a mobile human-player unit within 2 tiles
    _HERO={10,16,17,19,20,21,22,23,25,27,28,29,52,54,61,63,64,65,66,68,74,75,76,77,78,79,80,81,86,87,88,98,99,100,101,102}
    _cust={i for i in range(228) if S.get('UNIx',b'\1'*228)[i]==0}
    rb=[]
    for u in units:
        _sl=[v for v in units if v['id']==214 and v['owner']<8 and ownr[v['owner']]==6]
        _near=any(max(abs(v['x']-u['x']),abs(v['y']-u['y']))<=20*32 for v in _sl)   # start hero = within 20 tiles of a human start location; later rescues are story events
        if u['owner']<8 and ownr[u['owner']]==3 and (u['id'] in _HERO or u['id'] in _cust) and _near:
            if not any(ownr[v['owner']]==6 and v['owner']<8 and v['id']<106 and max(abs(v['x']-u['x']),abs(v['y']-u['y']))<=2*32+16 for v in units):
                rb.append(f"unit {u['id']} P{u['owner']+1} at {u['x']//32},{u['y']//32}")
    res(not rb,f'rescue heroes at start have a player unit within 2 tiles {rb or ""}')
    # 24 core abilities of available units
    import core_tech
    _ct=_guard(R,'24 core abilities',lambda: core_tech.check(S),[])
    res(not _ct,f'core abilities of available units enabled/researchable {_ct or ""}')
    # 25 gas building without town hall
    gok=[]; gf=os.path.splitext(path)[0]+'.gas_ok.json'
    if os.path.exists(gf): gok=json.load(open(gf)).get('sites',[])
    orph=[]
    for g in units:
        if g['id'] not in GASB: continue
        if any(h['id'] in HALLS and h['owner']==g['owner'] and abs(h['x']-g['x'])<=12*32 and abs(h['y']-g['y'])<=12*32 for h in units): continue
        tx,ty=g['x']//32,g['y']//32
        e=next((e for e in gok if abs(e['pos'][0]-tx)<=2 and abs(e['pos'][1]-ty)<=2),None)
        if e: R.append(f"EXEMPT gas building {IDS.get(g['id'])} P{g['owner']+1} at {(tx,ty)} - {e['reason']}")
        else: orph.append((IDS.get(g['id'],g['id']),f"P{g['owner']+1}",tx,ty))
    res(not orph,f'gas buildings have a same-owner town hall within 12 tiles (else <map>.gas_ok.json with reason) {orph or ""}')
    # 28 temporary reveals: every trigger-created Map Revealer (44, unit 101) needs a later removal
    # (22 Kill Unit / 24 Remove Unit anywhere, 23/25 at the same location or Anywhere=64) for that player; Comment with REVEAL_PERMANENT_OK exempts.
    def grp(x,pl): g=struct.unpack_from('<I',x,16)[0]; return set(pl) if g==13 else set(range(8)) if g in (17,) else {g}
    cr=[];rm=[]
    for ti,(c,a2,pl) in enumerate(trigs):
        perm=any(x[26]==47 and 'REVEAL_PERMANENT_OK' in st(struct.unpack_from('<I',x,4)[0]) for x in a2)
        for i,x in enumerate(a2):
            if x[26]==44 and struct.unpack_from('<H',x,24)[0]==101: cr.append((ti,i,grp(x,pl),struct.unpack_from('<I',x,0)[0],perm))
            if x[26] in (22,23,24,25) and struct.unpack_from('<H',x,24)[0] in (101,229): rm.append((ti,i,grp(x,pl),x[26],struct.unpack_from('<I',x,0)[0]))
    left=[];permok=[]
    for ti,i,g,l,perm in cr:
        if perm: permok.append(f'trig{ti} {locname(l)}'); continue
        if not any(g&g2 and (k in (22,24) or l2 in (l,64)) and (t2,i2)!=(ti,i) for t2,i2,g2,k,l2 in rm): left.append(f'trig{ti} P{min(g)+1} {locname(l)}')
    for o in permok: R.append('OK   permanent reveal (REVEAL_PERMANENT_OK) '+o)
    res(not left,f'trigger-created Map Revealers are removed again ({len(cr)} created) {left[:8] or ""}'+(f' ...{len(left)} total' if len(left)>8 else ''))
    # 29 enemy mineral fields: WARN above 4000
    hiM=[(u['x']//32,u['y']//32,u['res']) for u in units if u['id'] in (176,177,178) and any(abs(u['x']-h['x'])<=12*32 and abs(u['y']-h['y'])<=12*32 for h in halls) and u['res']>4000]
    R.append(('WARN' if hiM else 'OK  ')+f' enemy-base mineral fields <= 4000 {(str(len(hiM))+" fields above: "+str(hiM[:6])) if hiM else ""}')
    # 30 side-quest timing: first optional announcement >= 60 s after the intro end
    def tstart(c):  # base time of a trigger from its conditions, None if not timeable
        b=0.0; sws=[]
        for x in c:
            cid=x[15]
            if cid==22: continue
            if cid==12 and x[14] in (0,10): b=max(b,float(struct.unpack_from('<I',x,8)[0])); continue
            if cid==11 and x[14]==2: sws.append(x[16]); continue
            if cid==11 and x[14]==3: continue  # 'switch cleared' guards do not delay
            return None
        return b,sws
    swt={}; tt={}
    for _ in range(6):
        for ti,(c,a,pl) in enumerate(trigs):
            if not pl or ownr[pl[0]]!=6: continue
            r=tstart(c)
            if r is None: continue
            b,sws=r
            if any(w not in swt for w in sws): continue
            b=max([b]+[swt[w] for w in sws]); tt[ti]=b; t=b
            for x in a:
                if x[26]==4: t+=struct.unpack_from('<I',x,12)[0]/1000
                if x[26]==7: t+=struct.unpack_from('<I',x,12)[0]/1000
                if x[26]==13 and x[27]==4:
                    w=struct.unpack_from('<I',x,20)[0]
                    if w not in swt or t<swt[w]: swt[w]=t
    objT=[];openEnd=0.0;ann=[];untimed=[]
    for ti,(c,a,pl) in enumerate(trigs):
        if not pl or ownr[pl[0]]!=6: continue
        ok=any(x[26]==47 and 'SIDEQUEST_TIMING_OK' in st(struct.unpack_from('<I',x,4)[0]) for x in a)
        t=tt.get(ti)
        for x in a:
            if t is not None and x[26] in (4,7): t+=struct.unpack_from('<I',x,12)[0]/1000
            txt=st(struct.unpack_from('<I',x,4)[0]) if x[26] in (7,9,12) else ''
            if x[26]==12 and t is not None: objT.append(t)
            if x[26] in (7,9) and re.search(r'optional',txt,re.I) and not re.search(r'complete|failed',txt,re.I):
                if t is None: untimed.append(f'trig{ti}')
                elif not ok: ann.append((t,ti))
        if ti in tt and start(c): openEnd=max(openEnd,t or 0)
    iend=min(objT) if objT else openEnd
    if ann:
        t,ti=min(ann); d=t-iend
        res(d>=60,f'first optional-objective announcement {d:.0f} s after the intro end (trig{ti} at {t:.0f} s, intro end {iend:.0f} s, min 60 s)'+(f'; untimed reveals {untimed}' if untimed else ''))
    else: R.append(f'OK   side-quest timing: no timed optional announcement'+(f' (proximity/countdown-driven: {untimed})' if untimed else ''))
    # 31 tech progression across the campaign folder
    R.append(tech_progression(path))
    # 32 Characters: Design_Note '## Characters' with Trait/Goal/Weakness/Voice/Tick/Tone/Moments
    import subprocess as _sp
    _o=_sp.run([sys.executable,os.path.join(os.path.dirname(os.path.abspath(__file__)),'check_characters.py'),path],capture_output=True,text=True).stdout
    for _l in _o.splitlines():
        if _l.startswith('FAIL'): R.append('FAIL characters: '+_l[5:])
        elif _l.startswith('WARN'): R.append('WARN characters: '+_l[5:])
    # 33 voice delivery notes: Voice_Script*.md next to the map; every voiced line has VO markup
    # (emotion; stress/pause where a short clause, exclamation or beat needs it) and every speaker a profile
    _o=_sp.run([sys.executable,os.path.join(os.path.dirname(os.path.abspath(__file__)),'check_voice_delivery.py'),path],capture_output=True,text=True).stdout
    _vf=[_l.strip()[5:] for _l in _o.splitlines() if _l.strip().startswith('FAIL')]
    R+=['FAIL voice_delivery: '+_l for _l in _vf] or ['OK   voice delivery notes (%s)'%(_o.strip().splitlines() or ['?'])[-1].split('RESULT')[-1].strip()]
    # 34 the map opens in ScmDraft 2 (named DD2 doodads; real ScmDraft run when the wine harness is installed)
    import check_scmdraft_open
    R+=check_scmdraft_open.run(path)
    # 35 allied players share vision both ways (FORC shared-vision flag / Run AI Script next to Set Alliance Status)
    import check_ally_vision
    try: R+=check_ally_vision.run(path)
    except Exception as e: R.append(f'FAIL ally_shared_vision check crashed: {e!r}')
    return R
def run_safe(path):
    """all checks; never aborts: a crash inside run() is reported as FAIL and checks 36-41 still run"""
    import traceback
    R=[]
    try: run(path,R)
    except Exception as e:
        tb=traceback.extract_tb(e.__traceback__); where=next((f'{os.path.basename(f.filename)}:{f.lineno}' for f in reversed(tb)),'?')
        R.append(f'FAIL predelivery check crashed at {where}: {type(e).__name__}: {e} -- the checks after this point did not run; fix the map or the check'[:500])
    import check_story_delivery
    R+=_guard(R,'36-41 story delivery',lambda: check_story_delivery.run(path),[])
    import check_hero_own_color
    R+=_guard(R,'42 hero own color',lambda: check_hero_own_color.run(path),[])
    return R
if __name__=='__main__':
    rc=0
    for p in sys.argv[1:]:
        print('###',p)
        for l in run_safe(p):
            print(l); rc|=l.startswith('FAIL')
    sys.exit(rc)
