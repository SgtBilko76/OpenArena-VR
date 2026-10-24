#!/usr/bin/env python3
"""VR 3D crosshair for OpenArena (re-runnable).

OpenArena's gfx/2d/crosshair* shaders (rgbGen identity) draw nothing as a 3D sprite in the GLES3
renderer (verified headless: a balloon sprite and a white square show at the aim point, OA's
crosshair shaders don't, with or without RF_DEPTHHACK). Like the Urban Terror port, add VR copies
with rgbGen/alphaGen entity in pakQ3Q's vr.shader and colour them from the game's crosshair
colour settings."""
import pathlib
REPO = pathlib.Path(__file__).resolve().parents[2]
CODE = REPO / 'android/app/src/main/cpp/code'
SHADER = REPO / 'android/app/src/main/pakQ3Q/scripts/vr.shader'

def edit(p, old, new, count=1):
    t = p.read_text()
    if new in t and (old not in t or new not in old): print(f'  = {p.name}: already'); return
    assert t.count(old) == count, f'{p}: {t.count(old)}x {old[:80]!r}'
    p.write_text(t.replace(old, new)); print(f'  + {p.name}: {old.strip().splitlines()[0][:50]!r}')

# --- shaders ----------------------------------------------------------------------------------
t = SHADER.read_text()
if 'sprites/vr/crosshaira' not in t:
    t += '\n// OpenArena VR: 3D crosshairs (OpenArena crosshairs a-j), coloured per entity\n'
    for c in 'abcdefghij':
        t += f'''sprites/vr/crosshair{c}
{{
	nopicmip
	cull disable
	{{
		map gfx/2d/crosshair{c}.tga
		blendfunc GL_SRC_ALPHA GL_ONE_MINUS_SRC_ALPHA
		rgbGen entity
		alphaGen entity
	}}
}}
'''
    SHADER.write_text(t); print('  + vr.shader: sprites/vr/crosshaira..j')
else:
    print('  = vr.shader: already')

# --- cgame ------------------------------------------------------------------------------------
edit(CODE / 'cgame/cg_local.h', '\tqhandle_t\tcrosshairShader[NUM_CROSSHAIRS];',
     '\tqhandle_t\tcrosshairShader[NUM_CROSSHAIRS];\n\tqhandle_t\tvrCrosshairShader[10];\t// OpenArena VR: 3D crosshair sprites (vr.shader)')
edit(CODE / 'cgame/cg_main.c', '''			cgs.media.crosshairShader[i] = trap_R_RegisterShader(va("gfx/2d/crosshair%02d", i - 10));
	}
''', '''			cgs.media.crosshairShader[i] = trap_R_RegisterShader(va("gfx/2d/crosshair%02d", i - 10));
	}
	for (i = 0; i < 10; i++) {
		cgs.media.vrCrosshairShader[i] = trap_R_RegisterShader(va("sprites/vr/crosshair%c", 'a' + i));
	}
''')

edit(CODE / 'cgame/cg_draw.c', '''	ent.customShader = hShader;

''', '''	ent.customShader = hShader;

	// OpenArena VR: OA's crosshair shaders don't render as 3D sprites; use the VR copies, coloured
	// like the 2D crosshair (health colour or cg_crosshairColor*)
	if (cgs.media.vrCrosshairShader[ca % 10]) {
		vec4_t col;
		ent.customShader = cgs.media.vrCrosshairShader[ca % 10];
		if (cg_crosshairHealth.integer) {
			CG_ColorForHealth(col);
		} else {
			col[0] = cg_crosshairColorRed.value;
			col[1] = cg_crosshairColorGreen.value;
			col[2] = cg_crosshairColorBlue.value;
		}
		ent.shaderRGBA[0] = 255 * Com_Clamp(0, 1, col[0]);
		ent.shaderRGBA[1] = 255 * Com_Clamp(0, 1, col[1]);
		ent.shaderRGBA[2] = 255 * Com_Clamp(0, 1, col[2]);
		ent.shaderRGBA[3] = 255;
	}

''')
