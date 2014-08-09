"""Shared functions for the `doorstop.web` package."""


def json_response(request):  # pragma: no cover (integration test)
    """Determine if the request's response should be JSON."""
    if request.query.get('format') == 'json':
        return True
    else:
        return request.content_type == 'application/json'
