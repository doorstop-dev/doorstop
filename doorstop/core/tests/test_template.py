# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.core.template module."""

# pylint: disable=unused-argument,protected-access

import os
from pathlib import Path
from secrets import token_hex
from shutil import rmtree
import unittest

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
        os.makedirs(self.dirpath)

    @classmethod
    def tearDownClass(cls):
        """Remove test folder."""
        rmtree("mock_%s" % __name__)

    def test_standard_html_doc(self):
        """Verify that default html template is selected if no template is given and input is a document."""
        # Individual docs needs another level to prevent clashing between tests.
        self.dirpath = os.path.join(self.dirpath, self.hex)
        # Act
        asset_dir, selected_template = template.get_template(self.mock_tree.documents[0], self.dirpath, ".html", None)
        # Assert
        self.assertEqual(os.path.join(os.path.dirname(self.dirpath),"assets")  ,asset_dir)
        self.assertEqual("sidebar", selected_template)

    def test_standard_html_tree(self):
        """Verify that default html template is selected if no template is given and input is a tree."""
        # Act
        asset_dir, selected_template = template.get_template(self.mock_tree, self.dirpath, ".html", None)
        # Assert
        self.assertEqual(os.path.join(self.dirpath,"assets")  ,asset_dir)
        self.assertEqual("sidebar", selected_template)

    def test_standard_html_tree_with_assets(self):
        """Verify that default html template is selected if no template is given and input is a tree and there is an assets folder."""
        # Add assets folder.
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
        asset_dir, selected_template = template.get_template(self.mock_tree, self.dirpath, ".html", None)
        # Assert
        self.assertEqual(os.path.join(self.dirpath,"assets")  ,asset_dir)
        self.assertEqual("sidebar", selected_template)
        # Get the exported tree.
        walk = getWalk(self.dirpath)
        self.assertEqual(expected_walk, walk)
