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
	A pair of integers describing a position on screen; units are in "cells".
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
		Set the absolute position.

		Calculates a new &offset based on the absolute &position.
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

	def limit(self, minimum, maximum):
		"""
		Apply the minimum and maximum limits to the Position's absolute values.
		"""
		l = [
			minimum if x < minimum else (
				maximum if x > maximum else x
			)
			for x in self.snapshot()
		]
		self.restore(l)

	def snapshot(self):
		"""
		Calculate and return the absolute position as a triple.
		"""
		start = self.datum
		offset = start + self.offset
		stop = start + self.magnitude
		return (start, offset, stop)

	def restore(self, snapshot):
		"""
		Restores the given snapshot.
		"""
		self.datum = snapshot[0]
		self.offset = snapshot[1] - snapshot[0]
		self.magnitude = snapshot[2] - snapshot[0]

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

	def constrain(self):
		"""
		Adjust the offset to be within the bounds of the magnitude.
		Returns the change in position; positive values means that
		the magnitude was being exceeded and negative values
		mean that the minimum was being exceeded.
		"""
		o = self.offset
		if o > self.magnitude:
			self.offset = self.magnitude
		elif o < 0:
			self.offset = 0

		return o - self.offset

	def collapse(self):
		"""
		Move the origin to the position of the offset and zero out magnitude.
		"""
		o = self.offset
		self.datum += o
		self.offset = self.magnitude = 0
		return o

	def normalize(self):
		"""
		Relocate the origin, datum, to the offset and zero the magnitude and offset.
		"""
		if self.offset >= self.magnitude or self.offset < 0:
			o = self.offset
			self.datum += o
			self.magnitude = 0
			self.offset = 0
			return o
		return 0

	def reposition(self, offset = 0):
		"""
		Reposition the &datum such that &offset will be equal to the given parameter.

		The magnitude is untouched. The change to the origin, &datum, is returned.
		"""
		delta = self.offset - offset
		self.datum += delta
		self.offset = offset
		return delta

	def start(self):
		"""
		Start the position by adjusting the &datum to match the position of the &offset.
		The magnitude will also be adjust to maintain its position.
		"""
		change = self.reposition()
		self.magnitude -= change

	def halt(self):
		"""
		Halt the position by adjusting the &magnitude to match the position of the
		offset.
		"""
		self.magnitude = self.offset

	def invert(self):
		"""
		Invert the position; causes the direction to change.
		"""
		self.datum += self.magnitude
		self.offset = -self.offset
		self.magnitude = -self.magnitude

	def page(self, quantity = 0):
		"""
		Adjust the position's datum to be at the magnitude's position according
		to the given quantity. Essentially, this is used to "page" the position;
		a given quantity selects how far forward or backwards the origin is sent.
		"""
		self.datum += (self.magnitude * quantity)

	def contract(self, offset, quantity):
		"""
		Adjust, decrease, the magnitude relative to a particular offset.
		"""
		if offset < 0:
			self.datum -= quantity
		elif offset <= self.magnitude:
			self.magnitude -= quantity # positives decrement, and negatives expand

		# if the contraction occurred at or before the position,
		# move the offset back as well.
		if offset <= self.offset:
			self.offset -= quantity

	def changed(self, offset, quantity):
		"""
		Adjust the position to accomodate for a change that occurred
		to the reference space--insertion or removal.

		Similar to &contract, but attempts to maintain &offset when possible,
		and takes an absolute offset instead of a relative one.
		"""
		roffset = offset - self.datum

		if roffset < 0:
			self.datum += quantity
			return
		elif roffset > self.magnitude:
			return

		self.magnitude += quantity

		# if the contraction occurred at or before the position,
		# move the offset back as well in order to keep the position
		# consistent.
		if roffset <= self.offset:
			self.offset += quantity

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

	def compensate(self):
		r = self.relation()
		if r == 1:
			self.magnitude = self.offset
		elif r == -1:
			self.datum += self.offset
			self.offset = 0

	def slice(self, adjustment = 0, step = 1, Slice = slice):
		start, pos, stop = map(adjustment.__add__, self.snapshot())
		return Slice(start, stop, step)

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
