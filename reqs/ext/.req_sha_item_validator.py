# SPDX-License-Identifier: LGPL-3.0-only
import os
import subprocess
from copy import copy
from random import random

from doorstop import DoorstopError, DoorstopInfo, DoorstopWarning


def item_validator(item):
    if getattr(item, "references") == None:
        return []

    for ref in item.references:
        if ref['sha'] != item._hash_reference(ref['path']):
            yield DoorstopWarning("Hash has changed and it was not reviewed properly")

        if 'modified' in ref['path']:
            temp_item = copy(item)
            current_value = item.is_reviewed()
            
            # Get repository root using cross-platform method
            try:
                repo_root = subprocess.check_output(
                    ["git", "rev-parse", "--show-toplevel"],
                    text=True,
                    stderr=subprocess.DEVNULL
                ).strip()
            except subprocess.CalledProcessError:
                # Fallback if not in git repo
                repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            
            test_file = os.path.join(repo_root, "reqs", "ext", "test-modified.file")
            
            # Write test content using Python file operations (cross-platform)
            with open(test_file, 'w') as f:
                f.write('1111\n')
            
            temp_item.review()
            next_value = item.is_reviewed()
            
            # Write different content
            with open(test_file, 'w') as f:
                f.write('0000\n')

            yield DoorstopWarning(
                f"This is a demonstration of a validator per folder identifying a external ref modified "
                f"without a proper review current SHA {current_value} modified SHA {next_value}. "
                f"Result: {next_value == current_value}"
            )