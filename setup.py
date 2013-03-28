#!/usr/bin/env python

"""
Setup script for Doorstop.
"""

from distutils.core import setup, Command


class TestCommand(Command):  # pylint: disable=R0904
    """Runs the unit tests."""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import sys
        import subprocess
        raise SystemExit(subprocess.call([sys.executable, '-m', 'unittest', 'discover']))

setup(
    name='Doorstop',
    version='0.0.x',

    description="Text-based requirements management.",
    url='http://pypi.python.org/pypi/Doorstop/',
    author='Jace Browning',
    author_email='jacebrowning@gmail.com',

    packages=['doorstop', 'doorstop.test'],
    scripts=[],

    cmdclass={'test': TestCommand},
    long_description=open('README.rst').read(),
    license='LICENSE.txt',
)
