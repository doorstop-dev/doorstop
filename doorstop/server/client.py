#!/usr/bin/env python

"""REST client to request item numbers."""

import requests

from doorstop import common
from doorstop.common import DoorstopError
from doorstop import settings

log = common.logger(__name__)


def build_url(path=None):
    """Build the server's URL with optional path."""
    if not settings.SERVER_HOST:
        return None
    url = 'http://{}'.format(settings.SERVER_HOST)
    if settings.SERVER_PORT != 80:
        url += ':{}'.format(settings.SERVER_PORT)
    if path:
        url += path
    return url


def exists(path='/documents'):
    """Determine if the server exists."""
    found = False
    url = build_url(path=path)
    if url:
        log.debug("looking for {}...".format(url))
        try:
            response = requests.head(url)
        except requests.exceptions.RequestException as exc:
            log.debug(exc)
        else:
            found = response.status_code == 200
        if found:
            log.info("found: {}".format(url))
    return found


def check():
    """Ensure the server exists."""
    log.info("checking for a server...")
    if settings.SERVER_HOST is None:
        log.info("no server in use")
        return
    if not settings.SERVER_HOST:
        raise DoorstopError("no server specified")
    if not exists():
        raise DoorstopError("unknown server: {}".format(settings.SERVER_HOST))


def get_next_number(prefix):
    """Get the next number for the given document prefix."""
    number = None
    url = build_url('/documents/{p}/numbers'.format(p=prefix))
    if not url:
        log.info("no server to get the next number from")
        return None
    headers = {'content-type': 'application/json'}
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        number = data.get('next')
    if number is None:
        raise DoorstopError("bad response from: {}".format(url))
    log.info("next number from the server: {}".format(number))
    return number


if __name__ == '__main__':  # pragma: no cover (manual test)
    import sys
    if len(sys.argv) != 2:
        exit("Usage: {} <PREFIX>".format(sys.argv[0]))
    print(get_next_number(sys.argv[-1]))
