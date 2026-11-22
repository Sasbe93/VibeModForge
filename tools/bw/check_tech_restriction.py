#!/usr/bin/env python3
"""tech_restriction: an early or mid campaign mission restricts the player's tech tree; full tech must be declared.
   python3 tools/bw/check_tech_restriction.py MAP.scx [...]      (run from the repository root; exit 1 on FAIL)

Sasbe t1025: an early-looking mission offered the whole Terran tree (Battlecruiser, Ghost, Nuclear Silo, every
upgrade). Blizzard's campaigns hand out tech chapter by chapter. Brood War has no trigger action for tech: the
restriction lives in the map's Unit / Upgrade / Tech settings (PUNI, PUPx/UPGx, PTEx/TECx; sclib Map.tech).
Design note:
  TECH_LEVEL: <early|mid|late|full> :: <chapter, e.g. M2 of 8, or stand-alone> :: <what the player gets and why>
Measured per human player (available units/buildings of the player's race, upgrade maxima, techs):
  top tier   Terran: Science Facility, Covert Ops, Physics Lab, Nuclear Silo, Ghost, Science Vessel, Battlecruiser,
             Valkyrie, Nuke; Zerg: Hive, Defiler Mound, Ultralisk Cavern, Greater Spire, Nydus Canal, Defiler,
             Ultralisk, Guardian, Devourer; Protoss: Templar Archives, Arbiter Tribunal, Fleet Beacon, High/Dark
             Templar, Archon, Dark Archon, Arbiter, Carrier
  middle     Terran: Factory, Starport, Armory, Machine Shop, Control Tower, Vulture, Siege Tank, Goliath, Wraith,
             Dropship; Zerg: Lair, Spire, Queen's Nest, Mutalisk, Scourge, Queen, Lurker; Protoss: Citadel of Adun,
             Robotics Facility, Stargate, Observatory, Robotics Support Bay, Shuttle, Reaver, Observer, Scout, Corsair
FAIL:
  1 no TECH_LEVEL line (unless the player can produce nothing: no worker, hall or production building, none given)
  2 nothing is restricted (every unit, building, upgrade level and tech of the race available) and the level is not
    'full' (a missing line counts as not full)
  3 early: a top-tier unit or building is available, or more than half of the middle tier
  4 mid: the whole top tier is available (nothing held back)
  5 full: the third field (the reason) is empty
WARN: early with weapon/armor upgrades above level 1; mission M1/M2 (file name) declared late or full."""
import sys,os,re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import mission_model as MM
import json
_T=json.load(open(os.path.join(MM.ROOT,'data','bw','tech','bw_tech_tiers.json')))
TOP={r:set(v) for r,v in _T['top'].items()}; MID={r:set(v) for r,v in _T['middle'].items()}
WEAPON_ARMOR={r:tuple(v) for r,v in _T['weapon_armor'].items()}

def parse_level(text):
    m=re.search(r'TECH_LEVEL:\s*(early|mid|middle|late|full)\b\s*(?:::\s*([^:\n]*?)\s*(?:::\s*(.*))?)?$',text,re.I|re.M)
    if not m: return None
    lv=m.group(1).lower(); lv='mid' if lv=='middle' else lv
    return dict(level=lv,chapter=(m.group(2) or '').strip(),why=(m.group(3) or '').strip(),raw=m.group(0).strip())

def measure(S,p):
    race=MM.race_of(S,p)
    units,ups,techs=MM.tech_of(S,p)
    roster={u for u,d in MM.UNITS.items() if d['race']==race and d['how']!='auto' and not str(d['how']).startswith('tech:')}
    upg={g:d['max_level'] for g,d in MM.UPGS.items() if d['race']==race}
    tch={t for t,d in MM.TECHS.items() if d.get('race')==race}
    av_u=roster&units
    av_up=sum(min(ups.get(g,0),mx) for g,mx in upg.items()); all_up=sum(upg.values())
    av_t={t for t in tch if techs.get(t,(False,False))[0] or techs.get(t,(False,False))[1]}
    return dict(race=race,roster=roster,units=av_u,up=(av_up,all_up),ups=ups,techs=(len(av_t),len(tch)),
                full=(av_u==roster and av_up==all_up and len(av_t)==len(tch)))

def mission_no(path):
    m=re.match(r'M[A-Z]?(\d+)[_.]',os.path.basename(path)); return int(m.group(1)) if m else None

def run(path,M=None):
    M=M or MM.Model(path)
    lv=parse_level(M.notes)
    out=[]
    for p in M.hum:
        ms=measure(M.S,p); race=ms['race']
        if race not in TOP: continue
        top_av=sorted(TOP[race]&ms['units']); mid_av=sorted(MID[race]&ms['units'])
        info=(f"P{p+1} {race}: {len(ms['units'])}/{len(ms['roster'])} units+buildings, upgrade levels {ms['up'][0]}/{ms['up'][1]}, "
              f"techs {ms['techs'][0]}/{ms['techs'][1]}; top tier available {len(top_av)}/{len(TOP[race])}"
              +(f" ({', '.join(MM.uname(u).replace(race+' ','') for u in top_av[:6])}{' ...' if len(top_av)>6 else ''})" if top_av else '')
              +f"; middle tier {len(mid_av)}/{len(MID[race])}")
        F=[]; W=[]
        produce=MM.can_produce(M,p)
        if not produce:
            out.append(f"OK   tech_restriction: {info}; the player owns no worker, hall or production building and gets none, so tech settings do not matter"+(f" [{lv['raw']}]" if lv else ''))
            continue
        if lv is None:
            F.append("design note lacks 'TECH_LEVEL: <early|mid|late|full> :: <chapter, e.g. M2 of 8, or stand-alone> :: <what the player gets and why>'")
        level=lv['level'] if lv else None
        if ms['full'] and level!='full':
            F.append("nothing is restricted: every unit, building, upgrade level and tech of the race is available. Hand out tech chapter by chapter (Unit/Upgrade/Tech settings, sclib Map.tech) or declare 'TECH_LEVEL: full :: ... :: <reason>'")
        if level=='early':
            if top_av: F.append(f"TECH_LEVEL early, but top-tier tech is available: {', '.join(MM.uname(u) for u in top_av)}")
            if len(mid_av)*2>len(MID[race]): F.append(f"TECH_LEVEL early, but {len(mid_av)}/{len(MID[race])} middle-tier units/buildings are available ({', '.join(MM.uname(u) for u in mid_av)})")
            hi=[MM.UPN[g] for g in WEAPON_ARMOR[race] if ms['ups'].get(g,0)>1]
            if hi: W.append(f"TECH_LEVEL early with weapon/armor upgrades above level 1: {', '.join(hi)}")
        if level=='mid' and len(top_av)==len(TOP[race]):
            F.append(f"TECH_LEVEL mid, but the whole top tier is available ({', '.join(MM.uname(u) for u in top_av)}); hold some of it back")
        if level=='full' and not lv['why']:
            F.append("TECH_LEVEL full needs a reason in its third field (why this mission gives the whole tree)")
        n=mission_no(path)
        if level in ('late','full') and n is not None and n<=2: W.append(f"mission M{n} declares TECH_LEVEL {level}; early chapters normally restrict tech")
        out.append(('FAIL' if F else 'OK  ')+f" tech_restriction: {info}"+(f" [{lv['raw'][:160]}]" if lv else '')+''.join('\n     - '+f for f in F))
        if W: out.append('WARN tech_restriction:'+''.join('\n     - '+w for w in W))
    return out or ['OK   tech_restriction: no human player with a BW race']

if __name__=='__main__':
    rc=0
    for p in sys.argv[1:]:
        print('###',p)
        for l in run(p): print(l); rc|=l.startswith('FAIL')
    sys.exit(rc)
