#!/usr/bin/env python

import os
import sys
import shutil
import warnings
import urllib.request
import zipfile

import setuptools


PACKAGE_NAME = 'doorstop'
MINIMUM_PYTHON_VERSION = '3.4'


def check_python_version():
    """Exit when the Python version is too low."""
    if sys.version < MINIMUM_PYTHON_VERSION:
        sys.exit("Python {0}+ is required.".format(MINIMUM_PYTHON_VERSION))
    if sys.version < '3.5':
        warnings.warn("Doorstop v1.6 will drop support for Python 3.4", DeprecationWarning)


def read_package_variable(key, filename='__init__.py'):
    """Read the value of a variable from the package without importing."""
    module_path = os.path.join(PACKAGE_NAME, filename)
    with open(module_path) as module:
        for line in module:
            parts = line.strip().split(' ', 2)
            if parts[:-1] == [key, '=']:
                return parts[-1].strip("'")
    sys.exit("'%s' not found in '%s'", key, module_path)


def build_description():
    """Build a description for the project from documentation files."""
    try:
        readme = open("README.rst").read()
        changelog = open("CHANGELOG.rst").read()
    except IOError:
        return "<placeholder>"
    else:
        return readme + '\n' + changelog

def download_supplementary_assets():
    """ Download and store supplementary assets."""
    path_prefix = 'doorstop/core/files/assets/doorstop'
    shutil.rmtree(path_prefix + '/MathJax-2.7.5', ignore_errors=True)
    shutil.rmtree(path_prefix + '/MathJax', ignore_errors=True)
    url = "https://github.com/mathjax/MathJax/archive/2.7.5.zip"
    urllib.request.urlretrieve(url, path_prefix + '/MathJax.zip')
    zip_ref = zipfile.ZipFile(path_prefix + '/MathJax.zip', 'r')
    zip_ref.extractall(path_prefix)
    zip_ref.close()
    os.remove(path_prefix + '/MathJax.zip')
    shutil.rmtree(path_prefix + '/MathJax', ignore_errors=True)
    shutil.move(path_prefix + '/MathJax-2.7.5/unpacked', path_prefix + '/MathJax')
    shutil.rmtree(path_prefix + '/MathJax-2.7.5')

def package_files(directory, relPathBase):
    paths = []
    for (path, directories, filenames) in os.walk(directory): # pylint: disable=unused-variable
        paths.append(os.path.relpath(path, relPathBase) + "/*.*")
    return paths

check_python_version()
download_supplementary_assets()
package_data_doorstop_core = package_files('doorstop/core/files', 'doorstop/core')

setuptools.setup(
    name=read_package_variable('__project__'),
    version=read_package_variable('__version__'),

    description=read_package_variable('DESCRIPTION'),
    url='http://doorstop.readthedocs.io/',
    author='Jace Browning',
    author_email='jacebrowning@gmail.com',

    packages=setuptools.find_packages(),
    package_data={'doorstop.core': package_data_doorstop_core,
                  'doorstop': ['views/*.tpl']},

    entry_points={
        'console_scripts': [
            read_package_variable('CLI') + ' = doorstop.cli.main:main',
            read_package_variable('GUI') + ' = doorstop.gui.main:main',
            read_package_variable('SERVER') + ' = doorstop.server.main:main',
        ]
    },

    long_description=build_description(),
    license='LGPL',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Documentation',
        'Topic :: Text Editors :: Documentation',
        'Topic :: Text Processing :: Markup',
    ],

    install_requires=[
        "PyYAML >= 5.1, < 6",
        "Markdown >= 2, < 3",
        "openpyxl >= 2.1, < 2.2",
        "bottle == 0.12.13",
        "requests >= 2, < 3",
        "pyficache == 0.3.1",
        "mdx_outline >= 1.3.0, < 2",
        "python-markdown-math == 0.6",
    ],
)
