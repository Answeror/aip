#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from flask import (
    Flask,
    url_for,
    request,
    render_template
)
from BooruPy import BooruManager
import logging
import os
from operator import attrgetter as attr


PER = 20
COLUMN_WIDTH = 200
GUTTER = 10


def scale(images):
    if images:
        for im in images:
            im.scale = COLUMN_WIDTH
        max(images, key=attr('score')).scale = GUTTER + 2 * COLUMN_WIDTH
        for im in images:
            im.preview_height = im.scale * im.preview_height / im.preview_width
            im.preview_width = im.scale
    return images


class Site(object):

    def __init__(self, app):
        self.app = app

        @app.route('/', defaults={'page': 1})
        @app.route('/page/<int:page>')
        def index(page):
            tags = []
            images = [im for im, _ in zip(self.provider.get_images(tags), range(1024))]
            from pagination import Infinite
            pagination = Infinite(page, PER, lambda page, per: scale(images[(page - 1) * per:page * per]))
            return render_template('index.html', pagination=pagination)

        def url_for_page(page):
            args = request.view_args.copy()
            args['page'] = page
            return url_for(request.endpoint, **args)

        app.jinja_env.globals['url_for_page'] = url_for_page
        app.jinja_env.globals['column_width'] = COLUMN_WIDTH
        app.jinja_env.globals['gutter'] = GUTTER

    def run(self, *args, **kargs):
        return self.app.run(*args, **kargs)

    @property
    def manager(self):
        if not hasattr(self, '_manager'):
            with self.app.app_context():
                self._manager = BooruManager(os.path.join(self.app.static_folder, 'provider.json'))
        return self._manager

    @property
    def provider(self):
        return self.manager.get_provider_by_id(0)


def setuplogging(level, stdout):
    logging.basicConfig(filename='boorubox.log', level=level)
    if stdout:
        import sys
        soh = logging.StreamHandler(sys.stdout)
        soh.setLevel(level)
        logger = logging.getLogger()
        logger.addHandler(soh)


if __name__ == "__main__":
    setuplogging(logging.DEBUG, True)
    site = Site(Flask(__name__))
    site.run(debug=True)
