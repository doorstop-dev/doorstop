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
from doorstop.core.types import ID


_DOCUMENTS = []  # cache of unplaced documents


def from_file(path, document, ext=None, **kwargs):
    """Import items from an exported file.

    @param path: input file location
    @param document: document to import items
    @param ext: file extension to override input path's extension

    @raise DoorstopError: for unknown file formats

    @return: document with imported items

    """
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


def import_tsv(path, document, delimiter='\t'):
    """Import items from a TSV export to a document.

    @param path: input file location
    @param document: document to import items

    """
    import_csv(path, document, delimiter=delimiter)


def import_csv(path, document, delimiter=','):
    """Import items from a CSV export to a document.

    @param path: input file location
    @param document: document to import items

    """
    rows = []

    with open(path) as stream:
        reader = csv.reader(stream, delimiter=delimiter)
        for row in reader:
            rows.append(row)

    add_doorstop_items(rows[1:], rows[0], document, all_strings=True)


def import_xlsx(path, document):
    """Import items from an XLSX export to a document.

    @param path: input file location
    @param document: document to import items

    """
    # basically the first row
    header = []
    data = []

    logging.debug("opening {}...".format(path))
    workbook = load_workbook(path)
    # assuming that the desired worksheet is the wanted one
    worksheet = workbook.active

    # last cell is the last column with info combined with the last row with info
    # last cell may actually have nothing in it
    last_cell = openpyxl.cell.get_column_letter(worksheet.get_highest_column()) + str(worksheet.get_highest_row())

    for i, row in enumerate(worksheet.range('A1:%s' % last_cell)):
        data.append([])
        for j, cell in enumerate(row):
            if not i:
                # first row. just header info
                header.append(str(cell.value).lower())
            else:
                # convert to text for processing
                data[i].append(cell.value)
    add_doorstop_items(data, header, document)



def add_doorstop_items(value_array, header_array, document, all_strings=False):
    """Conversion function for multiple formats.

    @param value_array is the rows of data to be added as doorstop items (array of arrays)
    @param header_array is the mapping of columns to doorstop attributes
    @param document: document to import items

    """
    # Load the current tree
    prefix = None

    for row in value_array:
        attributes = {}
        id_text = ""
        for j, cell in enumerate(row):
            # not first row, this should be all the actual data
            # gather all attribute data based on column headers
            if cell:
                if header_array[j] == "id":
                    id_text = cell
                elif 'links' == header_array[j]:
                    # split links into a list
                    attributes[header_array[j]] = re.split(r'[\s;,]+', cell)
                elif ('active' == header_array[j] or 'normative' == header_array[j] or 'derived' == header_array[j]) and all_strings:
                    # all cells are strings, but doorstop expects some things to be boolean. Convert those here.
                    # csv reader returns a list of strings
                    # TODO: is there a better way of doing this?
                    attributes[header_array[j]] = (cell == "True")
                else:
                    attributes[header_array[j]] = cell
        # guard against empty rows
        if id_text and row:
            # all columns parsed for a given row
            # create the requirement based on accumulated attributes
            identifier = ID(id_text)

            # TODO: figure out a better way to determine the item's document from an exported file
            # TODO: get rid of the following if statement. Currently in place to show how deleting a req and re-adding it fails.
            if not prefix:
                prefix = identifier.prefix
            # prefix = re.search("[a-zA-Z]+", id_text).group(0)
            req = id_text

            # Delete the old item
            try:
                item = document.find_item(req)
                # TODO: maybe compare data with attributes first to see if anything changed,
                #       no point in deleting if nothing changed
            except DoorstopError:
                logging.debug("not yet an item: {}".format(req))
            else:
                logging.debug("deleting old item: {}".format(req))
                item.delete()

            # Import the item
            try:
                add_item(document.prefix, req, attributes, document=document)
            except DoorstopError as exc:
                logging.warning(exc)


# Mapping from file extension to file reader
FORMAT_FILE = {'.xlsx': import_xlsx, '.csv': import_csv, '.tsv': import_tsv}


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
