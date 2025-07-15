# SPDX-License-Identifier: LGPL-3.0-only
from doorstop import DoorstopWarning
from subprocess import check_output
from copy import copy


def item_validator(item):
    if getattr(item, "references") is None:
        return []

    for ref in item.references:
        if ref['sha'] != item._hash_reference(ref['path']):
            yield DoorstopWarning("Hash has changed and it was not reviewed properly")

        if 'modified' in ref['path']:
            temp_item = copy(item)
            current_value = item.is_reviewed()
            check_output(
                "echo '1111' > $(git rev-parse --show-toplevel)/reqs/ext/test-modified.file", shell=True)
            temp_item.review()
            next_value = item.is_reviewed()
            check_output(
                "echo '0000' > $(git rev-parse --show-toplevel)/reqs/ext/test-modified.file", shell=True)

            yield DoorstopWarning(f"""This is a demonstration of a validator per folder identifying a external ref modified
                      without a proper review current SHA {current_value} modified SHA {next_value }.
                      Result: { next_value == current_value} """)
