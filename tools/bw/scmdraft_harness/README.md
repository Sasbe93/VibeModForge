# ScmDraft 2 open test (wine harness)

Opens a `.scx/.scm` in the real ScmDraft 2 (0.9.10) under wine + Xvfb and reports whether the editor
loaded the map. It answers "does this map open in ScmDraft 2?" directly instead of through a proxy.

No StarCraft data is needed or shipped: `mkfake.py` writes synthetic stand-ins (zero-filled `.dat` files,
1x1 fonts, tiny PCX/GRP files, dummy tables) and the tileset files from `tools/lib/bw/tileset`.
ScmDraft parses the map (CHK sections, ISOM/MTXM, DD2 doodads, units, locations, strings, triggers) against
the real tileset doodad tables; sprite graphics are fake, so this is an open/parse test, not a render test.

## Setup (Debian/Ubuntu, once)

    sudo dpkg --add-architecture i386 && sudo apt update
    sudo apt install wine wine32 xvfb xdotool x11-utils imagemagick innoextract mingw-w64
    export HARNESS=$PWD/../../../external/scmdraft_harness     # any writable dir
    ./setup.sh

`setup.sh` downloads the ScmDraft 2 0.9.10 installer (web.archive.org copy of stormcoast-fortress.net),
checks its sha256, unpacks it with innoextract, builds the fake StarCraft folder and registry keys, and
makes a patched COPY of the exe (`patch_fontpath.py`): two bytes so the 1.16 font path reads the
synthetic, unencrypted fonts. Map loading code is not touched. The patched binary is never committed.

## Use

    HARNESS=... ./openmap.sh path/to/map.scx      # prints the ScmDraft log; last line OK/FAIL
    HARNESS=... python3 ../check_scmdraft_open.py --real path/to/map.scx

Success marker: `(ENGINE) Loaded map:` in the log and a window titled with the map path.
Typical failure: `Could not locate information in the tileset for a particular (Type N)` followed by
`Could not load a map passed via command line` (DD2 references an unnamed cv5 doodad slot).
