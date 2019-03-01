"""
# Terminal control sequences for emulator configuration management.

# While &.matrix.Context constructs sequences for drawing, the functions and data
# here provide high-level access to options that are usually maintained for the duration
# of the controlling process.

# The &options dictionary provides a mapping from a contrived option Symbols to the codes
# used to compose the escape sequence. Most &.control interfaces work with &[Symbols].

# The functions here behave similarly to &.matrix; the control sequences are constructed
# and returned for the caller to emit to the terminal in order to avoid state and to permit
# application control over buffering.
# &setup is the one notable exception and provides a solution for the common case of
# terminal initialization for the duration of the process.

# [ Symbols ]

# Symbols present in &options are described below. This will usually be a subset of
# the terminal's configuration intensely focused on what applications need to control
# for proper rendering.

# /line-wrap/
	# Control line wrapping.
# /cursor-visible/
	# Control whether the cursor is visible.
# /cursor-blink/
	# Control whether the cursor blinks.
# /mouse-extended-protocol/
	# Use the SGR protocol for mouse events.
# /mouse-events/
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
	# Subscribe to window enter and exit events.
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

# [ Configuration Types ]

# &[Symbols] will be added when desireable features are added by emulators. In order to keep usage
# consistent as possible without requiring changes to applications, configuration types are defined
# to allow applications to refer to and define groups of symbols.

# /curse/
	# The default configuration type referrenced by &setup; used by raw line disciplines.
# /bless/
	# A reasonable set of defaults for use with cooked line disciplines.
# /observe/
	# Configuration used by &.terminal.bin.observe to maximize the perceived events.

# [ Engineering ]
# The sequences are hard coded here. &..terminal is generally focused on modern terminal emulators, but
# in this case, using terminfo may be desireable to ensure proper configuration.
"""
import typing

_set_flag = b'h'
_rst_flag = b'l'
_save_flag = b's'
_restore_flag = b'r'
_flag_map = {True:_set_flag, False:_rst_flag}
_escape_sequence = b'\x1b[?'

options = {
	'alternate-screen': b'1049',
	'line-wrap': b'7',
	'cursor-visible': b'25',
	'cursor-blink': b'12',

	'mouse-extended-protocol': b'1006', # SGR's format is sane and the only supported one in &.events.
	'mouse-events': b'1000',
	'mouse-drag': b'1002',
	'mouse-motion': b'1003',
	'bracket-paste-mode': b'2004',
	'mouse-highlight': b'1001',

	# xterm
	'focus-events': b'1004',
	'meta-escape': b'1036',
	'log': b'46',

	# rxvt
	'scroll-bar': b'30',
	'scroll-bottom-on-output': b'1010',
	'scroll-bottom-on-input': b'1011',
}

def _build(flag, fields, esc=_escape_sequence):
	for x in fields:
		code = options[x]
		if code:
			yield esc + code + flag

def save(symbols:typing.Sequence[str]) -> bytes:
	"""
	# Save the Private Mode values referenced by &symbols.
	"""
	return b''.join(_build(_save_flag, symbols))

def restore(symbols:typing.Sequence[str]) -> bytes:
	"""
	# Restore the Private Mode values referenced by &symbols.
	"""
	return b''.join(_build(_restore_flag, symbols))

def enable(symbols:typing.Sequence[str]) -> bytes:
	"""
	# Construct escape sequences enabling the options cited in &symbols.
	# The strings in &symbols must be keys from &options.
	"""
	return b''.join(_build(_set_flag, symbols))

def disable(symbols:typing.Sequence[str]) -> bytes:
	"""
	# Construct escape sequences disabling the options cited in &symbols.
	# The strings in &symbols must be keys from &options.
	"""
	return b''.join(_build(_rst_flag, symbols))

def configure(settings:typing.Mapping, escape_sequence=b'\x1b[?', options=options) -> bytes:
	"""
	# Construct the control sequences necessary to change the terminal's options
	# to reflect the given &settings mapping.

	# The keys in &settings must be keys from &options and their values determine whether
	# or not to enable or disable the option.
	"""
	return b''.join([
		escape_sequence + options[symbol] + _flag_map[value] # No such symbol or value is not a bool.
		for (symbol, value) in settings.items()
		if options[symbol] # Allow symbols to be globally disabled.
	])

ctypes = {
	'curse': ('raw', {
		'mouse-extended-protocol': True,
		'mouse-drag': True,
		'alternate-screen': True,
		'focus-events': True,
		'line-wrap': False,
		'cursor-visible': False,
	}),
	'cooked': (None, {
		'mouse-events': False,
		'mouse-drag': False,
		'mouse-motion': False,
		'alternate-screen': False,
		'line-wrap': True,
		'cursor-visible': True,
		'focus-events': False,
	}),
	'observe': ('raw', {
		'mouse-extended-protocol': True,
		'mouse-motion': True,
		'bracket-paste-mode': True,
		'focus-events': True,
	}),
}

def _warn_incoherent(message="(tty) terminal configuration may be incoherent"):
	import sys
	sys.stderr.write("\n\r[!* WARNING: %s]\n\r" %(message,))

def _ctl_exit(tty, ctype, write):
	# Usually called by &setup.
	try:
		mode, cfg = ctypes[ctype]
		changes = restore(cfg.keys())
		while changes:
			changes = changes[write(tty.fileno(), changes):]
		tty.restore() # fault.system.tty.Device instance
	except BaseException as err:
		_warn_incoherent()
		raise

def _ctl_init(tty, ctype, write):
	# Usually called by &setup.
	mode, cfg = ctypes[ctype]
	init_dev = getattr(tty, 'set_' + mode) # set_raw, normally
	init_dev()

	changes = save(cfg.keys())
	changes += configure(cfg)
	while changes:
		changes = changes[write(tty.fileno(), changes):]

def setup(ctype='curse', tty=None):
	"""
	# Register an atexit handler to reconfigure the terminal into a state that is usually consistent
	# with a shell's expectations.

	# The given &tty or the created one will be returned.

	# [ Parameters ]
	# /ctype/
		# The Configuration Type to apply immediately after the atexit handler has been registered.
		# Usually, the default, `'curse'`, is the desired value and selects the configuration
		# set from &ctypes.
	# /tty/
		# The &fault.system.tty.Device whose restore method should be called atexit.
		# If &tty is not provided, a &fault.system.tty.Device instance will be created from the
		# system's tty path (usually (fs/path)`/dev/tty`).
	"""
	import functools
	import atexit
	from os import write

	if tty is None:
		from ..system.tty import Device
		tty = Device.open()
	tty.record()

	atexit.register(functools.partial(_ctl_exit, tty, ctype, write))
	_ctl_init(tty, ctype, write)

	return tty
