#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import division
from flask import (
    g,
    url_for,
    request,
    render_template
)
import os
from operator import attrgetter as attr
import logging
from . import aip
from .settings import PER, COLUMN_WIDTH, GUTTER


def manager():
    if not manager in g:
        from BooruPy import BooruManager
        g.manager = BooruManager(os.path.join(aip.static_folder, 'provider.json'))
    return g.manager


def provider():
    return manager().get_provider_by_id(0)


def providers():
    return manager().providers


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
            if im.preview_width != g.column_width and hasattr(im, 'sample_url'):
                im.preview_url = url_for('.image', src=im.sample_url)
            #if im.preview_width != g.column_width and hasattr(im, 'sample_url'):
                #f = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                #f.write(provider()._fetch(im.sample_url))
                #f.close()
                #im.id = os.path.basename(f.name)
                #im.preview_url = url_for('image', id=im.id)
    return images


def posts(page):
    init_globals()
    init_page_layout()
    from .pagination import Infinite
    tags = []
    from itertools import chain
    pagination = Infinite(
        page,
        PER,
        lambda page, per: scale(chain.from_iterable(
            [p.get_images(tags, page - 1, per) for p in providers()]
        ))
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
