# SPDX-License-Identifier: LGPL-3.0-only

"""Interfaces to version control systems."""

import logging
import os

from doorstop import common
from doorstop.common import DoorstopError
from doorstop.core.vcs import git, mercurial, mockvcs, subversion, veracity

DEFAULT = mockvcs.WorkingCopy
DIRECTORIES = {
    git.WorkingCopy.DIRECTORY: git.WorkingCopy,
    subversion.WorkingCopy.DIRECTORY: subversion.WorkingCopy,
    veracity.WorkingCopy.DIRECTORY: veracity.WorkingCopy,
    mercurial.WorkingCopy.DIRECTORY: mercurial.WorkingCopy,
    DEFAULT.DIRECTORY: DEFAULT,
}

log = common.logger(__name__)


def find_root(cwd):
    """Find the root of the working copy.

    :param cwd: current working directory

    :raises: :class:`doorstop.common.DoorstopError` if the root cannot be found

    :return: path to root of working copy

    """
    path = cwd

    log.debug("looking for working copy from {}...".format(path))
    log.debug("options: {}".format(', '.join([d for d in DIRECTORIES])))
    while not any(d in DIRECTORIES for d in os.listdir(path)):
        parent = os.path.dirname(path)
        if path == parent:
            msg = "no working copy found from: {}".format(cwd)
            raise DoorstopError(msg)
        path = parent

    log.debug("found working copy: {}".format(path))
    return path


def load(path):
    """Return a working copy for the specified path."""
    for directory in os.listdir(path):
        if directory in DIRECTORIES:
            return DIRECTORIES[directory](path)  # type: ignore

    log.warning("no working copy found at: {}".format(path))
    return DEFAULT(path)
