#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def make(config=None):
    from flask import Flask
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

    from . import views
    views.make(app=app, oid=oid)

    from . import store
    db = store.make(app=app)

    from . import api
    api.make(app)

    return app
