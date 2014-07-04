Doorstop
========

[![Build Status](http://img.shields.io/travis/jacebrowning/doorstop/master.svg)](https://travis-ci.org/jacebrowning/doorstop)
[![Coverage Status](http://img.shields.io/coveralls/jacebrowning/doorstop/master.svg)](https://coveralls.io/r/jacebrowning/doorstop)
[![Scrutinizer Code Quality](http://img.shields.io/scrutinizer/g/jacebrowning/doorstop.svg)](https://scrutinizer-ci.com/g/jacebrowning/doorstop/?branch=master)
[![PyPI Version](http://img.shields.io/pypi/v/Doorstop.svg)](https://pypi.python.org/pypi/Doorstop)
[![PyPI Downloads](http://img.shields.io/pypi/dm/Doorstop.svg)](https://pypi.python.org/pypi/Doorstop)
[![Gittip](http://img.shields.io/badge/gittip-me-brightgreen.svg)](https://www.gittip.com/jacebrowning)

Doorstop is a tool to manage the storage of textual requirements alongside source code in version control.

Each linkable item (requirement, test case, etc.) is stored as a YAML file in a designated directory. The items in each directory form a document. Document items can be linked to one another to form a tree hierarchy. Doorstop provides mechanisms for modifying this hierarchy, checking the tree for consistency, and publishing documents in several formats.

Additional reading:

- publication: [JSEA Paper](http://www.scirp.org/journal/PaperInformation.aspx?PaperID=44268#.UzYtfWRdXEZ)
- conference: [GRDevDay Talk](https://speakerdeck.com/jacebrowning/doorstop-requirements-management-using-python-and-version-control)
- demo: [IPython Notebook](http://nbviewer.ipython.org/gist/jacebrowning/9754157)
- sample: [Generated HTML](http://doorstop.info/reqs/index)


Getting Started
===============

Requirements
------------

* Python 3.3+
* A version control system for requirements storage


Installation
------------

Doorstop can be installed with pip:

    $ pip install doorstop

Or directly from source:

    $ git clone https://github.com/jacebrowning/doorstop.git
    $ cd doorstop
    $ python setup.py install

After installation, Doorstop is available on the command-line:

    $ doorstop --help

And the package is available under the name 'doorstop':

    $ python
    >>> import doorstop
    >>> doorstop.__version__



Basic Usage
===========

Document Creation
-----------------

**Parent Document**

After configuring version control, a new parent document can be created:

    $ doorstop new REQ ./reqs
    created document: REQ (@/reqs)

Items can be added to the document and edited:

    $ doorstop add REQ
    added item: REQ001 (@/reqs/REQ001.yml)

    $ doorstop edit REQ1
    opened item: REQ001 (@/reqs/REQ001.yml)

**Child Documents**

Additional documents can be created that link to other documents:

    $ doorstop new TST ./reqs/tests --parent REQ
    created document: TST (@/reqs/tests)

Items can be added and linked to parent items:

    $ doorstop add TST
    added item: TST001 (@/reqs/tests/TST001.yml)

    $ doorstop link TST1 REQ1
    linked item: TST001 (@/reqs/tests/TST001.yml) -> REQ001 (@/reqs/REQ001.yml)


Document Validation
-------------------

To check a document hierarchy for consistency, run the main command:

    $ doorstop
    valid tree: REQ <- [ TST ]


Document Publishing
-------------------

A text report of a document can be displayed:

    $ doorstop publish TST
    1       TST001

            Verify the foobar will foo and bar.

            Links: REQ001

Other formats are also supported:

    $ doorstop publish TST --html
    <!DOCTYPE html>
    ...
    <body>
    <h1>1 (TST001)</h1>
    <p>Verify the foobar will foo and bar.</p>
    <p><em>Links: REQ001</em></p>
    </body>
    </html>

Or a file can be created using one of the supported extensions:

    $ doorstop publish TST path/to/tst.md
    publishing TST to path/to/tst.md...

Supported formats:

- Text: **.txt**
- Markdown: **.md**
- HTML: **.html**


Content Interchange
-------------------

**Export**

Documents can be exported for editing or to exchange with other systems:

    $ doorstop export TST
    TST001:
      active: true
      dervied: false
      level: 1
      links:
      - REQ001
      normative: true
      ref: ''
      text: |
        Verify the foobar will foo and bar.

Or a file can be created using one of the supported extensions:

    $ doorstop export TST path/to/tst.csv
    exporting TST to path/to/tst.csv...
    exported: path/to/tst.csv

Supported formats:

- YAML: **.yml**
- Comma-Separated Values: **.csv**
- Tab-Separated Values: **.tsv**
- Microsoft Office Excel: **.xlsx**

**Import**

Items can be created/updated from the export formats:

    $ doorstop import path/to/tst.csv TST



For Contributors
================

Requirements
------------

* GNU Make:
    * Windows: http://cygwin.com/install.html
    * Mac: https://developer.apple.com/xcode
    * Linux: http://www.gnu.org/software/make (likely already installed)
* virtualenv: https://pypi.python.org/pypi/virtualenv#installation
* Pandoc: http://johnmacfarlane.net/pandoc/installing.html
* Graphviz: http://www.graphviz.org/Download.php


Installation
------------

Create a virtualenv:

    make env

Run the tests:

    make test
    make tests  # includes integration tests

Build the documentation:

    make doc

Run static analysis:

    make pep8
    make pep257
    make pylint
    make check  # includes all checks

Prepare a release:

    make dist  # dry run
    make upload
