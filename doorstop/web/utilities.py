"""Shared server functions."""


def json_response(req):
    """Determine if the request's response should be JSON."""
    if req.query.get('format') == 'json':
        return True
    else:
        return req.content_type == 'application/json'
