"""Unit tests for the doorstop.vcs.base module."""

import unittest
from unittest.mock import patch

from doorstop.core.vcs.base import BaseWorkingCopy


class SampleWorkingCopy(BaseWorkingCopy):
    """Sample WorkingCopy implementation."""

    def __init__(self, path):
        super().__init__(path)
        self._ignores_cache = ["*build*", "ignored.*", "*published*"]

    def lock(self, path):
        print(path)

    def edit(self, path):
        print(path)

    def add(self, path):
        print(path)

    def delete(self, path):
        print(path)

    def commit(self, message=None):
        print(message)


class TestSampleWorkingCopy(unittest.TestCase):
    """Tests for the doorstop.vcs.base module."""

    def setUp(self):
        self.wc = SampleWorkingCopy(None)

    @patch('os.environ', {})
    def test_ignored(self):
        """Verify ignored paths are detected."""
        self.assertTrue(self.wc.ignored("ignored.txt"))
        self.assertFalse(self.wc.ignored("not_ignored.txt"))
        self.assertTrue(self.wc.ignored("path/to/published.html"))
        self.assertTrue(self.wc.ignored("build/path/to/anything"))
