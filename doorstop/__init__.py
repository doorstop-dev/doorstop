"""
Package for doorstop.
"""

__project__ = 'Doorstop'
__version__ = '0.0.21'

CLI = 'doorstop'
GUI = 'doorstop-gui'
VERSION = __project__ + '-' + __version__

try:
    from doorstop.common import DoorstopError
    from doorstop.core import Item, Document, Tree, build, report
except ImportError:  # pragma: no cover, manual test
    pass
