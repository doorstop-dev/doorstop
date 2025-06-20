# 3.0.2 (2025-06-16)

- Upgraded `bottle` to fix import errors.

# 3.0.1 (2025-06-08)

- Added support for Python 3.13.

# 3.0 (2025-01-25)

- **BREAKING:** Dropped support for Python 3.6, 3.7, and 3.8.
- **BREAKING:** Removed `--no-body-levels` option to `doorstop publish`.
- Fixed overriding default attributes with `doorstop add`. ([@tangoalx](https://github.com/doorstop-dev/doorstop/pull/544))
- Fixed encoding error with special characters on Windows. ([@urbasus](https://github.com/doorstop-dev/doorstop/pull/526))
- Added support for publishing to the LaTeX format. ([@neerdoc](https://github.com/doorstop-dev/doorstop/pull/545))
- Added support for storing items in Markdown with YAML front matter. ([@ckolumbus](https://github.com/doorstop-dev/doorstop/pull/566))

# 2.2.1 (2023-10-07)

- Upgrade PyYAML to 6.x to fix installation on newer versions of Python.

# 2.2 (2022-01-22)

- Added support for UTF-8 symbols in references. ([@stanislaw](https://github.com/doorstop-dev/doorstop/pull/485))
- Added custom attributes to published documents. ([@chrta](https://github.com/doorstop-dev/doorstop/pull/476))
- Fixed handling of special characters when reordering items. ([@asimon-1](https://github.com/doorstop-dev/doorstop/pull/521))

# 2.1.4 (2021-01-15)

- Updated `markdown` to fix `AttributeError` in `doorstop-server`.

# 2.1.3 (2021-01-14)

- Removed `mdx_outline` Markdown extension, which is incompatible with Python 3.9.

# 2.1.2 (2020-07-06)

- Fixed tree builder to skip virtual environments.

# 2.1.1 (2020-02-16)

- Fixed missing `six` dependency.

# 2.1 (2020-02-16)

- Updated dependencies.

# 2.0 (2019-11-30)

- **BREAKING:** Switched to SHA256 for tracking changes to files and reviews of extended attributes. Use `doorstop review all` followed by `doorstop clear all` to update an existing project. WARNING: This marks all items as reviewed and clears all suspect links.
- Dropped support for Python 3.5.
- Fixed a bug with items not getting saved after edits.
- Added the ability to explicitly name a requirement.
- Improved the error message when there are multiple root documents.

# 1.6 (2019-08-10)

- Updated `edit` and `reorder` commands to use `$EDITOR`.
- Promoted support for item headers out of beta.
- Fixed bug with Doorstop attempting to import formulas from XLSX.
- Added support for `!include` statements in YAML to share configuration.
- Added `--default` option to `add` to specify a file with defaults values.

# 1.5 (2018-09-19)

- Added preliminary support for item headers. ([@rickeywang](https://github.com/doorstop-dev/doorstop/pull/285))
- Added major enhancements to the Desktop GUI. ([@elarivie](https://github.com/doorstop-dev/doorstop/pull/290))
  - Converted document outline to a tree view.
  - Made documents navigable via clicking links.
  - Added an icon for Linux and Windows.
- Fixed duplicate headings when publishing. ([@guille-r](https://github.com/doorstop-dev/doorstop/pull/302))
- Added Python 3.7 support.

# 1.4 (2017-10-22)

- Fixed issue running doorstop on CI. ([@ojohnny](https://github.com/doorstop-dev/doorstop/pull/281))

# 1.3.1 (2017-08-26)

- Fixed templates location for installation issue.

# 1.3 (2017-07-29)

- Updated HTML templates.
- Bug fixes.

# 1.2.1 (2017-02-25)

- Fixed issue where could `doorstop create` deleting the whole project.

# 1.2 (2017-02-11)

- Disabled excessive text cleanup in items. ([@michaelnt](https://github.com/michaelnt))
  - Running `doorstop review all` will be required due to whitespace changes.
- Added `--no-levels={all,body}` publishing options. ([@michaelnt](https://github.com/michaelnt))
- Removed unnecessary line breaks (`<br>`) in generated HTML. ([@michaelnt](https://github.com/michaelnt))
- **DEPRECATION WARNING:** `--no-body-levels` will not be supported in a future release.

# 1.1 (2017-01-09)

- Added '--strict-child-check' option to ensure links from every child document.

# 1.0.2 (2016-06-08)

- Moved the documentation to [ReadTheDocs](http://doorstop.readthedocs.io).

# 1.0 (2016-04-17)

- Fixed a bug checking levels across inactive items.
- Added error message for all IO errors.
- Added '--skip' options to disable documents during validation.
- Added Mercurial support. ([@tjasz](https://github.com/tjasz))

# 0.8.4 (2015-03-12)

- Restrict `openpyxl < 2.2` (there appears to be a breaking change).

# 0.8.3 (2014-10-10)

- Fixed a bug running VCS commands in subdirectories.
- Excluded `openpyxl == 2.1.0` as a dependency version.

# 0.8.2 (2014-09-29)

- Limit the maximum version of `openpyxl` to 2.1.0 due to deprecation bug.

# 0.8.1 (2014-09-04)

- Fixed a bug requesting new item numbers from the server.

# 0.8 (2014-08-28)

- Added `doorstop clear ...` to absolve items of their suspect link status.
- Added `doorstop review ...` to absolve items of their unreviewed status.
- Added `Item.clear()` to save stamps (hashes) of linked items.
- Added `Item.review()` to save stamps (hashes) of reviewed items.
- Added `doorstop reorder ...` to organize a document's structure.
- Renamed `Item.id` and `identifer` arguments to `uid`
- Added '--no-body-levels' to `doorstop publish` to hide levels on non-headings.
- Added `doorstop-server` to launch a REST API for UID reservation.
- Added '--server' argument to `doorstop add` to specify the server address.
- Added '--warn-all' and '--error-all' options promote warnings to errors.

# 0.7.1 (2014-08-18)

- Fixed bug importing items with empty attributes.

# 0.7 (2014-07-08)

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

# 0.6 (2014-05-15)

- Refactored `Item` levels into a `Level` class.
- Refactored `Item` identifiers into an `ID` class.
- Refactored `Item` text into a `Text` class (behaves like `str`).
- Methods no longer require nor accept 'document' and 'tree' arguments.
- Renamed `Item.find_rlinks()` to `Item.find_child_links()`.
- Changed '--no-rlink-check' to '--no-child-check'.
- Added `Item.find_child_items()` and `Item.find_child_documents()`.
- Added aliases to Item: parent_links, child_links/items/documents.
- Added '--with-child-links' to `doorstop publish` to publish child links.
- Added `doorstop import ...` CLI to import documents and items.
- Refactored `Document` prefixes in a `Prefix` class.
- Added '--no-level-check' to disable document level validation.
- Added '--reorder' option to `doorstop` to enable reordering.

# 0.5 (2014-04-25)

- Converted `Item.issues()` to a property and added `Item.get_issues()`.
- Added '--level' option to `doorstop add` to force an item level.
- Added warnings for duplicate item levels in a document.
- Added warnings for skipped item levels in a document.
- Renamed `Item` methods: add_link -> link, remove_link -> unlink, valid -> validate.
- Renamed `Document` methods: add -> add_item, remove -> remove_item, valid -> validate.
- Renamed `Tree` methods: new -> new_document, add -> add_item, remove -> remove_item, link -> link_items, unlink -> unlink_items, edit -> edit_item, valid -> validate.
- Added `doorstop.importer` functions to add exiting documents and items.

# 0.4.3 (2014-03-18)

- Fixed storage of 2-part levels ending in a multiple of 10.

# 0.4.2 (2014-03-17)

- Fixed a case where `Item.root` was not set.

# 0.4.1 (2014-03-16)

- Fixed auto save/load decorator order.

# 0.4 (2014-03-16)

- Added `Tree.delete()` to delete all document directories and item files.
- Added `doorstop publish all <directory>` to publish trees and `index.html`.

# 0.3 (2014-03-12)

- Added find_document and find_item convenience functions.
- Added `Document.delete()` to delete a document directory and its item files.

# 0.2 (2014-03-05)

- All `Item` text attributes are now be split by sentences and line-wrapped.
- Added `Tree.load()` for cases when lazy loading is too slow.
- Added caching to `Tree.find_item()` and `Tree.find_document()`.

# 0.1 (2014-02-17)

- Top-level items are no longer required to have a level ending in zero.
- Added `Item/Document.extended` to get a list of extended attribute names.

# 0.0.21 (2014-02-14)

- Documents can now have item files in sub-folders.

# 0.0.20 (2014-02-13)

- Updated `doorstop.core.report` to support lists of items.

# 0.0.19 (2014-02-13)

- Updated doorstop.core.report to support items or documents.
- Removed the 'iter\_' prefix from all generators.

# 0.0.18 (2014-02-12)

- Fixed CSS bullets indent.

# 0.0.17 (2014-01-31)

- Added caching of `Item` in the `Document` class.
- Added `Document.remove()` to delete an item by its ID.
- `Item.find_rlinks()` will now search the entire tree for links.

# 0.0.16 (2014-01-28)

- Added `Item.find_rlinks()` to return reverse links and child documents.
- Changed the logging format.
- Added a '--project' argument to provide a path to the root of the project.

# 0.0.15 (2014-01-27)

- Fixed a mutable default argument bug in `Item` creation.

# 0.0.14 (2014-01-27)

- Added `Tree/Document/Item.iter_issues()` method to yield all issues.
- `Tree/Document/Item.check()` now logs all issues rather than failing fast.
- Renamed `Tree/Document/Item.check()` to `valid()`.

# 0.0.13 (2014-01-25)

- Added `Document.sep` to separate prefix and item numbers.

# 0.0.12 (2014-01-24)

- Fixed missing package data.

# 0.0.11 (2014-01-23)

- Added `Item.active` property to disable certain items.
- Added `Item.derived` property to disable link checking on certain items.

# 0.0.10 (2014-01-22)

- Switched to embedded CSS in generated HTML.
- Shortened default `Item` and `Document` string formatting.

# 0.0.9 (2014-01-21)

- Added top-down link checking.
- Non-normative items with a zero-ended level are now headings.
- Added a CSS for generated HTML.
- The 'publish' command now accepts an output file path.

# 0.0.8 (2014-01-16)

- Searching for 'ref' will now also find filenames.
- Item files can now contain arbitrary fields.
- Document prefixes can now contain numbers, dashes, and periods.
- Added a 'normative' attribute to the Item class.

# 0.0.7 (2013-12-09)

- Always showing 'ref' in items.
- Reloading item attributes after a save.
- Inserting lines breaks after sentences in item 'text'.

# 0.0.6 (2013-12-04)

- Added basic report creation via `doorstop publish ...`.

# 0.0.5 (2013-11-20)

- Added item link and reference validation.
- Added cached of loaded items.
- Added preliminary VCS support for Git and Veracity.

# 0.0.4 (2013-11-04)

- Implemented `add`, `remove`, `link`, and `unlink` commands.
- Added basic tree validation.

# 0.0.3 (2013-10-17)

- Added the initial `Document` class.
- Items can now be ordered by 'level' in a document.
- Initial tutorial created.

# 0.0.2 (2013-09-25)

- Changed `doorstop init` to `doorstop new`.
- Added the initial `Item` class.
- Added stubs for the `Document` class.

# 0.0.1 (2013-09-11)

- Initial release of Doorstop.
