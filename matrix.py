"""
# Character matrix rendering contexts.

# Holds &Context and &Screen defintions for constructing escape sequences to be transmitted
# to the terminal.
"""
import functools
import itertools
import typing
import codecs

from ..system import text
from .core import \
	Units, \
	Phrase, \
	Traits, \
	RenderParameters, \
	Page

def encoders(encoding, errors='surrogateescape', size=64):
	"""
	# Cached encoder lookup. Internally composes a function with the configured
	# error handler that returns the encoded string alone. Caches the resolved
	# encoding information and functions in the module's globals for repeat reads.

	# [ Returns ]
	# Tuple of four items.

	# # &encoding parameter.
	# # `codecs.getencoder(encoding)` result
	# # &..collections.abc.Callable
	# # Caching form of the prior composed callable.
	"""
	name = "_" + encoding.replace("-", "_") + "_" + errors.replace("-", "_")
	if name in globals():
		return globals()[name]

	ef = codecs.getencoder(encoding)
	def context_encoder(obj, errors=errors, str=str, ef=ef):
		return ef(str(obj), errors)[0] # str.encode(&encoding)
	r = globals()[name] = (encoding, ef, context_encoder, functools.lru_cache(size)(context_encoder))
	return r

class Context(object):
	"""
	# Rendering Context for character matrices.

	# Initialized with the encoding that text should be encoded with.

	# Methods beginning with (id)`context_` are Context configuration interfaces
	# returning the instance for method chaining.
	"""
	point = (None, None)

	control_mapping = {chr(i): chr(0x2400 + i) for i in range(32)}
	control_table = str.maketrans(control_mapping)

	escape_character = b'\x1b'
	_join = b';'.join
	_csi_init = b'\x1b['
	_osc_init = b'\x1b]'
	_osc_terminate = b'\x07'
	_reset_text_attributes = b'0'

	# Support for SGR color.
	@staticmethod
	def _select_foreground_16(code, offsets=(30, 90)):
		return offsets[code//8] + (code % 8)

	@staticmethod
	def _select_background_16(code, offsets=(40, 100)):
		return offsets[code//8] + (code % 8)

	_select_foreground_256 = b'38;5'
	_select_background_256 = b'48;5'
	_select_foreground_rgb = b'38;2'
	_select_background_rgb = b'48;2'

	# Pairs are of the form: (Initiate, Terminate)
	_style_codes = {
		'bold': (b'1', b'22'),
		'feint': (b'2', b'22'),
		'blink': (b'5', b'25'),
		'rapid': (b'6', b'25'),

		'italic': (b'3', b'23'),
		'underline': (b'4', b'24'),
		'inverse': (b'7', b'27'),
		'invisible': (b'8', b'28'),
		'cross': (b'9', b'29'),

		# Does not appear to be commonly supported.
		'double-underline': (b'21', b'24'),
		'frame': (b'51', b'54'),
		'encircle': (b'52', b'54'),
		'overline': (b'53', b'55'),
	}

	escape_sequence = _csi_init

	@staticmethod
	@functools.lru_cache(32)
	def translate(spoint, point):
		return (point[0] + spoint[0], point[1] + spoint[1])

	def __init__(self, encoding='utf-8'):
		self.dimensions = (None, None)
		self.width = self.height = None
		self._context_text_color = -1024
		self._context_cell_color = -1024
		self._context_cursor = (0, 0)

		codec = encoders(encoding)
		self.encoding, self._encoder, self._encode, self._cached_encode = codec
		self.encode = codec[-1]

	def adjust(self, position, dimensions):
		"""
		# Adjust the position and dimensions of the rendering context.
		"""
		self.point = position
		self.dimensions = dimensions
		# track relative position for seek operations
		self.width, self.height = dimensions

	@property
	def _context_traits(self):
		return (self._context_text_color, self._context_cell_color, 0)

	def context_set_position(self, point:typing.Tuple[int, int]):
		"""
		# Designate the absolute positioning of the character matrix.
		# Appropriate interface to use to set &self.point.
		"""
		self.point = point
		return self

	def context_set_dimensions(self, dimensions):
		"""
		# Designate the width and height of the character matrix being targeted.
		# Initializes &Context.dimensions, &width, and &height.
		"""
		self.width, self.height = dimensions
		self.dimensions = dimensions
		return self

	def context_set_text_color(self, color_id):
		"""
		# Configure the default text color.
		# Used by &reset_text and &reset_text_color.
		"""
		self._context_text_color = color_id
		return self

	def context_set_cell_color(self, color_id):
		"""
		# Configure the default cell color.
		# used by &reset_text and &reset_cell_color.
		"""
		self._context_cell_color = color_id
		return self

	def _csi(self, terminator, *parts):
		# Control Sequence Introducer
		return self._csi_init + self._join(parts) + terminator
	escape = _csi

	def _osc(self, *parts):
		# Operating System Command
		return self._osc_init + self._join(parts) + self._osc_terminate

	def _csi_filter_empty(self, terminator, *parts):
		"""
		# &escape variant that returns an empty string when &parts is empty.
		"""
		if parts == ():
			return b''
		return self.escape_sequence + self._join(parts) + terminator

	def draw_unit_vertical(self, character):
		e = self.encode
		if not character:
			return b''

		c = e(character)
		c += self.seek_next_column()

		return c

	def draw_unit_horizontal(self, character):
		return self.encode(character)

	def draw_segment_vertical(self, unit, length):
		e = self.encode
		h, v = self._context_cursor
		h -= self.point[0]
		v -= self.point[1]

		c = e(unit)
		return b''.join([c + self.seek_absolute((h, v+i)) for i in range(length)])

	def draw_segment_horizontal(self, unit, length):
		return self.draw_unit_horizontal(unit) * length

	@functools.lru_cache(32)
	def _color_selector(self, target, color_code,
			targets_rgb={True:_select_foreground_rgb,False:_select_background_rgb},
			targets_256={True:_select_foreground_256,False:_select_background_256},
			str=str,
		):
		"""
		# Color code cache. Values beyond 24-bit are ignored. Negatives select from traditional palettes.
		"""
		e = self.encode

		if color_code >= 0:
			r = (color_code >> 16) & 0xFF
			g = (color_code >> 8) & 0xFF
			b = (color_code >> 0) & 0xFF

			return (targets_rgb[target], b';'.join(map(e, (r, g, b))))
		else:
			color_code = -color_code
			if color_code <= 256:
				# 1-256 inclusive; 0 (-0) is recognized as a 24-bit color.
				return (targets_256[target], self.encode(color_code-1))
			elif color_code == 1024:
				# Special code for defaults.
				if target:
					return (self.encode(39),)
				else:
					return (self.encode(49),)
			else:
				# Sixteen colors offset at 512.
				color_code -= 512
				assert color_code < 16

				if target:
					return (self.encode(self._select_foreground_16(color_code)),)
				else:
					return (self.encode(self._select_background_16(color_code)),)

	def set_cell_color(self, color:int) -> bytes:
		"""
		# Construct the escape sequence for selecting a different cell (background) color.
		"""
		return self._csi(b'm', *self._color_selector(False, color))

	def set_text_color(self, color:int) -> bytes:
		"""
		# Construct the escape sequence for selecting a different text (foreground) color.
		"""
		return self._csi(b'm', *self._color_selector(True, color))

	def reset_text_color(self) -> bytes:
		"""
		# Use the text color configured with &context_set_text_color.
		"""
		return self._csi(b'm', *self._color_selector(True, self._context_text_color))

	def reset_cell_color(self) -> bytes:
		"""
		# Use the cell color configured with &context_set_cell_color.
		"""
		return self._csi(b'm', *self._color_selector(False, self._context_cell_color))

	def reset_colors(self) -> bytes:
		"""
		# Using the cell and text colors stored on the Context, &self, construct
		# a sequence to instruct the terminal to use those colors.
		"""
		return self._csi(b'm', *(
			self._color_selector(True, self._context_text_color) + \
			self._color_selector(False, self._context_cell_color)
		))

	def reset_text(self) -> bytes:
		"""
		# Reset text traits and colors.
		"""
		return self._csi(b'm', *(
			(b'0',) + \
			self._color_selector(True, self._context_text_color) + \
			self._color_selector(False, self._context_cell_color)
		))

	def transition(self,
			leading:RenderParameters,
			following:RenderParameters,
			style_codes=_style_codes,
		) -> typing.Iterator[bytes]:
		"""
		# Construct escape sequences necessary to transition the SGR state from
		# &leading to &following.

		# Used by &render to minimize the emitted sequences for displaying a &.core.Phrase.
		"""

		if leading == following:
			# Identical; no transition.
			return

		# text color
		current = leading[0]
		target = following[0]
		if current != target:
			yield from self._color_selector(True, target)

		# cell color
		current = leading[1]
		target = following[1]
		if current != target:
			yield from self._color_selector(False, target)

		# text traits
		current = leading[2]
		target = following[2]
		if current != target:
			kept = current & target # traits to ignore

			# Must precede newtraits.
			cleartraits = target.__class__(kept ^ current)
			for x in cleartraits:
				yield style_codes[x][1]

			# Must follow cleartraits as some trait exits apply to multiple
			# enters. (double-underline and underline for instance)
			newtraits = target.__class__(kept ^ target)
			for x in newtraits:
				yield style_codes[x][0]

	def draw_words(self, phraseword, control_map=control_table):
		"""
		# Translate the given &phraseword with &control_map and encode it
		# with the Context's configured encoding.
		"""

		return self._encode(phraseword.translate(control_map))

	def render(self, phrase, rparams:RenderParameters=None) -> typing.Iterator[bytes]:
		"""
		# Render the given &phrase for display on the terminal.
		# Unlike most Context methods, &render returns an iterator
		# producing the sequences necessary to represent the phrase.

		# [ Parameters ]
		# /phrase/
			# The sequence of words to render. The text of the word must
			# be retrievable at (index)`1` and the rendering parameters
			# must be retrievable at (index)`2`.
		# /rparams/
			# &rparams is a triple used by phrasewords to describe the text's properties.
			# If &None is given, the configured text and cell colors are used for
			# identifying the initial transition into the Phrase.
			# When rendering multiple &Phrase instances, the final triple of a phrase can be
			# provided to the next render call to make minimal transitions.
		"""

		_csi = self._csi_filter_empty
		encoding = self.encoding
		e = self.encode
		transition = self.transition

		if rparams is None:
			last = self._context_traits
		else:
			last = rparams

		for words in phrase:
			to = words[2]
			yield _csi(b'm', *transition(last, to))
			last = to

			yield e(words[1])

	def print(self,
			phrases:Page,
			cellcounts:typing.Sequence[int],
			dirtycells:typing.Sequence[int]=(),
			zip=zip
		) -> typing.Iterator[bytes]:
		"""
		# Print the page of phrases using &render.

		# Unlike most Context methods, &print returns an iterator
		# producing the sequences necessary to represent the phrase.

		# Text properties will be unconditionally reset, and lines will
		# be presumed dirty causing a following erase to be emitted after
		# the phrase is rendered.
		"""

		rst = self.reset_text()
		nl = self.seek_next_line
		erase = self.erase
		render = self.render
		w = self.width

		yield rst

		for x, cc in zip(phrases, cellcounts):
			if cc > w:
				yield from render(x.rstripcells(cc - w))
				yield rst + nl()
			else:
				yield from render(x)
				yield rst + erase(w - cc) + nl()

	def blank(self, count=1):
		"""
		# Generate sequence for writing blank characters.
		# Semantically, this should be equivalent to writing spaces.
		"""
		return self._csi(self.encode(count) + b'@')

	def clear_line(self, lineno):
		return self.seek_line(lineno) + self.clear_current_line()

	def clear_to_line(self, n = 1):
		return self._csi(self.encode(n) + b'J')

	def clear_to_bottom(self):
		return self._csi(b'J')

	def clear_before_cursor(self):
		return self._csi_sequence + b'\x31\x4b'

	def clear_after_cursor(self):
		return self._csi_sequence + b'\x4b'

	def clear_current_line(self):
		return self.clear_before_cursor() + self.clear_after_cursor()

	def deflate_horizontal(self, size):
		return self._csi(b'P', self.encode(size))

	def deflate_vertical(self, size):
		return self._csi(b'M', self.encode(size))

	def inflate_horizontal(self, size):
		return self._csi(b'@', self.encode(size))

	def inflate_vertical(self, size):
		return self._csi(b'L', self.encode(size))

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
		# Clear the area according to its configured width and default text properties.

		# Text properties will be reset; the cell color configured on the context will be used.
		"""
		width = self.width

		init = self.seek_absolute(self.translate(self.point, (0, 0)))
		init += self.reset_text() # Make sure cell color is correct.

		clearline = self.erase(width)
		nl = self.seek_vertical_relative(1)

		return init + (self.height * (clearline + nl))

	def erase(self, count):
		"""
		# Erase the given &count of characters before or after the cursor.
		# Positive counts clear cells after the cursor, negative clears cells before the cursor.

		# This should respect the current cell color, but not traits like underline.
		"""

		if count > 0:
			return self._csi(b'X', self.encode(count))
		elif count < 0:
			return self._csi(b'P', self.encode(-count))
		else:
			return b''

	def seek_absolute(self, coordinates) -> bytes:
		"""
		# Primitive absolute seek; Context cursor poisition is *not* updated.
		"""
		h, v = coordinates
		return self._csi(b'H', self.encode(v+1), self.encode(h+1))

	def seek_horizontal_relative(self, cells) -> bytes:
		"""
		# Primitive relative seek; Context cursor position is *not* updated.
		"""
		if cells < 0:
			return self._csi(b'D', self.encode(-cells))
		elif cells > 0:
			return self._csi(b'C', self.encode(cells))
		else:
			return b''

	def seek_vertical_relative(self, cells) -> bytes:
		"""
		# Primitive relative seek; Context cursor position is *not* updated.
		"""
		if cells < 0:
			return self._csi(b'A', self.encode(-cells))
		elif cells > 0:
			return self._csi(b'B', self.encode(cells))
		else:
			return b''

	def seek_first(self):
		"""
		# Seek the first cell in the Context.

		# Requires prior &context_set_position.
		"""
		return self.seek((0,0))

	def seek_last(self):
		"""
		# Seek the last cell in the Context.

		# Requires prior &context_set_dimensions.
		"""
		h, v = self.dimensions
		return self.seek((h-1, v-1))

	def seek(self, point):
		"""
		# Seek to the point relative to the area and store the point on the context.
		"""
		self._context_cursor = point
		return self.seek_absolute(self.translate(self.point, point))

	def tell(self):
		return self._context_cursor

	def seek_bottom(self):
		"""
		# Seek to the last row of the area and the first column.
		"""
		return self.seek((0, self.height-1))

	def seek_start_of_line(self):
		"""
		# Seek to the start of the line.
		"""
		return self.seek((0, self._context_cursor[1]))

	def seek_line(self, lineno):
		"""
		# Seek to the beginning of a particular line number.
		"""
		return self.seek((0, lineno))

	def seek_next_line(self):
		"""
		# Seek beginning of next line.
		"""
		return self.seek((0, self._context_cursor[1]+1))

	def seek_next_column(self):
		h, v = self._context_cursor
		return self.seek((h, v+1))

	def seek_relative(self, rcoords):
		"""
		# Seek the relative coordinates and update the Context's cursor.
		"""
		h, v = rcoords
		self._context_cursor = (h+self._context_cursor[0], v+self._context_cursor[1])
		return self.seek_horizontal_relative(h) + self.seek_vertical_relative(v)

class Screen(Context):
	"""
	# Matrix &Context bound to the first column and row.

	# Screens are given a slightly wider scope than &Context and provides
	# access to some configuration options that are not always maintained
	# for the duration of the process.
	"""
	point = (0,0)

	def set_window_title_text(self, title):
		"""
		# Instruct the emulator to use the given title for the window.
		# The given &title should be plain text and control characters will be translated.
		"""
		etitle = self._encoder(title.translate(self.control_table))
		return self._csi_character + b']2;' + etitle + b'\x07'

	def reset(self):
		"""
		# Construct a soft terminal reset.
		"""
		return self._csi(b'!p')

	def set_scrolling_region(self, top, bottom):
		"""
		# Confine the scrolling area to the given rows.
		"""
		return self._csi(b'r', top+1, bottom+1)

	def reset_scrolling_region(self):
		"""
		# Set the scrolling region to the entire screen.
		"""
		return self._csi(b'r')

	def store_cursor_location(self):
		"""
		# Emulator level cursor storage.
		"""
		return self.escape_character + b'7' # Also, CSI s, but maybe less portable.

	def restore_cursor_location(self):
		"""
		# Restore a previously stored cursor location.
		"""
		return self.escape_character + b'8' # Also, CSI u, but maybe less portable.

	def scroll_up(self, count):
		"""
		# Adjust the scroll region's view by scrolling up &count rows.
		"""
		return self._csi(b'S', count)

	def scroll_down(self, count):
		"""
		# Adjust the scroll region's view by scrolling down &count rows.
		"""
		return self._csi(b'T', rows)

	def adjust(self, point, dimensions):
		"""
		# Set the screen's configured dimensions.

		# This method should be called upon receiving SIGWINCH and after
		# creating an instance. However, it is not mandatory for many operations
		# to know the screen size.
		"""
		if point != (0, 0):
			raise ValueError("screen contexts must be positioned at zero")

		return super().adjust(point, dimensions)

	def clear(self):
		return self.reset_text() + self._csi(b'H') + self._csi(b'2J')
