Introduction
============

Doorstop is a tool to manage the storage of texual requirements alongside
source code in version control.

Each requirement item is stored as a YAML file in a designated directory.
The items in each designated directory form a document. Document items can
be linked to one another to form a document hiearchy. Doorstop provides
mechanisms for modifying this hiearchy and checking the tree for consistency.

.. NOTE::
   0.0.x releases are experimental and no functionality is gaurenteed.



Getting Started
===============

Requirements
------------

* Python 3
* Git or Veracity (for requirements storage)


Installation
------------

Doorstop can be installed with ``pip``::

    pip install Doorstop

After installation, Doorstop is available on the command-line::

   doorstop --help

And the package is available under the name ``doorstop``::

    python
    >>> import doorstop
    >>> doorstop.__version__


Document Creation
=================

Parent Document
---------------

After configuring version control, a new parent document can be created::

    doorstop new REQ ./reqs

Items can be added to the document and edited::

    doorstop add REQ

    doorstop edit REQ1


Child Documents
---------------

Additional documents can be created that will link to the parent::

    doorstop new TST ./reqs/tests --parent REQ

Items can be added and linked to parent items::

    doorstop add TST

    doorstop link TST1 REQ1


Document Validation
===================

To check a document hiearchy for consistency, run the main command::

    doorstop


