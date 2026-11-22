#!/usr/bin/env python3
"""Shared model for the BW mission-design checks objective_shortcuts, enemy_base_pressure and tech_restriction
(predelivery checks 52-54). Reads the final .scx through path_tool.MapView and adds:
  - the human player's tech: available units, upgrade maxima, available/researched techs (PUNI/PUPx/PTEx, with the
    'use default' flags), and which units the player can actually obtain (pre-placed, or buildable through a real
    production chain from what the player owns)
  - trigger helpers (conditions, actions, switch propagation, morph-chain instances)
Library only; run the checks themselves."""
import sys,os,struct,math,json,re
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0,HERE); sys.path.insert(0,os.path.join(ROOT,'data','bw','tech'))
import path_tool as P
from check_ally_vision import note_files
_J=json.load(open(os.path.join(ROOT,'data','bw','tech','bw_techtree.json')))
UNITS={u['id']:u for u in _J['units']}
UPGS={g['id']:g for g in _J['upgrades']}
TECHS={t['id']:t for t in _J['techs']}
EQUIV={int(k):v for k,v in _J['equivalents'].items()}      # Hatchery is satisfied by Lair/Hive, Spire by Greater Spire
UN={int(k):v for k,v in _J['unit_names'].items()}
UPN={int(k):v for k,v in _J['upgrade_names'].items()}
TNN={int(k):v for k,v in _J['tech_names'].items()}
RACE={0:'Zerg',1:'Terran',2:'Protoss'}
ANY,MEN,BUILDINGS,FACTORIES=229,230,231,232
GROUP_NAMES={ANY:'Any unit',MEN:'Men',BUILDINGS:'Buildings',FACTORIES:'Factories'}
HALLS={106,130,131,132,133,154}
WORKERS={7,41,64}
CHAIN={131:(131,132,133),132:(132,133),133:(133,),143:(143,146,144),146:(146,),144:(144,),141:(141,137),137:(137,)}
ROOT_OF={132:131,133:131,146:143,144:143,137:141}

def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def u16(b,o): return struct.unpack_from('<H',b,o)[0]
def uname(i): return GROUP_NAMES.get(i) or UN.get(i,f'unit {i}')
def is_building(uid): return 106<=uid<=202 or UNITS.get(uid,{}).get('kind')=='building'

def notes_text(path):
    t=''
    for f in note_files(path):
        try: t+='\n'+open(f,encoding='utf8',errors='replace').read()
        except OSError: pass
    return t

# ---------------- tech ----------------
def tech_of(S,p):
    """(available unit ids, {upgrade id: max level}, {tech id: (available, researched)}) for player p."""
    puni=S.get('PUNI') or b''; pupx=S.get('PUPx') or b''; ptex=S.get('PTEx') or b''
    units=set()
    if len(puni)>=5700:
        gu=puni[12*228:13*228]; ud=puni[13*228+p*228:13*228+p*228+228]
        units={u for u in range(228) if (gu[u] if ud[u] else puni[p*228+u])}
    else: units=set(range(228))
    ups={}
    if len(pupx)>=2318:
        for i in range(61):
            usedef=pupx[12*61*2+61*2+p*61+i]; ups[i]=pupx[12*61*2+i] if usedef else pupx[p*61+i]
    else: ups={g:d['max_level'] for g,d in UPGS.items()}
    techs={}
    if len(ptex)>=1672:
        for i in range(44):
            usedef=ptex[12*44*2+44*2+p*44+i]
            av=ptex[12*44*2+i] if usedef else ptex[p*44+i]
            rs=ptex[12*44*2+44+i] if usedef else ptex[12*44+p*44+i]
            techs[i]=(bool(av),bool(rs))
    else: techs={t:(True,False) for t in TECHS}
    return units,ups,techs

def race_of(S,p):
    return RACE.get((S.get('SIDE') or bytes(12))[p])

def satisfied(req,have):
    return req in have or any(e in have for e in EQUIV.get(req,()))

def obtainable(S,p,placed):
    """Units the player can field: pre-placed ones, plus available units reachable through a production chain from
    them (producer owned or obtainable, every requirement obtainable). A player without workers/production gets only
    what is placed."""
    units,ups,techs=tech_of(S,p)
    have=set(placed)
    if have&{131,132,133}: have.add(35)          # larvae come with every hatchery
    changed=True
    while changed:
        changed=False
        for uid,d in UNITS.items():
            if uid in have or uid not in units: continue
            if d['how'] in ('auto',) or str(d['how']).startswith('tech:'): continue
            prod=d.get('produced_by') or []
            if prod and not any(satisfied(x,have) for x in prod): continue
            if not all(satisfied(r,have) for r in d.get('requires') or []): continue
            have.add(uid); changed=True
            if uid in (131,132,133): have.add(35)
    return have

PRODUCERS={106,111,113,114,131,132,133,154,160,155,167,35}
def can_produce(M,p):
    """the player owns (or is given by trigger) a worker, a town hall or a production building"""
    if M.placed[p]&(WORKERS|PRODUCERS): return True
    for c,a,own in M.v.trigs:
        for x in a:
            if x[26]==48 and u32(x,20)==p: return True                                   # Give Units to p
            if x[26] in (44,45) and p in M.v.grp(u32(x,16),own) and u16(x,24) in WORKERS|PRODUCERS: return True
    return False

# ---------------- triggers ----------------
class Model:
    def __init__(s,path):
        s.path=path
        s.v=P.MapView(path)
        s.S=s.v.S
        s.notes=notes_text(path)
        s.hum=sorted(s.v.hum)
        s.placed={p:{u['id'] for u in s.v.U if u['o']==p} for p in range(12)}
    def grp(s,t,own): return s.v.grp(t,own)
    def human_trig(s,own): return bool(set(own)&s.v.hum) or 17 in own
    def switch_setters(s):
        """switch -> list of trigger indices that set it"""
        out={}
        for i,(c,a,own) in enumerate(s.v.trigs):
            for x in a:
                if x[26]==13 and x[27] in (4,6): out.setdefault(u32(x,20),[]).append(i)
        return out
    def instances(s,player_set,uid,loc=None):
        """Pre-placed buildings that can satisfy 'player owns uid' (a Lair condition is satisfied by the Hatchery that
        morphs into it). Returns a frozenset of (x,y) tile positions."""
        root=ROOT_OF.get(uid,uid); fam={root}|set(CHAIN.get(root,(root,)))
        fam={t for t in fam if uid in CHAIN.get(t,(t,))}   # types that are or become uid
        r=s.v.rect(loc) if loc and not s.v.whole(loc) else None
        out=set()
        for u in s.v.U:
            if u['o'] in player_set and u['id'] in fam:
                if r and not (r[0]<=u['x']<r[2] and r[1]<=u['y']<r[3]): continue
                out.add((round(u['x']/32,1),round(u['y']/32,1)))
        return frozenset(out)
