#!/usr/bin/env python
# -*- coding: utf-8 -*-


from setuptools import setup
import subprocess as sp


# see http://goo.gl/y6wgWV for details
version = sp.check_output(["git", "describe"]).decode('utf-8').strip()


setup(
    name='aip.core',
    version=version,
    author='answeror',
    author_email='answeror@gmail.com',
    packages=['aip'],
    description='AIP Instrumentality Project',
    include_package_data=True,
    zip_safe=False
)
