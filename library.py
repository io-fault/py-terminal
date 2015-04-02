"""
The terminal I/O interfaces.

.. warning:: This module is for internal use only. DO NOT USE!
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

#: Description of a key press. Terminals provide limited information about
#: things like keyboard state, so this structure is limited to what is
#: usually available.
Key = collections.namedtuple(
	"Key", ("type", "string", "identity", "control", "meta")
)

class Teletype(object):
	"XXX: Lame hack avoiding terminfo databases; docs are hard to find."
	def __init__(self, name):
		self.name = name

	@staticmethod
	def backspace(ntimes):
		return '\b \b' * ntimes

	@staticmethod
	def seek(coords):
		'relocate the carat to an arbitrary, absolute location'
		h, v = coords
		return ''.join((
			'\x1b[', str(h), ';', str(v), 'H',
		))

	@staticmethod
	def hseekr(n):
		'Horizontally adjust the carat (relative)'
		if n < 0:
			return ''.join((
				'\x1b[', str(-n), 'D'
			))
		elif n > 0:
			return ''.join((
				'\x1b[', str(n), 'C'
			))
		else:
			return ''

	@staticmethod
	def vseekr(n):
		'Vertically adjust the carat (relative)'
		if n < 0:
			return ''.join(('\x1b[', str(-n), 'A'))
		elif n > 0:
			return ''.join(('\x1b[', str(n), 'B'))
		else:
			return ''

	@classmethod
	def seekr(typ, rcoords):
		h, v = rcoords
		return typ.hseekr(h) + typ.vseekr(v)

	@staticmethod
	def clear():
		'Clear the entire screen.'
		return '\x1b[\x48\x1b\x5b\x32\x4a'

	@staticmethod
	def clear_former():
		return '\x1b[\x31\x4b'

	@staticmethod
	def clear_latter():
		return '\x1b[\x4b'

	@staticmethod
	def clear_line():
		return '\x1b[\x31\x4b' + '\x1b[\x4b'

	@staticmethod
	def new():
		'Open newline'
		return '\n\r'

	@staticmethod
	def beginning():
		'Return the beginning of the line'
		return '\r'

	@staticmethod
	def store():
		'Save the current carat position'
		return '\x1b\x37'

	@staticmethod
	def restore():
		'Restore the stored carat position'
		return '\x1b\x38'

	@staticmethod
	def deflate(area):
		'Delete space, (horizontal, vertical) between the carat.'
		change = ''
		h, v = area
		if h:
			change += ''.join((
				'\x1b[', str(h), 'P'
			))
		if v:
			change += ''.join((
				'\x1b[', str(v), 'M'
			))
		return change

	@staticmethod
	def inflate(area):
		"""
		Insert space, (horizontal, vertical) between the carat.
		"""
		change = ''
		h, v = area
		if h:
			change += ''.join((
				'\x1b[', str(h), '@'
			))
		if v:
			change += ''.join((
				'\x1b[', str(v), 'L'
			))
		return change

	@classmethod
	def adjust(typ, slice, characters):
		"""
		Perform a subsitution.
		"""
		seek = typ.seek((slice.start, -1)) # relative to the carat
		deletes = typ.deflate((slice.stop - slice.start, 0))
		spaces = typ.inflate((len(characters), 0))
		return ''.join((
			seek,
			deletes,
			spaces,
		))

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

	#: Key events whose identifiers assume an escape prefix.
	escaped = {
		'': Key('control', '', 'escape', None, False),
		' ': Key('control', ' ', 'space', False, True),

		'[3~': Key('control', '[3~', 'delete', False, False),
		'\x7f': Key('control', '\x7f', 'delete-back', False, True),
		'\x08': Key('control', '\x08', 'backspace', False, True),

		# shift-tab and shift-meta-tab
		'[Z': Key('tab', '[Z', 'shift-tab', False, False),
		'[Z': Key('tab', '[Z', 'shift-tab', False, True),

		'[H': Key('direction', '[H', 'home', False, False), # home
		'[F': Key('direction', '[F', 'end', False, False), # end
		'[5~': Key('direction', '[5~', 'pageup', False, False), # page up
		'[6~': Key('direction', '[6~', 'pagedown', False, False), # page down

		'OD': Key('direction', 'OD', 'left', False, False),
		'OC': Key('direction', 'OC', 'right', False, False),
		'OA': Key('direction', 'OA', 'up', False, False),
		'OB': Key('direction', 'OB', 'down', False, False),

		'[1;3D': Key('direction', '[1;3D', 'left', False, True),
		'[1;3C': Key('direction', '[1;3C', 'right', False, True),
		'[1;3A': Key('direction', '[1;3A', 'up', False, True),
		'[1;3B': Key('direction', '[1;3B', 'down', False, True),

		'OP': Key('function', 'OP', 1, False, False),
		'OQ': Key('function', 'OQ', 2, False, False),
		'OR': Key('function', 'OR', 3, False, False),
		'OS': Key('function', 'OS', 4, False, False),
		'[15~': Key('function', '[15~', 5, False, False),
		'[17~': Key('function', '[17~', 6, False, False),
		'[18~': Key('function', '[18~', 7, False, False),
		'[19~': Key('function', '[19~', 8, False, False),
		'[20~': Key('function', '[20~', 9, False, False),
		'[21~': Key('function', '[21~', 10, False, False),
	}

	exact = dict(
		# Some of these get overridden with their
		# common representation.
		zip(
			(
				'', '', '', '',
				'', '', '', '',
				'\t', '\r', '', '',
				'\n', '', '', '',
				'\x11', '', '\x13', '',
				'', '', '', '',
				'', '',
			),
			(
				Key('control', x, x, True, False)
				for x in map(chr, range(ord('a'), ord('z')+1))
			)
		)
	)

	# Override any of the identified control characters with these.
	exact.update({
		'\x00': Key('control', '\x00', 'space', True, False),
		'\t': Key('control', '\t', 'tab', False, False),
		' ': Key('control', ' ', 'space', False, False),

		'\x7f': Key('control', '\x7f', 'delete-back', False, False),
		'\b': Key('control', '\b', 'backspace', False, False),

		'\r': Key('control', '\r', 'return', False, False),
		'': Key('control', '', 'enter', True, False),
		'\n': Key('control', '\n', 'newline', False, False),

		'': Key('control', '\\', 'backslash', True, False),
		'': Key('control', '_', 'underscore', True, False),
	})

	def kexact(self, keys):
		'Resolve events for keys without escapes'
		return [
			self.exact.get(x) if x in self.exact
			else Key('literal', x, x, False, False) for x in keys
		]

	def kescaped(self, key):
		if key in self.escaped:
			return self.escaped[key]
		else:
			return Key('meta', key, key, False, True)

	def kevent(self, keys):
		"""
		Resolve the events for the given keys.
		"""
		first = keys.find('\x1b')

		if first == -1:
			# No escapes, just iterate over the characters.
			return self.kexact(keys)
		elif keys:
			# Escape Code to map control characters.

			if first > 0:
				events = self.kexact(keys[:first])
			else:
				events = []

			# split on the escapes and map the sequences to KeyPressEvents
			escapes = iter(keys[first:].split('\x1b'))
			next(escapes) # skip initial empty sequence
			##
			# XXX
			# handle cases where multiple escapes are found.
			# there are some cases of ambiguity, but this seems to be ideal?
			escape_level = 0
			for x in escapes:
				# escape escape.
				if not x:
					escape_level += 1
				else:
					events.append(self.kescaped(('\x1b' * escape_level) + x))
					escape_level = 0
			else:
				# handle the trailing escapes
				if escape_level:
					events.append(self.kescaped('\x1b' * escape_level))
			return events
		else:
			# empty keys
			return []

	def draw(self):
		"""
		Draw events *from* the source.
		"""
		data = self.source()
		if not data:
			return None
		decoded = data.decode(self.encoding)
		return self.kevent(decoded)

	def __iter__(self):
		return self

	def __next__(self):
		return self.draw()

class Control(object):
	"""
	UNIX Terminal controller.

	This class is fundamental and should be subclassed
	in order to provide the desired functionality.
	"""
	Input = Input
	Output = Output

	def __init__(self, filenos, input, output):
		self.fio = filenos
		self.input = input
		self.output = output

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

		tty = Teletype(os.environ['TERM'])
		return typ(
			filenos,
			typ.Input(tty, encoding, doread),
			typ.Output(tty, encoding, dowrite)
		)
