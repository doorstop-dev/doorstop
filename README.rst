Introduction
============

Doorstop is a tool to manage the storage of textual requirements alongside
source code in version control.

Each requirement item is stored as a YAML file in a designated directory.
The items in each designated directory form a document. Document items can
be linked to one another to form a document hierarchy. Doorstop provides
mechanisms for modifying this hierarchy, checking the tree for consistency,
and publishing documents in several formats.

.. NOTE::
   0.0.x releases are experimental and interfaces will likely change.



Getting Started
===============

Requirements
------------

* Python 3.3
* Git or Veracity (for requirements storage)


Installation
------------

Doorstop can be installed with ``pip``::

    $ pip install Doorstop

After installation, Doorstop is available on the command-line::

    $ doorstop --help

And the package is available under the name ``doorstop``::

    $ python
    >>> import doorstop
    >>> doorstop.__version__


Document Creation
=================

Parent Document
---------------

After configuring version control, a new parent document can be created::

    $ doorstop new REQ ./reqs
    created document: REQ (@/reqs)

Items can be added to the document and edited::

    $ doorstop add REQ
    added item: REQ001 (@/reqs/REQ001.yml)

    $ doorstop edit REQ1
    opened item: REQ001 (@/reqs/REQ001.yml)


Child Documents
---------------

Additional documents can be created that link to other documents::

    $ doorstop new TST ./reqs/tests --parent REQ
    created document: TST (@/reqs/tests)

Items can be added and linked to parent items::

    $ doorstop add TST
    added item: TST001 (@/reqs/tests/TST001.yml)

    $ doorstop link TST1 REQ1
    linked item: TST001 (@/reqs/tests/TST001.yml) -> REQ001 (@/reqs/REQ001.yml)


Document Validation
===================

To check a document hierarchy for consistency, run the main command::

    $ doorstop
    valid tree: REQ <- [ TST ]


Document Publishing
===================

A text report of a document can be displayed::

    $ doorstop publish TST
    1       TST001

            Verify the foobar will foo and bar.

            Links: REQ001

Other formats are also supported::

    $ doorstop publish TST --html
    <!DOCTYPE html>
    ...
    <body>
    <h1>1 (TST001)</h1>
    <p>Verify the foobar will foo and bar.</p>
    <p><em>Links: REQ001</em></p>
    </body>
    </html>

Or a file can be created using one of the supported extensions::

   $ doorstop publish TST path/to/tst.md
   publishing TST to path/to/tst.md...

Supported formats:

* Text: **.txt**
* Markdown: **.md**
* HTML: **.html**
