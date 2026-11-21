#!/bin/bash
# one-time ScmDraft 2 harness setup into $HARNESS (see README.md)
set -e
H=${HARNESS:?set HARNESS}; HERE=$(cd "$(dirname "$0")" && pwd); mkdir -p "$H"; cd "$H"
URL='https://web.archive.org/web/2024id_/http://www.stormcoast-fortress.net/downloads/scmdraft2ZIP/download/'
SHA=9d74907310ec9ccafa2bbcb02182548f755081ac4b9e24b0628d4c49ac3d93c4   # sha256 of scmdraft2_setup.exe (0.9.10)
[ -f scmdraft2_setup.exe ] || curl -L -o scmdraft2_setup.exe "$URL"
sha256sum scmdraft2_setup.exe | grep -q "^$SHA" || { echo "unexpected installer checksum"; exit 1; }
[ -d scmd/app ] || innoextract -d scmd scmdraft2_setup.exe
python3 "$HERE/patch_fontpath.py" "scmd/app/ScmDraft 2.exe"
mkdir -p fakesc fakeexe
cat > fakeexe/main.c <<'C'
int main(){return 0;}
C
cat > fakeexe/ver.rc <<'C'
1 VERSIONINFO
FILEVERSION 1,16,1,1
PRODUCTVERSION 1,16,1,1
FILEOS 0x4
FILETYPE 0x1
BEGIN
 BLOCK "StringFileInfo"
 BEGIN
  BLOCK "040904b0"
  BEGIN
   VALUE "FileVersion", "1, 16, 1, 1"
   VALUE "ProductName", "Starcraft"
   VALUE "ProductVersion", "1, 16, 1, 1"
  END
 END
 BLOCK "VarFileInfo"
 BEGIN
  VALUE "Translation", 0x409, 1200
 END
END
C
i686-w64-mingw32-windres fakeexe/ver.rc -O coff -o fakeexe/ver.o
i686-w64-mingw32-gcc -o fakesc/StarCraft.exe fakeexe/main.c fakeexe/ver.o
TS=$(cd "$HERE/../../lib/bw/tileset" && pwd) python3 "$HERE/mkfake.py"
export WINEPREFIX=$H/wineprefix WINEDEBUG=-all
wineboot -i >/dev/null 2>&1 || true
W="Z:${H//\//\\}\\fakesc"
for K in 'HKLM\Software\Blizzard Entertainment\Starcraft' 'HKLM\Software\Wow6432Node\Blizzard Entertainment\Starcraft'; do
  wine reg add "$K" /v InstallPath /t REG_SZ /d "$W" /f >/dev/null
  wine reg add "$K" /v Program /t REG_SZ /d "$W\\StarCraft.exe" /f >/dev/null
done
export DISPLAY=${DISPLAY:-:57}; xdpyinfo -display "$DISPLAY" >/dev/null 2>&1 || (Xvfb "$DISPLAY" -screen 0 1280x1024x24 -nolisten tcp >/dev/null 2>&1 &); sleep 2   # setup only; openmap.sh starts its own display
SE="scmd_setup_$$.exe"; cp "$H/scmd/app/ScmDraft 2.exe" "$H/scmd/app/$SE"
SCMD_EXE="$SE" "$HERE/scmd_start.sh" "$H/first_run.log" >/dev/null      # creates the Default profile
pkill -f "$SE" || true; sleep 2; rm -f "$H/scmd/app/$SE"   # only this setup run's copy, never other ScmDraft runs
wine reg add 'HKCU\Software\Stormcoast Fortress\ScmDraft 2.0\Settings\Default' /v GameDataVersion /t REG_BINARY /d 02000000 /f >/dev/null
echo "harness ready in $H"
