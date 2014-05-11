#!/usr/bin/env python

"""Profiles a section of Doorstop."""

import sys

import doorstop


def main():
    """Process arguments."""
    root = sys.argv[-1] if len(sys.argv) > 1 else None
    run(root)


def run(root):
    """Profile tree validation."""
    tree = doorstop.build(root=root)
    print("project: {}".format(tree.document.root))
    print("tree: {}".format(tree))
    print("profiling issues...")
    for issue in tree.issues:
        print(issue)


if __name__ == '__main__':
    main()
