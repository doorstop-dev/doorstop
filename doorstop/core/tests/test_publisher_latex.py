# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.core.publisher_latex module."""

# pylint: disable=unused-argument,protected-access

import os
import unittest
from shutil import rmtree
from unittest import mock
from unittest.mock import Mock, call, patch

from doorstop.core import publisher
from doorstop.core.builder import build
from doorstop.core.document import Document
from doorstop.core.tests import ROOT, MockDataMixIn, MockDocument
from doorstop.core.types import iter_documents

YAML_LATEX_DOC = """
settings:
  digits: 3
  prefix: REQ
  sep: ''
attributes:
  defaults:
    doc:
      name: 'Tutorial'
      title: 'Development test document'
      ref: 'TUT-DS-22'
      by: 'Jng'
      major: 1
      minor: A
  publish:
    - CUSTOM-ATTRIB
""".lstrip()

YAML_LATEX_NO_DOC = """
settings:
  digits: 3
  prefix: REQ
  sep: ''
attributes:
  defaults:
    doc:
      name: ''
      title: ''
      ref: ''
      by: ''
      major: ''
      minor: ''
  publish:
    - CUSTOM-ATTRIB
""".lstrip()

LINES = """
initial: 1.2.3
outline:
        - REQ001: # Lorem ipsum d...
        - REQ003: # Unicode: -40° ±1%
        - REQ004: # Hello, world! !['..
        - REQ002: # Hello, world! !["...
        - REQ2-001: # Hello, world!
""".lstrip()


class TestModule(MockDataMixIn, unittest.TestCase):
    """Unit tests for the doorstop.core.publisher_latex module."""

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
    @patch("doorstop.settings.PUBLISH_HEADING_LEVELS", False)
    def test_publish_document_no_headings_with_latex_data(
        self, mock_open, mock_makedirs
    ):
        """Verify a LaTeX document can be published with LaTeX doc data but without publishing heading levels."""
        dirpath = os.path.join("mock", "directory")
        document = MockDocument("/some/path")
        document._file = YAML_LATEX_DOC
        document._items = LINES
        document.load(reload=True)
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


class TestDocument(MockDataMixIn, unittest.TestCase):
    """Unit tests for the doorstop.core.publisher_latex module."""

    # pylint: disable=no-value-for-parameter

    def setUp(self):
        """Setup test folder."""
        # Build a tree.
        self.mock_tree = build(cwd=ROOT, root=ROOT, request_next_number=None)
        self.dirpath = os.path.join("mock", "LaTeX", "directory")
        os.makedirs(self.dirpath)

    def tearDown(self):
        """Remove test folder."""
        rmtree("mock")

    def test_publish_latex_document_copies_assets(self):
        """Verify that LaTeX assets are published."""
        expected_walk = """directory/
    traceability.tex
    TUT.tex
    doc-REQ.tex
    HLT.tex
    compile.sh
    Tutorial.tex
    doc-HLT.tex
    REQ.tex
    LLT.tex
    doc-LLT.tex
    assets/
        logo-black-white.png
        doorstop.cls
"""
        # Act
        path2 = publisher.publish(self.mock_tree, self.dirpath, ".tex")
        # Assert
        self.assertIs(self.dirpath, path2)
        # Get the exported tree.
        walk = ""
        for root, _, files in os.walk(self.dirpath):
            level = root.replace(self.dirpath, "").count(os.sep)
            indent = " " * 4 * (level)
            walk = walk + "{}{}/\n".format(indent, os.path.basename(root))
            subindent = " " * 4 * (level + 1)
            for f in files:
                walk = walk + "{}{}\n".format(subindent, f)
        self.assertEqual(expected_walk, walk)
