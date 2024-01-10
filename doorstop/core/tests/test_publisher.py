# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.core.publisher module."""

# pylint: disable=unused-argument,protected-access

import os
import unittest
from secrets import token_hex
from shutil import rmtree
from unittest.mock import Mock, patch

from doorstop.common import DoorstopError
from doorstop.core import publisher
from doorstop.core.builder import build
from doorstop.core.tests import EMPTY, ROOT, MockDataMixIn


class TestModule(MockDataMixIn, unittest.TestCase):
    """Unit tests for the doorstop.core.publisher module."""

    # pylint: disable=no-value-for-parameter
    def setUp(self):
        """Setup test folder."""
        self.mock_tree = build(cwd=ROOT, root=ROOT, request_next_number=None)
        self.hex = token_hex()
        self.dirpath = os.path.abspath(os.path.join("mock_%s" % __name__, self.hex))
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
        if os.path.exists("mock_%s" % __name__):
            rmtree("mock_%s" % __name__)

    def test_publish_document_unknown(self):
        """Verify an exception is raised when publishing unknown formats."""
        self.assertRaises(DoorstopError, publisher.publish, self.document, "a.a")
        self.assertRaises(
            DoorstopError, publisher.publish, self.document, "a.txt", ".a"
        )

    @patch("doorstop.core.vcs.find_root", Mock(return_value=EMPTY))
    def test_nothing_to_publish(self):
        """Verify an exception is raised when publishing nothing."""
        tree = build(EMPTY)
        self.assertRaises(DoorstopError, publisher.publish, tree, "a.txt")

    def test_linkify_none_for_html(self):
        """Verify that linkify = None works correctly."""
        tmp_publisher = publisher.check(".html", self.mock_tree)
        tmp_publisher.setup(None, None, None)
        result = tmp_publisher.getLinkify()
        # Assert
        self.assertEqual(result, True)

    def test_linkify_none_for_latex(self):
        """Verify that linkify = None works correctly."""
        tmp_publisher = publisher.check(".tex", self.mock_tree)
        tmp_publisher.setup(None, None, None)
        result = tmp_publisher.getLinkify()
        # Assert
        self.assertEqual(result, True)

    def test_linkify_none_for_md(self):
        """Verify that linkify = None works correctly."""
        tmp_publisher = publisher.check(".md", self.mock_tree)
        tmp_publisher.setup(None, None, None)
        result = tmp_publisher.getLinkify()
        # Assert
        self.assertEqual(result, True)

    def test_linkify_none_for_txt(self):
        """Verify that linkify = None works correctly."""
        tmp_publisher = publisher.check(".txt", self.mock_tree)
        tmp_publisher.setup(None, None, None)
        result = tmp_publisher.getLinkify()
        # Assert
        self.assertEqual(result, False)

    def test_linkify_true(self):
        """Verify that linkify = true forces true."""
        tmp_publisher = publisher.check(".txt", self.mock_tree)
        tmp_publisher.setup(True, None, None)
        result = tmp_publisher.getLinkify()
        # Assert
        self.assertEqual(result, True)

    def test_linkify_false(self):
        """Verify that linkify = false forces false."""
        tmp_publisher = publisher.check(".html", self.mock_tree)
        tmp_publisher.setup(False, None, None)
        result = tmp_publisher.getLinkify()
        # Assert
        self.assertEqual(result, False)

    def test_index_none_for_html(self):
        """Verify that index = None works correctly."""
        tmp_publisher = publisher.check(".html", self.mock_tree)
        tmp_publisher.setup(None, None, None)
        result = tmp_publisher.getIndex()
        # Assert
        self.assertEqual(result, True)

    def test_index_none_for_latex(self):
        """Verify that index = None works correctly."""
        tmp_publisher = publisher.check(".tex", self.mock_tree)
        tmp_publisher.setup(None, None, None)
        result = tmp_publisher.getIndex()
        # Assert
        self.assertEqual(result, False)

    def test_index_none_for_md(self):
        """Verify that index = None works correctly."""
        tmp_publisher = publisher.check(".md", self.mock_tree)
        tmp_publisher.setup(None, None, None)
        result = tmp_publisher.getIndex()
        # Assert
        self.assertEqual(result, False)

    def test_index_none_for_txt(self):
        """Verify that index = None works correctly."""
        tmp_publisher = publisher.check(".txt", self.mock_tree)
        tmp_publisher.setup(None, None, None)
        result = tmp_publisher.getIndex()
        # Assert
        self.assertEqual(result, False)

    def test_index_true(self):
        """Verify that index = true forces true."""
        tmp_publisher = publisher.check(".html", self.mock_tree)
        tmp_publisher.setup(None, True, None)
        do_index = tmp_publisher.getIndex()
        # Assert
        self.assertEqual(do_index, True)

    def test_index_false(self):
        """Verify that index = false forces false."""
        tmp_publisher = publisher.check(".html", self.mock_tree)
        tmp_publisher.setup(None, False, None)
        do_index = tmp_publisher.getIndex()
        # Assert
        self.assertEqual(do_index, False)

    def test_matrix_none_for_tree(self):
        """Verify that matrix = None works correctly."""
        tmp_publisher = publisher.check(".html", self.mock_tree)
        tmp_publisher.setup(None, None, None)
        result = tmp_publisher.getMatrix()
        # Assert
        self.assertEqual(result, True)

    def test_matrix_none_for_doc(self):
        """Verify that matrix = None works correctly."""
        tmp_publisher = publisher.check(".html", self.document)
        tmp_publisher.setup(None, None, None)
        result = tmp_publisher.getMatrix()
        # Assert
        self.assertEqual(result, False)

    def test_matrix_true(self):
        """Verify that matrix = true forces true."""
        tmp_publisher = publisher.check(".html", self.document)
        tmp_publisher.setup(None, None, True)
        do_index = tmp_publisher.getMatrix()
        # Assert
        self.assertEqual(do_index, True)

    def test_matrix_false(self):
        """Verify that matrix = false forces false."""
        tmp_publisher = publisher.check(".html", self.mock_tree)
        tmp_publisher.setup(None, None, False)
        do_index = tmp_publisher.getMatrix()
        # Assert
        self.assertEqual(do_index, False)
