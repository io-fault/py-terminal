"""
# Terminal input events parser.
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

# Override any of the control characters with the common representation.
literal_overrides = {
	'\x7f': '?',
	' ': ' ',
}

def ictlchr(ctlid:str, offset=ord('A')-1) -> int:
	"""
	# Transform a `'control'` &Character.identity into its literal form.

	# When a control character is transformed into a &Character, its
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

@functools.lru_cache(32)
def print(k, source=None, modifiers=Zero, Character=Character, Space=ord(' '), ControlOffset=ord('A')-1):
	"""
	# Construct literal key press event.

	# Handles control and literals.
	"""
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

@functools.lru_cache(8)
def interpret_key_modifiers(packed, Create=Modifiers.construct):
	return Create(packed-1)

@functools.lru_cache(16)
def mouse(origin, terminator, parameters):
	"""
	# Construct a raw mouse event from the given string.
	# &mouse separates scroll, click, and drag events.
	"""
	mbutton, mx, my = parameters

	if mbutton < 32:
		type = 'mouse'
		if terminator == 'M':
			act = 1 # press
		elif terminator == 'm':
			act = -1 # release
		offset = 0
	elif mbutton < 64:
		# drag
		offset = 32
		act = 0
		type = 'motion'
	else:
		type = 'scroll'
		# Scroll Events.
		if mbutton < 128:
			offset = 64
		else:
			offset = 128
		id_mult = offset // 64

		# Evens scroll up, odds down.
		if mbutton % 2:
			act = 1 * id_mult
			offset += 1
		else:
			act = -1 * id_mult

	mods = mbutton - offset
	return Character((
		type, origin,
		(point(mx, my), act, mods & 0b11),
		interpret_key_modifiers((mods >> 2)+1),
	))

def im_test(char, xstart=ord('A'), xstop=ord('z')):
	"""
	# Test if the character can be considered an intermediate.

	# This is not consistent with VT100's as it allows for control characters
	# to be used as intermediates.
	"""
	if not char or char.isdigit() or char == ';':
		return False

	ci = ord(char)

	if ci < xstart:
		return True
	if ci > xstop:
		return True

	return False

def dispatch_sequence(region:str, separator=';'):
	"""
	# Parse, normally CSI, returning the intermediates, parameters, terminator,
	# and any following text as a remainder.

	# If no final character is present in the CSI, the last field in the returned
	# tuple will be &None indicating that a continuation or timeout should occur.
	"""

	terminator = None
	remainder = ""
	parameters = ()

	im_count = 0
	for i in range(1, len(region)):
		if not im_test(region[i:i+1]):
			break
		im_count += 1

	param_idx = 1 + im_count
	im = region[1:param_idx]

	pstart = region[param_idx:param_idx+1]
	if pstart.isdigit() or pstart == ';':
		# Parse decimal parameters.
		parameters = []

		param_strings = iter(region[param_idx:].split(separator))
		for x in param_strings:
			if x.isdigit() or not x:
				parameters.append(x or None)
			else:
				# non-digit
				final = x.lstrip("0123456789")
				terminator = final[:1]
				remainder = final[1:]
				pstr = x[:len(x) - len(final)]
				parameters.append(pstr or None)

				# Pickup remainder and finish iterator.
				trail = separator.join(param_strings)
				if trail != "":
					remainder += separator + trail
	else:
		# No parameters.
		terminator = region[param_idx:param_idx+1] or None
		remainder = region[param_idx+1:]

	return (remainder, (im, tuple(int(x) if x is not None else x for x in parameters), terminator))

def dispatch_string(region:str):
	"""
	# Parse OSC returning the intermediates, parameters, and any following text.
	"""
	return dispatch_sequence(region)

type_switch = {
	'[': ('csi', dispatch_sequence),
	']': ('osc', dispatch_string),
	'X': ('sos', dispatch_string),
	'^': ('pm', dispatch_string),
	'_': ('apc', dispatch_string),
	'P': ('dcs', dispatch_string),
}

csi_keymap = {
	1: ('navigation', 'home'),
	2: ('delta', 'insert'),
	3: ('delta', 'delete'),
	4: ('navigation', 'end'),
	5: ('navigation', 'page-up'),
	6: ('navigation', 'page-down'),
	11: ('function', 1),
	12: ('function', 2),
	13: ('function', 3),
	14: ('function', 4),
	15: ('function', 5),
	17: ('function', 6),
	18: ('function', 7),
	19: ('function', 8),
	20: ('function', 9),
	21: ('function', 10),
	23: ('function', 11),
	24: ('function', 12),
	29: ('function', 'applications'),
	34: ('function', 'windows'),
	200: ('paste', 'start'),
	201: ('paste', 'stop'),
}

csi_terminator_keys = {
	'A': 'up',
	'B': 'down',
	'C': 'right',
	'D': 'left',
	'H': 'home',
	'F': 'end',
}

csi_alternates = {
	# Tabs; [.u makes this uncessary, but leave it in for compatibility.
	'Z': ('control', 'i'),

	# xterm focus events
	'I': ('focus', 'in'),
	'O': ('focus', 'out'),
}

def sequence_map(escape, stype, action, region, remainder, Zero=Zero):
	assert stype == 'csi'
	origin = escape + region[:len(region) - len(remainder)]
	type = 'ignored-escape-sequence'
	ident = None
	mods = Zero

	intermediates, parameters, terminator = action

	if parameters[1:2] and parameters[1] is not None:
		mods = interpret_key_modifiers(parameters[1])

	if intermediates == "<":
		return (mouse(origin, terminator, parameters), remainder)
	if terminator == '~':
		assert len(parameters) > 0 # No key-id or modifiers
		key_id = parameters[0]

		type, ident = csi_keymap[key_id]
	elif terminator == 'u':
		codepoint = parameters[0]
		ident = chr(codepoint)
		return print(ident, source=origin, modifiers=mods), remainder
	elif terminator in csi_terminator_keys:
		type = 'navigation'
		ident = csi_terminator_keys[terminator]
	elif terminator in csi_alternates:
		type, ident = csi_alternates[terminator]
	elif terminator == 'R':
		type = 'cursor'
		ident = parameters
		mods = None

	return Character((type, origin, ident, mods)), remainder

def process_region_ground(escape, region, Meta=Meta, Zero=Zero):
	typ = region[0:1]
	stype, handler = type_switch.get(typ, (None, None))

	if handler is None:
		# Escape qualified character.
		start = region[:1]
		yield print(start, source=escape+start, modifiers=Meta)
		yield from map(print, region[1:])
	else:
		remainder, action = handler(region)
		event, remainder = sequence_map(escape, stype, action, region, remainder)
		yield event
		if (event[0], event[2]) == ("paste", "start"):
			# Switches to &process_region_data in &Parser
			yield Character(('data', remainder, 'paste', Zero))
		else:
			yield from map(print, remainder)

def process_region_data(escape, region, Meta=Meta, Zero=Zero):
	typ = region[0:1]
	stype, handler = type_switch.get(typ, (None, None))

	if handler is not None:
		remainder, action = handler(region)
		# [200~ starts and [201~ stops.
		if not action[0] and action[-1] == '~' and action[1][0] == 201:
			# Stop data state. No remainder if CSI is incomplete.
			d = len(region) - len(remainder)
			yield Character(('paste', escape+region[:d], 'stop', Zero))
			yield from map(print, remainder)

			# Otheriwse, generate data events.
			return
		elif action[-1] == None:
			# Incomplete sequence.
			yield Character(('ignored-escape-sequence', region, None, None))
			return

	# Literal Data
	yield Character(('data', escape, 'paste', Zero))
	yield Character(('data', region, 'paste', Zero))

def Parser(initial="", Sequence=list, escape="\x1b", separator=";", print=print, Zero=Zero, map=map):
	"""
	# VT100 CSI and Ground Parser constructing &core.Event sequences from
	# received &str instances.

	# Some functionality exceptions being that intermediate characters may not
	# appear after the first parameter and unrecognized forms will always be
	# emitted as a (id)`ignored-escape-sequence` event type.
	"""

	csi_cache = functools.lru_cache(64)(sequence_map)
	lit_cache = functools.lru_cache(32)(print)
	lit_ground = functools.partial(map, lit_cache)
	putdata = (lambda x: (Character(('data', x, 'paste', Zero)),))

	process_region = process_region_ground
	ground = lit_ground

	continuation = initial
	del initial # Make sure the reference gets dropped.

	events = Sequence()
	data, finish = (yield None)

	while True:
		# Leading the escape character if any.
		if continuation:
			data = continuation + data
			continuation = ""

		strings = data.split(escape)
		nregions = len(strings)
		if nregions < 0:
			data, finish = (yield Sequence())
			continue

		events.extend(ground(strings[0]))

		# If the read data length is less than the read size,
		# the parser should normally presume to finish.
		# Processors wishing to impose a delay can lie about
		# being on an edge in order to cause a continuation.
		if not finish and nregions > 1:
			# Trigger continuation; stop short in next step.
			last = -1
			continuation = escape + strings[-1]
		else:
			last = None

		for region in strings[1:last]:
			if region:
				events.extend(process_region(escape, region))
				if events:
					le = events[-1]
					if le[0] == 'data' and le[2] == 'paste':
						# Paste started/continued; change process_region
						process_region = process_region_data
						ground = putdata
					else:
						process_region = process_region_ground
						ground = lit_ground
			else:
				# Raw escape.
				events.extend(ground(escape))

		# If the last region is empty, it's either a sequence or a
		# literal escape that has not timed out yet.
		if last is not None and strings[last] != "":
			# Attempt to process last field and update continuation.

			advanced = 0
			for x in process_region(escape, strings[last]):
				if (x.type == 'ignored-escape-sequence'):
					# Incomplete CSI.
					break

				# Advanced position on continuation.
				if x.string[0:1] == escape:
					advanced -= 1
				advanced += len(x.string)
				events.append(x)
			else:
				# Aligned on continuation
				advanced = len(continuation)

			continuation = continuation[advanced:]
			# Check for paste.
			if advanced and events:
				le = events[-1]
				if le[0] == 'data' and le[2] == 'paste':
					# Paste started/continued; change process_region
					process_region = process_region_data
					ground = putdata
				else:
					process_region = process_region_ground
					ground = lit_ground

		data, finish = (yield events)
		events = Sequence()

def parser(initial:str=""):
	"""
	# Construct a started &Parser instance.

	# [ Parameters ]
	# /initial/
		# Optional initial string to be transformed when the first (id)`send` is performed.
	"""
	p = Parser(initial=initial)
	next(p)
	return p

del Char, Mod, Zero, Meta
