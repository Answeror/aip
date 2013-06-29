#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import division
from flask import (
    g,
    url_for,
    request,
    render_template
)
from operator import attrgetter as attr
import logging
from . import aip
from .settings import PER, COLUMN_WIDTH, GUTTER


def http():
    if not 'http' in g:
        import urllib3
        g.http = urllib3.PoolManager()
    return g.http


def fetch_head(url):
    return http().request('HEAD', url)


def fetch_data(url):
    return http().request('GET', url).data


def fetch_redirect_url(url):
    return fetch_head(url).get_redirect_location()


def scale(images):
    images = list(images)
    if images:
        for im in images:
            im.scale = g.column_width
        max(images, key=attr('score')).scale = g.gutter + 2 * g.column_width
        for im in images:
            im.preview_height = im.scale * im.height / im.width
            im.preview_width = im.scale
            if im.preview_width != g.column_width and hasattr(im, 'sample_url') and im.sample_url is not None:
                im.preview_url = url_for('.image', src=im.sample_url)
    return images


def posts(page):
    aip.update()
    with aip.connection() as con:
        init_globals()
        init_page_layout()
        from .pagination import Infinite
        pagination = Infinite(
            page,
            PER,
            lambda page, per: scale(
                con.get_images_order_bi_ctime(r=range((page - 1) * per, page * per))
            )
        )
        return render_template('index.html', pagination=pagination)


def image(src):
    logging.debug('image: %s' % src)
    return fetch_data(src), 200, {'Content-Type': 'image/jpeg'}


def init_page_layout():
    g.column_width = COLUMN_WIDTH
    g.gutter = GUTTER


def url_for_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)


def init_globals():
    g.url_for_page = url_for_page
