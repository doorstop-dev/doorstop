# SPDX-License-Identifier: LGPL-3.0-only

"""Integration tests for the doorstop.vcs package."""

import unittest

from doorstop.core.vcs import load
from doorstop.core.vcs.tests import ROOT


class TestWorkingCopy(unittest.TestCase):
    """Integration tests for a working copy."""

    @classmethod
    def setUpClass(cls):
        cls.wc = load(ROOT)

    def test_ignores(self):
        """Verify the ignores file is parsed."""
        patterns = list(self.wc.ignores)
        for pattern in patterns:
            print(pattern)
        self.assertIn("*__pycache__*", patterns)
        self.assertIn("*build*", patterns)
