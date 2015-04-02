escape_sequence = b'\x1b['
escape = escape_sequence.__add__

# Part of the initial escape.
separator = b';'
terminator = b'm'

normal = b'0'
select_foreground = b'38;5;'
select_background = b'48;5;'

# Pairs are of the form: (Initiate, Terminate)
styles = {
	'bold': (b'1', b'22'),
	'dim': (b'2', b'22'),
	'reverse': (b'7', b'0'),
	'italic': (b'3', b'23'),
	'underline': (b'4', b'24'),
	'blink': (b'5', b'25'),
	'rapid': (b'6', b'25'),
	'conceal': (b'8', b'28'),
	'cross': (b'9', b'29'),
}

def foreground(color):
	return (
		str(color_code(color)).encode('ascii').join((_fg, b'm')), 
	)

def background(color):
	return (
		str(color_code(color)).encode('ascii').join((_bg, b'm')), 
	)
