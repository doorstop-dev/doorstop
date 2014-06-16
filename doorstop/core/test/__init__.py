"""Package for the doorstop.core tests."""

import unittest
from unittest.mock import patch, Mock, MagicMock

import os
import logging

from doorstop.core.base import BaseFileObject
from doorstop.core.item import Item
from doorstop.core.document import Document
from doorstop.core.vcs.mockvcs import WorkingCopy


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                    '..', '..', '..'))

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


class DocumentNoSkip(Document):  # pylint: disable=R0904

    """Document class that is never skipped."""

    SKIP = '__disabled__'  # never skip test Documents


class MockFileObject(BaseFileObject):  # pylint: disable=W0223,R0902,R0904

    """Mock FileObject class with stubbed file IO."""

    def __init__(self, *args, **kwargs):
        self._file = kwargs.pop('_file', "")  # mock file system contents
        with patch('os.path.isfile', Mock(return_value=True)):
            super().__init__(*args, **kwargs)
        self._read = Mock(side_effect=self._mock_read)
        self._write = Mock(side_effect=self._mock_write)

    _new = Mock()

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


class MockItem(MockFileObject, Item):  # pylint: disable=W0223,R0902,R0904

    """Mock Item class with stubbed file IO."""


class MockDocument(MockFileObject, Document):  # pylint: disable=W0223,R0902,R0904

    """Mock Document class with stubbed file IO."""


class MockDocumentSkip(MockDocument):  # pylint: disable=W0223,R0902,R0904

    """Mock Document class that is always skipped in tree placement."""

    skip = True


class MockDocumentNoSkip(MockDocumentSkip):  # pylint: disable=W0223,R0902,R0904

    """Mock Document class that is never skipped in tree placement."""

    SKIP = '__disabled__'  # never skip mock Documents


class MockItemAndVCS(MockItem):  # pylint: disable=W0223,R0902,R0904

    """Mock item class with stubbed IO and a mock VCS reference."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree = Mock()
        self.tree.vcs = WorkingCopy(None)


class MockDataMixIn:  # pylint: disable=W0232,R0903

    """Data for test cases requiring mock items and documents."""

    item = MockItemAndVCS('path/to/req3.yml',
                          _file=("links: [sys3]" + '\n'
                                 "text: 'Heading'" + '\n'
                                 "level: 1.1.0" + '\n'
                                 "normative: false"))

    item2 = MockItemAndVCS('path/to/req3.yml',
                           _file=("links: [sys3]\ntext: '" +
                                  ("Hello, world! " * 10) +
                                  "'\nlevel: 1.2"))
    _mock_item = Mock()
    _mock_item.id = 'sys3'
    _mock_item.document.prefix = 'sys'
    item2.tree = Mock()
    item2.tree.find_item = Mock(return_value=_mock_item)
    _mock_item2 = Mock()
    _mock_item2.id = 'tst1'
    _mock_item2.document.prefix = 'tst'
    item2.find_child_links = lambda: [MockDataMixIn._mock_item2.id]
    item2.find_child_items = lambda: [MockDataMixIn._mock_item2]

    document = MagicMock(spec=['items'])
    document.items = [
        item,
        item2,
        MockItemAndVCS('path/to/req1.yml',
                       _file="links: []\ntext: 'abc\n123'\nlevel: 1.1"),
        MockItemAndVCS('path/to/req2.yml',
                       _file="links: []\ntext: ''\nlevel: 2"),
        MockItemAndVCS('path/to/req4.yml',
                       _file="links: []\nref: 'CHECK_PUBLISHED_CONTENT'\n"
                       "level: 2.1.1"),
        MockItemAndVCS('path/to/req2.yml',
                       _file="links: [sys1]\ntext: 'Heading 2'\nlevel: 2.1.0\n"
                       "normative: false"),
    ]

    item3 = MockItem('path/to/req4.yml', _file=(
        "links: [sys4]" + '\n'
        "text: 'This shall...'" + '\n'
        "ref: Doorstop.sublime-project" + '\n'
        "level: 1.2" + '\n'
        "normative: true"))
    _mock_item3 = Mock()
    _mock_item3.id = 'sys4'
    _mock_item3.document.prefix = 'sys'
    item3.tree = Mock()
    item3.tree.find_item = Mock(return_value=_mock_item3)
    item3.tree.vcs.ignored = (lambda _: False)

    item4 = MockItemAndVCS('path/to/req3.yml',
                           _file=("links: [sys3]" + '\n'
                                  "text: 'Heading'" + '\n'
                                  "long: " + ('"' + '0' * 66 + '"') + '\n'
                                  "level: 1.1.0" + '\n'
                                  "normative: false"))
