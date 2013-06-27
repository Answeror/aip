#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask


app = Flask(__name__)
app.config.from_object('%s.settings' % __name__)


from . import urls
