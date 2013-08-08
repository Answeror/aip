#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from flask import Flask
import redis


def make(config=None):
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='static'
    )

    # config
    from . import config as base
    app.config.from_object(base)
    if config:
        app.config.from_object(config)
    if 'AIP_TEMP_PATH' not in app.config:
        import tempfile
        app.config['AIP_TEMP_PATH'] = tempfile.mkdtemp()

    from flask.ext.openid import OpenID
    oid = OpenID(app, 'temp/openid')

    from . import cache
    cached = cache.make(app)

    from . import store
    store = store.make(app=app)

    from . import views
    views.make(app=app, oid=oid, cached=cached, store=store)

    from . import api
    red = redis.StrictRedis()
    api.make(app=app, cached=cached, store=store, red=red)

    return app
