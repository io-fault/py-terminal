"""
Terminal device input and output interfaces.
"""
import collections
import functools

class Character(tuple):
	__slots__ = ()

	@property
	def type(self):
		return self[0]

	@property
	def string(self):
		return self[1]

	@property
	def identity(self):
		return self[2]

	@property
	def control(self):
		return self[3]

	@property
	def meta(self):
		return self[4]

def character(*args, Type = Character):
	return Type(args)
Character = character

escape_sequence = b'\x1b['

# Part of the initial escape.
separator = b';'
terminator = b'm'

reset = b'0'
select_foreground = b'38;5;'
select_background = b'48;5;'

# Pairs are of the form: (Initiate, Terminate)
styles = {
	'reset': (b'0', None),
	'dim': (b'2', b'22'),
	'bold': (b'1', b'22'),
	'blink': (b'5', b'25'),
	'rapid': (b'6', b'25'),
	'cross': (b'9', b'29'),
	'italic': (b'3', b'23'),
	'reverse': (b'7', b'0'),
	'conceal': (b'8', b'28'),
	'underline': (b'4', b'24'),
}

# Escape codes mapped to constructed Key presses.
escape_codes = {
	b'': Character('control', b'', 'escape', None, False),
	b' ': Character('control', b' ', 'space', False, True),

	b'[3~': Character('control', b'[3~', 'delete', False, False),
	b'\x7f': Character('control', b'\x7f', 'delete-back', False, True),
	b'\x08': Character('control', b'\x08', 'backspace', False, True),

	 # shift-tab and shift-meta-tab
	b'[Z': Character('tab', b'[Z', 'shift-tab', False, False),
	b'[Z': Character('tab', b'[Z', 'shift-tab', False, True),

	b'[H': Character('direction', b'[H', 'home', False, False), # home
	b'[F': Character('direction', b'[F', 'end', False, False), # end
	b'[5~': Character('direction', b'[5~', 'pageup', False, False), # page up
	b'[6~': Character('direction', b'[6~', 'pagedown', False, False), # page down

	b'OD': Character('direction', b'OD', 'left', False, False),
	b'OC': Character('direction', b'OC', 'right', False, False),
	b'OA': Character('direction', b'OA', 'up', False, False),
	b'OB': Character('direction', b'OB', 'down', False, False),

	b'[1;3D': Character('direction', b'[1;3D', 'left', False, True),
	b'[1;3C': Character('direction', b'[1;3C', 'right', False, True),
	b'[1;3A': Character('direction', b'[1;3A', 'up', False, True),
	b'[1;3B': Character('direction', b'[1;3B', 'down', False, True),

	b'OP': Character('function', b'OP', 1, False, False),
	b'OQ': Character('function', b'OQ', 2, False, False),
	b'OR': Character('function', b'OR', 3, False, False),
	b'OS': Character('function', b'OS', 4, False, False),

	b'[15~': Character('function', b'[15~', 5, False, False),
	b'[17~': Character('function', b'[17~', 6, False, False),
	b'[18~': Character('function', b'[18~', 7, False, False),
	b'[19~': Character('function', b'[19~', 8, False, False),
	b'[20~': Character('function', b'[20~', 9, False, False),
	b'[21~': Character('function', b'[21~', 10, False, False),
}

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
			Character('control', x, x, True, False)
			for x in map(chr, range(ord('a'), ord('z')+1))
		)
	)
)

# Override any of the control characters with the common representation.
control_characters.update({
	'\x00': Character('control', '\x00', 'nul', True, False),
	'\t': Character('control', '\t', 'tab', False, False),
	' ': Character('control', ' ', 'space', False, False),

	'\x7f': Character('control', '\x7f', 'delete-back', False, False),
	'\b': Character('control', '\b', 'backspace', False, False),

	'\r': Character('control', '\r', 'return', False, False),
	'': Character('control', '', 'enter', True, False),
	'\n': Character('control', '\n', 'newline', False, False),

	'': Character('control', '\\', 'backslash', True, False),
	'': Character('control', '_', 'underscore', True, False),
})

@functools.lru_cache(32)
def literal(k, Character = Character):
	return Character('literal', k, k, False, False)

def literal_events(data):
	'Resolve events for keys without escapes'
	return tuple(
		control_characters.get(x) if x in control_characters else literal(x)
		for x in (
			data[i:i+1] for i in range(len(data))
		)
	)

def escaped_events(data):
	"""
	Resolve the Key instance for the given bytes() instance.
	"""
	if data in escape_codes:
		return escape_codes[key]
	else:
		return Character('meta', key, key, False, True)

def key_events(data, escape = '\x1b'):
	"""
	Resolve the key events for the binary input read from a terminal.
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
			events = escaped_events(data[:first])
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

class Display(object):
	"""
	Control function index for manipulating a terminal display.

	This currently does not use the termcap database to shape the rendered escape sequences,
	and is primarily supporting xterm and xterm-like terminal implementations.
	"""
	escape_character = b'\x1b'
	escape_sequence = b'\x1b['

	def encode(self, escseq_param):
		return escseq_param.encode(self.encoding)

	def encode_decimal(self, num):
		return encode(str(num))

	def escape(self, terminator, *parts):
		return self.escape_sequence + b';'.join(parts) + terminator

	def __init__(self, name, capabilities = None, encoding = 'ascii'):
		self.name = name
		# XXX: reference capabilities instead of hardcoding sequences
		self.capabilities = capabilities
		self.encoding = encoding

	def carat_hide(self):
		return self.escape_sequence + b'?25l'

	def style(self, style_set, text):
		"""
		Style the text according to the given set.
		"""
		return text.encode('utf-8') # XXX: assumed encoding

	def backspace(self, times = 1):
		"""
		Cause an actual backspace to be performed.
		"""
		# mimics an actual backspace
		return b'\b \b' * times

	def seek(self, coordinates):
		'relocate the carat to an arbitrary, absolute location'
		h, v = coordinates
		return self.escape(b'H', str(h).encode('ascii'), str(v).encode('ascii'))

	def seek_horizontal_relative(self, n):
		'Horizontally adjust the carat (relative)'
		if n < 0:
			return self.escape(b'D', str(-n).encode('ascii'))
		elif n > 0:
			return self.escape(b'C', str(n).encode('ascii'))
		else:
			return ''

	def seek_vertical_relative(self, n):
		'Vertically adjust the carat (relative)'
		if n < 0:
			return self.escape(b'A', str(-n).encode('ascii'))
		elif n > 0:
			return self.escape(b'B', str(n).encode('ascii'))
		else:
			return b''

	def seek_relative(self, rcoords):
		h, v = rcoords
		return self.seek_horizontal_relative(h) + self.seek_vertical_relative(v)

	def seek_start_of_line(self):
		'Return the beginning of the line'
		return b'\r'

	def seek_next_line(self):
		return b'\n'

	def seek_start_of_next_line(self):
		'Open newline'
		return b'\n\r'

	def clear_display(self):
		'Clear the entire screen.'
		return self.escape_sequence + b'\x48\x1b\x5b\x32\x4a'

	def clear_before_caret(self):
		return self.escape_sequence + b'\x31\x4b'

	def clear_after_caret(self):
		return self.escape_sequence + b'\x4b'

	def clear_line(self):
		return self.clear_before_caret() + self.clear_after_caret()

	def store_caret_position(self):
		return self.escape_character + b'\x37'

	def restore_caret_position(self):
		return self.escape_character + b'\x38'

	def deflate_horizontal(self, size):
		return self.escape(b'P', self.encode_decimal(size))

	def deflate_vertical(self, size):
		return self.escape(b'M', self.encode_decimal(size))

	def inflate_horizontal(self, size):
		return self.escape(b'@', self.encode_decimal(size))

	def inflate_vertical(self, size):
		return self.escape(b'L', self.encode_decimal(size))

	def deflate_area(self, area):
		"""
		Delete space, (horizontal, vertical) between the carat.

		Often used to contract space after deleting characters.
		"""
		change = b''
		h, v = area

		if h:
			change += self.deflate_horizontal(h)
		if v:
			change += self.deflate_vertical(v)

		return change

	def inflate_area(self, area):
		"""
		Insert space, (horizontal, vertical) between the carat.

		Often used to make room for displaying characters.
		"""
		change = b''
		h, v = area

		if h:
			change += self.inflate_horizontal(h)
		if v:
			change += self.inflate_vertical(v)

		return change

	def resize(self, old, new):
		"""
		Given a number of characters from the caret @old, resize the area
		to @new. This handles cases when the new size is smaller and larger than the old.
		"""
		deletes = self.deflate_horizontal(old)
		spaces = self.inflate_horizontal(new)

		return deletes + spaces
