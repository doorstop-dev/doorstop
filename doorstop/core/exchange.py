#!/usr/bin/env python

"""
Doorstop import/export functionality.
"""

# pylint: disable=W0613


def import_csv(path, document):
    """Add items from a CSV file to an existing document."""
    raise NotImplementedError()


def import_tsv(path, document):
    """Add items from a CSV file to an existing document."""
    raise NotImplementedError()


def export_csv(document, path):
    """Output items from a document to a CSV file."""
    raise NotImplementedError()


def export_tsv(document, path):
    """Output items from a document to a CSV file."""
    raise NotImplementedError()
