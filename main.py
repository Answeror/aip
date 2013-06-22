#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import (
    Flask,
    url_for,
    render_template
)
from BooruPy import BooruManager
import logging
import os


class Site(object):

    def __init__(self, app):
        self.app = app

        @app.route("/")
        def index():
            tags = []
            images = [im for im, _ in zip(self.provider.get_images(tags), range(300))]
            return render_template('index.html', images=images)

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
