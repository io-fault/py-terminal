"""
Color code translations for 256-color supporting terminals. Sourced from xterm.
"""

def gray_palette(index):
	"""
	Twenty four shades. Map range(24) for the full palette.

	White and black are not included.
	"""
	if index < 0:
		index = 0
	elif index > 23:
		index = 23

	base = index * 10 + 8

	return (base<<16|base<<8|base), index + 232

def gray_code(color):
	"""
	Look up a particular gray code in the gray palette using a 32-bit color.
	"""
	value = value & 0xFF
	r = (value - 8) // 10
	return r + 232

def color_palette(red, green, blue):
	"""
	Select a color from the 256-color palette using 0-6 indexes for each color.

	Map the combination of three range(6) instances to render the full palette.
	"""
	code = 16 + (red * 36) + (green * 6) + blue

	red_value = green_value = blue_value = 0
	if red:
		red_value = red * 40 + 55
	if green:
		green_value = green * 40 + 55
	if blue:
		blue_value = blue * 40 + 55
	value = (red_value << 16) | (green_value << 8) | blue_value

	return (value, code)

def color_code(color):
	"""
	Look up a particular gray code in the gray palette using a 32-bit color.
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

grays = dict(map(gray_palette, range(24)))

sixteen_colors = {
	# grays
	0x000000: 0,
	0xc0c0c0: 7,
	0x808080: 8,
	0xFFFFFF: 15,

	# red
	0x800000: 1,
	0xFF0000: 9,

	# green
	0x008000: 2,
	0x00FF00: 10,

	# yellow
	0x808000: 3,
	0xFFFF00: 11,

	# blue
	0x000080: 4,
	0x0000FF: 12,

	# magenta
	0x800080: 5,
	0xFF00FF: 13,

	# cyan
	0x008080: 6,
	0x00FFFF: 14,
}
