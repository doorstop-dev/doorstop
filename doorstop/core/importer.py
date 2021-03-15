# SPDX-License-Identifier: LGPL-3.0-only

"""Functions to import exiting documents and items."""

import csv
import os
import re
import warnings
from typing import Any

import openpyxl

from doorstop import common, settings
from doorstop.common import DoorstopError
from doorstop.core.builder import _get_tree
from doorstop.core.document import Document
from doorstop.core.item import Item
from doorstop.core.types import UID

import portableqda,pathlib


LIST_SEP_RE = re.compile(r"[\s;,]+")  # regex to split list strings into parts

_documents = []  # cache of unplaced documents

log = common.logger(__name__)


def import_file(path, document, ext=None, mapping=None, **kwargs):
    """Import items from an exported file.

    :param path: input file location
    :param document: document to import items
    :param ext: file extension to override input path's extension
    :param mapping: dictionary mapping custom to standard attribute names

    :raise DoorstopError: for unknown file formats

    :return: document with imported items

    """
    log.info("importing {} into {}...".format(path, document))
    ext = ext or os.path.splitext(path)[-1]
    func = check(ext)
    func(path, document, mapping=mapping, **kwargs)


def create_document(prefix, path, parent=None, tree=None):
    """Create a Doorstop document from existing document information.

    :param prefix: existing document's prefix (for new items)
    :param path: new directory path to store this document's items
    :param parent: parent document's prefix (if one will exist)
    :param tree: explicit tree to add the document

    :return: imported Document

    """
    if not tree:
        tree = _get_tree()

    # Attempt to create a document with the given parent
    log.info("importing document '{}'...".format(prefix))
    try:
        document = tree.create_document(path, prefix, parent=parent)
    except DoorstopError as exc:
        if not parent:
            raise exc from None  # pylint: disable=raising-bad-type

        # Create the document despite an unavailable parent
        document = Document.new(tree, path, tree.root, prefix, parent=parent)
        log.warning(exc)
        _documents.append(document)

    # TODO: attempt to place unplaced documents?

    log.info("imported: {}".format(document))
    return document


def add_item(prefix, uid, attrs=None, document=None, request_next_number=None):
    """Create a Doorstop document from existing document information.

    :param prefix: previously imported document's prefix
    :param uid: existing item's UID
    :param attrs: dictionary of Doorstop and custom attributes
    :param document: explicit document to add the item
    :param request_next_number: server method to get a document's next number

    :return: imported Item

    """
    if document:
        # Get an explicit tree
        tree = document.tree
        assert tree  # tree should be set internally
    else:
        # Get an implicit tree and document
        tree = _get_tree(request_next_number=request_next_number)
        document = tree.find_document(prefix)

    # Add an item using the specified UID
    log.info("importing item '{}'...".format(uid))
    item = Item.new(tree, document, document.path, document.root, uid, auto=False)
    for key, value in (attrs or {}).items():
        item.set(key, value)
    item.save()

    log.info("imported: {}".format(item))
    return item


def _file_yml(path, document, **_):
    """Import items from a YAML export to a document.

    :param path: input file location
    :param document: document to import items

    """
    # Parse the file
    log.info("reading items in {}...".format(path))
    text = common.read_text(path)
    # Load the YAML data
    data = common.load_yaml(text, path)
    # Add items
    for uid, attrs in data.items():
        try:
            item = document.find_item(uid)
        except DoorstopError:
            pass  # no matching item
        else:
            item.delete()
        add_item(document.prefix, uid, attrs=attrs, document=document)

def _onefile_qpdx(path):
    raise NotImplementedError("importing QDPX project not yet supported")


def _onefile_qdc(path, rootDoc, **_):
    """Import items from a QDC file to a tree, to create a new Tree follow these steps:

    ```bash
    #assuming that PRJ is the root Document
    cd baseDirectory
    git init
    doorstop create PRJ PRJ #
    doorstop  import -b codebook.qdc PRJ
    ```


    :param path: input file location
    :param document: document to import items

    """
    import portableqda
    portableqda.log = log

    try:
        CATEGORY_SEP = str(portableqda.CATEGORY_SEP)
    except Exception:
        CATEGORY_SEP = "::"
    # Parse the file
    log.info("reading items in {}...".format(path))
    codebook = portableqda.codebookCls(output=path.replace(".qdc","-diff.qdc"))
    #
    # read QDC file and find Codes and Sets tag
    #
    codebook.readQdcFile(input=path)
    #codebook_xml=portableqda.etree.tostring(codebook.tree,pretty_print=True).decode(encoding="utf8")
    sets=None
    codes = None
    root = codebook.tree.getroot()
    if root is not None:
        for elm in list(root):
            #print(elm.attrib["name"])
            tag=elm.tag.split("}")[-1] #crop namespace
            if tag == portableqda.setCls.TAG+"s":
                sets=elm
            if tag == portableqda.codeCls.TAG + "s":
                codes = elm

    if sets is None or codes is None:
        raise ValueError("malformed QDC file: {} is missing 'Codes' tag or 'Sets' tag as second level elements")

    #
    # iterate sets, create one Document for each element (split the name using portableqda.CATEGRORY_SEP)
    #
    for elm in list(sets):
        #print(elm.attrib)
        name=elm.attrib["name"]
        path=name.split(portableqda.CATEGORY_SEP)
        parent = None
        for level,doc in enumerate(path):
            if level == 0:
                if str(rootDoc.prefix) == doc:
                        parent = rootDoc
                        #print(parent)
                else:
                    raise DoorstopError(f"all sets in codebook must have names that are absolute paths to docs, starting with {rootDoc} (like {rootDoc}{CATEGORY_SEP}ancestor{CATEGORY_SEP}child, docs 'ancestor' and 'child' will be created )")
            else:
                try:
                    parent = rootDoc.tree.find_document(doc)
                except common.DoorstopError as e:
                    #raise ("root doc {} not found".format(rootDoc))
                    # doc didn't existe, creating one
                    newDoc=rootDoc.tree.create_document(
                        str(pathlib.Path(parent.path)/doc) ,
                        doc,
                        parent=parent.prefix)#,
                        #digits=args.digits,
                        #sep=args.separator)
                    newDoc.extended_reviewed.append("guid")
                    newDoc._attribute_defaults = {"guid": None}
                    newDoc.save()
                    log.info(f"bashScript: doorstop create {doc} --parent {parent.prefix} #add items with doorstop add -d defaults.yml {doc} for GUID attribute")
                    parent=newDoc
                except Exception:
                    raise
    #
    # iterate memberCodes in sets, create corresponding Items
    #
    # not yet implemented



    data=None



def _file_csv(path, document, delimiter=',', mapping=None):
    """Import items from a CSV export to a document.

    :param path: input file location
    :param document: document to import items
    :param delimiter: CSV field delimiter
    :param mapping: dictionary mapping custom to standard attribute names

    """
    rows = []

    # Parse the file
    log.info("reading rows in {}...".format(path))
    with open(path, 'r', encoding='utf-8') as stream:
        reader = csv.reader(stream, delimiter=delimiter)
        for _row in reader:
            row = []
            value: Any
            for value in _row:
                # convert string booleans
                if isinstance(value, str):
                    if value.lower() == 'true':
                        value = True
                    elif value.lower() == 'false':
                        value = False
                row.append(value)
            rows.append(row)

    # Extract header and data rows
    header = rows[0]
    data = rows[1:]

    # Import items from the rows
    _itemize(header, data, document, mapping=mapping)


def _file_tsv(path, document, mapping=None):
    """Import items from a TSV export to a document.

    :param path: input file location
    :param document: document to import items
    :param mapping: dictionary mapping custom to standard attribute names

    """
    _file_csv(path, document, delimiter='\t', mapping=mapping)


def _file_xlsx(path, document, mapping=None):
    """Import items from an XLSX export to a document.

    :param path: input file location
    :param document: document to import items
    :param mapping: dictionary mapping custom to standard attribute names

    """
    header = []
    data = []

    # Parse the file
    log.debug("reading rows in {}...".format(path))
    workbook = openpyxl.load_workbook(path, data_only=True)
    worksheet = workbook.active

    index = 0

    # Extract header and data rows
    for index, row in enumerate(worksheet.iter_rows()):
        row2 = []
        for cell in row:
            if index == 0:
                header.append(cell.value)
            else:
                row2.append(cell.value)
        if index:
            data.append(row2)

    # Warn about workbooks that may be sized incorrectly
    if index >= 2 ** 20 - 1:
        msg = "workbook contains the maximum number of rows"
        warnings.warn(msg, Warning)

    # Import items from the rows
    _itemize(header, data, document, mapping=mapping)


def _itemize(header, data, document, mapping=None):
    """Conversion function for multiple formats.

    :param header: list of columns names
    :param data: list of lists of row values
    :param document: document to import items
    :param mapping: dictionary mapping custom to standard attribute names

    """
    log.info("converting rows to items...")
    log.debug("header: {}".format(header))
    for row in data:
        log.debug("row: {}".format(row))

        # Parse item attributes
        attrs = {}
        uid = None
        for index, value in enumerate(row):

            # Key lookup
            key = str(header[index]).lower().strip() if header[index] else ''
            if not key:
                continue

            # Map key to custom attributes names
            for custom, standard in (mapping or {}).items():
                if key == custom.lower():
                    msg = "mapped: '{}' => '{}'".format(key, standard)
                    log.debug(msg)
                    key = standard
                    break

            # Convert values for particular keys
            if key in ('uid', 'id'):  # 'id' for backwards compatibility
                uid = value
            elif key == 'links':
                # split links into a list
                attrs[key] = _split_list(value)

            elif key == 'references' and (value is not None):
                ref_items = value.split('\n')
                if ref_items[0] != '':
                    ref = []
                    for ref_item in ref_items:
                        ref_item_components = ref_item.split(',')

                        ref_type = ref_item_components[0].split(':')[1]
                        ref_path = ref_item_components[1].split(':')[1]

                        ref_dict = {'type': ref_type, 'path': ref_path}
                        if len(ref_item_components) == 3:
                            ref_keyword = ref_item_components[2].split(':')[1]
                            ref_dict['keyword'] = ref_keyword

                        ref.append(ref_dict)

                    attrs[key] = ref
            elif key == 'active':
                # require explicit disabling
                attrs['active'] = value is not False
            else:
                attrs[key] = value

        # Get the next UID if the row is a new item
        if attrs.get('text') and uid in (None, '', settings.PLACEHOLDER):
            uid = UID(
                document.prefix, document.sep, document.next_number, document.digits
            )

        # Convert the row to an item
        if uid and uid != settings.PLACEHOLDER:

            # Delete the old item
            try:
                item = document.find_item(uid)
            except DoorstopError:
                log.debug("not yet an item: {}".format(uid))
            else:
                log.debug("deleting old item: {}".format(uid))
                item.delete()

            # Import the item
            try:
                item = add_item(document.prefix, uid, attrs=attrs, document=document)
            except DoorstopError as exc:
                log.warning(exc)


def _split_list(value):
    """Split a string list into parts."""
    if value:
        return [p for p in LIST_SEP_RE.split(value) if p]
    else:
        return []


# Mapping from file extension to file reader
FORMAT_FILE = {
    '.yml': _file_yml,
    '.csv': _file_csv,
    '.tsv': _file_tsv,
    '.xlsx': _file_xlsx,
    '.qdc': _onefile_qdc,
    '.qpdx': _onefile_qpdx,
}


def check(ext):
    """Confirm an extension is supported for import.

    :raise DoorstopError: for unknown formats

    :return: file importer if available

    """
    exts = ', '.join(ext for ext in FORMAT_FILE)
    msg = "unknown import format: {} (options: {})".format(ext or None, exts)
    exc = DoorstopError(msg)
    try:
        func = FORMAT_FILE[ext]
    except KeyError:
        raise exc from None
    else:
        log.debug("found file reader for: {}".format(ext))
        return func
