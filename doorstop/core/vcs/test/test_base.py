"""Unit tests for the doorstop.vcs.base module."""

import unittest

from doorstop.core.vcs.base import BaseWorkingCopy


class SampleWorkingCopy(BaseWorkingCopy):

    """Sample WorkingCopy implementation."""

    @property
    def ignores(self):
        return ["ignored.*"]

    def lock(self, *args, **kwargs):
        pass

    def save(self, *args, **kwargs):
        pass


class TestSampleWorkingCopy(unittest.TestCase):  # pylint: disable=R0904

    """Tests for the doorstop.vcs.base module."""  # pylint: disable=C0103

    def setUp(self):
        self.wc = SampleWorkingCopy(None)

    def test_ignored(self):
        """Verify ignored paths are detected."""
        self.assertTrue(self.wc.ignored("ignored.txt"))
        self.assertFalse(self.wc.ignored("not_ignored.txt"))
