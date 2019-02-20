"""
# Terminal device input and output interfaces.

# The Character input works with unicode while the output works with bytes.
# Certain display events (style) may work with unicode (str) object, but access
# to raw output is available.

# The module level constants are xterm-compatible and can be used directly, but
# won't be updated to support other terminals. The &Display class provides [or will provide]
# the necessary abstraction to load and use terminal implementation specific codes.
# Currently, however, xterm is assumed.
"""
import array
import collections
import functools
import itertools

from . import core
from . import palette

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

class Display(object):
	"""
	# Control function index for manipulating a terminal display.

	# This currently does not use the termcap database to shape the rendered escape sequences,
	# and is primarily supporting xterm and xterm-like terminal implementations.
	"""
	control_mapping = {chr(i): chr(0x2400 + i) for i in range(32)}
	control_table = str.maketrans(control_mapping)

	escape_character = b'\x1b'
	escape_sequence = b'\x1b['
	join = b';'.join

	def __init__(self, encoding = 'utf-8'):
		self.encoding = encoding

	def encode(self, escseq_param, str=str):
		return str(escseq_param).encode(self.encoding)

	def draw_unit_vertical(self, character):
		c = character.encode(self.encoding)
		if character:
			l = character.__len__()
			c += self.seek_horizontal_relative(-l) + self.seek_vertical_relative(1)
		return c

	def draw_unit_horizontal(self, character):
		return character.encode(self.encoding)

	def draw_segment_vertical(self, unit, length):
		return self.draw_unit_vertical(unit) * length

	def draw_segment_horizontal(self, unit, length):
		return self.draw_unit_horizontal(unit) * length

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
		#  24-bit color constructor.
		"""
		r = (rgb >> 16) & 0xFF
		g = (rgb >> 8) & 0xFF
		b = (rgb >> 0) & 0xFF
		return b';'.join(map(self.encode, (r, g, b)))

	def background(self, color, select_background=select_background):
		translation = palette.translate(color)
		strcode = palette.code_string(translation)

		return (select_background, strcode)

	def foreground(self, color, select_foreground=select_foreground_rgb):
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
		#  Style the text for printing according to the given style set and color.

		#  &styles is a set of style names to apply. The support set is listed in &style_codes.
		#  &color is a 24-bit color value that is translated to a terminal color code.
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
		# Apply the &style method to a sequence joining the results into a single string.
		"""

		style = partial(self.style, foreground=foreground, background=background)
		return b''.join(chain((), map(style, seq)))

	def backspace(self, times=1):
		"""
		# Cause an actual backspace to be performed.
		"""
		# mimics an actual backspace
		return b'\b \b' * times

	def space(self, times = 1):
		"""
		# Insert a sequence of spaces.
		"""
		return b' ' * times

	def erase(self, times=1):
		"""
		# The 'X' terminal code.
		"""
		return self.escape(self.encode(times) + b'X')

	def blank(self, times=1):
		"""
		# The '@' terminal code.
		"""
		return self.escape(self.encode(times) + b'@')

	def seek_absolute(self, coordinates):
		h, v = coordinates
		return self.escape(b'H', self.encode(v+1), self.encode(h+1))

	def seek(self, coordinates):
		"""
		# Relocate the caret to an arbitrary, (area) relative location.
		"""
		return self.seek_absolute(coordinates)

	def seek_line(self, lineno):
		"""
		# Seek to the beginning of a particular line number.
		"""
		return self.seek((0, lineno))

	def seek_start_of_line(self):
		return b'\r'

	def seek_horizontal_relative(self, n):
		if n < 0:
			return self.escape(b'D', self.encode(-n))
		elif n > 0:
			return self.escape(b'C', self.encode(n))
		else:
			return b''

	def seek_vertical_relative(self, n):
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
		return self.escape(b'H') + self.escape(b'2J')

	def clear_line(self, lineno):
		return self.seek_line(lineno) + self.clear_current_line()

	def clear_to_line(self, n = 1):
		return self.escape(self.encode(n) + b'J')

	def clear_to_bottom(self):
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
		# Delete space, (horizontal, vertical) between the caret.

		# Often used to contract space after deleting characters.
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
		# Insert space, (horizontal, vertical) between the caret.

		# Often used to make room for displaying characters.
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
		# Given a number of characters from the caret &old, resize the area
		# to &new. This handles cases when the new size is smaller and larger than the old.
		"""
		deletes = self.deflate_horizontal(old)
		spaces = self.inflate_horizontal(new)

		return deletes + spaces

	def delete(self, start, stop):
		"""
		# Delete the slice of characters moving the remainder in.
		"""
		buf = self.seek_start_of_line()
		buf += self.seek_horizontal_relative(start)
		buf += self.deflate_horizontal(stop)
		return buf

	def overwrite(self, offset_styles):
		"""
		# Given a sequence of (relative_offset, style(text)), return
		# the necessary sequences to *overwrite* the characters at the offset.
		"""
		buf = bytearray()
		for offset, styles in offset_styles:
			buf += self.seek_horizontal_relative(offset)
			buf += self.style(styles)
		return buf
