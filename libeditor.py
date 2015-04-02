"""
Classes for managing the content and style of the fields.
"""

class Field(object):
	"""
	The base field class providing management for the content of a field.
	"""
	#: Pairs of characters that make up the actual text in the
	#: field and the representation text.
	sequence = None

	def __init__(self):
		self.sequence = []

	@property
	def content(self):
		'The literal characters of the field.'
		return ''.join(self.sequence)

	@property
	def length(self):
		'Number of elements in the Field.'
		return len(self.sequence)

	@property
	def empty(self):
		'Indicates that there are no elements in the Field.'
		return self.length == 0

	def modify(self, sliced, sequence):
		"""
		:returns: ``inverse``
		:rtype: :py:class:`tuple`

		Write a slice of sequence and return the inverse operation.
		"""
		replaced = self.sequence[sliced]
		self.sequence[sliced] = sequence
		return (
			slice(sliced.start, sliced.start + len(sequence),),
			replaced,
		)

class Separator(Field):
	sequence = (' ',)

	def modify(self, sliced, sequence):
		return None
Separator = Separator()

class Editor(object):
	def __init__(self):
		self.fields = Field()
		self.fields.modify(slice(0,0), [Field()])
		self.types = []
		self.changelog = []
		self.cws = self.inserts
		self.reset()

	@property
	def content(self):
		return ''.join(x.content for x in self.fields.sequence)

	@property
	def cwf(self):
		return self.fields.sequence[self.field]

	@property
	def fcarat(self):
		return self.carat[-1]

	def reset(self):
		self.state = None
		self.carat = (0, 0)
		self.field = 0
		return [
			('beginning',)
		]

	def inserts(self, key):
		"""
		Handle keys in insert mode.
		"""
		draw = []
		if key.identity == 'space':
			self.fields.append(Separator)
			self.fields.append(Field())
			self.types.append(None)
			self.types.append(None)
			draw += self.types
			self.focus += 2
		else:
			lc, fc = self.carat
			undo = self.cwf.modify(slice(fc, fc), key.string)
			draw += [(slice(self.carat[0], self.carat[0]), key.string, ())]
			self.carat = (lc + 1, fc + 1)
		return draw

	def move(self, nchars):
		"""
		Move the cursor the specified number of characters.

		This move method works with buffer characters, not display characters.
		"""
		if not nchars:
			# no movement
			return []
		lc, fc = [x+chars for x in self.carat]

		if lc < 0:
			# cursor is at edge of screen. XXX: wrap cases?
			lc = 0
			fc = 0
			self.focus = 0
		elif fc == -1:
			# previous field
			self.focus -= 1

	def key(self, key):
		return self.cws(key)
