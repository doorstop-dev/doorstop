<h1> Installation </h1>

Doorstop requires [Python](https://www.python.org/) and [Git](https://git-scm.com/) or another version control system.

Once Python is installed on your platform, install Doorstop using pip.

```sh
$ pip install doorstop
```

!!! note "Installing Pre-releases"
    By default, pip only installs stable [releases of Doorstop from PyPi](https://pypi.org/project/doorstop/#history).

    To tell pip to install a pre-release version, [use the `--pre` option](https://pip.pypa.io/en/stable/cli/pip_install/#pre-release-versions):

    ```
    $ pip install --pre doorstop
    ```

Alternatively, add it to your [Poetry](https://python-poetry.org/) project:

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
