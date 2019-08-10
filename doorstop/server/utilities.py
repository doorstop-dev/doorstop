# SPDX-License-Identifier: LGPL-3.0-only

"""Shared functions for the `doorstop.server` package."""

from doorstop import common, settings

log = common.logger(__name__)


class StripPathMiddleware:  # pylint: disable=R0903
    """WSGI middleware that strips trailing slashes from all URLs."""

    def __init__(self, app):
        self.app = app

    def __call__(self, e, h):
        e['PATH_INFO'] = e['PATH_INFO'].rstrip('/')
        return self.app(e, h)


def build_url(host=None, port=None, path=None):
    """Build the server's URL with optional path."""
    host = host or settings.SERVER_HOST
    port = port or settings.SERVER_PORT
    log.debug("building URL: {} + {} + {}".format(host, port, path))
    if not host:
        return None
    url = 'http://{}'.format(host)
    if port != 80:
        url += ':{}'.format(port)
    if path:
        url += path
    return url


def json_response(request):
    """Determine if the request's response should be JSON."""
    if request.query.get('format') == 'json':
        return True
    else:
        return request.content_type == 'application/json'
