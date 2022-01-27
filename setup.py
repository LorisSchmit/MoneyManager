"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

from setuptools import setup

APP = ['Money Manager.py']
DATA_FILES = ['--iconfile']
OPTIONS = {'iconfile': '/Users/lorisschmit1/PycharmProjects/MoneyManager/images/icon.icns'}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)