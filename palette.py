"""
# Color code translations for the 256-color palette defined by xterm.

# &translate and &code_string are the primary functions used to select 256-color palette
# entries from 24-bit RGB values.
"""
import functools

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
	# Map the given RGB color to the one closest in the xterm palette.

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
	# Translate the given RGB color into a terminal color and gray colors that exist in
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

	normal = escape(bg) + '0m'
	fgnormal = escape(fg) + '16m'

	args = sys.argv[1:]
	if args:
		color, text = args
		normal = escape('0') + 'm'
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
