"""
# Developer tool used to observe the transformed events from received from standard input.
"""
import sys
import os
from .. import library

def main():
	library.restore_at_exit()
	library.device.set_raw(0)
	d = library.Display()
	os.write(0, d.enable_mouse())

	while True:
		data = os.read(0, 128)
		string = data.decode('utf-8')
		for k in library.construct_character_events(string):
			print(repr(k) + '\r')
			if k.modifiers.control == True and k.identity == 'c':
				sys.exit(1)

if __name__ == '__main__':
	main()
