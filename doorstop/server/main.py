#!/usr/bin/env python

"""REST server to display content and reserve item numbers."""

import os
from collections import defaultdict
import webbrowser
import argparse
import logging
import subprocess

import bottle
from bottle import get, post, request, hook, response, static_file, template, auth_basic, abort

from doorstop import common, build, publisher
from doorstop.common import HelpFormatter
from doorstop.server import utilities
from doorstop import settings
from doorstop.core import vcs
from doorstop.core import types

app = bottle.Bottle()
tree = None  # set in `run`, read in the route functions
numbers = defaultdict(int)  # cache of next document numbers
TEMPLATE = 'server'

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
    cwd = os.getcwd()

    parser.add_argument('-j', '--project', default=None,
                        help="path to the root of the project")
    parser.add_argument('-P', '--port', metavar='NUM', type=int,
                        default=settings.SERVER_PORT,
                        help="use a custom port for the server")
    parser.add_argument('-H', '--host', default='127.0.0.1',
                        help="IP address to listen")
    parser.add_argument('-w', '--wsgi', action='store_true',
                        help="Run as a WSGI process")
    parser.add_argument('-b', '--baseurl', default='',
                        help="Base URL this is served at (Usually only necessary for WSGI)")
    parser.add_argument('-v', '--verbose', action='count', default=0,
                       help="enable verbose logging")

    # Parse arguments
    args = parser.parse_args(args=args)

    if args.project is None:
        args.project = vcs.find_root(cwd)

    if args.verbose == 0:
        logging_level = settings.VERBOSE_LOGGING_LEVEL
        logging_format = settings.VERBOSE_LOGGING_FORMAT
    else:
        logging_level = settings.VERBOSE2_LOGGING_LEVEL
        logging_format = settings.VERBOSE2_LOGGING_FORMAT
    # Run the program
    run(args, os.getcwd())


def run(args, cwd):
    """Start the server.

    :param args: Namespace of CLI arguments (from this module or the CLI)
    :param cwd: current working directory
    :param error: function to call for CLI errors

    """
    global tree  # pylint: disable=W0603
    tree = build(cwd=cwd, root=args.project)
    tree.load()
    host = args.host
    port = args.port or settings.SERVER_PORT
    bottle.TEMPLATE_PATH.insert(0, os.path.join(os.path.dirname(__file__),
                                                '..', '..', 'views'))

    # If you started without WSGI, the base will be '/'.
    if args.baseurl == '' and not args.wsgi:
        args.baseurl = '/'

    # If you specified a base URL, make sure it ends with '/'.
    if args.baseurl != '' and not args.baseurl.endswith('/'):
        args.baseurl += '/'

    bottle.SimpleTemplate.defaults['baseurl'] = args.baseurl
    bottle.SimpleTemplate.defaults['navigation'] = True

    if args.launch:
        url = utilities.build_url(host=host, port=port)
        webbrowser.open(url)
    if not args.wsgi:
        bottle.run(app=app, host=host, port=port,
                   debug=args.debug, reloader=args.debug)

@hook('before_request')
def strip_path():
    request.environ['PATH_INFO'] = request.environ['PATH_INFO'].rstrip('.html')


@hook('after_request')
def enable_cors():  # pragma: no cover (manual test)
    """Allow a webserver running on the same machine to access data."""
    response.headers['Access-Control-Allow-Origin'] = '*'


@app.route('/')
def index():
    """Read the tree."""
    yield template('index', tree_code=tree.draw(html_links=True))


@app.route('/documents')
def get_documents():
    """Read the tree's documents."""
    prefixes = [str(document.prefix) for document in tree]
    if utilities.json_response(request):
        data = {'prefixes': prefixes}
        return data
    else:
        return template('document_list', prefixes=prefixes)


@app.route('/documents/all')
def get_all_documents():
    """Read the tree's documents."""
    if utilities.json_response(request):
        data = {str(d.prefix): {str(i.uid): i.data for i in d} for d in tree}
        return data
    else:
        prefixes = [str(document.prefix) for document in tree]
        return template('document_list', prefixes=prefixes)

@app.route('/documents/<prefix>/')
def get_document(prefix):
    """Read a tree's document."""
    document = tree.find_document(prefix)
    if utilities.json_response(request):
        data = {str(item.uid): item.data for item in document}
        return data
    else:
        return publisher.publish_lines(document, ext='.html',
                                       template=TEMPLATE, linkify=True,
                                       baseurl='/documents/doorstop/')


@app.get('/documents/<prefix>/items')
def get_items(prefix):
    """Read a document's items."""
    document = tree.find_document(prefix)
    uids = [str(item.uid) for item in document]
    if utilities.json_response(request):
        data = {'uids': uids}
        return data
    else:
        return template('item_list', prefix=prefix, items=uids)

@app.post('/documents/<prefix>/items')
def insert_item(prefix):
    """Create a new item at the level"""
    uid = request.forms.get('uid')
    document = tree.find_document(prefix)
    item = document.find_item(uid)
    level = item.level + 1
    item = document.add_item(level=level)
    return {'result':'ok'}

@app.route('/documents/<prefix>/items/<uid>')
def get_item(prefix, uid):
    """Read a document's item."""
    document = tree.find_document(prefix)
    item = document.find_item(uid)
    if utilities.json_response(request):
        children = ", ".join([str(child) for child in item.find_child_links()])[2:]
        return {'text': item.text,
                'level': str(item.level),
                'normative': item.normative,
                'derived': item.derived,
                'links': ", ".join([str(uid) for uid in item.parent_links]),
                'children': children}
    else:
        return publisher.publish_lines(item, ext='.html', linkify=True)


@app.route('/documents/<prefix>/items/<uid>/attrs')
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


@app.route('/documents/<prefix>/items/<uid>/attrs/<name>')
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


@app.route('/documents/<prefix>/assets/<filepath:path>')
def get_assets(prefix, filepath):
    if prefix == 'doorstop':
        root = os.path.join(os.path.dirname(__file__), '..', 'core', 'files', 'assets')
    else:
        document = tree.find_document(prefix)
        root = os.path.join(document.path, 'assets')
    print("static file %s/%s" % (root, filepath))
    return static_file(filepath, root=root)


@app.post('/documents/<prefix>/numbers')
def post_numbers(prefix):
    """Create the next number in a document."""
    document = tree.find_document(prefix)
    number = max(document.next_number, numbers[prefix])
    numbers[prefix] = number + 1
    if utilities.json_response(request):
        data = {'next': number}
        return data
    else:
        return str(number)


@app.delete('/documents/<prefix>/items/<uid>')
def delete_item(prefix, uid):
    """Delete document item."""
    document = tree.find_document(prefix)
    item = document.find_item(uid)
    item.delete()
    return {'result':'ok'}

def check(user, password):
    "Dummy authentication"
    return True

@app.post('/documents/<prefix>/items/<uid>')
@auth_basic(check)
def save_item(prefix, uid):
    """Update a document's item."""
    document = tree.find_document(prefix)
    item = document.find_item(uid)
    item.auto = False
    itemtext = request.forms.itemtext
    item.text = itemtext

    link_text = request.forms.links
    if ',' in link_text:
        links = link_text.split(',')
    else:
        links = link_text.split()
    links = [l.strip() for l in links]

    if links:
        item.links = links

    if request.forms.normative == "on":
        item.normative = True
    else:
        item.normative = False

    if request.forms.derived == "on":
        item.derived = True
    else:
        item.derived = False

    if item.level != request.forms.level:
        item.level = request.forms.level
        document.reorder(manual=False, keep=item)

    item.save()
    message = request.forms.message
    if not message:
        message = "Change by {}".format(request.auth[0])

    try:
        stdout = tree.vcs.commit(path=item.path, 
                                 message=message,
                                 username=request.auth[0],
                                 password=request.auth[1])
    except subprocess.CalledProcessError:
        abort(401)

    return {'result':'ok'}


if __name__ == '__main__':  # pragma: no cover (manual test)
    main()
