#!/bin/bash
# Stage the OpenArena 0.8.8 baseoa paks for the full APK: build/gamedata/baseoa/*.pk3
# (passed to Gradle as -PgameData=build/gamedata). Downloads the official release zip if needed.
set -euo pipefail
cd "$(dirname "$0")/../.."
ZIP=${1:-$HOME/workspace/openarena-src/openarena-0.8.8.zip}
URL=https://download.tuxfamily.org/openarena/rel/088/openarena-0.8.8.zip
OUT=build/gamedata/baseoa
if [ ! -f "$ZIP" ]; then
	mkdir -p "$(dirname "$ZIP")"
	curl -L -o "$ZIP.part" "$URL" && mv "$ZIP.part" "$ZIP"
fi
rm -rf build/gamedata && mkdir -p "$OUT"
unzip -q -j "$ZIP" 'openarena-0.8.8/baseoa/*.pk3' -d "$OUT"
ls -l "$OUT"
du -sh "$OUT"
