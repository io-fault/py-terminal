"""
# Dictionaries containing various unicode symbols for display purposes.
"""

horizontal_progress = ' ▏▎▎▍▌▋▊▉█'
vertical_progress = ' ▁▂▃▄▅▆▇█'
quadrants = '▖▘▝▗'
wands = "/-\\|"

suits = {
	'spades': '♠',
	'hearts': '♥',
	'diamonds': '♦',
	'clubs': '♣',
}

math = {
	'divison': '÷',
	'multiplication': '×',
	'addition': '+',
	'subtraction': '−',
	'addition-and-subtraction': '±',
	'angle': '∠',
	'radical': '√',
	'function': '𝑓',
	'integral': '∫',
	'coproduct': '∐',
	'product': '∏',
	'summation': '∑',
	'infinity': '∞',
	'differential': '𝜕',
}

development = {
	'branch': '\uE0A0', # 
	'line-number': '\uE0A1', # 
	'locked': '\uE0A2', # 

	'arrowhead-block-right': '\uE0B0', # 
	'arrowhead-block-left': '\uE0B2', # 

	'arrowhead-line-right': '\uE0B1', # 
	'arrowhead-line-left': '\uE0B3', # 
}

logic = {
	'identical': '≡',
	'not-identical': '≢',
	'equal': '=',
	'not-equal': '≠',
	'greater-than': '>',
	'less-than': '<',
	'equal-greater-than': '≥',
	'equal-less-than': '≤',
}

arrows = {
	'left': '←',
	'right': '→',
	'up': '↑',
	'down': '↓',
}

wedges = {
	'up': '∧',
	'down': '∨',
	'left': '<',
	'right': '>',
}

marks = {
	'x': '✗',
	'check': '✓',
	'bullet': '•',
	'triangle': '‣',
	'checkbox': '❏',
}

editing = {
	'scissors': '✂',
	'pencil': '✎',
	'envelope': '✉',
}

modifiers = {
	'capslock': '\u21EA', # ⇪
	'numlock': '\u21ED', # ⇭
	'shift': '\u21E7', # ⇧
	'control': '\u2303', # ⌃
	'option': '\u2325', # ⌥
	'apple': '\uF8FF', # 
	'command': '\u2318', # ⌘
}

control = {
	'eject': '\u23CF', # ⏏
	'power': '\u233D', # ⌽
}

whitespace = {
	'tab': '\u21E5', # ⇥
	'space': '\u2423', # ␣
	'return': '\u23CE', # ⏎
	'enter': '\u2324', # ⌤
}

manipulations = {
	'backspace': '\u232B', # ⌫
	'delete': '\u2326', # ⌦
	'clear': '\u2327', # ⌧
}

navigation = {
	'escape': '\u238B', # ⎋
	'home': '\u21F1', # ⇱
	'end': '\u21F2', # ⇲
	'page-up': '\u21DE', # ⇞
	'page-down': '\u21DF', # ⇟
}

# borders middle of cell
corners = {
	'bottom-left': '└',
	'bottom-right': '┘',
	'top-left': '┌',
	'top-right': '┐',
}

rounds = {
	'bottom-left': '╰',
	'bottom-right': '╯',
	'top-left': '╭',
	'top-right': '╮',
}

double = {
	'bottom-left': '╚',
	'bottom-right': '╝',
	'top-left': '╔',
	'top-right': '╗',
	'vertical': '║',
	'horizontal': '═',
}

intersections = {
	'top': '┬',
	'bottom': '┴',
	'full': '┼',
	'left': '├',
	'right': '┤',
}

lines = {
	'horizontal': '─',
	'vertical': '│',
	'diagonal-right': '╱',
	'diagonal-left': '╲',
	'diagonal-cross': '╳',
}

dotted = {
	'horizontal': '┄',
	'vertical': '┆',
}

# used for interactive annotations
combining = {
	'high': {
		'horizontal-line': '\u0305',

		'rotate-arrow-left': '\u20D4',
		'rotate-arrow-right': '\u20D5',

		'corner-right': '\u031A',

		'asterisk': '\u20F0',
		'zigzag': '\u035B',
		'x': '\u033D',
		'squiggly': '\u1DD3',
		'congruent': '\u034C',
		'vertical-tilde': '\u033E',

		'horizontal-bridge-down': '\u0346',
		'horizontal-bridge-up': '\u0346',

		'wedge-left': '\u0356',
		'wedge-right': '\u0350',
		'circumflex': '\u0302', 'caron': '\u030C', # similar symbols
	},

	'low': {
		'horizontal-line': '\u035F',

		'intersection-left': '\u0318',
		'intersection-right': '\u0319',
		'intersection-up': '\u031D',
		'intersection-down': '\u031E',
		'intersection-full': '\u031F',

		'up-arrow': '\u034E',
		'left-arrow': '\u20EE',
		'right-arrow': '\u20EF',

		'horizontal-double-arrow': '\u034D',

		'asterisk': '\u0359',
		'zigzag': '\u1DCF',
		'equality': '\u0347',
		'tilde': '\u0347',
		'x': '\u0353',
		'squiggly': '\u032B',
		'box': '\u033B',
		'addition': '\u031F',

		'horizontal-bridge-down': '\u032A',
		'horizontal-bridge-up': '\u033A',

		'wedge-left': '\u0354',
		'wedge-right': '\u0355',

		'dotted-line': '\u20E8',
	},

	# combining characters that look like alphabet symbols.
	'alphabet': {
		'a': '\u0363',
		'e': '\u0364',
		'i': '\u0365',
		'o': '\u0365',
		'u': '\u0366',
		'c': '\u0367',
		'd': '\u0368',
		'h': '\u0369',
		'm': '\u036A',
		'r': '\u036B',
		't': '\u036C',
		'v': '\u036D',
		'x': '\u036E',
		'g': '\u1DDB',
		'k': '\u1DDC',
		'l': '\u1DDD',
		'L': '\u1DDE',
		'm': '\u1DDF',
		'n': '\u1DE0',
		'N': '\u1DE1',
		'R': '\u1DE2',
		'r': '\u1DE3',
		's': '\u1DE4',
		'z': '\u1DE6',
	},

	'center': {
		'left-arrow': '\u20EA',
		'right-arrow': '\u0362',
	},

	'right': {
		'vertical-line': '\u20D2'
	},

	# overlays on the entire cell
	'full': {
		'circle': '\u20DD',
		'circle-slash': '\u20E0',
		'square': '\u20DE',
		'diamond': '\u20DF',
		'forward-slash': '\u0338',
	},
}

greek = dict(
	lower = {
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
	},

	upper = {
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
	}
)

import itertools
keyboard = dict(itertools.chain(
	modifiers.items(),
	control.items(),
	whitespace.items(),
	manipulations.items(),
	navigation.items(),
))
del itertools
