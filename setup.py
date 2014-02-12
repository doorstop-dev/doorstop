#!/usr/bin/env python

"""
Setup script for Doorstop.
"""

import setuptools

from doorstop import __project__, __version__, CLI, GUI

setuptools.setup(
    name=__project__,
    version=__version__,

    description="Text-based requirements management using version control.",
    url='http://pypi.python.org/pypi/Doorstop',
    author='Jace Browning',
    author_email='jacebrowning@gmail.com',

    packages=setuptools.find_packages(),
    package_data={'doorstop.core': ['files/*']},

    entry_points={'console_scripts': [CLI + ' = doorstop.cli.main:main',
                                      GUI + ' = doorstop.gui.main:main']},

    long_description=(open('README.rst').read() + '\n' +
                      open('CHANGES.rst').read()),
    license='LGPL',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',  # pylint: disable=C0301
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.3',
        'Topic :: Software Development :: Documentation',
        'Topic :: Text Editors :: Documentation',
        'Topic :: Text Processing :: Markup',
    ],

    install_requires=["PyYAML == 3.10", "Markdown == 2.3.1"],
)
