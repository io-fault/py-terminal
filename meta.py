"""
# Meta character mappings for accessing greek characters and mathematic symbols.

# Exports the function &select which maps the latin character to a greek character
# or mathematic symbol according to the &mapping table.

# The &mapping table provides the mapping to a term that is then resolved in either
# &characters or &capitals.
"""

characters = {
	'alpha': 'α',
	'beta': 'β',
	'gamma': 'γ',
	'delta': 'δ',
	'epsilon': 'ε',
	'zeta': 'ζ',
	'eta': 'η',
	'theta': 'θ',
	'iota': 'ι',
	'kappa': 'κ',
	'lambda': 'λ',
	'mu': 'μ',
	'nu': 'ν',
	'xi': 'ξ',
	'omicron': 'ο',
	'pi': 'π',
	'rho': 'ρ',
	'sigma': 'σ',
	'tau': 'τ',
	'upsilon': 'υ',
	'phi': 'φ',
	'chi': 'χ',
	'psi': 'ψ',
	'omega': 'ω',

	'function': '𝑓',
	'sine': '∿',
	'infinity': '∞',

	'less': '≤',
	'greater': '≥',
	'identical': '≡',
	'division': '÷',
	'multiplication': '×',
	'root': '√',

	'not': '¬',
	'n-ary-product': '∏',
	'n-ary-summation': '∑',

	'subset-of': '⊂',
	'superset-of': '⊃',
	'intersection': '∩',
	'union': '∪',
	'element-of': '∈',
	'contains-as': '∋',

	'universal-quantifier': '∀',
	'there-exists': '∃',
}

capitals = {
	'alpha': 'Α',
	'beta': 'Β',
	'gamma': 'Γ',
	'delta': 'Δ',
	'epsilon': 'Ε',
	'zeta': 'Ζ',
	'eta': 'Η',
	'theta': 'Θ',
	'iota': 'Ι',
	'kappa': 'Κ',
	'lambda': 'Λ',
	'mu': 'Μ',
	'nu': 'Ν',
	'xi': 'Ξ',
	'omicron': 'Ο',
	'pi': 'Π',
	'rho': 'Ρ',
	'sigma': 'Σ',
	'tau': 'Τ',
	'upsilon': 'Υ',
	'phi': 'Φ',
	'chi': 'Χ',
	'psi': 'Ψ',
	'omega': 'Ω',

	'function': '∫',
}

mapping = {
	'a': 'alpha',
	'b': 'beta',
	'd': 'delta',
	'e': 'epsilon',
	'g': 'gamma',
	'h': 'eta',
	'i': 'iota',

	'k': 'kappa',
	'l': 'lambda',
	'm': 'mu',
	'n': 'nu',
	'o': 'omicron',
	'p': 'pi',

	'r': 'rho',
	's': 'sigma',
	't': 'tau',
	'u': 'upsilon',

	'x': 'chi',
	'y': 'psi',
	'z': 'zeta',

	# mnemonic exceptions
	'w': 'omega',
	'j': 'theta',
	'v': 'phi',
	'c': 'xi',

	'q': '',
	'f': 'function', # integral capital

	'<': 'less',
	'>': 'greater',
	'=': 'identical',

	'/': 'division',
	'*': 'multiplication',
	'?': 'root',
	'!': 'not',
	'^': 'n-ary-product',

	'[': 'subset-of',
	']': 'superset-of',
	'(': 'intersection',
	')': 'union',
	'{': 'element-of',
	'}': 'contains-as',

	';': 'infinity',
	':': 'sine',
}

def select(char, tables={False:capitals, True:characters}):
	"""
	# Select the greek character or math symbol associated with
	# the latin character.
	"""

	index = char.lower()
	lower = (index == char)
	name = mapping[index]
	sc = tables[lower][name]

	return sc
