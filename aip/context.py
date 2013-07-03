#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from flask import (
    g,
    request,
    url_for
)
from .settings import PER, COLUMN_WIDTH, GUTTER


def _url_for_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)


def _proxy(url):
    from urllib.parse import quote_plus
    return quote_plus(url)


def setup(aip):
    @aip.before_request
    def before_request():
        g.aip = aip.local()
        g.url_for_page = _url_for_page
        g.column_width = COLUMN_WIDTH
        g.gutter = GUTTER
        g.per = PER
        g.proxy = _proxy
