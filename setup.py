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
    author='Jace Browning',
    author_email='jacebrowning@gmail.com',
    packages=['doorstop', 'doorstop.test'],
    scripts=[],
    url='http://pypi.python.org/pypi/Doorstop/',
    license='LICENSE.txt',
    description="Text-based requirements management.",
    long_description=open('README.rst').read(),
    install_requires=[],
    cmdclass={'test': TestCommand},
)
