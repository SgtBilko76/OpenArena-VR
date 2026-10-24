#!/bin/bash
# Build OpenArena VR: engine + game modules (Makefile) and the full APK (Gradle).
# The ioq3 Makefile has NO header dependency tracking: an edited header (e.g. cg_local.h) leaves
# stale objects with the old struct layout behind, and modules then read the wrong fields
# (seen as sounds swapped / the announcer looping). So the make output is wiped whenever any
# header is newer than the last build.
set -euo pipefail
cd "$(dirname "$0")/../.."
export ANDROID_SDK_ROOT=${ANDROID_SDK_ROOT:-$HOME/workspace/android-sdk}
export JAVA_HOME=${JAVA_HOME:-$HOME/.local/jdk-17.0.20.1+1}
OUT=build/release-android-aarch64
STAMP=$OUT/.build-stamp
if [ -f "$STAMP" ] && [ -n "$(find android/app/src/main/cpp -name '*.h' -newer "$STAMP" -print -quit)" ]; then
	echo "header changed since last build: clean rebuild"
	rm -rf "$OUT"
fi
make -j"$(nproc)" release > build/make.log 2>&1 || { grep -m20 'error' build/make.log; exit 1; }
touch "$STAMP"
[ -d build/gamedata/baseoa ] || tools/openarena/stage_data.sh
cd android
./gradlew --no-daemon assembleRelease -PskipEngineBuild=true -PgameData="$PWD/../build/gamedata" > ../build/gradle.log 2>&1 \
	|| { grep -m20 -E 'error|FAIL' ../build/gradle.log; exit 1; }
ls -l app/build/outputs/apk/release/app-release.apk
