#!/bin/bash
# Headless repro loop for the looping-announcer bug: start a bot match N times, pull qconsole.log each time.
A=~/workspace/android-sdk/platform-tools/adb; S=192.168.178.115:5555; P=com.bilko.openarenavr
OUT=${OUT:-$TMPDIR/sndruns}; mkdir -p "$OUT"
MAP=${MAP:-oa_minia}
for i in $(seq 1 ${RUNS:-3}); do
	$A -s $S shell "am force-stop $P; rm -f /sdcard/OpenArenaVR/baseoa/qconsole.log; echo '+set fs_basepath /sdcard/OpenArenaVR/ +set fs_basegame baseoa +set logfile 2 +set g_gametype 2 +spmap $MAP' > /sdcard/OpenArenaVR/commandline.txt; am broadcast -a com.oculus.vrpowermanager.prox_close >/dev/null; input keyevent KEYCODE_WAKEUP"
	sleep 3
	$A -s $S shell monkey -p $P -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1
	sleep ${SECS:-45}
	$A -s $S pull /sdcard/OpenArenaVR/baseoa/qconsole.log "$OUT/run$i.log" >/dev/null 2>&1
	echo "run $i: $(grep -c 'SNDDBG.*Looping\|SNDDBG loop' "$OUT/run$i.log") loop lines, $(grep -c 'entered the game' "$OUT/run$i.log") entered"
done
$A -s $S shell "am force-stop $P"
