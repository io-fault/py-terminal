from .. import matrix as library

def test_offsets(test):
	"""
	# Check the character width analysis.
	"""

	# one-to-one mapping
	seq = [("first",), ("second",), (" and some more",)]
	for x in range(6):
		test/x == list(library.offsets(seq, x))[0]

	test/list(library.offsets(seq, *range(6))) == list(range(6))

	# empty line
	seq = [("",)]
	xo, = library.offsets(seq, 0)
	test/xo == 0

	test/IndexError ^ library.offsets(seq, 1).__next__

	# wide characters
	seq = [("林花謝了春紅",)]
	for x in range(6):
		xo, = library.offsets(seq, x)
		test/xo == (x*2)

	seq = [("f林o花謝了春紅",)]
	xo, = library.offsets(seq, 2)
	test/xo == 3
	xo, = library.offsets(seq, 3)
	test/xo == 4
	xo, = library.offsets(seq, 4)
	test/xo == 6

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules[__name__])
