# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.__init__ module."""
import unittest
from importlib import reload
from importlib.metadata import PackageNotFoundError
from unittest.mock import patch

import doorstop


class InitTestCase(unittest.TestCase):
    """Init test class for server tests."""

    @patch("importlib.metadata.version")
    def test_import(self, mock_version):
        """Verify the doorstop package can be imported as a local version.

        This test is a bit of a hack. It is intended to verify that the
        doorstop package can be imported as a local version. This is
        necessary because if the doorstop package is not installed in the
        test environment, the version shall be set to "(local)". The patch
        ensures that the version lookup will fail.
        """
        mock_version.side_effect = PackageNotFoundError()

        # Reload the doorstop package to allow import of the patched version.
        reload(doorstop)
        from doorstop import VERSION

        # Assert that the version number is correct.
        self.assertEqual("Doorstop v(local)", VERSION)
