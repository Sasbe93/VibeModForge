#!/bin/bash
# open one map in ScmDraft 2 (synthetic data); prints the ScmDraft log and a final OK/FAIL line.
# Isolated per run: its own Xvfb on a free display (unless SCMD_DISPLAY is given), its own copy of the exe under a unique
# name, its own log; on exit it kills only the processes of that exe copy and its own Xvfb. Other ScmDraft runs and
# other X displays on the machine are never touched.
H=${HARNESS:?set HARNESS}; HERE=$(cd "$(dirname "$0")" && pwd)
M=$(readlink -f "$1"); WM="Z:${M//\//\\}"
TAG="scmd_$$_$RANDOM"; EXE="$TAG.exe"; APP="$H/scmd/app"; LOG="$H/open_$TAG.log"; XPID=""
cleanup() {
  pkill -f "$EXE" 2>/dev/null; sleep 1; pkill -9 -f "$EXE" 2>/dev/null
  rm -f "$APP/$EXE"
  [ -n "$XPID" ] && kill "$XPID" 2>/dev/null
  [ -n "$KEEP_LOG" ] || rm -f "$LOG"
}
trap cleanup EXIT
# one real run at a time per harness (parallel runs in one wine prefix starve each other and miss the load);
# a waiting run just queues, nothing is killed
exec 9>"$H/.openmap.lock"; flock -w ${LOCK_WAIT:-500} 9 || { echo "harness busy (lock wait timed out)"; echo "SCMDRAFT_OPEN FAIL"; exit 0; }
if [ -n "$SCMD_DISPLAY" ]; then D=$SCMD_DISPLAY
else
  D=""
  for n in $(shuf -i 100-899 -n 40); do
    [ -e "/tmp/.X$n-lock" ] || [ -e "/tmp/.X11-unix/X$n" ] && continue
    Xvfb ":$n" -screen 0 1280x1024x24 -nolisten tcp >/dev/null 2>&1 & XPID=$!
    for i in $(seq 1 20); do xdpyinfo -display ":$n" >/dev/null 2>&1 && break; kill -0 $XPID 2>/dev/null || break; sleep 0.25; done
    if xdpyinfo -display ":$n" >/dev/null 2>&1; then D=":$n"; break; fi
    kill $XPID 2>/dev/null; XPID=""
  done
  [ -z "$D" ] && { echo "no free X display for Xvfb"; echo "SCMDRAFT_OPEN FAIL"; exit 0; }
fi
export DISPLAY=$D
cp "$APP/ScmDraft 2.exe" "$APP/$EXE" || { echo "cannot copy the exe"; echo "SCMDRAFT_OPEN FAIL"; exit 0; }
SCMD_EXE="$EXE" WD=err+all,warn+seh "$HERE/scmd_start.sh" "$LOG" "$WM" >/dev/null
"$HERE/dismiss.sh" open >/dev/null 2>&1; sleep ${WAIT:-6}; "$HERE/dismiss.sh" open2 >/dev/null 2>&1
for i in $(seq 1 ${LOAD_WAIT:-30}); do grep -aq "(ENGINE) Loaded map:\|Could not load a map" "$LOG" && break; sleep 1; done; sleep 1
grep -a 'dispatch_exception "' "$LOG" | sed 's/^.*dispatch_exception "//; s/\\r\\n"$//' | sed -n '/Loaded plugin/,$p' | grep -v "Loaded plugin"
T=$(xwininfo -root -tree | grep -F "ScmDraft" | grep -F "$(basename "$M")" | head -1)
if grep -aq "(ENGINE) Loaded map:" "$LOG" && [ -n "$T" ] && ! grep -aq "Could not load a map" "$LOG"; then echo "SCMDRAFT_OPEN OK"; else echo "SCMDRAFT_OPEN FAIL"; fi
