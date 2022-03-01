# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.core.publisher_latex module."""

# pylint: disable=unused-argument,protected-access

import os
import unittest
from secrets import token_hex
from shutil import rmtree
from unittest import mock
from unittest.mock import Mock, call, patch

from doorstop.common import DoorstopError
from doorstop.core import publisher
from doorstop.core.builder import build
from doorstop.core.document import Document
from doorstop.core.tests import (
    ROOT,
    MockDataMixIn,
    MockDocument,
    MockItem,
    MockItemAndVCS,
)
from doorstop.core.tests.helpers_latex import (
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
        # Setup
        dirpath = os.path.join("mock", "directory")
        document = MockDocument("/some/path")
        document._file = YAML_LATEX_DOC
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
        # Setup
        dirpath = os.path.join("mock", "directory")
        document = MockDocument("/some/path")
        document._file = YAML_LATEX_NO_DOC
        document.load(reload=True)
        itemPath = os.path.join("path", "to", "TST-001.yml")
        item = MockItem(document, itemPath)
        item._file = LINES
        item.load(reload=True)
        document._items.append(item)
        path = os.path.join(dirpath, str(self.document))
        expected_calls = [
            call(
                os.path.join("mock", "directory", "doc-TST.tex"),
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
        # Setup
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
        expected = r"\subsection{Heading}\label{req3}\zlabel{req3}" + "\n\n"
        # Act
        result = getLines(publisher.publish_lines(self.item, ".tex"))
        # Assert
        self.assertEqual(expected, result)

    @patch("doorstop.settings.PUBLISH_HEADING_LEVELS", False)
    def test_setting_publish_heading_levels_false(self):
        """Verify that the settings.PUBLISH_HEADING_LEVELS changes the output appropriately when False."""
        # Setup
        expected = r"\subsection*{Heading}\label{req3}\zlabel{req3}" + "\n\n"
        # Act
        result = getLines(publisher.publish_lines(self.item, ".tex"))
        # Assert
        self.assertEqual(expected, result)

    @patch("doorstop.settings.ENABLE_HEADERS", True)
    def test_setting_enable_headers_true(self):
        """Verify that the settings.ENABLE_HEADERS changes the output appropriately when True."""
        generated_data = (
            r"active: true" + "\n"
            r"derived: false" + "\n"
            r"header: 'Header name'" + "\n"
            r"level: 1.0" + "\n"
            r"normative: true" + "\n"
            r"reviewed:" + "\n"
            r"text: |" + "\n"
            r"  Test of a single text line."
        )
        item = MockItemAndVCS(
            "path/to/REQ-001.yml",
            _file=generated_data,
        )
        expected = (
            r"\section{Header name{\small{}REQ-001}}\label{REQ-001}\zlabel{REQ-001}"
            + "\n\n"
            r"Test of a single text line." + "\n\n"
        )
        # Act
        result = getLines(publisher.publish_lines(item, ".tex"))
        # Assert
        self.assertEqual(expected, result)

    @patch("doorstop.settings.ENABLE_HEADERS", False)
    def test_setting_enable_headers_false(self):
        """Verify that the settings.ENABLE_HEADERS changes the output appropriately when False."""
        generated_data = (
            r"active: true" + "\n"
            r"derived: false" + "\n"
            r"header: 'Header name'" + "\n"
            r"level: 1.0" + "\n"
            r"normative: true" + "\n"
            r"reviewed:" + "\n"
            r"text: |" + "\n"
            r"  Test of a single text line."
        )
        item = MockItemAndVCS(
            "path/to/REQ-001.yml",
            _file=generated_data,
        )
        expected = (
            r"\section{REQ-001}\label{REQ-001}\zlabel{REQ-001}" + "\n\n"
            r"Test of a single text line." + "\n\n"
        )
        # Act
        result = getLines(publisher.publish_lines(item, ".tex"))
        # Assert
        self.assertEqual(expected, result)

    @patch("doorstop.settings.PUBLISH_BODY_LEVELS", True)
    def test_setting_publish_body_levels_true(self):
        """Verify that the settings.PUBLISH_BODY_LEVELS changes the output appropriately when True."""
        # Setup
        generated_data = (
            r"active: true" + "\n"
            r"derived: false" + "\n"
            r"header: ''" + "\n"
            r"level: 1.1" + "\n"
            r"normative: true" + "\n"
            r"reviewed:" + "\n"
            r"text: |" + "\n"
            r"  Test of a single text line."
        )
        item = MockItemAndVCS(
            "path/to/REQ-001.yml",
            _file=generated_data,
        )
        expected = (
            r"\subsection{REQ-001}\label{REQ-001}\zlabel{REQ-001}" + "\n\n"
            r"Test of a single text line." + "\n\n"
        )
        # Act
        result = getLines(publisher.publish_lines(item, ".tex"))
        # Assert
        self.assertEqual(expected, result)

    @patch("doorstop.settings.PUBLISH_BODY_LEVELS", False)
    def test_setting_publish_body_levels_false(self):
        """Verify that the settings.PUBLISH_BODY_LEVELS changes the output appropriately when False."""
        # Setup
        generated_data = (
            r"active: true" + "\n"
            r"derived: false" + "\n"
            r"header: ''" + "\n"
            r"level: 1.1" + "\n"
            r"normative: true" + "\n"
            r"reviewed:" + "\n"
            r"text: |" + "\n"
            r"  Test of a single text line."
        )
        item = MockItemAndVCS(
            "path/to/REQ-001.yml",
            _file=generated_data,
        )
        expected = (
            r"\subsection*{REQ-001}\label{REQ-001}\zlabel{REQ-001}" + "\n\n"
            r"Test of a single text line." + "\n\n"
        )
        # Act
        result = getLines(publisher.publish_lines(item, ".tex"))
        # Assert
        self.assertEqual(expected, result)

    @patch("doorstop.settings.PUBLISH_CHILD_LINKS", True)
    def test_setting_publish_child_links_true(self):
        """Verify that the settings.PUBLISH_CHILD_LINKS changes the output appropriately when True."""
        # Setup
        expected = (
            r"\subsection{req4}\label{req4}\zlabel{req4}" + "\n\n"
            r"This shall..." + "\n\n"
            r"\begin{quote} \verb|Doorstop.sublime-project|\end{quote}" + "\n\n"
            r"\textbf{Parent links: sys4}" + "\n\n"
        )
        # Act
        result = getLines(publisher.publish_lines(self.item3, ".tex"))
        # Assert
        self.assertEqual(expected, result)

    @patch("doorstop.settings.PUBLISH_CHILD_LINKS", False)
    def test_setting_publish_child_links_false(self):
        """Verify that the settings.PUBLISH_CHILD_LINKS changes the output appropriately when False."""
        # Setup
        expected = (
            r"\subsection{req4}\label{req4}\zlabel{req4}" + "\n\n"
            r"This shall..." + "\n\n"
            r"\begin{quote} \verb|Doorstop.sublime-project|\end{quote}" + "\n\n"
            r"\textbf{Links: sys4}" + "\n\n"
        )
        # Act
        result = getLines(publisher.publish_lines(self.item3, ".tex"))
        # Assert
        self.assertEqual(expected, result)

    @patch("doorstop.settings.CHECK_REF", False)
    def test_external_reference_check_ref_false(self):
        """Verify that external references are published correctly with settings.CHECK_REF set to False."""
        # Setup
        mock_value = [("path/to/mock/file1", 3), ("path/to/mock/file2", None)]
        self.item6.unlink("sys3")
        expected = (
            r"\subsubsection{req3}\label{req3}\zlabel{req3}" + "\n\n"
            r"Heading" + "\n\n"
            r"\begin{quote} \verb|abc1|\end{quote}" + "\n"
            r"\begin{quote} \verb|abc2|\end{quote}" + "\n\n"
        )
        # Act
        with patch.object(self.item6, "find_references", Mock(return_value=mock_value)):
            result = getLines(publisher.publish_lines(self.item6, ".tex"))
        # Assert
        self.assertEqual(expected, result)

    @patch("doorstop.settings.CHECK_REF", True)
    def test_external_reference_check_ref_true(self):
        """Verify that external references are published correctly with settings.CHECK_REF set to True."""
        # Setup
        mock_value = [("path/to/mock/file1", 3), ("path/to/mock/file2", None)]
        self.item6.unlink("sys3")
        expected = (
            r"\subsubsection{req3}\label{req3}\zlabel{req3}" + "\n\n"
            r"Heading" + "\n\n"
            r"\begin{quote} \verb|path/to/mock/file1| (line 3)\end{quote}" + "\n"
            r"\begin{quote} \verb|path/to/mock/file2|\end{quote}" + "\n\n"
        )
        # Act
        with patch.object(self.item6, "find_references", Mock(return_value=mock_value)):
            result = getLines(publisher.publish_lines(self.item6, ".tex"))
        # Assert
        self.assertEqual(expected, result)

    @patch("doorstop.settings.CHECK_REF", False)
    def test_external_ref_check_ref_false(self):
        """DEPRECATED: Verify that external references (OLD ref:) are published correctly with settings.CHECK_REF set to False."""
        # Setup
        mock_value = ("path/to/mock/abc123", None)
        self.item5.unlink("sys3")
        expected = (
            r"\subsubsection{req3}\label{req3}\zlabel{req3}" + "\n\n"
            r"Heading" + "\n\n"
            r"\begin{quote} \verb|abc123|\end{quote}" + "\n\n"
        )
        # Act
        with patch.object(self.item5, "find_ref", Mock(return_value=mock_value)):
            result = getLines(publisher.publish_lines(self.item5, ".tex"))
        # Assert
        self.assertEqual(expected, result)

    @patch("doorstop.settings.CHECK_REF", True)
    def test_external_ref_check_ref_true(self):
        """DEPRECATED: Verify that external references (OLD ref:) are published correctly with settings.CHECK_REF set to True."""
        # Setup
        mock_value = ("path/to/mock/abc123", None)
        self.item5.unlink("sys3")
        expected = (
            r"\subsubsection{req3}\label{req3}\zlabel{req3}" + "\n\n"
            r"Heading" + "\n\n"
            r"\begin{quote} \verb|path/to/mock/abc123|\end{quote}" + "\n\n"
        )
        # Act
        with patch.object(self.item5, "find_ref", Mock(return_value=mock_value)):
            result = getLines(publisher.publish_lines(self.item5, ".tex"))
        # Assert
        self.assertEqual(expected, result)

    def test_custom_attributes(self):
        """Verify that custom attributes are published correctly."""
        # Setup
        generated_data = (
            r"CUSTOM-ATTRIB: true" + "\n"
            r"invented-by: jane@example.com" + "\n"
            r"text: |" + "\n"
            r"  Test of custom attributes."
        )
        document = MockDocument("/some/path")
        document._file = YAML_LATEX_DOC
        document.load(reload=True)
        itemPath = os.path.join("path", "to", "REQ-001.yml")
        item = MockItem(document, itemPath)
        item._file = generated_data
        item.load(reload=True)
        document._items.append(item)
        expected = (
            r"\section{REQ-001}\label{REQ-001}\zlabel{REQ-001}" + "\n\n"
            r"Test of custom attributes." + "\n"
            r"\begin{longtable}{|l|l|}" + "\n"
            r"Attribute & Value\\" + "\n"
            r"\hline" + "\n"
            r"CUSTOM-ATTRIB & True" + "\n"
            r"invented-by & jane@example.com" + "\n"
            r"\end{longtable}" + "\n\n"
        )
        # Act
        result = getLines(publisher.publish_lines(document, ".tex"))
        # Assert
        self.assertEqual(expected, result)

    def test_multiline_math(self):
        """Verify that math environments over multiple lines are published correctly."""
        # Setup
        generated_data = (
            r"text: |" + "\n"
            r"  Test of multiline math environments." + "\n"
            r"  " + "\n"
            r"  $$" + "\n"
            r"  \frac{a*b}{0} = \infty{}" + "\n"
            r"  \text{where}" + "\n"
            r"  a = 2.0" + "\n"
            r"  b = 32" + "\n"
            r"  $$"
        )
        item = MockItemAndVCS(
            "path/to/REQ-001.yml",
            _file=generated_data,
        )
        expected = (
            r"\section{REQ-001}\label{REQ-001}\zlabel{REQ-001}" + "\n\n"
            r"Test of multiline math environments.\\" + "\n\n"
            r"$\\" + "\n"
            r"\frac{a*b}{0} = \infty{}\\" + "\n"
            r"\text{where}\\" + "\n"
            r"a = 2.0\\" + "\n"
            r"b = 32\\" + "\n"
            r"$" + "\n\n"
        )
        # Act
        result = getLines(publisher.publish_lines(item, ".tex"))
        # Assert
        self.assertEqual(expected, result)

    def test_multiline_math_error(self):
        """Verify that math environments that are badly specified generates an error."""
        # Setup
        generated_data = (
            r"text: |" + "\n"
            r"  Test of multiline math environments." + "\n"
            r"  " + "\n"
            r"  $$\frac{a*b}{0} = \infty{}$$where$$s" + "\n"
        )
        item = MockItemAndVCS(
            "path/to/REQ-001.yml",
            _file=generated_data,
        )
        # Act & Assert
        with self.assertRaises(DoorstopError):
            _ = getLines(publisher.publish_lines(item, ".tex"))

    def test_enumerate_environment_normal_ending(self):
        """Verify that enumerate environments are published correctly with normal ending."""
        # Setup
        generated_data = (
            r"text: |" + "\n"
            r"  Test of enumeration end." + "\n"
            r"  " + "\n"
            r"  1. item one" + "\n"
            r"  21. item two" + "\n"
            r"  441. item three"
        )
        item = MockItemAndVCS(
            "path/to/REQ-001.yml",
            _file=generated_data,
        )
        expected = (
            r"\section{REQ-001}\label{REQ-001}\zlabel{REQ-001}" + "\n\n"
            r"Test of enumeration end.\\" + "\n\n"
            r"\begin{enumerate}" + "\n"
            r"\item item one" + "\n"
            r"\item item two" + "\n"
            r"\item item three" + "\n"
            r"\end{enumerate}" + "\n\n"
        )
        # Act
        result = getLines(publisher.publish_lines(item, ".tex"))
        # Assert
        self.assertEqual(expected, result)

    def test_enumerate_environment_empty_row_ending(self):
        """Verify that enumerate environments are published correctly with and empty row ending."""
        # Setup
        generated_data = (
            r"text: |" + "\n"
            r"  Test of enumeration end." + "\n"
            r"  " + "\n"
            r"  1. item one" + "\n"
            r"  21. item two" + "\n"
            r"  441. item three" + "\n"
            r"" + "\n"
            r"  This is not an item!"
        )
        item = MockItemAndVCS(
            "path/to/REQ-001.yml",
            _file=generated_data,
        )
        expected = (
            r"\section{REQ-001}\label{REQ-001}\zlabel{REQ-001}" + "\n\n"
            r"Test of enumeration end.\\" + "\n\n"
            r"\begin{enumerate}" + "\n"
            r"\item item one" + "\n"
            r"\item item two" + "\n"
            r"\item item three" + "\n"
            r"\end{enumerate}" + "\n\n"
            r"This is not an item!" + "\n\n"
        )
        # Act
        result = getLines(publisher.publish_lines(item, ".tex"))
        # Assert
        self.assertEqual(expected, result)

    def test_enumerate_environment_multiline_item(self):
        """Verify that enumerate environments are published correctly with multiline items."""
        # Setup
        generated_data = (
            r"text: |" + "\n"
            r"  Test of enumeration end." + "\n"
            r"  " + "\n"
            r"  1. item one" + "\n"
            r"  21. item two" + "\n"
            r"  441. item three" + "\n"
            r"  This still a part of the previous item!" + "\n"
            r"  **This too!**" + "\n"
        )
        item = MockItemAndVCS(
            "path/to/REQ-001.yml",
            _file=generated_data,
        )
        expected = (
            r"\section{REQ-001}\label{REQ-001}\zlabel{REQ-001}" + "\n\n"
            r"Test of enumeration end.\\" + "\n\n"
            r"\begin{enumerate}" + "\n"
            r"\item item one" + "\n"
            r"\item item two" + "\n"
            r"\item item three" + "\n"
            r"This still a part of the previous item!" + "\n"
            r"\textbf{This too!}" + "\n"
            r"\end{enumerate}" + "\n\n"
        )
        # Act
        result = getLines(publisher.publish_lines(item, ".tex"))
        # Assert
        self.assertEqual(expected, result)

    def test_itemize_environment_normal_ending(self):
        """Verify that itemize environments are published correctly with normal ending."""
        # Setup
        generated_data = (
            r"text: |" + "\n"
            r"  Test of itemization end." + "\n"
            r"  " + "\n"
            r"  * item one" + "\n"
            r"  + item two" + "\n"
            r"  - item three"
        )
        item = MockItemAndVCS(
            "path/to/REQ-001.yml",
            _file=generated_data,
        )
        expected = (
            r"\section{REQ-001}\label{REQ-001}\zlabel{REQ-001}" + "\n\n"
            r"Test of itemization end.\\" + "\n\n"
            r"\begin{itemize}" + "\n"
            r"\item item one" + "\n"
            r"\item item two" + "\n"
            r"\item item three" + "\n"
            r"\end{itemize}" + "\n\n"
        )
        # Act
        result = getLines(publisher.publish_lines(item, ".tex"))
        # Assert
        self.assertEqual(expected, result)

    def test_itemize_environment_empty_row_ending(self):
        """Verify that itemize environments are published correctly with and empty row ending."""
        # Setup
        generated_data = (
            r"text: |" + "\n"
            r"  Test of itemization end." + "\n"
            r"  " + "\n"
            r"  * item one" + "\n"
            r"  + item two" + "\n"
            r"  - item three" + "\n"
            r"" + "\n"
            r"  This is not an item!"
        )
        item = MockItemAndVCS(
            "path/to/REQ-001.yml",
            _file=generated_data,
        )
        expected = (
            r"\section{REQ-001}\label{REQ-001}\zlabel{REQ-001}" + "\n\n"
            r"Test of itemization end.\\" + "\n\n"
            r"\begin{itemize}" + "\n"
            r"\item item one" + "\n"
            r"\item item two" + "\n"
            r"\item item three" + "\n"
            r"\end{itemize}" + "\n\n"
            r"This is not an item!" + "\n\n"
        )
        # Act
        result = getLines(publisher.publish_lines(item, ".tex"))
        # Assert
        self.assertEqual(expected, result)

    def test_itemize_environment_multiline_item(self):
        """Verify that itemize environments are published correctly with multiline items."""
        # Setup
        generated_data = (
            r"text: |" + "\n"
            r"  Test of itemization end." + "\n"
            r"  " + "\n"
            r"  * item one" + "\n"
            r"  + item two" + "\n"
            r"  - item three" + "\n"
            r"  This still a part of the previous item!" + "\n"
            r"  This too!" + "\n"
            r"  " + "\n"
            r"  But not this!" + "\n"
        )
        item = MockItemAndVCS(
            "path/to/REQ-001.yml",
            _file=generated_data,
        )
        expected = (
            r"\section{REQ-001}\label{REQ-001}\zlabel{REQ-001}" + "\n\n"
            r"Test of itemization end.\\" + "\n\n"
            r"\begin{itemize}" + "\n"
            r"\item item one" + "\n"
            r"\item item two" + "\n"
            r"\item item three" + "\n"
            r"This still a part of the previous item!" + "\n"
            r"This too!" + "\n"
            r"\end{itemize}" + "\n\n"
            r"But not this!" + "\n\n"
        )
        # Act
        result = getLines(publisher.publish_lines(item, ".tex"))
        # Assert
        self.assertEqual(expected, result)


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
