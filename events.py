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

# Escape codes mapped to constructed Key presses.
escape_codes = {
	'': Char(('control', '', 'escape', Zero)),
	' ': Char(('control', ' ', 'space', Mod(meta=True))),
	'\t': Char(('control', '\t', 'tab', Mod(meta=True))),
	'[Z': Char(('control', '[Z', 'tab', Mod(shift=True))),
	'[Z': Char(('control', '[Z', 'tab', Mod(shift=True, meta=True))),
	'OM': Char(('control', 'OM', 'enter', Zero)),

	'\x7f': Char(('delta', '\x7f', 'delete', Mod(meta=True))),
	'\b': Char(('delta', '\b', 'backspace', Mod(meta=True))),

	'[2~': Char(('delta', '[2~', 'insert', Mod(meta=False))),
	'[3~': Char(('delta', '[3~', 'delete', Mod(meta=False))),

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

control_characters = dict(
	# Some of these get overridden with their
	# common representation. (newline, backspace, etc)
	zip(
		(
			'', '',
			'', '',
			'', '',
			'', '',
			'\t', '\r',
			'', '',
			'\n', '',
			'', '',
			'\x11', '',
			'\x13', '',
			'', '',
			'', '',
			'', '',
		),
		(
			Char(('control', x, x, Mod(control=True)))
			for x in map(chr, range(ord('a'), ord('z')+1))
		)
	)
)

# Override any of the control characters with the common representation.
control_characters.update({
	'\x00': Char(('control', '\x00', 'nul', Mod(control=False))),

	'\x7f': Char(('delta', '\x7f', 'delete', Mod(control=False))),
	'\b': Char(('delta', '\b', 'backspace', Mod(control=False))),

	' ': Char(('control', ' ', 'space', Mod(control=False))),

	'\t': Char(('control', '\t', 'tab', Mod(control=False))),
	'\r': Char(('control', '\r', 'return', Mod(control=False))),
	'\n': Char(('control', '\n', 'newline', Mod(control=False))),

	'': Char(('control', '', 'bracket', Mod(control=True))),
	'': Char(('control', '', 'backslash', Mod(control=True))),
	'': Char(('control', '', 'underscore', Mod(control=True))),
})

@functools.lru_cache(32)
def literal(k, Character=Character, Zero=Zero):
	return Character(('literal', k, k, Zero))

def literal_events(data):
	"""
	# Resolve events for keys without escapes.
	"""
	return tuple(
		control_characters[x]
		if x in control_characters else literal(x)
		for x in data
	)

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

def escaped_characters(string, Character=Character, Zero=Zero):
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
			return Character(('escaped', string, string, Zero))

def construct_character_events(data, escape = '\x1b'):
	"""
	# Resolve the key events for the binary input read from a terminal.
	"""
	# Some keys are represented literally and some
	# use escape encoding, "\x1b[...".

	first = data.find(escape)

	if first == -1:
		# No escapes, just iterate over the characters.
		# mapping control characters to their prebuilt Character() instances.
		return literal_events(data)
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

del Char, Mod
