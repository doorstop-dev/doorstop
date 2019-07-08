# Setup

## Requirements

* Make:
    * macOS: `$ xcode-select --install`
    * Linux: [https://www.gnu.org/software/make](https://www.gnu.org/software/make)
    * Windows: [https://mingw.org/download/installer](https://mingw.org/download/installer)
* Python: `$ pyenv install`
* Poetry: [https://poetry.eustace.io/docs/#installation](https://poetry.eustace.io/docs/#installation)
* Graphviz:
    * macOS: `$ brew install graphviz`
    * Linux: [https://graphviz.org/download](https://graphviz.org/download/)
    * Windows: [https://graphviz.org/download](https://graphviz.org/download/)

To confirm these system dependencies are configured correctly:

```sh
$ make doctor
```

## Installation

Install project dependencies into a virtual environment:

```sh
$ make install
```

# Development Tasks

## Manual

Run the tests:

```sh
$ make test
```

Run static analysis:

```sh
$ make check
```

Build the documentation:

```sh
$ make docs
```

## Automatic

Keep all of the above tasks running on change:

```sh
$ make watch
```

> In order to have OS X notifications, `brew install terminal-notifier`.

# Continuous Integration

The CI server will report overall build status:

```sh
$ make ci
```

# Release Tasks

Release to PyPI:

```sh
$ make upload
```
