"""Unit tests for the doorstop.vcs.base module."""

import unittest

from doorstop.core.vcs.base import BaseWorkingCopy


class SampleWorkingCopy(BaseWorkingCopy):

    """Sample WorkingCopy implementation."""

    def __init__(self, path):
        super().__init__(path)
        self._ignores_cache = ["ignored.*", "*published*"]

    def lock(self, *args, **kwargs):
        pass

    def edit(self, *args, **kwargs):
        pass

    def add(self, *args, **kwargs):
        pass

    def delete(self, *args, **kwargs):
        pass

    def commit(self, *args, **kwargs):
        pass


class TestSampleWorkingCopy(unittest.TestCase):

    """Tests for the doorstop.vcs.base module."""

    def setUp(self):
        self.wc = SampleWorkingCopy(None)

    def test_ignored(self):
        """Verify ignored paths are detected."""
        self.assertTrue(self.wc.ignored("ignored.txt"))
        self.assertFalse(self.wc.ignored("not_ignored.txt"))
        self.assertTrue(self.wc.ignored("path/to/published.html"))
