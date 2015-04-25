"""
The terminal I/O interfaces.
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

from . import core
from . import device

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

class Output(object):
	"""
	Manages display of text and carat positioning.

	FIXME: RESOLVE SEQUENCES USING TERMCAP
	"""
	def __init__(self, tty, encoding, terminal):
		self.tty = tty
		self.terminal = terminal
		self.encoding = encoding

	def modify(self, sliced, chars, styles):
		'Echo with style'
		adjustments = self.tty.adjust(sliced, chars)
		data = adjustments.encode(self.encoding) + chars.encode(self.encoding)
		self.terminal(data)

	def draw(self, events, getattr = getattr):
		data = ''
		for methname, *args in events:
			meth = getattr(self.terminal, methname)
			data += meth(*args)
		self.terminal(data)

class Input(object):
	"""
	Terminal input controller and key mapping.

	In order to properly regulate the event sequence and to shape initial
	typing and conversion,

	FIXME: RESOLVE SEQUENCES USING TERMCAP DB or terminal querying?
	"""

	def __init__(self, tty, encoding, source):
		self.tty = tty
		self.encoding = encoding
		self.source = source

	def draw(self):
		"""
		Draw events *from* the source.
		"""
		data = self.source()
		if not data:
			return None
		decoded = data.decode(self.encoding)
		return device.key_events(decoded)

	def __iter__(self):
		return self

	def __next__(self):
		return self.draw()

class Terminal(object):
	"""
	Terminal controller.

	This class is fundamental and should be subclassed
	in order to provide the desired functionality.
	"""
	Input = Input
	Output = Output

	def __init__(self, filenos, input, output):
		self.fio = filenos
		self.input = input
		self.output = output

	def acquire(self):
		"""
		Acquire control of the Terminal storing the existing settings
		and initializing raw mode.
		"""
		fd = self.fio[1]
		self._stored_settings = termios.tcgetattr(fd)
		tty.setcbreak(fd)
		tty.setraw(fd)
		new = termios.tcgetattr(fd)
		new[3] = new[3] & ~(termios.ECHO|termios.ICRNL)
		termios.tcsetattr(fd, termios.TCSADRAIN, new)

	@property
	def terminated(self):
		'Designates when the session has been closed.'
		return self.input is None

	def terminate(self):
		self.input = None

	def dimensions(self, winsize = array.array("h", [0,0,0,0])):
		winsize = winsize * 1
		fcntl.ioctl(self.fio[1], termios.TIOCGWINSZ, winsize, True)
		return (winsize[1], winsize[0])

	def __enter__(self):
		self._stored_settings = termios.tcgetattr(self.fio[1])
		tty.setcbreak(self.fio[1])
		tty.setraw(self.fio[1])
		new = termios.tcgetattr(self.fio[1])
		new[3] = new[3] & ~(termios.ECHO|termios.ICRNL)
		termios.tcsetattr(self.fio[1], termios.TCSADRAIN, new)

	def __exit__(self, *args):
		termios.tcsetattr(self.fio[1], termios.TCSADRAIN, self._stored_settings)

	@contextlib.contextmanager
	def lend(self):
		"""
		Restore the terminal state to how it was prior to entering;
		then back to raw on exit.
		"""
		self.__exit__()
		try:
			yield None
		finally:
			self.__enter__()

	def events(self):
		"""
		Yield the events produced by :py:attr:`input`.
		"""
		for x in self.input:
			yield x

	def draws(self, tgi):
		"""
		Perform the sequence of modification.
		"""
		for x in tgi:
			self.output.modify(*x)

	@classmethod
	def stdtty(typ, filenos = None, encoding = None):
		"""
		Return a Controlling associated with stdie.
		"""
		if filenos is None:
			filenos = (sys.stdin.fileno(), sys.stderr.fileno())
		if encoding is None:
			encoding = locale.getpreferredencoding()

		def doread(fd = filenos[0], chunksize = 128, read = os.read):
			return read(fd, chunksize)
		doread.fileno = filenos[0]

		def dowrite(data, fd = filenos[1], write = os.write):
			total = len(data)
			sent = 0
			while data:
				sent = write(fd, data)
				data = data[sent:]
			return total
		dowrite.fileno = filenos[1]

		return typ(
			filenos,
			Input(tty, encoding, doread),
			Output(tty, encoding, dowrite)
		)

class Line(object):
	"""
	A line in a view to be drawn into an area.
	"""
	__slots__ = ('text',)

	def __init__(self):
		pass

class View(object):
	"""
	A position independent sequence of lines.
	View contents are projected to a rectangle.
	"""

class Point(tuple):
	"""
	A pair of integers describing a position.
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
		return Class(points[:2])

class Rectangle(tuple):
	"""
	A arbitrary rectangle.
	"""
	@classmethod
	def construct(Class, *points):
		p = list(points)
		p.sort()
		return Class((p[0], p[-1]))

	@classmethod
	def define(Class, topleft = None, bottomright = None):
		return Class((Point(topleft), Point(bottomright)))

	@property
	def width(self):
		"""
		Physical width.
		"""
		return self[1][0] - self[0][0]

	@property
	def height(self):
		"""
		Physical height.
		"""
		return self[1][1] - self[0][1]

class Area(object):
	"""
	A subjective rectangle with a view for displaying lines.

	A projection of the view.
	"""

class Layer(object):
	"""
	A view of the display. Contains &Area instances.
	"""

	def contents(self, rectangle):
		"""
		Returns a view of the rectangle based on the view of the underlying areas.
		"""

class Stack(object):
	"""
	The stack of layers that make up a display.
	An ordered dictionary with explicitly defined indexes.
	"""
	@property
	def width(self):
		return self.dimensions[0]

	@property
	def height(self):
		return self.dimensions[1]

	@property
	def quantity(self):
		return len(self.layers)

	@property
	def names(self):
		"""
		Tuple of layer names according to their physical index.
		"""
		return tuple(x[1] for x in self.layers)

	def __init__(self):
		# literal sequence
		self.layers = []
		# index of names to layer index
		self.index = {}

		# absolute phsyical dimensions
		self.dimensions = device.dimensions()

	def insert(self, level, name, layer, _sk = operator.itemgetter(0)):
		"""
		Add a layer to the stack with the given name and level.
		"""
		self.layers.append((level, name, layer))
		self.layers.sort(key=_sk)
		self.index = { self.layers[i][1] : i for i in range(self.quantity) }

	def update(self):
		"""
		Signal that the terminal has changed dimensions to cause.
		"""
		new_dims = device.dimensions()
		self.dimensions = new_dims
