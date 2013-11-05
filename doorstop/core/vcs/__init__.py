#!/usr/bin/env python

"""
Interfaces to version control systems.
"""

import os
import logging

from doorstop.common import DoorstopError

# TODO: build dymacially from the modules in this package
VCS_DIRECTORIES = ['.git', '.sgdrawer', '.mockvcs']


class VersionControlError(DoorstopError):
    """Exception for Version Control errors."""


def find_root(cwd):
    """Find the root of the working copy.

    @param: current working directory
    """
    path = cwd

    logging.debug("looking for working copy from {}...".format(path))
    while not any(d in VCS_DIRECTORIES for d in os.listdir(path)):
        parent = os.path.dirname(path)
        if path == parent:
            msg = "no working copy found from: {}".format(cwd)
            raise VersionControlError(msg)
        else:
            path = parent

    logging.debug("found working copy: {}".format(path))
    return path
