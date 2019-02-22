"""
# The terminal I/O interfaces. The module consists of four conceptual areas: input, output,
# settings management, and control management.

# The input portions cover the data structures used to represent character (key) events, &Character,
# and the function used to construct them from an arbitrary bytes stream.

# The output portions are primarily two classes used to render the terminal control codes
# for a particular operation, essentially high-level tput. &Display for the entire terminal
# screen and &Area for displaying to parts of the screen.

# Settings management is covered with a few functions to configure the terminal in raw mode
# and store and restore the settings themselves.

# The control portion keeps state about the process-local controller of the terminal and any
# requests for control. This is a local version of the process signals used by sessions to
# manage terminal access for concurrent jobs.

# Coloring:
	# /textcolor/
		# Foreground color.
	# /cellcolor/
		# Uppermost background color. (opacity mixing?)
	# /foreground/
		# Default text color.
	# /background/
		# Default cell color.
"""
import sys
import os
import tty
import termios
import fcntl
import array
import contextlib
import collections
import operator
import functools
import itertools

pastels = {
	'purple': 0x875fff,
	'blue': 0x0087d7,
	'cyan': 0x6b9aea,
	'green': 0x77DD77,
	'magenta': 0xF49AC2,
	'orange': 0xFFB347,
	'pink': 0xFFD1DC,
	'violet': 0xCB99C9,
	'yellow': 0xFDFD96,
	'red': 0xFF6961,
	'gray': 0xCFCFC4,
	#'cyan': 0x6d889a, metallic green
	#'blue-green': 0x0D98BA,
	#'pink': 0xDEA5A4, dark pink
	#'red': 0xD75F5F, dark red
}

theme = {
	'number': 'blue',
	'text': 'gray',
	'core': 'purple',
	'date': 'yellow',
	'time': 'red',
	'timestamp': 'orange',
}

def restore_at_exit():
	"""
	# Save the Terminal state and register an atexit handler to restore it.

	# Called once when the process is started to restore the terminal state.
	"""
	import atexit
	from . import control

	with open('/dev/tty', mode='r+b') as tty:
		def _restore_terminal(path='/dev/tty', ctl=control, terminal_state=termios.tcgetattr(tty.fileno())):
			lw = ctl.optset('line-wrapping')
			dm = ctl.optrst('mouse-drag', 'mouse-events')
			# in case cursor was hidden
			with open(path, mode='r+b') as f:
				# bit of a hack and assumes no other state changes need to occur.
				resets = b'\x1b[?12l\x1b[?25h' # normalize cursor
				resets += dm
				resets += lw
				f.write(resets)
				termios.tcsetattr(f.fileno(), termios.TCSADRAIN, terminal_state)

	atexit.register(_restore_terminal)

def scale(n, target = (1, 100), origin = (0, 0xFFFFFFFF), divmod = divmod):
	"""
	# Given a number, target range, and a origin range. Project the number
	# onto the target range so that the projected number
	# is proportional to the target range with respect to the number's
	# relative position in the origin range. For instance::

	>>> scale(5, target=(1,100), origin=(1,10))
	(50, 0, 9)

	# The return is a triple: (N, remainder, origin[1] - origin[0])
	# Where the second item is the remainder with the difference between the source
	# range's end and beginning.
	"""
	# The relative complexity of this sequence of computations is due to the
	# need to push division toward the end of the transformation sequence. That
	# is, greater clarity can be achieved with some reorganization, but this
	# would require the use of floating point operations, which is not desirable
	# for some use cases where "perfect" scaling (index projections) is desired.

	dx, dy = target
	sx, sy = origin
	# source range
	# (this is used to adjust 'n' relative to zero, see 'N' below)
	sb = sy - sx
	# destination range
	# (used to map the adjusted 'n' relative to the destination)
	db = dy - dx
	# bring N relative to *beginning of the source range*
	N = n - sx
	# magnify N to the destination range
	# divmod by the source range to get N relative to the
	# *the destination range*
	n, r = divmod(N * db, sb)
	# dx + N to make N relative to beginning of the destination range
	return dx + n, r, sb
