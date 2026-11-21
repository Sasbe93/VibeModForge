#!/bin/bash
# start ScmDraft under wine on $DISPLAY (default :57), pass extra args (map path), click Launch in the profile dialog
H=${HARNESS:?set HARNESS}; export DISPLAY=${DISPLAY:-:57} WINEPREFIX=$H/wineprefix WINEDEBUG=${WD:--all}
pkill -f "ScmDraft 2.exe"; sleep 2
LOG=$(readlink -f "$1"); shift; cd "$H/scmd/app"
(wine "ScmDraft 2.exe" -console "$@" > "$LOG" 2>&1 &)
for i in $(seq 1 40); do sleep 1; xdotool search --name "Select Profile" >/dev/null 2>&1 && break; done
sleep 2; xdotool mousemove ${LAUNCH_X:-840} ${LAUNCH_Y:-755} click 1; sleep 8
