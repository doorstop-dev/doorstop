# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.core.publisher_latex module."""

# pylint: disable=unused-argument,protected-access

import os
import unittest
from secrets import token_hex
from shutil import rmtree
from unittest.mock import patch

from doorstop.core import publisher
from doorstop.core.builder import build
from doorstop.core.tests import ROOT, MockDataMixIn, MockDocument
from doorstop.core.tests.helpers_latex import YAML_LATEX_DOC, YAML_LATEX_NO_DOC, getWalk


class TestPublisherFullDocument(MockDataMixIn, unittest.TestCase):
    """Unit tests for the doorstop.core.publisher_latex module by publishing a full document tree."""

    # pylint: disable=no-value-for-parameter
    def setUp(self):
        """Setup test folder."""
        # Build a tree.
        self.mock_tree = build(cwd=ROOT, root=ROOT, request_next_number=None)
        self.hex = token_hex()
        self.dirpath = os.path.abspath(os.path.join("mock_%s" % __name__, self.hex))
        os.makedirs(self.dirpath)
        self.expected_walk = """{n}/
    HLT.tex
    LLT.tex
    REQ.tex
    TUT.tex
    compile.sh
    doc-HLT.tex
    doc-LLT.tex
    doc-REQ.tex
    doc-TUT.tex
    traceability.tex
    assets/
        logo-black-white.png
    template/
        doorstop.cls
        doorstop.yml
        logo-black-white.png
""".format(
            n=self.hex
        )

    @classmethod
    def tearDownClass(cls):
        """Remove test folder."""
        rmtree("mock_%s" % __name__)

    def test_publish_latex_tree_copies_assets(self):
        """Verify that LaTeX assets are published when publishing a tree."""
        # Act
        path2 = publisher.publish(self.mock_tree, self.dirpath, ".tex")
        # Assert
        self.assertIs(self.dirpath, path2)
        # Get the exported tree.
        walk = getWalk(self.dirpath)
        self.assertEqual(self.expected_walk, walk)

    def test_publish_latex_document_copies_assets(self):
        """Verify that LaTeX assets are published when publishing a document."""
        expected_walk = """{n}/
    TUT.tex
    compile.sh
    doc-TUT.tex
    template/
        doorstop.cls
        doorstop.yml
        logo-black-white.png
""".format(
            n=self.hex
        )
        # Act
        dirpath = self.dirpath + "/dummy.tex"
        path2 = publisher.publish(self.mock_tree.find_document("TUT"), dirpath, ".tex")
        # Assert
        self.assertIs(dirpath, path2)
        # Get the exported tree.
        walk = getWalk(self.dirpath)
        self.assertEqual(expected_walk, walk)

    @patch("doorstop.settings.PUBLISH_HEADING_LEVELS", False)
    def test_publish_document_no_headings_with_latex_data(self):
        """Verify a LaTeX document can be published with LaTeX doc data but without publishing heading levels."""
        # Act
        path2 = publisher.publish(self.mock_tree, self.dirpath, ".tex")
        # Assert
        self.assertIs(self.dirpath, path2)
        # Get the exported tree.
        walk = getWalk(self.dirpath)
        self.assertEqual(self.expected_walk, walk)

    def test_publish_latex_document_with_attributes(self):
        """Verify that LaTeX specific attributes are published when publishing a document."""
        expected_walk = """{n}/
    REQ.tex
    Tutorial.tex
    compile.sh
    template/
        doorstop.cls
        doorstop.yml
        logo-black-white.png
""".format(
            n=self.hex
        )
        dirpath = self.dirpath + "/dummy.tex"
        doc_with_attributes = MockDocument(dirpath)
        doc_with_attributes._file = YAML_LATEX_DOC
        doc_with_attributes.load(reload=True)
        # Act
        path2 = publisher.publish(doc_with_attributes, dirpath, ".tex")
        # Assert
        self.assertIs(dirpath, path2)
        # Get the exported tree.
        walk = getWalk(self.dirpath)
        self.assertEqual(expected_walk, walk)

    def test_publish_latex_document_without_attributes(self):
        """Verify that missing LaTeX attibutes does not fail publish."""
        expected_walk = """{n}/
    TST.tex
    compile.sh
    doc-TST.tex
    template/
        doorstop.cls
        doorstop.yml
        logo-black-white.png
""".format(
            n=self.hex
        )
        dirpath = self.dirpath + "/dummy.tex"
        doc_with_attributes = MockDocument(dirpath)
        doc_with_attributes._file = YAML_LATEX_NO_DOC
        doc_with_attributes.load(reload=True)
        # Act
        path2 = publisher.publish(doc_with_attributes, dirpath, ".tex")
        # Assert
        self.assertIs(dirpath, path2)
        # Get the exported tree.
        walk = getWalk(self.dirpath)
        self.assertEqual(expected_walk, walk)
