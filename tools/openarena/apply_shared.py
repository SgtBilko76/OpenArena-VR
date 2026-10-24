#!/usr/bin/env python3
"""Shared-code glue so OpenArena's game code compiles against the Quake3Quest engine headers.
Re-runnable: each insertion is guarded by a marker string."""
import pathlib, subprocess
REPO = pathlib.Path(__file__).resolve().parents[2]
CPP = REPO / 'android/app/src/main/cpp'
CODE = CPP / 'code'

def insert(p, marker, old, new):
    t = p.read_text()
    if marker in t: print(f'  = {p.name}: already'); return
    assert t.count(old) == 1, f'{p}: {t.count(old)}x {old[:70]!r}'
    p.write_text(t.replace(old, new)); print(f'  + {p.name}')

insert(CODE / 'qcommon/q_shared.h', 'OpenArena game-code helpers', 'char\t*Q_strlwr( char *s1 );',
     '''// OpenArena game-code helpers (from OpenArena's q_shared.h)
#define Q_strequal(s1,s2) (Q_stricmp(s1,s2)==0)
#define Q_strnequal(s1, s2, n) (Q_strncmp(s1, s2, n)==0)
#define Q_strequaln(s1, s2, n) (Q_stricmpn(s1, s2, n)==0)
#define strequals(s1, s2) (strcmp(s1, s2)==0)
#ifndef Q_snprintf
#define Q_snprintf snprintf
#endif
void	Q_StrToLower(char *io_string);
char\t*Q_strlwr( char *s1 );''')
insert(CODE / 'qcommon/q_shared.c', 'void Q_StrToLower', '\nchar *Q_strlwr( char *s1 ) {',
     '''
void Q_StrToLower(char *io_string) {
	int i;
	for (i = 0; io_string[i]; i++) {
		io_string[i] = tolower(io_string[i]);
	}
}

char *Q_strlwr( char *s1 ) {''')

# OpenArena's q3_ui defines BASEOA and keeps its own static Controls_* functions
insert(CODE / 'ui/ui_shared.h', '#ifndef BASEOA', '''void Controls_GetConfig( void );
void Controls_SetConfig(qboolean restart);
void Controls_SetDefaults( void );''', '''#ifndef BASEOA
void Controls_GetConfig( void );
void Controls_SetConfig(qboolean restart);
void Controls_SetDefaults( void );
#endif''')

# OpenArena's menudef.h (voice chats, feeders) is a superset of Q3's
oa = subprocess.run(['git', '-C', str(pathlib.Path.home() / 'workspace/openarena-src/gamecode'),
                     'show', 'oaxB53.2:ui/menudef.h'], capture_output=True, text=True, check=True).stdout
(CPP / 'ui/menudef.h').write_text(oa); print('  + ui/menudef.h <- OpenArena')

# renderer/tr_types.h lives in renderercommon/ in ioq3
for d in ('cgame', 'game', 'q3_ui'):
    for f in (CODE / d).glob('*.[ch]'):
        t = f.read_text(errors='surrogateescape')
        if '"../renderer/tr_types.h"' in t:
            f.write_text(t.replace('"../renderer/tr_types.h"', '"../renderercommon/tr_types.h"'), errors='surrogateescape')
            print(f'  + {d}/{f.name}: tr_types path')
