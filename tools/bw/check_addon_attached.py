#!/usr/bin/env python3
"""addon_attached: every pre-placed Terran add-on is really attached to its parent building.

    python3 tools/bw/check_addon_attached.py MAP.scx [...]      (exit 1 on any FAIL)

Standing next to the parent is NOT enough: the game only attaches a pre-placed add-on when the UNIT section links
the two units. Reference: all 328 pre-placed add-ons in 17 third-party campaign maps ('Empire Wars', all 6 add-on types) look
like this; none of them is unlinked:
  - add-on record: relation field (u16 at offset 10) has bit 9 (0x200) set, last u32 (offset 32) = parent's serial
  - parent record: relation field has 0x200 set, last u32 = the add-on's serial (link both ways)
  - parent type fits: ComSat/Nuclear Silo -> Command Center, Machine Shop -> Factory, Control Tower -> Starport,
    Physics Lab/Covert Ops -> Science Facility; same owner
  - position: add-on centre = parent centre + (96,16) px (add-on top-left tile = parent top-left + (4,1))
  - serials (class instance, offset 0) are unique and non-zero
A loose add-on is only allowed for the Neutral player (P12, owner 11): that is how the game leaves an add-on whose
building lifted off. Any other unlinked add-on FAILs. Trigger 'Create Unit' cannot attach add-ons, so they must be
pre-placed with sclib Map.addon().
"""
import sys, struct
ADDON_PARENT = {107: 106, 108: 106, 115: 114, 117: 116, 118: 116, 120: 113}
PARENTS = set(ADDON_PARENT.values())
NAME = {106: 'Command Center', 107: 'ComSat Station', 108: 'Nuclear Silo', 113: 'Factory', 114: 'Starport',
        115: 'Control Tower', 116: 'Science Facility', 117: 'Covert Ops', 118: 'Physics Lab', 120: 'Machine Shop'}
REL_ADDON = 0x200

def parse(U):
    out = []
    for i in range(0, len(U) // 36 * 36, 36):
        ser, x, y, uid, rel = struct.unpack_from('<IHHHH', U, i)
        out.append(dict(ser=ser, x=x, y=y, id=uid, rel=rel, owner=U[i + 16], state=struct.unpack_from('<H', U, i + 26)[0],
                        link=struct.unpack_from('<I', U, i + 32)[0]))
    return out

def check(U):
    """U = raw UNIT section bytes (all UNIT chunks joined). Returns (fails, infos)."""
    units = parse(U); fails = []; info = []
    allser = {}
    for u in units: allser.setdefault(u['ser'], []).append(u)
    linked = {u['ser'] for u in units if u['rel'] or u['link']} | {u['link'] for u in units if u['link']}
    dup = sorted(s for s in linked if len(allser.get(s, [])) > 1 or s == 0)
    if dup: fails.append(f'duplicate or zero serials on linked units {dup[:8]} (links would point at the wrong unit)')
    else:
        d2 = sorted(s for s, l in allser.items() if len(l) > 1)
        if d2: info.append(f'duplicate serials on unlinked units {d2[:8]} (harmless while nothing links to them)')
    for a in units:
        if a['id'] not in ADDON_PARENT: continue
        tag = f"{NAME[a['id']]} P{a['owner']+1} at tile ({a['x']//32-1},{a['y']//32-1})"
        if not (a['rel'] & REL_ADDON) and a['link'] == 0:
            if a['owner'] == 11: info.append(f'{tag}: loose neutral add-on (allowed)'); continue
            fails.append(f'{tag}: not linked to a parent (relation 0x{a["rel"]:x}, link 0) - it will stand detached in the game'); continue
        ps = allser.get(a['link'], [])
        if not (a['rel'] & REL_ADDON): fails.append(f'{tag}: relation field 0x{a["rel"]:x} lacks the add-on bit 0x200')
        if len(ps) != 1: fails.append(f'{tag}: link {a["link"]} points at {len(ps)} units'); continue
        p = ps[0]; want = ADDON_PARENT[a['id']]
        if p['id'] != want: fails.append(f'{tag}: linked to {NAME.get(p["id"], p["id"])}, needs a {NAME[want]}'); continue
        if p['owner'] != a['owner']: fails.append(f'{tag}: parent belongs to P{p["owner"]+1}')
        if (a['x'] - p['x'], a['y'] - p['y']) != (96, 16):
            fails.append(f'{tag}: offset from parent centre {(a["x"]-p["x"], a["y"]-p["y"])} px, must be (96, 16)')
        if not (p['rel'] & REL_ADDON) or p['link'] != a['ser']:
            fails.append(f'{tag}: parent {NAME[p["id"]]} does not link back (relation 0x{p["rel"]:x}, link {p["link"]}, add-on serial {a["ser"]})')
        if p['state'] & 4: fails.append(f'{tag}: parent is pre-placed lifted (in transit) but has an add-on')
        else: info.append(f'{tag}: attached to {NAME[p["id"]]} at tile ({p["x"]//32-2},{p["y"]//32-1})')
    for p in units:
        if p['id'] in PARENTS and (p['rel'] & REL_ADDON or p['link']):
            a = allser.get(p['link'], [])
            if len(a) != 1 or a[0]['id'] not in ADDON_PARENT or a[0]['link'] != p['ser']:
                fails.append(f"{NAME[p['id']]} P{p['owner']+1} at tile ({p['x']//32-2},{p['y']//32-1}): add-on link {p['link']} has no matching add-on")
    return fails, info

def unit_section(path):
    from eudplib.bindings._rust import mpqapi
    d = bytes(mpqapi.MPQ.open(path).extract_file('staredit\\scenario.chk')); i = 0; U = b''
    while i + 8 <= len(d):
        k = d[i:i + 4]; n = struct.unpack_from('<i', d, i + 4)[0]
        if n < 0: break
        if k == b'UNIT': U += d[i + 8:i + 8 + n]      # 'additional UNIT sections add more units'
        i += 8 + n
    return U

if __name__ == '__main__':
    bad = 0
    for path in sys.argv[1:]:
        fails, info = check(unit_section(path))
        for l in info: print('INFO', l)
        for l in fails: print('FAIL addon_attached', l)
        print(('FAIL' if fails else 'OK  '), 'addon_attached', path, f'({sum(1 for l in info if "attached to" in l)} attached)')
        bad |= bool(fails)
    sys.exit(1 if bad else 0)
