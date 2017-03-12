"""Unit tests for the doorstop.vcs.base module."""

import unittest
from unittest.mock import patch

from doorstop.core.vcs.base import BaseWorkingCopy


class SampleWorkingCopy(BaseWorkingCopy):
    """Sample WorkingCopy implementation."""

    def __init__(self, path):
        super().__init__(path)
        self._ignores_cache = ["*build*", "ignored.*", "*published*"]

    def lock(self, *args, **kwargs):
        pass  # no implementation

    def edit(self, *args, **kwargs):
        pass  # no implementation

    def add(self, *args, **kwargs):
        pass  # no implementation

    def delete(self, *args, **kwargs):
        pass  # no implementation

    def commit(self, *args, **kwargs):
        pass  # no implementation


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

    @patch('os.environ', {'CI': 'true'})
    def test_ignored_on_ci(self):
        """Verify the build directory is not ignored during CI."""
        self.assertTrue(self.wc.ignored("ignored.txt"))
        self.assertFalse(self.wc.ignored("not_ignored.txt"))
        self.assertTrue(self.wc.ignored("path/to/published.html"))
        self.assertFalse(self.wc.ignored("build/path/to/anything"))
