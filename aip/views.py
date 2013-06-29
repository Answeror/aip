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
import pickle
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


def fetch(url):
    return http().request('GET', url)


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


def update():
    aip.update()
    return 'updated'


def posts(page):
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
    with aip.connection() as con:
        cache = con.get_cache_bi_id(src)
        if cache is None:
            logging.info('cache miss %s' % src)
            r = fetch(src)
            cache = aip.store.Cache(
                id=src,
                data=r.data,
                meta=pickle.dumps({'Content-Type': r.headers['content-type']})
            )
            con.add_or_update(cache)
            con.commit()
        else:
            logging.info('cache hit %s' % src)
        return cache.data, 200, pickle.loads(cache.meta)


def init_page_layout():
    g.column_width = COLUMN_WIDTH
    g.gutter = GUTTER


def url_for_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)


def init_globals():
    g.url_for_page = url_for_page
