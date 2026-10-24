#!/usr/bin/env python3
"""Hand fixes on top of the automatic OA+Q3Q game-code merge (re-runnable)."""
import pathlib
CODE = pathlib.Path(__file__).resolve().parents[2] / 'android/app/src/main/cpp/code'

def edit(rel, old, new, count=1):
    p = CODE / rel; t = p.read_text(errors='surrogateescape')
    if new in t and (old not in t or new not in old): print(f'  = {rel}: already'); return
    assert t.count(old) == count, f'{rel}: {t.count(old)}x {old[:80]!r}'
    p.write_text(t.replace(old, new), errors='surrogateescape'); print(f'  + {rel}: {old.strip()[:50]!r}')

# cg_event.c EV_RAILTRAIL: keep OA's unlagged structure, VR muzzle from the controller
edit('cgame/cg_event.c', '''				if (es->clientNum == cg.snap->ps.clientNum && !cg.renderingThirdPerson) {
		
		if(es->clientNum == cg.snap->ps.clientNum && !cg.renderingThirdPerson)
		{
			vec3_t angles;''', '''				if (es->clientNum == cg.snap->ps.clientNum && !cg.renderingThirdPerson) {
			vec3_t angles;''')

# cg_draw.c: OA draws the prox-mine warning in baseoa too; drop the stray #endif left by the merge
edit('cgame/cg_draw.c', '''			CG_DrawProxWarning();
#endif
''', '''			CG_DrawProxWarning();
''')

# cg_weapons.c weapon wheel: Q3Q tints the railgun with ioq3's c1RGBA/railFireTime, which OA lacks
edit('cgame/cg_weapons.c', '''					if( cg_entities[cg.predictedPlayerState.clientNum].pe.railFireTime + 1500 > cg.time ) {
						int scale = 255 * ( cg.time - cg_entities[cg.predictedPlayerState.clientNum].pe.railFireTime ) / 1500;
						ent.shaderRGBA[0] = ( ci->c1RGBA[0] * scale ) >> 8;
						ent.shaderRGBA[1] = ( ci->c1RGBA[1] * scale ) >> 8;
						ent.shaderRGBA[2] = ( ci->c1RGBA[2] * scale ) >> 8;
						ent.shaderRGBA[3] = 255;
					}
					else {
						Byte4Copy( ci->c1RGBA, ent.shaderRGBA );
					}''', '''					ent.shaderRGBA[0] = 255 * ci->color1[0];
					ent.shaderRGBA[1] = 255 * ci->color1[1];
					ent.shaderRGBA[2] = 255 * ci->color1[2];
					ent.shaderRGBA[3] = 255;''')

# g_main.c: Q3Q's VR serverinfo block clashes with OA's own serverinfo variable
edit('game/g_main.c', '''	char serverinfo[MAX_INFO_STRING];
	trap_GetServerinfo( serverinfo, sizeof( serverinfo ) );
	vr->no_crosshair = (strcasestr(serverinfo, "nocrosshair") != NULL || strcasestr(serverinfo, "no crosshair") != NULL);''',
'''	{
	char vrServerinfo[MAX_INFO_STRING];
	trap_GetServerinfo( vrServerinfo, sizeof( vrServerinfo ) );
	vr->no_crosshair = (strcasestr(vrServerinfo, "nocrosshair") != NULL || strcasestr(vrServerinfo, "no crosshair") != NULL);
	}''')

# cg_players.c: the head was added twice (Q3Q's spot + OA's spot after the chibi scale); keep OA's
# spot and Q3Q's "no head on your own first-person body" rule
edit('cgame/cg_players.c', '''	if (!firstPersonBody)
	{
		CG_AddRefEntityWithPowerups(&head, &cent->currentState, ci->team);
	}
''', '')
edit('cgame/cg_players.c', '''


	CG_AddRefEntityWithPowerups(&head, &cent->currentState, ci->team, qfalse);

	CG_BreathPuffs(cent, &head);''', '''
	if (!firstPersonBody) {
		CG_AddRefEntityWithPowerups(&head, &cent->currentState, ci->team, qfalse);
	}

	CG_BreathPuffs(cent, &head);''')

# OpenArena's renderer has eye-look fields on refEntity_t; the GLES3 renderer ignores them
edit('renderercommon/tr_types.h', '''	qboolean	invert;
} refEntity_t;''', '''	qboolean	invert;

	// OpenArena: eye position/look target for its eye-tracking player models (unused here)
	vec3_t		eyepos[2];
	vec3_t		eyelook;
} refEntity_t;''')

# cg_unlagged.c (OpenArena-only client hit prediction): the predicted rail beam starts at the VR
# gun like Q3Q's EV_RAILTRAIL path; the hit trace itself stays eye-based, matching the server
edit('cgame/cg_unlagged.c', '''			if(!cg.renderingThirdPerson) {
				if(cg_drawGun.integer == 2) {
					VectorMA(muzzlePoint, 8, cg.refdef.viewaxis[1], muzzlePoint);
				}
				else if(cg_drawGun.integer == 3) {
					VectorMA(muzzlePoint, 4, cg.refdef.viewaxis[1], muzzlePoint);
				}
			}
''', '''			if(!cg.renderingThirdPerson) {
				vec3_t vrAngles;
				CG_CalculateVRWeaponPosition(muzzlePoint, vrAngles);
			}
''')

# OAX b53.2 bug (upstream reverted the whole .info rework in #342): G_InitGame reads the SP map's
# bot list / frag limit / special rules from the arena files BEFORE G_InitBots loads them, so
# single player got no bots ("No arena info found for the map ..."). Load the arenas first.
edit('game/g_bot.c', '''static void G_LoadArenas( void ) {''', '''// OpenArena VR: not static, G_InitGame loads the arenas early (see g_main.c)
void G_LoadArenas( void ) {''')
edit('game/g_main.c', '''	MapInfoPrint(&mapinfo);
	MapInfoSaveIntoCvars(&mapinfo);
	if ( g_gametype.integer == GT_SINGLE_PLAYER || g_autoGameLimits.integer) {''', '''	MapInfoPrint(&mapinfo);
	MapInfoSaveIntoCvars(&mapinfo);
	if ( g_gametype.integer == GT_SINGLE_PLAYER || g_autoGameLimits.integer) {
		// OpenArena VR fix: the arena files must be loaded before the map's SP settings are read
		// from them (BG_InitMemory below resets the pool; G_InitBots loads them again after it)
		extern void G_LoadArenas( void );
		BG_InitMemory();
		G_LoadArenas();
	}
	if ( g_gametype.integer == GT_SINGLE_PLAYER || g_autoGameLimits.integer) {''')
