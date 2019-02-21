"""
# Terminal input events data types.
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
	# consistent with the usual terminal visualization.

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
	' ': Char(('control', ' ', ' ', Meta)),
	'\x7f': Char(('control', '\x7f', '?', Meta)),
	'\t': Char(('control', '\t', 'i', Meta)),
	'[Z': Char(('control', '[Z', 'i', Mod(shift=True))),
	'\x19': Char(('control', '\x19', 'i', Mod(shift=True, meta=True))),

	'OM': Char(('control', 'OM', 'enter', Zero)),

	'[2~': Char(('delta', '[2~', 'insert', Zero)),
	'[3~': Char(('delta', '[3~', 'delete', Zero)),

	'[A': Char(('navigation', '[A', 'up', Zero)),
	'[B': Char(('navigation', '[B', 'down', Zero)),
	'[C': Char(('navigation', '[C', 'right', Zero)),
	'[D': Char(('navigation', '[D', 'left', Zero)),

	'OA': Char(('navigation', 'OA', 'up', Zero)),
	'OB': Char(('navigation', 'OB', 'down', Zero)),
	'OC': Char(('navigation', 'OC', 'right', Zero)),
	'OD': Char(('navigation', 'OD', 'left', Zero)),

	'[H': Char(('navigation', '[H', 'home', Zero)),
	'[F': Char(('navigation', '[F', 'end', Zero)),
	'[1~': Char(('navigation', '[1~', 'home', Zero)),
	'[4~': Char(('navigation', '[4~', 'end', Zero)),
	'[5~': Char(('navigation', '[5~', 'pageup', Zero)),
	'[6~': Char(('navigation', '[6~', 'pagedown', Zero)),

	# VT100 compat
	'OP': Char(('function', 'OP', 1, Zero)),
	'OQ': Char(('function', 'OQ', 2, Zero)),
	'OR': Char(('function', 'OR', 3, Zero)),
	'OS': Char(('function', 'OS', 4, Zero)),

	'[11~': Char(('function', '[11~', 1, Zero)),
	'[12~': Char(('function', '[12~', 2, Zero)),
	'[13~': Char(('function', '[13~', 3, Zero)),
	'[14~': Char(('function', '[14~', 4, Zero)),
	'[15~': Char(('function', '[15~', 5, Zero)),
	'[17~': Char(('function', '[17~', 6, Zero)),
	'[18~': Char(('function', '[18~', 7, Zero)),
	'[19~': Char(('function', '[19~', 8, Zero)),
	'[20~': Char(('function', '[20~', 9, Zero)),
	'[21~': Char(('function', '[21~', 10, Zero)),
	'[23~': Char(('function', '[23~', 11, Zero)),
	'[24~': Char(('function', '[24~', 12, Zero)),

	'[29~': Char(('function', '[29~', 'applications', Zero)),
	'[34~': Char(('function', '[34~', 'windows', Zero)),

	'[200~': Char(('paste', '[200~', 'start', Zero)),
	'[201~': Char(('paste', '[201~', 'stop', Zero)),
}

# build out the codes according to the available patterns
def build_event_table():
	modifier_sequence = tuple(zip((2,3,5,6,7), (
		Mod(shift=True),
		Mod(meta=True),
		Mod(control=True),
		Mod(shift=True, control=True),
		Mod(control=True, meta=True),
	)))

	# insert and delete
	for formatting, ident in (('[2;%d~', 'insert'), ('[3;%d~', 'delete')):
		escape_codes.update([
			(x.string[1:], x) for x in (
				Char(('delta', formatting %(n,), ident, mods))
				for n, mods in modifier_sequence
			)
		])

	# page up and page down
	formatting = '[%s;%d~'
	for key in (('5', 'page-up'), ('6', 'page-down'), ('1', 'home'), ('4', 'end')):
		num, name = key
		escape_codes.update([
			(x.string[1:], x) for x in (
				Char(('navigation', formatting % (num, n), key[1], mods))
				for n, mods in modifier_sequence
			)
		])

	# arrows and home and end
	formatting = '[1;%d%s'
	for key in (('A', 'up'), ('B', 'down'), ('C', 'right'), ('D', 'left'), ('H', 'home'), ('F', 'end')):
		kid, name = key
		escape_codes.update([
			(x.string[1:], x) for x in (
				Char(('navigation', formatting % (n, kid), key[1], mods))
				for n, mods in modifier_sequence
			)
		])

	# modern function keys
	formatting = '[%d~%d'
	for kid, fn in zip((11, 12, 13, 14, 15, 17, 18, 19, 20, 21, 23, 24), range(1, 13)):
		escape_codes.update([
			(x.string[1:], x) for x in (
				Char(('function', formatting % (kid, n), fn, mods))
				for n, mods in modifier_sequence
			)
		])

	# media keys
	formatting = '[%d;%d~'
	for kid, fn in zip((15, 17, 18, 19, 20, 21, 23, 24), range(5, 12)):
		escape_codes.update([
			(x.string[1:], x) for x in (
				Char(('function', formatting % (kid, n), fn, mods))
				for n, mods in modifier_sequence
			)
		])

	formatting = '[%d;%d~'
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
control_characters = {
	'\x7f': Char(('control', '\x7f', '?', Zero)),
	' ': Char(('control', ' ', ' ', Zero)),
}

@functools.lru_cache(32)
def char(k, modifiers=Zero, Character=Character, Space=ord(' '), ControlOffset=ord('A')-1):
	if k in control_characters:
		return control_characters[k]

	i = ord(k)
	if i < Space:
		return Character(('control', k, chr(ControlOffset+i).lower(), modifiers))

	return Character(('literal', k, k, modifiers))

@functools.lru_cache(16)
def point(x, y, Type=Point):
	"""
	# Build a &core.Point for describing mount events.
	"""
	return Type((x,y))

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
		event = 'drag'
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
	shift = mods & 4
	meta = mods & 8
	control = mods & 16

	return Character((
		event, string,
		(point(mx, my), act, mods & 0b11),
		Modifiers.construct(shift=shift, meta=meta, control=control),
	))

def escaped_characters(string, Character=Character, Zero=Zero, modifiers=Meta):
	"""
	# Resolve the Key instance for the given string instance.
	"""

	if string in escape_codes:
		return escape_codes[string]
	else:
		if string[:2] == '[<':
			# mouse event
			return mouse(string)
		else:
			return char(string, modifiers=modifiers)

def construct_character_events(data:str, escape='\x1b', iter=iter, next=next):
	"""
	# Resolve the key events for the binary input read from a terminal.
	"""

	first = data.find(escape)

	if first == -1:
		# No escapes, just iterate over the characters.
		# mapping control characters to their prebuilt Character() instances.
		return tuple(map(char, data))
	elif data:
		# Escape Code to map control characters.

		if first > 0:
			events = [escaped_characters(data[:first])]
		else:
			events = []

		# split on the escapes and map the sequences to KeyPressEvents
		escapes = iter(data[first:].split(escape))
		next(escapes) # skip initial empty sequence

		##
		# XXX
		# handle cases where multiple escapes are found.
		# there are some cases of ambiguity, but this seems to be ideal?
		escape_level = 0
		for x in escapes:
			# escape escape.
			if not x:
				escape_level += 1
			else:
				events.append(escaped_characters((escape * escape_level) + x))
				escape_level = 0
		else:
			# handle the trailing escapes
			if escape_level:
				events.append(escaped_characters(escape * escape_level))
		return events
	else:
		# empty keys
		return []

del Char, Mod, Zero, Meta
