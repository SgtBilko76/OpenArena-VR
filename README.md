# OpenArena-VR

**OpenArena 0.8.8** as a standalone 6DoF VR game for Meta Quest (Quest 2 / Pro / 3 / 3S, tested on Quest 3)
and PICO 4 / Neo 3 (untested). One APK covers both.
One APK with the whole game inside: no PC, no extra downloads, no game files to copy.

Built on Team Beef's [ioq3quest](https://github.com/Team-Beef-Studios/ioq3quest) (Quake3Quest) VR engine,
merged with OpenArena's open-source game code ([OAX B53.2](https://github.com/OpenArena/gamecode)).

## Download

Get the APK from the [Releases](https://github.com/SgtBilko76/OpenArena-VR/releases) page, or from
[portroyale.online](https://portroyale.online/openarena.html).

## Features

- The full OpenArena 0.8.8: all maps, characters, weapons and game modes
- Single player against bots, skirmish
- Online multiplayer on the real OpenArena servers (official server list), including pure servers
  and mod servers (ratmod, Clan Arena, freeze tag, defrag, …); missing maps and mod files download automatically
- Quake3Quest VR controls: aim with the controller, weapon wheel, snap turning, comfort options, VR HUD
- 3D crosshair coloured by your health
- Virtual keyboard for the player name and other text fields

## Install

1. Sideload `OpenArena-VR-v1.1.0.apk` with [SideQuest](https://sidequestvr.com/setup-howto) or
   `adb install -r OpenArena-VR-v1.1.0.apk`. On PICO use adb or the sideloader you already use.
2. Start **OpenArena-VR** from *Unknown Sources* and allow file access.
3. The first start unpacks the game data (about 400 MB) to `/sdcard/OpenArenaVR/`. This takes about a minute.

## Controls

| Input | Action |
|---|---|
| Right trigger | Fire |
| Right grip (hold) | Weapon wheel: point at a weapon, release |
| Right stick left / right | Turn |
| Left stick click | Scoreboard |
| A / left trigger | Jump |
| B | Crouch |
| X | Use item |
| Y | Gesture |
| Left stick | Move |
| Left grip | Steady the weapon with both hands |
| Menus | Point with the controller, trigger = click |

Other layouts (weapon wheel on the stick, prev/next weapon) and comfort settings are in the VR options of the menu.
PICO controllers use the same layout.

## PICO

PICO support is new and **not tested on PICO hardware yet**. It needs PICO OS 5.9.0 or newer. If the game does
not start or the controllers do nothing, please open an issue; `adb logcat -s Quake3:*` shows how far it gets.

## Multiplayer

Multiplayer → Source **Internet** → Refresh. Servers running mods download their files before you join
(ratmod is about 100 MB); downloaded files are kept, so the next join is fast. Mod servers run with the
built-in VR game code: maps, textures and sounds of the mod work, special mod rules or HUD features may not.

## Building

Linux, Android SDK + NDK 25.1.8937393, JDK 17.

```sh
tools/openarena/stage_data.sh   # downloads openarena-0.8.8.zip, unpacks baseoa into build/gamedata
tools/openarena/build.sh                                      # engine, game modules, APK
```

The APK ends up in `android/app/build/outputs/apk/release/`.
`tools/openarena/` also holds the scripts that applied the OpenArena changes to the Quake3Quest code.

## Credits and licence

- [ioq3quest / Quake3Quest](https://github.com/Team-Beef-Studios/ioq3quest) by Team Beef (DrBeef and contributors)
- [ioquake3](https://ioquake3.org/)
- [OpenArena](https://openarena.ws/) engine and game code by the OpenArena team, game data OpenArena 0.8.8
- Quake III Arena source code © id Software

Code: GPL v2 (see `COPYING.txt`). OpenArena game data: GPL v2 and other free licences, see openarena.ws.
This project is not affiliated with id Software, Team Beef or the OpenArena team.
