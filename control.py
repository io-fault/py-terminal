"""
# Rendering Context implementation.
"""

# Store Cursor Position / Restore Cursor Position
def scrolling_region(top, bottom):
	t = str(top).encode('utf-8')
	b = str(bottom).encode('utf-8')
	return b'\x1b[' + t + b';' + b + b'r'

_set_flag = b'h'
_reset_flag = b'l'

_state = {
	'cursor-location': (b'\x1b7', b'\x1b8'),
}

_options = {
	# rxvt
	'scroll-bottom-on-output': b'?1010',
	'scroll-bottom-on-input': b'?1011',

	'raw-buffer': b'?1049', # save cursor in normal and switch to alternate

	'mouse-drag': b'?1002',
	'mouse-motion': b'?1003',
	'mouse-events': b'?1006',

	'cursor-visible': b'?25',
	'line-wrapping': b'?7',
	'meta-escape': b'?1036',
	'bracket-paste-mode': b'?2004',

	# xterm
	'emulator-log': b'?46',
}

def _build(flag, fields, escape_sequence=b'\x1b['):
	for x in fields:
		code = _options[x]
		yield escape_sequence + code + flag

def optset(*fields):
	return b''.join(_build(_set_flag, fields))

def optrst(*fields):
	return b''.join(_build(_reset_flag, fields))
