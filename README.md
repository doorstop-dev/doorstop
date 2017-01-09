**STATUS:** As of the 1.0 release, this project is no longer under active development. Passing pull requests will be considered for future 1.x and 2.x releases.

-----

[![Build Status](http://img.shields.io/travis/jacebrowning/doorstop/master.svg)](https://travis-ci.org/jacebrowning/doorstop)
[![Coverage Status](http://img.shields.io/coveralls/jacebrowning/doorstop/master.svg)](https://coveralls.io/r/jacebrowning/doorstop)
[![Scrutinizer Code Quality](http://img.shields.io/scrutinizer/g/jacebrowning/doorstop.svg)](https://scrutinizer-ci.com/g/jacebrowning/doorstop/?branch=master)
[![PyPI Version](http://img.shields.io/pypi/v/Doorstop.svg)](https://pypi.python.org/pypi/Doorstop)
[![PyPI Downloads](http://img.shields.io/pypi/dm/Doorstop.svg)](https://pypi.python.org/pypi/Doorstop)

# Overview

Doorstop manages the storage of textual requirements alongside source code in version control.

<img align="left" width="140" src="https://raw.githubusercontent.com/jacebrowning/doorstop/develop/docs/images/logo-black-white.png"/>

When a project utilizes this tool, each linkable item (requirement, test case, etc.) is stored as a YAML file in a designated directory. The items in each directory form a document. The relationship between documents forms a tree hierarchy. Doorstop provides mechanisms for modifying this tree, validating item traceability, and publishing documents in several formats.

Additional reading:

- publication: [JSEA Paper](http://www.scirp.org/journal/PaperInformation.aspx?PaperID=44268#.UzYtfWRdXEZ)
- talks: [GRDevDay](https://speakerdeck.com/jacebrowning/doorstop-requirements-management-using-python-and-version-control), [BarCamp](https://speakerdeck.com/jacebrowning/strip-searched-a-rough-introduction-to-requirements-management)
- sample: [Generated HTML](http://jacebrowning.github.io/doorstop/index.html)

# Setup

## Requirements

* Python 3.3+
* A version control system for requirements storage

## Installation

Install Doorstop with pip:

```
$ pip install doorstop
```

or directly from source:

```
$ git clone https://github.com/jacebrowning/doorstop.git
$ cd doorstop
$ python setup.py install
```

After installation, Doorstop is available on the command-line:

```
$ doorstop --help
```

And the package is available under the name 'doorstop':

```
$ python
>>> import doorstop
>>> doorstop.__version__
```

# Usage

Switch to an existing version control working directory, or create one:

```
$ git init .
```

## Create documents

Create a new parent requirements document:

```
$ doorstop create SRD ./reqs/srd
```

Add a few items to that document:

```
$ doorstop add SRD
$ doorstop add SRD
$ doorstop add SRD
```

## Link items

Create a child document to link to the parent:

```
$ doorstop create HLTC ./tests/hl --parent SRD
$ doorstop add HLTC
```

Link items between documents:

```
$ doorstop link HLTC001 SRD002
```

## Publish reports

Run integrity checks on the document tree:

```
$ doorstop
```

Publish the documents as HTML:

```
$ doorstop publish all ./public
```
