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
import itertools

from . import core
from . import palette

@functools.lru_cache(16)
def point(x, y, Type=core.Point):
	return Type((x,y))

path = '/dev/tty'

escape_character = b'\x1b'
escape_sequence = b'\x1b['

# Part of the initial escape.
separator = b';'

reset = b'0'
select_foreground = b'38;5'
select_background = b'48;5'
select_foreground_rgb = b'38;2'
select_background_rgb = b'48;2'

# Pairs are of the form: (Initiate, Terminate)
style_codes = {
	'bold': (b'1', b'22'),
	'feint': (b'2', b'22'),
	'italic': (b'3', b'23'),
	'underline': (b'4', b'24'),
	'double-underline': (b'21', b'24'),
	'blink': (b'5', b'25'),
	'rapid': (b'6', b'25'),
	'reverse': (b'7', b'27'),
	'invisible': (b'8', b'28'),
	'cross': (b'9', b'29'),
}

Char = core.Character
zero = core.Modifiers.construct()
# Escape codes mapped to constructed Key presses.
escape_codes = {
	'': Char(('control', '', 'escape', zero)),
	' ': Char(('control', ' ', 'space', core.Modifiers.construct(meta=True))),
	'\t': Char(('control', '\t', 'tab', core.Modifiers.construct(meta=True))),
	'[Z': Char(('control', '[Z', 'tab', core.Modifiers.construct(shift=True))),
	'[Z': Char(('control', '[Z', 'tab', core.Modifiers.construct(shift=True, meta=True))),
	'OM': Char(('control', 'OM', 'enter', zero)),

	'\x7f': Char(('delta', '\x7f', 'delete', core.Modifiers.construct(meta=True))),
	'\b': Char(('delta', '\b', 'backspace', core.Modifiers.construct(meta=True))),

	'[2~': Char(('delta', '[2~', 'insert', core.Modifiers.construct(meta=False))),
	'[3~': Char(('delta', '[3~', 'delete', core.Modifiers.construct(meta=False))),

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
	'[5~': Char(('navigation', '[5~', 'pageup', zero)),
	'[6~': Char(('navigation', '[6~', 'pagedown', zero)),

	'OP': Char(('function', 'OP', 1, zero)),
	'OQ': Char(('function', 'OQ', 2, zero)),
	'OR': Char(('function', 'OR', 3, zero)),
	'OS': Char(('function', 'OS', 4, zero)),
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
				core.Character(('delta', formatting %(n,), ident, mods))
				for n, mods in modifier_sequence
			)
		])

	# page up and page down
	formatting = '[%s;%d~'
	for key in (('5', 'page-up'), ('6', 'page-down')):
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

Modifier = core.Modifiers.construct
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
			Char(('control', x, x, Modifier(control=True)))
			for x in map(chr, range(ord('a'), ord('z')+1))
		)
	)
)

# Override any of the control characters with the common representation.
control_characters.update({
	'\x00': Char(('control', '\x00', 'nul', Modifier(control=False))),

	'\x7f': Char(('delta', '\x7f', 'delete', Modifier(control=False))),
	'\b': Char(('delta', '\b', 'backspace', Modifier(control=False))),

	' ': Char(('control', ' ', 'space', Modifier(control=False))),

	'\t': Char(('control', '\t', 'tab', Modifier(control=False))),
	'\r': Char(('control', '\r', 'return', Modifier(control=False))),
	'\n': Char(('control', '\n', 'newline', Modifier(control=False))),

	'': Char(('control', '', 'bracket', Modifier(control=True))),
	'': Char(('control', '', 'backslash', Modifier(control=True))),
	'': Char(('control', '', 'underscore', Modifier(control=True))),
})
del Char, Modifier

@functools.lru_cache(32)
def literal(k, Character = core.Character,
		none = core.Modifiers(0),
		shift = core.Modifiers.construct(shift=True),
	):
	id = k.lower()
	return Character(('literal', k, id, shift if k != id else none))

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
	Resolve the Key instance for the given string instance.
	"""

	if string in escape_codes:
		return escape_codes[string]
	else:
		if string[:2] == '[<':
			# mouse event
			return mouse(string)
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

class Display(object):
	"""
	Control function index for manipulating a terminal display.

	This currently does not use the termcap database to shape the rendered escape sequences,
	and is primarily supporting xterm and xterm-like terminal implementations.
	"""
	control_mapping = {chr(i): chr(0x2400 + i) for i in range(32)}
	control_table = str.maketrans(control_mapping)

	escape_character = b'\x1b'
	escape_sequence = b'\x1b['
	join = b';'.join

	def __init__(self, encoding = 'utf-8'):
		self.encoding = encoding

	def encode(self, escseq_param, str = str):
		return str(escseq_param).encode(self.encoding)

	def escape(self, terminator, *parts):
		return self.escape_sequence + self.join(parts) + terminator

	def caret_hide(self):
		return self.escape_sequence + b'?25l'

	def caret_show(self):
		return self.escape_sequence + b'[?12l' + self.escape_sequence + b'[?25h'

	def disable_line_wrap(self):
		return self.escape_sequence + b'?7l'

	def enable_line_wrap(self):
		return self.escape_sequence + b'?7h'

	def print(self, text, control_map = control_table):
		return self.encode(text.translate(control_map))

	@functools.lru_cache(32)
	def color_string(self, rgb):
		"""
		# 24-bit color constructor.
		"""
		r = (rgb >> 16) & 0xFF
		g = (rgb >> 8) & 0xFF
		b = (rgb >> 0) & 0xFF
		return b';'.join(map(self.encode, (r, g, b)))

	def background(self, color, select_background=select_background):
		"Change the background color."

		translation = palette.translate(color)
		strcode = palette.code_string(translation)

		return (select_background, strcode)

	def foreground(self, color, select_foreground=select_foreground_rgb):
		"Change the foreground color."

		#translation = palette.translate(color)
		#strcode = palette.code_string(translation)

		return (select_foreground, self.color_string(color))

	def style(self, text, styles=(),
			textcolor=None, cellcolor=None,
			foreground=None,
			background=None,
			control_map=control_table
		):
		"""
		# Style the text for printing according to the given style set and color.

		# &styles is a set of style names to apply. The support set is listed in &style_codes.
		# &color is a 24-bit color value that is translated to a terminal color code.
		"""

		# XXX: escape newlines and low-ascii?
		txt = self.encode(text.translate(control_map))

		prefix = []
		suffix = []
		prefix_bytes = b''
		suffix_bytes = b''

		if styles:
			prefix.extend([style_codes[x][0] for x in styles])

		if textcolor is not None:
			prefix.extend(self.foreground(textcolor))
			#prefix += self.escape(b'm', select_foreground_rgb, self.color_string(color))

			# Reset to foreground.
			if foreground is not None:
				suffix.extend(self.foreground(foreground))

		if cellcolor is not None:
			prefix.extend(self.background(cellcolor))
			#prefix += self.escape(b'm', select_background_rgb, self.color_string(color))

			# Reset to background.
			if background is not None:
				suffix.extend(self.background(background))

		if prefix:
			prefix_bytes = self.escape(b'm', *prefix)

		suffix_bytes = self.escape(b'm', reset, *suffix)

		return prefix_bytes + txt + suffix_bytes

	def renderline(self, seq,
			foreground=None,
			background=None,
			map=itertools.starmap,
			chain=itertools.chain,
			partial=functools.partial,
		):
		"""
		Apply the &style method to a sequence joining the results into a single string.
		"""

		style = partial(self.style, foreground=foreground, background=background)
		return b''.join(chain((), map(style, seq)))

	def backspace(self, times=1):
		"""
		Cause an actual backspace to be performed.
		"""
		# mimics an actual backspace
		return b'\b \b' * times

	def space(self, times = 1):
		"""
		Insert a sequence of spaces.
		"""
		return b' ' * times

	def erase(self, times=1):
		"""
		The 'X' terminal code.
		"""
		return self.escape(self.encode(times) + b'X')

	def blank(self, times=1):
		"""
		The '@' terminal code.
		"""
		return self.escape(self.encode(times) + b'@')

	def seek_absolute(self, coordinates):
		'mechanics used by seek method. (use &seek)'
		h, v = coordinates
		return self.escape(b'H', self.encode(v+1), self.encode(h+1))

	def seek(self, coordinates):
		"""
		Relocate the caret to an arbitrary, (area) relative location.
		"""
		return self.seek_absolute(coordinates)

	def seek_line(self, lineno):
		"""
		Seek to the beginning of a particular line number.
		"""
		return self.seek((0, lineno))

	def seek_start_of_line(self):
		'Return the beginning of the line'
		return b'\r'

	def seek_horizontal_relative(self, n):
		'Horizontally adjust the caret (relative)'
		if n < 0:
			return self.escape(b'D', self.encode(-n))
		elif n > 0:
			return self.escape(b'C', self.encode(n))
		else:
			return b''

	def seek_vertical_relative(self, n):
		'Vertically adjust the caret (relative)'
		if n < 0:
			return self.escape(b'A', self.encode(-n))
		elif n > 0:
			return self.escape(b'B', self.encode(n))
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
		'Clear the entire area.'
		return self.escape(b'H') + self.escape(b'2J')

	def clear_line(self, lineno):
		return self.seek_line(lineno) + self.clear_current_line()

	def clear_to_line(self, n = 1):
		'Clear the lines to a relative number.'
		return self.escape(self.encode(n) + b'J')

	def clear_to_bottom(self):
		'Clear to the end of screen from the caret.'
		return self.escape(b'J')

	def clear_before_caret(self):
		return self.escape_sequence + b'\x31\x4b'

	def clear_after_caret(self):
		return self.escape_sequence + b'\x4b'

	def clear_current_line(self):
		return self.clear_before_caret() + self.clear_after_caret()

	def store_caret_position(self):
		return self.escape_character + b'\x37'

	def restore_caret_position(self):
		return self.escape_character + b'\x38'

	def save_screen(self):
		return self.escape(b'?1049h')

	def restore_screen(self):
		return self.escape(b'?1049l')

	def enable_mouse(self):
		return self.escape(b'?1002h') + self.escape(b'?1006h')

	def disable_mouse(self):
		return self.escape(b'?1002l') + self.escape(b'?1006l')

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
		Delete space, (horizontal, vertical) between the caret.

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
		Insert space, (horizontal, vertical) between the caret.

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

def set_raw(fd, path=path):
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

def settings_restore(fd, stored_settings, path=path):
	"""
	Apply the given settings.
	"""
	return termios.tcsetattr(fd, termios.TCSADRAIN, stored_settings)

def dimensions(fd, winsize=array.array("h", [0,0,0,0])):
	"""
	Dimensions of the physical terminal.
	"""
	winsize = winsize * 1 # get a new array instance
	fcntl.ioctl(fd, termios.TIOCGWINSZ, winsize, True)
	return (winsize[1], winsize[0])
