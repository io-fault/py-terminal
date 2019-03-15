"""
# Fundamental classes for representing input from a terminal and caret state management.

# [ Types ]
# /&Page/
	# &Phrase sequence.
# /&Text/
	# Alias to the builtin &str.
"""
import typing
import functools
import itertools
from ..system import text

Text = str

class Point(tuple):
	"""
	# A pair of integers locating a cell on the screen.
	# Used by &.events.mouse to specify the cursor location.

	# Usually referenced from &.events.Point.
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

	# Usually referenced from &.events.Modifiers.
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
		"""
		# Whether there are any modifiers present.
		"""
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
		"""
		# Check for the presence of multiple modifiers.

		#!/pl/python
			if mod.test('shift', 'meta'):
				action()
			else:
				no_shift_meta_action()
		"""
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
		'control', # Control Character
		'delta', # Insert/Delete keys
		'navigation', # Arrow/Paging keys
		'function', # F-keys
		'scroll',
		'mouse',
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
	# No constraints are enforced and position coherency is considered subjective.

	# [ Properties ]
	# /datum/
		# The absolute position. (start)
	# /offset/
		# The actual position relative to the &datum. (current=datum+offset)
	# /magnitude/
		# The size of the range relative to the &datum. (stop=datum+magnitude)
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
	# A pair of &Position instances describing an area and point on a two dimensional plane.

	# Primarily this exists to provide methods that will often be used simultaneously on the vertical
	# and horizontal positions. State snapshots and restoration being common or likely.

	# [ Properties ]
	# /horizontal/
		# The horizontal &Position.
	# /vertical/
		# The vertical &Position.
	"""

	def __len__(self):
		return 2

	def __getitem__(self, index:int):
		if index:
			if index != 1:
				raise IndexError("terminal poisition vectors only have two entries")
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
		"""
		# Create a &Vector whose positions are initialized to zero.
		"""
		self.horizontal = Position()
		self.vertical = Position()

	def snapshot(self):
		return (self.horizontal.snapshot(), self.vertical.snapshot())

	def restore(self, snapshot):
		self.horizontal.restore(snapshot[0])
		self.vertical.restore(snapshot[1])

class Traits(int):
	"""
	# Word attribute bitmap used to describe a part of a &Phrase.

	# The bitmap of attributes allows for conflicting decorations;
	# &.terminal makes no presumptions about how the terminal responds to
	# these, so constraints that might be expected are not present.
	"""
	__slots__ = ()

	def _build(fields):
		return fields, {
			fields[i]: i for i in range(len(fields))
		}

	fields, field_index = _build(
		(
			'underline',
			'double-underline',

			'inverse',
			'cross',
			'italic',

			'invisible',
			'feint',
			'bold',

			'blink',
			'rapid',

			'overline',
			'frame',
			'encircle',

			'sentinal',
		)
	)
	del _build

	def __and__(self, rhs):
		return self.__class__(super().__and__(rhs))
	def __or__(self, rhs):
		return self.__class__(super().__or__(rhs))
	def __xor__(self, rhs):
		return self.__class__(super().__xor__(rhs))

	@classmethod
	def all(Class):
		return Class((1 << len(Class.fields)) - 1)

	@classmethod
	def construct(Class, *style):
		i = 0
		for x in style:
			i = i | (1 << Class.field_index[x])

		return Class(i)

	def test(self, *names):
		for trait in names:
			if not self & (1 << self.field_index[trait]):
				return False

		return True

	def __iter__(self):
		for name, i in self.field_index.items():
			if self & (1 << i):
				yield name

	def __str__(self):
		if self:
			return '<' + '|'.join(self) + '>'
		return '<notraits>'

NoTraits = Traits(0)

class RenderParameters(tuple):
	"""
	# Rendering context parameters to use for displaying text on a Terminal.
	# Instances hold the text and cell colors and the &Traits.
	"""
	__slots__ = ()

	_cc_none = -1024
	_tc_none = -1024

	@property
	def textcolor(self) -> int:
		"""
		# The RGB color to use as the text color.
		"""
		return self[0]

	@property
	def cellcolor(self) -> int:
		"""
		# The RGB color to use as the cell's background color.
		"""
		return self[1]

	@property
	def traits(self) -> Traits:
		"""
		# The set of &Traits used to style displayed text.
		"""
		return self[2]

	@classmethod
	def from_colors(Class, textcolor, cellcolor) -> 'RenderParameters':
		return Class((textcolor, cellcolor, NoTraits))

	def set(self, traits) -> 'RenderParameters':
		"""
		# Create a new instance with the given &traits added to
		# the traits present in &self.
		"""
		return self.__class__((
			self[0], self[1], traits | self[2]
		))

	def clear(self, traits) -> 'RenderParameters':
		"""
		# Create a new instance with the given &traits removed
		# from the traits present in &self.
		"""
		c = self[2]
		return self.__class__((
			self[0], self[1], ((c & traits) ^ c)
		))

	def update(self, textcolor=None, cellcolor=None, traits=None):
		return self.__class__((
			textcolor if textcolor is not None else self[0],
			cellcolor if cellcolor is not None else self[1],
			traits if traits is not None else self[2],
		))

	def form(self, *strings, cells=text.cells):
		"""
		# Construct words suitable for use by &Phrase associated with the parameters, &self.
		"""
		for text in strings:
			yield (cells(text), text, self)

class Units(tuple):
	"""
	# Explicitly partitioned string for forced segmentation.

	# Provides a string-like object for explicitly designating the User Perceived Character
	# boundaries. Primarily used for managing surrogate pairs and multicharacter tokens.
	"""
	__slots__ = ()

	def __str__(self, map=map, str=str, tuple=tuple):
		return ''.join(map(str, super().__iter__()))

	def encode(self, encoding, errors='surrogateescape'):
		return str(self).encode(encoding, errors=errors)

	def __getitem__(self, item, isinstance=isinstance, slice=slice):
		if isinstance(item, slice):
			# Make sure to return typed instance for slices.
			return self.__class__(super().__getitem__(item))

		return super().__getitem__(item)

	def __add__(self, rhs):
		return self.__class__(super().__add__(rhs))

def grapheme(text, index, cells=text.cells, slice=slice, Units=Units, str=str):
	"""
	# Retrieve the slice to characters that make up an indivisible unit of cells.
	# This is not always consistent with User Perceived Characters.

	# If the given &index refers to a zero width character,
	# find the non-zero width character before the index.
	# If the given &index refers to a non-zero width character,
	# find all the zero width characters after it.

	# ! WARNING:
		# This is **not** consistent with Unicode grapheme (clusters).
	"""
	if isinstance(text, Units):
		# Units instances are one-to-one.
		return slice(index, index+1)

	start = text[index:index+1]
	count = 0

	c = cells(str(start))
	if c < 0:
		# check surrogate pair; identify latter part of pair
		# and consume following combinations normally.
		pass

	if c > 0:
		# check after
		for i in range(index+1, len(text)):
			if cells(text[i]):
				break
			count += 1
		return slice(index, index+count+1)
	else: # c==0
		# check before
		for i in range(index-1, -1, -1):
			if cells(text[i]):
				break
			count += 1
		return slice(index-count-1, index+1)

def itergraphemes(text, getslice=grapheme, len=len):
	end = len(text)
	i = 0
	while i < end:
		s = getslice(text, i)
		yield s
		i = s.stop

Words = typing.Tuple[int, Text, RenderParameters]

class Phrase(tuple):
	"""
	# A terminal Phrase expressing a sequence of styled words.

	# Each Word in the Phrase contains an arbitrary string associated with a foreground,
	# background, and &Traits.
	"""
	__slots__ = ()

	@staticmethod
	def default(text, traits=(None,None,Traits(0))):
		"""
		# Construct a Word Specification with default text attributes.
		"""
		return (text, traits)

	@classmethod
	def wordspace(Class):
		"""
		# Word specification consisting of a single space.
		"""
		return Class.default(" ")

	@classmethod
	def from_words(Class, *words:Words, ichain=itertools.chain.from_iterable) -> 'Phrase':
		return Class(ichain(words))

	def join(self, phrases, zip=zip, repeat=itertools.repeat, ichain=itertools.chain.from_iterable):
		"""
		# Create a new Phrase from &phrases by placing &self between each &Phrase instance
		# in &phrases.
		"""
		if not phrases:
			return self.__class__(())

		i = ichain(ichain(zip(repeat(self, len(phrases)), phrases)))
		next(i)
		return self.__class__((i))

	@classmethod
	def construct(Class,
			specifications:typing.Sequence[object],
			RenderParametersConstructor=RenderParameters,
			cells=text.cells, str=str
		) -> 'Phrase':
		"""
		# Create a &Phrase instance from the &specifications designating
		# the text of the words and their properties.

		# [ Parameters ]
		# /specifications/
			# The words and their attributes making up the phrase.
		"""
		specs = [
			(cells(str(spec[0])), spec[0], RenderParameters(spec[1:]))
			for spec in specifications
		]

		return super().__new__(Class, specs)

	def combine(self) -> 'Phrase':
		"""
		# Combine word specifications with identical attributes(styles).
		# Returns a new &Phrase instance with any redundant word attributes eliminated.
		"""

		out = [self[0]]
		cur = out[-1]

		for spec in self[1:]:
			if spec[2] == cur[2]:
				cur = out[-1] = (cur[0] + spec[0], cur[1] + spec[1], cur[3:])
			else:
				out.append(spec)
				cur = spec

		return self.__class__(out)

	def cellcount(self):
		"""
		# Number of cells that the phrase will occupy.
		"""
		return sum(x[0] for x in self)

	def unitcount(self):
		"""
		# Number of character units contained by the phrase.
		"""
		return sum(len(x[1]) for x in self)

	def translate(self, *indexes, iter=iter, len=len, next=next, cells=text.cells):
		"""
		# Get the cell offsets of the given character indexes.

		# [ Parameters ]
		# /indexes/
			# Ordered sequence of grapheme (cluster) indexes to resolve.
			# (Currently a lie, it is mere character index translation)
		"""
		offset = 0
		nc = 0
		noffset = 0

		if not self:
			for x in indexes:
				if x == 0:
					yield 0
				else:
					raise IndexError(indexes[0])
			return

		i = iter(y[:2] for y in self)
		x = next(i)

		c, t = x
		chars = len(t)
		noffset = offset + chars

		for y in indexes:
			while x is not None:
				if noffset >= y:
					# found index, report and jump to next index
					yield nc + cells(t[:y-offset])
					break

				nc += c
				offset = noffset
				try:
					x = next(i)
				except StopIteration:
					yield None
					break

				# New words.
				c, t = x
				chars = len(t)
				noffset = offset + chars
			else:
				# index out of range
				yield None

	def findcells(self, *offsets, index=(0,0,0)):
		lfc = self.lfindcell
		last = 0
		for co in offsets:
			index = lfc(co - last, index)
			last = co
			yield index

	def reverse(self):
		"""
		# Construct an iterator to the concrete words for creating a new &Phrase
		# instance that is in reversed form of the words in &self.
		# `assert phrase == Phrase(Phrase(phrase.reverse()).reverse())`
		"""
		return (
			(x[0], x[1].__class__(reversed(x[1])),) + x[2:]
			for x in reversed(self)
		)

	def subphrase(self, start, stop, adjust=(lambda x: x)):
		"""
		# Extract the subphrase at the given cell offsets.
		"""

		return self.__class__(self.select(start, stop, adjust))

	def select(self, start, stop, adjust=(lambda x: x), cells=text.cells):
		"""
		# Extract the subphrase at the given indexes.

		# [ Parameters ]
		# /adjust/
			# Callable that changes the text properties of the selected words.
			# Defaults to no change.
		"""
		start_i, char_i, acell_i = start
		stop_i, schar_i, bcell_i = stop

		if start_i == stop_i:
			# Single word phrase.
			word = self[start_i]
			text = word[1][char_i:schar_i]
			yield (cells(text), text, adjust(word[2]))
		else:
			word = self[start_i]
			text = word[1][char_i:]
			if text:
				yield (cells(text), text, adjust(word[2]))

			yield from self[start_i+1:stop_i]

			word = self[stop_i]
			text = word[1][:schar_i]
			if text:
				yield (cells(text), text, adjust(word[2]))

	# lfindcell and rfindcell are conceptually identical,
	# but it's a little tricky to keep the Python implementation dry
	# without introducing some unwanted overhead.
	# So, the implementation redundancy is permitted with the minor variations.

	def lfindcell(self,
			celloffset:int, start=(0,0,0),
			map=map, len=len, range=range,
			cells=text.cells, islice=itertools.islice
		):
		"""
		# Find the word and character index using a cell offset.
		"""

		wordoffset, character_index, wordcell = start
		# relative to wordcell for continuation support
		offset = celloffset + wordcell
		cell_index = wordcell

		i = l = 0
		if wordoffset < 16:
			# Small offset? recalc from sum.
			s = sum(x[0] for x in self[:wordoffset])
		elif character_index:
			# Large offset, recalc from cells.
			s = wordcell - cells(self[wordoffset][1][:character_index])
		else:
			s = wordcell

		nwords = len(self)
		ri = range(wordoffset, nwords, 1)

		# Scan for offset wrt the cells.
		for i in ri:
			l = self[i][0]
			s += l
			if s >= offset:
				if i != wordoffset:
					# Reset index if in a new word.
					character_index = 0
				break
			cell_index = s
		else:
			# celloffset is beyond the end of the phrase
			return None

		itext = self[i][1]

		charcells = 0
		for charcells in map(cells, islice(itext, character_index, None)):
			if cell_index >= offset:
				break
			cell_index += charcells
			character_index += 1

		# Greedily skip any adjacent zerowidth characters.
		# rfindcell does this naturally.
		for charcells in map(cells, islice(itext, character_index, None)):
			if charcells:
				# Not zero width, keep current index.
				break
			character_index += 1
		else:
			# End of word; empty string or empty Units
			while not self[i][1][character_index:character_index+1]:
				i += 1
				if i == nwords:
					i -= 1
					break
				character_index = 0

		return (i, character_index, cell_index)

	def rfindcell(self,
			celloffset:int, start=(-1,0,0),
			map=map, len=len, range=range,
			cells=text.cells, islice=itertools.islice
		):
		"""
		# Find the word and character index using a cell offset.
		"""

		wordoffset, character_index, wordcell = start

		# relative to wordcell for continuation support
		offset = celloffset + wordcell
		cell_index = wordcell

		i = l = 0
		nwords = len(self)
		ri = range(wordoffset, -nwords-1, -1)

		if wordoffset > -16:
			s = sum(x[0] for x in self[nwords+wordoffset+1:])
		elif character_index:
			s = wordcell - cells(self[wordoffset][1][-character_index:])
		else:
			s = wordcell

		for i in ri:
			l = self[i][0]
			s += l
			if s >= offset:
				if i != wordoffset:
					character_index = 0
				break
			cell_index = s
		else:
			# celloffset is beyond the beginning of the phrase.
			return None

		itext = self[i][1]
		istart = len(itext)-character_index-1

		for charcells in map(cells, (itext[x] for x in range(istart, -1, -1))):
			if cell_index >= offset:
				break
			cell_index += charcells
			character_index += 1
		else:
			# End of word
			if nwords + i == 0:
				# End of Phrase.
				pass
			elif cell_index == offset:
				# Only step into the next word if it's not torn.
				i -= 1
				character_index = 0

		return (i, character_index, cell_index)

	def lstripcells(self,
			cellcount:int, substitute=(lambda x: '*'),
			list=list, len=len, range=range,
			cells=text.cells
		):
		"""
		# Remove the given number of cells from the start of the phrase.

		# If the cell count traverses a wide character, the &substitute parameter is
		# called with the character as its only argument and the result is prefixed
		# to the start of the phrase.
		"""

		if cellcount <= 0:
			# Zero offset, no trim.
			return self

		i, character_index, cell_index = self.lfindcell(cellcount)
		itext = self[i][1]

		if cellcount == cell_index:
			# Aligned.
			txt = itext[character_index:]
		else:
			# Cut on wide character and substitute.
			g = grapheme(itext, character_index - 1)
			txt = substitute(itext[g]) + itext[character_index:]

		# final words
		out = list(self[i:]) # Include the i'th; it will be overwritten.
		out[0] = ((cells(txt), txt,) + out[0][2:])

		return self.__class__(out)

	def rstripcells(self,
			cellcount:int, substitute=(lambda x: '*'),
			list=list, len=len, range=range,
			cells=text.cells
		):
		"""
		# Remove the given number of cells from the end of the phrase.

		# If the cell count traverses a wide character, the &substitute parameter is
		# called with the character as its only argument and the result is suffixed
		# to the end of the phrase.
		"""

		if cellcount <= 0:
			# Zero offset, no trim.
			return self

		i, rcharacter_index, cell_index = self.rfindcell(cellcount)

		out = list(self[:len(self)+i+1])
		itext = out[-1][1]
		character_right_offset = len(itext) - rcharacter_index

		if cellcount == cell_index:
			# Aligned on character.
			txt = itext[:character_right_offset]
		else:
			# Tear multicell character and substitute.
			g = grapheme(itext, character_right_offset)
			txt = itext[:g.start] + substitute(itext[g])

		# final words
		out[-1] = ((cells(txt), txt,) + out[-1][2:])

		return self.__class__(out)

# Common descriptor endpoint.
Page = typing.Sequence[Phrase]
