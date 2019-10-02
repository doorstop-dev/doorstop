# SPDX-License-Identifier: LGPL-3.0-only
# pylint: disable=C0302

"""Unit tests for the doorstop.core.reference_finder module."""

import os
import unittest
from unittest.mock import Mock

from doorstop.common import DoorstopError
from doorstop.core.reference_finder import ReferenceFinder
from doorstop.core.tests import TESTS_ROOT, MockItem, MockSimpleDocument
from doorstop.core.vcs.mockvcs import WorkingCopy


class TestReferenceFinder(unittest.TestCase):
    """Unit tests for the ReferenceFinder class."""

    def setUp(self):
        path = os.path.join('path', 'to', 'RQ001.yml')
        self.item = MockItem(MockSimpleDocument(), path)

    def test_check_file_reference(self):
        reference_path = "files/REQ001.yml"
        root = TESTS_ROOT
        tree = Mock()
        tree.vcs = WorkingCopy(TESTS_ROOT)
        item_path = os.path.join('path', 'to', 'RQ001.yml')

        # Act
        reference_finder = ReferenceFinder()

        reference_exist = reference_finder.check_file_reference(
            reference_path, root, tree, item_path
        )

        # Assert
        self.assertTrue(reference_exist)

    def test_check_file_reference_should_skip_item_path(self):
        root = TESTS_ROOT
        tree = Mock()
        tree.vcs = WorkingCopy(TESTS_ROOT)
        item_path = os.path.join('path', 'to', 'RQ001.yml')

        # Act
        reference_finder = ReferenceFinder()

        with self.assertRaises(DoorstopError) as context:
            reference_finder.check_file_reference(item_path, root, tree, item_path)

        self.assertTrue('external reference not found' in str(context.exception))

    def test_check_file_reference_valid_keyword_given(self):
        keyword = "Lorem ipsum dolor sit amet"
        reference_path = "files/REQ001.yml"
        root = TESTS_ROOT
        tree = Mock()
        tree.vcs = WorkingCopy(TESTS_ROOT)
        item_path = os.path.join('path', 'to', 'RQ001.yml')

        # Act
        reference_finder = ReferenceFinder()

        reference_exist = reference_finder.check_file_reference(
            reference_path, root, tree, item_path, keyword
        )

        # Assert
        self.assertTrue(reference_exist)

    def test_check_file_reference_invalid_keyword_given(self):
        keyword = "Invalid keyword"
        reference_path = "files/REQ001.yml"
        root = TESTS_ROOT
        tree = Mock()
        tree.vcs = WorkingCopy(TESTS_ROOT)
        item_path = os.path.join('path', 'to', 'RQ001.yml')

        reference_finder = ReferenceFinder()

        with self.assertRaises(DoorstopError) as context:
            reference_finder.check_file_reference(
                reference_path, root, tree, item_path, keyword
            )

        self.assertTrue('external reference not found' in str(context.exception))

    def test_check_file_reference_does_not_exist(self):
        reference_path = "reference-that-does-not-exist.yml"
        root = TESTS_ROOT
        tree = Mock()
        tree.vcs = WorkingCopy(TESTS_ROOT)
        item_path = os.path.join('path', 'to', 'RQ001.yml')

        reference_finder = ReferenceFinder()

        with self.assertRaises(DoorstopError) as context:
            reference_finder.check_file_reference(reference_path, root, tree, item_path)

        self.assertTrue('external reference not found' in str(context.exception))
