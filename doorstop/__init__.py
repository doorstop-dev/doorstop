#!/usr/bin/env python

"""
Package for doorstop.
"""

from pkg_resources import get_distribution, DistributionNotFound

__project__ = 'Doorstop'
__version__ = None  # required for initial installation

CLI = 'doorstop'


try:
    __version__ = get_distribution(__project__).version  # pylint: disable=E1103
except DistributionNotFound:  # pragma: no cover - can only be tested manually
    VERSION = __project__ + '-' + '(local)'
else:
    VERSION = __project__ + '-' + __version__

try:

    pass

except (ImportError, EnvironmentError) as error:  # pragma: no cover - can only be tested manually
    print(error)
