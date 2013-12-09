"""
Package for doorstop.
"""

from pkg_resources import get_distribution, DistributionNotFound

__project__ = 'Doorstop'
__version__ = None  # required for initial installation

CLI = 'doorstop'
GUI = 'Doorstop'


try:
    __version__ = get_distribution(__project__).version  # pylint: disable=E1103
except DistributionNotFound:  # pragma: no cover, manual test
    VERSION = __project__ + '-' + '(local)'
else:
    VERSION = __project__ + '-' + __version__


try:
    from doorstop.core import Item, Document, Tree, build
except ImportError:
    pass
