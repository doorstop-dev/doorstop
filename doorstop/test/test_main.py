"""
Unit tests for the veracity.main module.
"""

import unittest

from veracity.main import run, VeracityException


class TestRun(unittest.TestCase):  # pylint: disable=R0904
    """Tests for the Veracity wrapper function."""  # pylint: disable=C0103

    def test_exception(self):
        """Verify a VeracityException is raised on an invalid call."""
        self.assertRaises(VeracityException, run, 'not_a_function')


if __name__ == '__main__':
    unittest.main()
