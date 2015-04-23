from .. import library

def main():
	terminal = library.Terminal.stdtty()
	with terminal:
		for x in terminal.events():
			for y in x:
				print(repr(y) + '\r')
				if y.control == True and y.identity == 'c':
					break
			else:
				continue
			break

if __name__ == '__main__':
	main()
