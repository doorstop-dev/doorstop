"""Functions to import exiting documents and items."""

import os
import logging
import re
import openpyxl
from openpyxl import load_workbook

from doorstop.common import DoorstopError
from doorstop.core.document import Document
from doorstop.core.item import Item
from doorstop.core.builder import _get_tree


_DOCUMENTS = []  # cache of unplaced documents


def from_file(path, ext=None, **kwargs):
    """Import items from an exported file.

    @param path: input file location
    @param ext: file extension to override input path's extension

    @raise DoorstopError: for unknown file formats

    """
    ext = ext or os.path.splitext(path)[-1]
    func = check(ext)
    func(path, **kwargs)


def new_document(prefix, path, parent=None):
    """Create a Doorstop document from existing document information.

    @param prefix: existing document's prefix (for new items)
    @param path: new directory path to store this document's items
    @param parent: parent document's prefix (if one will exist)

    @return: imported Document

    """
    # Load the current tree
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


def add_item(prefix, identifier, attrs=None):
    """Create a Doorstop document from existing document information.

    @param prefix: previously imported document's prefix
    @param identifier: existing item's unique ID
    @param attrs: dictionary of Doorstop and custom attributes

    @return: imported Item

    """
    # Load the current tree
    tree = _get_tree()

    # Get the specified document
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


def import_xlsx(file_path):
    """Import an xlsx document to doorstop.

    Excel format should be in the exported format
    where the first row is the doorstop attributes, one of which is the ID
    """
    # Load the current tree
    tree = _get_tree()

    # basically the first row
    col_headers = []
    # which column is the id column
    id_col = 0

    workbook = load_workbook(file_path)
    # assuming that the desired worksheet is the wanted one
    worksheet = workbook.active

    # last cell is the last column with info combined with the last row with info
    # last cell may actually have nothing in it
    last_cell = openpyxl.cell.get_column_letter(worksheet.get_highest_column()) + str(worksheet.get_highest_row())

    for i, row in enumerate(worksheet.range('A1:%s' % last_cell)):
        attributes = {}
        for j, cell in enumerate(row):
            if not i:
                # first row. just header info
                # determine which column is the ID
                col_headers.append(cell.value)
                if cell.value.lower() == 'id':
                    id_col = j
            else:
                # not first row, this should be all the actual data
                # gather all attribute data based on column headers
                if j != id_col and cell.value is not None:
                    if 'links' == col_headers[j]:
                        # split links into a list
                        # todo: this regex could change based on project req format
                        attributes[col_headers[j]] = re.findall('[a-zA-Z0-9]+', cell.value)
                    else:
                        attributes[col_headers[j]] = cell.value
        if i:
            # all columns parsed for a given row
            # create the requirement based on accumulated attributes
            # todo: this regex could change based on project req format
            prefix = re.search("[a-zA-Z]+", str(row[id_col].value)).group(0)
            req = row[id_col].value

            try:
                # if the item exists, delete and re-create from excel data
                # todo: maybe compare data with attributes first to see if anything changed
                item = tree.find_item(req)
                item.delete()
                add_item(prefix, req, attributes)
            except DoorstopError:
                # item doesn't exist yet
                if prefix in [doc.prefix for doc in tree.documents]:
                    add_item(prefix, req, attributes)
                else:
                    new_document(prefix, tree.root + os.sep + prefix)
                    add_item(prefix, req, attributes)


# Mapping from file extension to file reader
FORMAT_FILE = {'.xlsx': import_xlsx}


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
