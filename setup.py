#!/usr/bin/env python

"""
Setup script for Doorstop.
"""

from setuptools import setup, Command

from doorstop import __project__, CLI


class TestCommand(Command):  # pylint: disable=R0904
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

setup(
    name=__project__,
    version='0.0.0',

    description="Manage your requirements as text using version control.",
    url='http://pypi.python.org/pypi/Doorstop',
    author='Jace Browning',
    author_email='jacebrowning@gmail.com',

    packages=['doorstop', 'doorstop.test'],

    entry_points={'console_scripts': [CLI + ' = doorstop.cli:main']},

    cmdclass={'test': TestCommand},
    long_description=open('README.rst').read(),
    license='LICENSE.txt',

    install_requires=["scripttest >= 1.2"],
)
