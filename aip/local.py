#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import pickle
import logging
import urllib3
from flask import (
    g,
    url_for,
    render_template
)
from operator import attrgetter as attr
from .cache import Pool as CachePool
from .settings import PER


def _scale(images):
    images = list(images)
    if images:
        for im in images:
            im.scale = g.column_width
        max(images, key=attr('score')).scale = g.gutter + 2 * g.column_width
        for im in images:
            im.preview_height = im.scale * im.height / im.width
            im.preview_width = im.scale
            if im.preview_width != g.column_width and hasattr(im, 'sample_url') and im.sample_url is not None:
                from urllib.parse import quote_plus
                im.preview_url = url_for('.image', src=quote_plus(im.sample_url))
    return images


class Local(object):

    def __init__(self, blue):
        self.blue = blue
        self.cache_pool = CachePool(blue)
        self.http = urllib3.PoolManager()

    @property
    def store(self):
        return self.blue.store

    def fetch(self, url):
        return self.http.request('GET', url)

    def image(self, url):
        from urllib.parse import unquote_plus
        url = unquote_plus(url)
        logging.debug('get image: %s' % url)
        cache = self.cache_pool.get(url)
        if cache is None:
            logging.debug('cache miss %s' % url)
            r = self.fetch(url)
            cache = self.store.Cache(
                id=url,
                data=r.data,
                meta=pickle.dumps({'Content-Type': r.headers['content-type']})
            )
            self.cache_pool.put(cache)
        else:
            logging.debug('cache hit %s' % url)
        return cache.data, 200, pickle.loads(cache.meta)

    def connection(self):
        return self.blue.connection()

    def site_count(self):
        with self.connection() as con:
            return str(con.site_count())

    def image_count(self):
        with self.connection() as con:
            return str(con.image_count())

    def update_sites(self):
        self.blue.update_sites()
        return ''

    def update_images(self, begin):
        from datetime import datetime
        begin = datetime.strptime(begin, '%Y%m%d')
        self.blue.update_images(begin)
        return ''

    def last_update_time(self):
        t = self.blue.last_update_time
        return '' if t is None else t.strftime('%Y-%m-%d %H:%M:%S')

    def posts_in_page(self, page):
        with self.connection() as con:
            from .pagination import Infinite
            pagination = Infinite(
                page,
                PER,
                lambda page, per: _scale(
                    con.get_images_order_bi_ctime(r=list(range((page - 1) * per, page * per)))
                )
            )
            for it in pagination.items:
                pass
            return render_template('index.html', pagination=pagination)

    def update(self, begin):
        from datetime import datetime
        begin = datetime.strptime(begin, '%Y%m%d')
        self.blue.update(begin)
        return 'updated from %s' % begin.strftime('%Y-%m-%d')
