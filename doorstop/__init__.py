"""Package for doorstop."""

import sys

__project__ = 'Doorstop'
__version__ = '1.2'

CLI = 'doorstop'
GUI = 'doorstop-gui'
SERVER = 'doorstop-server'
VERSION = "{0} v{1}".format(__project__, __version__)
DESCRIPTION = "Requirements management using version control."

MIN_PYTHON_VERSION = 3, 3

if not sys.version_info >= MIN_PYTHON_VERSION:  # pragma: no cover (manual test)
    exit("Python {}.{}+ is required.".format(*MIN_PYTHON_VERSION))

try:
    from doorstop.common import DoorstopError, DoorstopWarning, DoorstopInfo
    from doorstop.core import Item, Document, Tree
    from doorstop.core import build, find_document, find_item
    from doorstop.core import importer, exporter, builder, editor, publisher
except ImportError:  # pragma: no cover (manual test)
    pass
