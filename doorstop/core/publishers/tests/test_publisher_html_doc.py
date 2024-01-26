# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.core.publishers.html module."""

# pylint: disable=unused-argument,protected-access

import os
import unittest
from secrets import token_hex
from shutil import rmtree

from doorstop.common import DoorstopError
from doorstop.core import publisher
from doorstop.core.builder import build
from doorstop.core.publishers.tests.helpers import HTML_TEMPLATE_WALK, getWalk
from doorstop.core.tests import ROOT, MockDataMixIn


class TestPublisherFullDocument(MockDataMixIn, unittest.TestCase):
    """Unit tests for the doorstop.core.publishers.html module by publishing a full document tree."""

    # pylint: disable=no-value-for-parameter
    def setUp(self):
        """Setup test folder."""
        # Build a tree.
        self.mock_tree = build(cwd=ROOT, root=ROOT, request_next_number=None)
        self.hex = token_hex()
        self.dirpath = os.path.abspath(os.path.join("mock_%s" % __name__, self.hex))
        os.makedirs(self.dirpath)
        self.expected_walk = """{n}/
    index.html
    traceability.csv
    traceability.html
    documents/
        HLT.html
        LLT.html
        REQ.html
        TUT.html
        assets/
            logo-black-white.png{w}""".format(
            n=self.hex, w=HTML_TEMPLATE_WALK
        )

    @classmethod
    def tearDownClass(cls):
        """Remove test folder."""
        rmtree("mock_%s" % __name__)

    def test_publish_html_tree_copies_assets(self):
        """Verify that html assets are published when publishing a tree."""
        # Act
        path2 = publisher.publish(self.mock_tree, self.dirpath, ext=".html")
        # Assert
        self.assertIs(self.dirpath, path2)
        # Get the exported tree.
        walk = getWalk(self.dirpath)
        self.assertEqual(self.expected_walk, walk)

    def test_bad_html_template(self):
        """Verify a bad HTML template raises an error."""
        # Act
        with self.assertRaises(DoorstopError):
            publisher.publish(self.mock_tree, ".html", template="DOES_NOT_EXIST")
