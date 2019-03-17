"""
# Developer tool used to observe the transformed events from received from standard input.
"""
import sys
import os
from .. import events

def loop(tty):
	fd = tty.fileno()
	while True:
		data = os.read(fd, 256)
		string = data.decode('utf-8')
		for k in events.construct_character_events(string):
			print(repr(k) + '\r')
			if k.type == 'control' and k.identity == 'c':
				sys.exit(1)

def main():
	from .. import control
	screen = control.matrix.Screen()
	sys.stdout.buffer.write(screen.set_window_title_text("Event Observations"))
	sys.stdout.buffer.write(screen.report_window_title_text())
	loop(control.setup(ctype='observe'))

if __name__ == '__main__':
	main()
