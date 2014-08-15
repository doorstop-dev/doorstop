#!/usr/bin/env python

"""REST server to display content and reserve item numbers."""

import os
from collections import defaultdict
import webbrowser
import argparse
import logging

import bottle
from bottle import get, post, request

from doorstop import common, build, publisher
from doorstop.common import HelpFormatter
from doorstop.server import utilities
from doorstop import settings

log = common.logger(__name__)

tree = None  # set in `run`, read in the route functions
numbers = defaultdict(int)  # cache of next document numbers


def main(args=None):
    """Process command-line arguments and run the program."""
    from doorstop import SERVER, VERSION

    # Shared options
    debug = argparse.ArgumentParser(add_help=False)
    debug.add_argument('-V', '--version', action='version', version=VERSION)
    debug.add_argument('--debug', action='store_true', help=argparse.SUPPRESS)
    debug.add_argument('--launch', action='store_true', help=argparse.SUPPRESS)
    shared = {'formatter_class': HelpFormatter, 'parents': [debug]}

    # Build main parser
    parser = argparse.ArgumentParser(prog=SERVER, description=__doc__,
                                     **shared)
    parser.add_argument('-j', '--project', metavar="PATH",
                        help="path to the root of the project")
    parser.add_argument('-P', '--port', metavar='NUM', type=int,
                        help="use a custom port for the server")

    # Parse arguments
    args = parser.parse_args(args=args)

    # Configure logging
    logging.basicConfig(format=settings.VERBOSE_LOGGING_FORMAT,
                        level=settings.VERBOSE_LOGGING_LEVEL)

    # Run the program
    run(args, os.getcwd(), parser.error)


def run(args, cwd, _):
    """Start the server.

    :param args: Namespace of CLI arguments (from this module or the CLI)
    :param cwd: current working directory
    :param error: function to call for CLI errors

    """
    global tree  # pylint: disable=W0603,C0103
    tree = build(cwd=cwd, root=args.project)
    tree.load()
    host = 'localhost'
    port = args.port or settings.SERVER_PORT
    if args.launch:
        url = utilities.build_url(host=host, port=port)
        webbrowser.open(url)
    bottle.run(host=host, port=port, debug=args.debug, reloader=args.debug)


@get('/')
def index():
    """Read the tree."""
    yield '<pre><code>'
    yield tree.draw()
    yield '</pre></code>'


@get('/documents')
def get_documents():
    """Read the tree's documents."""
    prefixes = [str(document.prefix) for document in tree]
    if utilities.json_response(request):
        data = {'prefixes': prefixes}
        return data
    else:
        return '<br>'.join(prefixes)


@get('/documents/<prefix>')
def get_document(prefix):
    """Read a tree's document."""
    document = tree.find_document(prefix)
    if utilities.json_response(request):
        data = {str(item.uid): item.data for item in document}
        return data
    else:
        return publisher.publish_lines(document, ext='.html')


@get('/documents/<prefix>/items')
def get_items(prefix):
    """Read a document's items."""
    document = tree.find_document(prefix)
    uids = [str(item.uid) for item in document]
    if utilities.json_response(request):
        data = {'uids': uids}
        return data
    else:
        return '<br>'.join(uids)


@get('/documents/<prefix>/items/<uid>')
def get_item(prefix, uid):
    """Read a document's item."""
    document = tree.find_document(prefix)
    item = document.find_item(uid)
    if utilities.json_response(request):
        return {'data': item.data}
    else:
        return publisher.publish_lines(item, ext='.html')


@get('/documents/<prefix>/items/<uid>/attrs')
def get_attrs(prefix, uid):
    """Read an item's attributes."""
    document = tree.find_document(prefix)
    item = document.find_item(uid)
    attrs = sorted(item.data.keys())
    if utilities.json_response(request):
        data = {'attrs': attrs}
        return data
    else:
        return '<br>'.join(attrs)


@get('/documents/<prefix>/items/<uid>/attrs/<name>')
def get_attr(prefix, uid, name):
    """Read an item's attribute value."""
    document = tree.find_document(prefix)
    item = document.find_item(uid)
    value = item.data.get(name, None)
    if utilities.json_response(request):
        data = {'value': value}
        return data
    else:
        if isinstance(value, str):
            return value
        try:
            return '<br>'.join(str(e) for e in value)
        except TypeError:
            return str(value)


@post('/documents/<prefix>/numbers')
def post_numbers(prefix):
    """Create the next number in a document."""
    document = tree.find_document(prefix)
    number = max(document.next, numbers[prefix])
    numbers[prefix] = number + 1
    if utilities.json_response(request):
        data = {'next': number}
        return data
    else:
        return str(number)


if __name__ == '__main__':  # pragma: no cover (manual test)
    main()
