#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from nose.tools import assert_equal
from bs4 import BeautifulSoup as Soup
from flask import Flask
from .. import make
from .settings import CONFIG_FILE_PATH


class TestBase(object):

    def setUp(self):
        app = Flask(__name__)
        self.aip = make()
        app.register_blueprint(self.aip)
        self.app = app.test_client()


class TestConfig(object):

    def setUp(self):
        TestBase.setUp(self)

    def test_config(self):
        self.aip.config(CONFIG_FILE_PATH)
        assert_equal(len(self.aip.providers), 2)


class TestConfigured(TestBase):

    def setUp(self):
        TestBase.setUp(self)
        self.aip.config(CONFIG_FILE_PATH)

    def test_index_empty(self):
        r = self.app.get('/')
        soup = Soup(r.data)
        content = soup.find(id='items').get_text().strip()
        return assert_equal(content, '')
