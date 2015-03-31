import abc
import collections
from ..interface import library as iflib

@iflib.interface("fault.io/Transformer")
class Terminal(metaclass=abc.ABCMeta):
	pass

class Device(metaclass=abc.ABCMeta):
	"""
	A stateful device that can be used to render text.
	"""

	@abc.abstractmethod
	def dimensions(self):
		"""
		:returns: (width, height)
		Returns a tuple describing the size of the window in characters.
		"""

	@abc.abstractmethod
	def backspace(self):
		"""
		Visually remove the character preceding the carat on the device.
		"""

	@abc.abstractmethod
	def tell_line(self):
		"""
		Return the line number of the text display that the carat is on.
		"""

	@abc.abstractmethod
	def tell_offset(self):
		"""
		Return the number of characters preceding the carat until the
		newline.
		"""

	@abc.abstractmethod
	def seek(self, coords):
		"""
		Relocate the carat to the given coordinates, (horiz, vert).
		"""

	@abc.abstractmethod
	def seek(self, coords):
		"""
		Relocate the carat to the given coordinates, (horiz, vert).
		"""

	@abc.abstractmethod
	def __enter__(self):
		"""
		Acquire access to the device and perform any requisite configuration.
		"""

	@abc.abstractmethod
	def __exit__(self, *args):
		"""
		Relinquish the device restoring original configuration, if possible.
		"""

class Field(metaclass=abc.ABCMeta):
	"""
	A structured, type qualified command with state
	that allows arbitrary modification of extant fields.
	"""
	@abc.abstractproperty
	def kind(self):
		"""
		A character string identifying the Field and its configuration.
		"""

	@abc.abstractproperty
	def subfields(self):
		"""
		The sequence of :py:class:`Field` instances making up this Field.

		:py:obj:`None` if there are no subfields.
		"""

	@abc.abstractmethod
	def focus(self, field):
		"""
		Called when the Field is entered; acquired focus.

		Given one argument, the field that gave this field focus.
		"""

	@abc.abstractmethod
	def blur(self, field):
		"""
		Called when the Field loses focus.

		Given one argument, the field that now has focus.
		"""

	@abc.abstractmethod
	def measure(self):
		"""
		Return the width of the rendered text without styling data.
		"""

	@abc.abstractproperty
	def transform(self, events):
		"""
		Transform the given events into stored state and return reactions
		to the transformations: usually, Field relative draw events.
		"""
