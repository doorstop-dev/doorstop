# SPDX-License-Identifier: LGPL-3.0-only
# pylint: disable=C0302

"""Unit tests for the doorstop.core.validators.item_validator module."""

import os
import unittest
from unittest.mock import MagicMock, Mock, patch

from doorstop import core
from doorstop.common import DoorstopError
from doorstop.core.tests import MockItem, MockItemValidator, MockSimpleDocument
from doorstop.core.tests.helpers import ListLogHandler
from doorstop.core.types import Stamp


class TestItemValidator(unittest.TestCase):
    """Unit tests for the ItemValidator class."""

    # pylint: disable=protected-access,no-value-for-parameter

    def setUp(self):
        path = os.path.join("path", "to", "RQ001.yml")
        self.item = MockItem(MockSimpleDocument(), path)
        self.item_validator = MockItemValidator()

    def test_validate_invalid_ref(self):
        """Verify an invalid ref fails validity."""
        with patch(
            "doorstop.core.item.Item.find_ref",
            Mock(side_effect=DoorstopError("test invalid ref")),
        ):
            with ListLogHandler(core.validators.item_validator.log) as handler:
                self.assertFalse(self.item_validator.validate(self.item))
                self.assertIn("test invalid ref", handler.records)

    def test_validate_invalid_references(self):
        """Verify an invalid reference fails validity."""
        self.item.document = MockSimpleDocument()
        self.item._data["references"] = [{"path": "invalid", "type": "file"}]
        self.item_validator = MockItemValidator()
        with patch(
            "doorstop.core.item.Item.find_references",
            Mock(side_effect=DoorstopError("test invalid reference")),
        ):
            with ListLogHandler(core.validators.item_validator.log) as handler:
                self.assertFalse(self.item_validator.validate(self.item))
                self.assertIn("test invalid reference", handler.records)

    def test_validate_inactive(self):
        """Verify an inactive item is not checked."""
        self.item.active = False
        with patch("doorstop.core.item.Item.find_ref", Mock(side_effect=DoorstopError)):
            self.assertTrue(self.item_validator.validate(self.item))

    def test_validate_reviewed(self):
        """Verify that checking a reviewed item updates the stamp."""
        self.item._data["reviewed"] = True
        self.assertTrue(self.item_validator.validate(self.item))
        stamp = "OoHOpBnrt8us7ph8DVnz5KrQs6UBqj_8MEACA0gWpjY="
        self.assertEqual(stamp, self.item._data["reviewed"])

    @patch("doorstop.settings.REVIEW_NEW_ITEMS", False)
    def test_validate_reviewed_first(self):
        """Verify that a missing initial review leaves the stamp empty."""
        self.item._data["reviewed"] = Stamp(None)
        self.assertTrue(self.item_validator.validate(self.item))
        self.assertEqual(Stamp(None), self.item._data["reviewed"])

    @patch("doorstop.settings.ERROR_ALL", True)
    def test_validate_reviewed_second(self):
        """Verify that a modified stamp fails review."""
        self.item._data["reviewed"] = Stamp("abc123")
        with ListLogHandler(core.validators.item_validator.log) as handler:
            self.assertFalse(self.item_validator.validate(self.item))
            self.assertIn("unreviewed changes", handler.records)

    def test_validate_cleared(self):
        """Verify that checking a cleared link updates the stamp."""
        mock_item = Mock()
        mock_item.stamp = Mock(return_value=Stamp("abc123"))
        mock_tree = MagicMock()
        mock_tree.find_item = Mock(return_value=mock_item)
        self.item.tree = mock_tree
        self.item.links = [{"mock_uid": True}]
        self.item_validator.disable_get_issues_document()
        self.assertTrue(self.item_validator.validate(self.item))
        self.assertEqual("abc123", self.item.links[0].stamp)

    def test_validate_cleared_new(self):
        """Verify that new links are stamped automatically."""
        mock_item = Mock()
        mock_item.stamp = Mock(return_value=Stamp("abc123"))
        mock_tree = MagicMock()
        mock_tree.find_item = Mock(return_value=mock_item)
        self.item.tree = mock_tree
        self.item.links = [{"mock_uid": None}]
        self.item_validator.disable_get_issues_document()
        self.assertTrue(self.item_validator.validate(self.item))
        self.assertEqual("abc123", self.item.links[0].stamp)

    @patch("doorstop.settings.REFORMAT", True)
    def test_validate_reformat_when_setting_is_set(self):
        """Verify that new links are stamped automatically."""
        mock_item = Mock()
        mock_item.stamp = Mock(return_value=Stamp("abc123"))

        mock_tree = MagicMock()
        mock_tree.find_item = Mock(return_value=mock_item)
        self.item.tree = mock_tree
        self.item.links = [{"mock_uid": None}, {"mock_uid": None}]
        self.item_validator.disable_get_issues_document()
        # Assert that validation passes.
        self.assertTrue(self.item_validator.validate(self.item))
        # Assert that stamp was added.
        self.assertEqual("abc123", self.item.links[0].stamp)
        # Assert that 'mock_uid' HAS been changed, i.e., does NOT exist!
        self.assertNotIn("mock_uid", self.item.data["links"][0])

        # two calls:
        # 1) setting up mock links with self.item.links above
        # 2) calling item.links because of REFORMAT == True
        self.assertEqual(self.item._write.call_count, 2)

    @patch("doorstop.settings.REFORMAT", False)
    def test_validate_no_reformat_when_setting_is_not_set(self):
        """Verify that new links are stamped automatically."""

        mock_item = Mock()
        mock_item.stamp = Mock(return_value=Stamp("abc123"))

        mock_tree = MagicMock()
        mock_tree.find_item = Mock(return_value=mock_item)
        self.item.tree = mock_tree
        self.item.links = [{"mock_uid": None}, {"mock_uid": None}]
        self.item_validator.disable_get_issues_document()
        # Assert that validation passes.
        self.assertTrue(self.item_validator.validate(self.item))
        # Assert that stamp was added.
        self.assertEqual("abc123", self.item.links[0].stamp)
        # Assert that 'mock_uid' has NOT been changed, i.e., DOES exist!
        self.assertIn("mock_uid", self.item.data["links"][0])

        # two calls:
        # 1) setting up mock links with self.item.links above
        # 2) calling item.review()
        self.assertEqual(self.item._write.call_count, 2)

    def test_validate_nonnormative_with_links(self):
        """Verify a non-normative item with links can be checked."""
        self.item.normative = False
        self.item.links = ["a"]
        self.item_validator.disable_get_issues_document()
        self.assertTrue(self.item_validator.validate(self.item))

    @patch("doorstop.settings.STAMP_NEW_LINKS", False)
    def test_validate_link_to_inactive(self):
        """Verify a link to an inactive item can be checked."""
        mock_item = Mock()
        mock_item.active = False
        mock_tree = MagicMock()
        mock_tree.find_item = Mock(return_value=mock_item)
        self.item.links = ["a"]
        self.item.tree = mock_tree
        self.item_validator.disable_get_issues_document()
        self.assertTrue(self.item_validator.validate(self.item))

    @patch("doorstop.settings.STAMP_NEW_LINKS", False)
    def test_validate_link_to_nonnormative(self):
        """Verify a link to an non-normative item can be checked."""
        mock_item = Mock()
        mock_item.normative = False
        mock_tree = MagicMock()
        mock_tree.find_item = Mock(return_value=mock_item)
        self.item.links = ["a"]
        self.item.tree = mock_tree
        self.item_validator.disable_get_issues_document()
        self.assertTrue(self.item_validator.validate(self.item))

    def test_validate_document(self):
        """Verify an item can be checked against a document."""
        self.item.document.parent = "fake"
        self.assertTrue(self.item_validator.validate(self.item))

    def test_validate_document_with_links(self):
        """Verify an item can be checked against a document with links."""
        self.item.link("unknown1")
        self.item.document.parent = "fake"
        self.assertTrue(self.item_validator.validate(self.item))

    def test_validate_document_with_bad_link_uids(self):
        """Verify an item can be checked against a document w/ bad links."""
        self.item.link("invalid")
        self.item.document.parent = "fake"
        with ListLogHandler(core.validators.item_validator.log) as handler:
            self.assertFalse(self.item_validator.validate(self.item))
            self.assertIn("invalid UID in links: invalid", handler.records)

    @patch("doorstop.settings.STAMP_NEW_LINKS", False)
    def test_validate_tree(self):
        """Verify an item can be checked against a tree."""

        def mock_iter(self):  # pylint: disable=W0613
            """Mock Tree.__iter__ to yield a mock Document."""
            mock_document = Mock()
            mock_document.parent = "RQ"

            def mock_iter2(self):  # pylint: disable=W0613
                """Mock Document.__iter__ to yield a mock Item."""
                mock_item = Mock()
                mock_item.uid = "TST001"
                mock_item.links = ["RQ001"]
                yield mock_item

            mock_document.__iter__ = mock_iter2
            yield mock_document

        self.item.link("fake1")

        mock_tree = Mock()
        mock_tree.__iter__ = mock_iter
        mock_tree.find_item = lambda uid: Mock(uid="fake1")

        self.item.tree = mock_tree

        self.assertTrue(self.item_validator.validate(self.item))

    def test_validate_tree_error(self):
        """Verify an item can be checked against a tree with errors."""
        self.item.link("fake1")
        mock_tree = MagicMock()
        mock_tree.find_item = Mock(side_effect=DoorstopError)
        self.item.tree = mock_tree
        with ListLogHandler(core.validators.item_validator.log) as handler:
            self.assertFalse(self.item_validator.validate(self.item))
            self.assertIn("linked to unknown item: fake1", handler.records)

    @patch("doorstop.settings.REVIEW_NEW_ITEMS", False)
    def test_validate_both(self):
        """Verify an item can be checked against both."""

        def mock_iter(seq):
            """Create a mock __iter__ method."""

            def _iter(self):  # pylint: disable=W0613
                """Mock __iter__method."""
                yield from seq

            return _iter

        mock_item = Mock()
        mock_item.links = [self.item.uid]

        self.item.document.parent = "BOTH"
        self.item.document.prefix = "BOTH"
        self.item.document.set_items([mock_item])

        mock_tree = Mock()
        mock_tree.__iter__ = mock_iter([self.item.document])
        self.item.tree = mock_tree

        self.assertTrue(self.item_validator.validate(self.item))

    @patch("doorstop.settings.STAMP_NEW_LINKS", False)
    @patch("doorstop.settings.REVIEW_NEW_ITEMS", False)
    def test_validate_both_no_reverse_links(self):
        """Verify an item can be checked against both (no reverse links)."""

        def mock_iter(self):  # pylint: disable=W0613
            """Mock Tree.__iter__ to yield a mock Document."""
            mock_document = Mock()
            mock_document.parent = "RQ"

            def mock_iter2(self):  # pylint: disable=W0613
                """Mock Document.__iter__ to yield a mock Item."""
                mock_item = Mock()
                mock_item.uid = "TST001"
                mock_item.links = []
                yield mock_item

            mock_document.__iter__ = mock_iter2
            yield mock_document

        self.item.link("fake1")

        mock_tree = Mock()
        mock_tree.__iter__ = mock_iter
        mock_tree.find_item = lambda uid: Mock(uid="fake1")
        self.item.tree = mock_tree

        self.assertTrue(self.item_validator.validate(self.item))

    @patch("doorstop.settings.CHECK_CHILD_LINKS_STRICT", True)
    def test_validate_strict_child_links(self):
        """Verify root items are linked to from all child documents"""
        root_doc = MockSimpleDocument()
        root_doc.prefix = "ROOT"

        child_doc_a = MockSimpleDocument()
        child_doc_a.prefix = "CHILD_A"
        child_doc_a.parent = root_doc.prefix

        child_doc_b = MockSimpleDocument()
        child_doc_b.prefix = "CHILD_B"
        child_doc_b.parent = root_doc.prefix

        root_doc.children = [child_doc_a.prefix, child_doc_b.prefix]

        root_item_a = MockItem(root_doc, "ROOT001.yml")
        root_item_b = MockItem(root_doc, "ROOT002.yml")
        child_item_a = MockItem(child_doc_a, "CHILD_A001.yml")
        child_item_b = MockItem(child_doc_b, "CHILD_B001.yml")

        all_items = [root_item_a, root_item_b, child_item_a, child_item_b]

        root_doc.set_items([root_item_a, root_item_b])
        child_doc_a.set_items([child_item_a])
        child_doc_b.set_items([child_item_b])

        def mock_iter(seq):
            """Create a mock __iter__ method."""

            def _iter(self):  # pylint: disable=W0613
                """Mock __iter__method."""
                yield from seq

            return _iter

        mock_tree = Mock()
        mock_tree.__iter__ = mock_iter([root_doc, child_doc_a, child_doc_b])
        mock_tree.find_item = lambda uid: next(
            filter(lambda item: item.uid == uid, all_items), None
        )

        for item in all_items:
            item.text = "text"
            item.tree = mock_tree

        # Only create a link from each child document
        # to a different item in the root document, such
        # that not every item in the root has a child link
        # from every document
        child_item_a.links = [root_item_a.uid]
        child_item_b.links = [root_item_b.uid]

        self.item_validator = MockItemValidator()
        issues = list(self.item_validator.get_issues(root_item_a))
        self.assertEqual(len(issues), 1)
        self.assertIn("no links from document: CHILD_B", "{}".format(issues))

        issues = list(self.item_validator.get_issues(root_item_b))
        self.assertEqual(len(issues), 1)
        self.assertIn("no links from document: CHILD_A", "{}".format(issues))

        # Now make sure that every item in the root is
        # linked to by an item from every child document
        child_item_a.links = [root_item_a.uid, root_item_b.uid]
        child_item_b.links = [root_item_b.uid, root_item_a.uid]

        issues = list(self.item_validator.get_issues(root_item_a))
        self.assertEqual(len(issues), 0)

        issues = list(self.item_validator.get_issues(root_item_b))
        self.assertEqual(len(issues), 0)
