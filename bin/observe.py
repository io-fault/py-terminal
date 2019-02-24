"""
# Developer tool used to observe the transformed events from received from standard input.
"""
import sys
import os
from .. import events
from .. import control
from ...system.tty import Device

def loop():
	while True:
		data = os.read(0, 256)
		string = data.decode('utf-8')
		for k in events.construct_character_events(string):
			print(repr(k) + '\r')
			if k.type == 'control' and k.identity == 'c':
				sys.exit(1)

def main():
	tty = Device(2)
	tty.record()
	control.restore_at_exit(tty)
	tty.set_raw()
	options = control.choptions({
		'mouse-extended-protocol': True,
		'mouse-drag': True,
		'bracket-paste-mode': True,
	})
	os.write(1, options)
	loop()

if __name__ == '__main__':
	main()
