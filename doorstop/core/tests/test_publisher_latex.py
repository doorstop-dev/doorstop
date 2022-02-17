# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.core.publisher_latex module."""

# pylint: disable=unused-argument,protected-access

import os
import unittest
from unittest import mock
from unittest.mock import Mock, call, patch

from doorstop.core import publisher
from doorstop.core.document import Document
from doorstop.core.tests import MockDataMixIn, MockDocument
from doorstop.core.types import iter_documents

YAML_LATEX = """
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
        document._file = YAML_LATEX
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
