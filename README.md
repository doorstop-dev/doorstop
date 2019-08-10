[![Build Status](http://img.shields.io/travis/jacebrowning/doorstop/master.svg)](https://travis-ci.org/jacebrowning/doorstop)
[![Coverage Status](http://img.shields.io/coveralls/jacebrowning/doorstop/master.svg)](https://coveralls.io/r/jacebrowning/doorstop)
[![Scrutinizer Code Quality](http://img.shields.io/scrutinizer/g/jacebrowning/doorstop.svg)](https://scrutinizer-ci.com/g/jacebrowning/doorstop/?branch=master)
[![PyPI Version](http://img.shields.io/pypi/v/Doorstop.svg)](https://pypi.org/project/Doorstop)
[![Best Practices](https://bestpractices.coreinfrastructure.org/projects/754/badge)](https://bestpractices.coreinfrastructure.org/projects/754)
[![Gitter](https://badges.gitter.im/jacebrowning/doorstop.svg)](https://gitter.im/jacebrowning/doorstop?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)

# Overview

Doorstop is a [requirements management](http://alternativeto.net/software/doorstop/) tool that facilitates the storage of textual requirements alongside source code in version control.

<img align="left" width="100" src="https://raw.githubusercontent.com/jacebrowning/doorstop/develop/docs/images/logo-black-white.png"/>

When a project leverages this tool, each linkable item (requirement, test case, etc.) is stored as a YAML file in a designated directory. The items in each directory form a document. The relationship between documents forms a tree hierarchy. Doorstop provides mechanisms for modifying this tree, validating item traceability, and publishing documents in several formats.

Doorstop is under active development and we welcome contributions.
The project is licensed as [LGPLv3](https://github.com/jacebrowning/doorstop/blob/develop/LICENSE.md).
To report a problem or a security vulnerability please [raise an issue](https://github.com/jacebrowning/doorstop/issues).
Additional references:

- publication: [JSEA Paper](http://www.scirp.org/journal/PaperInformation.aspx?PaperID=44268#.UzYtfWRdXEZ)
- talks: [GRDevDay](https://speakerdeck.com/jacebrowning/doorstop-requirements-management-using-python-and-version-control), [BarCamp](https://speakerdeck.com/jacebrowning/strip-searched-a-rough-introduction-to-requirements-management)
- sample: [Generated HTML](http://jacebrowning.github.io/doorstop/index.html)


# Setup

## Requirements

* Python 3.5+
* A version control system for requirements storage

## Installation

Install Doorstop with pip:

```sh
$ pip install doorstop
```

or add it to your [Poetry](https://poetry.eustace.io/) project:

```sh
$ poetry add doorstop
```

After installation, Doorstop is available on the command-line:

```sh
$ doorstop --help
```

And the package is available under the name 'doorstop':

```sh
$ python
>>> import doorstop
>>> doorstop.__version__
```

# Usage

Switch to an existing version control working directory, or create one:

```sh
$ git init .
```

## Create documents

Create a new parent requirements document:

```sh
$ doorstop create SRD ./reqs/srd
```

Add a few items to that document:

```sh
$ doorstop add SRD
$ doorstop add SRD
$ doorstop add SRD
```

## Link items

Create a child document to link to the parent:

```sh
$ doorstop create HLTC ./tests/hl --parent SRD
$ doorstop add HLTC
```

Link items between documents:

```sh
$ doorstop link HLTC001 SRD002
```

## Publish reports

Run integrity checks on the document tree:

```sh
$ doorstop
```

Publish the documents as HTML:

```sh
$ doorstop publish all ./public
```
