#!/usr/bin/env bash
# Screenshots of the local preview with headless Microsoft Edge (Windows), for checking the layout by eye.
#   python -m http.server -d site 8765 --bind 127.0.0.1   (in another terminal; stop it afterwards)
#   bash tools/shoot.sh NAME WIDTH HEIGHT light|dark [PATH]
# Writes out/shots/NAME.png. Headless Edge exits on its own after the virtual time budget.
set -euo pipefail
name=$1 width=$2 height=$3 theme=$4 path=${5:-/}
edge="${EDGE:-/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe}"
mkdir -p out/shots
if [[ $theme == dark ]]; then scheme=(--force-dark-mode --blink-settings=preferredColorScheme=0)
else scheme=(--blink-settings=preferredColorScheme=1); fi
"$edge" --headless --disable-gpu --hide-scrollbars --no-first-run --user-data-dir="${TEMP:-/tmp}/edge-leaf-shots" \
  "${scheme[@]}" --virtual-time-budget=6000 --window-size="$width,$height" \
  --screenshot="$(cygpath -w "$PWD/out/shots/$name.png" 2>/dev/null || echo "$PWD/out/shots/$name.png")" \
  "http://127.0.0.1:8765$path" 2>/dev/null | grep -i written || true
