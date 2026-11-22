# BW terrain setup: isomtool and tileset files

The Brood War generator (`tools/lib/bw/sclib.py`) paints terrain with ISOM brushes and lets **isomtool** turn them into
real StarCraft tiles (cliff edges, ramps, shore transitions). isomtool reads the game's **tileset files**. Neither is
shipped: isomtool is built from source, the tileset files come from your own game install.

**What fails without them:** `Map.build_terrain()` stops with an error message; the minimap renderer, doodad helpers,
placement check and several predelivery checks (resource backs, cliff shape, doodad seams, walkability) cannot run.
There is no fallback. Do not work around it with rectangle plateaus or untextured maps; set the tools up or tell the
user what is missing.

Expected layout (both paths are git-ignored):
```
tools/lib/bw/isomtool                 # the binary (isomtool.exe on Windows)
tools/lib/bw/tileset/badlands.cv5     # .cv5 .vx4ex .vr4 .wpe (.vf4 optional) for each tileset
external/bw/vcod_seeds.txt            # python3 tools/bw/extract_vcod.py <any .scx/.scm you own>
```

## 1. Build isomtool

isomtool (`tools/lib/bw/isomtool_src/main.cpp`) uses Chkdraft's mapping core and RareCpp, plus StormLib and CascLib
(all four MIT). Their sources are cloned into `tools/lib/bw/isomtool_src/external/` (git-ignored), never committed.
One CMake file (`tools/lib/bw/isomtool_src/CMakeLists.txt`) builds on Linux, macOS and Windows.

### Quick way (all systems)
Needs git, CMake 3.24 or newer and a C++20 compiler (GCC 11+, Clang 14+, MinGW-w64 GCC, or MSVC 2022).
```
python3 tools/bw/build_isomtool.py               # Windows: py tools\bw\build_isomtool.py
python3 tools/bw/build_isomtool.py --casclib-dll # also the CascLib library for extract_tilesets.py --casc
```
The script clones the tested commits of the four libraries, builds into `build/isomtool/`, copies the binary to
`tools/lib/bw/isomtool` (`isomtool.exe` on Windows) and lists the Badlands brushes as a smoke test once the tileset
files exist. `--head` takes the newest upstream commits instead (untested combination). If the newest Chkdraft no
longer compiles with `main.cpp`, stay on the pinned commit (the API used: `Scenario::placeIsomTerrain`,
`Chk::IsomCache`).

### What the CMake file does (and why)
- **StormLib and CascLib** are built from their source trees as static libraries, without patching them. Where the
  system has zlib and bzip2 (Linux packages `zlib1g-dev libbz2-dev`) both libraries use them; otherwise StormLib's
  bundled copies are built once and given to both. (Their bundled zlib copies are different versions; linking both
  into one binary would need `--allow-multiple-definition` and mix two zlib versions.)
- **CMake 4** refuses CascLib's `cmake_minimum_required(VERSION 3.2)`. The CMake file sets the documented
  `CMAKE_POLICY_VERSION_MINIMUM=3.5` for that subproject only; no edit of CascLib is needed.
- **Winsock**: CascLib's HTTP code needs `ws2_32`. MSVC links it through a `#pragma comment(lib)`, MinGW ignores
  that pragma and CascLib's own CMake file only lists `wininet`, so the isomtool build adds `ws2_32` on Windows.
- **ICU**: Chkdraft's `cross_cut/simple_icu.cpp` needs three ICU functions (`u_strToUTF8`, `u_strFromUTF32`,
  `u_strFromUTF8WithSub`). `ISOMTOOL_ICU=AUTO` (default) links the system ICU when CMake finds it (Linux:
  `libicu-dev`), otherwise it compiles `icu_min/`, our implementation of exactly these three functions with ICU's
  behaviour (error codes, substitution of ill-formed UTF-8, buffer handling). It was cross-checked against ICU 76
  on 3 million random inputs with zero differences; `icu_min/test_icu_min.c` keeps known answers
  (`cmake --build build/isomtool --target test_icu_min` and run it). isomtool itself never calls these converters
  (it reads its files with `std::ifstream`); they only have to link.
- **Windows**: `gle.h` (a `GetLastError()` stub for old Chkdraft revisions on Linux) is not force-included, because
  it clashes with `windows.h`. `WIN32_LEAN_AND_MEAN` is not defined, so `windows.h` still includes `commdlg.h`,
  which Chkdraft's `system_io.cpp` needs; no patch to Chkdraft is required. MinGW builds link the GCC runtime
  statically, so `isomtool.exe` and `CascLib.dll` need no `libgcc_s`/`libstdc++`/`libwinpthread` DLLs next to them.
  `main.cpp` reads its file arguments as UTF-16 on Windows, so paths with any characters work (e.g. a user name
  in `%TEMP%`).
- Cache variables: `ISOMTOOL_CHKDRAFT_DIR`, `ISOMTOOL_RARECPP_DIR`, `ISOMTOOL_STORMLIB_DIR`, `ISOMTOOL_CASCLIB_DIR`
  (source trees), `ISOMTOOL_ICU` (`AUTO`/`SYSTEM`/`BUNDLED`), `ISOMTOOL_CASCLIB_DLL` (also build the shared CascLib).
  With `ISOMTOOL_STORMLIB_DIR`/`ISOMTOOL_CASCLIB_DIR` empty, installed `libstorm`/`libcasc` are linked instead.
- The Python tools call `tools/lib/bw/isomtool` (`isomtool.exe` on Windows) or the path in the environment
  variable `ISOMTOOL`.

### Manual build
Linux (Debian/Ubuntu):
```
sudo apt install build-essential cmake git zlib1g-dev libbz2-dev libicu-dev
git clone https://github.com/TheNitesWhoSay/Chkdraft    tools/lib/bw/isomtool_src/external/Chkdraft
git clone https://github.com/TheNitesWhoSay/RareCpp     tools/lib/bw/isomtool_src/external/RareCpp
git clone https://github.com/ladislav-zezula/StormLib  tools/lib/bw/isomtool_src/external/StormLib
git clone https://github.com/ladislav-zezula/CascLib   tools/lib/bw/isomtool_src/external/CascLib
cmake -S tools/lib/bw/isomtool_src -B build/isomtool -DCMAKE_BUILD_TYPE=Release
cmake --build build/isomtool -j
cp build/isomtool/isomtool tools/lib/bw/isomtool
```
(The commits `tools/bw/build_isomtool.py` pins are the tested ones; check them out to reproduce the tested build.)

Windows with MinGW-w64 (for example WinLibs GCC, which ships `cmake` and `mingw32-make`; Ninja also works), in
PowerShell from the repository root, after the four `git clone` lines above:
```
cmake -S tools/lib/bw/isomtool_src -B build/isomtool -G "MinGW Makefiles" "-DCMAKE_BUILD_TYPE=Release" "-DISOMTOOL_CASCLIB_DLL=ON"
cmake --build build/isomtool -j 8
copy build\isomtool\isomtool.exe tools\lib\bw\
```
Quote every `-D...` argument in PowerShell: Windows PowerShell 5.1 splits unquoted native-command arguments such as
`-DCMAKE_POLICY_VERSION_MINIMUM=3.5` at the dot (`build_isomtool.py` avoids this by passing arguments as a list). Windows with Visual Studio 2022: same CMake file, `cmake -S ... -B build/isomtool` picks the VS
generator, then `cmake --build build/isomtool --config Release`; the binary is in `build/isomtool/Release/`. The
MSVC build has not been tested.

WSL2 (Ubuntu) remains an alternative on Windows: clone the repository inside WSL and follow the Linux steps; it is
also the only way to run the real ScmDraft check (below).

### Verification status
- Linux (GCC 14): built from the pinned sources with system ICU/zlib/bzip2, and against installed StormLib/CascLib
  with `icu_min`; both binaries produce byte-identical terrain to the previous isomtool, and the BW example
  mission builds byte-identical and passes all delivery checks.
- Windows: cross-built with MinGW-w64 GCC 14 (Debian) and run under wine: the brush lists are identical to the Linux
  build, also with a non-ASCII folder name. The ISOM data and tile groups are identical; the tile *variants* inside
  a group differ, because Chkdraft picks variants with `std::rand()` and the Windows C runtime has a different
  generator. Maps built on Windows are therefore valid but not byte-identical to Linux builds of the same script.
- A native build on Windows itself has been reported working with WinLibs GCC (MinGW Makefiles) using an earlier,
  hand-patched version of these steps; the current CMake file has not yet been built on a Windows machine.

### Smoke test
```
tools/lib/bw/isomtool tools/lib/bw/tileset/badlands.cv5 0     # lists the Badlands ISOM brushes (Dirt = 2 ... Rocky Ground = 15)
python3 tools/bw/example_mission.py                            # builds and checks the example mission
```

## 2. Tileset files
```
python3 tools/bw/extract_tilesets.py --from-folder "<folder with badlands.cv5 ...>"    # from a CascView export
python3 tools/bw/extract_tilesets.py --casc "<StarCraft folder>"   # direct, needs the CascLib library (build_isomtool.py --casclib-dll)
```
- With **CascView** (Windows, free): open your StarCraft Remastered folder, extract the `TileSet` folder
  (`*.cv5 *.vx4ex *.vr4 *.wpe *.vf4`), then run `--from-folder` on it.
- `--casc` has been used on Windows with StarCraft Remastered (`C:\Program Files (x86)\StarCraft`), all eight tilesets.
  Without `--casclib` the script takes `build/isomtool/CascLib.dll` (Windows) or `libcasc.so`; on Linux it is untested.
- The script validates sizes, converts an old `.vx4` to `.vx4ex` only when it covers every megatile the `.cv5` uses,
  and copies into `tools/lib/bw/tileset/`.
- The files are Blizzard data: keep them local, never commit or redistribute them.
