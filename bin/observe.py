from .. import libterminal

def main():
	control = libterminal.Control.stdtty()
	with control:
		for x in control.events():
			for y in x:
				print(repr(y) + '\r')
				if y.control == True and y.identity == 'c':
					break
			else:
				continue
			break

if __name__ == '__main__':
	main()
