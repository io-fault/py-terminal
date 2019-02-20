"""
# Fundamental classes for representing input from a terminal and managing state.
"""
import functools

class Point(tuple):
	"""
	# A pair of integers locating a cell on the screen.
	"""
	__slots__ = ()

	@property
	def x(self):
		return self[0]

	@property
	def y(self):
		return self[1]

	def __add__(self, point, op=int.__add__):
		"""
		# Translate the point relative to another.
		"""
		return self.__class__((op(self[0], point[0]), op(self[1], point[1])))

	def __sub__(self, point, op=int.__sub__):
		"""
		# Abstract the point from another.
		"""
		return self.__class__((op(self[0], point[0]), op(self[1], point[1])))

	@classmethod
	def create(Class, *points):
		return Class(points)
	construct = create

class Modifiers(int):
	"""
	# Bitmap of modifiers with an imaginary index.

	# The imaginary index is usually not used, but can be used to describe
	# the modifier context or carry additional information about the event.
	"""
	__slots__ = ()

	sequence = (
		'control',
		'shift',
		'meta',
	)
	bits = {
		k: 1 << i for k, i in zip(sequence, range(len(sequence)))
	}

	def __repr__(self):
		return (
			"<" + ('|'.join([
				x for x in self.sequence
				if self.bits[x] & self
			]) or 'none') + ">"
		)

	@property
	def none(self):
		return not (self & 0b111)

	@property
	def control(self):
		return (self & 0b001)

	@property
	def meta(self):
		return (self & 0b100)

	@property
	def shift(self):
		return (self & 0b010)

	@property
	def imaginary(self, position=len(sequence)):
		"""
		# An arbitrary number designating an imaginary modifier.
		# Defaults to zero.
		"""
		return int(self >> position)

	def test(self, *fields):
		bitset = sum([self.bits[x] for x in fields])
		return bool(bitset & self)

	@classmethod
	@functools.lru_cache(9)
	def construct(Class, bits=0, control=False, meta=False, shift=False, imaginary=0):
		mid = imaginary << 3
		mid |= bits

		if control:
			mid |= Class.bits['control']

		if meta:
			mid |= Class.bits['meta']

		if shift:
			mid |= Class.bits['shift']

		return Class(mid)

class Event(tuple):
	"""
	# A single characeter from input event from a terminal device.
	# Usually referenced from &.events.Character along with the lookup tables.
	"""
	__slots__ = ()

	classifications = (
		'control',
		'manipulation',
		'navigation',
		'function',
		'mouse',
		'scroll',
	)

	@property
	def subtype(self):
		"""
		# The classification of the character with respect to the source.
		"""
		return self[0]
	type=subtype

	@property
	def string(self):
		"""
		# The literal characters, if any, of the event. Used for forwarding key events.
		"""
		return self[1]

	@property
	def identity(self):
		"""
		# A name for the &string contents; often the appropriate way to process
		# character events. For complex events, this field holds a structure.
		"""
		return self[2]

	@property
	def modifiers(self):
		"""
		# The identified &Modifiers of the Character.
		"""
		return self[3]

class Position(object):
	"""
	# Mutable position state for managing the position of a cursor with respect to a range.
	# Constraints are not enforced in order to allow the user to leverage the overflow.

	# [ Properties ]
	# /datum/
		# The absolute position.
	# /offset/
		# The actual position relative to the &datum.
	# /magnitude/
		# The size of the range relative to the &datum.
	"""
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
		# Get the absolute position.
		"""
		return self.datum + self.offset

	def set(self, position):
		"""
		# Set the absolute position.

		# Calculates a new &offset based on the absolute &position.
		"""
		new = position - self.datum
		change = self.offset - new
		self.offset = new
		return change

	def configure(self, datum, magnitude, offset = 0):
		"""
		# Initialize the values of the position.
		"""
		self.datum = datum
		self.magnitude = magnitude
		self.offset = offset

	def limit(self, minimum, maximum):
		"""
		# Apply the minimum and maximum limits to the Position's absolute values.
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
		# Calculate and return the absolute position as a triple.
		"""
		start = self.datum
		offset = start + self.offset
		stop = start + self.magnitude
		return (start, offset, stop)

	def restore(self, snapshot):
		"""
		# Restores the given snapshot.
		"""
		self.datum = snapshot[0]
		self.offset = snapshot[1] - snapshot[0]
		self.magnitude = snapshot[2] - snapshot[0]

	def update(self, quantity):
		"""
		# Update the offset by the given quantity.
		# Negative quantities move the offset down.
		"""
		self.offset += quantity

	def clear(self):
		"""
		# Reset the position state to a zeros.
		"""
		self.__init__()

	def zero(self):
		"""
		# Zero the &offset and &magnitude of the position.

		# The &datum is not changed.
		"""
		self.magnitude = 0
		self.offset = 0

	def move(self, location = 0, perspective = 0):
		"""
		# Move the position relatively or absolutely.

		# Perspective is like the whence parameter, but uses slightly different values.

		# `-1` is used to move the offset relative from the end.
		# `+1` is used to move the offset relative to the beginning.
		# Zero moves the offset relatively with &update.
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
		# Adjust the offset to be within the bounds of the magnitude.
		# Returns the change in position; positive values means that
		# the magnitude was being exceeded and negative values
		# mean that the minimum was being exceeded.
		"""
		o = self.offset
		if o > self.magnitude:
			self.offset = self.magnitude
		elif o < 0:
			self.offset = 0

		return o - self.offset

	def collapse(self):
		"""
		# Move the origin to the position of the offset and zero out magnitude.
		"""
		o = self.offset
		self.datum += o
		self.offset = self.magnitude = 0
		return o

	def normalize(self):
		"""
		# Relocate the origin, datum, to the offset and zero the magnitude and offset.
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
		# Reposition the &datum such that &offset will be equal to the given parameter.

		# The magnitude is untouched. The change to the origin, &datum, is returned.
		"""
		delta = self.offset - offset
		self.datum += delta
		self.offset = offset
		return delta

	def start(self):
		"""
		# Start the position by adjusting the &datum to match the position of the &offset.
		# The magnitude will also be adjust to maintain its position.
		"""
		change = self.reposition()
		self.magnitude -= change

	def bisect(self):
		"""
		# Place the position in the middle of the start and stop positions.
		"""
		self.offset = self.magnitude // 2

	def halt(self):
		"""
		# Halt the position by adjusting the &magnitude to match the position of the
		# offset.
		"""
		self.magnitude = self.offset

	def invert(self):
		"""
		# Invert the position; causes the direction to change.
		"""
		self.datum += self.magnitude
		self.offset = -self.offset
		self.magnitude = -self.magnitude

	def page(self, quantity = 0):
		"""
		# Adjust the position's datum to be at the magnitude's position according
		# to the given quantity. Essentially, this is used to "page" the position;
		# a given quantity selects how far forward or backwards the origin is sent.
		"""
		self.datum += (self.magnitude * quantity)

	def contract(self, offset, quantity):
		"""
		# Adjust, decrease, the magnitude relative to a particular offset.
		"""
		if offset < 0:
			# before range; offset is relative to datum, so only adjust datum
			self.datum -= quantity
		elif offset <= self.magnitude:
			# within range, adjust size and position
			self.magnitude -= quantity
			self.offset -= quantity
		else:
			# After of range, so only adjust offset
			self.offset -= quantity

	def changed(self, offset, quantity):
		"""
		# Adjust the position to accomodate for a change that occurred
		# to the reference space--insertion or removal.

		# Similar to &contract, but attempts to maintain &offset when possible,
		# and takes an absolute offset instead of a relative one.
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
		# Adjust, increase, the magnitude relative to a particular offset.
		"""
		return self.contract(offset, -quantity)

	def relation(self):
		"""
		# Return the relation of the offset to the datum and the magnitude.
		"""
		o = self.offset
		if o < 0:
			return -1
		elif o > self.magnitude:
			return 1
		else:
			return 0 # within bounds

	def compensate(self):
		"""
		# If the position lay outside of the range, relocate
		# the start or stop to be on position.
		"""
		r = self.relation()
		if r == 1:
			self.magnitude = self.offset
		elif r == -1:
			self.datum += self.offset
			self.offset = 0

	def slice(self, adjustment=0, step=1, Slice=slice):
		"""
		# Construct a &slice object that represents the range.
		"""
		start, pos, stop = map(adjustment.__add__, self.snapshot())
		return Slice(start, stop, step)

class Vector(object):
	"""
	# A pair of &Position instances describing a two dimensional area and point.

	# Primarily this exists to provide methods that will often be used simultaneously on the vertical
	# and horizontal positions. State snapshots and restoration being common or likely.

	# [ Engineering ]
	# This should probably be a tuple subclass.
	"""
	def __len__(self):
		return 2

	def __getitem__(self, index:int):
		if index:
			if index != 1:
				raise IndexError("terminal vectors only have two entries")
			return self.vertical
		return self.horizontal

	def __iter__(self):
		return (self.horizontal, self.vertical).__iter__()

	def clear(self):
		"""
		# Zero the horizontal and vertical positions.
		"""
		self.horizontal.clear()
		self.vertical.clear()

	def move(self, x, y):
		"""
		# Move the positions relative to their current state.
		# This method should be used for cases when applying a function:

		#!/pl/python
			for x in range(...):
				vector.move(x, f(x))
				draw(vector)
		"""
		if x:
			self.horizontal.update(x)
		if y:
			self.vertical.update(y)

	def get(self):
		"""
		# Get the absolute horizontal and vertical position as a 2-tuple.
		"""
		return Point((self.horizontal.get(), self.vertical.get()))

	def __init__(self):
		self.horizontal = Position()
		self.vertical = Position()

	def snapshot(self):
		return (self.horizontal.snapshot(), self.vertical.snapshot())

	def restore(self, snapshot):
		self.horizontal.restore(snapshot[0])
		self.vertical.restore(snapshot[1])
