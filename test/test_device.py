from .. import device

def test_literal_events(test):
	print(device.literal_events('ff'))
	test/device.literal_events('f') == (device.Character('literal', 'f', 'f', ),)
	test/device.literal_events('ff') == (device.Character('literal', 'f', 'f',),)*2

if __name__ == '__main__':
	import sys; from ...development import libtest
	libtest.execute(sys.modules[__name__])
