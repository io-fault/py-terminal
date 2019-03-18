"""
# Terminal input events data types.

# [ Engineering ]
# Currently, this does not properly parse CSI and relies heavily on timing.
# This may not properly interpret events in an asynchronous I/O context
# where the edge of a buffer may conceal an escape sequence or meta-escaped character event.
"""
import functools

from . import core

Character = core.Event
Modifiers = core.Modifiers
Point = core.Point

Char = Character
Mod = Modifiers.construct
Zero = Mod(0)
Meta = Mod(meta=True)

def ictlchr(ctlid:str, offset=ord('A')-1) -> int:
	"""
	# Transform a `'control'` &Character.identity into its literal form.

	# When a control character is transformed into a &core.Event, its
	# identity is processed into a lowercase english alphabet character
	# consistent with the usual visualization.

	# This function inverts the process for applications needing the actual
	# target control character. Notably, relying on the &Character.string
	# is inappropriate in the case where the character was escaped and the
	# event is qualified with some modifiers.
	"""
	if ctlid in {'?', ' '}:
		return '\x7f' if ctlid == '?' else ' '

	return chr(ord(ctlid.upper()) - offset)

# Escape codes mapped to constructed Key presses.
escape_codes = {
	# XXX: This &escape_codes table will be reduced once a proper parser is implemented.

	# xterm focus events
	'[I': Char(('focus', '[I', 'in', 0)),
	'[O': Char(('focus', '[O', 'out', 0)),

	# Special case for solo brackets. (CSI)
	'[[': Char(('literal', '\x1b[[', '[', Meta)),

	# XXX: This should probably trigger an exception or not occur at all.
	# Likely, if this is seen, it means there's more data to come to complete the sequence.
	# xterm will send this with meta escape.
	'[': Char(('literal', '\x1b[', '[', Meta)),

	# Tabs
	'[Z': Char(('control', '\x1b[Z', 'i', Mod(shift=True))),
	'\x19': Char(('control', '\x1b\x19', 'i', Mod(shift=True, meta=True))),

	'OM': Char(('control', '\x1bOM', 'enter', Zero)),

	'[2~': Char(('delta', '\x1b[2~', 'insert', Zero)),
	'[3~': Char(('delta', '\x1b[3~', 'delete', Zero)),

	'[A': Char(('navigation', '\x1b[A', 'up', Zero)),
	'[B': Char(('navigation', '\x1b[B', 'down', Zero)),
	'[C': Char(('navigation', '\x1b[C', 'right', Zero)),
	'[D': Char(('navigation', '\x1b[D', 'left', Zero)),

	'OA': Char(('navigation', '\x1bOA', 'up', Zero)),
	'OB': Char(('navigation', '\x1bOB', 'down', Zero)),
	'OC': Char(('navigation', '\x1bOC', 'right', Zero)),
	'OD': Char(('navigation', '\x1bOD', 'left', Zero)),

	'[H': Char(('navigation', '\x1b[H', 'home', Zero)),
	'[F': Char(('navigation', '\x1b[F', 'end', Zero)),
	'[1~': Char(('navigation', '\x1b[1~', 'home', Zero)),
	'[4~': Char(('navigation', '\x1b[4~', 'end', Zero)),
	'[5~': Char(('navigation', '\x1b[5~', 'pageup', Zero)),
	'[6~': Char(('navigation', '\x1b[6~', 'pagedown', Zero)),

	# VT100 compat.
	# This potentially conflicts with meta escapes, but timing
	# should usually manage to resolve the ambiguity.
	'OP': Char(('function', '\x1bOP', 1, Zero)),
	'OQ': Char(('function', '\x1bOQ', 2, Zero)),
	'OR': Char(('function', '\x1bOR', 3, Zero)),
	'OS': Char(('function', '\x1bOS', 4, Zero)),

	'[11~': Char(('function', '\x1b[11~', 1, Zero)),
	'[12~': Char(('function', '\x1b[12~', 2, Zero)),
	'[13~': Char(('function', '\x1b[13~', 3, Zero)),
	'[14~': Char(('function', '\x1b[14~', 4, Zero)),
	'[15~': Char(('function', '\x1b[15~', 5, Zero)),
	'[17~': Char(('function', '\x1b[17~', 6, Zero)),
	'[18~': Char(('function', '\x1b[18~', 7, Zero)),
	'[19~': Char(('function', '\x1b[19~', 8, Zero)),
	'[20~': Char(('function', '\x1b[20~', 9, Zero)),
	'[21~': Char(('function', '\x1b[21~', 10, Zero)),
	'[23~': Char(('function', '\x1b[23~', 11, Zero)),
	'[24~': Char(('function', '\x1b[24~', 12, Zero)),

	'[29~': Char(('function', '\x1b[29~', 'applications', Zero)),
	'[34~': Char(('function', '\x1b[34~', 'windows', Zero)),

	'[200~': Char(('paste', '\x1b[200~', 'start', Zero)),
	'[201~': Char(('paste', '\x1b[201~', 'stop', Zero)),
}

# build out the codes according to the available patterns
def build_event_table():
	# XXX: Rework this into a proper CSI parser.
	modifier_sequence = tuple(zip((2,3,5,6,7), (
		Mod(shift=True),
		Mod(meta=True),
		Mod(control=True),
		Mod(shift=True, control=True),
		Mod(control=True, meta=True),
	)))

	# insert and delete
	for formatting, ident in (('\x1b[2;%d~', 'insert'), ('\x1b[3;%d~', 'delete')):
		escape_codes.update([
			(x.string[1:], x) for x in (
				Char(('delta', formatting %(n,), ident, mods))
				for n, mods in modifier_sequence
			)
		])

	# page up and page down
	formatting = '\x1b[%s;%d~'
	for key in (('5', 'page-up'), ('6', 'page-down'), ('1', 'home'), ('4', 'end')):
		num, name = key
		escape_codes.update([
			(x.string[1:], x) for x in (
				Char(('navigation', formatting % (num, n), key[1], mods))
				for n, mods in modifier_sequence
			)
		])

	# arrows and home and end
	formatting = '\x1b[1;%d%s'
	for key in (('A', 'up'), ('B', 'down'), ('C', 'right'), ('D', 'left'), ('H', 'home'), ('F', 'end')):
		kid, name = key
		escape_codes.update([
			(x.string[1:], x) for x in (
				Char(('navigation', formatting % (n, kid), key[1], mods))
				for n, mods in modifier_sequence
			)
		])

	# modern function keys
	formatting = '\x1b[%d~%d'
	for kid, fn in zip((11, 12, 13, 14, 15, 17, 18, 19, 20, 21, 23, 24), range(1, 13)):
		escape_codes.update([
			(x.string[1:], x) for x in (
				Char(('function', formatting % (kid, n), fn, mods))
				for n, mods in modifier_sequence
			)
		])

	# media keys
	formatting = '\x1b[%d;%d~'
	for kid, fn in zip((15, 17, 18, 19, 20, 21, 23, 24), range(5, 12)):
		escape_codes.update([
			(x.string[1:], x) for x in (
				Char(('function', formatting % (kid, n), fn, mods))
				for n, mods in modifier_sequence
			)
		])

	formatting = '\x1b[%d;%d~'
	for name, kid in zip(('applications', 'windows'), (29, 34)):
		escape_codes.update([
			(x.string[1:], x) for x in (
				Char(('function', formatting % (kid, n), name, mods))
				for n, mods in modifier_sequence
			)
		])

# keep it in a function to avoid littering on the module locals
build_event_table()
del build_event_table

# Override any of the control characters with the common representation.
literal_overrides = {
	'\x7f': '?',
	' ': ' ',
}

@functools.lru_cache(32)
def char(k, source=None, modifiers=Zero, Character=Character, Space=ord(' '), ControlOffset=ord('A')-1):
	ok = k
	k = literal_overrides.get(ok, k)

	if source is None:
		source = ok

	i = ord(k)
	if i < Space:
		return Character(('control', source, chr(ControlOffset+i).lower(), modifiers))
	elif ok in literal_overrides:
		return Character(('control', source, k, modifiers))

	return Character(('literal', source, k, modifiers))

@functools.lru_cache(16)
def point(x, y, Type=Point):
	"""
	# Build a &core.Point for describing mount events.
	"""
	return Type((x,y))

@functools.lru_cache(8)
def interpret_modifiers(packed, Create=Modifiers.construct):
	return Create(
		shift=(packed & 4),
		meta=(packed & 8),
		control=(packed & 16)
	)

@functools.lru_cache(16)
def mouse(string):
	"""
	# Construct a raw mouse event from the given string.
	# &mouse separates scroll, click, and drag events.
	"""

	event = 'mouse'
	data = string[2:-1]
	mbutton, mx, my = map(int, data.split(';'))

	if mbutton < 32:
		event = 'mouse'
		if string[-1] == 'M':
			act = 1 # press
		elif string[-1] == 'm':
			act = -1 # release
		offset = 0
	elif mbutton < 64:
		# drag
		offset = 32
		act = 0
		event = 'motion'
	else:
		event = 'scroll'
		# Scroll Events.
		offset = 64

		# Evens scroll up, odds down.
		if mbutton % 2:
			act = 1
			offset += 1
		else:
			act = -1

	mods = mbutton - offset
	return Character((
		event, string,
		(point(mx, my), act, mods & 0b11),
		interpret_modifiers(mods),
	))

def cursor_report(string):
	"""
	# Parse a cursor position report.
	"""
	position = tuple(map(int, string[1:-1].split(';')))
	return Character(('report', string, position, 0))

def escaped_characters(string, Character=Character, Zero=Zero, modifiers=Meta):
	"""
	# Resolve the Key instance for the given string instance.
	"""

	if string in escape_codes:
		yield escape_codes[string]
	else:
		if string[:1] == '[':
			if string[1:2] == '<':
				# mouse event
				yield mouse(string)
			elif string[-1:] == 'R':
				yield cursor_report(string)
			elif string[:5] in {'[200~', '[201~'}:
				yield escape_codes[string[:5]]
				yield from map(char, string[5:])
		else:
			start = string[:1]
			yield char(start, source='\x1b'+start, modifiers=modifiers)
			yield from map(char, string[1:])

def construct_character_events(data:str, escape='\x1b', iter=iter, next=next):
	"""
	# Resolve the key events for the binary input read from a terminal.
	"""

	first = data.find(escape)

	if first == -1:
		# No escapes, just iterate over the characters.
		# mapping control characters to their prebuilt Character() instances.
		return list(map(char, data))
	elif data:
		# Escape Code to map control characters.
		events = []

		if first > 0:
			events.extend(map(char, data[:first]))

		escapes = iter(data[first+1:].split(escape))
		# XXX: Does not process CSI properly.
		for x in escapes:
			if not x:
				# Single escape.
				events.append(char(escape))
			else:
				events.extend(escaped_characters(x))
		return events
	else:
		# empty keys
		return []

del Char, Mod, Zero, Meta
