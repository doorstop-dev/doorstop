#!/usr/bin/env python

import logging

import bottle
from bottle import get, post, request

from doorstop import build, publisher

tree = None  # pylint: disable=C0103


@get('/')
def get_tree():
    yield '<pre><code>'
    yield tree.draw()
    yield '</pre></code>'


@get('/documents')
def get_documents():
    prefixes = [str(document.prefix) for document in tree]
    if json_response(request):
        data = {'prefixes': prefixes}
        return data
    else:
        return '<br>'.join(prefixes)


@get('/documents/<prefix>')
def get_document(prefix):
    document = tree.find_document(prefix)
    if json_response(request):
        data = {str(item.id): item.data for item in document}
        return data
    else:
        return publisher.publish_lines(document, ext='.html')


@get('/documents/<prefix>/items')
def get_items(prefix):
    document = tree.find_document(prefix)
    identifiers = [str(item.id) for item in document]
    if json_response(request):
        data = {'identifiers': identifiers}
        return data
    else:
        return '<br>'.join(identifiers)


@post('/documents/<prefix>/items')
def add_item(prefix):
    document = tree.find_document(prefix)
    number = document.next
    if json_response(request):
        data = {'number': number}
        return data
    else:
        return str(number)


@get('/documents/<prefix>/items/<identifier>')
def get_item(prefix, identifier):
    document = tree.find_document(prefix)
    item = document.find_item(identifier)
    if json_response(request):
        return item.data
    else:
        return publisher.publish_lines(item, ext='.html')


@get('/documents/<prefix>/items/<identifier>/<name>')
def get_item_attribute(prefix, identifier, name):
    document = tree.find_document(prefix)
    item = document.find_item(identifier)
    value = item.data.get(name, None)
    if json_response(request):
        data = {'value': value}
        return data
    else:
        return str(value)


def json_response(a_request):
    if a_request.query.get('format') == 'json':
        return True
    else:
        return a_request.content_type == 'application/json'


def main():
    logging.basicConfig(level=logging.INFO)
    run(None, None, None)


def run(args, cwd, err):
    global tree  # pylint: disable=W0603,C0103
    tree = build()
    tree.load()
    bottle.run(host='localhost', port=8080, debug=True, reloader=True)


if __name__ == '__main__':
    main()
