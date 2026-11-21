#!/bin/bash
# open one map in ScmDraft 2 (synthetic data); prints the ScmDraft log and a final OK/FAIL line
H=${HARNESS:?set HARNESS}; HERE=$(cd "$(dirname "$0")" && pwd)
M=$(readlink -f "$1"); WM="Z:${M//\//\\}"; LOG=$H/open.log
WD=err+all,warn+seh "$HERE/scmd_start.sh" "$LOG" "$WM" >/dev/null
"$HERE/dismiss.sh" open >/dev/null 2>&1; sleep ${WAIT:-6}; "$HERE/dismiss.sh" open2 >/dev/null 2>&1
grep -a 'dispatch_exception "' "$LOG" | sed 's/^.*dispatch_exception "//; s/\\r\\n"$//' | sed -n '/Loaded plugin/,$p' | grep -v "Loaded plugin"
T=$(DISPLAY=${DISPLAY:-:57} xwininfo -root -tree | grep -F "ScmDraft" | grep -F "$(basename "$M")" | head -1)
pkill -f "ScmDraft 2.exe"
if grep -aq "(ENGINE) Loaded map:" "$LOG" && [ -n "$T" ] && ! grep -aq "Could not load a map" "$LOG"; then echo "SCMDRAFT_OPEN OK"; else echo "SCMDRAFT_OPEN FAIL"; fi
