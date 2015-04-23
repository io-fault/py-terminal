"""
fault.io based interactive console
"""
import sys
import queue
import functools
import array
import locale

from .. import device
from .. import library

from ...io import library as iolib

class Events(iolib.Transformer):
	"""
	Transformer representing keyboard input.
	"""
	def __init__(self, context):
		self.context = context

	def _thread(self):
		with open('/dev/tty', 'r+b') as terminal_input:
			while True:
				data = terminal_input.read(256)
				self.context.enqueue(
					functools.partial(self.process, None, data)
				)

	def process(self, flow, data):
		# taks raw data and emits Key() instances to a Controller
		self.emit(flow, data)

class Application(iolib.Transformer):
	"""
	The terminal application state.
	"""
	def __init__(self, context):
		pass

	def process(self, flow, keys):
		# receives Key() instances and emits display events
		output = ''
		output += (repr(data) + '\r\n')

		self.emit(flow, draw)

class Display(iolib.Transformer):
	"""
	Transformer representing the terminal display.
	"""
	def __init__(self, context):
		self.context = context
		self.queue = queue.Queue()

	def _thread(self):
		with open('/dev/tty', 'r+b') as terminal_display:
			while True:
				terminal_display.write(self.output.get())

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

	def process(self, flow, data):
		self.queue.put(b''.join(data))

class Single(iolib.Transformer):
	def __init__(self, context):
		self.context = context
		self.terminal = library.Terminal.stdtty()
		self.output = queue.Queue()

	def _write_thread(self):
		while True:
			writes = self.output.get()
			self.terminal.output.terminal(writes.encode('utf-8'))

	def _read_thread(self):
		while True:
			for x in self.terminal.events():
				for y in x:
					if y.control == True and y.identity == 'c':
						self.context.enqueue(self.context.terminate)
					else:
						self.context.enqueue(
							functools.partial(self.process, None, y)
						)

	def dispatch(self):
		self.context._exit_stack.enter_context(self.terminal)
		self.context.weave(self._write_thread)
		self.context.weave(self._read_thread)
		self.terminal.output.terminal(self.terminal.output.tty.hide().encode('utf-8'))
		self.context.log("foo\nbar\n")

	def emit(self, flow, data):
		self.output.put(data)

	def process(self, flow, data):
		output = ''
		output += (repr(data) + '\r\n')

		self.emit(flow, output)

def initialize_division(div):
	div.tree['terminal'] = {'console':Single}
	t = div.index[('terminal', 'console')] = Single(div.context)
	t.dispatch()

if __name__ == '__main__':
	library.restore_at_exit() # cursor is hidden and raw is enabled
	iolib.execute(console = (initialize_division,))
