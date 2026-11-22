#!/usr/bin/env python3
"""check_story_delivery: briefing, voiced dialogue, text residues and campaign map shape for a StarCraft: Brood War mission.

Usage: python3 tools/bw/check_story_delivery.py MAP.scx   (run from the repository root; exit 1 on any FAIL)
Called by predelivery_check.py (checks 36-40). Every sub-check that crashes is reported as FAIL with its error.

36 briefing_present   a campaign mission has a briefing (MBRF) with text or objectives.
                      Exemption: 'NO_BRIEFING_OK: <reason>' in the Design_Note.
37 voiced_dialogue    a campaign mission has voiced lines (in-mission Transmission with a WAV, briefing Play WAV);
                      every Transmission carries a WAV that exists in the MPQ; briefing lines are voiced; no character
                      line ("Name: text") is shown as plain Display Text. Exemption: 'NO_VOICE_OK: <reason>' in the Design_Note.
38 text_residue       no string contains an escaped colour code that the game would print literally
                      (u0003, \\u0003, \\x03, <03>), e.g. from JSON or Python escaping in a generator.
39 map_design         check_map_design_bw.py runs for campaign maps too (FAIL lines are copied).
40 cliff_shape        organic cliff outlines (bw_cliff_outlines: no long straight cliff runs, enough corners).
41 reward_reason      every objective reward has an in-world source the player sees. A trigger that is not a start trigger
                      and adds minerals/gas to a human player (Set Resources, Add), or gives units to / creates units for a
                      human player after an event (any condition other than Always / Elapsed Time), needs a Design_Note line
                      REWARD_WHY: <objective> :: <reward> :: <in-world source the player sees>
                      matching that reward (the amount for resources, a unit name word or a generic group word for units).
                      Sources that only say 'reward', 'bonus' etc. are rejected. Non-quest income (a timed supply drop
                      that the story explains) is exempt with a Comment action 'INCOME_OK: <reason>' in that trigger.
A map counts as a campaign mission if it has Set Mission Objectives, a Transmission, a Victory action or a
Design_Note with '## Characters'. Melee/ranked maps only get checks 38-40.
"""
import sys, os, re, glob, struct, subprocess, traceback
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'tools', 'lib', 'bw'))

def _mpq_file(path, name):
    """one file from the map; the MPQ handle is released before returning (an open handle locks the map on
    Windows, and the map design check below opens it again in a subprocess)"""
    from eudplib.bindings._rust import mpqapi
    return bytes(mpqapi.MPQ.open(path).extract_file(name))

def _sections(path):
    d = _mpq_file(path, 'staredit\\scenario.chk'); S = {}; i = 0
    while i + 8 <= len(d):
        k = d[i:i+4].decode('latin1'); n = struct.unpack_from('<i', d, i+4)[0]
        if n < 0: break
        S[k] = S.get(k, b'') + d[i+8:i+8+n] if k in ('MTXM',) else d[i+8:i+8+n]; i += 8 + n
    return S

def _strings(S):
    st = S.get('STR ', b'')
    if len(st) < 2: return {}
    n = struct.unpack_from('<H', st)[0]; out = {}
    for j in range(1, n+1):
        o = struct.unpack_from('<H', st, 2*j)[0]
        if not o or o >= len(st): continue
        e = st.find(b'\0', o); out[j] = st[o:e if e >= 0 else len(st)].decode('utf-8', 'replace')
    return out

def _trigs(blob):
    out = []
    for t in range(0, len(blob) - len(blob) % 2400, 2400):
        r = blob[t:t+2400]
        c = [r[i*20:i*20+20] for i in range(16) if r[i*20+15]]
        a = [r[320+i*32:352+i*32] for i in range(64) if r[320+i*32+26]]
        out.append((c, a, [p for p in range(8) if r[2372+p]]))
    return out

def design_note(path):
    d = os.path.dirname(os.path.abspath(path)); base = os.path.splitext(os.path.basename(path))[0]
    fs = sorted(set(glob.glob(os.path.join(d, 'Design_Note*.md')) + glob.glob(os.path.join(d, base + '*design*.md'))))
    return '\n'.join(open(f, encoding='utf-8', errors='replace').read() for f in fs if 'SECRET' not in f)

def exemption(note, key):
    m = re.search(key + r'\s*:\s*(.{3,})', note)
    return m.group(1).strip() if m else None

RESIDUE = re.compile(r'(\\?u00[01][0-9a-fA-F])|(\\x[01][0-9a-fA-F])|(<[01][0-9A-Fa-f]>)')
CTRL = re.compile(r'[\x01-\x1f]')
STATUS = {'objectives', 'optional', 'hint', 'tip', 'note', 'mission', 'bonus', 'reward', 'status', 'warning', 'time',
          'objective', 'secondary', 'primary', 'new objective', 'objectives updated'}
STATUS_WORDS = {'objective', 'objectives', 'optional', 'hint', 'bonus', 'mission', 'reward', 'destroyed', 'remaining', 'left', 'killed', 'rescued', 'found', 'decision', 'reminder', 'choice', 'score', 'progress'}
SMALL = {'of', 'the', 'van', 'von', 'de', 'la', 'al', 'el', 'and'}

def speaker_line(t):
    """'Name: words' with a capitalised name of 1-4 words -> name, else None."""
    t = RESIDUE.sub('', t); t = CTRL.sub('', t).strip()
    m = re.match(r"^([A-Z][\w.'\-]*(?: [\w.'\-]+){0,3}):\s+(\S.*)$", t, re.S)
    if not m: return None
    name, rest = m.group(1), m.group(2)
    if name.lower() in STATUS or any(w.lower() in STATUS_WORDS for w in name.split()): return None
    if name.isupper() and len(name) > 4: return None       # 'NEW OBJECTIVE:', 'WARNING:' style status labels
    if not all(w[:1].isupper() or w.lower() in SMALL for w in name.split()): return None
    if len(rest.split()) < 3: return None
    return name

TRIVIAL_SOURCE = {'reward', 'bonus', 'objective', 'quest', 'prize', 'completion', 'none', 'n/a', 'na', 'tbd', 'because',
                  'for completing', 'objective reward', 'quest reward', 'mission reward', 'bonus reward', 'gift', 'payment'}
GROUP_WORDS = {'unit', 'units', 'squad', 'team', 'troops', 'forces', 'men', 'crew', 'buildings', 'base', 'camp', 'outpost',
               'join', 'joins', 'everything', 'garrison', 'survivors', 'convoy'}

def reward_lines(note):
    """[(objective, reward, source, valid, why_invalid)] from REWARD_WHY lines."""
    out = []
    for raw in re.findall(r'REWARD_WHY\s*:\s*(.+)', note):
        parts = [p.strip().strip('`*').strip() for p in raw.split('::')]
        if len(parts) != 3 or not all(parts):
            out.append((raw, '', '', False, 'needs three parts: <objective> :: <reward> :: <in-world source>')); continue
        src = re.sub(r'[^a-z/ ]', '', parts[2].lower()).strip()
        words = [w for w in src.split() if w not in ('the', 'a', 'an', 'of', 'for', 'as')]
        if src in TRIVIAL_SOURCE or len(words) < 2 or all(w in TRIVIAL_SOURCE for w in words):
            out.append((*parts, False, f"source '{parts[2]}' is not an in-world source the player sees")); continue
        out.append((*parts, True, ''))
    return out

def _unit_words(uid):
    try:
        import json
        n = json.load(open(os.path.join(ROOT, 'data', 'bw', 'bw_unit_ids.json'))).get(str(uid), '')
    except Exception:
        n = ''
    return {w.lower() for w in re.split(r'[_\s]+', n) if len(w) >= 4 and w.lower() not in ('terran', 'zerg', 'protoss')}

def run(path):
    R = []
    def res(ok, msg): R.append(('OK  ' if ok else 'FAIL') + ' ' + msg)
    def guard(label, fn):
        try: fn()
        except Exception as e:
            R.append(f'FAIL {label} check crashed: {type(e).__name__}: {e}'.rstrip()[:400])
    try:
        S = _sections(path)
    except Exception as e:
        return [f'FAIL story/briefing checks: cannot read the map: {type(e).__name__}: {e}']
    STR = _strings(S); TR = _trigs(S.get('TRIG', b'')); BR = _trigs(S.get('MBRF', b''))
    note = design_note(path)
    acts = [x for _, a, _ in TR for x in a]; bacts = [x for _, a, _ in BR for x in a]
    campaign = any(x[26] in (12, 7, 1) for x in acts) or bool(re.search(r'^##\s*Characters', note, re.M))
    wav_ok = {}
    def wav_exists(sid):
        if sid in wav_ok: return wav_ok[sid]
        name = STR.get(sid, '')
        try: ok = bool(name) and _mpq_file(path, name)[:4] == b'RIFF'
        except Exception: ok = False
        wav_ok[sid] = ok; return ok

    def c36():
        if not campaign: R.append('OK   briefing: not a campaign mission (no objectives/transmissions/victory)'); return
        ex = exemption(note, 'NO_BRIEFING_OK')
        text = [x for x in bacts if x[26] in (3, 4) and struct.unpack_from('<I', x, 4)[0]]
        if ex: R.append(f'OK   briefing (NO_BRIEFING_OK: {ex})'); return
        if not S.get('MBRF') or not bacts:
            res(False, 'briefing: the mission has NO briefing (MBRF empty). Build one with m.B([...]): b_obj objectives, b_portrait, '
                       'voiced b_trans lines, b_end (see tools/bw/example_mission.py), or write NO_BRIEFING_OK: <reason> in the Design_Note'); return
        res(bool(text), f'briefing present ({len(BR)} briefing trigger(s), {len(text)} text/objective action(s))'
            + ('' if text else ': the briefing shows no text and no objectives'))
    def c37():
        if not campaign: R.append('OK   voiced dialogue: not a campaign mission'); return
        ex = exemption(note, 'NO_VOICE_OK')
        trans = [x for x in acts if x[26] == 7]
        voiced = [x for x in trans if struct.unpack_from('<I', x, 8)[0]]
        mute = [STR.get(struct.unpack_from('<I', x, 4)[0], '')[:50] for x in trans if not struct.unpack_from('<I', x, 8)[0]]
        missing = sorted({STR.get(struct.unpack_from('<I', x, 8)[0], '?') for x in voiced if not wav_exists(struct.unpack_from('<I', x, 8)[0])})
        bwav = [x for x in bacts if x[26] == 2 and struct.unpack_from('<I', x, 8)[0]]
        bmiss = sorted({STR.get(struct.unpack_from('<I', x, 8)[0], '?') for x in bwav if not wav_exists(struct.unpack_from('<I', x, 8)[0])})
        btext = [STR.get(struct.unpack_from('<I', x, 4)[0], '') for x in bacts if x[26] == 3]
        bspeak = [t for t in btext if speaker_line(t)]
        plain = []
        for x in acts:
            if x[26] == 9:
                t = STR.get(struct.unpack_from('<I', x, 4)[0], '')
                if speaker_line(t): plain.append(t[:60])
        n = len(voiced) + len(bwav)
        if ex:
            R.append(f'OK   voiced dialogue (NO_VOICE_OK: {ex}; {n} voiced lines)'); return
        res(n > 0, f'voiced dialogue: {len(voiced)} voiced transmission(s), {len(bwav)} voiced briefing line(s)'
            + ('' if n else ' -> the mission has NO voice lines. Voice every story line with m.voice(...) + m.trans / m.b_trans '
                              '(edge-tts, see DEPENDENCIES.md), or write NO_VOICE_OK: <reason> in the Design_Note'))
        res(not mute, f'every Transmission has a sound file {mute[:5] or ""}' + (f' ...{len(mute)} total' if len(mute) > 5 else ''))
        res(not missing and not bmiss, f'voice WAVs referenced by triggers/briefing exist in the MPQ {(missing + bmiss)[:5] or ""}')
        res(len(bwav) >= len(bspeak), f'briefing speaker lines are voiced ({len(bwav)} Play WAV for {len(bspeak)} speaker line(s))')
        known = {speaker_line(STR.get(struct.unpack_from('<I', x, 4)[0], '')) for x in voiced} | set(bspeak and map(speaker_line, bspeak))
        known |= set(re.findall(r'^###\s*(.+?)\s*$', note, re.M)); known.discard(None)
        hard = [t for t in plain if n == 0 or speaker_line(t) in known]
        soft = [t for t in plain if t not in hard]
        res(not hard, 'character lines are spoken (Transmission + WAV), not plain Display Text '
            + (f'{hard[:4]}' + (f' ...{len(hard)} total' if len(hard) > 4 else '') if hard else ''))
        if soft: R.append(f'WARN Display Text looks like a character line (name not a known speaker; voice it if a character speaks): {soft[:4]}')
    def c38():
        bad = sorted({(j, t[:60]) for j, t in STR.items() if RESIDUE.search(t)})
        res(not bad, 'no escaped colour-code residue in strings (u0003, \\x03, <03> would be printed literally) '
            + (f'{bad[:5]}' + (f' ...{len(bad)} total' if len(bad) > 5 else '') if bad else ''))
    def c39():
        r = subprocess.run([sys.executable, os.path.join(HERE, 'check_map_design_bw.py'), path], capture_output=True, text=True, cwd=ROOT)
        out = r.stdout.strip().splitlines()
        fails = [l[5:] for l in out if l.startswith('FAIL')]
        if r.returncode not in (0, 1) or not out:
            R.append(f'FAIL map_design: check_map_design_bw.py crashed (exit {r.returncode}) {r.stderr.strip()[-300:]}'); return
        R.extend('FAIL map_design: ' + f for f in fails)
        if not fails: R.append('OK   map design (check_map_design_bw: ' + (out[-1].split('RESULT')[-1].strip() if out else '?') + ')')
    def c40():
        import bw_cliff_outlines
        F, I = bw_cliff_outlines.check(path)
        R.extend('FAIL ' + f for f in F)
        info = next((i for i in I if i.startswith('cliff_outlines')), '')
        if not F: R.append('OK   cliff shape: ' + info.replace('cliff_outlines cliff outlines: ', ''))
        R.extend('WARN ' + i[5:] for i in I if i.startswith('WARN'))
    def c41():
        own = S.get('OWNR', b'')
        humans = {p for p in range(8) if p < len(own) and own[p] == 6}
        if not humans: R.append('OK   reward reasons: no human player'); return
        lines = reward_lines(note)
        good = [l for l in lines if l[3]]
        for l in lines:
            if not l[3]: res(False, f'REWARD_WHY line invalid ({l[4]}): {l[0][:80]}')
        def to_human(p, owners): return p in humans or (p == 13 and owners & humans) or p in (17, 18, 19, 20, 21)
        bad = []; n = 0
        for ti_, (c, a, owners) in enumerate(TR):
            types = {x[15] for x in c}
            if not c or types <= {22} or (types <= {22, 12} and all(x[15] != 12 or struct.unpack_from('<I', x, 8)[0] <= 5 for x in c)):
                continue                                   # start trigger (start resources, starting units)
            comments = ' '.join(STR.get(struct.unpack_from('<I', x, 4)[0], '') for x in a if x[26] == 47)
            if re.search(r'INCOME_OK\s*:\s*\S{3,}', comments): continue
            event = not types <= {22, 12}
            for x in a:
                typ, mod = x[26], x[27]; pl = struct.unpack_from('<I', x, 16)[0]; num = struct.unpack_from('<I', x, 20)[0]
                uid = struct.unpack_from('<H', x, 24)[0]; ow = set(owners)
                if typ == 26 and mod == 8 and to_human(pl, ow) and num > 0:
                    kind = ('minerals', 'gas', 'minerals and gas')[min(uid, 2)]
                    want = lambda l, num=num: str(num) in re.sub(r'[,.]', '', l[1])
                    desc = f'+{num} {kind} (trigger {ti_})'
                elif uid not in (33, 101) and ((typ == 48 and to_human(num, ow) and not to_human(pl, ow) and event) or (typ == 44 and to_human(pl, ow) and event)):
                    words = _unit_words(uid); grp = uid >= 228
                    want = lambda l, words=words, grp=grp: (grp and bool(l[1])) or any(w in l[1].lower() for w in words | (GROUP_WORDS if grp else set()))
                    desc = f"{'give' if typ == 48 else 'create'} unit {uid} for a human player (trigger {ti_})"
                else:
                    continue
                n += 1
                if not any(want(l) for l in good): bad.append(desc)
        res(not bad, f'rewards have an in-world source (REWARD_WHY: <objective> :: <reward> :: <source the player sees>; '
                     f'{n} reward action(s), {len(good)} valid REWARD_WHY line(s)) '
            + (f'-> missing for {bad[:5]}' + (f' ...{len(bad)} total' if len(bad) > 5 else '')
               + '. Give the reward a visible source (guarded cache, grateful ally, captured base or depot, rescued unit, seized cargo) '
                 'and document it, or mark non-quest income with a Comment INCOME_OK: <reason>' if bad else ''))
    for label, fn in (('36 briefing', c36), ('37 voiced dialogue', c37), ('38 text residue', c38), ('39 map design', c39), ('40 cliff shape', c40), ('41 reward reason', c41)):
        guard(label, fn)
    return R

if __name__ == '__main__':
    rc = 0
    for p in sys.argv[1:]:
        print('###', p)
        for l in run(p):
            print(l); rc |= l.startswith('FAIL')
    sys.exit(rc)
