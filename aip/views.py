#!/usr/bin/env python
# -*- coding: utf-8 -*-



from flask import (
    g,
    url_for,
    request,
    render_template
)
import urllib.request, urllib.parse, urllib.error
from functools import wraps
from operator import attrgetter as attr
import logging
import pickle
from . import aip
from .settings import PER, COLUMN_WIDTH, GUTTER


def logged(f):
    @wraps(f)
    def inner(*args, **kargs):
        try:
            return f(*args, **kargs)
        except Exception as e:
            logging.exception(e)
            raise
    return inner


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
                im.preview_url = url_for('.image', src=urllib.parse.quote_plus(im.sample_url))
    return images


@logged
def update(begin):
    from datetime import datetime
    begin = datetime.strptime(begin, '%Y%m%d')
    aip.update(begin)
    return 'updated from %s' % begin.strftime('%Y-%m-%d')


@logged
def posts(page):
    with aip.connection() as con:
        init_globals()
        init_page_layout()
        from .pagination import Infinite
        pagination = Infinite(
            page,
            PER,
            lambda page, per: scale(
                con.get_images_order_bi_ctime(r=list(range((page - 1) * per, page * per)))
            )
        )
        for it in pagination.items:
            pass
        return render_template('index.html', pagination=pagination)


@logged
def image(src):
    src = urllib.parse.unquote_plus(src)
    logging.debug('image: %s' % src)
    with aip.connection() as con:
        cache = con.get_cache_bi_id(src)
        if cache is None:
            logging.debug('cache miss %s' % src)
            r = fetch(src)
            cache = aip.store.Cache(
                id=src,
                data=r.data,
                meta=pickle.dumps({'Content-Type': r.headers['content-type']})
            )
            con.add_or_update(cache)
            con.commit()
        else:
            logging.debug('cache hit %s' % src)
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
