# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.core.publishers.markdown module."""

# pylint: disable=unused-argument,protected-access

import os
import unittest
from secrets import token_hex
from shutil import rmtree

from doorstop.core import publisher
from doorstop.core.builder import build
from doorstop.core.publishers.tests.helpers import getWalk
from doorstop.core.tests import ROOT, MockDataMixIn, MockDocument


class TestPublisherFullDocument(MockDataMixIn, unittest.TestCase):
    """Unit tests for the doorstop.core.publishers.markdown module by publishing a full document tree."""

    # pylint: disable=no-value-for-parameter
    def setUp(self):
        """Setup test folder."""
        # Build a tree.
        self.mock_tree = build(cwd=ROOT, root=ROOT, request_next_number=None)
        self.hex = token_hex()
        self.dirpath = os.path.abspath(os.path.join("mock_%s" % __name__, self.hex))
        os.makedirs(self.dirpath)
        self.expected_walk = """{n}/
    HLT.md
    LLT.md
    REQ.md
    TUT.md
    assets/
        logo-black-white.png
""".format(
            n=self.hex
        )

    @classmethod
    def tearDownClass(cls):
        """Remove test folder."""
        rmtree("mock_%s" % __name__)

    def test_publish_markdown_tree_copies_assets(self):
        """Verify that markdown assets are published when publishing a tree."""
        # Act
        path2 = publisher.publish(self.mock_tree, self.dirpath, ext=".md")
        # Assert
        self.assertIs(self.dirpath, path2)
        # Get the exported tree.
        walk = getWalk(self.dirpath)
        self.assertEqual(self.expected_walk, walk)

    def test_publish_markdown_document_to_path(self):
        """Verify that single document export to path works."""
        expected_walk = """{n}/
    REQ.md
""".format(
            n=self.hex
        )
        dirpath = self.dirpath
        doc = MockDocument(dirpath)
        # Act
        path2 = publisher.publish(doc, dirpath, ".md")
        # Assert
        self.assertIs(dirpath, path2)
        # Get the exported tree.
        walk = getWalk(self.dirpath)
        self.assertEqual(expected_walk, walk)
