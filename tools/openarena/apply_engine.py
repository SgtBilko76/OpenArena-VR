#!/usr/bin/env python3
"""Turn the Quake3Quest (ioq3quest) engine tree into the OpenArena VR engine.
Re-runnable: every edit asserts its anchor (or that it was already applied)."""
import pathlib, re, sys

REPO = pathlib.Path(__file__).resolve().parents[2]
CODE = REPO / 'android/app/src/main/cpp/code'
OA_MAKEFILE = pathlib.Path.home() / 'workspace/openarena-src/gamecode/Makefile.oaxB53.2'

def edit(path, old, new, count=1):
    p = REPO / path if not str(path).startswith('/') else pathlib.Path(path)
    t = p.read_text()
    if new in t and (old not in t or new not in old):
        print(f'  = {p.name}: already applied'); return
    n = t.count(old)
    assert n == count, f'{p}: anchor found {n}x (want {count}): {old[:80]!r}'
    p.write_text(t.replace(old, new)); print(f'  + {p.name}: {old.strip().splitlines()[0][:60]!r}')

# --- game identity: OpenArena, standalone (no Quake 3 pak0 / CD key checks) -------------------
edit('android/app/src/main/cpp/code/qcommon/q_shared.h', '''#ifdef STANDALONE
  #define PRODUCT_NAME				"iofoo3"
  #define BASEGAME					"foobar"
  #define CLIENT_WINDOW_TITLE		"changeme"
  #define CLIENT_WINDOW_MIN_TITLE	"changeme2"
  #define HOMEPATH_NAME_UNIX		".foo"
  #define HOMEPATH_NAME_WIN			"FooBar"
  #define HOMEPATH_NAME_MACOSX		HOMEPATH_NAME_WIN
//  #define STEAMPATH_NAME			"Foo Bar"
//  #define STEAMPATH_APPID         ""
  #define GAMENAME_FOR_MASTER		"foobar"	// must NOT contain whitespace
  #define CINEMATICS_LOGO		"foologo.roq"
  #define CINEMATICS_INTRO		"intro.roq"
//  #define LEGACY_PROTOCOL	// You probably don't need this for your standalone game
#else''', '''#ifdef STANDALONE
  // OpenArena VR: same identity as OpenArena's own engine (github.com/OpenArena/engine), so the
  // client finds and joins normal OpenArena servers (dpmaster lists them under Quake3Arena).
  #define PRODUCT_NAME				"OpenArena"
  #define BASEGAME					"baseoa"
  #define CLIENT_WINDOW_TITLE		"OpenArena VR"
  #define CLIENT_WINDOW_MIN_TITLE	"OA VR"
  #define HOMEPATH_NAME_UNIX		".openarena"
  #define HOMEPATH_NAME_WIN			"OpenArena"
  #define HOMEPATH_NAME_MACOSX		HOMEPATH_NAME_WIN
  #define GAMENAME_FOR_MASTER		"Quake3Arena"	// must NOT contain whitespace; OA servers use it
  #define CINEMATICS_INTRO		"intro.roq"
  #define LEGACY_PROTOCOL	// OpenArena 0.8.8 servers speak protocol 71 and accept 68
#else''')

edit('android/app/src/main/cpp/code/qcommon/qcommon.h',
     '#define MASTER_SERVER_NAME\t"master.quake3arena.com"',
     '#define MASTER_SERVER_NAME\t"dpmaster.deathmask.net"\t// OpenArena\'s master server')

edit('android/app/src/main/cpp/code/server/sv_init.c',
     '''	vr_master[0] = Cvar_Get("vr_master1", "mp.quakevr.com:27950", 0); // This is set to our Q3Q master
	vr_master[1] = Cvar_Get("vr_master2", MASTER_SERVER_NAME, 0);
	vr_master[2] = Cvar_Get("vr_master3", "master.ioquake3.org", 0);''',
     '''	// OpenArena VR: OpenArena's masters (the Quake3Quest master lists only Quake 3 servers)
	vr_master[0] = Cvar_Get("vr_master1", MASTER_SERVER_NAME, 0);
	vr_master[1] = Cvar_Get("vr_master2", "master.ioquake3.org", 0);
	vr_master[2] = Cvar_Get("vr_master3", "", 0);''')

edit('android/app/src/main/cpp/code/qcommon/files.c',
     'fs_nativeVMBase = Cvar_Get( "fs_nativeVMBase", "baseq3", CVAR_ARCHIVE );',
     'fs_nativeVMBase = Cvar_Get( "fs_nativeVMBase", BASEGAME, CVAR_ARCHIVE );')

# --- build settings ----------------------------------------------------------------------------
edit('Makefile.local', 'ANDROID_NDK_VERSION=21.1.6352462', 'ANDROID_NDK_VERSION=25.1.8937393')
edit('Makefile.local', 'BUILD_MISSIONPACK=1', 'BUILD_MISSIONPACK=0')
edit('Makefile.local', 'BUILD_STANDALONE=0', 'BUILD_STANDALONE=1')
edit('Makefile', '\nBASEGAME=baseq3\n', '\nBASEGAME=baseoa\n')

# OpenArena's game-module source lists (it has many more files than stock Q3)
mk = (REPO / 'Makefile').read_text()
oamk = OA_MAKEFILE.read_text()
def block(text, name):
    m = re.search(r'^' + name + r'_ = \\\n(?:.*\\\n)*.*\n', text, re.M)
    assert m, name; return m.group(0)
for name, extra in (('Q3CGOBJ', []), ('Q3GOBJ', []),
                    ('Q3UIOBJ', ['ui_controls3', 'ui_comfort', 'ui_vrkeyboard'])):
    new = block(oamk, name)
    for e in extra:
        if f'/{e}.o' not in new:
            new = new.replace('  \\\n  $(B)/$(BASEGAME)/qcommon/q_math.o',
                              f'  $(B)/$(BASEGAME)/ui/{e}.o \\\n  \\\n  $(B)/$(BASEGAME)/qcommon/q_math.o', 1)
    mk = mk.replace(block(mk, name), new)
(REPO / 'Makefile').write_text(mk); print('  + Makefile: OpenArena module lists')
