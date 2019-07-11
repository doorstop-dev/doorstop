# SPDX-License-Identifier: LGPL-3.0-only

"""Integration tests for the doorstop.core.vcs package."""

import os
import unittest
from unittest.mock import Mock, patch

from doorstop.common import DoorstopError
from doorstop.core import vcs

DIR = os.path.dirname(__file__)
ROOT = os.path.join(DIR, '..', '..', '..', '..')


class TestFunctions(unittest.TestCase):
    """Unit tests for top-level VCS functions."""

    @patch('os.listdir', Mock(return_value=['.git']))
    def test_find_root(self):
        """Verify a root VCS directory can be found."""
        path = vcs.find_root('fake/path')
        self.assertEqual('fake/path', path)

    @patch('os.listdir', Mock(return_value=[]))
    def test_find_root_error(self):
        """Verify an error occurs when no VCS directory can be found."""
        self.assertRaises(DoorstopError, vcs.find_root, 'fake')

    def test_load(self):
        """Verify a working copy can be created."""
        working = vcs.load(ROOT)
        self.assertIsInstance(working, vcs.git.WorkingCopy)
        self.assertEqual(ROOT, working.path)

    def test_load_unknown(self):
        """Verify a working copy can be created."""
        working = vcs.load(DIR)
        self.assertIsInstance(working, vcs.mockvcs.WorkingCopy)
        self.assertEqual(DIR, working.path)
