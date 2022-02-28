# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.core.publisher_latex module."""

# pylint: disable=unused-argument,protected-access

import os
import unittest
from secrets import token_hex
from shutil import rmtree
from unittest import mock
from unittest.mock import Mock, call, patch

from doorstop.core import publisher, publisher_latex
from doorstop.core.builder import build
from doorstop.core.document import Document
from doorstop.core.tests import ROOT, MockDataMixIn, MockDocument, MockItem
from doorstop.core.tests.helpers import (
    LINES,
    YAML_LATEX_DOC,
    YAML_LATEX_NO_DOC,
    getLines,
    getWalk,
)
from doorstop.core.types import iter_documents


class TestPublisherModule(MockDataMixIn, unittest.TestCase):
    """Unit tests for the doorstop.core.publisher_latex module, more specifically the changes introduced by the doorstop.core.publisher_latex module."""

    @patch("os.path.isdir", Mock(return_value=False))
    @patch("os.makedirs")
    @patch("builtins.open")
    def test_publish_document_with_latex_data(self, mock_open, mock_makedirs):
        """Verify a LaTeX document can be published with LaTeX doc data."""
        dirpath = os.path.join("mock", "directory")
        document = MockDocument("/some/path")
        document._file = YAML_LATEX_DOC
        document._items = LINES
        document.load(reload=True)
        itemPath = os.path.join("path", "to", "REQ-001.yml")
        item = MockItem(document, itemPath)
        item._file = LINES
        item.load(reload=True)
        document._items.append(item)
        path = os.path.join(dirpath, str(self.document))
        expected_calls = [
            call(
                os.path.join("mock", "directory", "Tutorial.tex"),
                "wb",
            ),
            call(
                os.path.join("mock", "directory", "{n}.tex".format(n=str(document))),
                "wb",
            ),
            call(os.path.join("mock", "directory", "compile.sh"), "wb"),
        ]
        # Act
        path2 = publisher.publish(document, path, ".tex")
        # Assert
        self.assertIs(path, path2)
        mock_makedirs.assert_called_once_with(os.path.join(dirpath, Document.ASSETS))
        self.assertEqual(expected_calls, mock_open.call_args_list)
        self.assertEqual(mock_open.call_count, 3)

    @patch("os.path.isdir", Mock(return_value=False))
    @patch("os.makedirs")
    @patch("builtins.open")
    def test_publish_document_without_latex_data(self, mock_open, mock_makedirs):
        """Verify a LaTeX document can be published without LaTeX doc data."""
        dirpath = os.path.join("mock", "directory")
        document = MockDocument("/some/path")
        document._file = YAML_LATEX_NO_DOC
        document._items = LINES
        document.load(reload=True)
        itemPath = os.path.join("path", "to", "REQ-001.yml")
        item = MockItem(document, itemPath)
        item._file = LINES
        item.load(reload=True)
        document._items.append(item)
        path = os.path.join(dirpath, str(self.document))
        expected_calls = [
            call(
                os.path.join("mock", "directory", "doc-REQ.tex"),
                "wb",
            ),
            call(
                os.path.join("mock", "directory", "{n}.tex".format(n=str(document))),
                "wb",
            ),
            call(os.path.join("mock", "directory", "compile.sh"), "wb"),
        ]
        # Act
        path2 = publisher.publish(document, path, ".tex", linkify=True, matrix=True)
        # Assert
        self.assertIs(path, path2)
        mock_makedirs.assert_called_once_with(os.path.join(dirpath, Document.ASSETS))
        self.assertEqual(expected_calls, mock_open.call_args_list)
        self.assertEqual(mock_open.call_count, 3)

    @patch("os.path.isdir", Mock(return_value=False))
    @patch("os.makedirs")
    @patch("builtins.open")
    def test_publish_tree(self, mock_open, mock_makedirs):
        """Verify a LaTeX document tree can be published."""
        dirpath = os.path.join("mock", "directory")
        mock_open.side_effect = lambda *args, **kw: mock.mock_open(
            read_data="$body"
        ).return_value
        expected_calls = []
        for obj2, _ in iter_documents(self.mock_tree, dirpath, ".tex"):
            expected_calls.append(
                call(
                    os.path.join(
                        "mock", "directory", "doc-{n}.tex".format(n=str(obj2))
                    ),
                    "wb",
                )
            )
            expected_calls.append(
                call(
                    os.path.join("mock", "directory", "{n}.tex".format(n=str(obj2))),
                    "wb",
                )
            )

        expected_calls.append(
            call(os.path.join("mock", "directory", "compile.sh"), "wb")
        )
        expected_calls.append(
            call(os.path.join("mock", "directory", "traceability.tex"), "wb")
        )
        # Act
        dirpath2 = publisher.publish(self.mock_tree, dirpath, ".tex")
        # Assert
        self.assertIs(dirpath, dirpath2)
        self.assertEqual(expected_calls, mock_open.call_args_list)
        self.assertEqual(mock_open.call_count, 4)

    @patch("doorstop.settings.PUBLISH_HEADING_LEVELS", True)
    def test_setting_publish_heading_levels_true(self):
        """Verify that the settings.PUBLISH_HEADING_LEVELS changes the output appropriately when True."""
        # Setup
        generated_data = """active: true
derived: false
header: 'Header name'
level: '1.0'
normative: false
ref: ''
reviewed:
text: |
  Test of a single text line as a header!
"""
        expected_result = r"""\section{Test of a single text line as a header!}\label{REQ-001}\zlabel{REQ-001}

"""
        # Arrange
        document = MockDocument("/some/path")
        path = os.path.join("path", "to", "REQ-001.yml")
        item = MockItem(document, path)
        item._file = generated_data
        item.load(reload=True)
        document._file = YAML_LATEX_DOC
        document.load(reload=True)
        document._items.append(item)

        # Act
        result = getLines(publisher_latex._lines_latex(document))

        # Assert
        self.assertEqual(expected_result, result)

    @patch("doorstop.settings.PUBLISH_HEADING_LEVELS", False)
    def test_setting_publish_heading_levels_false(self):
        """Verify that the settings.PUBLISH_HEADING_LEVELS changes the output appropriately when False."""
        # Setup
        generated_data = """active: true
derived: false
header: 'Header name'
level: '1.0'
normative: false
ref: ''
reviewed:
text: |
  Test of a single text line as a header!
"""
        expected_result = r"""\section*{Test of a single text line as a header!}\label{REQ-001}\zlabel{REQ-001}

"""
        # Arrange
        document = MockDocument("/some/path")
        path = os.path.join("path", "to", "REQ-001.yml")
        item = MockItem(document, path)
        item._file = generated_data
        item.load(reload=True)
        document._file = YAML_LATEX_DOC
        document.load(reload=True)
        document._items.append(item)

        # Act
        result = getLines(publisher_latex._lines_latex(document))

        # Assert
        self.assertEqual(expected_result, result)


class TestPublisherFullDocument(MockDataMixIn, unittest.TestCase):
    """Unit tests for the doorstop.core.publisher_latex module by publishing a full document tree."""

    # pylint: disable=no-value-for-parameter
    def setUp(self):
        """Setup test folder."""
        # Build a tree.
        self.mock_tree = build(cwd=ROOT, root=ROOT, request_next_number=None)
        self.hex = token_hex()
        self.dirpath = os.path.join("mock", "LaTeX", self.hex)
        os.makedirs(self.dirpath)
        self.expected_walk = """{n}/
    traceability.tex
    TUT.tex
    doc-TUT.tex
    doc-REQ.tex
    HLT.tex
    compile.sh
    doc-HLT.tex
    REQ.tex
    LLT.tex
    doc-LLT.tex
    assets/
        logo-black-white.png
        doorstop.cls
""".format(
            n=self.hex
        )

    @classmethod
    def tearDownClass(cls):
        """Remove test folder."""
        rmtree("mock")

    def test_publish_latex_document_copies_assets(self):
        """Verify that LaTeX assets are published."""
        # Act
        path2 = publisher.publish(self.mock_tree, self.dirpath, ".tex")
        # Assert
        self.assertIs(self.dirpath, path2)
        # Get the exported tree.
        walk = getWalk(self.dirpath)
        self.assertEqual(self.expected_walk, walk)

    @patch("doorstop.settings.PUBLISH_HEADING_LEVELS", False)
    def test_publish_document_no_headings_with_latex_data(self):
        """Verify a LaTeX document can be published with LaTeX doc data but without publishing heading levels."""
        # Act
        path2 = publisher.publish(self.mock_tree, self.dirpath, ".tex")
        # path2 = publisher.publish(self.document, path, ".tex")
        # Assert
        self.assertIs(self.dirpath, path2)
        # Get the exported tree.
        walk = getWalk(self.dirpath)
        self.assertEqual(self.expected_walk, walk)
