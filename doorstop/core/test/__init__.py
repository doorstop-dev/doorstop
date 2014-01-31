"""
Package for the doorstop.core tests.
"""

import unittest
from unittest.mock import patch, Mock

import os
import logging

from doorstop.core.base import BaseFileObject


ROOT = os.path.join(os.path.dirname(__file__), '..', '..', '..')

FILES = os.path.join(os.path.dirname(__file__), 'files')
SYS = os.path.join(FILES, 'sys')
EMPTY = os.path.join(FILES, 'empty')  # an empty directory
EXTERNAL = os.path.join(FILES, 'external')  # external files to reference
NEW = os.path.join(FILES, 'new')  # new document with no items

ENV = 'TEST_INTEGRATION'  # environment variable to enable integration tests
REASON = "'{0}' variable not set".format(ENV)


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
        """Mock write method"""
        logging.debug("mock write text: {}".format(repr(text)))
        logging.debug("mock write path: {}".format(path))
        self._file = text
