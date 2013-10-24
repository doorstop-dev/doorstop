#!/usr/bin/env python

"""
Unit tests for the doorstop.core.processor module.
"""

import unittest

import os

from doorstop.core import processor

from doorstop.core.test import FILES


class TestModule(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the doorstop.core.processor module."""  # pylint: disable=C0103

    def test_run_empty(self):
        """Verify an empty directory is an invalid hiearchy."""
        path = os.path.join(FILES, 'empty')
        self.assertFalse(processor.run(path))


if __name__ == '__main__':
    unittest.main()
