"""
# Dictionary for terminal color identifiers and 24-bit code mapping functions for xterm-256 colors.

# The &colors mapping provides named access to the terminal's configured colors; the
# often available sixteen colors (tty-16) and various aliases for some xterm-256 indexes. The values
# of this dictionary are numeric identifiers usable with &.core.RenderParameters which recognizes positive
# numbers as 24-bit RGB values and negative numbers as a contrived index selecting
# colors from common palettes such as tty-16, xterm-256, and the default text and cell color.

# [ Common Colors ]

# The default cell and text color can be addressed in &colors using `'terminal-default'`. This entry
# should not be changed as it is the only color index with two color values: the foreground color and
# the background color.

# Most of the common color names refer to the tty-16 palette available in most terminals.
# By default, these colors map to normal (non-bright) colors in the dictionary.
# Bright colors from tty-16 must use the qualified form with the `'absolute-'` prefix,
# &[Relative and Absolute Colors].

# - `'black'`
# - `'red'`
# - `'green'`
# - `'yellow'`
# - `'blue'`
# - `'magenta'`
# - `'cyan'`
# - `'white'`

# As an extension, some bindings to the xterm-256 colors palette are provided as well:

# - `'gray'`
# - `'violet'`
# - `'teal'`
# - `'pink'`
# - `'orange'`
# - `'purple'`

# Example usage being:

#!/pl/python
	from fault.terminal import palette
	from fault.terminal import core
	fg = palette.colors['blue']
	bg = palette.colors['terminal-default']
	trp_blue_text = core.RenderParameters.from_colors(fg, bg)

# However, &.core.RenderParameters is normally accessed through matrix contexts as opposed
# to directly from the &.core module. This example is only meant to clarify the location
# of the color indexes and the type used to hold them.

# [ Relative and Absolute Colors ]

# The &colors dictionary also uses project local terminology to describe the tty-16 palette.
# The color names are intended to slightly generalize the concept of the color as a color slot.
# Notably, this is intended to encourage the expectation that a terminal has been customized,
# potentially, significantly.

# Most bright colors are called "absolute" and regular colors are called "relative". Absolute
# is used as an exaggeration meaning to imply emphasis, and relative means relative to the theme.
# For example, normal red is identified using `'relative-red'` and bright red is identified using
# `'absolute-red'`.

# These qualifications are used to make a distinction between a color slot and
# an actual color or a color chosen from the xterm-256 palette. While these entries can be
# modified, it is usually better to use and override unqualified color names.

# [ Other Color Slots ]

# In addition to relative and absolute names referring to most of the sixteen colors available,
# few are renamed entirely in order to encourage customization of the tty-16 slots.

# /`'background-limit'`/
	# Usually identified as normal black. This is intended to refer to a color
	# that is darker or lighter than the actual background.
	# Locally, this is used for inverted text areas.
# /`'foreground-adjacent'`/
	# Usually identified as normal white. Expected to be a somewhat light gray for dark themes.
# /`'background-adjacent'`/
	# Usually identified as bright black. Expected to be a dark gray for dark themes.
	# Locally, this is used as a border color.
# /`'foreground-limit'`/
	# Usually identified as bright white. This is intended to refer to a color
	# that is lighter or darker than the actual foreground.
# /`'application-border'`/
	# Alias for (id)`background-adjacent`. This is intended to be used as a default for drawing borders.

# The color slots should be configured to produce a progression with limit and default being
# close in value: (illustration)`limit -> default -> adjacent`.

# Where limit is the (relative) maximum or minimum color value, and default is the
# terminal-default cell or text color. While limit and default should be close in value, adjacents
# should be a fairly significant step away from default.
"""
import functools

# Identifiers for the configured sixteen colors.
# The numeric identifiers are mapped to terminal escape codes in &.matrix.
colors = {
	'terminal-default': -1024, # Identifies default cell and text color.
	'application-border': -236,

	# Common Names; bound to normal tty-16 colors palette by default.
	'black': -512,
	'red': -513,
	'green': -514,
	'yellow': -515,
	'blue': -516,
	'magenta': -517,
	'cyan': -518,
	'white': -519,

	# Extensions using xterm-256; intentionally a modest list.
	'gray': -248,
	'violet': -141,
	'teal': -24, # A little dark, but there are no other options aside from truecolor.
	'pink': -212,
	'orange': -209,
	'purple': -54,
	'chartreuse': -119,
	'olive': -101,
	'indigo': -55,
	'maroon': -89,
	'coral': -210,
	'beige': -231,
	'tan': -182,

	# Hard references to the sixteen color palette.
	'background-limit': -512, # Usually 0x000000; a color relatively beyond the terminal default cell.

	'relative-red': -513,
	'relative-green': -514,
	'relative-yellow': -515,
	'relative-blue': -516,
	'relative-magenta': -517,
	'relative-cyan': -518,

	'foreground-adjacent': -519, # The "white" slot.
	'background-adjacent': -520, # The "bright black" slot.

	# Brights
	'absolute-red': -521,
	'absolute-green': -522,
	'absolute-yellow': -523,
	'absolute-blue': -524,
	'absolute-magenta': -525,
	'absolute-cyan': -526,

	'foreground-limit': -527, # Usually 0xFFFFFF; a color relatively beyond the terminal default text.
}

remapped = {
	'application-border': -520, # background-adjacent.
	'violet': -517, # tty-16 magenta slot
	'pink': -525, # tty-16 bright magenta slot
	'teal': -518, # tty-16 cyan slot
	'orange': -526, # tty-16 bright cyan slot

	# Rewrite local bindings to xterm-256 entries to
	# maintain the possible expectation of these referring to exact colors.
	'cyan': -52,
	'magenta': -200,
	'white': -232,
	'black': -1,
}

# Temporary; environment variable should be used to select whether or not it should be applied.
colors.update(remapped)

def gray_palette(index):
	"""
	# Twenty four shades. Map range(24) for the full palette.
	# Returns a tuple with the 24-bit RGB value and the code.

	# White and black are not included.
	"""
	if index < 0:
		index = 0
	elif index > 23:
		index = 23

	base = index * 10 + 8

	return ((base << 16) | (base << 8) | base), index + 232

def gray_code(color):
	"""
	# Covert the given 24-bit RGB color into a gray color code.

	# If the color does not have an exact match in the palette, the returned code may
	# not be a reaonable substitute for the given color.
	"""
	r = (color - 8) // 10
	return r + 232

def scale_gray(color):
	"""
	# Return the closest gray available in the palette.
	"""
	return gray_palette(gray_code(color & 0xFF) - 232)[0]

def color_palette(r, g, b):
	"""
	# Select a color from the 256-color palette using 0-6 indexes for each color.

	# Map the product of three range(6) instances to render the full palette.
	"""
	code = 16 + (r * 36) + (g * 6) + b

	red_value = green_value = blue_value = 0
	if r:
		red_value = r * 40 + 55
	if g:
		green_value = g * 40 + 55
	if b:
		blue_value = b * 40 + 55

	value = (red_value << 16) | (green_value << 8) | blue_value

	return (value, code)

def color_code(color):
	"""
	# Convert the given 24-bit RGB color into a terminal color code.

	# If the color does not have an exact match in the palette, the returned code may
	# not be a reaonable substitute for the given color.
	"""
	r, g, b = (color & 0xFF0000) >> 16, (color & 0x00FF00) >> 8, (color & 0xFF)
	ri = (r - 55) // 40

	if ri < 0:
		ri = 0
	gi = (g - 55) // 40
	if gi < 0:
		gi = 0
	bi = (b - 55) // 40
	if bi < 0:
		bi = 0

	code = 16 + (ri * 36) + (gi * 6) + bi
	return code

def scale_color(r, g, b, initial = 0x5f):
	"""
	# Map the given RGB color to the one closest in the xterm-256 palette.

	# The ranges start at zero, 0x5f, and then increments to 40.

	# ! WARNING:
		# This is quite broken outside of exact matches.
	"""
	color = 0

	for x in (r,g,b):
		color = color << 8

		if x < initial:
			# initial increment is inconsistent, so handle specially.
			x = int(round(x / initial)) * initial
		else:
			x = initial + (int(round((x - initial) / 40)) * 40)

		# apply value
		color = color | x

	return color

def translate(rgb:int):
	"""
	# Translate the given 24-bit RGB color into a terminal color and gray colors that exist in
	# their corresponding palette.

	# This function analyzes the given RGB color and chooses the closest value in
	# both gray and color palettes. &scale_gray and &scale_color are used to the select
	# the closest value in the corresponding palette.

	# [ Return ]
	# A pair of tuples containing both the scaled gray and color. The tuples are
	# pairs with the first item designating whether it's color or gray and the second
	# item being the scaled value.
	"""
	typ = None
	bw = 0

	r = (rgb >> 16) & 0xFF
	g = (rgb >> 8) & 0xFF
	b = (rgb >> 0) & 0xFF

	# if the values are within a range relative to the average, identify it as a gray
	avg = ((r + g + b) / 3)
	gray = int(avg)

	# select closest from each table.
	r = [
		('color', scale_color(r, g, b)),
		('gray', scale_gray(gray)),
	]
	r.sort(key = lambda x: abs(x[1] - rgb))

	return tuple(r)

def color(translation):
	"""
	# Return the 24-bit RGB value from a translation tuple.
	"""
	return translation[0][1]

def code(translation):
	"""
	# Return the terminal color code to use given the translation.
	# Simply select the initial item as the translated values are sorted in &translate.
	"""
	typ, value = translation[0]

	if typ == 'gray':
		return gray_code(value & 0xFF)
	else:
		return color_code(value)

@functools.lru_cache(64)
def code_string(translation):
	"""
	# The translation's code in bytes form for sending to the display.
	"""
	return str(code(translation)).encode('utf-8')

def index():
	"""
	# Construct and return a full index of color codes to their corresponding RGB value.
	"""
	import itertools
	idx = dict()
	idx.update(((v, k) for k, v in map(gray_palette, range(24))))
	idx.update(((v, k) for k, v in itertools.starmap(
		color_palette, itertools.product(range(6),range(6),range(6))
	)))
	return idx

if __name__ == '__main__':
	import sys
	from . import matrix
	d = matrix.Screen()
	# render a palette to the screen
	escape = '\x1b['.__add__

	# Part of the initial escape.
	separator = ';'
	terminator = 'm'

	fg = '38;5;'
	bg = '48;5;'
	normal = escape('0m')

	args = sys.argv[1:]
	if args:
		color, text = args
		normal = escape('0m')
		sys.stderr.write(escape(fg) + color + 'm' + text + normal + ' eof\n')
		print("color = lambda x: '\\x1b[38;5;{0}m' + x + {1}".format(color, repr(normal)))
	else:
		ri = index()
		i = 0
		for r in range(6):
			for g in range(6):
				for b in range(6):
					i = i + 1
					v, c = color_palette(r, g, b)
					t = hex(ri[c])[2:].rjust(6, '0')
					t += '(' + str(c).rjust(3, ' ') + ')'
					sys.stderr.write((escape(bg) + str(c) + 'm     ' + normal + ': ' + t.rjust(3, ' ') + ' '))
					if i > 5:
						sys.stderr.write('\n')
						i = 0
		sys.stderr.write('\n')
		for g in range(24):
			i = i + 1
			v, c = gray_palette(g)
			t = hex(ri[c])[2:].rjust(6, '0')
			t += '(' + str(c).rjust(3, ' ') + ')'
			sys.stderr.write((escape(bg) + str(c) + 'm     ' + normal + ': ' + t.rjust(3, ' ') + ' '))
			if i > 5:
				sys.stderr.write('\n')
				i = 0
		sys.stderr.write('\n')
