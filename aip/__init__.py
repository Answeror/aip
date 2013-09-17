#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import logging


def make_executor(app):
    def cleanup():
        if 'AIP_EXECUTOR' in app.config:
            app.config['AIP_EXECUTOR'].shutdown()

    import atexit
    atexit.register(cleanup)
    from concurrent.futures import ProcessPoolExecutor as Ex
    app.config['AIP_EXECUTOR'] = ex = Ex()
    # trigger process creation
    import math
    ex.map(math.sqrt, list(range(42)))


def make(config=None, **kargs):
    from flask import Flask
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='static',
        **kargs
    )

    # config
    from . import config as base
    app.config.from_object(base)

    # config from params
    if config:
        app.config.from_object(config)

    # config from file
    app.config.from_pyfile('application.cfg', silent=True)

    if 'AIP_TEMP_PATH' not in app.config:
        import tempfile
        app.config['AIP_TEMP_PATH'] = tempfile.mkdtemp()

    # setup logging
    level = app.config.get('AIP_LOG_LEVEL', logging.DEBUG)
    logging.basicConfig(
        filename=app.config.get('AIP_LOG_FILE_PATH', os.path.join(app.instance_path, 'aip.log')),
        level=level
    )
    if app.config.get('AIP_LOG_STDOUT', True):
        import sys
        soh = logging.StreamHandler(sys.stdout)
        soh.setLevel(level)
        logger = logging.getLogger()
        logger.addHandler(soh)

    make_executor(app)

    from flask.ext.openid import OpenID
    oid = OpenID(app, 'temp/openid')

    from . import cache
    cached = cache.make(app)

    from . import store
    store = store.make(app=app)

    from . import views
    views.make(app=app, oid=oid, cached=cached, store=store)

    from . import api
    api.make(app=app, cached=cached, store=store)

    return app
