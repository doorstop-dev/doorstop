"""Package for doorstop."""

__project__ = 'Doorstop'
__version__ = '0.7.1'

CLI = 'doorstop'
GUI = 'doorstop-gui'
VERSION = __project__ + '-' + __version__
DESCRIPTION = "Text-based requirements management using version control."

MIN_PYTHON_VERSION = 3, 3

import sys
if not sys.version_info >= MIN_PYTHON_VERSION:  # pragma: no cover (manual test)
    exit("Python {}.{}+ is required.".format(*MIN_PYTHON_VERSION))

try:
    from doorstop.common import DoorstopError, DoorstopWarning, DoorstopInfo
    from doorstop.core import Item, Document, Tree
    from doorstop.core import build, find_document, find_item
    from doorstop.core import importer, exporter, builder, editor, publisher
except ImportError:  # pragma: no cover (manual test)
    pass
