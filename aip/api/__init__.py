#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def make(app, cached, store):
    app.config['AIP_API_URL_PREFIX'] = '/api'
    from flask import Blueprint
    api = Blueprint(
        'api',
        __name__
    )
    from . import views
    views.make(app=app, api=api, cached=cached, store=store)
    app.register_blueprint(api, url_prefix=app.config['AIP_API_URL_PREFIX'])
