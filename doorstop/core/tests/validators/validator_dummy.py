# SPDX-License-Identifier: LGPL-3.0-only

from doorstop import DoorstopInfo


def item_validator(item):
    if item:
        yield DoorstopInfo("Loaded")
