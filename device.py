"""
Terminal device input and output interfaces.

The Character input works with unicode while the output works with bytes.
Certain display events (style) may work with unicode (str) object, but access
to raw output is available.

The module level constants are xterm-compatible and can be used directly, but
won't be updated to support other terminals. The &Display class provides [or will provide]
the necessary abstraction to load and use terminal implementation specific codes.
Currently, however, xterm is assumed.
"""
import array
import collections
import functools
import fcntl
import tty
import termios

from . import core
from . import palette

path = '/dev/tty'

escape_character = b'\x1b'
escape_sequence = b'\x1b['

# Part of the initial escape.
separator = b';'
terminator = b'm'

reset = b'0'
select_foreground = b'38;5'
select_background = b'48;5'

# Pairs are of the form: (Initiate, Terminate)
style_codes = {
	'bold': (b'1', b'22'),
	'italic': (b'3', b'23'),
	'underline': (b'4', b'24'),
	'dim': (b'2', b'22'),
	'blink': (b'5', b'25'),
	'reverse': (b'7', b'7'),
	'cross': (b'9', b'29'),
	'rapid': (b'6', b'25'),
	'conceal': (b'8', b'28'),
}

# Escape codes mapped to constructed Key presses.
escape_codes = {
	'': core.Character(('control', '', 'escape', core.Modifiers.construct())),
	' ': core.Character(('control', ' ', 'space', core.Modifiers.construct(meta=True))),
	'[Z': core.Character(('control', '[Z', 'tab', core.Modifiers.construct(shift=True))),
	'[Z': core.Character(('control', '[Z', 'tab', core.Modifiers.construct(shift=True, meta=True))),

	'\x7f': core.Character(('control', '\x7f', 'delete-back', core.Modifiers.construct(meta=True))),
	'\x08': core.Character(('control', '\x08', 'backspace', core.Modifiers.construct(meta=True))),

	'[2~': core.Character(('manipulation', '[2~', 'insert', core.Modifiers.construct())),
	'[3~': core.Character(('manipulation', '[3~', 'delete', core.Modifiers.construct())),

	'OA': core.Character(('navigation', 'OA', 'up', core.Modifiers.construct())),
	'OB': core.Character(('navigation', 'OB', 'down', core.Modifiers.construct())),
	'OC': core.Character(('navigation', 'OC', 'right', core.Modifiers.construct())),
	'OD': core.Character(('navigation', 'OD', 'left', core.Modifiers.construct())),
	'[H': core.Character(('navigation', '[H', 'home', core.Modifiers.construct())),
	'[F': core.Character(('navigation', '[F', 'end', core.Modifiers.construct())),
	'[5~': core.Character(('navigation', '[5~', 'pageup', core.Modifiers.construct())),
	'[6~': core.Character(('navigation', '[6~', 'pagedown', core.Modifiers.construct())),

	'OP': core.Character(('function', 'OP', 1, core.Modifiers.construct())),
	'OQ': core.Character(('function', 'OQ', 2, core.Modifiers.construct())),
	'OR': core.Character(('function', 'OR', 3, core.Modifiers.construct())),
	'OS': core.Character(('function', 'OS', 4, core.Modifiers.construct())),
	'[15~': core.Character(('function', '[15~', 5, core.Modifiers.construct())),
	'[17~': core.Character(('function', '[17~', 6, core.Modifiers.construct())),
	'[18~': core.Character(('function', '[18~', 7, core.Modifiers.construct())),
	'[19~': core.Character(('function', '[19~', 8, core.Modifiers.construct())),
	'[20~': core.Character(('function', '[20~', 9, core.Modifiers.construct())),
	'[21~': core.Character(('function', '[21~', 10, core.Modifiers.construct())),
	'[23~': core.Character(('function', '[23~', 11, core.Modifiers.construct())),
	'[24~': core.Character(('function', '[24~', 12, core.Modifiers.construct())),
	'[29~': core.Character(('function', '[29~', 'applications', core.Modifiers.construct())),
	'[34~': core.Character(('function', '[34~', 'windows', core.Modifiers.construct())),
}

# build out the codes according to the available patterns
def render_codes():
	modifier_sequence = tuple(zip((2,3,5,6,7), (
		core.Modifiers.construct(shift=True),
		core.Modifiers.construct(meta=True),
		core.Modifiers.construct(control=True),
		core.Modifiers.construct(shift=True, control=True),
		core.Modifiers.construct(control=True, meta=True),
	)))

	# insert and delete
	for formatting, ident in (('[2;%d~', 'insert'), ('[3;%d~', 'delete')):
		escape_codes.update([
			(x.string[1:], x) for x in (
				core.Character(('manipulation', formatting %(n,), ident))
				for n, mods in modifier_sequence
			)
		])

	# page up and page down
	formatting = '[%s;%d~'
	for key in (('5', 'page-up'), ('6', 'page-down')):
		num, name = key
		escape_codes.update([
			(x.string[1:], x) for x in (
				core.Character(('navigation', formatting % (num, n), key))
				for n, mods in modifier_sequence
			)
		])

	# arrows and home and end
	formatting = '[1;%d%s'
	for key in (('A', 'up'), ('B', 'down'), ('C', 'right'), ('D', 'left'), ('H', 'home'), ('F', 'end')):
		kid, name = key
		escape_codes.update([
			(x.string[1:], x) for x in (
				core.Character(('navigation', formatting % (n, kid), key))
				for n, mods in modifier_sequence
			)
		])

	# function keys 1-4
	formatting = '[1;%d%s'
	chars = ('P', 'Q', 'R', 'S')
	for i in range(4):
		char = chars[i]
		escape_codes.update([
			(x.string[1:], x) for x in (
				core.Character(('function', formatting % (n, char), i+1, mods))
				for n, mods in modifier_sequence
			)
		])

	# function keys 5-12
	formatting = '[%d;%d~'
	for kid, fn in zip((15, 17, 18, 19, 20, 21, 23, 24), range(5, 12)):
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
			core.Character(('control', x, x, core.Modifiers.construct(control=True)))
			for x in map(chr, range(ord('a'), ord('z')+1))
		)
	)
)

# Override any of the control characters with the common representation.
control_characters.update({
	'\x00': core.Character(('control', '\x00', 'nul', core.Modifiers.construct(control=True))),
	'\t': core.Character(('control', '\t', 'tab', core.Modifiers.construct(control=True))),
	' ': core.Character(('control', ' ', 'space', core.Modifiers.construct(control=True))),

	'\x7f': core.Character(('control', '\x7f', 'delete-back', core.Modifiers.construct(control=True))),
	'\b': core.Character(('control', '\b', 'backspace', core.Modifiers.construct(control=True))),

	'\r': core.Character(('control', '\r', 'return', core.Modifiers.construct(control=True))),
	'': core.Character(('control', '', 'enter', core.Modifiers.construct(control=True))),
	'\n': core.Character(('control', '\n', 'newline', core.Modifiers.construct(control=True))),

	'': core.Character(('control', '\\', 'backslash', core.Modifiers.construct(control=True))),
	'': core.Character(('control', '_', 'underscore', core.Modifiers.construct(control=True))),
})

@functools.lru_cache(32)
def literal(k, Character = core.Character, Modifiers = core.Modifiers):
	return Character(('literal', k, k.lower(), Modifiers(0)))

def literal_events(data):
	'Resolve events for keys without escapes'
	return tuple(
		control_characters[x] if x in control_characters else literal(x)
		for x in data
	)

def escaped_events(string, Character = core.Character):
	"""
	Resolve the Key instance for the given string instance.
	"""
	if string in escape_codes:
		return escape_codes[string]
	else:
		return Character(('escaped', string, string, core.Modifiers(0)))

def construct_character_events(data, escape = '\x1b'):
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
	join = b';'.join

	def encode(self, escseq_param, str = str):
		return str(escseq_param).encode(self.encoding)

	def escape(self, terminator, *parts):
		return self.escape_sequence + self.join(parts) + terminator

	def __init__(self, capabilities = None, encoding = 'utf-8'):
		# XXX: reference capabilities instead of hardcoding sequences
		self.capabilities = capabilities
		self.encoding = encoding

	def carat_hide(self):
		return self.escape_sequence + b'?25l'

	def carat_show(self):
		return self.escape_sequence + b'[?12l' + self.escape_sequence + b'[?25h'

	def print(self, text):
		return self.encode(text)

	def style(self, text, styles = (), color = None):
		"""
		Style the text for printing according to the given style set and color.

		&styles is a set of style names to apply. The support set is listed in &style_codes.
		&color is a 24-bit color value that is translated to a terminal color code.
		"""
		# XXX: escape newlines and low-ascii?
		txt = self.encode(text)
		if color is None and not styles:
			return txt

		prefix = b''
		suffix = b''

		if styles:
			prefix += b''.join([self.escape(b'm', style_codes[x][0]) for x in styles])
			suffix += b''.join([self.escape(b'm', style_codes[x][1]) for x in styles])

		if color is not None:
			translation = palette.translate(color)
			strcode = palette.code_string(translation)

			prefix += self.escape(b'm', select_foreground, strcode)
			suffix += self.escape(b'm', reset)

		return prefix + txt + suffix

	def backspace(self, times = 1):
		"""
		Cause an actual backspace to be performed.
		"""
		# mimics an actual backspace
		return b'\b \b' * times

	def space(self, times = 1):
		"""
		Insert a set of spaces.
		"""
		return b' ' * times

	def erase(self, times = 1):
		"""
		The 'X' terminal code.
		"""
		return self.escape(self.encode(times) + b'X')

	def seek_absolute(self, coordinates):
		'mechanics used by seek method. (use &seek)'
		h, v = coordinates
		return self.escape(b'H', self.encode(h), self.encode(v))

	def seek(self, coordinates):
		"""
		Relocate the carat to an arbitrary, (area) relative location.
		"""
		return self.seek_absolute(coordinates)

	def seek_start_of_line(self):
		'Return the beginning of the line'
		return b'\r'

	def seek_horizontal_relative(self, n):
		'Horizontally adjust the carat (relative)'
		if n < 0:
			return self.escape(b'D', self.encode(-n))
		elif n > 0:
			return self.escape(b'C', self.encode(n))
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

	def seek_next_line(self):
		return self.seek_vertical_relative(1)

	def seek_start_of_next_line(self):
		return self.seek_next_line() + self.seek_start_of_line()

	def clear(self):
		'Clear the entire screen.'
		return self.escape_sequence + b'\x48' + self.escape_sequence + b'\x5b\x32\x4a'

	def clear_to_line(self, n = 1):
		'Clear the lines to a relative number'
		return self.escape(self.encode(n) + b'J')

	def clear_to_bottom(self):
		'End of screen'
		return self.escape(b'J')

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
		return self.escape(b'P', self.encode(size))

	def deflate_vertical(self, size):
		return self.escape(b'M', self.encode(size))

	def inflate_horizontal(self, size):
		return self.escape(b'@', self.encode(size))

	def inflate_vertical(self, size):
		return self.escape(b'L', self.encode(size))

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
		Given a number of characters from the caret &old, resize the area
		to &new. This handles cases when the new size is smaller and larger than the old.
		"""
		deletes = self.deflate_horizontal(old)
		spaces = self.inflate_horizontal(new)

		return deletes + spaces

	def delete(self, start, stop):
		"""
		Delete the slice of characters moving the remainder in.
		"""
		buf = self.seek_start_of_line()
		buf += self.seek_horizontal_relative(start)
		buf += self.deflate_horizontal(stop)
		return buf

	def overwrite(self, offset_styles):
		"""
		Given a sequence of (relative_offset, style(text)), return
		the necessary sequences to *overwrite* the characters at the offset.
		"""
		buf = bytearray()
		for offset, styles in offset_styles:
			buf += self.seek_horizontal_relative(offset)
			buf += self.style(styles)
		return buf

def set_raw(fd, path = path):
	"""
	Set raw mode and return the previous settings.
	"""
	tty.setcbreak(fd)
	tty.setraw(fd)
	new = termios.tcgetattr(fd)
	new[3] = new[3] & ~(termios.ECHO|termios.ICRNL)
	termios.tcsetattr(fd, termios.TCSADRAIN, new)

def settings_snapshot(fd):
	"""
	Get the current terminal settings.
	"""
	return termios.tcgetattr(fd)

def settings_restore(fd, stored_settings, path = path):
	"""
	Apply the given settings.
	"""
	return termios.tcsetattr(fd, termios.TCSADRAIN, stored_settings)

def dimensions(fd, winsize = array.array("h", [0,0,0,0])):
	"""
	Dimensions of the physical terminal.
	"""
	winsize = winsize * 1 # get a new array instance
	fcntl.ioctl(fd, termios.TIOCGWINSZ, winsize, True)
	return (winsize[1], winsize[0])
