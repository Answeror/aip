#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .blueprint import Blueprint


def make(temp_path):
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
