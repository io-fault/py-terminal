from .. import events

def test_ictlchr(test):
	"""
	# Check for basic consistency.
	"""
	# Special cases.
	test/events.ictlchr('?') == '\x7f'
	test/events.ictlchr(' ') == ' '

	# Normal range.
	test/events.ictlchr('[') == '\x1b'
	test/events.ictlchr('\\') == '\x1c'
	test/events.ictlchr(']') == '\x1d'
	test/events.ictlchr('^') == '\x1e'
	test/events.ictlchr('_') == '\x1f'
	test/events.ictlchr('@') == '\x00'

	test/events.ictlchr('a') == '\x01'
	test/events.ictlchr('z') == chr(1 + (ord('Z')-ord('A')))

	# Check invariant; ictlchr will .upper() the given string.
	test/events.ictlchr('A') == '\x01'
	test/events.ictlchr('Z') == chr(1 + (ord('Z')-ord('A')))

	# Out of range.
	test/ValueError ^ (lambda: events.ictlchr('%'))

	# Might be reasonable to explicitly raise this as a ValueError
	test/TypeError ^ (lambda: events.ictlchr('plural'))

def test_literal_events(test):
	test/events.char('f') == events.Character(('literal', 'f', 'f', 0))

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules[__name__])
