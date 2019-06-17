"""
# Most of the tests here are sanity tests primarily checking to make sure exceptions aren't
# raised from good parameters.
"""
from .. import core
from .. import matrix as module

def test_Type(test):
	"""
	# - &module.Type
	"""
	dt = module.Type('utf-8')
	test/dt.encoding == 'utf-8'
	test/dt.csi(b'm', b'0') == b"\x1b[0m"
	test/LookupError ^ (lambda: module.Type("no-such-encoding"))

def test_Type_transition(test):
	"""
	# - &module.Type.transition_render_parameters
	"""
	t = module.Type('utf-8')
	transition = t.transition_render_parameters
	notraits = core.NoTraits

	leading = (0, 0, notraits)
	following = (1, 0, notraits)
	test/(transition(leading, following)) == b'\x1b[38;2;0;0;1m'

	# No transition.
	leading = (1, 0, notraits)
	following = (1, 0, notraits)
	test/(transition(leading, following)) == b''

	# elimation (underline)
	leading = (1, 0, core.Traits.construct('underline'))
	following = (1, 0, notraits)
	test/(transition(leading, following)) == b'\x1b[24m'

	# transition in (underline)
	leading = (1, 0, notraits)
	following = (1, 0, core.Traits.construct('underline'))
	test/(transition(leading, following)) == b'\x1b[4m'

	# transition in underline from double
	leading = (1, 0, core.Traits.construct('double-underline'))
	following = (1, 0, core.Traits.construct('underline'))
	test/(transition(leading, following)) == b'\x1b[24;4m'

def test_Context_render_transitions(test):
	"""
	# - &module.Context.render

	# Validates that &module.Context.transition is properly applied.
	"""
	s = module.Screen()

	# Underline to bold.
	ph = core.Phrase.construct([
		("Simple", -1024, -1024, s.Traits.construct('underline')),
		(" ", -1024, -1024, s.Traits.construct('bold')),
		("phrase.", -1024, -1024, s.Traits.construct('bold')),
	])
	rph = list(s.render(ph))
	test/rph == [b'\x1b[4m', b'Simple', b'\x1b[24;1m', b' ', b'', b'phrase.']

	# Underline to far bold.
	ph = core.Phrase.construct([
		("Simple", -1024, -1024, s.Traits.construct('underline')),
		(" ", -1024, -1024, s.Traits.construct('underline')),
		("phrase.", -1024, -1024, s.Traits.construct('bold')),
	])
	rph = list(s.render(ph))
	test/rph == [b'\x1b[4m', b'Simple', b'', b' ', b'\x1b[24;1m', b'phrase.']

	# New text.
	ph = core.Phrase.construct([
		("Simple", -1024, -1024, s.Traits.construct('underline')),
		(" ", -1024, -1024, s.Traits.none()),
		("phrase.", -1024, -1024, s.Traits.construct('bold')),
	])
	rph = list(s.render(ph))
	test/rph == [b'\x1b[4m', b'Simple', b'\x1b[24m', b' ', b'\x1b[1m', b'phrase.']

def test_Context_stored_colors(test):
	"""
	# - &module.Context.context_set_text_color
	# - &module.Context.context_set_cell_color
	# - &module.Context.set_text_color
	# - &module.Context.set_cell_color
	# - &module.Context.reset_colors
	# - &module.Context.render
	"""
	s = module.Screen()
	test/s.reset_colors() == b'\x1b[39;49m'

	test/s.context_set_cell_color(-513)
	test/s.context_set_text_color(-513)
	test/s.reset_colors() == b'\x1b[31;41m'

	# Check that render considers the default; transition filters.
	ph = s.Phrase.construct([
		("Simple", -513, -513, core.Traits(0)),
		(" ", -513, -513, core.Traits(0)),
		("phrase.", -513, -513, core.Traits(0)),
	])
	rph = list(s.render(ph))
	test/rph == [b'', b'Simple', b'', b' ', b'', b'phrase.']

def test_Screen_methods(test):
	"""
	# - &module.Screen

	# Check sanity of the additional screen methods.
	"""
	S = module.Screen() # Explicitly utf-8.

	b"-test-title" in test/S.set_window_title_text("-test-title")
	b'!p' in test/S.reset()
	b'2J' in test/S.clear()

	sr = S.set_scrolling_region(0,1)
	b'1' in test/sr
	b'2' in test/sr

	b'7' in test/S.store_cursor_location()
	b'8' in test/S.restore_cursor_location()
	b'8' in test/S.scroll_up(8)
	b'8' in test/S.scroll_down(8)

def test_Context_seek(test):
	"""
	# - &module.Context.seek
	# - &module.Context.tell
	# - &module.Context.seek_last
	"""
	tctx = module.Context()
	tctx.context_set_position((32,32))
	tctx.context_set_dimensions((16, 16))

	b'33' in test/tctx.seek((0,0))
	test/tctx.tell() == (0,0)
	b'48' in test/tctx.seek_last()
	test/tctx.tell() == (15, 15)

def test_Context_properties(test):
	"""
	# - &module.Context
	"""
	ctx = module.Context()

	test.isinstance(ctx.terminal_type, module.Type)
	test/ctx.width == None
	test/ctx.height == None
	test/ctx.point == (None, None)

def test_Context_draw_words(test):
	"""
	# - &module.Context.draw_words
	"""
	ctx = module.Context()
	b'test' in test/ctx.draw_words("test")

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules[__name__])
