from .. import core
from .. import matrix as library

def test_Context_transition(test):
	"""
	# - &library.Context.transition
	"""
	s = library.Screen()
	zero = core.Traits(0)

	leading = (0, 0, 0)
	following = (1, 0, zero)
	test/list(s.transition(leading, following)) == [b'38;2', b'0;0;1']

	# No transition.
	leading = (1, 0, 0)
	following = (1, 0, zero)
	test/list(s.transition(leading, following)) == []

	# elimation (underline)
	leading = (1, 0, core.Traits.construct('underline'))
	following = (1, 0, zero)
	test/list(s.transition(leading, following)) == [b'24']

	# transition in (underline)
	leading = (1, 0, zero)
	following = (1, 0, core.Traits.construct('underline'))
	test/list(s.transition(leading, following)) == [b'4']

	# transition in underline from double
	leading = (1, 0, core.Traits.construct('double-underline'))
	following = (1, 0, core.Traits.construct('underline'))
	test/list(s.transition(leading, following)) == [b'24', b'4']

def test_Context_render_transitions(test):
	"""
	# - &library.Context.render

	# Validates that &library.Context.transition is properly applied.
	"""
	s = library.Screen()

	# Underline to bold.
	ph = core.Phrase.construct([
		("Simple", -1024, -1024, core.Traits.construct('underline')),
		(" ", -1024, -1024, core.Traits.construct('bold')),
		("phrase.", -1024, -1024, library.Traits.construct('bold')),
	])
	rph = list(s.render(ph))
	test/rph == [b'\x1b[4m', b'Simple', b'\x1b[24;1m', b' ', b'', b'phrase.']

	# Underline to far bold.
	ph = core.Phrase.construct([
		("Simple", -1024, -1024, core.Traits.construct('underline')),
		(" ", -1024, -1024, core.Traits.construct('underline')),
		("phrase.", -1024, -1024, core.Traits.construct('bold')),
	])
	rph = list(s.render(ph))
	test/rph == [b'\x1b[4m', b'Simple', b'', b' ', b'\x1b[24;1m', b'phrase.']

	# New text.
	ph = core.Phrase.construct([
		("Simple", -1024, -1024, core.Traits.construct('underline')),
		(" ", -1024, -1024, core.Traits(0)),
		("phrase.", -1024, -1024, core.Traits.construct('bold')),
	])
	rph = list(s.render(ph))
	test/rph == [b'\x1b[4m', b'Simple', b'\x1b[24m', b' ', b'\x1b[1m', b'phrase.']

def test_Context_stored_colors(test):
	"""
	# - &library.Context.context_set_text_color
	# - &library.Context.context_set_cell_color
	# - &library.Context.set_text_color
	# - &library.Context.set_cell_color
	# - &library.Context.reset_colors
	# - &library.Context.render
	"""
	s = library.Screen()
	test/s.reset_colors() == b'\x1b[39;49m'

	test/s.context_set_cell_color(-513)
	test/s.context_set_text_color(-513)
	test/s.reset_colors() == b'\x1b[31;41m'

	# Check that render considers the default; transition filters.
	ph = core.Phrase.construct([
		("Simple", -513, -513, core.Traits(0)),
		(" ", -513, -513, core.Traits(0)),
		("phrase.", -513, -513, core.Traits(0)),
	])
	rph = list(s.render(ph))
	test/rph == [b'', b'Simple', b'', b' ', b'', b'phrase.']

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules[__name__])
