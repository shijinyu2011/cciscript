#!/usr/bin/env python

import qcutils

try:
    # try produce egg by default
    from setuptools import setup
except ImportError:
    # use python builtin if no setuptools present
    from distutils.core import setup

setup(
    name='qcutils',
    version=qcutils.__version__,
    description='Quality Center utilities',
    url='https://deveo.access.nsn.com/Nokia/projects/activity/qcutils/',
    scripts=['qcutils/scripts/qcutilscli.py'],
    packages=['qcutils',
              'qcutils.client',
              'qcutils.client.rest',
              'qcutils.utils',
              'qcutils.robot']
)
