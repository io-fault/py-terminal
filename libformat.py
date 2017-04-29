"""
#  Color formatting for file paths, URIs, and timestamps.
"""
import os
import sys
import stat
from ..internet import ri

palette = {
	'yellow': 0xffff87,
	'blue': 0x0087ff,
}

route_colors = {
	'warning': 0xffff87,

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
	'text/xml': 0x4e4e4e,

	None: None,
}

ri_colors = {
	'delimiter': 0x6c6c6c,
	'scheme': palette['blue'],
	'type': 0x6c6c6c,

	'user': 0xff5f00,
	'password': 0x5f0000,

	'host': 0x875faf,
	'port': 0x005f5f,

	'path-root': None,
	'path-segment': 0x6e6e6e,
	'delimiter-path-only': 0x6e6e6e,
	'delimiter-path-initial': 0x6e6e6e,
	'delimiter-path-root': 0x6e6e6e,
	'delimiter-path-segments': 0x6e6e6e,
	'delimiter-path-final': 0x6e6e6e,
	'resource': 0xFFFFFF,

	'query-key': 0x5fafff,
	'query-value': 0x949494,
	'fragment': 0x303030,
	('delimiter', "#"): 0xFF0000,
}

def f_ri(struct):
	for t in ri.tokens(struct):
		yield (t[1], (), ri_colors.get(t[0]))

def route_is_link(route, islink=os.path.islink):
	try:
		return islink(str(route))
	except OSError:
		return False

def _f_route_path(route, _is_link=route_is_link):
	tid = route.identifier
	color = route_colors['path']

	while route.container.identifier is not None:

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
		if _is_link(route):
			yield ('/', (), 0x949494)
			yield (tid, (), route_colors['path-link'])
		else:
			yield ('/', (), 0x949494)
			yield (tid, (), 0xFFFFFF)

		yield ('/', (), 0xFFFFFF)

def f_route_path(route):
	l = list(_f_route_path(route))
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
		   elif rid[:1] == ".":
			   t = 'dot-file'
		elif t is None:
			t = 'file-not-found'

	return [(route.identifier, (), route_colors[t])]

def f_route_absolute(route, warning=False):
	return f_route_path(route.container) + f_route_identifier(route, warning=warning)

# Maps directly to xterm 256-colors.
behind = (
	0xff5f00,
	0xd75f00,
	0xaf5f00,
	0x870000,
	0x5f0000,
)
ahead = (
	0x005fff,
	0x005fd7,
	0x005faf,
	0x005f87,
	0x005f5f,
)

equivalence = 0x005f00
irrelevant = 0x585858
separator = 0xFFFFFF

def f_time_palette(delta, rate):
	rpos = position = int(rate(delta))
	if position == 0:
		return (0, equivalence)

	if delta < 0:
		palette = behind
	else:
		palette = ahead

	# Constrain to edges of color range.
	size = len(palette)
	if position >= size:
		position = size - 1
	elif position < 0:
		position = 0

	return rpos, palette[position]

def f_date(relation, subject):
	rd = relation.select('day')
	sd = subject.select('day')
	dd = rd - sd

	cposition, ccolor = f_time_palette(dd, rate=(lambda x: (abs(x) // 128) ** 0.5))
	mposition, mcolor = f_time_palette(dd, rate=(lambda x: (abs(x) // 30) ** 0.5))
	dposition, dcolor = f_time_palette(dd, rate=(lambda x: (abs(x) // 7) ** 0.5))

	y, m, d = subject.select('date')

	return [
		(str(y), (), ccolor),
		('-', (), separator),
		(str(m).rjust(2, '0'), (), mcolor),
		('-', (), separator),
		(str(d).rjust(2, '0'), (), dcolor),
	]

def f_time(relation, subject):
	h, M, s = subject.select('timeofday')
	m = subject.measure(relation)

	if abs(m) < m.of(hour=24):
		# Within 24 hours.
		secs = m.select('second')
		hposition, hcolor = f_time_palette(secs, rate=(lambda x: (abs(x) // (2*60*60)) ** 0.5))
		mposition, mcolor = f_time_palette(secs, rate=(lambda x: (abs(x) // 600) ** 0.5))
		sposition, scolor = f_time_palette(secs, rate=(lambda x: (abs(x) // 10) ** 0.5))

		return [
			(str(h).rjust(2, '0'), (), hcolor),
			(':', (), separator),
			(str(M).rjust(2, '0'), (), mcolor),
			(':', (), separator),
			(str(s).rjust(2, '0'), (), scolor),
		]
	else:
		# The delta was greater than one day and considers the time of day irrelevant.
		return [
			(str(h).rjust(2, '0'), (), irrelevant),
			(':', (), separator),
			(str(M).rjust(2, '0'), (), irrelevant),
			(':', (), separator),
			(str(s).rjust(2, '0'), (), irrelevant),
		]

from ..chronometry import metric
def f_subsecond(relation, timestamp, precision, exponents=metric.name_to_exponent):
	m = timestamp.measure(relation)
	ss = timestamp.select(precision, 'second')

	exp = -exponents[precision]
	if abs(m) > m.of(second=1):
		return [
			(str(ss).rjust(exp, '0'), (), irrelevant)
		]
	else:
		position, color = f_time_palette(m.select(precision), rate=(lambda x: (abs(x) // 1000) ** 0.5))
		return [
			(str(ss).rjust(exp, '0'), (), color)
		]
del metric

def f_timestamp(relation, timestamp, precision='microsecond'):
	"""
	#  Format with respect to the &relation point in time.
	"""
	prefix = f_date(relation, timestamp)
	suffix = f_time(relation, timestamp)
	yield from prefix
	yield ('T', (), separator)
	yield from suffix
	if precision is not None:
		yield ('.', (), separator)
		yield from f_subsecond(relation, timestamp, precision)

if __name__ == '__main__':
	import sys
	from . import library as lt
	dev = lt.device.Display()
	typ, *values = sys.argv[1:] # ri, path, ts, dir: libformat dir /

	if typ == 'ri':
		from ..internet import ri
		for x in values:
			ri = ri.parse(x)
			sys.stderr.buffer.write(dev.renderline(list(f_ri(ri))) + b'\n')
	elif typ == 'path':
		from ..routes import library as l
		for x in values:
			r = l.File.from_path(x)
			sys.stderr.buffer.write(dev.renderline(list(f_route(r))) + b'\n')
	elif typ == 'ts':
		from ..chronometry import library as t
		now = t.now()
		for x in values:
			ts = t.Timestamp.of(iso=x)
			sys.stderr.buffer.write(dev.renderline(list(f_timestamp(now, ts))) + b'\n')
	elif typ == 'dir':
		from ..routes import library as l
		from ..chronometry import library as t
		now = t.now()
		r = l.File.from_path(values[0])
		d, f = r.subnodes()
		fn = max(map(len, map(str, f+d)), default=10) + 2

		prefix = dev.renderline(f_route_path(r))
		for x in f + d:
			try:
				lm = x.get_last_modified()
			except FileNotFoundError:
				continue
			pl = len(str(x))
			sys.stderr.buffer.write(prefix + dev.renderline(f_route_identifier(x)) + (b' ' * (fn - pl)))
			sys.stderr.buffer.write(b'\t' + dev.renderline(list(f_timestamp(now, lm))) + b'\n')
			sys.stderr.buffer.flush()
