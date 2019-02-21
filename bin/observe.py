"""
# Developer tool used to observe the transformed events from received from standard input.
"""
import sys
import os
from .. import library
from .. import events
from ...system.tty import Device

def loop():
	while True:
		data = os.read(0, 128)
		string = data.decode('utf-8')
		for k in events.construct_character_events(string):
			print(repr(k) + '\r')
			if k.type == 'control' and k.identity == 'c':
				sys.exit(1)

def main():
	library.restore_at_exit()
	tty = Device(2)
	tty.set_raw()
	d = library.Display()
	os.write(1, d.enable_mouse())
	loop()

if __name__ == '__main__':
	main()
