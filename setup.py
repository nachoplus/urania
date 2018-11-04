#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#
# urania
# Copyright (c) Noviembre 2018 Nacho Mas
from codecs import open as codecs_open
from setuptools import setup, find_packages

# Get the long description from the relevant file
with codecs_open('README.rst', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='urania',
    version='0.0.1',
    description=u"astronomical moving object detection suit",
    long_description=long_description,
    classifiers=[],
    keywords=['detection','asteroid'],
    author=u"Nacho Mas",
    author_email='mas.ignacio@gmail.com',
    url='https://github.com/nachoplus/urania',
    license='GPL3',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=['astropy'],
    extras_require={
        'test': ['pytest'],
    },
    package_data={
        '': ['config.ini', 'config.ini.spec'],
    },
    entry_points="""
      [console_scripts]
      uSex=urania.scripts.cli:uSex
      """)
