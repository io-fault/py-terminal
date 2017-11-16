"""
# Color formatting for dates and timestamps.

# Formats timestamps with respect to another point in time to
# illustrate the distance from the reference point.
"""
from ...chronometry import metric

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

def f_timestamp(relation, timestamp, precision='microsecond'):
	"""
	# Format with respect to the &relation point in time.
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
	from .. import library as lt
	from ...chronometry import library as t
	dev = lt.device.Display()
	values = sys.argv[1:] # ri, path, ts, dir: libformat dir /

	now = t.now()
	for x in values:
		ts = t.Timestamp.of(iso=x)
		sys.stderr.buffer.write(dev.renderline(list(f_timestamp(now, ts))) + b'\n')
