#!/usr/bin/env python

import json
import logging

from bottle import get, post, request, run

from doorstop import build, publisher


@get('/')
def get_tree():
    yield '<pre><code>'
    yield tree.draw()
    yield '</pre></code>'


@get('/documents')
def get_documents():
    prefixes = [str(document.prefix) for document in tree]
    if json_response(request):
        return json.dumps(prefixes)
    else:
        return '<br>'.join(prefixes)


@get('/documents/<prefix>')
def get_document(prefix):
    document = tree.find_document(prefix)
    if json_response(request):
        data = {str(item.id): item.data for item in document}
        return json.dumps(data)
    else:
        return publisher.publish_lines(document, ext='.html')


@get('/documents/<prefix>/items')
def get_items(prefix):
    document = tree.find_document(prefix)
    identifiers = [str(item.id) for item in document]
    if json_response(request):
        return json.dumps(identifiers)
    else:
        return '<br>'.join(identifiers)


@post('/documents/<prefix>/items')
def add_item(prefix):
    document = tree.find_document(prefix)
    number = document.next
    if json_response(request):
        return json.dumps(number)
    else:
        return str(number)


@get('/documents/<prefix>/items/<identifier>')
def get_item(prefix, identifier):
    document = tree.find_document(prefix)
    item = document.find_item(identifier)
    if json_response(request):
        return json.dumps(item.data)
    else:
        return publisher.publish_lines(item, ext='.html')


@get('/documents/<prefix>/items/<identifier>/<name>')
def get_item_attribute(prefix, identifier, name):
    document = tree.find_document(prefix)
    item = document.find_item(identifier)
    value = item.data.get(name, None)
    if json_response(request):
        return json.dumps(value)
    else:
        return str(value)


def json_response(a_request):
    if a_request.query.get('format') == 'json':
        return True
    else:
        return a_request.content_type == 'application/json'


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    tree = build()
    tree.load()
    run(host='localhost', port=8080, debug=True, reloader=True)
