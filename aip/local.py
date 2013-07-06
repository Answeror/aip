#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import logging
import urllib3
from flask import (
    g,
    render_template,
    make_response,
    url_for
)
from operator import attrgetter as attr
from .settings import PER, LOG_FILE_PATH
import os
from io import BytesIO
from PIL import Image
from collections import namedtuple


Post = namedtuple('Post', (
    'url',
    'preview_url',
    'preview_width',
    'preview_height',
    'sample_url',
    'proxy_sample_url'
))


def url_for_resized(url, width, height):
    from urllib.parse import quote_plus
    return url_for('.resized', src=quote_plus(url), width=width, height=height)


def _scale(images):
    images = list(images)
    posts = []
    if images:
        for im in images:
            im.scale = g.column_width
        max(images, key=attr('score')).scale = g.gutter + 2 * g.column_width
        for im in images:
            sample_url = im.sample_url if im.sample_url else im.url
            preview_height = int(im.scale * im.height / im.width)
            preview_width = int(im.scale)
            posts.append(Post(
                url=im.post_url,
                preview_url=im.preview_url,
                preview_height=preview_height,
                preview_width=preview_width,
                sample_url=sample_url,
                proxy_sample_url=url_for_resized(sample_url, preview_width, preview_height)
            ))
    return posts


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

    def resized(self, url, width, height):
        from urllib.parse import unquote_plus
        url = unquote_plus(url)
        logging.debug('fetch image: %s' % url)
        r = self.fetch(url)
        input_stream = BytesIO(r.data)
        im = Image.open(input_stream)
        im = im.resize((width, height), Image.ANTIALIAS)
        output_stream = BytesIO()
        im.save(output_stream, format='JPEG')
        return output_stream.getvalue(), 200, {'Content-Type': r.headers['content-type']}

    def connection(self):
        return self.blue.connection()

    def image_count(self):
        with self.connection() as con:
            return str(con.image_count())

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
                lambda begin, end: _scale(
                    con.get_images_order_bi_ctime(r=slice(begin, end, 1))
                )
            )
            for it in pagination.items:
                pass
            return render_template('index.html', pagination=pagination)

    def stream(self, page):
        return make_response(
            self.posts_in_page(page),
            200,
            {'Content-Type': 'application/octet-stream'}
        )

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

    def clear(self):
        self.blue.clear()
        return ''
