# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.core.publishers.latex module."""

# pylint: disable=unused-argument,protected-access

import os
import unittest
from unittest.mock import Mock, patch

from doorstop.core import publisher
from doorstop.core.publishers.tests.helpers import getLines
from doorstop.core.publishers.tests.helpers_latex import YAML_LATEX_DOC
from doorstop.core.tests import MockDataMixIn, MockDocument, MockItem, MockItemAndVCS


class TestPublisherModule(MockDataMixIn, unittest.TestCase):
    """Unit tests for the doorstop.core.publishers.latex module, more specifically the changes introduced by the doorstop.core.publishers.latex module."""

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
            r"\section{Header name{ - \small{}\texttt{}REQ-001}}\label{REQ-001}\zlabel{REQ-001}"
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

    @patch("doorstop.settings.ENABLE_HEADERS", True)
    def test_setting_enable_headers_true_not_normative(self):
        """Verify that the settings.ENABLE_HEADERS changes the output appropriately when True and normative is False."""
        generated_data = (
            r"active: true" + "\n"
            r"derived: false" + "\n"
            r"header: 'Header name'" + "\n"
            r"level: 1.0" + "\n"
            r"normative: false" + "\n"
            r"reviewed:" + "\n"
            r"text: |" + "\n"
            r"  Test of a single text line."
        )
        item = MockItemAndVCS(
            "path/to/REQ-001.yml",
            _file=generated_data,
        )
        expected = (
            r"\section{Header name}\label{REQ-001}\zlabel{REQ-001}" + "\n"
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
        self.item6.load()
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
        self.item6.load()
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
        self.item5.load()
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
        self.item5.load()
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

    def test_image_with_title(self):
        """Verify that images are published correctly when title is set."""
        # Setup
        generated_data = (
            r"text: |" + "\n"
            r"  Test of image with title." + "\n\n"
            r'  ![Doorstop Logo](assets/logo-black-white.png "Doorstop Logo")'
        )
        item = MockItemAndVCS(
            "path/to/REQ-001.yml",
            _file=generated_data,
        )
        expected = (
            r"\section{REQ-001}\label{REQ-001}\zlabel{REQ-001}" + "\n\n"
            r"Test of image with title.\\" + "\n\n"
            r"\begin{figure}[h!]\center" + "\n"
            r"\includegraphics[width=0.8\textwidth]{assets/logo-black-white.png}"
            r"\label{fig:DoorstopLogo}\zlabel{fig:DoorstopLogo}"
            r"\caption{Doorstop Logo}" + "\n"
            r"\end{figure}" + "\n\n"
        )
        # Act
        result = getLines(publisher.publish_lines(item, ".tex"))
        # Assert
        self.assertEqual(expected, result)

    def test_image_without_title(self):
        """Verify that images are published correctly when title is **not** set."""
        # Setup
        generated_data = (
            r"text: |" + "\n"
            r"  Test of image with title." + "\n\n"
            r"  ![Doorstop Alt Text](assets/logo-black-white.png)"
        )
        item = MockItemAndVCS(
            "path/to/REQ-001.yml",
            _file=generated_data,
        )
        expected = (
            r"\section{REQ-001}\label{REQ-001}\zlabel{REQ-001}" + "\n\n"
            r"Test of image with title.\\" + "\n\n"
            r"\begin{figure}[h!]\center" + "\n"
            r"\includegraphics[width=0.8\textwidth]{assets/logo-black-white.png}"
            r"\label{fig:DoorstopAltText}\zlabel{fig:DoorstopAltText}"
            r"\caption{Doorstop Alt Text}" + "\n"
            r"\end{figure}" + "\n\n"
        )
        # Act
        result = getLines(publisher.publish_lines(item, ".tex"))
        # Assert
        self.assertEqual(expected, result)

    @patch("doorstop.settings.ENABLE_HEADERS", True)
    def test_formatting_in_header_italics(self):
        """Verify that italic formatting works in headers."""
        generated_data = (
            r"active: true" + "\n"
            r"derived: false" + "\n"
            r"header: 'Header with _italics_'" + "\n"
            r"level: 1.0" + "\n"
            r"normative: true" + "\n"
            r"reviewed:" + "\n"
            r"text: |" + "\n"
            r"  Test of plain text." + "\n"
            r"  Test of _italic_ text."
        )
        item = MockItemAndVCS(
            "path/to/REQ-001.yml",
            _file=generated_data,
        )
        expected = (
            r"\section{Header with \textit{italics}{ - \small{}\texttt{}REQ-001}}\label{REQ-001}\zlabel{REQ-001}"
            + "\n\n"
            r"Test of plain text." + "\n"
            r"Test of \textit{italic} text." + "\n\n"
        )
        # Act
        result = getLines(publisher.publish_lines(item, ".tex"))
        # Assert
        self.assertEqual(expected, result)

    def test_italics_formatting(self):
        """Verify that italic formatting works correctly in all aspects."""
        generated_data = (
            r"active: true" + "\n"
            r"derived: false" + "\n"
            r"header: ''" + "\n"
            r"level: 1.1" + "\n"
            r"normative: false" + "\n"
            r"reviewed:" + "\n"
            r"text: |" + "\n"
            r"  Test of plain text." + "\n"
            r"  Test of _italic_ word." + "\n"
            r"  Test of _italic\_word_ that has a \_ in it." + "\n"
            r"  Test of _a longer italic text_." + "\n"
            r"  Test of a single ital_i_c letter." + "\n"
            r"  Test of *italic* word." + "\n"
            r"  Test of *italic\_word* that has a \_ in it." + "\n"
            r"  Test of *a longer italic text*." + "\n"
            r"  Test of a single ital*i*c letter."
        )
        item = MockItemAndVCS(
            "path/to/REQ-001.yml",
            _file=generated_data,
        )
        expected = (
            r"\subsection{REQ-001}\label{REQ-001}\zlabel{REQ-001}" + "\n\n"
            r"Test of plain text." + "\n"
            r"Test of \textit{italic} word." + "\n"
            r"Test of \textit{italic\_word} that has a \_ in it." + "\n"
            r"Test of \textit{a longer italic text}." + "\n"
            r"Test of a single ital\textit{i}c letter." + "\n"
            r"Test of \textit{italic} word." + "\n"
            r"Test of \textit{italic\_word} that has a \_ in it." + "\n"
            r"Test of \textit{a longer italic text}." + "\n"
            r"Test of a single ital\textit{i}c letter." + "\n" + "\n"
        )
        # Act
        result = getLines(publisher.publish_lines(item, ".tex"))
        # Assert
        self.assertEqual(expected, result)

    @patch("doorstop.settings.ENABLE_HEADERS", True)
    def test_formatting_in_header_bold(self):
        """Verify that bold formatting works in headers."""
        generated_data = (
            r"active: true" + "\n"
            r"derived: false" + "\n"
            r"header: 'Header with **bold**'" + "\n"
            r"level: 1.0" + "\n"
            r"normative: true" + "\n"
            r"reviewed:" + "\n"
            r"text: |" + "\n"
            r"  Test of plain text." + "\n"
            r"  Test of **bold** text."
        )
        item = MockItemAndVCS(
            "path/to/REQ-001.yml",
            _file=generated_data,
        )
        expected = (
            r"\section{Header with \textbf{bold}{ - \small{}\texttt{}REQ-001}}\label{REQ-001}\zlabel{REQ-001}"
            + "\n\n"
            r"Test of plain text." + "\n"
            r"Test of \textbf{bold} text." + "\n\n"
        )
        # Act
        result = getLines(publisher.publish_lines(item, ".tex"))
        # Assert
        self.assertEqual(expected, result)

    @patch("doorstop.settings.ENABLE_HEADERS", True)
    def test_formatting_in_header_special(self):
        """Verify that special character formatting works in headers."""
        generated_data = (
            r"active: true" + "\n"
            r"derived: false" + "\n"
            r"header: 'Header with & sign'" + "\n"
            r"level: 1.0" + "\n"
            r"normative: true" + "\n"
            r"reviewed:" + "\n"
            r"text: |" + "\n"
            r"  Test of plain text." + "\n"
            r"  Test of stuff & text."
        )
        item = MockItemAndVCS(
            "path/to/REQ-001.yml",
            _file=generated_data,
        )
        expected = (
            r"\section{Header with \& sign{ - \small{}\texttt{}REQ-001}}\label{REQ-001}\zlabel{REQ-001}"
            + "\n\n"
            r"Test of plain text." + "\n"
            r"Test of stuff \& text." + "\n\n"
        )
        # Act
        result = getLines(publisher.publish_lines(item, ".tex"))
        # Assert
        self.assertEqual(expected, result)
