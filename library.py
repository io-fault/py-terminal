"""
The terminal I/O interfaces. The module consists of four conceptual areas: input, output,
settings management, and control management.

The input portions cover the data structures used to represent character (key) events, &Character,
and the function used to construct them from an arbitrary bytes stream.

The output portions are primarily two classes used to render the terminal control codes
for a particular operation, essentially high-level tput. &Display for the entire terminal
screen and &Area for displaying to parts of the screen.

Settings management is covered with a few functions to configure the terminal in raw mode
and store and restore the settings themselves.

The control portion keeps state about the process-local controller of the terminal and any
requests for control. This is a local version of the process signals used by sessions to
manage terminal access for concurrent jobs.
"""
import sys
import os
import tty
import termios
import fcntl
import array
import locale
import contextlib
import collections
import operator
import functools
import itertools

from . import core
from . import device

Character = core.Character
Modifiers = core.Modifiers
construct_character_events = device.construct_character_events

def restore_at_exit(path = device.path):
	"""
	Save the Terminal state and register an atexit handler to restore it.
	"""
	import atexit

	with open(path, mode='r+b') as tty:
		def _restore_terminal(path = path, terminal_state = termios.tcgetattr(tty.fileno())):
			# in case cursor was hidden
			with open(path, mode='r+b') as f:
				f.write(b'\x1b[?12l\x1b[?25h') # normalize cursor
				termios.tcsetattr(f.fileno(), termios.TCSADRAIN, terminal_state)

	atexit.register(_restore_terminal)

def request_control(controller):
	"""
	Request exclusive control of the terminal.
	Often used as a effect of to a SIGTIN or SIGTOUT signal for the would be foreground.

	Primarily used by shell implementations and multi-facet processes.
	"""

def residual_control(controller):
	"""
	Identify the controller as residual having the effect that it registers itself
	as taking control after outstanding requests have relinquished their ownership.
	"""

def scale(n, target = (1, 100), origin = (0, 0xFFFFFFFF), divmod = divmod):
	"""
	Given a number, target range, and a origin range. Project the number
	onto the target range so that the projected number
	is proportional to the target range with respect to the number's
	relative position in the origin range. For instance::

	>>> scale(5, target=(1,100), origin=(1,10))
	(50, 0, 9)

	The return is a triple: (N, remainder, origin[1] - origin[0])
	Where the second item is the remainder with the difference between the source
	range's end and beginning.
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

Display = device.Display

class Area(Display):
	"""
	A Display class whose seek operations are translated according to the configured position.
	"""

	def update(self, position, dimensions):
		"""
		Update the position of the area.
		"""
		self.point = position
		self.dimensions = dimensions
		# track relative position for seek operations
		self.width, self.height = dimensions

	def seek(self, point):
		"""
		Seek to the point relative to the area.
		"""
		return self.seek_absolute(self.translate(self.point, point))

	def seek_start_of_line(self):
		"""
		Seek to the start of the line.
		"""
		return super().seek_start_of_line() + self.seek_horizontal_relative(self.point[0] - 1)

	def seek_bottom(self):
		"""
		Seek to the last row of the area and the first column.
		"""
		return self.seek((0, self.height-1))

	@staticmethod
	@functools.lru_cache(32)
	def translate(spoint, point):
		return (point[0] + spoint[0], point[1] + spoint[1])

class Line(object):
	"""
	A line be drawn on an area; styled and width clipping functionality.
	"""
	__slots__ = ('text', 'overlay', 'display', 'clipped', 'length')

	def __init__(self, text, overlay = ()):
		self.text = text
		self.overlay = overlay
		self.length = sum(map(len, (x[0] for x in self.text)))
		self.clipped = 0
		self.display = (text, overlay)

	def clip(self, width):
		"""
		Clip the text according to the given width.
		Used to prepare the (display) line for rendering.

		Can be used multiple times in order to reflect area changes.
		"""
		s = 0
		i = 0
		l = 0

		for i in range(len(self.text)):
			l = len(self.text[i][0])
			s += l
			if s > width:
				break
		else:
			# text length does not exceed width
			self.clipped = 0
			return 0

		# trim the excess off of the i'th element
		trim, *styling = self.text[i]
		excess = s - width

		t = list(self.text[:i])
		trimmed = trim[:len(trim)-excess]

		styling.insert(0, trimmed)
		t.append(tuple(styling))

		self.display = (t, self.overlay)

		self.clipped = excess
		return excess

	def render(self, area, map = itertools.starmap):
		"""
		Render the line according to the given area.

		The rendered string should be clipped *ahead of time* to restrict
		its width.
		"""
		text, overlay = self.display
		data = b''

		if text:
			data += b''.join(map(area.style, text))

			display_length = - (self.length - self.clipped)
			if display_length:
				data += area.seek_horizontal_relative(display_length)

		for relative_offset, otext in overlay:
			data += area.seek_horizontal_relative(relative_offset)
			data += b''.join(map(area.style, otext))

		data += area.seek_start_of_next_line()

		return data
