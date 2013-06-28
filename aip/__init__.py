#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint


aip = Blueprint(
    'aip',
    __name__,
    template_folder='templates',
    static_folder='static'
)


from . import urls
