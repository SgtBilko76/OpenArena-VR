#!/usr/bin/env python3
"""Online play fixes for OpenArena VR (re-runnable, every edit asserts its anchor or is already applied).
 - pakQ3Q.pk3 (VR GLSL + VR shaders/menus) stays usable on pure servers and is never reported to them
 - cgame survives item numbers from server game code it does not know (was a fatal CG_Error)"""
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[2]
CODE = REPO / 'android/app/src/main/cpp/code'

def edit(path, old, new, count=1):
    p = CODE / path
    t = p.read_text()
    if new in t and (old not in t or new not in old):
        print(f'  = {p.name}: already applied'); return
    n = t.count(old)
    assert n == count, f'{p}: anchor found {n}x (want {count}): {old[:80]!r}'
    p.write_text(t.replace(old, new)); print(f'  + {p.name}: {old.strip().splitlines()[0][:60]!r}')

# --- pure servers: the VR pak is client-side only ------------------------------------------------
edit('qcommon/files.c', '''qboolean FS_PakIsPure( pack_t *pack ) {
	int i;

	if ( fs_numServerPaks ) {''', '''qboolean FS_PakIsPure( pack_t *pack ) {
	int i;

	// OpenArena VR: the VR renderer's GLSL and VR menu/crosshair shaders live in pakQ3Q.pk3, which no
	// server has. Without it a pure server makes the renderer load OpenArena's desktop GLSL
	// ("Couldn't compile shader"). It holds no game code, so keep it usable everywhere.
	if ( !Q_stricmp( pack->pakBasename, "pakQ3Q" ) ) {
		return qtrue;
	}

	if ( fs_numServerPaks ) {''')

# never mark it referenced, so it is not listed in the pure checksums sent to the server
# (a pak the server does not have would get us kicked as "unpure client")
edit('qcommon/files.c', '''					if (!(pak->referenced & FS_GENERAL_REF))
					{''', '''					if (!(pak->referenced & FS_GENERAL_REF) && Q_stricmp(pak->pakBasename, "pakQ3Q"))	// OpenArena VR
					{''')
edit('qcommon/files.c', '''					if(strstr(filename, "cgame.qvm"))
						pak->referenced |= FS_CGAME_REF;
					if(strstr(filename, "ui.qvm"))
						pak->referenced |= FS_UI_REF;''', '''					if(strstr(filename, "cgame.qvm") && Q_stricmp(pak->pakBasename, "pakQ3Q"))
						pak->referenced |= FS_CGAME_REF;
					if(strstr(filename, "ui.qvm") && Q_stricmp(pak->pakBasename, "pakQ3Q"))
						pak->referenced |= FS_UI_REF;''')

# --- unknown items from server game code: warn and ignore instead of dropping the connection -----
edit('cgame/cg_weapons.c', '''	if ( itemNum < 0 || itemNum >= bg_numItems ) {
		CG_Error( "CG_RegisterItemVisuals: itemNum %d out of range [0-%d]", itemNum, bg_numItems-1 );
	}''', '''	if ( itemNum < 0 || itemNum >= bg_numItems ) {
		// OpenArena VR: online servers may run game code with more items than ours
		static int warned;
		if ( warned++ < 5 ) {
			CG_Printf( S_COLOR_YELLOW "CG_RegisterItemVisuals: itemNum %d out of range [0-%d], ignored\\n", itemNum, bg_numItems-1 );
		}
		return;
	}''')

# callers that index cg_items[] with a server-provided item number
SAN = '\tif ( value < 0 || value >= bg_numItems ) value = 0;\t// OpenArena VR: unknown server item\n'
edit('cgame/cg_draw.c', '''	value = cg.itemPickup;
	if (value) {''', '''	value = cg.itemPickup;
''' + SAN + '''	if (value) {''')
edit('cgame/cg_draw.c', '''	value = cg.snap->ps.stats[STAT_HOLDABLE_ITEM];
	if (value) {
		CG_RegisterItemVisuals(value);''', '''	value = cg.snap->ps.stats[STAT_HOLDABLE_ITEM];
''' + SAN + '''	if (value) {
		CG_RegisterItemVisuals(value);''')
edit('cgame/cg_players.c', '''        value = cg.snap->ps.stats[STAT_HOLDABLE_ITEM];

        if (value ) {''', '''        value = cg.snap->ps.stats[STAT_HOLDABLE_ITEM];
''' + SAN + '''
        if (value ) {''')
edit('cgame/cg_draw.c', '''	value = cg.snap->ps.stats[STAT_PERSISTANT_POWERUP];
	if (value) {''', '''	value = cg.snap->ps.stats[STAT_PERSISTANT_POWERUP];
''' + SAN + '''	if (value) {''')
edit('cgame/cg_ents.c', '''	if ( es->modelindex >= bg_numItems ) {
		CG_Error( "Bad item index %i on entity", es->modelindex );
	}''', '''	if ( es->modelindex < 0 || es->modelindex >= bg_numItems ) {
		return;	// OpenArena VR: item from server game code we do not know (was a fatal CG_Error)
	}''')

# a pure server reorders the search path to its own pak order, which left pakQ3Q last: OpenArena's
# pak6-patch088.pk3 (desktop GLSL for renderer_oa) then won -> "Couldn't compile shader". Keep it first.
edit('qcommon/files.c', '''				p_insert_index = &s->next;
				break; // iterate to next server pack
			}
			p_previous = &s->next;
		}
	}
}''', '''				p_insert_index = &s->next;
				break; // iterate to next server pack
			}
			p_previous = &s->next;
		}
	}

	// OpenArena VR: the VR pak must stay in front of everything (its GLSL overrides OA's desktop GLSL)
	for ( p_previous = &fs_searchpaths; (s = *p_previous) != NULL; p_previous = &s->next ) {
		if ( s->pack && !Q_stricmp( s->pack->pakBasename, "pakQ3Q" ) ) {
			*p_previous = s->next;
			s->next = fs_searchpaths;
			fs_searchpaths = s;
			break;
		}
	}
}''')

# pure servers expect the checksums of the paks holding vm/cgame.qvm and vm/ui.qvm first in "cp".
# Our cgame/ui are native libraries, so those .qvm files are never opened -> "Unpure client
# detected". Open them once (this sets FS_CGAME_REF / FS_UI_REF on the right pure pak), like a
# QVM client would have.
edit('qcommon/files.c', '''const char *FS_ReferencedPakPureChecksums( void ) {
	static char	info[BIG_INFO_STRING];
	searchpath_t	*search;
	int nFlags, numPaks, checksum;

	info[0] = 0;
''', '''const char *FS_ReferencedPakPureChecksums( void ) {
	static char	info[BIG_INFO_STRING];
	searchpath_t	*search;
	int nFlags, numPaks, checksum;

	// OpenArena VR: reference the QVM paks as a QVM client would (see apply_online.py)
	if ( fs_numServerPaks ) {
		fileHandle_t vmf;
		if ( FS_FOpenFileRead( "vm/cgame.qvm", &vmf, qfalse ) >= 0 && vmf ) FS_FCloseFile( vmf );
		if ( FS_FOpenFileRead( "vm/ui.qvm", &vmf, qfalse ) >= 0 && vmf ) FS_FCloseFile( vmf );
	}

	info[0] = 0;
''')

# OpenArena 0.8.8 servers ("ioq3+oa 1.36_SVN1910M") make a NEW challenge for every getchallenge.
# We resend getchallenge while waiting, keep the first answer and ignore the rest as "unwanted",
# then connect with a challenge the server already replaced -> "No or bad challenge for your
# address." forever. While still challenging, take the newest challenge from our server instead.
edit('client/cl_main.c', '''		if (clc.state != CA_CONNECTING)
		{
			Com_DPrintf("Unwanted challenge response received. Ignored.\\n");
			return;
		}''', '''		if (clc.state != CA_CONNECTING)
		{
			// OpenArena VR: see apply_online.py
			if ( clc.state == CA_CHALLENGING && NET_CompareAdr( from, clc.serverAddress ) && *Cmd_Argv(1) ) {
				clc.challenge = atoi( Cmd_Argv(1) );
				clc.connectTime = -99999;	// resend connect with it right away
				Com_DPrintf( "challengeResponse (newer): %d\\n", clc.challenge );
				return;
			}
			Com_DPrintf("Unwanted challenge response received. Ignored.\\n");
			return;
		}''')
