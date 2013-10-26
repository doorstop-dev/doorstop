#!/usr/bin/env python

"""
Integration tests for the doorstop.core.vcs package.
"""

import unittest
from unittest.mock import patch, Mock

from doorstop.core import vcs


class TestFunctions(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for top-level VCS functions."""

    @patch('os.listdir', Mock(return_value=['.sgdrawer']))
    def test_find_root(self):
        """Verify a root VCS directory can be found."""
        path = vcs.find_root('fake/path')
        self.assertEqual('fake/path', path)

    @patch('os.listdir', Mock(return_value=[]))
    def test_find_root_error(self):
        """Verify an error occurs when no VCS directory can be found."""
        self.assertRaises(vcs.VersionControlError, vcs.find_root, 'fake')
