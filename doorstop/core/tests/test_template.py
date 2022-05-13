# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.core.template module."""

# pylint: disable=unused-argument,protected-access

import os
import unittest
from pathlib import Path
from secrets import token_hex
from shutil import rmtree

from doorstop.common import DoorstopError
from doorstop.core import template
from doorstop.core.builder import build
from doorstop.core.tests import ROOT, MockDataMixIn
from doorstop.core.tests.helpers_latex import getWalk


class TestTemplate(MockDataMixIn, unittest.TestCase):
    """Unit tests for the doorstop.core.template."""

    # pylint: disable=no-value-for-parameter
    def setUp(self):
        """Setup test folder."""
        # Build a tree.
        self.mock_tree = build(cwd=ROOT, root=ROOT, request_next_number=None)
        self.hex = token_hex()
        self.dirpath = os.path.abspath(os.path.join("mock_%s" % __name__, self.hex))

    @classmethod
    def tearDownClass(cls):
        """Remove test folder."""
        rmtree("mock_%s" % __name__)
        template_dir = os.path.join("reqs", "template")
        if os.path.isdir(template_dir):
            rmtree(template_dir)

    def test_standard_html_doc(self):
        """Verify that default html template is selected if no template is given and input is a document."""
        # Individual docs needs another level to prevent clashing between tests.
        self.dirpath = os.path.join(self.dirpath, self.hex)
        # Act
        asset_dir, selected_template = template.get_template(
            self.mock_tree.documents[0], self.dirpath, ".html", None
        )
        # Assert
        self.assertEqual(
            os.path.join(os.path.dirname(self.dirpath), "assets"), asset_dir
        )
        self.assertEqual("sidebar", selected_template)

    def test_standard_html_tree(self):
        """Verify that default html template is selected if no template is given and input is a tree."""
        # Act
        asset_dir, selected_template = template.get_template(
            self.mock_tree, self.dirpath, ".html", None
        )
        # Assert
        self.assertEqual(os.path.join(self.dirpath, "assets"), asset_dir)
        self.assertEqual("sidebar", selected_template)

    def test_standard_html_tree_with_assets(self):
        """Verify that default html template is selected if no template is given and input is a tree and there is an assets folder."""
        # Add assets folder.
        os.makedirs(self.dirpath)
        os.mkdir(os.path.join(self.dirpath, "assets"))
        Path(os.path.join(self.dirpath, "assets", "file.txt")).touch()
        # file.txt should not be in expected output!
        expected_walk = """{n}/
    assets/
    template/
        doorstop/
            bootstrap.min.css
            bootstrap.min.js
            general.css
            jquery.min.js
            sidebar.css
""".format(
            n=self.hex
        )

        # Act
        asset_dir, selected_template = template.get_template(
            self.mock_tree, self.dirpath, ".html", None
        )
        # Assert
        self.assertEqual(os.path.join(self.dirpath, "assets"), asset_dir)
        self.assertEqual("sidebar", selected_template)
        # Get the exported tree.
        walk = getWalk(self.dirpath)
        self.assertEqual(expected_walk, walk)

    def test_standard_html_tree_with_template(self):
        """Verify that default html template is selected if no template is given and input is a tree and there is a template folder."""
        # Add template folder.
        os.makedirs(self.dirpath)
        os.mkdir(os.path.join(self.dirpath, "template"))
        Path(os.path.join(self.dirpath, "template", "file.txt")).touch()
        # file.txt should not be in expected output!
        expected_walk = """{n}/
    template/
        doorstop/
            bootstrap.min.css
            bootstrap.min.js
            general.css
            jquery.min.js
            sidebar.css
""".format(
            n=self.hex
        )

        # Act
        asset_dir, selected_template = template.get_template(
            self.mock_tree, self.dirpath, ".html", None
        )
        # Assert
        self.assertEqual(os.path.join(self.dirpath, "assets"), asset_dir)
        self.assertEqual("sidebar", selected_template)
        # Get the exported tree.
        walk = getWalk(self.dirpath)
        self.assertEqual(expected_walk, walk)

    def test_html_doc_with_custom_template(self):
        """Verify that a custom html template is used correctly."""
        # Check that only custom template is published.
        os.makedirs(self.dirpath)
        # Create a custom template folder.
        doc_path = self.mock_tree.documents[0].path
        os.mkdir(os.path.join(doc_path, "template"))
        Path(os.path.join(doc_path, "template", "custom_css.css")).touch()
        expected_walk = """{n}/
    template/
        custom_css.css
""".format(
            n=self.hex
        )
        # Act
        asset_dir, selected_template = template.get_template(
            self.mock_tree, self.dirpath, ".html", "custom_css"
        )
        # Assert
        self.assertEqual(os.path.join(self.dirpath, "assets"), asset_dir)
        self.assertEqual("custom_css", selected_template)
        # Get the exported tree.
        walk = getWalk(self.dirpath)
        self.assertEqual(expected_walk, walk)
        rmtree(os.path.join(doc_path, "template"))

    def test_custom_template_without_folder(self):
        """Verify that a custom template that is missing a locally defined
        custom 'template' folder fails."""
        # Act
        with self.assertRaises(DoorstopError):
            _, _ = template.get_template(
                self.mock_tree, self.dirpath, ".html", "custom_css"
            )

    def test_standard_latex_doc(self):
        """Verify that default latex template is selected if no template is given and input is a document."""
        # Individual docs needs another level to prevent clashing between tests.
        self.dirpath = os.path.join(self.dirpath, self.hex)
        # Act
        asset_dir, selected_template = template.get_template(
            self.mock_tree.documents[0], self.dirpath, ".tex", None
        )
        # Assert
        self.assertEqual(
            os.path.join(os.path.dirname(self.dirpath), "assets"), asset_dir
        )
        self.assertEqual("doorstop", selected_template)

    def test_standard_latex_tree(self):
        """Verify that default latex template is selected if no template is given and input is a tree."""
        # Act
        asset_dir, selected_template = template.get_template(
            self.mock_tree, self.dirpath, ".tex", None
        )
        # Assert
        self.assertEqual(os.path.join(self.dirpath, "assets"), asset_dir)
        self.assertEqual("doorstop", selected_template)

    def test_standard_markdown_doc(self):
        """Verify that default markdown template is selected if no template is given and input is a document."""
        # Individual docs needs another level to prevent clashing between tests.
        self.dirpath = os.path.join(self.dirpath, self.hex)
        # Act
        asset_dir, selected_template = template.get_template(
            self.mock_tree.documents[0], self.dirpath, ".md", None
        )
        # Assert
        self.assertEqual(
            os.path.join(os.path.dirname(self.dirpath), "assets"), asset_dir
        )
        self.assertEqual(None, selected_template)

    def test_standard_markdown_tree(self):
        """Verify that default markdown template is selected if no template is given and input is a tree."""
        # Act
        asset_dir, selected_template = template.get_template(
            self.mock_tree, self.dirpath, ".md", None
        )
        # Assert
        self.assertEqual(os.path.join(self.dirpath, "assets"), asset_dir)
        self.assertEqual(None, selected_template)

    def test_standard_text_doc(self):
        """Verify that default text template is selected if no template is given and input is a document."""
        # Individual docs needs another level to prevent clashing between tests.
        self.dirpath = os.path.join(self.dirpath, self.hex)
        # Act
        asset_dir, selected_template = template.get_template(
            self.mock_tree.documents[0], self.dirpath, ".txt", None
        )
        # Assert
        self.assertEqual(
            os.path.join(os.path.dirname(self.dirpath), "assets"), asset_dir
        )
        self.assertEqual(None, selected_template)

    def test_standard_text_tree(self):
        """Verify that default text template is selected if no template is given and input is a tree."""
        # Act
        asset_dir, selected_template = template.get_template(
            self.mock_tree, self.dirpath, ".txt", None
        )
        # Assert
        self.assertEqual(os.path.join(self.dirpath, "assets"), asset_dir)
        self.assertEqual(None, selected_template)

    def test_read_template_data(self):
        """Verify that the read of LaTeX template data file is working."""
        # Act
        asset_dir, selected_template = template.get_template(
            self.mock_tree, self.dirpath, ".tex", None
        )
        template_data = template.read_template_data(asset_dir, selected_template)
        # Assert
        self.assertEqual(template_data["documentclass"], ["a4paper", "twoside"])

    def test_failed_read_template_data(self):
        """Verify that the read of LaTeX template data file raises an error if
        file is missing."""
        # Act
        asset_dir, _ = template.get_template(self.mock_tree, self.dirpath, ".tex", None)
        # Assert
        with self.assertRaises(DoorstopError):
            _ = template.read_template_data(asset_dir, "bad_name")

    def test_validate_template_data(self):
        """Verify that the validation of template data works correctly."""
        # Act
        asset_dir, selected_template = template.get_template(
            self.mock_tree, self.dirpath, ".tex", None
        )
        template_data = template.read_template_data(asset_dir, selected_template)
        # Assert
        template.check_latex_template_data(template_data)

    def test_validate_template_data_no_package_information(self):
        """Verify that the validation fails if packages are not defined at all."""
        # Act
        asset_dir, selected_template = template.get_template(
            self.mock_tree, self.dirpath, ".tex", None
        )
        template_data = template.read_template_data(asset_dir, selected_template)
        # Remove the usepackage key.
        del template_data["usepackage"]
        # Assert
        with self.assertRaises(DoorstopError):
            template.check_latex_template_data(template_data)

    def test_validate_template_data_package_wrong_format(self):
        """Verify that the validation fails if packages are not defined as a
        package."""
        # Act
        asset_dir, selected_template = template.get_template(
            self.mock_tree, self.dirpath, ".tex", None
        )
        template_data = template.read_template_data(asset_dir, selected_template)
        # Change usepackage to a list.
        template_data["usepackage"] = []
        # Assert
        with self.assertRaises(DoorstopError):
            template.check_latex_template_data(template_data)

    def test_validate_template_data_missing_a_package(self):
        """Verify that the validation fails if a required package is missing."""
        # Act
        asset_dir, selected_template = template.get_template(
            self.mock_tree, self.dirpath, ".tex", None
        )
        template_data = template.read_template_data(asset_dir, selected_template)
        # Remove one of the usepackage sub keys.
        del template_data["usepackage"][list(template.REQUIRED_LATEX_PACKAGES)[0]]
        # Assert
        with self.assertRaises(DoorstopError):
            template.check_latex_template_data(template_data)

    def test_validate_template_data_missing_an_option(self):
        """Verify that the validation fails if a required option is missing
        from a package."""
        # Act
        asset_dir, selected_template = template.get_template(
            self.mock_tree, self.dirpath, ".tex", None
        )
        template_data = template.read_template_data(asset_dir, selected_template)
        # Remove one of the required options.
        template_data["usepackage"]["hyperref"] = [
            "unicode",
        ]
        # Assert
        with self.assertRaises(DoorstopError):
            template.check_latex_template_data(template_data)
