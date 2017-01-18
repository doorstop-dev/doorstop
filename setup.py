#!/usr/bin/env python

"""Setup script for Doorstop."""

import setuptools

from doorstop import __project__, __version__, CLI, GUI, SERVER, DESCRIPTION

try:
    README = open("README.rst").read()
    CHANGELOG = open("CHANGELOG.rst").read()
except FileNotFoundError:
    LONG_DESCRIPTION = "<placeholder>"
else:
    LONG_DESCRIPTION = README + '\n' + CHANGELOG

setuptools.setup(
    name=__project__,
    version=__version__,

    description=DESCRIPTION,
    url='http://doorstop.readthedocs.io/',
    author='Jace Browning',
    author_email='jacebrowning@gmail.com',

    packages=setuptools.find_packages(),
    package_data={'doorstop.core': ['files/*']},

    entry_points={
        'console_scripts': [CLI + ' = doorstop.cli.main:main',
                            GUI + ' = doorstop.gui.main:main',
                            SERVER + ' = doorstop.server.main:main']
    },

    long_description=LONG_DESCRIPTION,
    license='LGPL',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Documentation',
        'Topic :: Text Editors :: Documentation',
        'Topic :: Text Processing :: Markup',
    ],

    install_requires=[
        "PyYAML >= 3.10, < 4",
        "Markdown >= 2, < 3",
        "openpyxl >= 2.1, < 3, != 2.1.0",
        "bottle == 0.12.13",
        "requests >= 2, < 3",
        "pyficache == 0.3.1",
    ],
)
