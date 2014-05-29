"""Functions to export documents and items."""

import os
import csv
import datetime
import logging

import yaml
import openpyxl

from doorstop.common import DoorstopError
from doorstop.core.types import iter_items


def export(obj, path, ext=None, **kwargs):
    """Export a document to a given format.

    @param obj: Item, list of Items, or Document to export
    @param path: output file location with desired extension
    @param ext: file extension to override output path's extension

    @raise DoorstopError: for unknown file formats

    """
    ext = ext or os.path.splitext(path)[-1]
    if ext in FORMAT:

        # Create output directory
        dirpath = os.path.dirname(path)
        if dirpath and not os.path.isdir(dirpath):
            logging.info("creating directory {}...".format(dirpath))
            os.makedirs(dirpath)

        # Create output file
        logging.info("creating file {}...".format(path))
        if ext in FORMAT_LINES:
            with open(path, 'w') as outfile:  # pragma: no cover (integration test)
                for line in lines(obj, ext, **kwargs):
                    outfile.write(line + '\n')
        else:
            create(obj, path, ext, **kwargs)
    else:
        raise DoorstopError("unknown export format: {}".format(ext))


def lines(obj, ext='.yml', **kwargs):
    """Yield lines for an export in the specified format.

    @param obj: Item, list of Items, or Document to export
    @param ext: file extension to specify the output format

    @raise DoorstopError: for unknown file formats

    """
    if ext in FORMAT_LINES:
        logging.debug("yielding {} as lines of {}...".format(obj, ext))
        yield from FORMAT_LINES[ext](obj, **kwargs)
    else:
        raise DoorstopError("unknown export format: {}".format(ext))


def create(obj, path, ext=None, **kwargs):
    """Create a file object for an export in the specified format.

    @param obj: Item, list of Items, or Document to export
    @param path: output file location with desired extension
    @param ext: file extension to override output path's extension

    @raise DoorstopError: for unknown file formats

    """
    ext = ext or os.path.splitext(path)[-1]
    if ext in FORMAT_FILE:
        logging.debug("converting {} to file format {}...".format(obj, ext))
        return FORMAT_FILE[ext](obj, path, **kwargs)
    else:
        raise DoorstopError("unknown export format: {}".format(ext))


def lines_yaml(obj):
    """Yield lines for a YAML export.

    @param obj: Item, list of Items, or Document to export

    @return: iterator of lines of text

    """
    for item in iter_items(obj):

        data = {str(item.id): item.data}
        text = yaml.dump(data)
        yield text


def tabulate(obj):
    """Yield lines of header/data for tabular export.

    @param obj: Item, list of Items, or Document to export

    @return: iterator of rows of data

    """
    yield_header = True

    for item in iter_items(obj):

        data = item.data

        # Yield header
        if yield_header:
            header = ['level', 'text', 'ref', 'links']
            for value in sorted(data.keys()):
                if value not in header:
                    header.append(value)
            yield ['id'] + header
            yield_header = False

        # Yield row
        row = [item.id]
        for key in header:
            value = data.get(key)
            if isinstance(value, list):
                # separate lists with commas
                row.append(', '.join(str(p) for p in value))
            else:
                row.append(value)
        yield row


def file_csv(obj, path, delimiter=','):
    """Create a CSV file at the given path.

    @param obj: Item, list of Items, or Document to export

    @return: path of created file

    """
    with open(path, 'w', newline='') as stream:
        writer = csv.writer(stream, delimiter=delimiter)
        for row in tabulate(obj):
            writer.writerow(row)
    return path


def file_tsv(obj, path):
    """Create a TSV file at the given path.

    @param obj: Item, list of Items, or Document to export

    @return: path of created file

    """
    return file_csv(obj, path, delimiter='\t')


def file_xlsx(obj, path):  # pragma: no cover (not implemented)
    """Create an XLSX file at the given path.

    @param obj: Item, list of Items, or Document to export

    @return: path of created file

    """
    # Create a new workbook
    workbook = openpyxl.Workbook()  # pylint: disable=E1102
    worksheet = workbook.active

    # Populate cells
    for row, data in enumerate(tabulate(obj), start=1):
        for col_idx, value in enumerate(data, start=1):
            col = openpyxl.cell.get_column_letter(col_idx)  # pylint: disable=E1101
            # compatible Excel types:
            # http://pythonhosted.org/openpyxl/api.html#openpyxl.cell.Cell.value
            if not isinstance(value, (int, float, str, datetime.datetime)):
                value = str(value)
            worksheet.cell('%s%s' % (col, row)).value = value

    # Save the workbook
    workbook.save(path)
    return path


# Mapping from file extension to lines generator
FORMAT_LINES = {'.yml': lines_yaml}
# Mapping from file extension to file generator
FORMAT_FILE = {'.csv': file_csv,
               '.tsv': file_tsv,
               '.xlsx': file_xlsx}
# Union of format dictionaries
FORMAT = dict(list(FORMAT_LINES.items()) + list(FORMAT_FILE.items()))
