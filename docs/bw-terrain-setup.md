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

isomtool (`tools/lib/bw/isomtool_src/main.cpp`) uses Chkdraft's mapping core (MIT) and RareCpp, plus StormLib and
CascLib (both MIT).

### Linux (Debian/Ubuntu)
These are the steps the working Linux build was made with; they have not been re-run from a clean machine.
```
sudo apt install build-essential cmake git libbz2-dev zlib1g-dev libicu-dev
# StormLib and CascLib as static libraries in /usr/local/lib (the CMakeLists links /usr/local/lib/libstorm.a, libcasc.a)
git clone https://github.com/ladislav-zezula/StormLib && cmake -S StormLib -B StormLib/build -DCMAKE_BUILD_TYPE=Release && sudo cmake --build StormLib/build --target install
git clone https://github.com/ladislav-zezula/CascLib  && cmake -S CascLib -B CascLib/build -DCMAKE_BUILD_TYPE=Release -DCASC_BUILD_STATIC_LIB=ON && sudo cmake --build CascLib/build --target install
# Chkdraft + RareCpp sources next to main.cpp
git clone https://github.com/TheNitesWhoSay/Chkdraft tools/lib/bw/isomtool_src/external/Chkdraft
git clone https://github.com/TheNitesWhoSay/RareCpp  tools/lib/bw/isomtool_src/external/RareCpp
cmake -S tools/lib/bw/isomtool_src -B build/isomtool -DCMAKE_BUILD_TYPE=Release && cmake --build build/isomtool -j
cp build/isomtool/isomtool tools/lib/bw/isomtool
```
If the Chkdraft head no longer compiles with this main.cpp, check out an older Chkdraft commit (the mapping-core ISOM
API: `Scenario::placeIsomTerrain`, `Chk::IsomCache`).

### Windows
Recommended: **WSL2 (Ubuntu)**. Clone the repository inside WSL and follow the Linux steps; run all tools from WSL.
A native MSVC build is possible in principle (CMake + Visual Studio 2022, StormLib/CascLib built as static .lib, the
paths in `CMakeLists.txt` adjusted, the `-include gle.h` option replaced by `/FI gle.h`) but is **untested**; the
Python tools expect `tools/lib/bw/isomtool` and would need the `.exe` name.

### Smoke test
```
tools/lib/bw/isomtool tools/lib/bw/tileset/badlands.cv5 0     # lists the Badlands ISOM brushes
python3 tools/bw/example_mission.py                            # builds and checks the example mission
```

## 2. Tileset files
```
python3 tools/bw/extract_tilesets.py --from-folder "<folder with badlands.cv5 ...>"    # from a CascView export
python3 tools/bw/extract_tilesets.py --casc "<StarCraft folder>" --casclib /usr/local/lib/libcasc.so   # direct (untested)
```
- With **CascView** (Windows, free): open your StarCraft Remastered folder, extract the `TileSet` folder
  (`*.cv5 *.vx4ex *.vr4 *.wpe *.vf4`), then run `--from-folder` on it.
- The script validates sizes, converts an old `.vx4` to `.vx4ex` only when it covers every megatile the `.cv5` uses,
  and copies into `tools/lib/bw/tileset/`.
- The files are Blizzard data: keep them local, never commit or redistribute them.
