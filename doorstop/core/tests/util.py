from doorstop.core.builder import build


_tree = None  # implicit tree for convenience functions


def find_document(prefix):
    """Find a document without an explicitly building a tree."""
    tree = _get_tree()
    document = tree.find_document(prefix)
    return document


def find_item(uid):
    """Find an item without an explicitly building a tree."""
    tree = _get_tree()
    item = tree.find_item(uid)
    return item


def _get_tree(request_next_number=None):
    """Get a shared tree for convenience functions."""
    global _tree  # pylint: disable=W0603
    if _tree is None:
        _tree = build(should_auto_save=True)
    _tree.request_next_number = request_next_number
    return _tree


def _set_tree(value):
    """Set the shared tree to a specific value (for testing)."""
    global _tree  # pylint: disable=W0603
    _tree = value


def _clear_tree():
    """Force the shared tree to be rebuilt."""
    global _tree  # pylint: disable=W0603
    _tree = None
