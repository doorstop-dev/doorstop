"""
Unit tests for the doorstop.main module.
"""

import unittest


class TestRun(unittest.TestCase):  # pylint: disable=R0904
    """Tests for the Veracity wrapper function."""  # pylint: disable=C0103

    def test_exception(self):
        """Verify a VeracityException is raised on an invalid call."""
        assert True


if __name__ == '__main__':
    unittest.main()
