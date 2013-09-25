#!/usr/bin/env python

"""
Unit tests for the doorstop.core.exchange module.
"""

import unittest

from doorstop.core import exchange


class TestModule(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the doorstop.core.exchange module."""  # pylint: disable=C0103

    def test_import_csv(self):
        """Verify a document can be imported as CSV."""
        self.assertRaises(NotImplementedError, exchange.import_csv, None, None)

    def test_import_tsv(self):
        """Verify a document can be imported as TSV."""
        self.assertRaises(NotImplementedError, exchange.import_tsv, None, None)

    def test_export_csv(self):
        """Verify a document can be exported as CSV."""
        self.assertRaises(NotImplementedError, exchange.export_csv, None, None)

    def test_export_tsv(self):
        """Verify a document can be exported as TSV."""
        self.assertRaises(NotImplementedError, exchange.export_tsv, None, None)


if __name__ == '__main__':
    unittest.main()
