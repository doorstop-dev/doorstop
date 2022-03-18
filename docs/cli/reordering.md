# Documents Headings

The items in a document are arranged according to their level attribute, with levels ending in .0
creating headings and the subsequent items forming sub headings.

A document can contain an arbitraty number of headings and sub headings.

A normative heading item will display the item's uid as the heading text. A non normative heading
displays the first line of the item text, with any subsequent text displayed in the body of the heading.


# Automatic item reordering

Items in a document can be automatically reordered to remove gaps or duplicate entries in item headings.

```sh
$ doorstop reorder --auto REQ
building tree...
reordering document REQ...
reordered document: REQ
```

# Manual item reordering

Manual reordering creates an index.yml file in the document directory which describes the desired outline
of the document. The index.yml is edited, changing the indentation and order of the items to update the
levels of each item.

```sh
$ doorstop reorder --tool vi REQ
building tree...
reorder from 'reqs/index.yml'? [y/n] y
reordering document REQ...
reordered document: REQ
```

## Adding a new item

An item can be added by adding a new line to the index.yml containing an unknown UID, e.g. new.
A comment following the new item ID can be used to set the item text.
If the line after a new item is further indented the item is treated as a heading and marked
as non normative.

```yaml
###############################################################################
# THIS TEMPORARY FILE WILL BE DELETED AFTER DOCUMENT REORDERING
# MANUALLY INDENT, DEDENT, & MOVE ITEMS TO THEIR DESIRED LEVEL
# A NEW ITEM WILL BE ADDED FOR ANY UNKNOWN IDS, i.e. - new:
# THE COMMENT WILL BE USED AS THE ITEM TEXT FOR NEW ITEMS
# CHANGES WILL BE REFLECTED IN THE ITEM FILES AFTER CONFIRMATION
###############################################################################

initial: 1.0
outline:
    - REQ018: # Overview
        - REQ019: # Doorstop is a requirements management tool that leverage...
        - NEW: # The text of a new item
    - NEW: # A new heading
        - NEW: # The text of a new ite,
```

## Deleting an item

Deleting a line from index.yml will result in the item being deleted.
