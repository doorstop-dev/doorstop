"""Package for doorstop."""

from doorstop.common import DoorstopError, DoorstopWarning, DoorstopInfo
from doorstop.core import Item, Document, Tree
from doorstop.core import build, find_document, find_item
from doorstop.core import importer, exporter, builder, editor, publisher

__project__ = 'Doorstop'
__version__ = '1.5b3'

CLI = 'doorstop'
GUI = 'doorstop-gui'
SERVER = 'doorstop-server'
VERSION = "{0} v{1}".format(__project__, __version__)
DESCRIPTION = "Requirements management using version control."
