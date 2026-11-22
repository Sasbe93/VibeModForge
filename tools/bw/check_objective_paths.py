#!/usr/bin/env python3
"""objective_paths: every main and side objective is judged by its real paths and its planned duration.
   python3 tools/bw/check_objective_paths.py MAP.scx [...]      (run from the repository root; exit 1 on FAIL)

For every required and optional objective the check traces the walkable path (cv5/vf4 walk grid, neutral
blockers applied): player start to each target, a rescue there and back, an escort route, and scripted
attack waves to the player base (travel time of the created unit, arrival time, approach direction and
choke). Design note:
  TARGET_DURATION: <Normal minutes> :: <Easy/Hard> :: <objective>=<minutes>; ...
  OBJECTIVE_PATHS: <objective> :: <path(s) with length in tiles/travel time> :: <threats / waves and directions> :: <why it is a challenge>
Rules (FAIL), unless 'OBJECTIVE_PATHS_EASY_OK: <reason>' is in the design note (waives the difficulty
rules, not a missing TARGET_DURATION or OBJECTIVE_PATHS line):
  1 the design note has a complete TARGET_DURATION line, and every detected objective has a time budget
    and an OBJECTIVE_PATHS line
  2 path encounters meet the budget: one encounter per 2 minutes of that objective's budget, and at least
    2 on any rescue, reach or escort route (the two-encounter baseline)
  3 a survive/hold objective has scripted waves arriving about every 120 s within its timer, from more
    than one direction (one choke is a FAIL when two or more waves arrive)
  4 the walk+fight estimate (walk time + 60 s per path encounter, plus 3 min for an enemy-hall assault)
    is at least about a third of the objective's budget
  5 the main objective cannot be finished before the first path encounter or scripted wave (a walk to
    victory over empty ground while the first wave is still minutes away is a FAIL)
Escort routes are also covered here (and in more detail by escort_route_challenge, check 46).
WARN: no routes PNG (*routes*.png) next to the map."""
import sys,os,re,glob,math
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','lib'))
import path_tool as P
import mission_duration as D

def line_matches(line, obj):
    head=line[0] if isinstance(line,(tuple,list)) else line
    return D.line_matches(head, obj)

def path_encounters(o):
    typ=o.get('type')
    kinds=('start_to_target','return') if typ=='rescue' else ('start_to_target','escort','return')
    n=0
    for item,enc in zip(o.get('paths') or [], o.get('encounters') or []):
        if item[0] in kinds or typ not in ('rescue','reach','escort'):
            n+=len(enc)
    if typ in ('rescue','reach','escort'):
        n=sum(len(e) for item,e in zip(o.get('paths') or [], o.get('encounters') or []) if item[0] in ('start_to_target','return','escort'))
    return n

def walk_sec(o):
    t=0.0
    for item in o.get('paths') or []:
        kind,src,dst,uid,seg,L=item
        sec=P.travel_sec(L,uid)
        if sec!=math.inf: t+=sec
    return t

def dest_is_base(v,o):
    if o.get('type') not in ('destroy','conquest'): return False
    halls=[(u['x']/32,u['y']/32) for u in v.U if u['o'] in v.enemy and u['id'] in P.HALLS]
    for item in o.get('paths') or []:
        dst=item[2]
        if dst and any(math.hypot(dst[0]-hx,dst[1]-hy)<=8 for hx,hy in halls): return True
    return False

def first_wave(waves):
    ts=[w['arrive'] for w in waves if w.get('arrive') not in (None,math.inf)]
    return min(ts) if ts else math.inf

def run(path):
    v,objs,waves=P.analyze(path, png=None)
    notes,easy=P.parse_notes(path)
    notes_text=''
    from check_ally_vision import note_files
    for f in note_files(path):
        notes_text+='\n'+open(f,encoding='utf8',errors='replace').read()
    duration=D.parse_target_duration(notes_text)
    out=[]; F=[]; info=[]
    if not objs:
        out.append('OK   objective_paths: no campaign objectives detected in this map')
        return out
    if duration is None or duration.get('incomplete'):
        F.append("design note lacks a complete 'TARGET_DURATION: <Normal minutes> :: <Easy/Hard> :: <objective>=<minutes>; ...' line (every objective needs a time budget)")
    for o in objs:
        typ=o['type']; name=o['name']
        paths=o.get('paths') or []
        encs=o.get('encounters') or []
        bits=[]
        for item,enc in zip(paths,encs):
            kind,src,dst,uid,seg,L=item
            bits.append(f'{kind} {P.travel_fmt(L,uid)}, {len(enc)} encounter(s)')
        nenc=path_encounters(o)
        walk=walk_sec(o)
        budget=D.budget_for(duration,o) if duration and not duration.get('incomplete') else None
        need=D.needed_encounters(typ,budget) if budget is not None else (D.RESCUE_MIN_ENCOUNTERS if typ in D.PATH_TYPES else None)
        est=D.walk_encounter_estimate(walk,nenc,dest_is_base(v,o))
        extra=''
        if budget is not None: extra=f', budget {budget:.0f} min, estimate {est:.0f}s, need {need} encounter(s)'
        info.append(f"{typ}{' optional' if o.get('optional') else ''} '{name}': "+('; '.join(bits) or 'no path traced')+extra)
        if not any(line_matches(n,o) for n in notes):
            F.append(f"design note lacks 'OBJECTIVE_PATHS: {name} :: <path(s) with length in tiles/travel time> :: <threats / waves and directions> :: <why it is a challenge>'")
        if duration and not duration.get('incomplete') and budget is None:
            F.append(f"TARGET_DURATION does not give a time budget for '{name}'")
        if typ in D.PATH_TYPES and not easy and nenc<D.RESCUE_MIN_ENCOUNTERS:
            F.append(f"{typ} path for '{name}' has {nenc} threat encounter(s) (need at least {D.RESCUE_MIN_ENCOUNTERS}: ambushes, chokes held by enemies, patrols, base range, triggered attacks along the way)")
        judged=typ not in ('survive','other') or bool(paths)   # survive is judged by its waves; an untraced 'other' line (defeat condition, ability use) has no path to count
        if budget is not None and need is not None and not easy and judged and nenc<need:
            F.append(f"'{name}' has {nenc} threat encounter(s), but its {budget:.0f} min budget asks for {need} (one per {D.BUDGET_MIN_PER_ENCOUNTER:.0f} min, and at least {D.RESCUE_MIN_ENCOUNTERS} on a rescue/reach/escort route)")
        if typ=='survive' and not easy:
            timer=o.get('timer') if o.get('timer') else (budget*60 if budget else None)
            arriving=[w for w in waves if w['arrive']!=math.inf and timer is not None and w['arrive']<=timer]
            need_w=D.needed_waves(timer) if timer else None
            if timer is None:
                F.append(f"survive objective '{name}' has no readable timer (Set Countdown Timer, 'N minutes' in the objectives text, or a TARGET_DURATION budget)")
            elif need_w is not None and len(arriving)<need_w:
                F.append(f"survive objective '{name}' ({timer:.0f}s): {len(arriving)} scripted wave(s) arrive within the timer (need {need_w}, about one every {D.SURVIVE_WAVE_EVERY_SEC:.0f}s); arrivals: "+
                         (', '.join(f"{w['label']} at t={w['arrive']:.0f}s" for w in waves[:6]) or 'none'))
            cl,dirs=P.wave_chokes(arriving or waves)
            if len(arriving)>=2 and len(cl)<=1:
                F.append(f"survive objective '{name}': all scripted waves enter through one choke (directions {dirs}); give the player more than one approach")
        if typ=='escort' and not easy and nenc<D.RESCUE_MIN_ENCOUNTERS:
            pass  # already reported in the PATH_TYPES branch
        if budget is not None and not easy and typ!='survive' and judged:
            floor=budget*60*D.ESTIMATE_MIN_FRACTION
            if est<floor:
                F.append(f"'{name}': walk+fight estimate is {est:.0f}s, below a third of its {budget:.0f} min budget ({floor:.0f}s); lengthen the path, add encounters, or cut the budget")
    # main objective completable before the first wave or path encounter
    mains=[o for o in objs if not o.get('optional')]
    if mains and not easy:
        main=mains[0]
        nenc=path_encounters(main)
        t_walk=walk_sec(main)
        t_wave=first_wave(waves)
        untraced=main.get('type')=='other' and not main.get('paths')   # a capture/ability objective without a traced path cannot be timed
        if nenc==0 and t_walk<t_wave and main.get('type')!='survive' and not untraced:   # a survive objective ends with its timer, never by walking
            when='the first scripted wave arrives at t=%.0fs'%t_wave if t_wave!=math.inf else 'no scripted wave or path encounter is in the way'
            F.append(f"main objective '{main['name']}' can be finished in {t_walk:.0f}s of walking with 0 path encounters, before {when}")
    tag='FAIL' if F else 'OK  '
    out.append(tag+' objective_paths: '+'; '.join(info)+(''.join('\n     - '+f for f in F)))
    if easy and not any('lacks' in f or 'does not give a time budget' in f or 'TARGET_DURATION' in f and 'lacks' in f for f in F):
        # EASY_OK waived difficulty; still report it when only difficulty issues were possible
        if not F: out.append(f'OK   objective_paths: OBJECTIVE_PATHS_EASY_OK ({easy})')
    if not glob.glob(os.path.join(os.path.dirname(os.path.abspath(path)) or '.','*routes*.png')):
        out.append('WARN objective_paths: no routes PNG (*routes*.png) next to the map showing start, targets, paths and threats')
    return out

if __name__=='__main__':
    rc=0
    for p in sys.argv[1:]:
        print('###',p)
        for l in run(p): print(l); rc|=l.startswith('FAIL')
    sys.exit(rc)
