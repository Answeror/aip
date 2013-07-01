#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from nose.tools import assert_equal
from bs4 import BeautifulSoup as Soup
from flask import Flask
from .. import aip


class TestAip(object):

    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(aip)
        self.app = app.test_client()

    def tearDown(self):
        pass

    def test_index_empty(self):
        r = self.app.get('/')
        soup = Soup(r.data)
        content = soup.find(id='items').get_text().strip()
        return assert_equal(content, '')
