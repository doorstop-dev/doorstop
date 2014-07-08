Changelog
=========

0.7 (dev)
---------

- Added `doorstop delete ...` to delete document directories.
- Added `doorstop export ...` to export content for external tools.
- Fixed `doorstop publish ...` handling of unknown formats.
- Added tree structure and traceability to `index.html`.
- Added clickable links using Item IDs in HTML header tags.
- Fixed bug publishing a document to a directory.
- Fixed bug publishing a document without an extension or type specified.
- Updated `doorstop import ...` to import from document export formats.
- Updated `doorstop edit ...` to support document export/import.
- Renamed `doorstop new ...` to `doorstop create ...`.
- Made 'all' a reserved word, which cannot be used as a prefix.

0.6 (2014/5/15)
---------------

- Refactored Item levels into a Level class
- Refactored Item identifiers into an ID class
- Refactored Item text into a Text class (behaves like str)
- Methods no longer require nore accept 'document' and 'tree' arguments
- Renamed Item.find_rlinks() to Item.find_child_links()
- Changed '--no-rlink-check' to '--no-child-check'
- Added Item.find_child_items() and Item.find_child_documents()
- Added aliases to Item: parent_links, child_links/items/documents
- Added '--with-child-links' to 'doorstop publish' to publish child links
- Added 'doorstop import' CLI to import documents and items.
- Refactored Document prefixes in a Prefix class (also used in the ID class)
- Added '--no-level-check' to disable document level validation
- Added '--reorder' option to 'doorstop' to enable reording

0.5 (2014/04/25)
----------------

- Converted Item.issues() to a property and added Item.get_issues()
- Added '--level' option to 'doorstop add' to force an Item level
- Added warnings for duplicate Item levels in a Document
- Added warnings for skipped Item levels in a Document
- Renamed Item methods:
    + add_link -> link
    + remove_link -> unlink
    + valid -> validate
- Renamed Document methods:
    + add -> add_item
    + remove -> remove_item
    + valid -> validate
- Renamed Tree methods:
    + new -> new_document
    + add -> add_item
    + remove -> remove_item
    + link -> link_items
    + unlink -> unlink_items
    + edit -> edit_item
    + valid -> validate
- Added doorstop.importer functions to add exiting Documents and Items

0.4.3 (2014/03/18)
------------------

- Fixed storage of 2-part levels ending in a multiple of 10

0.4.2 (2014/03/17)
------------------

- Fixed a case where Item.root was not set

0.4.1 (2014/03/16)
------------------

- Fixed auto save/load decorator order

0.4 (2014/03/16)
----------------

- Added Tree.delete() to delete all Documents and Items
- Added 'doorstop publish all <directory>' to publish Trees and index.html

0.3 (2014/03/12)
----------------

- Added find_document and find_item convenience functions
- Added Document.delete() to delete a Document and its Items

0.2 (2014/03/05)
----------------

- All Item text attributes are now be split by sentences and line-wrapped
- Added Tree.load() for cases when lazy loading is too slow
- Added caching to Tree.find_item() and Tree.find_document()


0.1 (2014/02/17)
----------------

- Top-level Items are no longer required to have a level ending in zero
- Added Item/Document.extended to get a list of extended attribute names


0.0.21 (2014/02/14)
-------------------

- Documents can now have Item files in sub-folders


0.0.20 (2014/02/13)
-------------------

- Updated doorstop.core.report to support lists of Items


0.0.19 (2014/02/13)
-------------------

- Updated doorstop.core.report to support Items or Documents
- Removed the 'iter\_' prefix from all generators


0.0.18 (2014/02/12)
-------------------

- Fixed CSS bullets indent


0.0.17 (2014/01/31)
-------------------

- Added caching of Items in the Document class
- Added Document.remove() to delete an item by its ID
- Item.find_rlinks() will now search the entire tree for links


0.0.16 (2014/01/28)
-------------------

- Added Item.find_rlinks() to return reverse links and child documents
- Changed the logging format
- Added a '--project' argument to provide a path to the root of the project


0.0.15 (2014/01/27)
-------------------

- Fixed a mutable default argument bug in Item creation


0.0.14 (2014/01/27)
--------------------

- Added Tree/Document/Item.iter_issues() method to yield all issues
- Tree/Document/Item.check() now logs all issues rather than failing fast
- Renamed Tree/Document/Item.check() to valid()


0.0.13 (2014/01/25)
-------------------

- Added Document.sep to separate prefix and item numbers.


0.0.12 (2014/01/24)
-------------------

- Fixed missing package data.


0.0.11 (2014/01/23)
-------------------

- Added Item.active property to disable certain items.
- Added Item.dervied property to disable link checking on certain items.


0.0.10 (2014/01/22)
-------------------

- Switched to embedded CSS in generated HTML.
- Shorted default Item and Document string formatting.


0.0.9 (2014/01/21)
------------------

- Added top-down link checking.
- Non-normative items with a zero-ended level are now headings.
- Added a CSS for generated HTML.
- The 'publish' command now accepts an output file path.


0.0.8 (2014/01/16)
------------------

- Searching for 'ref' will now also find filenames.
- Item files can now contain arbitrary fields.
- Document prefixes can now contain numbers, dashes, and periods.
- Added a 'normative' attribute to the Item class.


0.0.7 (2013/12/09)
------------------

- Always showing 'ref' in items.
- Reloading item attributes after a save.
- Inserting lines breaks after sentences in item 'text'.


0.0.6 (2013/12/04)
------------------

- Added basic report creation via 'doorstop publish'.


0.0.5 (2013/11/20)
------------------

- Added item link and reference validation.
- Added cached of loaded items.
- Added preliminary VCS support for Git and Veracity.


0.0.4 (2013/11/04)
------------------

- Implemented 'add', 'remove', 'link', and 'unlink' commands.
- Added basic tree validation.


0.0.3 (2013/10/17)
------------------

- Added the initial Document class.
- Items can now be ordered by 'level' in a Document.
- Initial tutorial created.


0.0.2 (2013/09/25)
------------------

- Changed 'doorstop init' to 'doorstop new'.
- Added the initial Item class.
- Added stubs for the Document class.


0.0.1 (2013/09/11)
------------------

- Initial release of Doorstop.
