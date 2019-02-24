"""
# Terminal control sequences for option management.

# While &.matrix.Context constructs sequences for drawing, the functions and data
# here provide high-level access to options that are usually maintained for the duration
# of the controlling process.

# The &options dictionary provides a mapping from a contrived option symbol to the code
# used to compose the escape sequence. All &.control interfaces work with symbols.

# [ Symbols ]

# Symbols present in &options are described below.

# /line-wrap/
	# Control line wrapping.
# /cursor-visible/
	# Control whether the cursor is visible.
# /cursor-blink/
	# Control whether the cursor blinks.
# /mouse-extended-protocol/
	# Use the SGR protocol for mouse events.
# /mouse-activations/
	# Subscribe to mouse button press events.
# /mouse-drag/
	# Subscribe to mouse button press events and motion within holds.
# /mouse-motion/
	# Subscribe to mouse button press events and motion within and outside of holds.
# /bracket-paste-mode/
	# Allow paste signals to be generated.
# /mouse-highlight/
	# Allow terminal-level mouse highlighting.
# /focus-events/
	# Subscribe to focus events.
# /alternate-screen/
	# Record the cursor position and switch to the alternate screen buffer.
	# Upon disabling, restore the original screen state.
# /meta-escape/
	# Enable escape qualified key events when the meta modifier is used.
# /scroll-bar/
	# Control scroll bar visibility.
# /scroll-bottom-on-output/
	# Control the effect of output being printed to the scrolling region.
# /scroll-bottom-on-input/
	# Control an effect of typing input into the terminal.
# /log/
	# Control the terminal's internal logging facility.
"""
import typing

_set_flag = b'h'
_rst_flag = b'l'

options = {
	'line-wrap': b'7',
	'cursor-visible': b'25',
	'cursor-blink': b'12',

	'mouse-extended-protocol': b'1006', # SGR's format is sane and the only supported one in &.events.
	'mouse-activations': b'1000', # press events only
	'mouse-drag': b'1002', # motion capture during drag and press events.
	'mouse-motion': b'1003', # everything
	'bracket-paste-mode': b'2004',
	'mouse-highlight': b'1001',

	# xterm
	'focus-events': b'1004', # terminal focus in and out events
	'alternate-screen': b'1049', # save cursor in normal buffer and switch to alternate buffer
	'meta-escape': b'1036',
	'log': b'46',

	# rxvt
	'scroll-bar': b'30',
	'scroll-bottom-on-output': b'1010',
	'scroll-bottom-on-input': b'1011',
}

def _build(flag, fields, escape_sequence=b'\x1b[?'):
	for x in fields:
		code = options[x]
		yield escape_sequence + code + flag

def enable(symbols:typing.Sequence[str]) -> bytes:
	"""
	# Construct escape sequences enabling the options cited in &symbols.
	# The strings in &symbols must be keys from &options.
	"""
	return b''.join(_build(_set_flag, fields))

def disable(symbols:typing.Sequence[str]) -> bytes:
	"""
	# Construct escape sequences disabling the options cited in &symbols.
	# The strings in &symbols must be keys from &options.
	"""
	return b''.join(_build(_rst_flag, fields))

def choptions(settings:typing.Mapping, _td={True:_set_flag, False:_rst_flag}, options=options) -> bytes:
	"""
	# Construct the control sequences necessary to change the terminal's options
	# to reflect the given &settings mapping.

	# The keys in &settings must be keys from &options and their values determine whether
	# or not to enable or disable the option.
	"""
	return b''.join([
		b'\x1b[?' + options[symbol] + _td[value] # No such symbol or value is not a bool.
		for (symbol, value) in settings.items()
	])

def restore_at_exit(tty=None):
	"""
	# Save the Terminal state and register an atexit handler to restore it.

	# Called once when the process is started to restore the terminal state.
	"""
	import atexit
	import os
	if tty is None:
		from ..system.tty import Device
		tty = Device.open()
		tty.record()

	def _restore_terminal(device=tty):
		changes = choptions({
			'mouse-motion': False,
			'alternate-screen': False,
			'line-wrap': True,
			'cursor-visible': True,
		})
		while changes:
			changes = changes[os.write(device.kport, changes):]
		device.restore()

	atexit.register(_restore_terminal)
