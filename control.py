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
# /margin-bell/
	# Control the margin bell.
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

# /cursed/
	# The default configuration type referrenced by &setup; used by raw line disciplines.
# /cooked/
	# A reasonable set of defaults for use with cooked line disciplines.
	# ! NOTE: Used primarily as an inverse for &cursed.
# /observe/
	# Configuration used by &.terminal.bin.observe to maximize the perceived events.
"""
from . import matrix

private_mode_options = {
	# CSI ? {0} [lhsr]
	'alternate-screen': 1049,
	'line-wrap': 7,
	'margin-bell': 44,

	'cursor-visible': 25,
	'cursor-blink': 12,

	'mouse-extended-protocol': 1006, # SGR's format is sane and the only supported one in &.events.
	'mouse-events': 1000,
	'mouse-drag': 1002,
	'mouse-motion': 1003,
	'bracket-paste-mode': 2004,
	'mouse-highlight': 1001,

	# xterm
	'focus-events': 1004,
	'meta-escape': 1036,
	'log': 46,

	# rxvt
	'scroll-bar': 30,
	'scroll-bottom-on-output': 1010,
	'scroll-bottom-on-input': 1011,
}

def configuration(ttype, settings, options=private_mode_options) -> bytes:
	"""
	# Construct the initialization and restoration sequences for the given &settings.

	# &settings is normally retrieved by selecting an entry from &ctypes.
	"""

	undo, mode, isets, irsts = settings
	sets = [options[k] for k in isets]
	rsts = [options[k] for k in irsts]
	sets.sort()
	rsts.sort()

	return (
		undo,
		ttype.decset(sets) if sets else b'',
		ttype.decrst(rsts) if rsts else b'',
		ttype.pm_save(sets+rsts),
		ttype.pm_restore(sets+rsts)
	)

# Configuration Types (ttydevice mode, PM sets, PM resets)
ctypes = {
	'cursed': (
		'cooked', # revert using
		'raw', {
			'mouse-extended-protocol',
			'mouse-drag',
			'alternate-screen',
			'focus-events',
			'bracket-paste-mode',
		}, {
			'line-wrap',
			'margin-bell',
			'cursor-visible',
		},
	),
	'cooked': (
		None, # no revert
		'cooked', {
			'line-wrap',
			'cursor-visible',
			# No margin bell assignment; force outer program to re-enable.
		}, {
			'mouse-extended-protocol',
			'mouse-events',
			'mouse-drag',
			'mouse-motion',
			'alternate-screen',
			'focus-events',
			'bracket-paste-mode',
		},
	),
	'observe': (
		'cooked', # revert using
		'raw', {
			'mouse-extended-protocol',
			'mouse-events',
			'mouse-drag',
			'mouse-motion',
			'bracket-paste-mode',
			'focus-events',
		}, (),
	),
	# no-op ctype
	'prepared': (None, None, (), ()),
}

def _terminal_ctl_exit(tty, ctype, write, restoration, limit=64):
	# Usually called by &setup via atexit
	issue_warning = False
	try:
		while restoration and limit > 0:
			restoration = restoration[write(tty.fileno(), restoration):]
			limit -= 1
		else:
			if limit <= 0:
				issue_warning = True

		# No-op if mode is None.
		tty.restore() # fault.system.tty.Device instance
	except BaseException as err:
		issue_warning = True
		raise
	finally:
		if issue_warning:
			import sys
			message = "(tty) terminal configuration may be incoherent"
			sys.stderr.write("\n\r[!* WARNING: %s]\n\r" %(message,))

def _terminal_ctl_init(tty, ctype, write, initialization, limit=64):
	# Usually called by &setup.
	mode = ctypes[ctype][1]
	if mode is not None:
		init_dev = getattr(tty, 'set_' + mode) # set_raw, normally
		init_dev()

	while initialization and limit > 0:
		initialization = initialization[write(tty.fileno(), initialization):]
		limit -= 1

	if limit <= 0 and initialization:
		# Didn't finish writing init?
		pass

def setup(
		ctype:str='cursed',
		ttype:matrix.Type=matrix.utf8_terminal_type,
		destruct=False,
		ttydevice=None,
		atinit=b'', atexit=b'', limit=64,
	):
	"""
	# Initialize the terminal and kernel line discipline for the given &ctype and
	# register an atexit handler to reconfigure the terminal into a state
	# that is usually consistent with a shell's expectations.

	# The given &ttydevice or the one created will be returned.

	# &setup is intended to be a one-shot intiailization method for applications
	# that can use one of the &.control.ctype entries. If it is insufficient,
	# applications should implement their own variant.

	# [ Parameters ]
	# /ctype/
		# The &[Configuration Type] to apply immediately after the atexit handler has been registered.
		# Usually, the default, `'cursed'`, is the desired value and selects the configuration
		# set from &ctypes.
	# /ttype/
		# The &matrix.Type instance to use to construct the initialization and restoration
		# sequences. Defaults to the &matrix.utf8_terminal_type. Applications
		# needing to select a distinct Type or encoding need to supply this instead
		# of the default.
	# /destruct/
		# Clear the module's globals (&.control) and remove it from &sys.modules after writing
		# the initialization string to &ttydevice.fileno and registering the atexit handler.
		# For most applications using &.control, &setup is called once and the module
		# is never used again. By default, this is &False and the module is retained in memory.
	# /ttydevice/
		# The &fault.system.tty.Device instance whose restore method should be called atexit.
		# If &tty is not provided, a &fault.system.tty.Device instance will be created from the
		# system's tty path (usually (fs/path)`/dev/tty`) and call its `record` method.
	# /atinit/
		# Additional binary string to write to the terminal device at initialization.
	# /atexit/
		# Additional binary string to write to the terminal device at exit.
	"""
	import functools
	import atexit as ae
	from os import write

	if ttydevice is None:
		from ..system.tty import Device
		ttydevice = Device.open()
	ttydevice.record()

	undomode, s, r, saves, restores = configuration(ttype, ctypes[ctype])
	init = saves + s + r + ttype.wm(22,0) + atinit

	undo = b''
	if undomode is not None:
		undo = b''.join(configuration(ttype, ctypes[undomode])[1:3])

	restoration = undo + restores + ttype.wm_title('') + ttype.wm(23, 0)
	restoration += atexit

	ae.register(functools.partial(_terminal_ctl_exit, ttydevice, ctype, write, restoration, limit=limit))
	_terminal_ctl_init(ttydevice, ctype, write, init, limit=limit)

	if destruct is True:
		import sys
		m = sys.modules.pop(__name__)
		m.__dict__.clear()
		del m

	return ttydevice
