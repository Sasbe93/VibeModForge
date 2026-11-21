#!/usr/bin/env python3
"""mission_type_variety: neighbouring missions of a campaign play differently. Two chapters in a row that are both
"destroy 3 specific structures within a time limit" feel like the same mission.
   python3 tools/bw/check_mission_type_variety.py MAP.scx [--prev PREV1(.scx|.md) PREV2 ...]   (exit 1 on FAIL)
   python3 tools/bw/check_mission_type_variety.py --outline DESIGN_NOTE.md                    (campaign-outline lint)
Without --prev the previous missions M<n-1>/M<n-2> next to the map are used (same search as check_start_setup).

Design note line: 'MISSION_TYPE: <objective type> :: <pressure> :: <target count>'
  objective types: destroy-targets, conquest, escort, hold, rescue, hero, reach, capture (other words are kept as written)
  pressure: time-limit, waves, hold-timer, none;  target count: a number (0 when it does not apply)
Rules:
  1 the line is present (FAIL)
  2 it matches the map (FAIL): objective type and pressure inferred from the triggers. Initial Set Mission Objectives
    text ('Destroy the 3 ...', 'Survive ...', 'Escort/keep ... alive until ...'), Set Countdown Timer with a Defeat or
    Victory at countdown 0 (time-limit / hold-timer), an escort order to a Bring objective (escort)
  3 FAIL when the mission has the same objective type and pressure as one of the previous 2 missions, or the same type
    and target count; exemption 'MISSION_TYPE_REPEAT_OK: <reason>' in the design note
Previous missions use their own MISSION_TYPE line when they have one, otherwise what their triggers show.
Outline lint (--outline, also run on the map's design note): in the campaign-outline table (a column named Goal,
Objective or Pattern), neighbouring chapters with the same type and pressure, or the same type and count = WARN."""
import sys,os,re,struct,glob
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from check_ally_vision import sections,note_files
NUM={'a':1,'an':1,'one':1,'single':1,'two':2,'both':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10}
TYPES=('destroy-targets','conquest','escort','hold','rescue','hero','reach','capture')
PRESS=('time-limit','waves','hold-timer','none')
def clean(t): return re.sub(r'[\x00-\x1f]',' ',t or '').replace('*','').strip()
def classify(text):
    """(type, pressure, count) from free objective text; None for parts it cannot tell"""
    t=clean(text).lower(); ty=None
    if re.search(r'\bhero (interlude|mission|squad)|\bhero-only|\bno base\b.*\blead\b',t): ty='hero'
    elif re.search(r'\bescort|\bkeep .{0,40}alive until|\bmust survive until .{0,40}(left|leave|reach|out)|\bbring .{0,40} to\b|\blead .{0,40} to\b',t): ty='escort'
    elif re.search(r'\b(survive|hold|protect|defend)\b.{0,60}(\bfor\b \d|\buntil\b|\bminutes\b)',t): ty='hold'
    elif re.search(r'\brescue|\bfree the\b|\bfind\b',t): ty='rescue'
    elif re.search(r'\b(destroy|kill|eliminate) (all|every)\b|\bwipe out|\bclear the\b|\bconquer',t): ty='conquest'
    elif re.search(r'\b(destroy|kill|break|bring down|take down)\b',t): ty='destroy-targets'
    elif re.search(r'\bcapture|\binfest\b|\bseize',t): ty='capture'
    elif re.search(r'\breach\b|\bget .{0,30} to\b',t): ty='reach'
    pr=None
    if ty=='hold' and re.search(r'\bfor \d+|\d+ minutes|\buntil\b',t): pr='hold-timer'
    elif re.search(r'\bbefore\b|\bwithin\b|\bcountdown|\btime limit|\bin time\b',t): pr='time-limit'
    elif re.search(r'\bwaves?\b',t): pr='waves'
    cnt=None
    m=re.search(r'\b(?:destroy|kill|break|hold|protect|defend|rescue|capture|infest|take down|bring down)\b(?: the| all)? (\d+|'+'|'.join(NUM)+r')\b',t)
    if m: cnt=int(m.group(1)) if m.group(1).isdigit() else NUM[m.group(1)]
    elif ty=='destroy-targets' and re.search(r'\b(destroy|kill|break)\b the [a-z]',t): cnt=1
    return ty,pr,cnt
def canon(ty,pr,cnt):
    ty=ty.strip().lower(); pr=pr.strip().lower()
    if ty not in TYPES: ty=classify(ty)[0] or ty
    if pr not in PRESS:
        p=classify('x '+pr)[1]; pr=p or ('none' if re.search(r'\bno(ne)?\b',pr) else pr)
    m=re.search(r'\d+',str(cnt)); return ty,pr,int(m.group()) if m else 0
def note_line(paths):
    decl=rep=None
    for f in paths:
        for l in open(f,encoding='utf8',errors='replace'):
            m=re.search(r'MISSION_TYPE:\s*(.+?)\s*::\s*(.+?)\s*::\s*(\S+)',l)
            if m and not decl: decl=canon(*m.groups())
            m=re.search(r'MISSION_TYPE_REPEAT_OK:\s*(\S.*)',l)
            if m: rep=m.group(1).strip()
    return decl,rep
def infer(path):
    """(type, pressure, count, evidence) from the map's triggers"""
    S=sections(bytes(__import__('eudplib.bindings._rust',fromlist=['mpqapi']).mpqapi.MPQ.open(path).extract_file('staredit\\scenario.chk')))
    ownr=S['OWNR']; hum={p for p in range(8) if ownr[p]==6}
    st=S.get('STR ',b'\0\0'); n=struct.unpack_from('<H',st,0)[0]
    def s(j):
        if not 0<j<=n: return ''
        o=struct.unpack_from('<H',st,2*j)[0]; return st[o:st.index(b'\0',o)].decode('utf8','replace')
    T=S.get('TRIG',b''); objs=[]; cd=False; cd_def=cd_win=False
    for t in range(0,len(T)-len(T)%2400,2400):
        r=T[t:t+2400]
        if not any(r[2372+p] for p in hum) and not r[2372+17]: continue
        c=[r[i*20:i*20+20] for i in range(16) if r[i*20+15]]
        a=[r[320+i*32:352+i*32] for i in range(64) if r[320+i*32+26]]
        for x in a:
            if x[26]==12: objs.append(s(struct.unpack_from('<I',x,4)[0]))
            if x[26]==14 and struct.unpack_from('<I',x,12)[0]>0: cd=True
        if any(x[15]==1 and struct.unpack_from('<I',x,8)[0]==0 for x in c):
            if any(x[26]==2 for x in a): cd_def=True
            if any(x[26]==1 for x in a): cd_win=True
    first=clean(objs[0]) if objs else ''
    ty,pr,cnt=classify(first); ev=[f"objectives: {first[:80]!r}"] if first else []
    if cd and cd_win and not cd_def and ty in (None,'hold'): ty,pr='hold','hold-timer'; ev.append('countdown 0 = victory')
    elif cd and cd_def: pr='time-limit'; ev.append('countdown 0 = defeat')
    elif pr=='time-limit' and not cd: ev.append('text says time limit but no countdown')
    try:
        import check_escort_route as E
        if ty is None and E.run(path)[0].find('route ')>=0: ty='escort'; ev.append('escort order to a Bring objective')
    except Exception: pass
    return ty,pr or 'none',cnt if cnt is not None else 0,ev
def mission_of(p):
    """declared line (design note next to the map / the .md itself) else inferred from the map"""
    if p.endswith('.md'):
        d,_=note_line([p])
        if d: return d,'design note'
        maps=sorted(glob.glob(os.path.join(os.path.dirname(p),'*.scx')))
        if not maps: return None,'no MISSION_TYPE line and no map'
        p=maps[0]
    d,_=note_line(note_files(p))
    if d: return d,'design note'
    ty,pr,cnt,ev=infer(p); return (ty or 'other',pr,cnt),'triggers ('+'; '.join(ev)+')'
def outline(paths):
    """WARN lines for neighbouring chapters with the same pattern in the campaign-outline table"""
    W=[]
    for f in paths:
        rows=[l for l in open(f,encoding='utf8',errors='replace') if l.startswith('|')]
        if len(rows)<3: continue
        hdr=[h.strip().lower() for h in rows[0].strip().strip('|').split('|')]
        col=next((i for i,h in enumerate(hdr) if h in ('pattern','goal','objective','objectives','mission type')),None)
        if col is None: continue
        prev=None
        for r in rows[2:]:
            c=[x.strip() for x in r.strip().strip('|').split('|')]
            if len(c)<=col: continue
            k=classify(c[col]); ch=clean(c[0])
            if prev and k[0] and k[0]==prev[1][0] and ((k[1] and k[1]==prev[1][1]) or (k[2] and k[2]==prev[1][2])):
                W.append(f"chapters {prev[0]} and {ch}: same pattern ({k[0]}, {k[1] or '-'}, {k[2] or '-'}) - {c[col][:60]!r}")
            prev=(ch,k)
        if W: break
    return W
def run(path,prev=None):
    import check_start_setup as CS
    prev=CS.previous_missions(path) if prev is None else prev
    nf=note_files(path); decl,rep=note_line(nf); F=[]; out=[]
    ty,pr,cnt,ev=infer(path); inf=(ty,pr,cnt)
    if not decl: F.append(f"design note lacks 'MISSION_TYPE: <objective type> :: <pressure> :: <target count>' (the map looks like: {ty or 'other'} :: {pr} :: {cnt})")
    else:
        if ty and decl[0]!=ty: F.append(f'MISSION_TYPE says {decl[0]} but the triggers look like {ty} ({"; ".join(ev)})')
        if (pr=='time-limit')!=(decl[1]=='time-limit') and (pr!='none' or decl[1]=='time-limit'): F.append(f"MISSION_TYPE pressure '{decl[1]}' but the triggers show '{pr}' ({'; '.join(ev)})")
    me=decl or (ty or 'other',pr,cnt); seen=[]
    for p in prev:
        o,src=mission_of(p)
        if not o: continue
        seen.append(f'{os.path.basename(p)}: {o[0]}/{o[1]}/{o[2]} ({src[:70]})')
        same=[]
        if o[0]==me[0] and o[1]==me[1]: same.append('type + pressure')
        if o[0]==me[0] and o[2] and o[2]==me[2]: same.append('type + target count')
        if same and not rep: F.append(f"same {' and '.join(same)} as {os.path.basename(p)} ({me[0]}, {me[1]}, {me[2]}): neighbouring missions must differ (or 'MISSION_TYPE_REPEAT_OK: <reason>')")
    out.append(('FAIL' if F else 'OK  ')+f" mission_type_variety: {me[0]}/{me[1]}/{me[2]}"+(f"; previous: {'; '.join(seen)}" if seen else '; no previous mission found')+(f'; repeat ok: {rep}' if rep and seen else '')+''.join('\n     - '+f for f in F))
    W=outline(nf)
    if W: out.append('WARN campaign_outline_variety:'+''.join('\n     - '+w for w in W[:8]))
    return out
if __name__=='__main__':
    a=sys.argv[1:]; rc=0
    if a and a[0]=='--outline':
        for f in a[1:]:
            W=outline([f]); print('###',f); print(('WARN campaign_outline_variety:'+''.join('\n     - '+w for w in W)) if W else 'OK   campaign_outline_variety')
        sys.exit(0)
    mp=a[0]; prev=a[a.index('--prev')+1:] if '--prev' in a else None
    print('###',mp)
    for l in run(mp,prev): print(l); rc|=l.startswith('FAIL')
    sys.exit(rc)
