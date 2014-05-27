"""Functions to export documents and items."""

import os
import logging

import yaml
import csv

from doorstop.common import DoorstopError
from doorstop.core.publisher import _get_items


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
        if not os.path.isdir(dirpath):
            logging.info("creating {}...".format(dirpath))
            os.makedirs(dirpath)

        # Publish report
        logging.info("publishing {}...".format(path))
        if ext in FORMAT_LINES:
            with open(path, 'w') as outfile:  # pragma: no cover (integration test)
                for line in lines(obj, ext, **kwargs):
                    outfile.write(line + '\n')
        else:
            create(obj, path, ext, **kwargs)
    else:
        raise DoorstopError("unknown format: {}".format(ext))


def lines(obj, ext='.yml', **kwargs):
    """Yield lines for an export in the specified format.

    @param obj: Item, list of Items, or Document to publish
    @param ext: file extension to specify the output format

    @raise DoorstopError: for unknown file formats

    """
    if ext in FORMAT_LINES:
        logging.debug("yielding {} as lines of {}...".format(obj, ext))
        yield from FORMAT_LINES[ext](obj, **kwargs)
    else:
        raise DoorstopError("unknown format: {}".format(ext))


def create(obj, path, ext=None, **kwargs):
    """Create a file object for an export in the specified format.

    @param obj: Item, list of Items, or Document to publish
    @param path: output file location with desired extension
    @param ext: file extension to override output path's extension

    @raise DoorstopError: for unknown file formats

    """
    ext = ext or os.path.splitext(path)[-1]
    if ext in FORMAT_FILE:
        logging.debug("converting {} to file format {}...".format(obj, ext))
        return FORMAT_FILE[ext](obj, path, **kwargs)
    else:
        raise DoorstopError("unknown format: {}".format(ext))


def lines_yaml(obj):
    """Yield lines for a YAML export.

    @param obj: Item, list of Items, or Document to export

    @return: iterator of lines of text

    """
    for item in _get_items(obj):

        data = {str(item.id): item.data}
        text = yaml.dump(data)
        yield text


def tabulate(obj):
    """Yield lines of header/data for tabular export.

    @param obj: Item, list of Items, or Document to export

    @return: iterator of rows of data

    """
    yield_header = True

    for item in _get_items(obj):

        data = item.data

        if yield_header:
            yield list(data.keys())
            yield_header = False

        yield list(data.values())


def file_csv(obj, path):
    """Create a CSV file at the given path.

    @param obj: Item, list of Items, or Document to export

    @return: path of created file

    """
    with open(path, 'w') as stream:
        writer = csv.writer(stream)
        for row in tabulate(obj):
            writer.writerow(row)


def file_xlsx(*args, **kwargs):  # pragma: no cover (not implemented)
    raise NotImplementedError


# Mapping from file extension to lines generator
FORMAT_LINES = {'.yml': lines_yaml}
# Mapping from file extension to file generator
FORMAT_FILE = {'.csv': file_csv,
               '.xlsx': file_xlsx}
# Union of format dictionaries
FORMAT = dict(list(FORMAT_LINES.items()) + list(FORMAT_FILE.items()))
