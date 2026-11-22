#!/usr/bin/env python3
"""objective_paths: every main and side objective is judged by its real paths on the map.
   python3 tools/bw/check_objective_paths.py MAP.scx [...]      (run from the repository root; exit 1 on FAIL)

For every required and optional objective the check traces the walkable path (cv5/vf4 walk grid, neutral
blockers applied): player start to each target, a rescue there and back, an escort route, and scripted
attack waves to the player base (travel time of the created unit, arrival time, approach direction and
choke). Design note, one line per objective:
  OBJECTIVE_PATHS: <objective> :: <path(s) with length in tiles/travel time> :: <threats / waves and directions> :: <why it is a challenge>
Rules (FAIL), unless 'OBJECTIVE_PATHS_EASY_OK: <reason>' is in the design note (waives the difficulty
rules, not a missing line):
  1 every detected objective has an OBJECTIVE_PATHS line
  2 a rescue or reach path has at least 2 threat encounters (enemy armed units, Bunkers, Sunkens or
    Cannons within 7 tiles of the path; ambush Create-Unit/Order locations within 3 tiles; threats less
    than 10 path tiles apart count as one encounter). A return leg is part of the rescue path.
  3 a survive/hold objective has at least 3 scripted waves that arrive within the timer, and those waves
    do not all enter through one choke
Escort routes are also covered here (and in more detail by escort_route_challenge, check 46).
WARN: no routes PNG (*routes*.png) next to the map."""
import sys,os,re,glob,math
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import path_tool as P

def line_matches(line, obj):
    """A design-note line covers this objective when its first field names it (shared keywords)."""
    head=(line[0] or '').lower()
    name=(obj.get('name') or '').lower()
    typ=obj.get('type') or ''
    if typ and typ in head: return True
    # significant words of length >= 4, minus boilerplate
    stop={'with','from','that','this','them','they','have','will','keep','coming','optional','objectives',
          'destroy','rescue','reach','survive','escort','hold','the','and','for','back'}
    words={w for w in re.findall(r'[a-z0-9]{4,}', name) if w not in stop}
    if words and sum(1 for w in words if w in head)>=max(1, (len(words)+1)//2): return True
    if typ=='escort' and head.startswith('escort'): return True
    return False

def run(path):
    v,objs,waves=P.analyze(path, png=None)
    notes,easy=P.parse_notes(path)
    out=[]; F=[]; info=[]
    if not objs:
        out.append('OK   objective_paths: no campaign objectives detected in this map')
        return out
    for o in objs:
        typ=o['type']; name=o['name']
        paths=o.get('paths') or []
        encs=o.get('encounters') or []
        bits=[]
        total_enc=0
        for item,enc in zip(paths,encs):
            kind,src,dst,uid,seg,L=item
            bits.append(f'{kind} {P.travel_fmt(L,uid)}, {len(enc)} encounter(s)')
            total_enc+=len(enc)
        # For a rescue, both legs together must offer 2+ encounters (a safe walk there AND back is the bug)
        rescue_enc=sum(len(e) for item,e in zip(paths,encs) if item[0] in ('start_to_target','return'))
        reach_enc=sum(len(e) for item,e in zip(paths,encs) if item[0] in ('start_to_target','escort'))
        info.append(f"{typ}{' optional' if o.get('optional') else ''} '{name}': "+('; '.join(bits) or 'no path traced'))
        if not any(line_matches(n,o) for n in notes):
            F.append(f"design note lacks 'OBJECTIVE_PATHS: {name} :: <path(s) with length in tiles/travel time> :: <threats / waves and directions> :: <why it is a challenge>'")
        if typ in ('rescue','reach') and not easy:
            nenc=rescue_enc if typ=='rescue' else reach_enc
            # each rescue/reach path (the journey the player takes) needs 2+ encounters
            if typ=='rescue':
                # there-and-back is one mission path: count encounters on all of its legs
                if nenc<2:
                    F.append(f"rescue path for '{name}' has {nenc} threat encounter(s) (need 2+: ambushes, chokes held by enemies, patrols, base range, triggered attacks along the way or on the way back)")
            else:
                if nenc<2:
                    F.append(f"reach path for '{name}' has {nenc} threat encounter(s) (need 2+ along the way)")
        if typ=='survive' and not easy:
            timer=o.get('timer')
            arriving=[w for w in waves if w['arrive']!=math.inf and timer is not None and w['arrive']<=timer]
            if timer is None:
                F.append(f"survive objective '{name}' has no readable timer (Set Countdown Timer, or 'N minutes' in the objectives text)")
            elif len(arriving)<3:
                F.append(f"survive objective '{name}' ({timer:.0f}s): {len(arriving)} scripted wave(s) arrive within the timer (need 3+); arrivals: "+
                         (', '.join(f"{w['label']} at t={w['arrive']:.0f}s" for w in waves[:6]) or 'none'))
            cl,dirs=P.wave_chokes(arriving or waves)
            if waves and len(cl)<=1:
                F.append(f"survive objective '{name}': all scripted waves enter through one choke (directions {dirs}); give the player more than one approach")
        if typ=='escort' and not easy:
            # same encounter floor as the escort check; length stays in check 46
            if reach_enc<2:
                F.append(f"escort route for '{name}' has {reach_enc} threat encounter(s) (need 2+)")
    tag='FAIL' if F else 'OK  '
    out.append(tag+' objective_paths: '+'; '.join(info)+(''.join('\n     - '+f for f in F)))
    if easy and F==[]:
        out.append(f'OK   objective_paths: OBJECTIVE_PATHS_EASY_OK ({easy})')
    if not glob.glob(os.path.join(os.path.dirname(os.path.abspath(path)) or '.','*routes*.png')):
        out.append('WARN objective_paths: no routes PNG (*routes*.png) next to the map showing start, targets, paths and threats')
    return out

if __name__=='__main__':
    rc=0
    for p in sys.argv[1:]:
        print('###',p)
        for l in run(p): print(l); rc|=l.startswith('FAIL')
    sys.exit(rc)
