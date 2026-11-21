#!/usr/bin/env python3
"""Extract / install the StarCraft tileset files that the BW terrain generator needs, from YOUR OWN game install.

The files are Blizzard data and are never committed (tools/lib/bw/tileset/ is git-ignored). Without them
sclib.Map.build_terrain(), the doodad helpers, the minimap renderer and several checks stop with an error;
there is no fallback terrain (never build "rectangle plateau" maps without ISOM terrain).

Needed per tileset (badlands, platform, install, ashworld, jungle, desert, ice, twilight):
  <name>.cv5    tile groups (ISOM / terrain flags)        required
  <name>.vx4ex  megatile -> minitile graphics (32-bit)     required (made from <name>.vx4 when only that exists and
                                                          the vx4 covers every megatile the cv5 uses)
  <name>.vr4    minitile pixels                           required (minimap/preview render)
  <name>.wpe    palette                                   required (minimap/preview render)
  <name>.vf4    minitile walk flags                       optional (precise walkability; checks fall back to cv5 flags)

Two ways:
  A) from a folder you exported yourself (CascView "Extract", or an old 1.16 install's unpacked tileset folder):
       python3 tools/bw/extract_tilesets.py --from-folder "<folder that contains badlands.cv5 ...>"
  B) straight from a StarCraft Remastered install with CascLib (https://github.com/ladislav-zezula/CascLib;
     build it and point --casclib at libcasc.so / CascLib.dll):
       python3 tools/bw/extract_tilesets.py --casc "<StarCraft install folder>" --casclib /usr/local/lib/libcasc.so
     NOTE: mode B is written against the public CascLib API but has NOT been tested on a real install here.
     If it fails, use mode A with CascView (Windows) and report the error.
Both modes validate the file sizes and copy into tools/lib/bw/tileset/ (or --out).
"""
import argparse, ctypes, os, shutil, struct, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
NAMES = ['badlands', 'platform', 'install', 'ashworld', 'jungle', 'desert', 'ice', 'twilight']
REQ = ['cv5', 'vx4ex', 'vr4', 'wpe']; OPT = ['vf4']
UNIT = {'cv5': 52, 'vx4ex': 64, 'vx4': 32, 'vr4': 64, 'vf4': 32}

def valid(ext, data):
    if ext == 'wpe': return len(data) == 1024
    return len(data) > 0 and len(data) % UNIT[ext] == 0

def vx4_to_vx4ex(data):
    """VX4 (16 x u16 per megatile: bit0 flip, bits1-15 VR4 index) -> VX4EX (16 x u32, same layout)."""
    n = len(data) // 2
    return struct.pack(f'<{n}I', *struct.unpack(f'<{n}H', data))

def max_megatile(cv5):
    """highest megatile index referenced by a cv5 (52-byte groups: 20-byte header + 16 x u16 megatile ids)"""
    n = len(cv5) // 52
    return max((v for g in range(n) for v in struct.unpack_from('<16H', cv5, g*52+20)), default=0)

def install(get, out):
    os.makedirs(out, exist_ok=True); ok = {}; report = []
    for name in NAMES:
        files = {}
        for ext in REQ + OPT + ['vx4']:
            d = get(name, ext)
            if d is not None and valid(ext, d): files[ext] = d
            elif d is not None: report.append(f'  {name}.{ext}: unexpected size {len(d)} (skipped)')
        if 'vx4ex' not in files and 'vx4' in files:
            need = max_megatile(files['cv5']) if 'cv5' in files else 0
            if need < len(files['vx4']) // 32: files['vx4ex'] = vx4_to_vx4ex(files['vx4'])
            else: report.append(f'  {name}.vx4 has {len(files["vx4"]) // 32} megatiles but {name}.cv5 uses #{need}: '
                                'the cv5 is from a newer game version than the vx4 - extract vx4ex from the same install')
        miss = [e for e in REQ if e not in files]
        if miss:
            report.append(f'  {name}: missing {miss} - tileset not installed'); continue
        for ext, d in files.items():
            if ext == 'vx4': continue
            open(os.path.join(out, f'{name}.{ext}'), 'wb').write(d)
        ok[name] = sorted(e for e in files if e != 'vx4')
    for name, exts in ok.items(): print(f'OK   {name}: {", ".join(exts)}')
    for r in report: print('WARN' + r)
    print(f'RESULT {len(ok)}/8 tilesets installed in {out}')
    return 0 if ok else 1

def from_folder(folder):
    idx = {}
    for dp, _, fs in os.walk(folder):
        for f in fs: idx.setdefault(f.lower(), os.path.join(dp, f))
    def get(name, ext):
        p = idx.get(f'{name}.{ext}')
        return open(p, 'rb').read() if p else None
    return get

def from_casc(storage, lib):
    L = ctypes.CDLL(lib)
    H = ctypes.c_void_p
    L.CascOpenStorage.argtypes = [ctypes.c_char_p, ctypes.c_uint32, ctypes.POINTER(H)]; L.CascOpenStorage.restype = ctypes.c_bool
    L.CascOpenFile.argtypes = [H, ctypes.c_char_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(H)]; L.CascOpenFile.restype = ctypes.c_bool
    L.CascGetFileSize.argtypes = [H, ctypes.POINTER(ctypes.c_uint32)]; L.CascGetFileSize.restype = ctypes.c_uint32
    L.CascReadFile.argtypes = [H, ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]; L.CascReadFile.restype = ctypes.c_bool
    L.CascCloseFile.argtypes = [H]; L.CascCloseStorage.argtypes = [H]
    hs = H()
    if not L.CascOpenStorage(storage.encode(), 0, ctypes.byref(hs)):
        raise SystemExit(f'CascOpenStorage failed for {storage!r} (try the install folder that contains .build.info, '
                         'or append ":s1" for the StarCraft product)')
    def get(name, ext):
        for path in (f'TileSet\\{name}.{ext}', f'tileset\\{name}.{ext}', f'SD\\TileSet\\{name}.{ext}'):
            hf = H()
            if not L.CascOpenFile(hs, path.encode(), 0, 0, ctypes.byref(hf)): continue
            hi = ctypes.c_uint32(0); n = L.CascGetFileSize(hf, ctypes.byref(hi))
            buf = ctypes.create_string_buffer(n); got = ctypes.c_uint32(0)
            okr = L.CascReadFile(hf, buf, n, ctypes.byref(got)); L.CascCloseFile(hf)
            if okr: return buf.raw[:got.value]
        return None
    return get

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--from-folder'); g.add_argument('--casc')
    ap.add_argument('--casclib', default='libcasc.so' if os.name != 'nt' else 'CascLib.dll')
    ap.add_argument('--out', default=os.path.join(ROOT, 'tools', 'lib', 'bw', 'tileset'))
    a = ap.parse_args()
    sys.exit(install(from_folder(a.from_folder) if a.from_folder else from_casc(a.casc, a.casclib), a.out))
