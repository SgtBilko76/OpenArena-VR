/*
===========================================================================
OpenArena VR: virtual keyboard for menu text fields.

Quest/PICO have no keyboard. Clicking a text field with the laser pointer (player name, server
address, host name, ...) opens this keyboard over the menu; its keys type straight into that
field. It closes on Done, on a click outside it, or when the menu changes.

GPL v2 or later, like the rest of the game code.
===========================================================================
*/
#include "ui_local.h"

#define KBD_X		20.0f
#define KBD_W		600.0f
#define KBD_ROWH	36.0f
#define KBD_GAP		3.0f
#define KBD_ROWS	5
#define KBD_H		( KBD_ROWS * ( KBD_ROWH + KBD_GAP ) - KBD_GAP )

enum { KK_CHAR, KK_SHIFT, KK_SPACE, KK_CLEAR, KK_BACK, KK_DONE };

static const char *kbdRows[4][2] = {
	{ "1234567890-", "!@#$%^&*()_" },
	{ "qwertyuiop", "QWERTYUIOP" },
	{ "asdfghjkl", "ASDFGHJKL" },
	{ "zxcvbnm.,", "ZXCVBNM?:" },
};

static menufield_s	*kbdField;		// field being edited, NULL = keyboard closed
static float		kbdY;			// top of the keyboard (below or above the field)
static qboolean		kbdShift;		// one-shot shift, on when the keyboard opens
static int			kbdFlashKey = -1, kbdFlashTime;

static qboolean UI_VRKeyboard_KeyRect( int i, int *type, char *ch, float *x, float *y, float *w, float *h ) {
	int row, n = 0;
	float unit = ( KBD_W - 10 * KBD_GAP ) / 11.0f;

	for ( row = 0; row < 4; row++ ) {
		int len = strlen( kbdRows[row][0] );
		if ( i < n + len ) {
			int col = i - n;
			float rowW = len * unit + ( len - 1 ) * KBD_GAP;
			*type = KK_CHAR;
			*ch = kbdRows[row][kbdShift ? 1 : 0][col];
			*x = KBD_X + ( KBD_W - rowW ) * 0.5f + col * ( unit + KBD_GAP );
			*y = kbdY + row * ( KBD_ROWH + KBD_GAP );
			*w = unit;
			*h = KBD_ROWH;
			return qtrue;
		}
		n += len;
	}
	{	// bottom row: Shift 2 | Space 4 | Clear 2 | Del 2 | Done 2 (units)
		static const int types[5] = { KK_SHIFT, KK_SPACE, KK_CLEAR, KK_BACK, KK_DONE };
		static const float units[5] = { 2, 4, 2, 2, 2 };
		int j = i - n, c;
		float xx = KBD_X, avail = KBD_W - 4 * KBD_GAP;
		if ( j < 0 || j > 4 ) {
			return qfalse;
		}
		for ( c = 0; c < j; c++ ) {
			xx += units[c] / 12.0f * avail + KBD_GAP;
		}
		*type = types[j];
		*ch = ' ';
		*x = xx;
		*y = kbdY + 4 * ( KBD_ROWH + KBD_GAP );
		*w = units[j] / 12.0f * avail;
		*h = KBD_ROWH;
		return qtrue;
	}
}

static int UI_VRKeyboard_Hit( void ) {
	int i, type;
	char ch;
	float x, y, w, h;

	for ( i = 0; UI_VRKeyboard_KeyRect( i, &type, &ch, &x, &y, &w, &h ); i++ ) {
		if ( uis.cursorx >= x - 1 && uis.cursorx < x + w + 1 &&
				uis.cursory >= y - 1 && uis.cursory < y + h + 1 ) {
			return i;
		}
	}
	return -1;
}

static void UI_VRKeyboard_Close( void ) {
	kbdField = NULL;
}

static void UI_VRKeyboard_Open( menufield_s *f ) {
	kbdField = f;
	kbdShift = qtrue;
	// below the field if it sits in the upper half, otherwise above it
	kbdY = ( f->generic.bottom < SCREEN_HEIGHT - KBD_H - 16 ) ? SCREEN_HEIGHT - KBD_H - 8 : 8;
	f->field.cursor = strlen( f->field.buffer );
}

qboolean UI_VRKeyboard_Open_p( void ) {
	if ( kbdField && kbdField->generic.parent != uis.activemenu ) {
		UI_VRKeyboard_Close();
	}
	return kbdField != NULL;
}

// qtrue while the pointer is over the open keyboard: the menu then ignores the pointer
qboolean UI_VRKeyboard_PointerInside( void ) {
	if ( !UI_VRKeyboard_Open_p() ) {
		return qfalse;
	}
	return uis.cursorx >= KBD_X - 8 && uis.cursorx <= KBD_X + KBD_W + 8 &&
		uis.cursory >= kbdY - 8 && uis.cursory <= kbdY + KBD_H + 8;
}

static void UI_VRKeyboard_Press( int i ) {
	int type;
	char ch;
	float x, y, w, h;
	mfield_t *field = &kbdField->field;

	if ( !UI_VRKeyboard_KeyRect( i, &type, &ch, &x, &y, &w, &h ) ) {
		return;
	}
	kbdFlashKey = i;
	kbdFlashTime = uis.realtime;
	trap_S_StartLocalSound( menu_move_sound, CHAN_LOCAL_SOUND );

	switch ( type ) {
	case KK_CHAR:
		MField_CharEvent( field, ch );
		kbdShift = qfalse;
		break;
	case KK_SPACE:
		MField_CharEvent( field, ' ' );
		break;
	case KK_SHIFT:
		kbdShift = !kbdShift;
		break;
	case KK_CLEAR:
		MField_Clear( field );
		kbdShift = qtrue;
		break;
	case KK_BACK:
		field->cursor = strlen( field->buffer );
		MField_CharEvent( field, 'h' - 'a' + 1 );	// ctrl-h = backspace
		break;
	case KK_DONE:
		UI_VRKeyboard_Close();
		break;
	}
	if ( kbdField && kbdField->generic.callback ) {
		kbdField->generic.callback( kbdField, QM_ACTIVATED );
	}
}

// Called first in UI_KeyEvent; qtrue = the key press was used by the keyboard.
qboolean UI_VRKeyboard_Key( int key, int down ) {
	menucommon_s *item;

	if ( !down || key != K_MOUSE1 || !uis.activemenu ) {
		return qfalse;
	}

	if ( UI_VRKeyboard_PointerInside() ) {
		int i = UI_VRKeyboard_Hit();
		if ( i >= 0 ) {
			UI_VRKeyboard_Press( i );
		}
		return qtrue;	// clicks in the gaps don't reach the menu either
	}

	item = (menucommon_s *)Menu_ItemAtCursor( uis.activemenu );
	if ( item && item->type == MTYPE_FIELD && !( item->flags & ( QMF_GRAYED | QMF_INACTIVE ) ) &&
			uis.cursorx >= item->left && uis.cursorx <= item->right &&
			uis.cursory >= item->top && uis.cursory <= item->bottom ) {
		UI_VRKeyboard_Open( (menufield_s *)item );
		return qtrue;
	}

	if ( kbdField ) {
		UI_VRKeyboard_Close();	// click elsewhere: close and let the menu handle it
	}
	return qfalse;
}

// Drawn after the menu, before the cursor.
void UI_VRKeyboard_Draw( void ) {
	static vec4_t panel = { 0.05f, 0.07f, 0.12f, 0.92f };
	static vec4_t keyCol = { 0.22f, 0.26f, 0.34f, 1.0f };
	static vec4_t keyHover = { 0.30f, 0.45f, 0.75f, 1.0f };
	static vec4_t keyFlash = { 0.95f, 0.65f, 0.20f, 1.0f };
	static vec4_t keyOn = { 0.20f, 0.55f, 0.35f, 1.0f };
	int i, type, hover;
	char ch;
	float x, y, w, h;

	if ( !UI_VRKeyboard_Open_p() ) {
		return;
	}
	// keep the edited field focused so it shows its caret
	if ( Menu_ItemAtCursor( uis.activemenu ) != kbdField ) {
		Menu_SetCursorToItem( uis.activemenu, kbdField );
	}

	hover = UI_VRKeyboard_Hit();
	UI_FillRect( KBD_X - 8, kbdY - 8, KBD_W + 16, KBD_H + 16, panel );
	for ( i = 0; UI_VRKeyboard_KeyRect( i, &type, &ch, &x, &y, &w, &h ); i++ ) {
		float *c = keyCol;
		const char *label;
		char buf[2];
		int style = UI_CENTER | UI_SMALLFONT;
		int th = SMALLCHAR_HEIGHT;

		if ( type == KK_SHIFT && kbdShift ) c = keyOn;
		if ( i == hover ) c = keyHover;
		if ( i == kbdFlashKey && uis.realtime - kbdFlashTime < 120 ) c = keyFlash;
		UI_FillRect( x, y, w, h, c );

		switch ( type ) {
		case KK_SHIFT: label = "Shift"; break;
		case KK_SPACE: label = "Space"; break;
		case KK_CLEAR: label = "Clear"; break;
		case KK_BACK: label = "<- Del"; break;
		case KK_DONE: label = "Done"; break;
		default:
			buf[0] = ch; buf[1] = 0; label = buf;
			style = UI_CENTER | UI_BIGFONT;
			th = BIGCHAR_HEIGHT;
			break;
		}
		UI_DrawString( (int)( x + w * 0.5f ), (int)( y + ( h - th ) * 0.5f ), label, style | UI_DROPSHADOW, color_white );
	}
	UI_SetColor( NULL );
}
