#!/usr/bin/env python

"""
Setup script for Doorstop.
"""

import setuptools

from doorstop import __project__, CLI, GUI

setuptools.setup(
    name=__project__,
    version='0.0.3-rc.1',

    description="Manage your requirements as text using version control.",
    url='http://pypi.python.org/pypi/Doorstop',
    author='Jace Browning',
    author_email='jacebrowning@gmail.com',

    packages=setuptools.find_packages(),

    entry_points={'console_scripts': [CLI + ' = doorstop.cli:main',
                                      GUI + ' = doorstop.gui:main']},

    long_description=open('README.rst').read(),
    license='LGPL',

    install_requires=["PyYAML >= 3.10", "scripttest >= 1.2"],
)
