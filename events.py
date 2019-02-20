"""
# Terminal input events data types.
"""
import functools

from . import core
Character = core.Character
Modifiers = core.Modifiers

Char = core.Character
zero = core.Modifiers.construct()
Mod = core.Modifiers.construct

# Escape codes mapped to constructed Key presses.
escape_codes = {
	'': Char(('control', '', 'escape', zero)),
	' ': Char(('control', ' ', 'space', Mod(meta=True))),
	'\t': Char(('control', '\t', 'tab', Mod(meta=True))),
	'[Z': Char(('control', '[Z', 'tab', Mod(shift=True))),
	'[Z': Char(('control', '[Z', 'tab', Mod(shift=True, meta=True))),
	'OM': Char(('control', 'OM', 'enter', zero)),

	'\x7f': Char(('delta', '\x7f', 'delete', Mod(meta=True))),
	'\b': Char(('delta', '\b', 'backspace', Mod(meta=True))),

	'[2~': Char(('delta', '[2~', 'insert', Mod(meta=False))),
	'[3~': Char(('delta', '[3~', 'delete', Mod(meta=False))),

	'[A': Char(('navigation', '[A', 'up', zero)),
	'[B': Char(('navigation', '[B', 'down', zero)),
	'[C': Char(('navigation', '[C', 'right', zero)),
	'[D': Char(('navigation', '[D', 'left', zero)),

	'OA': Char(('navigation', 'OA', 'up', zero)),
	'OB': Char(('navigation', 'OB', 'down', zero)),
	'OC': Char(('navigation', 'OC', 'right', zero)),
	'OD': Char(('navigation', 'OD', 'left', zero)),

	'[H': Char(('navigation', '[H', 'home', zero)),
	'[F': Char(('navigation', '[F', 'end', zero)),
	'[1~': Char(('navigation', '[1~', 'home', zero)),
	'[4~': Char(('navigation', '[4~', 'end', zero)),
	'[5~': Char(('navigation', '[5~', 'pageup', zero)),
	'[6~': Char(('navigation', '[6~', 'pagedown', zero)),

	# VT100 compat
	'OP': Char(('function', 'OP', 1, zero)),
	'OQ': Char(('function', 'OQ', 2, zero)),
	'OR': Char(('function', 'OR', 3, zero)),
	'OS': Char(('function', 'OS', 4, zero)),

	'[11~': Char(('function', '[11~', 1, zero)),
	'[12~': Char(('function', '[12~', 2, zero)),
	'[13~': Char(('function', '[13~', 3, zero)),
	'[14~': Char(('function', '[14~', 4, zero)),
	'[15~': Char(('function', '[15~', 5, zero)),
	'[17~': Char(('function', '[17~', 6, zero)),
	'[18~': Char(('function', '[18~', 7, zero)),
	'[19~': Char(('function', '[19~', 8, zero)),
	'[20~': Char(('function', '[20~', 9, zero)),
	'[21~': Char(('function', '[21~', 10, zero)),
	'[23~': Char(('function', '[23~', 11, zero)),
	'[24~': Char(('function', '[24~', 12, zero)),
	'[29~': Char(('function', '[29~', 'applications', zero)),
	'[34~': Char(('function', '[34~', 'windows', zero)),

	'[200~': Char(('paste', '[200~', 'start', zero)),
	'[201~': Char(('paste', '[201~', 'stop', zero)),
}
del zero

# build out the codes according to the available patterns
def render_codes():
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
				core.Character(('delta', formatting %(n,), ident, mods))
				for n, mods in modifier_sequence
			)
		])

	# page up and page down
	formatting = '[%s;%d~'
	for key in (('5', 'page-up'), ('6', 'page-down'), ('1', 'home'), ('4', 'end')):
		num, name = key
		escape_codes.update([
			(x.string[1:], x) for x in (
				core.Character(('navigation', formatting % (num, n), key[1], mods))
				for n, mods in modifier_sequence
			)
		])

	# arrows and home and end
	formatting = '[1;%d%s'
	for key in (('A', 'up'), ('B', 'down'), ('C', 'right'), ('D', 'left'), ('H', 'home'), ('F', 'end')):
		kid, name = key
		escape_codes.update([
			(x.string[1:], x) for x in (
				core.Character(('navigation', formatting % (n, kid), key[1], mods))
				for n, mods in modifier_sequence
			)
		])

	# modern function keys
	formatting = '[%d~%d'
	for kid, fn in zip((11, 12, 13, 14, 15, 17, 18, 19, 20, 21, 23, 24), range(1, 13)):
		escape_codes.update([
			(x.string[1:], x) for x in (
				core.Character(('function', formatting % (kid, n), fn, mods))
				for n, mods in modifier_sequence
			)
		])

	# media keys
	formatting = '[%d;%d~'
	for kid, fn in zip((15, 17, 18, 19, 20, 21, 23, 24), range(5, 12)):
		escape_codes.update([
			(x.string[1:], x) for x in (
				core.Character(('function', formatting % (kid, n), fn, mods))
				for n, mods in modifier_sequence
			)
		])

	formatting = '[%d;%d~'
	for name, kid in zip(('applications', 'windows'), (29, 34)):
		escape_codes.update([
			(x.string[1:], x) for x in (
				core.Character(('function', formatting % (kid, n), name, mods))
				for n, mods in modifier_sequence
			)
		])

# keep it in a function to avoid littering on the module locals
render_codes()
del render_codes

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
del Char, Mod

@functools.lru_cache(32)
def literal(k, Character = core.Character,
		none = core.Modifiers(0),
		shift = core.Modifiers.construct(shift=True),
	):
	id = k.lower()
	return Character(('literal', k, id, none))

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
def point(x, y, Type=core.Point):
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

	return core.Character((
		event, string,
		(point(mx, my), act, mods & 0b11),
		core.Modifiers.construct(shift=shift, meta=meta, control=control),
	))

def escaped_events(string, Character = core.Character):
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
			return Character(('escaped', string, string.lower(), core.Modifiers(0)))

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
			events = [escaped_events(data[:first])]
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
				events.append(escaped_events((escape * escape_level) + x))
				escape_level = 0
		else:
			# handle the trailing escapes
			if escape_level:
				events.append(escaped_events(escape * escape_level))
		return events
	else:
		# empty keys
		return []
