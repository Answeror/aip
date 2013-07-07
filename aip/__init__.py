#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .blueprint import Blueprint


def make(temp_path=None):
    if temp_path is None:
        import tempfile
        temp_path = tempfile.mkdtemp()

    aip = Blueprint(
        'aip',
        __name__,
        template_folder='templates',
        static_folder='static',
        static_url_path='/aip/static',
        temp_path=temp_path
    )

    from . import urls
    urls.make(aip)

    from .context import setup
    setup(aip)

    return aip
