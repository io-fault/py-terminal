"""
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
		The literal characters, if any, of the event.
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
