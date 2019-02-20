"""
# The terminal I/O interfaces. The module consists of four conceptual areas: input, output,
# settings management, and control management.

# The input portions cover the data structures used to represent character (key) events, &Character,
# and the function used to construct them from an arbitrary bytes stream.

# The output portions are primarily two classes used to render the terminal control codes
# for a particular operation, essentially high-level tput. &Display for the entire terminal
# screen and &Area for displaying to parts of the screen.

# Settings management is covered with a few functions to configure the terminal in raw mode
# and store and restore the settings themselves.

# The control portion keeps state about the process-local controller of the terminal and any
# requests for control. This is a local version of the process signals used by sessions to
# manage terminal access for concurrent jobs.

# Coloring:
	# /textcolor/
		# Foreground color.
	# /cellcolor/
		# Uppermost background color. (opacity mixing?)
	# /foreground/
		# Default text color.
	# /background/
		# Default cell color.
"""
import sys
import os
import tty
import termios
import fcntl
import array
import contextlib
import collections
import operator
import functools
import itertools

from . import core
from . import device
from .text import cells

Point = core.Point
Position = core.Position
Vector = core.Vector

pastels = {
	'purple': 0x875fff,
	'blue': 0x0087d7,
	#'cyan': 0x6d889a, metallic green
	'cyan': 0x6b9aea,
	'green': 0x77DD77,
	'magenta': 0xF49AC2,
	'orange': 0xFFB347,
	'pink': 0xFFD1DC,
	'violet': 0xCB99C9,
	'yellow': 0xFDFD96,
	'red': 0xFF6961,
	'gray': 0xCFCFC4,
	#'blue-green': 0x0D98BA,
	#'pink': 0xDEA5A4, dark pink
	#'red': 0xD75F5F, dark red
}

theme = {
	'number': 'blue',
	'text': 'gray',
	'core': 'purple',
	'date': 'yellow',
	'time': 'red',
	'timestamp': 'orange',
}

def restore_at_exit(path = device.path):
	"""
	# Save the Terminal state and register an atexit handler to restore it.

	# Called once when the process is started to restore the terminal state.
	"""
	import atexit

	with open(path, mode='r+b') as tty:
		def _restore_terminal(path = path, terminal_state = termios.tcgetattr(tty.fileno())):
			d = device.Display()

			# in case cursor was hidden
			with open(path, mode='r+b') as f:
				# bit of a hack and assumes no other state changes need to occur.
				resets = b'\x1b[?12l\x1b[?25h' # normalize cursor
				resets += d.disable_mouse()
				resets += d.enable_line_wrap()
				f.write(resets)
				termios.tcsetattr(f.fileno(), termios.TCSADRAIN, terminal_state)

	atexit.register(_restore_terminal)

def scale(n, target = (1, 100), origin = (0, 0xFFFFFFFF), divmod = divmod):
	"""
	# Given a number, target range, and a origin range. Project the number
	# onto the target range so that the projected number
	# is proportional to the target range with respect to the number's
	# relative position in the origin range. For instance::

	>>> scale(5, target=(1,100), origin=(1,10))
	(50, 0, 9)

	# The return is a triple: (N, remainder, origin[1] - origin[0])
	# Where the second item is the remainder with the difference between the source
	# range's end and beginning.
	"""
	# The relative complexity of this sequence of computations is due to the
	# need to push division toward the end of the transformation sequence. That
	# is, greater clarity can be achieved with some reorganization, but this
	# would require the use of floating point operations, which is not desirable
	# for some use cases where "perfect" scaling (index projections) is desired.

	dx, dy = target
	sx, sy = origin
	# source range
	# (this is used to adjust 'n' relative to zero, see 'N' below)
	sb = sy - sx
	# destination range
	# (used to map the adjusted 'n' relative to the destination)
	db = dy - dx
	# bring N relative to *beginning of the source range*
	N = n - sx
	# magnify N to the destination range
	# divmod by the source range to get N relative to the
	# *the destination range*
	n, r = divmod(N * db, sb)
	# dx + N to make N relative to beginning of the destination range
	return dx + n, r, sb

def offsets(text_sequence, *indexes, iter=iter, len=len, next=next, cells=cells):
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

Display = device.Display
class Area(Display):
	"""
	# A Display class whose seek operations are translated according to the configured position.
	"""

	def adjust(self, position, dimensions):
		"""
		# Adjust the position of the area.
		"""
		self.point = position
		self.dimensions = dimensions
		# track relative position for seek operations
		self.width, self.height = dimensions

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

	def seek(self, point):
		"""
		# Seek to the point relative to the area.
		"""
		return self.seek_absolute(self.translate(self.point, point))

	def seek_start_of_line(self):
		"""
		# Seek to the start of the line.
		"""
		return super().seek_start_of_line() + self.seek_horizontal_relative(self.point[0])

	def seek_bottom(self):
		"""
		# Seek to the last row of the area and the first column.
		"""
		return self.seek((0, self.height-1))

	def erase(self, times=1, background=None):
		if background is None:
			return super().erase(times)
		else:
			# fill with colored spaces if the background is not None.
			return self.style(' ' * times, styles=(), cellcolor=background)

	@staticmethod
	@functools.lru_cache(32)
	def translate(spoint, point):
		return (point[0] + spoint[0], point[1] + spoint[1])

class Unit(object):
	"""
	# A unit of text be drawn on an area; styled and width clipping functionality.

	# Changes in text length is tracked so that proper erase instructions can be generated.
	"""
	__slots__ = ('text', 'display', 'clipping', 'clipped', 'change', 'length')

	def __init__(self, text = ()):
		self.text = text
		self.length = sum(map(cells, (x[0] for x in self.text)))
		self.clipping = (0, None)
		self.change = self.clipped = 0
		self.display = tuple(text)

	def __iter__(self, iter=iter):
		"""
		# Returns an iterator to the display fragments.
		"""
		return iter(self.display)

	def __getitem__(self, item):
		"""
		# Get a portion of the Unit respecting the clipping of the unit.
		"""
		pass

	def clear(self):
		"""
		# Clear the line leaving the change data in order to allow subsequent renders to
		# properly clear excess and outdated display.
		"""

		change = self.change - self.length
		self.__init__()
		self.change = change

		return self

	def update(self, text):
		current_length = self.length
		self.text = text

		self.clip(*self.clipping)
		# use display length
		self.change = (self.length - current_length)
		return self

	def clip(self, offset, width, len=len, range=range, cells=cells):
		"""
		# Clip the text according to the given width and offset.
		# Used to prepare the (display) line for rendering.

		# Can be used multiple times in order to reflect area changes.
		"""

		self.clipping = (offset, width)
		text = self.text

		if width is None:
			self.clipped = 0
			self.display = tuple(text)
			self.length = sum(map(cells, (x[0] for x in self.text)))
			return self

		s = 0
		i = 0
		l = 0

		ri = range(len(text))
		for i in ri:
			l = cells(text[i][0])
			s += l
			if s > width:
				break
		else:
			# text length does not exceed width
			self.clipped = 0
			self.length = s
			self.display = tuple(text)
			return self

		# clipping occurred, so length is the full width
		self.length = width

		# trim the excess off of the i'th element
		trim, *styling = text[i]
		excess = s - width

		t = list(text[:i])
		trimmed = trim[:len(trim)-excess]

		styling.insert(0, trimmed)
		t.append(tuple(styling))

		self.display = tuple(t)

		self.clipped = excess

		return self

	def render(self, area, foreground=None, background=None):
		"""
		# Render the line according to the given area.

		# The rendered string should be clipped *ahead of time* to restrict
		# its width.

		# If there was any noted length change, it will be cleared by &render.
		"""

		text = self.display
		width = area.width
		length = self.length

		if text:
			data = area.renderline(text, background=background)
		else:
			data = b''

		if self.change < 0:
			# the text rendered before was longer than it is now
			# erase the difference after drawing
			data += area.erase(-self.change, background=background)
			self.change = 0
		elif length < width and background is not None:
			# fill remaining cells with background color.
			data += area.erase(width - length, background=background)

		return data
Line = Unit # Compat

class Overwrite(object):
	"""
	# Objects used in conjunction with &Line to writing combining characters.
	"""
	__slots__ = ('characters',)

	def __init__(self, characters):
		self.characters = characters

	def render(self):
		for relative_offset, otext in overlay:
			yield area.seek_horizontal_relative(relative_offset)
			yield b''.join(map(area.style, otext))

class Pattern(object):
	"""
	# Overwrite that is based on a frequency pattern.
	"""
	__slots__ = ('characters', 'style', 'color')

	def __init__(self, characters, style, color):
		self.characters = characters
		self.style = style
		self.color = color

	def render(self, area, frequency, *ranges):
		"""
		# Render the pattern for overwriting on to an existing line.
		"""
		overwrite = area.style(self.characters, self.style, self.color)

		if frequency == 1:
			initial = area.seek_horizontal_relative(start) + overwrite
			yield initial

			m = (stop - start) - 1
			if m > 0:
				move = area.seek_horizontal_relative(1)
				yield (move + overwrite) * m
		else:
			for start, stop in ranges:
				for i in range(start, stop, frequency):
					yield area.seek_horizontal_relative(i) + overwrite

class View(object):
	"""
	# A sequence of lines drawn into an &Area.
	"""

	def __init__(self, area, Sequence = list, Line = Line):
		self.area = area
		self.sequence = Sequence()
		self.Line = Line
		self.width = 0
		self.height = 0

		# Support area abstraction
		self.erase = self.area.erase
		self.renderline = functools.lru_cache(128)(area.renderline)

		# default text and background color
		self.background = None
		self.foreground = None

	def scroll(self, quantity):
		"""
		# Scroll the number of lines off-screen and add empty ones to the
		# other end of the sequence.

		# This method is used to implement relatively efficient scrolling.
		"""
		if quantity < 0:
			# move lines down
			clears = (0, -quantity)
			start = (self.height + quantity) - 1
			stop = -1
			dir = -1
		else:
			# move lines up
			clears = (self.height - quantity, self.height)
			start = quantity
			stop = self.height
			dir = 1

		for i in range(start, stop, dir):
			x = self.sequence[i]
			x.update(self.sequence[i - quantity].text)

		# clear the excess
		for i in range(*clears):
			self.sequence[i].clear()

	def lines(self, start, stop = None):
		"""
		# Return an iterator to a slice of the lines grouped with the relative line number.
		"""
		l = len(self.sequence)
		end = min(l, stop or l)
		for i in range(start, end):
			yield self.sequence[i]

	def clear(self, start = 0, stop = None):
		"""
		# Clear the view by removing the contents of the lines.
		"""
		for x in self.lines(start, stop):
			x.update(())

	def adjust(self, point, dimensions):
		"""
		# Update the position and the dimensions of the view.

		# Doing so causes lines to be clipped according to the width.
		"""
		lines = self.sequence
		self.area.adjust(point, dimensions)

		w, h = dimensions

		d = h - self.height
		if d < 0:
			del self.sequence[h:]
		elif d > 0:
			for i in range(d):
				self.sequence.append(self.Line())

		self.width, self.height = w, h

		# clip lines to width
		for x in self.lines(0):
			x.clip(0, w)

	def update(self, start, stop, lines):
		"""
		# Update the line range in the view.
		"""
		for x, l in zip(self.lines(start, stop), lines):
			x.update(l)

	def render(self, start=0, stop=None):
		"""
		# Render all the lines in the sequence into the area.
		"""
		a = self.area
		yield a.seek((0, start))
		for x in self.sequence[start:stop]:
			yield x.render(self, self.foreground, self.background)
			yield a.seek_start_of_next_line()

	draw = render # depracate
