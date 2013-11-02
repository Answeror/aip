#!/usr/bin/env python
# -*- coding: utf-8 -*-


from setuptools import setup, find_packages
import subprocess as sp


# see http://goo.gl/y6wgWV for details
version = sp.check_output(["git", "describe"]).decode('utf-8').strip()


setup(
    name='aip.core',
    version=version,
    author='answeror',
    author_email='answeror@gmail.com',
    packages=find_packages(),
    description='AIP Instrumentality Project',
    include_package_data=True,
    entry_points='''\
    [console_scripts]
    aiplog = log:main
    ''',
    zip_safe=False,
    install_requires=[
        'Flask==0.10.1',
        'urllib3',
        'pyScss==1.2.0',
        'SQLAlchemy==0.8.2',
        'Flask-SQLAlchemy==0.17',
        'Pillow==2.1.0',
        'Flask-OpenID==1.42.1',
        'python3-openid==3.0.1',
        'six',
        'fn',
        'nose',
        'baidupcs==0.3.0',
        'requests==2.0.0',
        'redis',
        'rq',
        'setproctitle',
        'logbook',
        'Wand',
        'profilehooks',
    ],
    dependency_links = [
        'https://github.com/Answeror/ConfigIt/tarball/version#egg=ConfigIt-0.1.3',
        'git+https://github.com/Answeror/pyScss.git@0a22ed41b76f183f19af6cba54a5a8193302509d#egg=pyScss-1.2.0',
        'https://github.com/Answeror/flask-openid/tarball/version#egg=Flask-OpenID-1.42.1',
        'https://github.com/zain/flask-sqlalchemy/tarball/ce1ed2abd0dbee04f0601d0e4d1770fff9ed9074#egg=Flask-SQLAlchemy-0.17'
    ]
)
