# SPDX-License-Identifier: LGPL-3.0-only

"""Package for the doorstop.core tests."""

import logging
import os
from typing import List
from unittest.mock import MagicMock, Mock, patch

from doorstop.core.base import BaseFileObject
from doorstop.core.document import Document
from doorstop.core.item import Item
from doorstop.core.validators.item_validator import ItemValidator
from doorstop.core.vcs.mockvcs import WorkingCopy

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

TESTS_ROOT = os.path.dirname(__file__)
FILES = os.path.join(os.path.dirname(__file__), 'files')
SYS = os.path.join(FILES, 'parent')
TST = os.path.join(FILES, 'child')
EMPTY = os.path.join(FILES, 'empty')  # an empty directory
EXTERNAL = os.path.join(FILES, 'external')  # external files to reference
NEW = os.path.join(FILES, 'new')  # new document with no items

ENV = 'TEST_INTEGRATION'  # environment variable to enable integration tests
REASON = "'{0}' variable not set".format(ENV)


if not os.path.exists(EMPTY):
    os.makedirs(EMPTY)


class DocumentNoSkip(Document):
    """Document class that is never skipped."""

    SKIP = '__disabled__'  # never skip test Documents


class MockFileObject(BaseFileObject):  # pylint: disable=W0223,R0902
    """Mock FileObject class with stubbed file IO."""

    def __init__(self, *args, **kwargs):
        self._file = kwargs.pop('_file', "")  # mock file system contents
        with patch('os.path.isfile', Mock(return_value=True)):
            super().__init__(*args, **kwargs)  # type: ignore
        self._read = Mock(side_effect=self._mock_read)
        self._write = Mock(side_effect=self._mock_write)

    _create = Mock()

    def _mock_read(self, path):
        """Mock read method."""
        logging.debug("mock read path: {}".format(path))
        text = self._file
        logging.debug("mock read text: {}".format(repr(text)))
        return text

    def _mock_write(self, text, path):
        """Mock write method."""
        logging.debug("mock write text: {}".format(repr(text)))
        logging.debug("mock write path: {}".format(path))
        self._file = text

    def __bool__(self):  # override __len__ behavior, pylint: disable=R0201
        return True


class MockItem(MockFileObject, Item):  # pylint: disable=W0223,R0902
    """Mock Item class with stubbed file IO."""


class MockItemValidator(ItemValidator):  # pylint: disable=W0223,R0902
    """Mock Item class with stubbed file IO."""

    def _no_get_issues_document(
        self, item, document, skip
    ):  # pylint: disable=W0613,R0201
        return
        yield  # pylint: disable=W0101

    def disable_get_issues_document(self):
        self._get_issues_document = self._no_get_issues_document


class MockDocument(MockFileObject, Document):  # pylint: disable=W0223,R0902
    """Mock Document class with stubbed file IO."""


class MockSimpleDocument:
    """Mock Document class with basic default members."""

    def __init__(self):
        self.parent = None
        self.prefix = 'RQ'
        self._items: List[Item] = []
        self.extended_reviewed: List[str] = []

    def __iter__(self):
        yield from self._items

    def set_items(self, items):
        self._items = items


class MockDocumentSkip(MockDocument):  # pylint: disable=W0223,R0902
    """Mock Document class that is always skipped in tree placement."""

    skip = True


class MockDocumentNoSkip(MockDocumentSkip):  # pylint: disable=W0223,R0902
    """Mock Document class that is never skipped in tree placement."""

    SKIP = '__disabled__'  # never skip mock Documents


class MockItemAndVCS(MockItem):  # pylint: disable=W0223,R0902
    """Mock item class with stubbed IO and a mock VCS reference."""

    def __init__(self, *args, **kwargs):
        super().__init__(None, *args, **kwargs)
        self.tree = Mock()
        self.tree.vcs = WorkingCopy(None)


class MockDataMixIn:  # pylint: disable=W0232,R0903
    """Data for test cases requiring mock items and documents."""

    # purely mock objects

    mock_document = MagicMock()
    mock_document.prefix = 'MOCK'
    mock_document.items = []
    mock_document.assets = None
    mock_tree = MagicMock()
    mock_tree.documents = [mock_document]

    # mock objects that behave like the real thing

    item = MockItemAndVCS(
        'path/to/req3.yml',
        _file=(
            "links: [sys3]" + '\n'
            "text: 'Heading'" + '\n'
            "level: 1.1.0" + '\n'
            "normative: false"
        ),
    )

    item2 = MockItemAndVCS(
        'path/to/req3.yml',
        _file=("links: [sys3]\ntext: '" + ("Hello, world! " * 10) + "'\nlevel: 1.2"),
    )
    _mock_item = Mock()
    _mock_item.uid = 'sys3'
    _mock_item.document.prefix = 'sys'
    item2.tree = Mock()
    item2.tree.find_item = Mock(return_value=_mock_item)
    _mock_item2 = Mock()
    _mock_item2.uid = 'tst1'
    _mock_item2.document.prefix = 'tst'
    # pylint: disable=undefined-variable
    item2.find_child_links = lambda: [MockDataMixIn._mock_item2.uid]  # type: ignore
    item2.find_child_items = lambda: [MockDataMixIn._mock_item2]  # type: ignore

    document = MagicMock(spec=['items'])
    document.items = [
        item,
        item2,
        MockItemAndVCS(
            'path/to/req1.yml', _file="links: []\ntext: 'abc\n123'\nlevel: 1.1"
        ),
        MockItemAndVCS('path/to/req2.yml', _file="links: []\ntext: ''\nlevel: 2"),
        MockItemAndVCS(
            'path/to/req4.yml',
            _file="links: []\nref: 'CHECK_PUBLISHED_CONTENT'\n" "level: 2.1.1",
        ),
        MockItemAndVCS(
            'path/to/req2.yml',
            _file="links: [sys1]\ntext: 'Heading 2'\nlevel: 2.1.0\n" "normative: false",
        ),
    ]
    document.copy_assets = Mock()
    document.assets = None

    item3 = MockItem(
        None,
        'path/to/req4.yml',
        _file=(
            "links: [sys4]" + '\n'
            "text: 'This shall...'" + '\n'
            "ref: Doorstop.sublime-project" + '\n'
            "level: 1.2" + '\n'
            "normative: true"
        ),
    )
    _mock_item3 = Mock()
    _mock_item3.uid = 'sys4'
    _mock_item3.document.prefix = 'sys'
    item3.tree = Mock()
    item3.tree.find_item = Mock(return_value=_mock_item3)
    item3.tree.vcs.paths = [
        (
            "Doorstop.sublime-project",
            "Doorstop.sublime-project",
            "Doorstop.sublime-project",
        )
    ]

    item4 = MockItemAndVCS(
        'path/to/req3.yml',
        _file=(
            "links: [sys3]" + '\n'
            "text: 'Heading'" + '\n'
            "long: " + ('"' + '0' * 66 + '"') + '\n'
            "level: 1.1.0" + '\n'
            "normative: false"
        ),
    )

    item5 = MockItemAndVCS(
        'path/to/req3.yml',
        _file=(
            "links: [sys3]" + '\n'
            "text: 'Heading'" + '\n'
            "level: 2.1.2" + '\n'
            "normative: false" + '\n'
            "ref: 'abc123'"
        ),
    )

    item6 = MockItemAndVCS(
        'path/to/req3.yml',
        _file=(
            "links: [sys3]" + '\n'
            "text: 'Heading'" + '\n'
            "level: 2.1.2" + '\n'
            "normative: false" + '\n'
            "references:" + '\n'
            "  - path: abc1" + '\n'
            "    type: file" + '\n'
            "  - path: abc2" + '\n'
            "    type: file" + '\n'
        ),
    )
