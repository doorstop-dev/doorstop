"""Shared functions for the `doorstop.web` package."""

from doorstop import settings


def build_url(host=None, port=None, path=None):
    """Build the server's URL with optional path."""
    host = host or settings.SERVER_HOST
    port = port or settings.SERVER_PORT
    if not host:
        return None
    url = 'http://{}'.format(host)
    if port != 80:
        url += ':{}'.format(port)
    if path:
        url += path
    return url


def json_response(request):  # pragma: no cover (integration test)
    """Determine if the request's response should be JSON."""
    if request.query.get('format') == 'json':
        return True
    else:
        return request.content_type == 'application/json'
