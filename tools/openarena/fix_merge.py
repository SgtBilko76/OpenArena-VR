#!/usr/bin/env python3
"""Hand fixes on top of the automatic OA+Q3Q game-code merge (re-runnable)."""
import pathlib
CODE = pathlib.Path(__file__).resolve().parents[2] / 'android/app/src/main/cpp/code'

def edit(rel, old, new, count=1):
    p = CODE / rel; t = p.read_text(errors='surrogateescape')
    if new in t: print(f'  = {rel}: already'); return
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
