#!/usr/bin/env python

"""REST client to request item numbers."""

import requests


def get_next_number(prefix, default=0):
    """Get the next number for the given document prefix."""
    url = 'http://127.0.0.1:8080/documents/{p}/numbers'.format(p=prefix)
    headers = {'content-type': 'application/json'}
    response = requests.post(url, headers=headers)
    data = response.json()
    number = data.get('next', default)
    return number


if __name__ == '__main__':  # pragma: no cover (manual test)
    import sys
    if len(sys.argv) != 2:
        exit("Usage: {} <PREFIX>".format(sys.argv[0]))
    print(get_next_number(sys.argv[-1]))
