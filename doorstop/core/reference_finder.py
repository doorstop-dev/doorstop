# SPDX-License-Identifier: LGPL-3.0-only

"""Finding external references."""

import os
import re

import pyficache

from doorstop import common, settings
from doorstop.common import DoorstopError

log = common.logger(__name__)


class ReferenceFinder:
    """Finds files referenced from an Item."""

    @staticmethod
    def find_ref(ref, tree, item_path):
        """Get the external file reference and line number.

        :raises: :class:`~doorstop.common.DoorstopError` when no
            reference is found

        :return: relative path to file or None (when no reference
            set),
            line number (when found in file) or None (when found as
            filename) or None (when no reference set)

        """

        # Search for the external reference
        log.debug("searching for ref '{}'...".format(ref))
        pattern = r"(\b|\W){}(\b|\W)".format(re.escape(ref))
        log.trace("regex: {}".format(pattern))  # type: ignore
        regex = re.compile(pattern)
        for path, filename, relpath in tree.vcs.paths:
            # Skip the item's file while searching
            if path == item_path:
                continue
            # Check for a matching filename
            if filename == ref:
                return relpath, None
            # Skip extensions that should not be considered text
            if os.path.splitext(filename)[-1] in settings.SKIP_EXTS:
                continue
            # Search for the reference in the file
            lines = pyficache.getlines(path)
            if lines is None:
                log.trace("unable to read lines from: {}".format(path))  # type: ignore
                continue
            for lineno, line in enumerate(lines, start=1):
                if regex.search(line):
                    log.debug("found ref: {}".format(relpath))
                    return relpath, lineno

        msg = "external reference not found: {}".format(ref)
        raise DoorstopError(msg)

    @staticmethod
    def find_file_reference(ref_path, root, tree, item_path, keyword=None):
        """Find the external file reference.

        :raises: :class:`~doorstop.common.DoorstopError` when no
            reference is found

        :return: Tuple (ref_path, line) when reference is found

        """

        log.debug("searching for ref '{}'...".format(ref_path))
        ref_full_path = os.path.join(root, ref_path)

        for path, filename, relpath in tree.vcs.paths:
            # Skip the item's file while searching
            if path == item_path:
                continue
            if path == ref_full_path:
                if keyword is None:
                    return relpath, None

                # Search for the reference in the file
                lines = pyficache.getlines(path)
                if lines is None:
                    log.trace(  # type: ignore
                        "unable to read lines from: {}".format(path)
                    )  # type: ignore
                    continue

                log.debug("searching for ref '{}'...".format(keyword))
                pattern = r"(\b|\W){}(\b|\W)".format(re.escape(keyword))
                log.trace("regex: {}".format(pattern))  # type: ignore
                regex = re.compile(pattern)
                for lineno, line in enumerate(lines, start=1):
                    if regex.search(line):
                        log.debug("found ref: {}".format(relpath))
                        return relpath, lineno

        msg = "external reference not found: {}".format(ref_path)
        raise DoorstopError(msg)
