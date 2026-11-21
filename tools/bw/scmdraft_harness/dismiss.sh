#!/bin/bash
# click OK on dialogs titled Error/Warning (up to N times), screenshots into $HARNESS/shots
H=${HARNESS:?set HARNESS}; export DISPLAY=${DISPLAY:-:57}; P=${1:-d}; RX=${2:-^(Error|Warning)$}; mkdir -p "$H/shots"
for i in $(seq 1 ${3:-6}); do
  W=$(xdotool search --name "$RX" 2>/dev/null | head -1); [ -z "$W" ] && break
  import -window root "$H/shots/${P}_$i.png"
  eval $(xdotool getwindowgeometry --shell $W)
  xdotool mousemove $((X+WIDTH/2)) $((Y+HEIGHT-22)) click 1; sleep 5
done
import -window root "$H/shots/${P}_end.png"
