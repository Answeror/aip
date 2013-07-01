#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from nose.tools import assert_equal, assert_in
from bs4 import BeautifulSoup as Soup
from flask import Flask
from .. import make
from .settings import CONFIG_FILE_PATH, RESPONSE_FILE_PATH
from mock import patch
from unittest import TestCase


class TestBase(TestCase):

    def setUp(self):
        app = Flask(__name__)
        self.aip = make()
        app.register_blueprint(self.aip)
        self.app = app.test_client()


class TestConfig(TestBase):

    def setUp(self):
        TestBase.setUp(self)

    def test_config(self):
        self.aip.config(CONFIG_FILE_PATH)
        assert_equal(len(self.aip.providers), 2)


class FakeResponse(object):
    pass


class FakePoolManager(object):

    def request(self, method, url):
        import pickle
        with open(RESPONSE_FILE_PATH, 'rb') as f:
            d = pickle.load(f)
        r = FakeResponse()
        assert_equal(method, 'GET')
        assert_in(url, d)
        r.data = d[url]
        return r


class TestConfigured(TestBase):

    def setUp(self):
        patcher = patch('urllib3.PoolManager', FakePoolManager)
        patcher.start()
        self.addCleanup(patcher.stop)

        TestBase.setUp(self)
        self.aip.config(CONFIG_FILE_PATH)

    def test_index_empty(self):
        r = self.app.get('/')
        soup = Soup(r.data)
        content = soup.find(id='items').get_text().strip()
        return assert_equal(content, '')

    def test_update_sites(self):
        r = self.app.get('/site_count')
        assert_equal(r.data, b'0')
        self.app.get('/update_sites')
        r = self.app.get('/site_count')
        assert_equal(r.data, b'2')

    def test_update_images(self):
        r = self.app.get('/image_count')
        assert_equal(r.data, b'0')
        self.app.get('/update_images')
        r = self.app.get('/image_count')
        assert_equal(r.data, b'0')
        self.app.get('/update_sites')
        r = self.app.get('/site_count')
        assert_equal(r.data, b'2')
        self.app.get('/update_images/20130630')
        r = self.app.get('/image_count')
        assert_equal(r.data, b'270')
