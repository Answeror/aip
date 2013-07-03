#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import logging
import urllib3
from flask import (
    g,
    url_for,
    render_template
)
from operator import attrgetter as attr
from .settings import PER, LOG_FILE_PATH
import os


def _scale(images):
    images = list(images)
    if images:
        from urllib.parse import quote_plus
        for im in images:
            im.scale = g.column_width
        max(images, key=attr('score')).scale = g.gutter + 2 * g.column_width
        for im in images:
            im.preview_height = im.scale * im.height / im.width
            im.preview_width = im.scale
            if im.preview_width != g.column_width and hasattr(im, 'sample_url') and im.sample_url is not None:
                im.preview_url = url_for('.image', src=quote_plus(im.sample_url))
            im.url = url_for('.image', src=quote_plus(im.url))
    return images


class Local(object):

    def __init__(self, blue):
        self.blue = blue
        self.http = urllib3.PoolManager()

    @property
    def store(self):
        return self.blue.store

    def fetch(self, url):
        return self.http.request('GET', url)

    def image(self, url):
        from urllib.parse import unquote_plus
        url = unquote_plus(url)
        logging.debug('fetch image: %s' % url)
        r = self.fetch(url)
        return r.data, 200, {'Content-Type': r.headers['content-type']}

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

    def scss(self):
        import scss
        from collections import OrderedDict
        root = os.path.join(self.blue.static_folder, 'scss')
        c = scss.Scss(
            scss_vars={},
            scss_opts={
                'compress': True,
                'debug_info': True,
                'load_paths': [root]
            }
        )
        sources = []
        for filename in os.listdir(root):
            if filename.endswith('.scss'):
                with open(os.path.join(root, filename), 'rb') as f:
                    content = f.read().decode('utf-8')
                sources.append((filename, content))
        c._scss_files = OrderedDict(sources)
        return c.compile(), 200, {'Content-Type': 'text/css'}

    def log(self):
        with open(LOG_FILE_PATH, 'rb') as f:
            return f.read()
