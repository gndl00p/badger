#!/usr/bin/env bash
set -euo pipefail

DEVICE="${DEVICE:-/dev/ttyACM0}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

MP="mpremote connect $DEVICE"

echo "Flashing to $DEVICE from $HERE"

$MP cp "$HERE/main.py"    :main.py
$MP cp "$HERE/fetcher.py" :fetcher.py
$MP cp "$HERE/render.py"  :render.py
$MP cp "$HERE/picker.py"  :picker.py
$MP cp "$HERE/status.py"  :status.py
$MP cp "$HERE/store.py"   :store.py

if [ ! -f "$HERE/config.py" ]; then
  echo "!! $HERE/config.py missing — copy config.example.py and fill in WIFI creds before flashing config."
else
  $MP cp "$HERE/config.py" :config.py
fi

# Only create /state.json on first flash — don't clobber persisted last_data.
$MP exec 'import os
try:
    os.stat("/state.json")
    print("state.json exists, leaving alone")
except OSError:
    open("/state.json","w").write("{}")
    print("state.json created")'

echo "Done. Soft-reset:"
$MP soft-reset
