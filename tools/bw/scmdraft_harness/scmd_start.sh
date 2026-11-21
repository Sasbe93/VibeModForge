#!/bin/bash
# start ScmDraft under wine on $DISPLAY (default :57), pass extra args (map path), click Launch in the profile dialog.
# SCMD_EXE = the exe file name in $HARNESS/scmd/app to run (openmap.sh passes its own unique copy). Kills nothing.
H=${HARNESS:?set HARNESS}; export DISPLAY=${DISPLAY:-:57} WINEPREFIX=$H/wineprefix WINEDEBUG=${WD:--all}
EXE=${SCMD_EXE:-ScmDraft 2.exe}
LOG=$(readlink -f "$1"); shift; cd "$H/scmd/app"
(wine "$EXE" -console "$@" > "$LOG" 2>&1 &)
for i in $(seq 1 40); do sleep 1; xdotool search --name "Select Profile" >/dev/null 2>&1 && break; done
sleep 2; xdotool mousemove ${LAUNCH_X:-840} ${LAUNCH_Y:-755} click 1; sleep 8
