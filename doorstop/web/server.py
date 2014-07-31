#!/usr/bin/env python

"""REST server to display content and reserve item numbers."""

from collections import defaultdict
import logging

import bottle
from bottle import get, post, request

from doorstop import build, publisher
from doorstop.web import utilities

tree = None
numbers = defaultdict(int)


def main():
    """Process command-line arguments and start the server."""
    logging.basicConfig(level=logging.INFO)
    run(None, None, None)


def run(args, cwd, err):
    """Start the server."""
    global tree  # pylint: disable=W0603,C0103
    tree = build(cwd=cwd)
    tree.load()
    bottle.run(host='localhost', port=8080, debug=True, reloader=True)


@get('/')
def get_tree():
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
        data = {str(item.id): item.data for item in document}
        return data
    else:
        return publisher.publish_lines(document, ext='.html')


@get('/documents/<prefix>/items')
def get_items(prefix):
    """Read a document's items."""
    document = tree.find_document(prefix)
    uids = [str(item.id) for item in document]
    if utilities.json_response(request):
        data = {'uids': uids}
        return data
    else:
        return '<br>'.join(uids)


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


@get('/documents/<prefix>/items/<uid>')
def get_item(prefix, uid):
    """Read a document's item."""
    document = tree.find_document(prefix)
    item = document.find_item(uid)
    if utilities.json_response(request):
        return item.data
    else:
        return publisher.publish_lines(item, ext='.html')


@get('/documents/<prefix>/items/<uid>/<name>')
def get_item_attribute(prefix, uid, name):
    """Read an item's attribute."""
    document = tree.find_document(prefix)
    item = document.find_item(uid)
    value = item.data.get(name, None)
    if utilities.json_response(request):
        data = {'value': value}
        return data
    else:
        return str(value)


if __name__ == '__main__':
    main()
