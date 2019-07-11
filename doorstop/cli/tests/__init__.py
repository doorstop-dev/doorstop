# SPDX-License-Identifier: LGPL-3.0-only

"""Package for the doorstop.cli tests."""

import os
import unittest

from doorstop import settings
from doorstop.cli.main import main

ROOT = os.path.join(os.path.dirname(__file__), '..', '..', '..')
REQS = os.path.join(ROOT, 'reqs')
TUTORIAL = os.path.join(REQS, 'tutorial')
FILES = os.path.join(os.path.dirname(__file__), 'files')

ENV = 'TEST_INTEGRATION'  # environment variable to enable integration tests
REASON = "'{0}' variable not set".format(ENV)


class SettingsTestCase(unittest.TestCase):
    """Base test case class that backs up settings."""

    def setUp(self):
        self.backup = (
            settings.REFORMAT,
            settings.CHECK_REF,
            settings.CHECK_CHILD_LINKS,
            settings.REORDER,
            settings.CHECK_LEVELS,
            settings.PUBLISH_CHILD_LINKS,
            settings.CHECK_SUSPECT_LINKS,
            settings.CHECK_REVIEW_STATUS,
            settings.PUBLISH_BODY_LEVELS,
            settings.CACHE_DOCUMENTS,
            settings.CACHE_ITEMS,
            settings.CACHE_PATHS,
            settings.WARN_ALL,
            settings.ERROR_ALL,
            settings.SERVER_HOST,
            settings.SERVER_PORT,
        )

    def tearDown(self):
        (
            settings.REFORMAT,
            settings.CHECK_REF,
            settings.CHECK_CHILD_LINKS,
            settings.REORDER,
            settings.CHECK_LEVELS,
            settings.PUBLISH_CHILD_LINKS,
            settings.CHECK_SUSPECT_LINKS,
            settings.CHECK_REVIEW_STATUS,
            settings.PUBLISH_BODY_LEVELS,
            settings.CACHE_DOCUMENTS,
            settings.CACHE_ITEMS,
            settings.CACHE_PATHS,
            settings.WARN_ALL,
            settings.ERROR_ALL,
            settings.SERVER_HOST,
            settings.SERVER_PORT,
        ) = self.backup
