"""Package for doorstop."""

__project__ = 'Doorstop'
__version__ = '0.2-rc.1'

CLI = 'doorstop'
GUI = 'doorstop-gui'
VERSION = __project__ + '-' + __version__

try:
    from doorstop.common import DoorstopError, DoorstopWarning, DoorstopInfo
    from doorstop.core import Item, Document, Tree, build, report
except ImportError:  # pragma: no cover, manual test
    pass
