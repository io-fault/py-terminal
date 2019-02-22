"""
# Character matrix rendering contexts.
"""
import functools
import itertools

from . import text

# Part of the initial escape.
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

def offsets(text_sequence, *indexes, iter=iter, len=len, next=next, cells=text.cells):
	"""
	# Get the cell offset of the given character indexes.
	"""
	offset = 0
	nc = 0
	noffset = 0

	i = iter(text_sequence or (('',),))
	x = next(i)
	t = x[0]

	for y in indexes:
		if y == 0:
			yield 0
			continue
		while x is not None:
			chars = len(t)
			noffset = offset + chars

			if noffset >= y:
				# found it
				yield nc + cells(t[:y-offset])
				break

			nc += cells(t)
			offset = noffset
			try:
				x = next(i)
			except StopIteration:
				raise IndexError(y)
			t = x[0]
		else:
			# index out of range
			raise IndexError(y)

class Context(object):
	"""
	# Rendering context for character matrices.
	"""
	control_mapping = {chr(i): chr(0x2400 + i) for i in range(32)}
	control_table = str.maketrans(control_mapping)

	escape_character = b'\x1b'
	escape_sequence = b'\x1b['
	reset = b'0'
	join = b';'.join

	@staticmethod
	@functools.lru_cache(32)
	def translate(spoint, point):
		return (point[0] + spoint[0], point[1] + spoint[1])

	def __init__(self, encoding='utf-8'):
		self.encoding = encoding

	def adjust(self, position, dimensions):
		"""
		# Adjust the position and dimensions of the rendering context.
		"""
		self.point = position
		self.dimensions = dimensions
		# track relative position for seek operations
		self.width, self.height = dimensions

	def encode(self, escseq_param, str=str):
		return str(escseq_param).encode(self.encoding)

	def escape(self, terminator, *parts):
		return self.escape_sequence + self.join(parts) + terminator

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

		##
		# REP doesn't have the greatest support when it comes to box drawing characters.
		# tmux and Apple's Terminal does not appear to recognize them as "graphic characters".
		return self.draw_unit_horizontal(unit) + self.escape(b'b', self.encode(str(length-1)))

	def print(self, text, control_map=control_table):
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

		suffix_bytes = self.escape(b'm', self.reset, *suffix)

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

	def space(self, count=1):
		"""
		# Insert a sequence of spaces.
		"""
		return b' ' * count

	def blank(self, count=1):
		"""
		# Generate sequence for writing blank characters.
		# Semantically, this should be equivalent to &space.
		"""
		return self.escape(self.encode(count) + b'@')

	def clear_line(self, lineno):
		return self.seek_line(lineno) + self.clear_current_line()

	def clear_to_line(self, n = 1):
		return self.escape(self.encode(n) + b'J')

	def clear_to_bottom(self):
		return self.escape(b'J')

	def clear_before_cursor(self):
		return self.escape_sequence + b'\x31\x4b'

	def clear_after_cursor(self):
		return self.escape_sequence + b'\x4b'

	def clear_current_line(self):
		return self.clear_before_cursor() + self.clear_after_cursor()

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
		# Delete space, (horizontal, vertical) between the cursor.

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
		# Insert space, (horizontal, vertical) between the cursor.

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
		# Given a number of characters from the cursor &old, resize the area
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

	def clear(self):
		"""
		# Clear the area.
		"""
		init = self.seek((0, 0))

		clearline = self.erase(self.width)
		#bol = self.seek_horizontal_relative(-(self.width-1))
		bol = b''
		nl = b'\n'

		return init + (self.height * (clearline + bol + nl))

	def erase(self, count=1, background=None):
		if background is None:
			return self.escape(self.encode(count) + b'X')
		else:
			# fill with colored spaces if the background is not None.
			return self.style(' ' * count, styles=(), cellcolor=background)

	def seek(self, point):
		"""
		# Seek to the point relative to the area.
		"""
		return self.seek_absolute(self.translate(self.point, point))

	def seek_start_of_line(self):
		"""
		# Seek to the start of the line.
		"""
		return b'\r' + self.seek_horizontal_relative(self.point[0])

	def seek_bottom(self):
		"""
		# Seek to the last row of the area and the first column.
		"""
		return self.seek((0, self.height-1))

	def seek_absolute(self, coordinates):
		"""
		# Coordinates are absolute; &Screen relative.
		"""
		h, v = coordinates
		return self.escape(b'H', self.encode(v+1), self.encode(h+1))

	def seek_line(self, lineno):
		"""
		# Seek to the beginning of a particular line number.
		"""
		return self.seek((0, lineno))

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

class Screen(Context):
	"""
	# Matrix Context bound to the first column and row.
	"""

	def adjust(self, point, dimensions):
		if point != (0, 0):
			raise ValueError("screen contexts must be positioned at zero")
		return super().adjust(point, dimensions)

	seek = Context.seek_absolute
	def seek_start_of_line(self):
		return b'\r'

	def clear(self):
		return self.escape(b'H') + self.escape(b'2J')

	def erase(self, count=1):
		"""
		# Erase &count number of characters. `(CSI {count} X)`
		# Implies default background.
		"""
		return self.escape(self.encode(times) + b'X')
