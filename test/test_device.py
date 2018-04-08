from .. import device

def test_literal_events(test):
	test/device.literal_events('f') == (device.core.Character(('literal', 'f', 'f', 0)),)
	test/device.literal_events('ff') == (device.core.Character(('literal', 'f', 'f', 0)),)*2

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules[__name__])
