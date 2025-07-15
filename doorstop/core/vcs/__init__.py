# SPDX-License-Identifier: LGPL-3.0-only

"""Interfaces to version control systems."""
from __future__ import annotations

import os
from pathlib import Path

from doorstop import common
from doorstop.common import DoorstopError
from doorstop.core.vcs import git, mercurial, mockvcs, subversion

DEFAULT = mockvcs.WorkingCopy
DIRECTORIES = {
    git.WorkingCopy.DIRECTORY: git.WorkingCopy,
    subversion.WorkingCopy.DIRECTORY: subversion.WorkingCopy,
    mercurial.WorkingCopy.DIRECTORY: mercurial.WorkingCopy,
    DEFAULT.DIRECTORY: DEFAULT,
}

log = common.logger(__name__)


def find_root(cwd: Path | str) -> Path:
    """Find the root of the working copy.

    :param cwd: current working directory
    :raises: DoorstopError if the root cannot be found
    :return: path to root of working copy
    """
    path = Path(cwd)

    log.debug(f"looking for working copy from {path}...")
    log.debug("options: {}".format(", ".join(DIRECTORIES)))

    for current_path in [path, *path.parents]:
        if any(d.name in DIRECTORIES for d in current_path.iterdir()):
            log.debug(f"found working copy: {current_path}")
            return current_path

    msg = f"no working copy found from: {cwd}"
    raise DoorstopError(msg)


def load(path):
    """Return a working copy for the specified path."""
    for directory in os.listdir(path):
        if directory in DIRECTORIES:
            return DIRECTORIES[directory](path)  # type: ignore

    log.warning("no working copy found at: {}".format(path))
    return DEFAULT(path)
