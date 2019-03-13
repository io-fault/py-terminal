"""
# Color formatting for file paths, URIs, and timestamps.
"""
import os

palette = {
	'yellow': 0xffff87,
	'blue': 0x0087ff,
}

route_colors = {
	'filesystem-root': palette['blue'],
	'warning': palette['yellow'],

	'directory': 0x0087ff,
	'executable': 0x008700,
	'file': 0xc6c6c6,

	'dot-file': 0x808080,
	'file-not-found': 0xaf0000,

	'link': 0xff0000,
	'device': 0xff5f00,
	'socket': 0xff5f00,
	'pipe': 0xff5f00,

	'path': 0x6e6e6e,
	'path-link': 0x005f87,
	'root-segments': 0x4e4e4e,

	'text/plain;pl=python': 0x875faf,
	'text/plain;sf=fault.txt': 0x875faf,
	'text/xml': 0x4e4e4e,

	None: None,
}

def route_is_link(route, islink=os.path.islink):
	try:
		return islink(str(route))
	except OSError:
		return False

def _f_route_factor_type(route, ia_link=route_is_link):
	idotpy = route / '__init__.py'
	file_exists = idotpy.exists()
	path = str(idotpy)
	islink = ia_link(path)
	if islink:
		if os.readlink(path) == 'context/root.py':
			return 'context'
	else:
		if file_exists:
			if (route / '.git').exists():
				return 'project'

	return 'unqualified'

def _f_route_path(root, route, _is_link=route_is_link):
	tid = route.identifier
	color = route_colors['path']

	while route.absolute != root.absolute and tid is not None:

		if tid in {'.', '..'}:
			yield ('/', (), color)
			yield (tid, (), 0xff0000)
		else:
			if _is_link(route):
				yield ('/', (), color)
				yield (tid, (), route_colors['path-link'])
			else:
				yield (tid + '/', (), color)

		route = route.container
		tid = route.identifier
	else:
		yield ('/', (), color)

def f_route_path(root, route):
	l = list(_f_route_path(root, route))
	l.reverse()
	return l

def f_route_identifier(route, warning=False):
	path = route.absolute
	if warning:
		t = 'warning'
	else:
		t = route.type()
		rid = route.identifier
		if t == 'file':
			if route.executable():
				t = 'executable'
			elif rid.endswith('.py'):
				t = 'text/plain;pl=python'
			elif rid == 'kfile':
				t = 'text/plain;sf=fault.txt'
			elif rid[:1] == ".":
				t = 'dot-file'
		elif t is None:
			t = 'file-not-found'

	return [(route.identifier, (), route_colors[t])]

def f_route_absolute(route, warning=False):
	"""
	# Format the absolute path of the given route.
	"""

	if route.identifier is None:
		# root directory path
		return [('/', (), route_colors['filesystem-root'])]

	root = route.container
	last = None

	while root.identifier is not None:
		ftyp = _f_route_factor_type(root)
		if ftyp == 'context':
			prefix = [(str(root), (), None)]
			break

		last = root
		root = root.container
	else:
		# no context package in path
		root = route.from_path('/')
		prefix = []

	return prefix + f_route_path(root, route.container) + f_route_identifier(route, warning=warning)

if __name__ == '__main__':
	import sys
	from ...routes import library as l
	from .. import matrix
	screen = matrix.Screen()
	values = sys.argv[1:]

	for x in values:
		r = l.File.from_path(x)
		phrase = matrix.Phrase.construct([
			(x[0], x[-1], None, matrix.Traits.construct(*x[1]))
			for x in f_route_absolute(r)
		])
		sys.stderr.buffer.write(b''.join(screen.render(phrase)) + b'\n')
