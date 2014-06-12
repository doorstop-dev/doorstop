"""Interfaces to version control systems."""

import os
import logging

from doorstop.common import DoorstopError

from doorstop.core.vcs import git
from doorstop.core.vcs import veracity
from doorstop.core.vcs import subversion
from doorstop.core.vcs import mockvcs

from doorstop.core.vcs.base import BaseWorkingCopy as _bwc
DIRECTORIES = {wc.DIRECTORY: wc for wc in _bwc.__subclasses__()}  # pylint: disable=E1101


def find_root(cwd):
    """Find the root of the working copy.

    :param cwd: current working directory

    :raises: :class:`doorstop.common.DoorstopError` if the root cannot be found

    :return: path to root of working copy

    """
    path = cwd

    logging.debug("looking for working copy from {}...".format(path))
    logging.debug("options: {}".format(', '.join([d for d in DIRECTORIES])))
    while not any(d in DIRECTORIES for d in os.listdir(path)):
        parent = os.path.dirname(path)
        if path == parent:
            msg = "no working copy found from: {}".format(cwd)
            raise DoorstopError(msg)
        else:
            path = parent

    logging.debug("found working copy: {}".format(path))
    return path


def load(path):
    """Return a working copy for the specified path."""
    for directory in os.listdir(path):
        if directory in DIRECTORIES:
            return DIRECTORIES[directory](path)
    logging.warning("no working copy found at: {}".format(path))
    return mockvcs.WorkingCopy(path)
