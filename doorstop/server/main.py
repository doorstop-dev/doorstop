#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-3.0-only
# pylint: disable=import-outside-toplevel

"""REST server to display content and reserve item numbers."""

import argparse
import logging
import os
import webbrowser
from collections import defaultdict
from typing import Dict

import bottle
from bottle import get, hook, post, request, response, template

from doorstop import Tree, build, common, settings
from doorstop.common import HelpFormatter
from doorstop.core import vcs
from doorstop.core.publishers.html import HtmlPublisher
from doorstop.server import utilities

log = common.logger(__name__)

app = utilities.StripPathMiddleware(bottle.app())
config = {}
tree: Tree = None  # type: ignore
html_publisher: HtmlPublisher = None  # type: ignore
numbers: Dict[str, int] = defaultdict(int)  # cache of next document numbers


def main(args=None):
    """Process command-line arguments and run the program."""
    from doorstop import SERVER, VERSION

    # Shared options
    debug = argparse.ArgumentParser(add_help=False)
    debug.add_argument("-V", "--version", action="version", version=VERSION)
    debug.add_argument(
        "--debug", action="store_true", help="run the server in debug mode"
    )
    debug.add_argument(
        "--launch", action="store_true", help="open the server UI in a browser"
    )
    shared = {"formatter_class": HelpFormatter, "parents": [debug]}

    # Build main parser
    parser = argparse.ArgumentParser(prog=SERVER, description=__doc__, **shared)  # type: ignore
    cwd = os.getcwd()

    parser.add_argument(
        "-j", "--project", default=None, help="path to the root of the project"
    )
    parser.add_argument(
        "-P",
        "--port",
        metavar="NUM",
        type=int,
        default=settings.SERVER_PORT,
        help="use a custom port for the server",
    )
    parser.add_argument(
        "-H", "--host", default="127.0.0.1", help="IP address to listen"
    )
    parser.add_argument(
        "-w", "--wsgi", action="store_true", help="Run as a WSGI process"
    )
    parser.add_argument(
        "-b",
        "--baseurl",
        default="",
        help="Base URL this is served at (Usually only necessary for WSGI)",
    )

    # Parse arguments
    args = parser.parse_args(args=args)

    if args.project is None:
        args.project = vcs.find_root(cwd)

    # Configure logging
    logging.basicConfig(
        format=settings.VERBOSE_LOGGING_FORMAT, level=settings.VERBOSE_LOGGING_LEVEL
    )

    # Run the program
    setup(args, os.getcwd(), parser.error)
    run(args)


def setup(args, cwd, _):
    """Handle the setup of the server.

    :param args: Namespace of CLI arguments (from this module or the CLI)
    :param cwd: current working directory
    :param error: function to call for CLI errors

    """
    global tree, html_publisher
    tree = build(cwd=cwd, root=args.project)
    tree.load()
    html_publisher = HtmlPublisher(tree, ext=".html")
    # Force html_publisher to set index and matrix to True.
    html_publisher.setup(True, True, True)
    host = args.host
    port = args.port or settings.SERVER_PORT
    bottle.TEMPLATE_PATH.insert(
        0, os.path.join(os.path.dirname(__file__), "..", "views")
    )

    # If you started without WSGI, the base will be '/'.
    if args.baseurl == "" and not args.wsgi:
        args.baseurl = "/"

    # If you specified a base URL, make sure it ends with '/'.
    if args.baseurl != "" and not args.baseurl.endswith("/"):
        args.baseurl += "/"

    bottle.SimpleTemplate.defaults["baseurl"] = args.baseurl
    # Remove navigation since we handle it ourselves.
    bottle.SimpleTemplate.defaults["navigation"] = False

    if args.launch:
        url = utilities.build_url(host=host, port=port)
        webbrowser.open(url)

    # Configure the app.
    config["host"] = host
    config["port"] = port
    config["args"] = args.debug


def run(args):
    if not args.wsgi:
        bottle.run(
            app=app,
            host=config["host"],
            port=config["port"],
            debug=config["args"],
            reloader=config["args"],
        )


@hook("before_request")
def strip_path():
    request.environ["PATH_INFO"] = request.environ["PATH_INFO"].rstrip("/")
    if (
        len(request.environ["PATH_INFO"]) > 0
        and request.environ["PATH_INFO"][-5:] == ".html"
    ):
        request.environ["PATH_INFO"] = request.environ["PATH_INFO"][:-5]


@hook("after_request")
def enable_cors():
    """Allow a webserver running on the same machine to access data."""
    response.headers["Access-Control-Allow-Origin"] = "*"


@get("/")
@get("/index")
def index():
    """Read the tree."""
    prefixes = [str(document.prefix) for document in tree]
    lines = html_publisher.lines_index(prefixes, tree=tree)
    yield template(
        "doorstop",
        body="\n".join(lines),
        toc=None,
        doc_attributes={
            "name": "Index",
            "ref": "-",
            "title": "Doorstop index",
            "by": "-",
            "major": "-",
            "minor": "",
        },
        is_doc=False,
    )


@get("/traceability")
def get_traceability():
    """Read the traceability matrix."""
    if utilities.json_response(request):
        trace_list = tree.get_traceability()
        # Convert the Items in the list to strings only.
        traces = []
        for row in trace_list:
            trace_row = []
            for col in row:
                trace_row.append(str(col))
            traces.append(trace_row)
        data = {"traceability": traces}
        return data
    else:
        lines = html_publisher.lines_matrix()
        return template(
            "doorstop",
            body="\n".join(lines),
            toc=None,
            doc_attributes={
                "name": "Traceability",
                "ref": "-",
                "title": "Doorstop traceability matrix",
                "by": "-",
                "major": "-",
                "minor": "",
            },
            is_doc=False,
        )


@get("/documents")
def get_documents():
    """Read the tree's documents."""
    prefixes = [str(document.prefix) for document in tree]
    if utilities.json_response(request):
        data = {"prefixes": prefixes}
        return data
    else:
        return template(
            "document_list",
            prefixes=prefixes,
            doc_attributes={
                "name": "Documents",
                "ref": "-",
                "title": "Doorstop document list",
                "by": "-",
                "major": "-",
                "minor": "",
            },
            is_doc=False,
        )


@get("/documents/all")
def get_all_documents():
    """Read the tree's documents."""
    if utilities.json_response(request):
        data = {str(d.prefix): {str(i.uid): i.data for i in d} for d in tree}
        return data
    else:
        prefixes = [str(document.prefix) for document in tree]
        return template(
            "document_list",
            prefixes=prefixes,
            doc_attributes={
                "name": "Documents",
                "ref": "-",
                "title": "Doorstop document list",
                "by": "-",
                "major": "-",
                "minor": "",
            },
            is_doc=False,
        )


@get("/documents/<prefix>")
def get_document(prefix):
    """Read a tree's document."""
    document = tree.find_document(prefix)
    if utilities.json_response(request):
        data = {str(item.uid): item.data for item in document}
        return data
    else:
        return html_publisher.lines(document, ext=".html", linkify=True, toc=True)


@get("/documents/<prefix>/items")
def get_items(prefix):
    """Read a document's items."""
    document = tree.find_document(prefix)
    uids = [str(item.uid) for item in document]
    if utilities.json_response(request):
        data = {"uids": uids}
        return data
    else:
        return template(
            "item_list",
            prefix=prefix,
            items=uids,
            doc_attributes={
                "name": "Items",
                "ref": "-",
                "title": "Doorstop item list",
                "by": "-",
                "major": "-",
                "minor": "",
            },
            is_doc=False,
        )


@get("/documents/<prefix>/items/<uid>")
def get_item(prefix, uid):
    """Read a document's item."""
    document = tree.find_document(prefix)
    item = document.find_item(uid)
    lines = html_publisher.lines(item, ext=".html")
    if utilities.json_response(request):
        return {"data": item.data}
    else:
        return "<br>".join(lines)


@get("/documents/<prefix>/items/<uid>/attrs")
def get_attrs(prefix, uid):
    """Read an item's attributes."""
    document = tree.find_document(prefix)
    item = document.find_item(uid)
    attrs = sorted(item.data.keys())
    if utilities.json_response(request):
        data = {"attrs": attrs}
        return data
    else:
        return "<br>".join(attrs)


@get("/documents/<prefix>/items/<uid>/attrs/<name>")
def get_attr(prefix, uid, name):
    """Read an item's attribute value."""
    document = tree.find_document(prefix)
    item = document.find_item(uid)
    value = item.data.get(name, None)
    if utilities.json_response(request):
        data = {"value": value}
        return data
    else:
        if isinstance(value, str):
            return value
        try:
            return "<br>".join(str(e) for e in value)
        except TypeError:
            return str(value)


@get("/template/<filename>")
def get_template(filename):
    """Serve static files. Mainly used to serve CSS files and javascript."""
    public_dir = os.path.join(
        os.path.dirname(__file__), "..", "core", "files", "templates", "html"
    )
    if os.path.isfile(os.path.join(public_dir, filename)):
        return bottle.static_file(filename, root=public_dir)
    return bottle.HTTPError(404, "File does not exist.")


@get("/documents/assets/<filename>")
def get_assets(filename):
    """Serve static files. Used to serve images and other assets."""
    # Since assets are stored in the document, we need to loop over all the
    # documents to find the requested asset.
    for document in tree:
        # Check if the asset exists in the document's assets folder.
        if document.assets:
            temporary_path = os.path.join(document.assets, filename)
            if os.path.exists(temporary_path):
                return bottle.static_file(filename, root=document.assets)
    # If the asset does not exist, return a 404.
    return bottle.HTTPError(404, "File does not exist.")


@post("/documents/<prefix>/numbers")
def post_numbers(prefix):
    """Create the next number in a document."""
    document = tree.find_document(prefix)
    number = max(document.next_number, numbers[prefix])
    numbers[prefix] = number + 1
    if utilities.json_response(request):
        data = {"next": number}
        return data
    else:
        return str(number)


if __name__ == "__main__":
    main()
