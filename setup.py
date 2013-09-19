#!/usr/bin/env python

"""
Setup script for Doorstop.
"""

import setuptools

from doorstop import __project__, CLI, GUI


class TestCommand(setuptools.Command):  # pylint: disable=R0904
    """Runs the unit and integration tests."""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import sys
        import subprocess
        raise SystemExit(subprocess.call([sys.executable, '-m',
                                          'unittest', 'discover']))

setuptools.setup(
    name=__project__,
    version='0.0.1',

    description="Manage your requirements as text using version control.",
    url='http://pypi.python.org/pypi/Doorstop',
    author='Jace Browning',
    author_email='jacebrowning@gmail.com',

    packages=setuptools.find_packages(),

    entry_points={'console_scripts': [CLI + ' = doorstop.cli:main',
                                      GUI + ' = doorstop.gui:main']},

    cmdclass={'test': TestCommand},
    long_description=open('README.rst').read(),
    license='LICENSE.txt',

    install_requires=["PyYAML >= 3.10", "scripttest >= 1.2"],
)
