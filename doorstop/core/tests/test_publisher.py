# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.core.publisher module."""

# pylint: disable=unused-argument,protected-access

import os
import unittest
from secrets import token_hex
from shutil import rmtree

from doorstop.common import DoorstopError
from doorstop.core import publisher
from doorstop.core.tests import MockDataMixIn


class TestModule(MockDataMixIn, unittest.TestCase):
    """Unit tests for the doorstop.core.publisher module."""

    # pylint: disable=no-value-for-parameter
    def setUp(self):
        """Setup test folder."""
        self.hex = token_hex()
        self.dirpath = os.path.abspath(os.path.join("mock_%s" % __name__, self.hex))

    @classmethod
    def tearDownClass(cls):
        """Remove test folder."""
        if os.path.exists("mock_%s" % __name__):
            rmtree("mock_%s" % __name__)

    def test_publish_document_unknown(self):
        """Verify an exception is raised when publishing unknown formats."""
        self.assertRaises(DoorstopError, publisher.publish, self.document, "a.a")
        self.assertRaises(
            DoorstopError, publisher.publish, self.document, "a.txt", ".a"
        )
