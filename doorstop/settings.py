# SPDX-License-Identifier: LGPL-3.0-only

"""Settings for the Doorstop package."""

import logging

# Logging settings
DEFAULT_LOGGING_FORMAT = "%(message)s"
LEVELED_LOGGING_FORMAT = "%(levelname)s: %(message)s"
VERBOSE_LOGGING_FORMAT = "[%(levelname)-8s] %(message)s"
VERBOSE2_LOGGING_FORMAT = "[%(levelname)-8s] (%(name)s @%(lineno)4d) %(message)s"
QUIET_LOGGING_LEVEL = logging.WARNING
TIMED_LOGGING_FORMAT = "%(asctime)s" + ' ' + VERBOSE_LOGGING_FORMAT
DEFAULT_LOGGING_LEVEL = logging.WARNING
VERBOSE_LOGGING_LEVEL = logging.INFO
VERBOSE2_LOGGING_LEVEL = logging.DEBUG
VERBOSE3_LOGGING_LEVEL = logging.DEBUG - 1

# Value constants
SEP_CHARS = "-_."  # valid prefix/number separators
SKIP_EXTS = ['.yml', '.csv', '.tsv']  # extensions skipped in reference search
RESERVED_WORDS = ['all']  # keywords that cannot be used for prefixes
PLACEHOLDER = "..."  # placeholder for new item UIDs on export/import
PLACEHOLDER_COUNT = 1  # number of placeholders to include on export

# Formatting settings
MAX_LINE_LENGTH = 79  # line length to trigger multiline on extended attributes

# Validation settings
REFORMAT = True  # reformat item files during validation
REORDER = False  # reorder document levels during validation
CHECK_LEVELS = True  # validate document levels during validation
CHECK_REF = True  # validate external file references
CHECK_CHILD_LINKS = True  # validate reverse links
CHECK_CHILD_LINKS_STRICT = False  # require child (reverse) links from every document
CHECK_SUSPECT_LINKS = True  # check stamps on links
CHECK_REVIEW_STATUS = True  # check stamps on items
WARN_ALL = False  # display info-level issues as warnings
ERROR_ALL = False  # display warning-level issues as errors

# Review settings
REVIEW_NEW_ITEMS = True  # automatically review new items during validation

# Stamping settings
STAMP_NEW_LINKS = True  # automatically stamp links upon creation

# Publishing settings
PUBLISH_CHILD_LINKS = True  # include child links when publishing
PUBLISH_BODY_LEVELS = True  # include levels on non-header items
PUBLISH_HEADING_LEVELS = True  # include levels on header items
ENABLE_HEADERS = True  # use headers if defined

# Version control settings
ADDREMOVE_FILES = True  # automatically add/remove new/changed files

# Caching settings
CACHE_ITEMS = True  # cache items in documents and trees
CACHE_DOCUMENTS = True  # cache documents in trees
CACHE_PATHS = True  # cache file/directory paths and contents

# Server settings
SERVER_HOST = None  # '' = server not specified, None = no server in use
SERVER_PORT = 7867
