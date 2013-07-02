#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .blueprint import Blueprint


def make():
    aip = Blueprint(
        'aip',
        __name__,
        template_folder='templates',
        static_folder='static',
        static_url_path='/aip/static'
    )

    from . import urls
    urls.make(aip)

    from .context import setup
    setup(aip)

    return aip
