# SPDX-License-Identifier: LGPL-3.0-only

from doorstop import DoorstopError, DoorstopInfo, DoorstopWarning


def item_validator(item):
    if item:
        yield DoorstopInfo("Loaded")
