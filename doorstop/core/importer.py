"""Functions to import exiting documents and items."""

import os
import logging
import re
import csv

import openpyxl
from openpyxl import load_workbook

from doorstop.common import DoorstopError
from doorstop.core.document import Document
from doorstop.core.item import Item
from doorstop.core.builder import _get_tree


_DOCUMENTS = []  # cache of unplaced documents


def import_file(path, document, ext=None, **kwargs):
    """Import items from an exported file.

    @param path: input file location
    @param document: document to import items
    @param ext: file extension to override input path's extension

    @raise DoorstopError: for unknown file formats

    @return: document with imported items

    """
    logging.info("importing {} to {}...".format(path, document))
    ext = ext or os.path.splitext(path)[-1]
    func = check(ext)
    func(path, document, **kwargs)


def new_document(prefix, path, parent=None, tree=None):
    """Create a Doorstop document from existing document information.

    @param prefix: existing document's prefix (for new items)
    @param path: new directory path to store this document's items
    @param parent: parent document's prefix (if one will exist)
    @param document: explicit tree to add the document

    @return: imported Document

    """
    if not tree:
        tree = _get_tree()

    # Attempt to create a document with the given parent
    logging.info("importing document '{}'...".format(prefix))
    try:
        document = tree.new_document(path, prefix, parent=parent)
    except DoorstopError as exc:
        if not parent:
            raise exc from None

        # Create the document despite an unavailable parent
        document = Document.new(tree,
                                path, tree.root, prefix,
                                parent=parent)
        logging.warning(exc)
        _DOCUMENTS.append(document)

    # TODO: attempt to place unplaced documents?

    # Cache and return the document
    logging.info("imported: {}".format(document))
    tree._document_cache[document.prefix] = document  # pylint: disable=W0212
    return document


def add_item(prefix, identifier, attrs=None, document=None):
    """Create a Doorstop document from existing document information.

    @param prefix: previously imported document's prefix
    @param identifier: existing item's unique ID
    @param attrs: dictionary of Doorstop and custom attributes
    @param document: explicit document to add the item

    @return: imported Item

    """
    if document:
        # Get an explicit tree
        tree = document.tree
        assert tree  # tree should be set internally
    else:
        # Get an implicit tree and document
        tree = _get_tree()
        document = tree.find_document(prefix)

    logging.info("importing item '{}'...".format(identifier))
    item = Item.new(tree, document,
                    document.path, document.root, identifier,
                    auto=False)
    for key, value in (attrs or {}).items():
        item.set(key, value)
    item.save()

    # Cache and return the item
    logging.info("imported: {}".format(item))
    document._items.append(item)  # pylint: disable=W0212
    tree._item_cache[item.id] = item  # pylint: disable=W0212
    return item


def _file_csv(path, document, delimiter=','):
    """Import items from a CSV export to a document.

    @param path: input file location
    @param document: document to import items

    """
    rows = []

    # Parse the file
    logging.info("reading rows in {}...".format(path))
    with open(path, 'r') as stream:
        reader = csv.reader(stream, delimiter=delimiter)
        for row in reader:
            rows.append(row)

    # Extract header and data rows
    header = rows[0]
    data = rows[1:]

    # Import items from the rows
    _itemize(header, data, document, all_strings=True)


def _file_tsv(path, document):
    """Import items from a TSV export to a document.

    @param path: input file location
    @param document: document to import items

    """
    _file_csv(path, document, delimiter='\t')


def _file_xlsx(path, document):
    """Import items from an XLSX export to a document.

    @param path: input file location
    @param document: document to import items

    """
    # TODO: openpyxl has false positives with pylint
    # pylint: disable=E1101,E1120,E1123

    header = []
    data = []

    # Parse the file
    logging.debug("reading rows in {}...".format(path))
    workbook = load_workbook(path)
    worksheet = workbook.active

    # Locate the bottom right cell in the workbook that contains cell info
    _highest_column = worksheet.get_highest_column()
    _highest_letter = openpyxl.cell.get_column_letter(_highest_column)
    _highest_row = worksheet.get_highest_row()
    last_cell = _highest_letter + str(_highest_row)

    # Extract header and data rows
    for i, row in enumerate(worksheet.range('A1:%s' % last_cell)):
        row2 = []
        for cell in row:
            if not i:
                # first row. just header info
                header.append(str(cell.value).lower())
            else:
                # convert to text for processing
                row2.append(cell.value)
        if i:
            data.append(row2)

    # Import items from the rows
    _itemize(header, data, document)


def _itemize(header_array, value_array, document, all_strings=False):
    """Conversion function for multiple formats.

    @param header_array is the mapping of columns to doorstop attributes
    @param value_array is the rows of data to be added as doorstop items (array of arrays)
    @param document: document to import items

    """
    logging.info("converting rows to items...")
    logging.debug("header: {}".format(header_array))
    for row in value_array:
        logging.debug("datum: {}".format(row))
        attrs = {}
        identifier = ""
        for j, cell in enumerate(row):
            # not first row, this should be all the actual data
            # gather all attribute data based on column headers
            if cell:
                if header_array[j] == "id":
                    identifier = cell
                elif 'links' == header_array[j]:
                    # split links into a list
                    attrs[header_array[j]] = re.split(r'[\s;,]+', cell)
                elif ('active' == header_array[j] or 'normative' == header_array[j] or 'derived' == header_array[j]) and all_strings:  # pragma: no cover
                    # all cells are strings, but doorstop expects some things to be boolean. Convert those here.
                    # csv reader returns a list of strings
                    # TODO: is there a better way of doing this?
                    attrs[header_array[j]] = (cell == "True")
                else:
                    attrs[header_array[j]] = cell

        # Convert the row to an item
        if identifier and row:

            # Delete the old item
            try:
                item = document.find_item(identifier)
                # TODO: maybe compare data with attributes first to see if anything changed,
                #       no point in deleting if nothing changed
            except DoorstopError:
                logging.debug("not yet an item: {}".format(identifier))
            else:
                logging.debug("deleting old item: {}".format(identifier))
                item.delete()

            # Import the item
            try:
                add_item(document.prefix, identifier,
                         attrs=attrs, document=document)
            except DoorstopError as exc:
                logging.warning(exc)


# Mapping from file extension to file reader
FORMAT_FILE = {'.csv': _file_csv,
               '.tsv': _file_tsv,
               '.xlsx': _file_xlsx}


def check(ext):
    """Confirm an extension is supported for import.

    @raise DoorstopError: for unknown formats

    @return: file importer if available

    """
    exts = ', '.join(ext for ext in FORMAT_FILE)
    msg = "unknown import format: {} (options: {})".format(ext or None, exts)
    exc = DoorstopError(msg)
    try:
        func = FORMAT_FILE[ext]
    except KeyError:
        raise exc from None
    else:
        logging.debug("found file reader for: {}".format(ext))
        return func
