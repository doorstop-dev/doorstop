#!/usr/bin/env python

"""
Settings for the Doorstop package.
"""

import logging

# Logging settings
DEFAULT_LOGGING_FORMAT = "%(message)s"
VERBOSE_LOGGING_FORMAT = "%(levelname)s: %(message)s"
VERBOSE2_LOGGING_FORMAT = "%(levelname)s: %(module)s:%(lineno)d: %(message)s"
DEFAULT_LOGGING_LEVEL = logging.WARNING
VERBOSE_LOGGING_LEVEL = logging.INFO
VERBOSE2_LOGGING_LEVEL = logging.DEBUG
