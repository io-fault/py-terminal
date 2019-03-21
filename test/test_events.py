from .. import events

def test_ictlchr(test):
	"""
	# Check for basic consistency.
	"""
	# Special cases.
	test/events.ictlchr('?') == '\x7f'
	test/events.ictlchr(' ') == ' '

	# Normal range.
	test/events.ictlchr('[') == '\x1b'
	test/events.ictlchr('\\') == '\x1c'
	test/events.ictlchr(']') == '\x1d'
	test/events.ictlchr('^') == '\x1e'
	test/events.ictlchr('_') == '\x1f'
	test/events.ictlchr('@') == '\x00'

	test/events.ictlchr('a') == '\x01'
	test/events.ictlchr('z') == chr(1 + (ord('Z')-ord('A')))

	# Check invariant; ictlchr will .upper() the given string.
	test/events.ictlchr('A') == '\x01'
	test/events.ictlchr('Z') == chr(1 + (ord('Z')-ord('A')))

	# Out of range.
	test/ValueError ^ (lambda: events.ictlchr('%'))

	# Might be reasonable to explicitly raise this as a ValueError
	test/TypeError ^ (lambda: events.ictlchr('plural'))

def test_print(test):
	"""
	# - &events.print
	"""
	test/events.print('f') == events.Character(('literal', 'f', 'f', 0))
	test/events.print(' ') == events.Character(('control', ' ', ' ', 0))

def test_dispatch_sequence_common(test):
	"""
	# - &events.dispatch_sequence
	"""
	test/events.dispatch_sequence("[z") == ("", ("", (), "z"))
	test/events.dispatch_sequence("[<z") == ("", ("<", (), "z"))
	test/events.dispatch_sequence("[<?z") == ("", ("<?", (), "z"))
	test/events.dispatch_sequence("[<?123;321ztra;iling junk") == ("tra;iling junk", ("<?", (123, 321), "z"))
	test/events.dispatch_sequence("[<?123;2~") == ("", ("<?", (123, 2), "~"))
	test/events.dispatch_sequence("[123;2~") == ("", ("", (123, 2), "~"))
	test/events.dispatch_sequence("[O") == ("", ("", (), "O"))

	test/events.dispatch_sequence("[0;1;49m") == ("", ("", (0,1,49), "m"))

def test_dispatch_sequence_empty_parameters(test):
	"""
	# - &events.dispatch_sequence
	"""
	test/events.dispatch_sequence("[;X") == ("", ("", (None, None), "X"))
	test/events.dispatch_sequence("[0;X") == ("", ("", (0, None), "X"))
	test/events.dispatch_sequence("[;0X") == ("", ("", (None, 0), "X"))
	test/events.dispatch_sequence("[;;0X") == ("", ("", (None, None, 0), "X"))

def test_dispatch_sequence_no_terminator(test):
	"""
	# - &events.dispatch_sequence

	# &None is used to signal that no final character was present.
	"""
	test/events.dispatch_sequence("[1;2") == ("", ("", (1,2), None))
	test/events.dispatch_sequence("[1") == ("", ("", (1,), None))
	test/events.dispatch_sequence("[") == ("", ("", (), None))
	test/events.dispatch_sequence("[<") == ("", ("<", (), None))
	test/events.dispatch_sequence("[<##") == ("", ("<##", (), None))
	test/events.dispatch_sequence("[<##1") == ("", ("<##", (1,), None))
	test/events.dispatch_sequence("[<##2;1") == ("", ("<##", (2,1,), None))

def test_dispatch_sequence_no_negatives(test):
	"""
	# - &events.dispatch_sequence
	"""
	test/events.dispatch_sequence("[-0;X") == ("", ("-", (0, None), "X"))
	test/events.dispatch_sequence("[;-32X") == ("32X", ("", (None, None), "-"))

def test_Parser_literal(test):
	"""
	# - &events.Parser
	# - &events.parser
	"""
	C = events.Character
	shift = events.Modifiers.construct(shift=True)
	meta = events.Modifiers.construct(meta=True)
	control = events.Modifiers.construct(control=True)
	p = events.parser()

	test/p.send(("", True)) == []
	test/p.send(("t", True)) == [events.print("t")]
	test/p.send((" ", True)) == [events.print(" ")]
	test/p.send(("th", True)) == [events.print("t"), events.print("h")]
	test/p.send(("\x1b[17~", True)) == [C(('function', '\x1b[17~', 6, 0))]
	test/p.send(("\x1b[17;5~", True)) == [C(('function', '\x1b[17;5~', 6, control))]
	test/p.send(("\x1b[A", True)) == [C(('navigation', '\x1b[A', 'up', 0))]
	test/p.send(("\x1b[X", True)) == [C(('ignored-escape-sequence', '\x1b[X', None, 0))]

def test_Parser_u_control(test):
	"""
	# - &events.Parser
	# - &events.parser
	# - &events.sequence_map
	"""
	C = events.Character
	meta = events.Modifiers.construct(meta=True)
	control = events.Modifiers.construct(control=True)
	p = events.parser()

	test/p.send(("\x1b[9;1u", True)) == [C(('control', "\x1b[9;1u", "i", 0))]
	test/p.send(("\x1b[9;3u", True)) == [C(('control', "\x1b[9;3u", "i", meta))]
	test/p.send(("\x1b[9;5u", True)) == [C(('control', "\x1b[9;5u", "i", control))]

def test_Parser_compound_events(test):
	"""
	# - &events.Parser
	# - &events.parser
	"""
	C = events.Character
	shift = events.Modifiers.construct(shift=True)
	meta = events.Modifiers.construct(meta=True)
	control = events.Modifiers.construct(control=True)
	p = events.parser()

	test/p.send(("\x1b[48;1u", True)) == [C(('literal', '\x1b[48;1u', chr(48), 0))]

	test/p.send(("\x1b[48;1ux", True)) == [
		C(('literal', '\x1b[48;1u', chr(48), 0)),
		C(('literal', 'x', 'x', 0)),
	]

	test/p.send(("\x1b[48;1uabcd", True)) == [
		C(('literal', '\x1b[48;1u', chr(48), 0)),
		C(('literal', 'a', 'a', 0)),
		C(('literal', 'b', 'b', 0)),
		C(('literal', 'c', 'c', 0)),
		C(('literal', 'd', 'd', 0)),
	]

	test/p.send(("\x1b[48;1u\x1b[49;2ux", True)) == [
		C(('literal', '\x1b[48;1u', chr(48), 0)),
		C(('literal', '\x1b[49;2u', chr(49), shift)),
		C(('literal', 'x', 'x', 0)),
	]

def test_Parser_incompleted_sequence(test):
	"""
	# - &events.Parser
	# - &events.parser
	"""
	C = (lambda x,y,z,a: events.Character((x,y,z,a)))
	shift = events.Modifiers.construct(shift=True)
	meta = events.Modifiers.construct(meta=True)
	control = events.Modifiers.construct(control=True)
	p = events.parser()

	# Incompleted sequence.
	test/p.send(("\x1b[48;1", True)) == [C('ignored-escape-sequence', "\x1b[48;1", None, 0)]
	test/p.send(("\x1b[48;1", False)) == []
	test/p.send(("", True)) == [C('ignored-escape-sequence', "\x1b[48;1", None, 0)]
	# check ground state
	test/p.send(("X", True)) == [C('literal', "X", "X", 0)]

def test_Parser_completed_sequence(test):
	"""
	# - &events.Parser
	# - &events.parser
	"""
	C = (lambda x,y,z,a: events.Character((x,y,z,a)))
	shift = events.Modifiers.construct(shift=True)
	meta = events.Modifiers.construct(meta=True)
	control = events.Modifiers.construct(control=True)

	p = events.parser()

	# Run this multiple times to make sure the ground state is being properly maintained.
	csi_48 = "\x1b[48;1u"
	for x in range(3):
		for x in csi_48[:-1]: # stop short of completion
			test/p.send((x, False)) == []
		test/p.send((csi_48[-1], False)) == [C('literal', "\x1b[48;1u", chr(48), 0)]

def test_Parser_focus_events(test):
	"""
	# - &events.Parser
	# - &events.parser
	# - &events.sequence_map
	"""
	C = (lambda x,y,z,a: events.Character((x,y,z,a)))
	shift = events.Modifiers.construct(shift=True)
	meta = events.Modifiers.construct(meta=True)
	control = events.Modifiers.construct(control=True)

	p = events.parser()

	# Run this multiple times to make sure the ground state is being properly maintained.
	test/p.send(("\x1b[I", False)) == [C('focus', "\x1b[I", "in", 0)]
	test/p.send(("\x1b[O", False)) == [C('focus', "\x1b[O", "out", 0)]

def test_Parser_common_tabs(test):
	"""
	# - &events.Parser
	# - &events.parser
	# - &events.sequence_map
	"""
	C = (lambda x,y,z,a: events.Character((x,y,z,a)))
	Mods = events.Modifiers.construct
	shift = Mods(shift=True)
	shiftmeta = Mods(shift=True, meta=True)

	p = events.parser()

	# Run this multiple times to make sure the ground state is being properly maintained.
	test/p.send(("\x1b[Z", False)) == [C('control', "\x1b[Z", "i", 0)]
	test/p.send(("\x1b[1;2Z", False)) == [C('control', "\x1b[1;2Z", "i", shift)]
	test/p.send(("\x1b[1;4Z", False)) == [C('control', "\x1b[1;4Z", "i", shiftmeta)]

def test_Parser_paste(test):
	"""
	# - &events.Parser
	# - &events.parser
	# - &events.process_region_data
	"""
	C = (lambda x,y,z,a: events.Character((x,y,z,a)))
	N = events.Modifiers.construct()
	p = events.parser()

	# Run this multiple times to make sure the ground state is being properly maintained.
	test/p.send(("\x1b[200~", True))[0] == C('paste', "\x1b[200~", "start", N)
	for x in range(16):
		test/p.send(("test data", True)) == [C('data', "test data", "paste", N)]

	# Check escape handling in paste.
	expect = [
		C('data', "with", "paste", N),
		C('data', "\x1b", "paste", N),
		C('data', "[Zescape", "paste", N),
		C('data', "\x1b", "paste", N),
	]
	for x in range(16):
		test/p.send(("with\x1b[Zescape\x1b", True)) == expect

	# Transition back
	after = map(events.print, "after")
	p.send(("\x1b[201~after", True)) == [C('paste', "\x1b[201~", 'stop', N)] + list(after)

def test_Parser_paste_oneshot(test):
	"""
	# - &events.Parser
	# - &events.parser
	# - &events.process_region_data
	"""
	C = (lambda x,y,z,a: events.Character((x,y,z,a)))
	N = events.Modifiers.construct()
	p = events.parser()

	for partialread in (True, False):
		expect = [
			C('paste', '\x1b[200~', 'start', N),
			C('data', 'paste-content', 'paste', N),
			C('paste', '\x1b[201~', 'stop', N),
		]
		test/p.send(("\x1b[200~paste-content\x1b[201~", partialread)) == expect

		# check ground
		test/p.send(("ground", partialread)) == list(map(events.print, "ground"))

		expect.extend(map(events.print, "after"))
		test/p.send(("\x1b[200~paste-content\x1b[201~after", partialread)) == expect

		# check ground
		test/p.send(("ground", partialread)) == list(map(events.print, "ground"))

def test_Parser_paste_edge(test):
	"""
	# - &events.Parser
	# - &events.parser
	# - &events.process_region_data
	"""
	C = (lambda x,y,z,a: events.Character((x,y,z,a)))
	N = events.Modifiers.construct()
	p = events.parser()

	test/p.send(("\x1b[200~", True))[0] == C('paste', "\x1b[200~", "start", N)
	for x in range(16):
		test/p.send(("test data", True)) == [C('data', "test data", "paste", N)]

	# Transition back
	after = map(events.print, "after")
	for x in "\x1b[201":
		test/p.send((x, False)) == [C('data', "", "paste", N)]

	p.send(("~", False)) == [C('paste', "\x1b[201~", "stop", N)]

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules[__name__])
