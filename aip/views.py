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
import tempfile
from . import app


def manager():
    if not manager in g:
        from BooruPy import BooruManager
        g.manager = BooruManager(os.path.join(app.static_folder, 'provider.json'))
    return g.manager


def provider():
    return manager().get_provider_by_id(0)


def scale(images):
    images = list(images)
    if images:
        for im in images:
            im.scale = g.column_width
        max(images, key=attr('score')).scale = g.gutter + 2 * g.column_width
        for im in images:
            im.preview_height = im.scale * im.preview_height / im.preview_width
            im.preview_width = im.scale
            #if im.preview_width != g.column_width and hasattr(im, 'sample_url'):
                #f = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                #f.write(provider()._fetch(im.sample_url))
                #f.close()
                #im.id = os.path.basename(f.name)
                #im.preview_url = url_for('image', id=im.id)
    return images


def posts(page):
    init_page_layout()
    from .pagination import Infinite
    tags = []
    pagination = Infinite(
        page,
        app.config['PER'],
        lambda page, per: scale(provider().get_images(tags, page - 1, per))
    )
    return render_template('index.html', pagination=pagination)


def image(id):
    with open(os.path.join(tempfile.tempdir, id), 'rb') as f:
        return f.read(), 200, {'Content-Type': 'image/jpeg'}


def init_page_layout():
    g.column_width = app.config['COLUMN_WIDTH']
    g.gutter = app.config['GUTTER']


def url_for_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)


app.jinja_env.globals['url_for_page'] = url_for_page
