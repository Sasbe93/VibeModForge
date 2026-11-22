#!/usr/bin/env python3
"""Fetch the isomtool dependencies and build isomtool, on Linux, macOS and Windows.

    python3 tools/bw/build_isomtool.py                 # clone pinned sources, build, install tools/lib/bw/isomtool[.exe]
    python3 tools/bw/build_isomtool.py --casclib-dll   # also CascLib.dll / libcasc.so for extract_tilesets.py --casc
    python3 tools/bw/build_isomtool.py --head          # newest upstream commits instead of the tested ones

Needs git, CMake >= 3.24 and a C++20 compiler (GCC/MinGW-w64, Clang or MSVC). The sources go to
tools/lib/bw/isomtool_src/external/ (git-ignored), the build to build/isomtool/. All four libraries are MIT
licensed; nothing of them is committed. Arguments go to git/cmake as lists, so no shell quoting is involved
(PowerShell splits unquoted -DNAME=3.5 style arguments). Steps and manual build: docs/bw-terrain-setup.md."""
import argparse, os, shutil, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
SRC = os.path.join(ROOT, 'tools', 'lib', 'bw', 'isomtool_src')
# Tested combination (Linux GCC 14 build and MinGW-w64 GCC 14 cross build); see docs/bw-terrain-setup.md.
DEPS = [
    ('Chkdraft', 'https://github.com/TheNitesWhoSay/Chkdraft', '7d256a3e566ea8a68fe973e5ff80c11e619adf2e'),
    ('RareCpp', 'https://github.com/TheNitesWhoSay/RareCpp', 'aaa9b0f0aa1fcf1ce357c3cc9bc0fe8a1fbc5569'),  # 2.6.5, pinned by Chkdraft
    ('StormLib', 'https://github.com/ladislav-zezula/StormLib', 'd60b7e6d3501474f4d92c7b9c752a37e78385f67'),
    ('CascLib', 'https://github.com/ladislav-zezula/CascLib', '6b889ec8f421cbc9baccec296c582362ab917887'),
]


def run(cmd, **k):
    print('+', ' '.join(f'"{c}"' if ' ' in c else c for c in cmd), flush=True)
    subprocess.run(cmd, check=True, **k)


def fetch(name, url, commit, ext, head):
    d = os.path.join(ext, name)
    if os.path.isdir(os.path.join(d, '.git')) or os.path.isfile(os.path.join(d, '.git')):
        print(f'{name}: using existing checkout {d}')
        return
    if os.path.exists(d):
        print(f'{name}: using existing folder {d} (not a git checkout)')
        return
    if head:
        run(['git', 'clone', '--depth', '1', url, d])
    else:
        os.makedirs(d)
        run(['git', 'init', '-q'], cwd=d)
        run(['git', 'fetch', '-q', '--depth', '1', url, commit], cwd=d)
        run(['git', '-c', 'advice.detachedHead=false', 'checkout', '-q', 'FETCH_HEAD'], cwd=d)


def generator():
    """CMake picks Visual Studio on Windows when it is installed; with only MinGW-w64 (e.g. WinLibs) choose for it."""
    if os.name != 'nt' or shutil.which('cl'): return []
    if shutil.which('ninja'): return ['-G', 'Ninja']
    if shutil.which('mingw32-make'): return ['-G', 'MinGW Makefiles']
    return []


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--casclib-dll', action='store_true', help='also build the CascLib shared library')
    ap.add_argument('--head', action='store_true', help='clone the newest upstream commits (untested combination)')
    ap.add_argument('--build-dir', default=os.path.join(ROOT, 'build', 'isomtool'))
    ap.add_argument('--generator', help='CMake generator, e.g. "Ninja" or "MinGW Makefiles"')
    ap.add_argument('--cmake-arg', action='append', default=[], help='extra -D... argument for CMake (repeatable)')
    a = ap.parse_args()
    for tool in ('git', 'cmake'):
        if not shutil.which(tool): sys.exit(f'{tool} not found on PATH (docs/bw-terrain-setup.md)')
    ext = os.path.join(SRC, 'external'); os.makedirs(ext, exist_ok=True)
    for name, url, commit in DEPS: fetch(name, url, commit, ext, a.head)
    gen = ['-G', a.generator] if a.generator else generator()
    cfg = ['cmake', '-S', SRC, '-B', a.build_dir, '-DCMAKE_BUILD_TYPE=Release'] + gen
    if a.casclib_dll: cfg.append('-DISOMTOOL_CASCLIB_DLL=ON')
    run(cfg + a.cmake_arg)
    run(['cmake', '--build', a.build_dir, '--config', 'Release', '--parallel'])
    exe = 'isomtool.exe' if os.name == 'nt' else 'isomtool'
    built = next((p for p in (os.path.join(a.build_dir, exe), os.path.join(a.build_dir, 'Release', exe)) if os.path.exists(p)), None)
    if not built: sys.exit(f'build finished but {exe} was not found in {a.build_dir}')
    dst = os.path.join(ROOT, 'tools', 'lib', 'bw', exe)
    shutil.copy2(built, dst); print(f'installed {dst}')
    cv5 = os.path.join(ROOT, 'tools', 'lib', 'bw', 'tileset', 'badlands.cv5')
    if os.path.exists(cv5):
        out = subprocess.run([dst, cv5, '0'], capture_output=True, text=True, errors='replace').stdout
        ok = '2 Dirt' in out and '14 Asphalt' in out
        names = [l.split(' sort=')[0] for l in out.splitlines() if ' sort=' in l and not l.split(' sort=')[0].strip().isdigit()]
        print(('OK   smoke test: ' if ok else 'FAIL smoke test: ') + 'Badlands brushes ' + ', '.join(names))
        if not ok: sys.exit(1)
    else:
        print('isomtool installed; smoke test skipped (no tileset files yet: tools/bw/extract_tilesets.py)')


if __name__ == '__main__':
    main()
