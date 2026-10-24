#!/usr/bin/env python3
"""VR virtual keyboard for q3_ui text fields + editable player name (re-runnable)."""
import pathlib, re
REPO = pathlib.Path(__file__).resolve().parents[2]
CODE = REPO / 'android/app/src/main/cpp/code'

def edit(rel, old, new, count=1):
    p = CODE / rel if not rel.startswith('/') else pathlib.Path(rel)
    t = p.read_text(errors='surrogateescape')
    if new in t and (old not in t or new not in old): print(f'  = {p.name}: already'); return
    assert t.count(old) == count, f'{p}: {t.count(old)}x {old[:80]!r}'
    p.write_text(t.replace(old, new), errors='surrogateescape'); print(f'  + {p.name}: {old.strip().splitlines()[0][:50]!r}')

edit('q3_ui/ui_local.h', 'extern void\t\t\tMenu_SetCursorToItem( menuframework_s *m, void* ptr );',
     '''extern void			Menu_SetCursorToItem( menuframework_s *m, void* ptr );

// ui_vrkeyboard.c
extern qboolean		UI_VRKeyboard_Key( int key, int down );
extern qboolean		UI_VRKeyboard_PointerInside( void );
extern void			UI_VRKeyboard_Draw( void );''')

edit('q3_ui/ui_atoms.c', '''	if (!uis.activemenu) {
		return;
	}

	if (!down) {
		return;
	}

	if (uis.activemenu->key)''', '''	if (!uis.activemenu) {
		return;
	}

	if (UI_VRKeyboard_Key(key, down)) {
		return;	// a click on the VR keyboard, or on a text field that opened it
	}

	if (!down) {
		return;
	}

	if (uis.activemenu->key)''')

edit('q3_ui/ui_atoms.c', '''	else if (uis.cursory > SCREEN_HEIGHT+16)
		uis.cursory = SCREEN_HEIGHT+16;

	// region test the active menu items''', '''	else if (uis.cursory > SCREEN_HEIGHT+16)
		uis.cursory = SCREEN_HEIGHT+16;

	// the VR keyboard covers the menu items under it
	if (UI_VRKeyboard_PointerInside())
		return;

	// region test the active menu items''')

edit('q3_ui/ui_atoms.c', '''	// draw cursor
	UI_SetColor( NULL );
	UI_DrawHandlePic( uis.cursorx-16, uis.cursory-16, 32, 32, uis.cursor);''', '''	UI_VRKeyboard_Draw();

	// draw cursor
	UI_SetColor( NULL );
	UI_DrawHandlePic( uis.cursorx-16, uis.cursory-16, 32, 32, uis.cursor);''')

# player name: editable again (Quake3Quest had disabled it and pointed at its companion app)
COMP = '\tUI_DrawString( 320, 460, "To change player name use the companion app.", UI_CENTER|UI_SMALLFONT, text_color_normal );\n'
for f in ('q3_ui/ui_playersettings.c', 'q3_ui/ui_playermodel.c'):
    p = CODE / f; t = p.read_text()
    if COMP in t: p.write_text(t.replace(COMP, '')); print(f'  - {f}: companion-app line')
edit('q3_ui/ui_playersettings.c', '''	//s_playersettings.name.generic.type			= MTYPE_FIELD;
	//s_playersettings.name.generic.flags			= QMF_NODEFAULTINIT;
	s_playersettings.name.generic.type			= MTYPE_BTEXT;
	s_playersettings.name.generic.flags			= QMF_INACTIVE;''', '''	// OpenArena VR: editable again; clicking it opens the VR keyboard (ui_vrkeyboard.c)
	s_playersettings.name.generic.type			= MTYPE_FIELD;
	s_playersettings.name.generic.flags			= QMF_NODEFAULTINIT;''')
# restore focus highlight + caret in the name draw function (lines Q3Q commented out)
p = CODE / 'q3_ui/ui_playersettings.c'; t = p.read_text()
s = t.index('static void PlayerSettings_DrawName'); e = t.index('\n}\n', s)
body = t[s:e]
nb = body
for a, b in (('\t//qboolean\t\tfocus;', '\tqboolean\t\tfocus;'),
             ('\t//focus = (f->generic.parent->cursor', '\tfocus = (f->generic.parent->cursor'),
             ('\t//if( focus ) {\n\t//\tstyle |= UI_PULSE;\n\t//\tcolor = text_color_highlight;\n\t//}\n',
              '\tif( focus ) {\n\t\tstyle |= UI_PULSE;\n\t\tcolor = text_color_highlight;\n\t}\n'),
             ('\t\t//if ( !focus && Q_IsColorString( txt ) ) {\n\t\tif ( Q_IsColorString( txt ) ) {',
              '\t\tif ( !focus && Q_IsColorString( txt ) ) {'),
             ('''	//if( focus ) {
	//	if ( trap_Key_GetOverstrikeMode() ) {
	//		c = 11;
	//	} else {
	//		c = 10;
	//	}
	//
	//	style &= ~UI_PULSE;
	//	style |= UI_BLINK;
	//
	//	UI_DrawChar( basex + f->field.cursor * SMALLCHAR_WIDTH, y, c, style, color_white );
	//}''', '''	if( focus ) {
		if ( trap_Key_GetOverstrikeMode() ) {
			c = 11;
		} else {
			c = 10;
		}

		style &= ~UI_PULSE;
		style |= UI_BLINK;

		UI_DrawChar( basex + f->field.cursor * SMALLCHAR_WIDTH, y, c, style, color_white );
	}''')):
    if a in nb: nb = nb.replace(a, b)
if nb != body:
    p.write_text(t[:s] + nb + t[e:]); print('  + ui_playersettings.c: name focus/caret drawing restored')
else:
    print('  = ui_playersettings.c: name drawing already restored')
assert 'if( focus ) {\n\t\tif ( trap_Key_GetOverstrikeMode() )' in p.read_text()

# build: add the module to the q3_ui object list
mk = REPO / 'Makefile'; t = mk.read_text()
if 'ui/ui_vrkeyboard.o' not in t:
    t = t.replace('  $(B)/$(BASEGAME)/ui/ui_comfort.o \\\n', '  $(B)/$(BASEGAME)/ui/ui_comfort.o \\\n  $(B)/$(BASEGAME)/ui/ui_vrkeyboard.o \\\n', 1)
    assert 'ui/ui_vrkeyboard.o' in t; mk.write_text(t); print('  + Makefile: ui_vrkeyboard.o')
