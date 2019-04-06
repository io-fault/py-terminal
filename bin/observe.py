"""
# Developer tool used to observe the transformed events from received from standard input.
"""
import sys
import os
from .. import events

def loop(tty):
	parser = events.parser()
	fd = tty.fileno()
	while True:
		data = os.read(fd, 1024*2)
		string = data.decode('utf-8')
		for k in parser.send((string, True)):
			print(repr(k) + '\r')
			if k.type == 'control' and k.identity == 'c':
				sys.exit(1)

def main():
	from .. import control
	screen = control.matrix.Screen()
	sys.stdout.buffer.write(screen.set_window_title_text("Event Observations"))
	loop(control.setup(ctype='observe'))

if __name__ == '__main__':
	main()
