#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .blueprint import Blueprint


aip = Blueprint(
    'aip',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/aip/static'
)


from . import urls
