from .. import events

def test_literal_events(test):
	test/events.literal_events('f') == (events.Character(('literal', 'f', 'f', 0)),)
	test/events.literal_events('ff') == (events.Character(('literal', 'f', 'f', 0)),)*2

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules[__name__])
