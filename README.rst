Introduction
============

Doorstop is a tool that let's you store texual requirements along with your
source code in version control. It takes care checking document items and
links for consistency and compleness. Doorstop supports multiple
import/export and reporting formats.

.. NOTE::
   0.0.x releases are experimental and non-functional.



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
    