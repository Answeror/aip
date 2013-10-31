#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))

from logbook.compat import redirect_logging
redirect_logging()

from aip import make
from aip.log import RedisPub

with RedisPub():
    app = make(
        instance_path=DATA_PATH,
        instance_relative_config=True
    )

from werkzeug.contrib.fixers import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app)
