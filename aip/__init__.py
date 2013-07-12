#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from flask.ext.openid import OpenID
import tempfile
from flask import Flask


app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static'
)
app.config['aip.temp_path'] = tempfile.mkdtemp()
oid = OpenID(app, 'temp/openid')


from . import urls
