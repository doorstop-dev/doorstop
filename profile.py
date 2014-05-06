#!/usr/bin/env python

"""Profiles a section of Doorstop."""

import doorstop

from profilehooks import profile


def main():
    """Profile tree validation."""
    print("profiling issues")
    tree = doorstop.build()
    print(profile(tree.issues))


if __name__ == '__main__':
    main()
