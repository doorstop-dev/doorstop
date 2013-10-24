#!/usr/bin/env python

"""
Unit tests for the doorstop.core.processor module.
"""

import unittest

from doorstop.core import processor


class TestModule(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the doorstop.core.processor module."""  # pylint: disable=C0103

    def test_run(self):
        """Verify run can be called with default arguments."""
        self.assertRaises(NotImplementedError, processor.run, None)


if __name__ == '__main__':
    unittest.main()
