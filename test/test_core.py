"""
# Tests for &.core.
"""
from .. import core as library
notraits = library.NoTraits

def test_Modifiers(test):
	M = library.Modifiers

	m = M(0)
	test/m.control == False
	test/m.shift == False
	test/m.meta == False

	m = M.construct(control=True, meta=True, shift=True)
	test/m.control == True
	test/m.shift == True
	test/m.meta == True

	m = M.construct(control=False, meta=True, shift=False)
	test/m.meta == True
	test/m.control == False
	test/m.shift == False

def test_Traits(test):
	"""
	# - &library.Traits
	"""

	Traits = library.Traits
	test/Traits.construct('underline').test('underline') == True
	test/Traits.construct('underline').test('double-underline') == False
	test/Traits.none() == library.NoTraits

def test_Traits_unique(test):
	"""
	# - &library.Traits
	"""

	# Given aliases, this will need to change.
	s = set(map(library.Traits.construct, library.Traits.fields))
	test/len(s) == len(library.Traits.fields)

def test_Traits_expected(test):
	"""
	# - &library.Traits
	"""
	seq = [
		'underline',
		'double-underline',
		'cross',
		'italic',
		'bold',
		'feint',

		'invisible',
		'inverse',

		'rapid',
		'blink',

		'overline',
		'encircle',
		'frame',
	]

	# Sanity.
	t = library.Traits.construct(*seq)
	seq.sort()
	out = list(t)
	out.sort()
	test/out == seq

def test_RenderParameters(test):
	"""
	# - &library.RenderParameters
	"""

	rp = library.RenderParameters.from_colors(0, 0)
	test/rp.textcolor == 0
	test/rp.cellcolor == 0
	test/rp.traits == 0

	test/rp.update(cellcolor=1) == (0, 1, 0)
	test/rp.update(textcolor=1) == (1, 0, 0)

def test_RenderParameters_apply(test):
	"""
	# - &library.RenderParamters.apply
	"""
	t = library.NoTraits
	r = library.RenderParameters((None, None, t))
	test/r.apply('underline').traits.test('underline') == True
	test/r.apply('underline', 'bold').traits.test('underline') == True
	test/r.apply('underline', 'bold').traits.test('bold') == True

	test/r.apply('bold').textcolor == None
	test/r.apply('bold', textcolor=1).textcolor == 1

def test_RenderParameters_traits(test):
	"""
	# - &library.RenderParameters.clear
	# - &library.RenderParameters.set
	"""

	# Sanity
	rp = library.RenderParameters((0, 0, library.Traits(0)))
	ul = library.Traits.construct('underline')
	dul = library.Traits.construct('double-underline')

	rp = rp.set(ul)
	test/list(rp.traits) == ['underline']
	test/list(rp.clear(ul).traits) == []

	rp = rp.set(dul)
	test/list(rp.clear(ul).traits) == ['double-underline']

def test_RenderParameters_equality(test):
	"""
	# - &library.RenderParameters
	"""
	rp = library.RenderParameters((0, 0, library.Traits(0)))
	rp1 = library.RenderParameters((0, 0, library.Traits(1)))
	rp2 = library.RenderParameters((0, 1, library.Traits(0)))

	test/rp == rp
	test/rp != rp1
	test/rp != rp2

def test_Units(test):
	"""
	# - &library.Units
	"""

	# Validate rather features.
	# They are important, however, for the use case
	# of consolidating cells.

	u = library.Units(("->",))
	test/str(u) == "->"
	test/len(u) == 1
	test/u.encode('utf-8') == b"->"

	u = library.Units(("->", "::"))
	test/str(u) == "->::"
	test/len(u) == 2
	test/u.encode('utf-8') == b"->::"

	# Check iter() and __add__
	test.isinstance(u + ("rhs",), library.Units)
	test/''.join(list(u)) == str(u)

def test_Units_slice(test):
	"""
	# - &library.Units.__getitem__
	"""

	u = library.Units(("->", "::"))
	test/str(u) == "->::"
	test/len(u) == 2
	test/u.encode('utf-8') == b"->::"

	test/u[0] == "->"
	test/u[1] == "::"
	test.isinstance(u[:1], library.Units)
	u += ("rhs",)
	test.isinstance(u, library.Units)
	test/u[:] == u

def test_grapheme(test):
	"""
	# - &library.Phrase.grapheme
	"""
	getg = library.grapheme
	t = "謝了春\u0353."

	test/t[getg(t, 0)] == t[0]
	test/t[getg(t, 1)] == t[1]
	test/t[getg(t, 4)] == t[-1]

	# Primary checks.
	test/t[getg(t, 2)] == t[2:-1]
	test/t[getg(t, 3)] == t[2:-1]

def test_itergraphemes(test):
	t = "f\u0356ield\u035B"
	l=list(t[i] for i in library.itergraphemes(t))

def test_Phrase_properties(test):
	"""
	# - &library.Phrase.cellcount
	# - &library.Phrase.stringlength
	"""

	ph = library.Phrase.construct([
		("field", None, None, 0)
	])
	test/ph == ((5, "field", (None, None, 0)),)
	test/len(ph) == 1
	test/ph.cellcount() == 5
	test/ph.unitcount() == 5

def test_Phrase_rstripcells_singular(test):
	"""
	# - &library.Phrase.rstripcells
	# - &library.Phrase.rfindcell
	"""
	ph = library.Phrase.construct([
		("field", None, None, 0)
	])

	result = ph.rstripcells(5)
	test/result == ((0, "", (None, None, 0)),)

	result = ph.rstripcells(4)
	test/result == ((1, "f", (None, None, 0)),)

	result = ph.rstripcells(3)
	test/result == ((2, "fi", (None, None, 0)),)

	result = ph.rstripcells(2)
	test/result == ((3, "fie", (None, None, 0)),)

	result = ph.rstripcells(1)
	test/result == ((4, "fiel", (None, None, 0)),)

	# Validate empty remainder.
	pair = library.Phrase.construct([
		("first", None, None, 0),
		("second", None, None, 0),
	])

	result = pair.rstripcells(6)
	test/result == ((5, "first", (None, None, 0)),)

findcell_phrase_1 = library.Phrase.construct([
	("field", None, None, notraits),
	(" ", None, None, notraits),
	("sequence", None, None, notraits),
	(",", None, None, notraits),
	(" ", None, None, notraits),
	("terminal", None, None, notraits),
])

# Combining Characters; limited to testing on the edges of words to avoid displacing indexes.
findcell_phrase_1_cc = library.Phrase.construct([
	("field\u0356\u035B", None, None, notraits),
	(" ", None, None, notraits),
	("sequence\u035B", None, None, notraits),
	(",", None, None, notraits),
	(" \u035B", None, None, notraits),
	("terminal", None, None, notraits),
])

# Only with respect to single unit words.
findcell_phrase_1_units = library.Phrase.construct([
	("field", None, None, notraits),
	(library.Units((" ",)), None, None, notraits),
	("sequence", None, None, notraits),
	(library.Units((",",)), None, None, notraits),
	(library.Units((" ",)), None, None, notraits),
	("terminal", None, None, notraits),
])

def t_lfindcell_1(test, phrase):
	findmethod = phrase.lfindcell
	cells = phrase.cellcount()

	test/findmethod(0) == (0, 0, 0)
	test/findmethod(1) == (0, 1, 1)
	test/findmethod(0, start=(0,1,1)) == (0, 1, 1)
	test/findmethod(1, start=(0,1,1)) == (0, 2, 2)
	test/findmethod(2, start=(0,2,2)) == (0, 4, 4)

	# Select next word.
	test/findmethod(2, start=(0,3,3)) == (1, 0, 5)
	test/findmethod(3, start=(0,2,2)) == (1, 0, 5)
	test/findmethod(0, start=(0,5,5)) == (1, 0, 5)
	#test/findmethod(0, start=(0,6,6)) == (1, 1, 6) carry on invalid addresses?

	test/findmethod(0, start=(1,0,5)) == (1, 0, 5)
	test/findmethod(1, start=(1,0,5)) == (2, 0, 6)
	test/findmethod(2, start=(1,0,5)) == (2, 1, 7)

	edge = findmethod(cells)
	test/edge == (len(phrase)-1, len(phrase[-1][1]), phrase.cellcount())
	test/findmethod(0, start=edge) == edge
	test/findmethod(1, start=(edge[0], edge[1]-1, edge[2]-1)) == edge

	test/findmethod(1, start=edge) == None # Beyond edge.

def test_Phrase_lfindcell(test):
	"""
	# - &library.Phrase.lfindcell
	"""
	library.text.setlocale()
	t_lfindcell_1(test, findcell_phrase_1)
	t_lfindcell_1(test, findcell_phrase_1_cc)
	t_lfindcell_1(test, findcell_phrase_1_units)

def t_rfindcell_1(test, phrase):
	# r/lfindcell cannot be symmetric wrt the current zero width character handling.
	# (expectation of the naive grapheme breaker is that combining characters follow base)

	findmethod = phrase.rfindcell
	cells = phrase.cellcount()
	wordcount = len(phrase)

	test/findmethod(0) == (-1, 0, 0)
	test/findmethod(1) == (-1, 1, 1)
	test/findmethod(0, start=(-1,1,1)) == (-1, 1, 1)
	test/findmethod(1, start=(-1,1,1)) == (-1, 2, 2)
	test/findmethod(2, start=(-1,2,2)) == (-1, 4, 4)

	# Next words.
	test/findmethod(0, start=(-1,8,8)) == (-2, 0, 8)
	test/findmethod(1, start=(-1,8,8)) == (-3, 0, 9)
	test/findmethod(2, start=(-1,8,8)) == (-4, 0, 10)
	test/findmethod(1, start=(-3,0,9)) == (-4, 0, 10)

	edge = findmethod(cells)
	test/edge == (-len(phrase), len(phrase[0][1]), cells)
	test/findmethod(0, start=edge) == edge
	test/findmethod(1, start=(edge[0], edge[1]-1, edge[2]-1)) == edge

	test/findmethod(1, start=edge) == None # Beyond edge.

def test_Phrase_rfindcell(test):
	"""
	# - &library.Phrase.rfindcell
	"""
	library.text.setlocale()
	t_rfindcell_1(test, findcell_phrase_1)
	t_rfindcell_1(test, findcell_phrase_1_cc)
	t_rfindcell_1(test, findcell_phrase_1_units)

def test_Phrase_lstripcells_singular(test):
	"""
	# - &library.Phrase.lstripcells
	# - &library.Phrase.lfindcell
	"""
	ph = library.Phrase.construct([
		("field", None, None, 0)
	])

	result = ph.lstripcells(1)
	test/result == ((4, "ield", (None, None, 0)),)

	result = ph.lstripcells(2)
	test/result == ((3, "eld", (None, None, 0)),)

	result = ph.lstripcells(3)
	test/result == ((2, "ld", (None, None, 0)),)

	result = ph.lstripcells(4)
	test/result == ((1, "d", (None, None, 0)),)

	result = ph.lstripcells(5)
	test/result == ((0, "", (None, None, 0)),)

	# Validate empty remainder.
	pair = library.Phrase.construct([
		("first", None, None, 0),
		("second", None, None, 0),
	])

	result = pair.lstripcells(5)
	test/result == ((6, "second", (None, None, 0)),)

def test_Phrase_lstripcells_wide(test):
	"""
	# - &library.Phrase.lstripcells
	# - &library.Phrase.lfindcell

	# Failure is likely due to a malfunctioning &wcswidth implementation.
	"""

	seq = [("謝了春",)]
	ph = library.Phrase.construct(seq)
	test/ph.lstripcells(1)[0][1] == "*了春"
	test/ph.lstripcells(2)[0][1] == "了春"
	test/ph.lstripcells(3)[0][1] == "*春"
	test/ph.lstripcells(4)[0][1] == "春"
	test/ph.lstripcells(5)[0][1] == "*"
	test/ph.lstripcells(6)[0][1] == ""

def test_Phrase_rstripcells_wide(test):
	"""
	# - &library.Phrase.rstripcells
	# - &library.Phrase.rfindcell

	# Failure is likely due to a malfunctioning &wcswidth implementation.
	"""

	seq = [("謝了春",)]
	ph = library.Phrase.construct(seq)
	test/ph.rstripcells(1)[0][1] == "謝了*"
	test/ph.rstripcells(2)[0][1] == "謝了"
	test/ph.rstripcells(3)[0][1] == "謝*"
	test/ph.rstripcells(4)[0][1] == "謝"
	test/ph.rstripcells(5)[0][1] == "*"
	test/ph.rstripcells(6)[0][1] == ""

def test_Phrase_lstripcells_boundary(test):
	"""
	# - &library.Phrase.lstripcells
	# - &library.Phrase.lfindcell
	"""

	seq = [("謝了春",), ("check",)]
	ph = library.Phrase.construct(seq)
	test/ph.lstripcells(6)[0][1] != "" # Should not include empty initial.
	test/ph.lstripcells(6)[0][1] == "check"
	test/ph.lstripcells(7)[0][1] == "heck"
	test/IndexError ^ (lambda: ph.lstripcells(7).__getitem__(1))

	seq = [("check",), ("謝了春",),]
	ph = library.Phrase.construct(seq)
	test/ph.lstripcells(5)[0][1] != "" # Should not include empty initial.
	test/ph.lstripcells(7)[0][1] == "了春"

def test_Phrase_rstripcells_boundary(test):
	"""
	# - &library.Phrase.rstripcells
	# - &library.Phrase.rfindcell
	"""

	seq = [("謝了春",), ("check",)]
	ph = library.Phrase.construct(seq)
	test/IndexError ^ (lambda: ph.rstripcells(5)[1][1] == "")
	test/ph.rstripcells(5)[0][1] == "謝了春"
	test/ph.rstripcells(6)[0][1] == "謝了*"
	test/ph.rstripcells(7)[0][1] == "謝了"
	test/IndexError ^ (lambda: ph.rstripcells(7).__getitem__(1))

	iseq = [("check",), ("謝了春",)]
	ph = library.Phrase.construct(iseq)
	test/IndexError ^ (lambda: ph.rstripcells(6)[1][1] == "")
	test/ph.rstripcells(4)[-1][1] == "謝"
	test/ph.rstripcells(5)[-1][1] == "*"

def test_Phrase_lstripcells_zerowidth(test):
	"""
	# - &library.Phrase.lstripcells
	# - &library.Phrase.lfindcell
	"""

	# Zero width space might be greater than zero cells.
	seq = [("Leading, C\u0353, Following",)]
	ph = library.Phrase.construct(seq)
	test/ph.lstripcells(len("Leading, "))[0][1] == "C\u0353, Following"

	# lfindcell needs to be greedy and consume any zero width characters.
	test/ph.lstripcells(len("Leading, X"))[0][1] == ", Following"

	# Two cells
	seq = [("謝了春\u0353, Following",)]
	ph = library.Phrase.construct(seq)
	test/ph.lstripcells(6)[0][1] == ", Following"

	noted = []
	def sub(x):
		noted.append(x)
		return '*'
	test/ph.lstripcells(5, substitute=sub)[0][1] == "*, Following"
	test/noted == ["春\u0353"]

def test_Phrase_rstripcells_zerowidth(test):
	"""
	# - &library.Phrase.rstripcells
	# - &library.Phrase.rfindcell

	# Failure is likely due to a malfunctioning &wcswidth implementation.
	"""

	seq = [("Leading, C\u0353, Following",)]
	ph = library.Phrase.construct(seq)
	test/ph.rstripcells(len("Following"))[0][1] == "Leading, C\u0353, "
	test/ph.rstripcells(len(", Following"))[0][1] == "Leading, C\u0353"

	# Unlike lfindcell, zero width is naturally consumed prior to hitting the final offset.
	test/ph.rstripcells(len("x, Following"))[0][1] == "Leading, "

	seq = [("謝了春\u0353, Following",)]
	ph = library.Phrase.construct(seq)
	n = len(", Following")
	test/ph.rstripcells(n)[0][1] == "謝了春\u0353"

	noted = []
	def sub(x):
		noted.append(x)
		return '*'
	test/ph.rstripcells(n+1, substitute=sub)[0][1] == "謝了*"
	test/noted == ["春\u0353"]

def test_Phrase_lstripcells_noop(test):
	ph = library.Phrase.construct([
		("Simple", None, None, notraits),
		(" ", None, None, notraits),
		("Phrase.", None, None, notraits),
	])
	test/ph.lstripcells(0) == ph
	test/ph.lstripcells(-1) == ph
	test/ph.lstripcells(-128) == ph

def test_Phrase_rstripcells_noop(test):
	ph = library.Phrase.construct([
		("Simple", None, None, notraits),
		(" ", None, None, notraits),
		("Phrase.", None, None, notraits),
	])
	test/ph.rstripcells(0) == ph
	test/ph.rstripcells(-1) == ph
	test/ph.rstripcells(-128) == ph

def test_Phrase_translate_ascii(test):
	"""
	# - &library.Phrase.translate
	"""

	# one-to-one mapping
	seq = [("first",), ("second",), (" and some more",)]
	ph = library.Phrase.construct(seq)

	for x in range(6):
		test/x == list(ph.translate(x))[0]

	test/list(ph.translate(*range(6))) == list(range(6))

def test_Phrase_translate_empty(test):
	"""
	# - &library.Phrase.translate
	"""

	# empty line
	seq = [("",)]
	ph = library.Phrase.construct(seq)
	xo, = ph.translate(0)
	test/xo == 0
	test/list(ph.translate(1)) == [None]

def test_Phrase_translate_wide(test):
	"""
	# - &library.Phrase.translate
	"""

	seq = [("謝了春謝了春",)]
	ph = library.Phrase.construct(seq)
	for x in range(6):
		xo, = ph.translate(x)
		test/xo == (x*2)

	seq = [("f謝o了春謝了春",)]
	ph = library.Phrase.construct(seq)

	xo, = ph.translate(2)
	test/xo == 3
	xo, = ph.translate(3)
	test/xo == 4
	xo, = ph.translate(4)
	test/xo == 6

def test_Phrase_combine(test):
	"""
	# - &library.Phrase.combine
	"""

	# Zero attributes.
	p = library.Phrase.construct([("prefix",), ("-",), ("suffix",)])
	c = library.Phrase.construct([("prefix-suffix",)])

	test/p.combine() == c

def test_Phrase_subphrase(test):
	"""
	# - &library.Phrase.subphrase
	"""
	seq = [
		("def", 0x0000FF, None, library.Traits(0)),
		(" ", None, None, None),
		("function", None, None, library.Traits(0)),
		("(arguments)", None, None, library.Traits(0)),
		("-> tuple:", None, None, library.Traits(0)),
	]
	ph = library.Phrase.construct(seq)

	# First edge
	test/list(ph.subphrase(*ph.findcells(0, 0))) == [(0, "", ph[0][2])]

	test/list(ph.subphrase(*ph.findcells(0, 3))) == [ph[0]]
	fun = (3, "fun", (None, None, 0))
	test/list(ph.subphrase(*ph.findcells(0, 7))) == [ph[0], ph[1], fun]

def test_Phrase_join(test):
	"""
	# - &library.Phrase.join
	"""
	normal = library.RenderParameters((0xFFFFFF, 0x000000, library.Traits(0)))
	tab = library.Phrase(normal.form("<TAB>"))

	# Three elements.
	r = tab.join([
		normal.form("first"),
		normal.form("middle"),
		normal.form("last"),
	])
	test/''.join([x[1] for x in r]) == "first<TAB>middle<TAB>last"
	test/r[0][2] == normal
	test/r[1] == tab[0]
	test/r[2][2] == normal
	test/r[3] == tab[0]
	test/r[4][2] == normal

	# Two elements.
	r = tab.join([
		normal.form("first"),
		normal.form("last"),
	])
	test/''.join([x[1] for x in r]) == "first<TAB>last"

	# Single element case.
	r = tab.join([
		normal.form("first"),
	])
	test/''.join([x[1] for x in r]) == "first"

	# Zero element case.
	r = tab.join([])
	test/''.join([x[1] for x in r]) == ""

def test_Constructors(test):
	"""
	# - &library.RenderParameters.form
	# - &library.Phrase.from_words
	"""
	rp1 = library.RenderParameters((0xFFFFFF, 0x000000, library.Traits(0)))
	rp2 = library.RenderParameters((-1024, 0x000000, library.Traits(0)))
	test/len(list(rp1.form("first", "second"))) == 2

	ph = library.Phrase.from_words(
		rp1.form("Former", " ", "sentence", ". "),
		rp2.form("Latter sentence", "."),
	)
	test/"".join([x[1] for x in ph]) == "Former sentence. Latter sentence."

	# Check units usage.
	ph = library.Phrase.from_words(
		rp1.form("Former", " ", "sentence", library.Units(("->",))),
		rp2.form("Latter sentence", library.Units((";",))),
	)
	test/"".join([str(x[1]) for x in ph]) == "Former sentence->Latter sentence;"

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules[__name__])
