#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from flask.ext.openid import OpenID
from .blueprint import Blueprint


def make(app, temp_path=None):
    if temp_path is None:
        import tempfile
        temp_path = tempfile.mkdtemp()

    aip = Blueprint(
        'aip',
        __name__,
        template_folder='templates',
        static_folder='static',
        static_url_path='/aip/static',
        temp_path=temp_path,
        oid=OpenID(app, 'temp/openid')
    )

    from . import urls
    urls.make(aip)

    from .context import setup
    setup(aip)

    app.register_blueprint(aip)

    return aip
