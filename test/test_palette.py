"""
# - &.palette
"""
from .. import palette as module

def test_colors(test):
	"""
	# - &module.colors

	# Sanity.
	# Check that colors exist and have at least terminal-default and application-border.
	"""
	test/module.colors['terminal-default'] == -1024
	test/module.colors['application-border'] != -1024

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules[__name__])
