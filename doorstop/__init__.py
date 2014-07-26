"""Package for doorstop."""

__project__ = 'Doorstop'
__version__ = '0.8-dev'

CLI = 'doorstop'
GUI = 'doorstop-gui'
VERSION = __project__ + '-' + __version__
DESCRIPTION = "Requirements management using version control."

MIN_PYTHON_VERSION = 3, 3

import sys
if not sys.version_info >= MIN_PYTHON_VERSION:  # pragma: no cover (manual test)
    exit("Python {}.{}+ is required.".format(*MIN_PYTHON_VERSION))


def _trace(self, message, *args, **kws):  # pragma: no cover (manual test)
    """New logging level, TRACE."""
    if self.isEnabledFor(logging.DEBUG - 1):
        self._log(logging.DEBUG - 1, message, args, **kws)  # pylint: disable=W0212

import logging
logging.addLevelName(logging.DEBUG - 1, "TRACE")
logging.Logger.trace = _trace

log = logging.getLogger(__name__)  # pylint: disable=C0103

try:
    from doorstop.common import DoorstopError, DoorstopWarning, DoorstopInfo
    from doorstop.core import Item, Document, Tree
    from doorstop.core import build, find_document, find_item
    from doorstop.core import importer, exporter, builder, editor, publisher
except ImportError:  # pragma: no cover (manual test)
    pass
