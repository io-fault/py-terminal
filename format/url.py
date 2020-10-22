"""
# Color formatting for URL strings.
"""
from ...internet import ri

palette = {
	'yellow': 0xffff87,
	'blue': 0x0087ff,
}

colors = {
	'delimiter': 0x6c6c6c,
	'scheme': palette['blue'],
	'type': 0x6c6c6c,

	'user': 0xff5f00,
	'password': 0x5f0000,

	'host': 0x875faf,
	'port': 0x005f5f,

	'path-root': -1024,
	'path-segment': 0x6e6e6e,
	'delimiter-path-only': 0x6e6e6e,
	'delimiter-path-initial': 0x6e6e6e,
	'delimiter-path-root': 0x6e6e6e,
	'delimiter-path-segments': 0x6e6e6e,
	'delimiter-path-final': 0x6e6e6e,
	'resource': 0xFFFFFF,

	'query-key': 0x5fafff,
	'query-value': 0x949494,
	'fragment': 0x505050,
	('delimiter', "#"): 0xFF0000,
}

def f_struct(struct):
	for t in ri.tokens(struct):
		yield (t[1], colors.get(t[0], -1024))

def f_string(string):
	"""
	# Format the string returning an iterable for use with &.matrix.Context.render
	"""
	return f_struct(ri.parse(string))

if __name__ == '__main__':
	import sys, itertools
	from .. import matrix
	screen = matrix.Screen()
	values = sys.argv[1:] # ri, path, ts, dir: libformat dir /

	rp = screen.terminal_type.normal_render_parameters
	for x in values:
		ph = screen.Phrase.from_words(
			itertools.chain.from_iterable(
				rp.apply(textcolor=color).form(s)
				for s, color in f_string(x)
			)
		)
		sys.stderr.buffer.write(
			b''.join(screen.render(ph)) + b'\n'
		)
