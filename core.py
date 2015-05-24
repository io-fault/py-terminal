"""
Primarily classes for representing input into a terminal.
"""
import functools
import unicodedata

# process global state for managing the controlling [logical] process
__control_requests__ = []
__control_residual__ = []

class Character(tuple):
	"""
	A single characeter from input event from a terminal device.
	"""
	__slots__ = ()

	classifications = (
		'control',
		'manipulation',
		'navigation',
		'function',
	)

	@property
	def type(self):
		"""
		The classification of the character with respect to the source.
		"""
		return self[0]

	@property
	def string(self):
		"""
		The literal characters, if any, of the event. Used for forwarding key events.
		"""
		return self[1]

	@property
	def identity(self):
		"""
		A name for the &string contents; often the appropriate way to process
		character events.
		"""
		return self[2]

	@property
	def modifiers(self):
		"""
		The identified &Modifiers of the Character.
		"""
		return self[3]

	def combining(self):
		"""
		The sequence of combining character data.

		Items are zero if there is no combining character at that index.
		"""
		return map(unicodedata.combining, self[1])

class Modifiers(int):
	"""
	Bitmap of modifiers with an single imaginary numeric modifier.
	"""
	sequence = (
		'control',
		'shift',
		'meta',
	)
	bits = {
		k: 1 << i for k, i in zip(sequence, range(len(sequence)))
	}

	@property
	def none(self):
		return not (self & 0b111)

	@property
	def control(self):
		return (self & 0b001)

	@property
	def meta(self):
		"Often the alt or option key."
		return (self & 0b010)

	@property
	def shift(self):
		"""
		Shift key was detected.
		"""
		return (self & 0b100)

	@property
	def imaginary(self):
		"""
		An arbitrary number designating an imaginary modifier.
		Defaults to zero.
		"""
		return self >> 3

	@classmethod
	@functools.lru_cache(9)
	def construct(Class, bits = 0, control = False, meta = False, shift = False, imaginary = 0):
		mid = imaginary << 3
		mid |= bits

		if control:
			mid |= Class.bits['control']

		if meta:
			mid |= Class.bits['meta']

		if shift:
			mid |= Class.bits['shift']

		return Class(mid)

class Point(tuple):
	"""
	A pair of integers describing a position on screen.
	The point may be relative or absolute; the usage context defines its meaning.
	"""
	__slots__ = ()

	@property
	def x(self):
		return self[0]

	@property
	def y(self):
		return self[1]

	@classmethod
	def construct(Class, *points):
		return Class(points)

class Position(object):
	"""
	Relative position from a particular point, &datum.

	&offset specifies the relative offset to the datum,
	and &magnitude defines the size, upper bounds.

	Constraints are not enforced in order to allow the user to leverage the overflow.
	"""
	__slots__ = ('datum', 'offset', 'magnitude')

	@property
	def minimum(self):
		return self.datum

	@property
	def maximum(self):
		return self.datum + self.magnitude

	def __init__(self):
		self.datum = 0 # physical position
		self.offset = 0 # offset from datum (0 is minimum)
		self.magnitude = 0 # offset from datum (maximum of offset)

	def get(self):
		"""
		Get the absolute position.
		"""
		return self.datum + self.offset

	def set(self, position):
		"""
		Set the offset relative to the datum using the given position.
		"""
		new = position - self.datum
		change = self.offset - new
		self.offset = new
		return change

	def configure(self, datum, magnitude, offset = 0):
		"""
		Initialize the values of the position.
		"""
		self.datum = datum
		self.magnitude = magnitude
		self.offset = offset

	def update(self, quantity):
		"""
		Update the offset by the given quantity.
		Negative quantities move the offset down.
		"""
		self.offset += quantity

	def clear(self):
		"""
		Reset the position state to a zeros.
		"""
		self.__init__()

	def zero(self):
		"""
		Zero the &offset and &magnitude of the position.

		The &datum is not changed.
		"""
		self.magnitude = 0
		self.offset = 0

	def move(self, location = 0, perspective = 0):
		"""
		Move the position relatively or absolutely.

		Perspective is like the whence parameter, but uses slightly different values.

		-1 is used to move the offset relative from the end.
		+1 is used to move the offset relative to the beginning.
		Zero moves the offset relatively with &update.
		"""
		if perspective == 0:
			self.offset += location
			return location

		if perspective > 0:
			offset = 0
		else:
			# negative
			offset = self.magnitude

		offset += (location * perspective)
		change = self.offset - offset
		self.offset = offset

		return change

	def contract(self, offset, quantity):
		"""
		Adjust, decrease, the magnitude relative to a particular offset.
		"""
		self.magnitude -= quantity # positives decrement, and negatives expand

		# if the contraction occurred at or before the position,
		# move the offset back as well.
		if offset <= self.offset:
			self.offset -= quantity

	def expand(self, offset, quantity):
		"""
		Adjust, increase, the magnitude relative to a particular offset.
		"""
		return self.contract(offset, -quantity)

	def relation(self):
		"""
		Return the relation of the offset to the datum and the magnitude.
		"""
		o = self.offset
		if o < 0:
			return -1
		elif o > self.magnitude:
			return 1
		else:
			return 0 # within bounds

	def snapshot(self):
		"""
		Calculate and return the absolute position as a triple.
		"""
		start = self.datum
		offset = start + self.offset
		stop = start + self.magnitude
		return (start, offset, stop)

class Vector(object):
	"""
	A pair of positions describing an area and point.
	"""
	def __len__(self):
		return 2

	def __getitem__(self, index):
		if index:
			if index != 1:
				raise IndexError("terminal vectors only have two entries")
			return self.vertical
		return self.horizontal

	def clear(self):
		self.horizontal.clear()
		self.vertical.clear()

	def move(self, x, y):
		"""
		Move the positions relative to their current state.
		"""
		self.horizontal.update(x)
		self.vertical.update(y)

	def get(self):
		"""
		Get the absolute horizontal and vertical position as a 2-tuple.
		"""
		return Point.construct(self.horizontal.get(), self.vertical.get())

	def __init__(self):
		self.horizontal = Position()
		self.vertical = Position()

	def snapshot(self):
		return (self.horizontal.snapshot(), self.vertical.snapshot())
