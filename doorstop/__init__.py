"""Package for doorstop."""

__project__ = 'Doorstop'
__version__ = '0.5-rc.2'

CLI = 'doorstop'
GUI = 'doorstop-gui'
VERSION = __project__ + '-' + __version__

try:
    from doorstop.common import DoorstopError, DoorstopWarning, DoorstopInfo
    from doorstop.core import Item, Document, Tree
    from doorstop.core import importer, build, report, find_document, find_item
except ImportError:  # pragma: no cover, manual test
    pass
