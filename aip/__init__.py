#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
from flask import Flask
from .log import RedisPub


def init_slaves(app):
    def cleanup():
        if 'AIP_EXECUTOR' in app.config:
            app.config['AIP_EXECUTOR'].shutdown()

    import atexit
    atexit.register(cleanup)
    from concurrent.futures import ThreadPoolExecutor as Ex
    app.config['AIP_EXECUTOR'] = ex = Ex(8)
    # trigger process creation
    import math
    ex.map(math.sqrt, list(range(42)))


def init_conf(app, config):
    # basic config
    from . import config as base
    app.config.from_object(base)

    if config is None:
        config = 'application.cfg'

    if type(config) is str:
        # config from file
        app.config.from_pyfile(config, silent=True)
    elif type(config) is dict:
        app.config.update(**config)
    else:
        # config from params
        app.config.from_object(config)

    if 'AIP_TEMP_PATH' not in app.config:
        import tempfile
        app.config['AIP_TEMP_PATH'] = tempfile.mkdtemp()


def init_store(app):
    from . import store
    store = store.make(app=app)
    app.store = store


class App(Flask):

    def __init__(self, *args, **kargs):
        super(App, self).__init__(*args, **kargs)
        self.redispub = RedisPub()

    def __call__(self, *args, **kargs):
        with self.redispub.threadbound():
            return super(App, self).__call__(*args, **kargs)


def init_core(app):
    from .core import Core
    app.core = Core(
        db=app.store,
        baidupan_cookie=app.config['AIP_BAIDUPAN_COOKIE'],
        baidupan_timeout=app.config['AIP_BAIDUPAN_TIMEOUT'],
    )


def make(config=None, dbmode=False, **kargs):
    try:
        from .rq import q
    except:
        pass

    if 'instance_path' in kargs:
        kargs['instance_path'] = os.path.abspath(kargs['instance_path'])

    app = App(
        __name__,
        template_folder='templates',
        static_folder='static',
        **kargs
    )
    app.kargs = kargs

    init_conf(app, config)
    init_store(app)
    init_core(app)

    if not dbmode:
        #init_slaves(app)

        from flask.ext.openid import OpenID
        oid = OpenID(app, 'temp/openid')

        from . import cache
        cached = cache.make(app)

        from . import views
        views.make(app=app, oid=oid, cached=cached, store=app.store)

        from . import api
        api.make(app=app, cached=cached, store=app.store)

    return app
