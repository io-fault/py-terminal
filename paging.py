"""
# Classes for managing page display state.
"""
import functools

from . import text

class Unit(object):
	"""
	# A unit of text be drawn on an area; styled and width clipping functionality.

	# Changes in text length is tracked so that proper erase instructions can be generated.
	"""
	__slots__ = ('text', 'display', 'clipping', 'clipped', 'change', 'length')

	def __init__(self, text=()):
		self.text = text
		self.length = sum(map(text.cells, (x[0] for x in self.text)))
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

	def clip(self, offset, width, len=len, range=range, cells=text.cells):
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
	# A sequence of lines drawn into a &.canvas.Context.
	"""

	def __init__(self, area, Sequence=list, Line=Unit):
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
